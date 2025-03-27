import os
import asyncio
import json
import logging
import time
import uuid
import ssl
import threading
from tornado.web import Application, RequestHandler, StaticFileHandler
from tornado.websocket import WebSocketHandler

DEFAULT_CONFIG = {
    'websocket': {'host': '0.0.0.0', 'port': 8888, 'max_connections': 100},
    'security': {'ssl_cert_path': None, 'ssl_key_path': None}
}

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('WebSocketServer')
for log_name in ["tornado.access", "tornado.application", "tornado.general"]:
    logging.getLogger(log_name).setLevel(logging.WARNING)

class BaseHandler(RequestHandler):
    def set_default_headers(self):
        self.set_header("Access-Control-Allow-Origin", "*")
        self.set_header("Access-Control-Allow-Headers", "Content-Type")
        self.set_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.set_header("Content-Type", "application/json")

    def options(self):
        self.set_status(204)
        self.finish()

class ConnectionManager:
    def __init__(self):
        self.clients = {}
        self._connection_count = 0
        self._lock = threading.Lock()

    def add_client(self, client_id: str, client: WebSocketHandler) -> bool:
        with self._lock:
            if client_id in self.clients:
                self.remove_client(client_id)
            if self._connection_count >= DEFAULT_CONFIG['websocket']['max_connections']:
                return False
            self.clients[client_id] = client
            self._connection_count += 1
            return True

    def remove_client(self, client_id: str):
        with self._lock:
            if client_id in self.clients:
                try:
                    self.clients[client_id].close()
                except:
                    pass
                del self.clients[client_id]
                self._connection_count = max(0, self._connection_count - 1)

    async def send_to_client(self, client_id: str, message: str) -> bool:
        if client_id in self.clients:
            try:
                await self.clients[client_id].write_message(message)
                return True
            except Exception as e:
                logger.error(f"Send failed to {client_id}: {str(e)}")
        return False

    async def broadcast(self, sender_id: str, message: str, client_id: str = None):
        dead_clients = []
        if client_id:
            if not await self.send_to_client(client_id, message):
                dead_clients.append(client_id)
        else:
            for cid, client in list(self.clients.items()):
                if cid != sender_id:
                    try:
                        if not client.ws_connection or not client.ws_connection.client_terminated:
                            await client.write_message(message)
                        else:
                            dead_clients.append(cid)
                    except Exception:
                        dead_clients.append(cid)
        
        for cid in dead_clients:
            self.remove_client(cid)

class HealthHandler(BaseHandler):
    manager = None
    start_time = time.time()

    async def get(self):
        self.write({
            "status": "healthy",
            "connections": len(self.manager.clients),
            "max_connections": DEFAULT_CONFIG['websocket']['max_connections'],
            "uptime": time.time() - self.start_time
        })

class DataHandler(BaseHandler):
    async def get(self):
        self.write({"data": "example"})

    async def post(self):
        self.write({"received": json.loads(self.request.body)})

class SecureWebSocketHandler(WebSocketHandler):
    def initialize(self, manager: ConnectionManager):
        self.manager = manager
        self.client_id = None
        self.is_closed = False
        self.connection_ready = False

    def check_origin(self, origin):
        return True

    async def open(self):
        try:
            self.client_id = str(uuid.uuid4().hex)
            if not self.manager.add_client(self.client_id, self):
                self.close(reason="Connection limit reached")
                return
            self.connection_ready = True
            if self.ws_connection and not self.ws_connection.client_terminated:
                await self.send_connection_info()
            else:
                self.on_close()
        except Exception as e:
            logger.error(f"Open error: {str(e)}")
            self.close(reason="Internal server error")

    async def send_connection_info(self):
        if not self.connection_ready or self.is_closed:
            return
        try:
            await self.write_message(json.dumps({
                "type": "connection",
                "client_id": self.client_id
            }))
        except Exception:
            await self.close()

    async def on_message(self, message):
        try:
            data = json.loads(message)
            await self.manager.broadcast(self.client_id, message, data.get('client_id'))
        except json.JSONDecodeError:
            logger.error("Invalid JSON message received")
        except Exception as e:
            logger.error(f"Message handling error: {str(e)}")

    def on_close(self):
        if not self.is_closed:
            self.is_closed = True
            self.connection_ready = False
            if self.client_id:
                self.manager.remove_client(self.client_id)

class WebSocketServer:
    def __init__(self):
        self.manager = ConnectionManager()
        HealthHandler.manager = self.manager
        self.server = None

    def create_app(self):
        ssl_options = None
        if all(DEFAULT_CONFIG['security'].values()):
            ssl_options = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
            ssl_options.load_cert_chain(
                DEFAULT_CONFIG['security']['ssl_cert_path'],
                DEFAULT_CONFIG['security']['ssl_key_path']
            )
        
        # Fix the frontend path to point to the correct location
        frontend_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "frontend", "build")
        
        # Verify the path exists
        if os.path.exists(frontend_path):
            logger.info(f"Using frontend path: {frontend_path}")
        else:
            logger.warning(f"Frontend path does not exist: {frontend_path}")
        
        return Application([
            (r"/health", HealthHandler),
            (r"/api/data", DataHandler),
            (r"/ws", SecureWebSocketHandler, {"manager": self.manager}),
            (r"/(.*)", StaticFileHandler, {
                "path": frontend_path,
                "default_filename": "index.html"
            }),
        ], debug=False, ssl_options=ssl_options)

    async def start(self, port=None):
        app = self.create_app()
        try:
            # Attempt to bind server to port.
            self.server = app.listen(
                port or DEFAULT_CONFIG['websocket']['port'],
                address="0.0.0.0",
                max_buffer_size=10485760,
                max_body_size=10485760
            )
            logger.info(f"WebSocket server started at ws://0.0.0.0:{port or DEFAULT_CONFIG['websocket']['port']}/ws")
        except OSError as e:
            if "Address already in use" in str(e):
                logger.error(f"Port busy error: {e}")
                # Optionally perform graceful shutdown or exit
                return
            else:
                raise

    async def stop(self):
        if self.server:
            self.server.stop()
            await self.server.close_all_connections()
            self.server = None

async def main():
    server = WebSocketServer()
    try:
        await server.start()
        while True:
            await asyncio.sleep(1)
    except KeyboardInterrupt:
        await server.stop()
    except Exception as e:
        logger.error(f"Server error: {e}")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Server shutdown requested")
    finally:
        logger.info("Server shutdown complete")