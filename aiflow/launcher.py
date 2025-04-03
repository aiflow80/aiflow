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

logger = setup_logger('Launcher')

class Launcher:
    # Class variables
    _instance: Optional['Launcher'] = None
    _loop: Optional[asyncio.AbstractEventLoop] = None
    _thread: Optional[threading.Thread] = None
    _lock = threading.Lock()
    _loop_ready = threading.Event()
    _main_thread_exit = threading.Event()

    # Singleton implementation
    def __new__(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super().__new__(cls)
                cls._instance._initialize()
            return cls._instance

    def _initialize(self):
        logger.info("Initializing...")
        
        # Save original handlers for proper cleanup
        self._original_sigint_handler = signal.getsignal(signal.SIGINT)
        self._original_sigterm_handler = signal.getsignal(signal.SIGTERM)
        
        # Setup signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, self._handle_interrupt)
        signal.signal(signal.SIGTERM, self._handle_interrupt)
        
        # Register atexit handler as a backup cleanup mechanism
        atexit.register(self._atexit_cleanup)
        
        self.running = True
        self.processes: Dict[str, subprocess.Popen] = {}
        self.threads: List[threading.Thread] = []
        self.caller_file = self._get_caller_info()
        
        logger.info("Starting server monitoring thread")
        # Start server monitoring thread
        self._start_server_monitor()
        
        logger.info("Starting event loop thread")
        # Start event loop thread
        self.start()
        if not self._loop_ready.wait(timeout=10):
            logger.error("Event loop initialization timeout after 10 seconds")
            raise RuntimeError("Event loop initialization timeout")
        
        # Start server and wait for it to be ready
        logger.info("Starting WebSocket server")
        process = self._start_server()
        if not process:
            logger.error("Server process not started")
            raise RuntimeError("Failed to start server process")
        
        # Initialize client and launch browser
        logger.info("Initializing WebSocket client")
        self._client_ready = threading.Event()
        asyncio.run_coroutine_threadsafe(self._init_client(), self._loop)
        if not self._client_ready.wait(timeout=30):
            logger.error("Client initialization timeout after 30 seconds")
            raise RuntimeError("Client initialization timeout")

        # Start a non-daemon thread that will keep the program alive
        logger.info("Starting keep-alive thread")
        self._start_keep_alive_thread()
        logger.info("Initialization complete")

    def _atexit_cleanup(self):
        """Backup cleanup handler registered with atexit"""
        if self.running:  # Only run if normal cleanup hasn't run yet
            logger.info("Atexit cleanup triggered")
            self._cleanup()

    def _handle_interrupt(self, signum, frame):
        """Handle interrupt signals like SIGINT (Ctrl+C) and SIGTERM"""
        logger.info(f"Received signal {signum}, shutting down gracefully...")
        # Reset signal handlers to prevent recursive calls
        signal.signal(signal.SIGINT, self._original_sigint_handler)
        signal.signal(signal.SIGTERM, self._original_sigterm_handler)
        
        self._cleanup()
        # Use os._exit to avoid threading module shutdown errors
        os._exit(0)

    def _start_server_monitor(self):
        """Monitor WebSocket server status and exit when it's done"""
        def monitor():
            # Wait for initialization to complete
            time.sleep(5)
            
            while self.running:
                try:
                    # Check if WebSocket server has exited
                    for name, process in list(self.processes.items()):
                        if name == 'Server' and process.poll() is not None:
                            logger.info("Server process exited, initiating cleanup")
                            self._cleanup()
                            os._exit(0)
                    
                    # Short sleep between checks
                    time.sleep(0.5)
                except Exception as e:
                    logger.error(f"Error in server monitor: {e}")
                    time.sleep(1)
        
        thread = threading.Thread(target=monitor, name="ServerMonitor", daemon=True)
        self.threads.append(thread)
        thread.start()

    def _cleanup(self, is_restart=False):
        """Clean up resources before exit or restart"""
        if not self.running:
            logger.info("Cleanup already in progress, skipping")
            return  # Already cleaning up
        
        self.running = False
        logger.info("Cleaning up resources...")
        
        # Close WebSocket client if it exists
        if hasattr(event_base, 'ws_client') and event_base.ws_client:
            try:
                loop = self._loop  # Local reference to avoid race conditions
                if loop and loop.is_running():
                    logger.info("Closing WebSocket client")
                    future = asyncio.run_coroutine_threadsafe(
                        event_base.ws_client.close(), loop
                    )
                    # Wait for client close to complete with timeout
                    try:
                        future.result(timeout=3)  # Increased from 2
                        logger.info("WebSocket client closed successfully")
                    except (asyncio.TimeoutError, concurrent.futures.TimeoutError):
                        logger.warning("WebSocket client close timed out")
                else:
                    logger.warning("Can't close WebSocket client: event loop not running")
            except Exception as e:
                logger.error(f"Error closing WebSocket client: {e}", exc_info=True)
        
        # Terminate all processes we started
        self._terminate_processes()
        
        # Stop the event loop
        self._shutdown_event_loop()
        
        # Signal the keep-alive thread to exit
        if not is_restart:
            logger.info("Signaling keep-alive thread to exit")
            self._main_thread_exit.set()
        
        # Wait briefly for threads to finish their current task
        logger.info("Waiting for threads to finish")
        
        # Wait longer for threads
        for thread in self.threads:
            if thread.is_alive() and not thread.daemon:
                logger.info(f"Waiting for thread {thread.name} to complete")
                thread.join(timeout=2)
        
        # Log final status
        alive_threads = [t.name for t in self.threads if t.is_alive() and not t.daemon]
        if alive_threads:
            logger.warning(f"Non-daemon threads still running: {', '.join(alive_threads)}")
        
        logger.info("Cleanup completed")

    def _terminate_processes(self):
        """Terminate all processes started by this launcher"""
        if not self.processes:
            logger.info("No processes to terminate")
            return
            
        logger.info(f"Terminating {len(self.processes)} processes")
        
        # First attempt: terminate gracefully
        for name, process in list(self.processes.items()):
            try:
                if process.poll() is None:
                    logger.info(f"Terminating {name} process (PID {process.pid})")
                    # Use different methods depending on platform
                    if sys.platform == 'win32':
                        # Windows-specific process termination
                        process.terminate()
                    else:
                        # Unix-like systems can use the terminate signal
                        process.terminate()
                else:
                    logger.info(f"{name} process (PID {process.pid}) already terminated")
            except Exception as e:
                logger.error(f"Error terminating {name} process: {e}", exc_info=True)
        
        # Wait briefly for processes to terminate
        termination_wait = 3  # seconds - increased from 2
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
        
        # Force kill any remaining processes
        for name, process in list(self.processes.items()):
            try:
                if process.poll() is None:
                    logger.warning(f"{name} process did not terminate gracefully, killing forcefully")
                    if sys.platform == 'win32':
                        # On Windows, use taskkill for more reliable termination
                        try:
                            subprocess.run(['taskkill', '/F', '/T', '/PID', str(process.pid)], 
                                           timeout=3, check=False)
                        except Exception:
                            # Fall back to process.kill()
                            process.kill()
                    else:
                        # On Unix-like systems
                        process.kill()
                    
                    # Wait briefly to confirm it's killed
                    start = time.time()
                    while time.time() - start < 1.5:  # Increased from 1
                        if process.poll() is not None:
                            logger.info(f"{name} process killed")
                            break
                        time.sleep(0.1)
                    else:
                        logger.error(f"Failed to kill {name} process")
                        # Last resort: use psutil to find and kill child processes
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
        
        # Final check and reporting
        still_running = []
        for name, process in list(self.processes.items()):
            try:
                if process.poll() is None:
                    still_running.append(name)
            except Exception:
                pass
        
        if still_running:
            logger.error(f"Processes still running after cleanup: {', '.join(still_running)}")
        else:
            logger.info("All processes terminated successfully")

    def _shutdown_event_loop(self):
        """Safely shut down the event loop"""
        loop = self._loop  # Local reference to avoid race conditions
        if loop is not None:
            try:
                if loop.is_running():
                    logger.info("Stopping event loop")
                    for task in asyncio.all_tasks(loop):
                        task.cancel()
                    
                    loop.call_soon_threadsafe(self._stop_loop)
                    
                    # Wait longer for the loop to stop
                    wait_time = 1.0
                    time.sleep(wait_time)
                    
                    # Try a second time if still running
                    if loop.is_running():
                        logger.warning("Event loop still running after first stop attempt, trying again")
                        loop.call_soon_threadsafe(self._stop_loop)
                        time.sleep(wait_time)
                        
                    if not loop.is_running():
                        logger.info("Event loop stopped successfully")
                    else:
                        logger.warning("Event loop still running after multiple stop attempts")
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
        """Start WebSocket server and wait for it to be ready"""
        import socket
        # Check if server is already running
        try:
            with socket.create_connection(("localhost", config.websocket.port), timeout=1):
                logger.info(f"Server already running on port {config.websocket.port}")
                return "Process started"
        except Exception:
            logger.info(f"Starting new server on port {config.websocket.port}")
            pass

        server_script = os.path.join(os.path.dirname(__file__), 'network', 'ws_server.py')
        
        # Use different startup options based on platform
        cmd = [sys.executable, "-Xfrozen_modules=off", server_script]
        
        # Add platform-specific options if needed
        if sys.platform == 'win32':
            # Windows-specific options could go here if needed
            # For example: creationflags for subprocess
            pass
        
        process = self._start_process('Server', cmd)
        
        if not process:
            logger.error("Failed to start WebSocket server process")
            raise RuntimeError("Failed to start WebSocket server")
        
        # Wait for the server to be ready before returning the process
        self._wait_for_server(timeout=15)  # Increased from 10
        return process

    def _start_process(self, name: str, args: list) -> Optional[subprocess.Popen]:
        try:
            # Universal process creation that works on both Windows and Linux
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
                daemon=True
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
        """Public interface to clean up resources before exit or restart"""
        if cls._instance:
            cls._instance._cleanup(is_restart=is_restart)
            
            # If this is a restart, reset the singleton instance
            if is_restart:
                cls.reset_instance()
    
    @classmethod
    def reset_instance(cls):
        """Reset the singleton instance to allow a fresh start on restart"""
        logger.info("Resetting Launcher singleton instance")
        with cls._lock:
            # Reset class variables
            cls._instance = None
            cls._loop = None
            cls._thread = None
            cls._loop_ready.clear()
            cls._main_thread_exit.clear()
            
            # Reset any remaining state in event_base
            if hasattr(event_base, 'ws_client'):
                event_base.ws_client = None
                
            logger.info("Launcher instance reset complete")
    
    @classmethod
    def restart(cls):
        """Restart the application - clean up resources and reset the instance"""
        try:
            logger.info("RESTART TRIGGERED - Beginning restart sequence")
            
            # Store original info first
            script_path = sys.argv[0]
            script_dir = os.path.dirname(os.path.abspath(script_path))
            orig_args = sys.argv[1:]
            
            # Create a restart script that will be executed
            restart_script = os.path.join(script_dir, "_restart_helper.py")
            
            with open(restart_script, "w") as f:
                f.write(f"""
import os
import sys
import time
import subprocess

# Wait for parent to exit
time.sleep(2)

try:
    # Start new instance
    new_process = subprocess.Popen(
        ["{sys.executable}", "{script_path}"] + {orig_args},
        close_fds=True,
        start_new_session=True
    )
    print(f"Started new process with PID: {{new_process.pid}}")
except Exception as e:
    print(f"Error restarting: {{e}}")

# Remove this helper script
try:
    os.unlink(__file__)
except:
    pass
""")
            
            # Launch the restart helper
            logger.info(f"Launching restart helper script: {restart_script}")
            subprocess.Popen(
                [sys.executable, restart_script],
                close_fds=True,
                start_new_session=True
            )
            
            # Perform cleanup
            logger.info("Cleaning up before restart")
            cls.cleanup(is_restart=True)
            
            # Exit current process
            logger.info("Exiting for restart")
            os._exit(0)
            
        except Exception as e:
            logger.error(f"CRITICAL ERROR DURING RESTART: {e}", exc_info=True)
            # Try to create a debug file to diagnose the issue
            try:
                with open("/tmp/restart_error.log", "w") as f:
                    f.write(f"Restart error: {str(e)}\n")
                    import traceback
                    traceback.print_exc(file=f)
            except:
                pass
            return False
            
        return True  # Won't be reached

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
        browser_script = os.path.join(os.path.dirname(__file__), 'network', 'browser.py')
        self._start_process(
            'Browser',
            [sys.executable, "-Xfrozen_modules=off", browser_script, client_id]
        )

    def _wait_for_server(self, timeout=15, check_interval=0.5):
        import socket
        start_time = time.time()
        while time.time() - start_time < timeout:
            try:
                with socket.create_connection(("localhost", config.websocket.port), timeout=1):
                    return True
            except (socket.timeout, ConnectionRefusedError) as e:
                time.sleep(check_interval)
        
        logger.error(f"Server failed to start within timeout of {timeout}s")
        raise TimeoutError("Server failed to start within timeout")

    def _monitor_output(self, pipe, prefix):
        try:
            for line in iter(pipe.readline, ''):
                line = line.strip()
                if line:
                    logger.info(f"[{prefix}] {line}")
        except Exception as e:
            logger.error(f"Output monitoring error for {prefix}: {e}", exc_info=True)
        finally:
            pipe.close()

    @staticmethod
    def _get_caller_info() -> str:
        """Get information about the calling module"""
        try:
            main_module = sys.modules['__main__']
            if hasattr(main_module, '__file__'):
                main_file = os.path.abspath(main_module.__file__)
                launcher_file = os.path.abspath(__file__)
                if main_file != launcher_file:
                    return main_file
        except Exception as e:
            logger.error(f"Error getting caller info: {e}", exc_info=True)
        return None