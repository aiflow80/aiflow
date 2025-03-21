import asyncio
from collections import deque
from aiflow import logger
import threading

class EventBase:
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._init()
        return cls._instance

    def _init(self):
        self.last_message = None
        self.sender_id = None
        self.session_id = None
        self._ws_client = None
        self.caller_file = None
        self.paired = False
        self.message_queue = deque()
        self._processing = False
        self._ready = threading.Event()

    def set_ws_client(self, client):
        self._ws_client = client
    
    def set_caller_file(self, caller_file):
        self.caller_file = caller_file
        
    async def handle_message(self, message):
        self.last_message = message.get('payload')
        self.sender_id = message.get('sender_id')
        self.session_id = message.get('client_id')

        if self.sender_id:
            response = {
                "type": "message",
                "client_id": self.sender_id,
                "sender_id": self.session_id,
                "payload": f"Received your message: {self.last_message}"
            }
            await self.send_response(response)

            if self.paired:
                logger.info(f"Refresh session: {self.session_id} client: {self.sender_id}")
                # Run the caller file when already paired and do not reexecute it for the first time
                if self.caller_file:
                    from aiflow.events.run import run_module
                    # Use threaded=True to ensure timing operations work correctly
                    run_module(self.caller_file, method='importlib')
            else:
                self.paired = True
                logger.info(f"Paired session: {self.session_id} with client: {self.sender_id}")
                
            # Mark as ready after first message is processed
            self._ready.set()

    def queue_message(self, payload):
        self.message_queue.append(payload)
            
    def send_response_sync(self, payload):
        if self._ws_client:
            self._processing = True
            try:
                # Handle the case where we might already be in an event loop
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    # Create a future and run the coroutine in the background
                    # Use asyncio.create_task to schedule the coroutine
                    asyncio.create_task(self.send_response(payload))
                else:
                    # If no loop is running, we can use asyncio.run
                    asyncio.run(self.send_response(payload))
            except RuntimeError:
                # Fallback for when we can't get a loop or it's closed
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                loop.run_until_complete(self.send_response(payload))
            finally:
                self._processing = False
        else:
            self.queue_message(payload)

    async def send_response(self, payload):
        try:
            await self._ws_client.send(payload)
        except Exception as e:
            logger.error(f"Failed to send response: {e}")
            self.queue_message(payload)

    def get_message_info(self):
        return {
            'last_message': self.last_message,
            'sender_id': self.sender_id,
            'session_id': self.session_id
        }
    
    def wait_until_ready(self, timeout=30):
        """Wait until the EventBase has processed all messages and is ready."""
        return self._ready.wait(timeout=timeout)
    
    def is_ready(self):
        """Check if EventBase is ready."""
        return self._ready.is_set()

event_base = EventBase()
