import asyncio
from collections import deque
import time
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
        self.events = {}
        self.events_store = {}
        self.paired = False
        self.message_queue = deque()
        self._processing = False
        self._ready = threading.Event()

    def set_ws_client(self, client):
        self._ws_client = client

    def set_caller_file(self, caller_file):
        self.caller_file = caller_file

    async def handle_message(self, message):
        self.last_message = message.get("payload")
        self.sender_id = message.get("sender_id")
        self.session_id = message.get("client_id")

        if self.sender_id:

            response = {
                "type": "paired",
                "payload": {
                    "status": "success",
                    "client_id": self.sender_id,
                    "session_id": self.session_id,
                    "timestamp": time.time()
                }
            }
            # Use the async version since we're in an async context
            await self.send_response_async(response)

            if self.paired:
                logger.info(
                    f"Refresh session: {self.session_id} client: {self.sender_id}"
                )

                if message.get("type") == "events":
                    self.events_store["events"] = message.get("payload")
                    # Store event values by ID for easy retrieval
                    form_events = self.events_store.get("formEvents", [])
                    for event_id in form_events:
                        event_data = form_events[event_id]
                        if "value" in event_data:
                            self.events[event_id] = event_data["value"]

                # Reset MUI state before running the module again
                self.reset_mui_state()
                # Run the caller file when already paired and do not reexecute it for the first time
                if self.caller_file:
                    # Run in a separate thread to avoid event loop conflicts
                    self.is_rerun = True
                    self._run_module_in_thread(self.caller_file)
            else:
                self.paired = True
                logger.info(
                    f"Paired session: {self.session_id} with client: {self.sender_id}"
                )

            # Mark as ready after first message is processed
            self._ready.set()

    def _run_module_in_thread(self, module_path):
        """Run the module in a separate thread to avoid event loop conflicts"""

        def _run():
            try:
                from aiflow.events.run import run_module

                run_module(module_path, method="runpy")
            except Exception as e:
                logger.error(f"Error running module {module_path}: {e}")

        # Start a new thread to run the module
        thread = threading.Thread(target=_run, name="ModuleRunner", daemon=True)
        thread.start()

    def queue_message(self, payload):
        self.message_queue.append(payload)

    def send_response_sync(self, payload):
        """Send a response synchronously, for use from synchronous code"""
        if self._ws_client:
            self._processing = True
            try:
                self._ws_client.send_sync(payload)
            except Exception as e:
                logger.error(f"Failed to send response synchronously: {e}")
                self.queue_message(payload)
            finally:
                self._processing = False
        else:
            self.queue_message(payload)

    async def send_response_async(self, payload):
        """Send a response asynchronously, for use from async code"""
        try:
            await self._ws_client.send(payload)
        except Exception as e:
            logger.error(f"Failed to send response asynchronously: {e}")
            self.queue_message(payload)

    # Main send method - choose sync by default
    def send_response(self, payload):
        """Default send method - synchronous by default"""
        self.send_response_sync(payload)

    def get_message_info(self):
        return {
            "last_message": self.last_message,
            "sender_id": self.sender_id,
            "session_id": self.session_id,
        }

    def wait_until_ready(self, timeout=30):
        """Wait until the EventBase has processed all messages and is ready."""
        return self._ready.wait(timeout=timeout)

    def is_ready(self):
        """Check if EventBase is ready."""
        return self._ready.is_set()

    def reset_mui_state(self):
        """Reset MUI builder state"""
        from aiflow.mui import mui

        mui.reset()
        logger.info("MUI builder state has been reset")


event_base = EventBase()
