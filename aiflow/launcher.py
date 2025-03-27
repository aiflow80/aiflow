import asyncio
import os
import subprocess
import sys
import threading
import time
import signal
import atexit
import platform
from typing import Optional, Dict
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
        """Initialize all launcher components in one place"""
        logger.info("Initializing Launcher...")
        logger.info(f"Platform: {platform.platform()}, Python: {platform.python_version()}")
        logger.info(f"Process ID: {os.getpid()}, Parent PID: {os.getppid()}")
        
        self.running = True
        self.processes: Dict[str, subprocess.Popen] = {}
        self.caller_file = self._get_caller_info()
        logger.info(f"Caller file: {self.caller_file}")
        
        # Start server monitoring thread
        self._start_server_monitor()
        
        # Start event loop thread
        self.start()
        logger.info("Waiting for event loop to be ready...")
        if not self._loop_ready.wait(timeout=10):
            logger.error("Event loop initialization timeout after 10 seconds")
            raise RuntimeError("Event loop initialization timeout")
        logger.info("Event loop is ready")
        
        # Start server and wait for it to be ready
        logger.info("Starting WebSocket server...")
        self._start_server()
        
        # Initialize client and launch browser
        self._client_ready = threading.Event()
        logger.info("Initializing WebSocket client...")
        asyncio.run_coroutine_threadsafe(self._init_client(), self._loop)
        logger.info("Waiting for client to be ready...")
        if not self._client_ready.wait(timeout=30):
            logger.error("Client initialization timeout after 30 seconds")
            raise RuntimeError("Client initialization timeout")
        logger.info("Client is ready")

        # Start a non-daemon thread that will keep the program alive
        self._start_keep_alive_thread()

    def _start_server_monitor(self):
        """Monitor WebSocket server status and exit when it's done"""
        def monitor():
            # Wait for initialization to complete
            time.sleep(5)
            
            while True:
                try:
                    # Check if WebSocket server has exited
                    for name, process in list(self.processes.items()):
                        if name == 'WebSocketServer' and process.poll() is not None:
                            logger.info("WebSocket server has exited - shutting down application")
                            self._cleanup()
                            os._exit(0)
                    
                    # Short sleep between checks
                    time.sleep(0.5)
                except Exception as e:
                    logger.error(f"Error in server monitor: {e}")
                    time.sleep(1)
        
        thread = threading.Thread(target=monitor,name="ServerMonitor", daemon=True)
        thread.start()

    def _cleanup(self):
        """Clean up resources before exit"""
        if not self.running:
            logger.info("Cleanup already in progress, skipping")
            return  # Already cleaning up
        
        self.running = False
        logger.info("Cleaning up resources...")
        
        # Close WebSocket client if it exists
        if hasattr(event_base, 'ws_client') and event_base.ws_client:
            try:
                logger.info("Closing WebSocket client...")
                if self._loop and self._loop.is_running():
                    asyncio.run_coroutine_threadsafe(
                        event_base.ws_client.close(), self._loop
                    )
                    logger.info("WebSocket client close request sent")
                else:
                    logger.warning("Can't close WebSocket client: event loop not running")
            except Exception as e:
                logger.error(f"Error closing WebSocket client: {e}", exc_info=True)
        
        # Kill all child processes
        for name, process in list(self.processes.items()):
            try:
                logger.info(f"Terminating {name} (PID: {process.pid})...")
                if process.poll() is None:
                    logger.info(f"Process {name} still running, sending kill signal")
                    process.kill()
                    logger.info(f"Kill signal sent to {name}")
                else:
                    logger.info(f"Process {name} already exited with code {process.returncode}")
            except Exception as e:
                logger.error(f"Error killing {name}: {e}", exc_info=True)
        
        # Stop the event loop
        if self._loop and self._loop.is_running():
            logger.info("Stopping event loop...")
            try:
                self._loop.call_soon_threadsafe(self._stop_loop)
                logger.info("Stop request sent to event loop")
            except Exception as e:
                logger.error(f"Error stopping event loop: {e}", exc_info=True)
        else:
            logger.warning("Event loop not running, no need to stop it")
        
        # Signal the keep-alive thread to exit
        logger.info("Signaling keep-alive thread to exit")
        self._main_thread_exit.set()
    
    def _stop_loop(self):
        """Stop the asyncio event loop"""
        self._loop.stop()

    def _start_keep_alive_thread(self):
        """Start a thread that keeps the program alive until explicitly stopped"""
        def keep_alive():
            logger.info("Keep-alive thread started - application will remain running")
            self._main_thread_exit.wait()
            logger.info("Keep-alive thread ending - allowing application to exit")
            
        thread = threading.Thread(target=keep_alive, name="KeepAliveThread", daemon=False)
        thread.start()
        
    @classmethod
    def start(cls):
        if not cls._thread:
            cls._thread = threading.Thread(target=cls._run_event_loop, name="RunEventLoop")
            cls._thread.daemon = True
            cls._thread.start()

    @classmethod
    def _run_event_loop(cls):
        try:
            logger.info("Creating new event loop")
            cls._loop = asyncio.new_event_loop()
            asyncio.set_event_loop(cls._loop)
            logger.info("Event loop created and set")
            cls._loop_ready.set()
            logger.info("Starting event loop forever")
            cls._loop.run_forever()
        except Exception as e:
            logger.error(f"Event loop error: {e}", exc_info=True)
        finally:
            if cls._loop and cls._loop.is_running():
                logger.info("Closing event loop")
                cls._loop.close()
            cls._loop = None
            cls._loop_ready.clear()
            logger.info("Event loop stopped")

    def _start_server(self):
        """Start WebSocket server and wait for it to be ready"""
        import socket
        # Check if server is already running
        try:
            with socket.create_connection(("localhost", config.websocket.port), timeout=1):
                logger.info("WebSocket server already running, using existing instance")
                return
        except Exception:
            pass
        server_script = os.path.join(os.path.dirname(__file__), 'network', 'ws_server.py')
        logger.info(f"WebSocket server script path: {server_script}")
        logger.info(f"Python executable: {sys.executable}")
        
        process = self._start_process(
            'WebSocketServer',
            [sys.executable, "-Xfrozen_modules=off", server_script]
        )
        
        if not process:
            logger.error("Failed to start WebSocket server process")
            raise RuntimeError("Failed to start WebSocket server")
            
        logger.info(f"WebSocket server process started with PID: {process.pid}")
        self._wait_for_server()
        logger.info("WebSocket server is ready")

    def _start_process(self, name: str, args: list) -> Optional[subprocess.Popen]:
        try:
            logger.info(f"Starting process {name} with command: {' '.join(args)}")
            process = subprocess.Popen(
                args,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                bufsize=1,
                universal_newlines=True,
                start_new_session=True
            )
            
            logger.info(f"Process {name} started with PID: {process.pid}")
            
            threading.Thread(
                target=self._monitor_output,
                args=(process.stdout, name),
                name=f"MonitorOutput_{name}",
                daemon=True
            ).start()
            
            self.processes[name] = process
            return process
        except Exception as e:
            logger.error(f"Failed to start {name}: {str(e)}", exc_info=True)
            return None

    @classmethod
    def cleanup(cls):
        """Public interface to clean up resources before exit"""
        if cls._instance:
            cls._instance._cleanup()
        else:
            logger.info("No instance to cleanup")

    async def _init_client(self):
        try:
            logger.info("Creating WebSocket client")
            ws_client = WebSocketClient()
            event_base.set_ws_client(ws_client)

            logger.info(f"Connecting to WebSocket server on port {config.websocket.port}")
            await ws_client.connect()
            logger.info("Waiting for WebSocket server to be ready")
            await ws_client.wait_for_ready()
            logger.info("WebSocket client connected")
            
            if ws_client.client_id:
                logger.info(f"Received client ID: {ws_client.client_id}")
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
        logger.info(f"Launching browser with script: {browser_script}")
        logger.info(f"Client ID for browser: {client_id}")
        self._start_process(
            'Browser',
            [sys.executable, "-Xfrozen_modules=off", browser_script, client_id]
        )

    def _wait_for_server(self, timeout=10, check_interval=0.5):
        import socket
        start_time = time.time()
        logger.info(f"Waiting for WebSocket server to be ready on port {config.websocket.port}, timeout={timeout}s")
        while time.time() - start_time < timeout:
            try:
                logger.debug(f"Attempting to connect to localhost:{config.websocket.port}")
                with socket.create_connection(("localhost", config.websocket.port), timeout=1):
                    logger.info(f"Successfully connected to WebSocket server after {time.time() - start_time:.2f}s")
                    return True
            except (socket.timeout, ConnectionRefusedError) as e:
                logger.debug(f"Connection attempt failed: {str(e)}, retrying in {check_interval}s")
                time.sleep(check_interval)
        
        logger.error(f"Server failed to start within timeout of {timeout}s")
        raise TimeoutError("Server failed to start within timeout")

    def _monitor_output(self, pipe, prefix):
        try:
            logger.info(f"Started output monitoring for {prefix}")
            for line in iter(pipe.readline, ''):
                line = line.strip()
                if line:
                    logger.info(f"[{prefix}] {line}")
        except Exception as e:
            logger.error(f"Output monitoring error for {prefix}: {e}", exc_info=True)
        finally:
            logger.info(f"Output monitoring for {prefix} has ended")
            pipe.close()

    @staticmethod
    def _get_caller_info() -> str:
        """Get information about the calling module"""
        try:
            main_module = sys.modules['__main__']
            if hasattr(main_module, '__file__'):
                main_file = os.path.abspath(main_module.__file__)
                launcher_file = os.path.abspath(__file__)
                logger.info(f"Main module file: {main_file}")
                logger.info(f"Launcher file: {launcher_file}")
                if main_file != launcher_file:
                    return main_file
        except Exception as e:
            logger.error(f"Error getting caller info: {e}", exc_info=True)
        return None