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
        threading.Thread(target=self._background_init, name="WSClientInit", daemon=False).start()

    def _background_init(self):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(self.connect())
            while self._running:
                loop.run_until_complete(asyncio.sleep(1))
        except Exception as e:
            logger.error(f"Background initialization failed: {e}")
        finally:
            loop.close()

    def register_handler(self, message_type: str, callback):
        self._message_handlers[message_type] = callback

    async def _handle_message(self, message):
        try:
            if isinstance(message, str):
                message = json.loads(message)
            await event_base.pair(message)
        except Exception as e:
            logger.error(f"Error processing message: {e}")

    def on_message(self, message):
        """Handle incoming WebSocket messages"""
        # Create task to handle message asynchronously
        asyncio.create_task(self._handle_message(message))

    async def _listen_messages(self):
        while self._connected.is_set():
            try:
                if message := await self.client.read_message():
                    await self._handle_message(message)
                else:
                    break
            except Exception:
                break
        self._connected.clear()
        self._ready.clear()
        await self.connect(force_reconnect=True)

    async def connect(self, force_reconnect=False):
        if force_reconnect:
            await self.close()
        if self._connected.is_set() and self.client and not self.client.close_code:
            return

        attempt = 0
        while True:
            try:
                delay = min(config.websocket.retry_base_delay * (2 ** attempt), 
                          config.websocket.retry_max_delay)
                if attempt > 0:
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
                logger.info(f"Connected successfully with client ID: {self.client_id}")
                return
            except Exception as e:
                logger.error(f"Connection attempt {attempt + 1} failed: {str(e)}")
                if (attempt := attempt + 1) >= config.websocket.retry_max_attempts:
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

async def main():
    print("Starting WebSocket client...")
    
    async def handle_chat(message):
        print(f"Received chat message: {message}")
    
    try:
        client.register_handler('chat', handle_chat)
        
        print("Attempting to connect...")
        await client.connect()
        print(f"Successfully connected with client ID: {client.client_id}")
        
        await asyncio.sleep(60)
    except Exception as e:
        print(f"Failed to connect: {e}")
    finally:
        print("Closing connection...")
        await client.close()

if __name__ == "__main__":
    import time
    asyncio.run(main())