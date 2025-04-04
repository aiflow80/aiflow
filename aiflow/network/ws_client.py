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

class ChunkTracker:
    def __init__(self):
        self.chunks = {}  # { message_id: { total_chunks, received_chunks, data, sender_id } }
        self._cleanup_lock = threading.Lock()
        self._last_activity = {}  # Track last activity for each chunked message

    def add_chunk(self, message_id, chunk_index, total_chunks, chunk_data, sender_id):
        with self._cleanup_lock:
            if message_id not in self.chunks:
                logger.info(f"Starting new chunked message with ID {message_id}, expecting {total_chunks} chunks")
                self.chunks[message_id] = {'total_chunks': total_chunks,'received_chunks': {},'data': {},'sender_id': sender_id,'timestamp': time.time()}
            self.chunks[message_id]['received_chunks'][chunk_index] = True
            self.chunks[message_id]['data'][chunk_index] = chunk_data
            self._last_activity[message_id] = time.time()
            return self.is_complete(message_id)
    
    def is_complete(self, message_id):
        if message_id not in self.chunks: 
            return False
        message_data = self.chunks[message_id]
        return len(message_data['received_chunks']) == message_data['total_chunks']
    
    def get_complete_message(self, message_id):
        if not self.is_complete(message_id): 
            return None, None
        message_data = self.chunks[message_id]
        sorted_chunks = [message_data['data'][i] for i in range(message_data['total_chunks'])]
        first_chunk = sorted_chunks[0]
        if (first_chunk.get('payload').get('type') == 'file-change' and first_chunk.get('payload').get('fileEvent')):
            combined_base64 = "".join(chunk['payload']['fileEvent']['data'] for chunk in sorted_chunks)
            # Use a shallow copy instead of json reserialization to avoid evaluation errors
            complete_message = first_chunk.copy()
            complete_message['payload']['fileEvent']['data'] = combined_base64
            with self._cleanup_lock:
                sender_id = message_data['sender_id']
                del self.chunks[message_id]
                if message_id in self._last_activity:
                    del self._last_activity[message_id]
            return complete_message, sender_id
        return None, None
    
    def cleanup_old_chunks(self, max_age_seconds=300):
        with self._cleanup_lock:
            current_time = time.time()
            message_ids = list(self.chunks.keys())
            for message_id in message_ids:
                chunk_data = self.chunks[message_id]
                last_activity = self._last_activity.get(message_id, chunk_data['timestamp'])
                if current_time - last_activity > max_age_seconds:
                    logger.warning(f"Removing stale chunked message {message_id}: received {len(chunk_data['received_chunks'])}/{chunk_data['total_chunks']} chunks")
                    del self.chunks[message_id]
                    if message_id in self._last_activity:
                        del self._last_activity[message_id]

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
        self.chunk_tracker = ChunkTracker()  # New instance of ChunkTracker
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
            if message.get('type') == 'chunked_message':
                message_id = message.get('messageId')
                # Ensure chunk_index, total_chunks, and payload are present
                chunk_index = message.get('chunkIndex')
                total_chunks = message.get('totalChunks')
                payload = message.get('payload')
                sender_id = message.get('client_id')  # Assume sender identity is passed in the message
                if message_id and chunk_index is not None and total_chunks and payload:
                    is_complete = self.chunk_tracker.add_chunk(message_id, chunk_index, total_chunks, payload, sender_id)
                    if is_complete:
                        logger.info(f"All chunks received for message ID {message_id}, reassembling")
                        complete_message, _ = self.chunk_tracker.get_complete_message(message_id)
                        if complete_message:
                            await event_base.handle_message(complete_message)
                return
            # For non-chunked messages
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
            message_str = json.dumps(payload)
            logger.debug(f"Sending message of size {len(message_str) / (1024 * 1024):.2f} MB")
            THRESHOLD = 1_000_000
            if len(message_str) > THRESHOLD:
                logger.warning("Large message detected, which may trigger Tornado write issues. Consider using chunked messages.")
                # ...optionally implement chunked sending logic here...
            # Use message_str instead of payload
            await self.client.write_message(message_str)
            logger.info("Write message completed")
        except WebSocketClosedError:
            await self.connect(force_reconnect=True)
            await self.send(payload, target)
        except Exception as e:
            logger.error(f"Failed to send message: {str(e)}")
            raise

    def send_sync(self, payload: dict, target: str):
        try:
            loop = asyncio.get_running_loop()
            return asyncio.run_coroutine_threadsafe(self.send(payload, target), loop).result()
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

