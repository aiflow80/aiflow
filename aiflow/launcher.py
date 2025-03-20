import asyncio
import atexit
import inspect
import os
import subprocess
import sys
import threading
from contextlib import suppress
import time
from typing import Optional
from aiflow.network.ws_client import client as ws_client
from aiflow.logger import setup_logger
from aiflow.config import config

logger = setup_logger('Launcher')

class Launcher:
    # Class variables
    _instance: Optional['Launcher'] = None
    _loop: Optional[asyncio.AbstractEventLoop] = None
    _thread: Optional[threading.Thread] = None
    _websocket_process: Optional[subprocess.Popen] = None
    _lock = threading.Lock()
    _loop_ready = threading.Event()

    # Singleton implementation
    def __new__(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super().__new__(cls)
                cls._instance._init_resources()
            return cls._instance

    # Core initialization and lifecycle methods
    def _init_resources(self):
        logger.info("Initializing Launcher resources...")
        self.running = True
        self.processes = {}
        self._setup_signal_handlers()
        self.caller_file = self._get_caller_info()
        
        self._start_server_process()
        self._wait_for_server()
        
        logger.info("Starting event loop thread...")
        self.start()
        
        if not self._loop_ready.wait(timeout=10):
            raise RuntimeError("Event loop initialization timeout")
            
        self._client_ready = threading.Event()
        logger.info("Initializing client and browser...")
        asyncio.run_coroutine_threadsafe(self._init_client(), self._loop)
        try:
            self._client_ready.wait(timeout=10)
            logger.info("Initialization completed")
        except Exception as e:
            logger.error(f"Initialization failed: {str(e)}", exc_info=True)

    @classmethod
    def start(cls):
        if not cls._thread:
            logger.info("Starting main event loop in background thread...")
            cls._thread = threading.Thread(target=cls._run_event_loop)
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

    # Process management methods
    def _start_server_process(self):
        server_script = os.path.join(os.path.dirname(__file__), 'network', 'ws_server.py')
        try:
            process = self._start_process(
                'WebSocketServer',
                [sys.executable, "-Xfrozen_modules=off", server_script]
            )
            logger.info("WebSocket server process started")
            return process
        except Exception as e:
            logger.error(f"Failed to start server process: {e}")
            raise

    def _start_process(self, name: str, args: list):
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

    # Client and browser methods
    async def _init_client(self):
        try:
            await ws_client.connect()
            await ws_client.wait_for_ready()
            logger.info("WebSocket client connected successfully")
            
            if ws_client.client_id:
                self._launch_browser(ws_client.client_id)
                self._client_ready.set()
            else:
                logger.error("Client ID not available, cannot launch browser")
                return False
            
            while self.running:
                await asyncio.sleep(1)
        except Exception as e:
            logger.error(f"Client initialization failed: {e}")
            return False
        return True

    def _launch_browser(self, client_id: str):
        browser_script = os.path.join(os.path.dirname(__file__), 'network', 'browser.py')
        logger.info(f"Launching browser with client_id: {client_id}")
        try:
            self._start_process(
                'Browser',
                [sys.executable, "-Xfrozen_modules=off", browser_script, client_id]
            )
            logger.info("Browser process started successfully")
        except Exception as e:
            logger.error(f"Failed to launch browser: {e}", exc_info=True)

    # Utility methods
    def _wait_for_server(self, timeout=10, check_interval=0.5):
        import socket
        start_time = time.time()
        while time.time() - start_time < timeout:
            try:
                with socket.create_connection(("localhost", config.websocket.port), timeout=1):
                    logger.info("Server is available")
                    return True
            except (socket.timeout, ConnectionRefusedError):
                logger.debug("Server not yet available, retrying...")
                time.sleep(check_interval)
        raise TimeoutError("Server failed to start within timeout")

    def _monitor_output(self, pipe, prefix):
        try:
            for line in iter(pipe.readline, ''):
                line = line.strip()
                if line:
                    logger.info(f"[{prefix}] {line}")
        except Exception as e:
            logger.error(f"Error monitoring {prefix} output: {e}")
        finally:
            pipe.close()

    @staticmethod
    def _get_caller_info() -> str:
        try:
            main_module = sys.modules['__main__']
            if hasattr(main_module, '__file__'):
                main_file = os.path.abspath(main_module.__file__)
                launcher_file = os.path.abspath(__file__)
                if main_file != launcher_file:
                    return main_file
        except Exception as e:
            logger.debug(f"Error finding caller info: {e}")
        
        return 'unknown'

    def _setup_signal_handlers(self):
        import signal
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)

    def _signal_handler(self, signum, frame):
        logger.info(f"Received signal {signum}")
        self.cleanup()
        sys.exit(0)

    # Cleanup and context management
    def cleanup(self):
        logger.info("Starting cleanup...")
        self.running = False

        if self._loop:
            asyncio.run_coroutine_threadsafe(
                ws_client.close(), 
                self._loop
            ).result(timeout=5)
            self._loop.stop()

        for name, process in self.processes.items():
            try:
                logger.info(f"Terminating {name}...")
                process.terminate()
                process.wait(timeout=5)
            except Exception as e:
                logger.error(f"Error cleaning up {name}: {str(e)}")
            
        logger.info("Cleanup completed")

    def keep_alive(self):
        try:
            while self.running:
                time.sleep(1)
        except KeyboardInterrupt:
            self.cleanup()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.cleanup()

    def __del__(self):
        self.cleanup()