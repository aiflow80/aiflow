import asyncio
import os
import subprocess
import sys
import threading
import time
import signal
from typing import Optional, Dict
from aiflow.network.ws_client import client as ws_client
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
        
        # Set up signal handlers for clean exit
        signal.signal(signal.SIGINT, self._exit_handler)
        signal.signal(signal.SIGTERM, self._exit_handler)
        
        # Start event loop thread
        self.start()
        if not self._loop_ready.wait(timeout=10):
            raise RuntimeError("Event loop initialization timeout")
        
        # Start server and wait for it to be ready
        self._start_server()
        
        # Initialize client and launch browser
        self._client_ready = threading.Event()
        asyncio.run_coroutine_threadsafe(self._init_client(), self._loop)
        if not self._client_ready.wait(timeout=10):
            raise RuntimeError("Client initialization timeout")
        
        logger.info("Launcher initialization completed")

    @classmethod
    def start(cls):
        if not cls._thread:
            logger.info("Starting event loop thread...")
            cls._thread = threading.Thread(target=cls._run_event_loop)
            cls._thread.daemon = True
            cls._thread.start()

    @classmethod
    def _run_event_loop(cls):
        try:
            cls._loop = asyncio.new_event_loop()
            asyncio.set_event_loop(cls._loop)
            cls._loop_ready.set()
            logger.info("Event loop started")
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
        logger.info("Starting WebSocket server...")
        
        process = self._start_process(
            'WebSocketServer',
            [sys.executable, "-Xfrozen_modules=off", server_script]
        )
        
        if not process:
            raise RuntimeError("Failed to start WebSocket server")
            
        # Wait for server to be available
        self._wait_for_server()
        logger.info("WebSocket server is ready")

    def _start_process(self, name: str, args: list) -> Optional[subprocess.Popen]:
        """Start a new process and monitor its output"""
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
                daemon=True
            ).start()
            
            self.processes[name] = process
            return process
        except Exception as e:
            logger.error(f"Failed to start {name}: {str(e)}")
            return None

    async def _init_client(self):
        """Initialize WebSocket client and launch browser"""
        try:
            await ws_client.connect()
            await ws_client.wait_for_ready()
            logger.info("WebSocket client connected")
            
            if ws_client.client_id:
                self._launch_browser(ws_client.client_id)
                self._client_ready.set()
            else:
                logger.error("No client ID available")
                return False
            
            # Keep running
            while self.running:
                await asyncio.sleep(1)
        except Exception as e:
            logger.error(f"Client error: {e}")
            return False
        return True

    def _launch_browser(self, client_id: str):
        """Launch browser process"""
        browser_script = os.path.join(os.path.dirname(__file__), 'network', 'browser.py')
        logger.info(f"Launching browser with client_id: {client_id}")
        self._start_process(
            'Browser',
            [sys.executable, "-Xfrozen_modules=off", browser_script, client_id]
        )

    def _wait_for_server(self, timeout=10, check_interval=0.5):
        """Wait for the server to be available"""
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
        """Monitor and log process output"""
        try:
            for line in iter(pipe.readline, ''):
                line = line.strip()
                if line:
                    logger.info(f"[{prefix}] {line}")
        except Exception as e:
            logger.error(f"Output monitoring error for {prefix}: {e}")
        finally:
            pipe.close()

    def _exit_handler(self, signum, frame):
        """Handle exit signals gracefully"""
        logger.info(f"Received signal {signum}, shutting down...")
        self.running = False
        
        # Terminate all child processes
        for name, process in self.processes.items():
            logger.info(f"Terminating {name}...")
            try:
                if process.poll() is None:
                    process.terminate()
            except Exception as e:
                logger.error(f"Error terminating {name}: {e}")
        
        # Exit with a slight delay to allow cleanup
        threading.Thread(target=lambda: (time.sleep(0.5), os._exit(0))).start()

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
        return 'unknown'