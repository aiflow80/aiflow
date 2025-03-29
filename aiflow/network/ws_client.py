import json
import asyncio
import threading
import time
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
        self._init_thread = threading.Thread(target=self._start_asyncio_loop, name="Client", daemon=True)
        self._init_thread.start()
        
        # Wait for the client to initialize before returning
        start_time = time.time()
        while not self._ready.is_set() and time.time() - start_time < 10:
            time.sleep(0.1)
        
        if not self._ready.is_set():
            logger.warning("WebSocketClient initialization may not be complete after timeout")

    def _start_asyncio_loop(self):
        loop = asyncio.new_event_loop()
        self._loop = loop  # store reference to the loop for shutdown control
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(self.connect())
            loop.run_until_complete(self._run_event_loop())
        except Exception as e:
            # logger.error(f"WebSocket client loop failed: {e}")
            pass
        finally:
            loop.close()

    async def _run_event_loop(self):
        while self._running:
            if not self._connected.is_set():
                try:
                    await self.connect(force_reconnect=True)
                except Exception as e:
                    logger.error(f"Reconnection attempt failed: {e}")
                    await asyncio.sleep(2)  # Prevent rapid reconnection attempts
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
                
        # Connection lost: shut down the client properly
        logger.warning("Connection lost, shutting down client")
        await self.close()

    async def connect(self, force_reconnect=False):
        # Add lock to prevent multiple simultaneous connection attempts
        connect_lock = asyncio.Lock()
        async with connect_lock:
            if force_reconnect:
                await self.close()
            
            if self._connected.is_set() and self.client and not self.client.close_code:
                return

            for attempt in range(config.websocket.retry_max_attempts):
                try:
                    if attempt > 0:
                        delay = min(config.websocket.retry_base_delay * (2 ** attempt), 
                                config.websocket.retry_max_delay)
                        logger.info(f"Retrying connection in {delay} seconds (attempt {attempt+1})")
                        await asyncio.sleep(delay)

                    self.client = await websocket_connect(
                        f"ws://{config.websocket.host}:{config.websocket.port}/ws",
                        connect_timeout=config.websocket.connection_timeout
                    )
                    
                    data = json.loads(await self.client.read_message())
                    self.client_id = data['client_id']
                    
                    self._connected.set()
                    self._ready.set()
                    
                    # Start message listener in a new task
                    asyncio.create_task(self._listen_messages())
                    return
                except Exception as e:
                    logger.error(f"Connection attempt {attempt + 1} failed: {str(e)}")
            
            raise ConnectionError("Max retry attempts reached")

    async def wait_for_ready(self, timeout=10):
        await asyncio.wait_for(self._ready.wait(), timeout=timeout)

    async def send(self, payload: dict, target: str):
        try:
            await self.connect()
            payload['client_id'] = target
            await self.client.write_message(payload)
        except WebSocketClosedError:
            await self.connect(force_reconnect=True)
            await self.send(payload, target)
        except Exception as e:
            logger.error(f"Failed to send message: {str(e)}")
            raise

    def send_sync(self, payload: dict, target: str):
        try:
            # Check if we're already in an event loop
            try:
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    future = asyncio.run_coroutine_threadsafe(self.send(payload, target), loop)
                    return future.result()
                else:
                    return loop.run_until_complete(self.send(payload, target))
            except RuntimeError:
                loop = asyncio.new_event_loop()
                try:
                    return loop.run_until_complete(self.send(payload, target))
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
        # Signal the loop to stop if it's running
        if hasattr(self, "_loop") and self._loop.is_running():
            self._loop.call_soon_threadsafe(self._loop.stop)

    async def __aenter__(self):
        await self.connect()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()

