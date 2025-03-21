import json
import asyncio
import threading
from typing import Optional
from tornado.websocket import websocket_connect, WebSocketClosedError
from aiflow.logger import setup_logger
from aiflow.config import config
from aiflow.events import event_base

logger = setup_logger('WebSocketClient')

class WebSocketClient:
    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super().__new__(cls)
                cls._instance._init()
            return cls._instance

    def _init(self):
        self.client = None
        self.client_id = None
        self._connected = asyncio.Event()
        self._ready = asyncio.Event()
        self._running = True
        self._message_handlers = {}
        threading.Thread(target=self._start_asyncio_loop, name="WSClientInit", daemon=False).start()

    def _start_asyncio_loop(self):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(self.connect())
            loop.run_until_complete(self._run_event_loop())
        except Exception as e:
            logger.error(f"WebSocket client loop failed: {e}")
        finally:
            loop.close()

    async def _run_event_loop(self):
        while self._running:
            await asyncio.sleep(1)

    def register_handler(self, message_type: str, callback):
        self._message_handlers[message_type] = callback

    async def _handle_message(self, message):
        try:
            if isinstance(message, str):
                message = json.loads(message)
            await event_base.handle_message(message)
        except Exception as e:
            logger.error(f"Error processing message: {e}")

    async def _listen_messages(self):
        while self._connected.is_set():
            try:
                message = await self.client.read_message()
                if message:
                    await self._handle_message(message)
                else:
                    break
            except Exception as e:
                logger.error(f"Error reading message: {e}")
                break
                
        # Connection lost
        self._connected.clear()
        self._ready.clear()
        await self.connect(force_reconnect=True)

    async def connect(self, force_reconnect=False):
        if force_reconnect:
            await self.close()
        if self._connected.is_set() and self.client and not self.client.close_code:
            return

        for attempt in range(config.websocket.retry_max_attempts):
            try:
                if attempt > 0:
                    delay = min(config.websocket.retry_base_delay * (2 ** attempt), 
                              config.websocket.retry_max_delay)
                    await asyncio.sleep(delay)

                self.client = await websocket_connect(
                    f"ws://{config.websocket.host}:{config.websocket.port}/ws",
                    connect_timeout=config.websocket.connection_timeout
                )
                
                data = json.loads(await self.client.read_message())
                self.client_id = data['client_id']
                self._connected.set()
                self._ready.set()
                asyncio.create_task(self._listen_messages())
                return
            except Exception as e:
                logger.error(f"Connection attempt {attempt + 1} failed: {str(e)}")
        
        raise ConnectionError("Max retry attempts reached")

    async def wait_for_ready(self, timeout=10):
        await asyncio.wait_for(self._ready.wait(), timeout=timeout)

    async def send(self, payload: dict, targets: list = None):
        try:
            await self.connect()
            await self.client.write_message(payload)
        except WebSocketClosedError:
            await self.connect(force_reconnect=True)
            await self.send(payload, targets)
        except Exception as e:
            logger.error(f"Failed to send message: {str(e)}")
            raise

    def send_sync(self, payload: dict, targets: list = None):
        """Synchronous version of send that can be called from any thread"""
        try:
            # Check if we're already in an event loop
            try:
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    # We're in an event loop, create a new future and run it properly
                    future = asyncio.run_coroutine_threadsafe(self.send(payload, targets), loop)
                    return future.result()
                else:
                    # Loop exists but isn't running
                    return loop.run_until_complete(self.send(payload, targets))
            except RuntimeError:
                # No event loop in this thread, create a new one
                loop = asyncio.new_event_loop()
                try:
                    return loop.run_until_complete(self.send(payload, targets))
                finally:
                    loop.close()
        except Exception as e:
            logger.error(f"Failed to send message synchronously: {str(e)}")
            raise
            
    async def close(self):
        self._running = False
        self._connected.clear()
        self._ready.clear()
        if self.client:
            self.client.close()
            self.client = None
            self.client_id = None

    async def __aenter__(self):
        await self.connect()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()

client = WebSocketClient()
event_base.set_ws_client(client)