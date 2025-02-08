import asyncio
from aiflow.logger import setup_logger

logger = setup_logger('EventBase')

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
        self._loop = None
        self._ws_client = None

    def set_ws_client(self, client):
        self._ws_client = client

    def store_message(self, message):
        self.last_message = message.get('payload')
        self.sender_id = message.get('sender_id')
        self.client_id = message.get('client_id')
        
        if self.sender_id:
            response = {
                "type": "message",
                "client_id": self.sender_id,
                "sender_id": self.client_id,
                "payload": f"Received your message: {self.last_message}"
            }
            self.send_response(response)

    async def _send_message_async(self, payload):
        if self._ws_client:
            await self._ws_client.send(payload, [self.sender_id])
            logger.info(f"Response sent to sender {self.sender_id}")

    def send_response(self, payload):
        if not self.sender_id or not self._ws_client:
            logger.warning("No sender_id or ws_client available to send response")
            return

        try:
            # Try to get the current event loop
            loop = asyncio.get_running_loop()
            # If we're in an async context, create a task
            asyncio.create_task(self._send_message_async(payload))
        except RuntimeError:
            # If we're in a synchronous context, run the coroutine directly
            asyncio.run(self._send_message_async(payload))

    def get_message_info(self):
        return {
            'last_message': self.last_message,
            'sender_id': self.sender_id,
            'session_id': self.session_id
        }

event_base = EventBase()
