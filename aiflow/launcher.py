import asyncio
import os
import subprocess
import sys
import threading
import time
import signal
import psutil
import concurrent.futures
import atexit
from typing import Optional, Dict, List
from aiflow.events import event_base
from aiflow.network.ws_client import WebSocketClient
from aiflow.logger import setup_logger
from aiflow.config import config

logger = setup_logger("Launcher")


class Launcher:
    _instance: Optional["Launcher"] = None
    _loop: Optional[asyncio.AbstractEventLoop] = None
    _thread: Optional[threading.Thread] = None
    _lock = threading.Lock()
    _loop_ready = threading.Event()
    _main_thread_exit = threading.Event()

    def __new__(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super().__new__(cls)
                cls._instance._initialize()
            return cls._instance

    def _initialize(self):
        logger.info("Initializing...")
        self._original_sigint_handler = signal.getsignal(signal.SIGINT)
        self._original_sigterm_handler = signal.getsignal(signal.SIGTERM)
        signal.signal(signal.SIGINT, self._handle_interrupt)
        signal.signal(signal.SIGTERM, self._handle_interrupt)
        atexit.register(self._atexit_cleanup)
        self.running = True
        self.processes: Dict[str, subprocess.Popen] = {}
        self.threads: List[threading.Thread] = []
        self.caller_file = self._get_caller_info()
        logger.info("Starting server monitoring thread")
        self._start_server_monitor()
        logger.info("Starting event loop thread")
        self.start()
        if not self._loop_ready.wait(timeout=10):
            logger.error("Event loop initialization timeout after 10 seconds")
            raise RuntimeError("Event loop initialization timeout")
        logger.info("Starting WebSocket server")
        process = self._start_server()
        if not process:
            logger.error("Server process not started")
            raise RuntimeError("Failed to start server process")
        logger.info("Initializing WebSocket client")
        self._client_ready = threading.Event()
        asyncio.run_coroutine_threadsafe(self._init_client(), self._loop)
        if not self._client_ready.wait(timeout=30):
            logger.error("Client initialization timeout after 30 seconds")
            raise RuntimeError("Client initialization timeout")
        logger.info("Starting keep-alive thread")
        self._start_keep_alive_thread()
        logger.info("Initialization complete")

    def _atexit_cleanup(self):
        if self.running:
            logger.info("Atexit cleanup triggered")
            self._cleanup()

    def _handle_interrupt(self, signum, frame):
        logger.info(f"Received signal {signum}, shutting down gracefully...")
        signal.signal(signal.SIGINT, self._original_sigint_handler)
        signal.signal(signal.SIGTERM, self._original_sigterm_handler)
        self._cleanup()
        os._exit(0)

    def _start_server_monitor(self):
        def monitor():
            time.sleep(5)
            while self.running:
                try:
                    for name, process in list(self.processes.items()):
                        if name == "Server" and process.poll() is not None:
                            logger.info("Server process exited, initiating cleanup")
                            self._cleanup()
                            os._exit(0)
                    time.sleep(0.5)
                except Exception as e:
                    logger.error(f"Error in server monitor: {e}")
                    time.sleep(1)

        thread = threading.Thread(target=monitor, name="ServerMonitor", daemon=True)
        self.threads.append(thread)
        thread.start()

    def _cleanup(self, is_restart=False):
        if not self.running:
            logger.info("Cleanup already in progress, skipping")
            return
        self.running = False
        logger.info("Cleaning up resources...")
        if hasattr(event_base, "ws_client") and event_base.ws_client:
            try:
                loop = self._loop
                if loop and loop.is_running():
                    logger.info("Closing WebSocket client")
                    future = asyncio.run_coroutine_threadsafe(
                        event_base.ws_client.close(), loop
                    )
                    try:
                        future.result(timeout=3)
                        logger.info("WebSocket client closed successfully")
                    except (asyncio.TimeoutError, concurrent.futures.TimeoutError):
                        logger.warning("WebSocket client close timed out")
                else:
                    logger.warning(
                        "Can't close WebSocket client: event loop not running"
                    )
            except Exception as e:
                logger.error(f"Error closing WebSocket client: {e}", exc_info=True)
        self._terminate_processes()
        self._shutdown_event_loop()
        if not is_restart:
            logger.info("Signaling keep-alive thread to exit")
            self._main_thread_exit.set()
        logger.info("Waiting for threads to finish")
        for thread in self.threads:
            if thread.is_alive() and not thread.daemon:
                logger.info(f"Waiting for thread {thread.name} to complete")
                thread.join(timeout=2)
        alive_threads = [t.name for t in self.threads if t.is_alive() and not t.daemon]
        if alive_threads:
            logger.warning(
                f"Non-daemon threads still running: {', '.join(alive_threads)}"
            )
        logger.info("Cleanup completed")

    def _terminate_processes(self):
        if not self.processes:
            logger.info("No processes to terminate")
            return
        logger.info(f"Terminating {len(self.processes)} processes")
        for name, process in list(self.processes.items()):
            try:
                if process.poll() is None:
                    logger.info(f"Terminating {name} process (PID {process.pid})")
                    if sys.platform == "win32":
                        process.terminate()
                    else:
                        process.terminate()
                else:
                    logger.info(
                        f"{name} process (PID {process.pid}) already terminated"
                    )
            except Exception as e:
                logger.error(f"Error terminating {name} process: {e}", exc_info=True)
        termination_wait = 3
        termination_start = time.time()
        any_terminated = False
        while time.time() - termination_start < termination_wait:
            all_terminated = True
            for name, process in list(self.processes.items()):
                try:
                    if process.poll() is None:
                        all_terminated = False
                    else:
                        if not any_terminated:
                            logger.info(f"{name} process terminated gracefully")
                            any_terminated = True
                except Exception:
                    pass
            if all_terminated:
                logger.info("All processes terminated gracefully")
                return
            time.sleep(0.2)
        for name, process in list(self.processes.items()):
            try:
                if process.poll() is None:
                    logger.warning(
                        f"{name} process did not terminate gracefully, killing forcefully"
                    )
                    if sys.platform == "win32":
                        try:
                            subprocess.run(
                                ["taskkill", "/F", "/T", "/PID", str(process.pid)],
                                timeout=3,
                                check=False,
                            )
                        except Exception:
                            process.kill()
                    else:
                        process.kill()
                    start = time.time()
                    while time.time() - start < 1.5:
                        if process.poll() is not None:
                            logger.info(f"{name} process killed")
                            break
                        time.sleep(0.1)
                    else:
                        logger.error(f"Failed to kill {name} process")
                        try:
                            parent = psutil.Process(process.pid)
                            children = parent.children(recursive=True)
                            for child in children:
                                logger.info(f"Killing child process {child.pid}")
                                child.kill()
                            if parent.is_running():
                                parent.kill()
                        except psutil.NoSuchProcess:
                            pass
                        except Exception as e:
                            logger.error(f"Error killing process tree: {e}")
            except Exception as e:
                logger.error(f"Error killing {name} process: {e}", exc_info=True)
        still_running = [
            name for name, process in self.processes.items() if process.poll() is None
        ]
        if still_running:
            logger.error(
                f"Processes still running after cleanup: {', '.join(still_running)}"
            )
        else:
            logger.info("All processes terminated successfully")

    def _shutdown_event_loop(self):
        loop = self._loop
        if loop:
            try:
                if loop.is_running():
                    logger.info("Stopping event loop")
                    for task in asyncio.all_tasks(loop):
                        task.cancel()
                    loop.call_soon_threadsafe(self._stop_loop)
                    time.sleep(1)
                    if loop.is_running():
                        logger.warning(
                            "Event loop still running after first stop attempt, trying again"
                        )
                        loop.call_soon_threadsafe(self._stop_loop)
                        time.sleep(1)
                    logger.info(
                        "Event loop stopped successfully"
                        if not loop.is_running()
                        else "Event loop still running after multiple stop attempts"
                    )
                else:
                    logger.info("Event loop not running, no need to stop it")
            except Exception as e:
                logger.error(f"Error stopping event loop: {e}", exc_info=True)
        else:
            logger.info("Event loop is None, no need to stop it")

    def _stop_loop(self):
        self._loop.stop()

    def _start_keep_alive_thread(self):
        def keep_alive():
            logger.info("Keep-alive thread started")
            self._main_thread_exit.wait()
            logger.info("Keep-alive thread exiting")

        thread = threading.Thread(target=keep_alive, name="KeepAlive", daemon=False)
        self.threads.append(thread)
        thread.start()

    @classmethod
    def start(cls):
        if not cls._thread:
            cls._thread = threading.Thread(target=cls._run_event_loop, name="EventLoop")
            cls._thread.daemon = True
            cls._thread.start()
            if cls._instance:
                cls._instance.threads.append(cls._thread)

    @classmethod
    def _run_event_loop(cls):
        try:
            cls._loop = asyncio.new_event_loop()
            asyncio.set_event_loop(cls._loop)
            cls._loop_ready.set()
            cls._loop.run_forever()
        except Exception as e:
            logger.error(f"Event loop error: {e}", exc_info=True)
        finally:
            if cls._loop and cls._loop.is_running():
                cls._loop.close()
            cls._loop = None
            cls._loop_ready.clear()

    def _start_server(self):
        import socket

        try:
            with socket.create_connection(
                ("localhost", config.websocket.port), timeout=1
            ):
                logger.info(f"Server already running on port {config.websocket.port}")
                return "Process started"
        except Exception:
            logger.info(f"Starting new server on port {config.websocket.port}")
        server_script = os.path.join(
            os.path.dirname(__file__), "network", "ws_server.py"
        )
        cmd = [sys.executable, "-Xfrozen_modules=off", server_script]
        process = self._start_process("Server", cmd)
        if not process:
            logger.error("Failed to start WebSocket server process")
            raise RuntimeError("Failed to start WebSocket server")
        self._wait_for_server(timeout=15)
        return process

    def _start_process(self, name: str, args: list) -> Optional[subprocess.Popen]:
        try:
            process = subprocess.Popen(
                args,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                bufsize=1,
                universal_newlines=True,
            )
            thread = threading.Thread(
                target=self._monitor_output,
                args=(process.stdout, name),
                name=f"MonitorOutput-{name}",
                daemon=True,
            )
            self.threads.append(thread)
            thread.start()
            logger.info(f"Started {name} process with PID {process.pid}")
            self.processes[name] = process
            return process
        except Exception as e:
            logger.error(f"Failed to start {name}: {str(e)}", exc_info=True)
            return None

    @classmethod
    def cleanup(cls, is_restart=False):
        if cls._instance:
            cls._instance._cleanup(is_restart=is_restart)
            if is_restart:
                cls.reset_instance()

    @classmethod
    def reset_instance(cls):
        logger.info("Resetting Launcher singleton instance")
        with cls._lock:
            cls._instance = None
            cls._loop = None
            cls._thread = None
            cls._loop_ready.clear()
            cls._main_thread_exit.clear()
            if hasattr(event_base, "ws_client"):
                event_base.ws_client = None
            logger.info("Launcher instance reset complete")

    @classmethod
    def restart(cls):
        try:
            logger.info("RESTART TRIGGERED - Beginning restart sequence")
            script_path = sys.argv[0]
            script_dir = os.path.dirname(os.path.abspath(script_path))
            restart_script = os.path.join(script_dir, "restart.py")
            logger.info(f"Launching restart script: {restart_script}")
            subprocess.Popen(
                [sys.executable, restart_script, script_path] + sys.argv[1:],
                close_fds=True,
                start_new_session=True,
            )
            logger.info("Cleaning up before restart")
            cls.cleanup(is_restart=True)
            logger.info("Exiting for restart")
            os._exit(0)
        except Exception as e:
            logger.error(f"CRITICAL ERROR DURING RESTART: {e}", exc_info=True)
            try:
                with open("/tmp/restart_error.log", "w") as f:
                    f.write(f"Restart error: {str(e)}\n")
                    import traceback

                    traceback.print_exc(file=f)
            except:
                pass
            return False
        return True

    async def _init_client(self):
        try:
            ws_client = WebSocketClient()
            event_base.set_ws_client(ws_client)
            await ws_client.connect()
            await ws_client.wait_for_ready()
            if ws_client.client_id:
                self._launch_browser(ws_client.client_id)
                self._client_ready.set()
            else:
                logger.error("No client ID available")
                return False
            while self.running:
                await asyncio.sleep(3)
        except Exception as e:
            logger.error(f"Client error: {e}", exc_info=True)
            return False
        return True

    def _launch_browser(self, client_id: str):
        browser_script = os.path.join(
            os.path.dirname(__file__), "network", "browser.py"
        )
        self._start_process(
            "Browser",
            [sys.executable, "-Xfrozen_modules=off", browser_script, client_id],
        )

    def _wait_for_server(self, timeout=15, check_interval=0.5):
        import socket

        start_time = time.time()
        while time.time() - start_time < timeout:
            try:
                with socket.create_connection(
                    ("localhost", config.websocket.port), timeout=1
                ):
                    return True
            except (socket.timeout, ConnectionRefusedError) as e:
                time.sleep(check_interval)
        logger.error(f"Server failed to start within timeout of {timeout}s")
        raise TimeoutError("Server failed to start within timeout")

    def _monitor_output(self, pipe, prefix):
        try:
            for line in iter(pipe.readline, ""):
                line = line.strip()
                if line:
                    logger.info(f"[{prefix}] {line}")
        except Exception as e:
            logger.error(f"Output monitoring error for {prefix}: {e}", exc_info=True)
        finally:
            pipe.close()

    @staticmethod
    def _get_caller_info() -> str:
        try:
            main_module = sys.modules["__main__"]
            if hasattr(main_module, "__file__"):
                main_file = os.path.abspath(main_module.__file__)
                launcher_file = os.path.abspath(__file__)
                if main_file != launcher_file:
                    return main_file
        except Exception as e:
            logger.error(f"Error getting caller info: {e}", exc_info=True)
        return None
