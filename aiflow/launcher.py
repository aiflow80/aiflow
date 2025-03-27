import asyncio
import os
import subprocess
import sys
import threading
import time
import signal
import atexit
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
        self.running = True
        self.processes: Dict[str, subprocess.Popen] = {}
        self.caller_file = self._get_caller_info()
        
        # Start server monitoring thread
        self._start_server_monitor()
        
        # Start event loop thread
        self.start()
        if not self._loop_ready.wait(timeout=10):
            raise RuntimeError("Event loop initialization timeout")
        
        # Start server and wait for it to be ready
        self._start_server()
        
        # Initialize client and launch browser
        self._client_ready = threading.Event()
        asyncio.run_coroutine_threadsafe(self._init_client(), self._loop)
        if not self._client_ready.wait(timeout=30):
            raise RuntimeError("Client initialization timeout")

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
            return  # Already cleaning up
        
        self.running = False
        logger.info("Cleaning up resources...")
        
        # Close WebSocket client if it exists
        if hasattr(event_base, 'ws_client') and event_base.ws_client:
            try:
                if self._loop and self._loop.is_running():
                    asyncio.run_coroutine_threadsafe(
                        event_base.ws_client.close(), self._loop
                    )
            except Exception as e:
                logger.error(f"Error closing WebSocket client: {e}")
        
        # Kill all child processes
        for name, process in list(self.processes.items()):
            try:
                logger.info(f"Terminating {name}...")
                if process.poll() is None:
                    process.kill()
            except Exception as e:
                logger.error(f"Error killing {name}: {e}")
        
        # Stop the event loop
        if self._loop and self._loop.is_running():
            logger.info("Stopping event loop...")
            try:
                self._loop.call_soon_threadsafe(self._stop_loop)
            except Exception as e:
                logger.error(f"Error stopping event loop: {e}")
        
        # Signal the keep-alive thread to exit
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
            logger.info("Event loop stopped")

    def _start_server(self):
        """Start WebSocket server and wait for it to be ready"""
        server_script = os.path.join(os.path.dirname(__file__), 'network', 'ws_server.py')
        
        process = self._start_process(
            'WebSocketServer',
            [sys.executable, "-Xfrozen_modules=off", server_script]
        )
        
        if not process:
            raise RuntimeError("Failed to start WebSocket server")
            
        self._wait_for_server()
        logger.info("WebSocket server is ready")

    def _start_process(self, name: str, args: list) -> Optional[subprocess.Popen]:
        try:
            process = subprocess.Popen(
                args,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                bufsize=1,
                universal_newlines=True,
                start_new_session=True
            )
            
            threading.Thread(
                target=self._monitor_output,
                args=(process.stdout, name),
                name="MonitorOuputFromProcess",
                daemon=True
            ).start()
            
            self.processes[name] = process
            return process
        except Exception as e:
            logger.error(f"Failed to start {name}: {str(e)}")
            return None

    async def _init_client(self):
        try:
            ws_client = WebSocketClient()
            event_base.set_ws_client(ws_client)

            await ws_client.connect()
            await ws_client.wait_for_ready()
            logger.info("WebSocket client connected")
            
            if ws_client.client_id:
                self._launch_browser(ws_client.client_id)
                self._client_ready.set()
            else:
                logger.error("No client ID available")
                return False
            
            while self.running:
                await asyncio.sleep(3)
        except Exception as e:
            logger.error(f"Client error: {e}")
            return False
        return True

    def _launch_browser(self, client_id: str):
        browser_script = os.path.join(os.path.dirname(__file__), 'network', 'browser.py')
        self._start_process(
            'Browser',
            [sys.executable, "-Xfrozen_modules=off", browser_script, client_id]
        )

    def _wait_for_server(self, timeout=10, check_interval=0.5):
        import socket
        start_time = time.time()
        while time.time() - start_time < timeout:
            try:
                with socket.create_connection(("localhost", config.websocket.port), timeout=1):
                    return True
            except (socket.timeout, ConnectionRefusedError):
                time.sleep(check_interval)
        raise TimeoutError("Server failed to start within timeout")

    def _monitor_output(self, pipe, prefix):
        try:
            for line in iter(pipe.readline, ''):
                line = line.strip()
                if line:
                    logger.info(f"[{prefix}] {line}")
        except Exception as e:
            logger.error(f"Output monitoring error for {prefix}: {e}")
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
        except Exception:
            pass
        return None