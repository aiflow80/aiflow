from collections import deque
import time
from aiflow import logger
import threading
from datetime import datetime


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
        self._processing = False
        self._ready = threading.Event()
        self.state = {}

    def set_ws_client(self, client):
        self._ws_client = client

    def set_caller_file(self, caller_file):
        self.caller_file = caller_file

    async def handle_message(self, message):
        self.last_message = message.get("payload")
        self.previous_sender_id = self.sender_id
        self.sender_id = message.get("sender_id")
        self.session_id = message.get("client_id")

        if self.previous_sender_id and self.previous_sender_id != self.sender_id:
            self.events_store.clear()  
            self.events.clear()        
            self.state.clear()

        if self.sender_id:
            response = {
                "type": "paired",
                "payload": {
                    "message": "stream_start",
                    "client_id": self.sender_id,
                    "session_id": self.session_id,
                    "time_stamp": datetime.now().strftime("%H:%M:%S.%f")[:-3],
                },
            }

            # Use the async version since we're in an async context
            await self.send_response_async(response)

            if self.paired:
                if message.get("type") == "events":
                    self.events_store["payload"] = message.get("payload")
                    # Store event values by ID for easy retrieval
                    form_events = self.events_store.get('payload').get("formEvents", [])
                    if form_events:
                        for event_id in form_events:
                            event_data = form_events[event_id]
                            if "value" in event_data:
                                self.events[event_id] = event_data["value"]

                    file_event = self.events_store.get('payload').get("fileEvent", [])
                    if file_event:
                        event_id = self.events_store.get('payload').get("key")
                        self.events[event_id] = file_event


                # Reset MUI state before running the module again
                self.reset_mui_state()
                # Run the caller file when already paired and do not reexecute it for the first time
                if self.caller_file:
                    # Run in a separate thread to avoid event loop conflicts
                    self.is_rerun = True
                    self._run_module_in_thread(self.caller_file)
            else:
                self.paired = True

            # Mark as ready after first message is processed
            self._ready.set()

    def _run_module_in_thread(self, module_path):
        """Run the module in a separate thread to avoid event loop conflicts"""

        def _run():
            try:
                from aiflow.events.run import run_module

                run_module(module_path, method="importlib")

                response = {
                    "type": "paired",
                    "payload": {
                        "message": "stream_end",
                        "client_id": self.sender_id,
                        "session_id": self.session_id,
                        "time_stamp": datetime.now().strftime("%H:%M:%S.%f")[:-3],
                    },
                }
                self.send_response_sync(response)
            except Exception as e:
                logger.error(f"Error running module {module_path}: {e}")

        # Start a new thread to run the module
        thread = threading.Thread(target=_run, name="ModuleRunner", daemon=True)
        thread.start()

    def send_response_sync(self, payload):
        """Send a response synchronously, for use from synchronous code"""
        if self._ws_client:
            self._processing = True
            try:
                self._ws_client.send_sync(payload, self.sender_id)
            except Exception as e:
                logger.error(f"Failed to send response synchronously: {e}")
            finally:
                self._processing = False
        else:
            self.queue_message(payload)

    async def send_response_async(self, payload):
        try:
            await self._ws_client.send(payload, self.sender_id)
        except Exception as e:
            logger.error(f"Failed to send response asynchronously: {e}")

    def send_component_update(self, component_dict):
        payload = {
            "type": "component_update",
            "payload": {"component": component_dict, "timestamp": time.time()},
        }
        self.send_response(payload)

    async def send_component_update_async(self, component_dict):
        payload = {
            "type": "component_update",
            "payload": {
                "component": component_dict,
            },
        }
        await self.send_response_async(payload)

    def send_response(self, payload):
        self.send_response_sync(payload)

    def get_message_info(self):
        return {
            "last_message": self.last_message,
            "sender_id": self.sender_id,
            "session_id": self.session_id,
        }

    def wait_until_ready(self, timeout=30):
        return self._ready.wait(timeout=timeout)

    def is_ready(self):
        return self._ready.is_set()

    def reset_mui_state(self):
        from aiflow.mui import mui
        mui.reset()

event_base = EventBase()
