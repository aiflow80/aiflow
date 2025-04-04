import os, asyncio, json, logging, time, uuid, ssl, threading
from tornado.web import Application, RequestHandler, StaticFileHandler
from tornado.websocket import WebSocketHandler

DEFAULT_CONFIG = {'websocket':{'host':'0.0.0.0','port':8888,'max_connections':100},'security':{'ssl_cert_path':None,'ssl_key_path':None}}
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'); logger = logging.getLogger('Server')
for log_name in ["tornado.access", "tornado.application", "tornado.general"]: logging.getLogger(log_name).setLevel(logging.WARNING)

class BaseHandler(RequestHandler):
	def set_default_headers(self): 
		self.set_header("Access-Control-Allow-Origin", "*"); self.set_header("Access-Control-Allow-Headers", "Content-Type"); self.set_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS"); self.set_header("Content-Type", "application/json")
	def options(self): self.set_status(204); self.finish()

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
			received = len(self.chunks[message_id]['received_chunks'])
			logger.info(f"Received chunk {chunk_index+1}/{total_chunks} for message {message_id} ({received}/{total_chunks} total received)")
			return self.is_complete(message_id)
	
	def is_complete(self, message_id):
		if message_id not in self.chunks: return False
		message_data = self.chunks[message_id]
		return len(message_data['received_chunks']) == message_data['total_chunks']
	
	def get_complete_message(self, message_id):
		if not self.is_complete(message_id): return None
		message_data = self.chunks[message_id]
		sorted_chunks = [message_data['data'][i] for i in range(message_data['total_chunks'])]
		first_chunk = sorted_chunks[0]
		if (first_chunk.get('payload').get('type') == 'file-change' and first_chunk.get('payload').get('fileEvent')):
			combined_base64 = "".join(chunk['payload']['fileEvent']['data'] for chunk in sorted_chunks)
			complete_message = json.loads(json.dumps(first_chunk))
			complete_message['payload']['fileEvent']['data'] = combined_base64
			with self._cleanup_lock:
				sender_id = message_data['sender_id']
				del self.chunks[message_id]
				if message_id in self._last_activity: del self._last_activity[message_id]
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
					if message_id in self._last_activity: del self._last_activity[message_id]

class ConnectionManager:
	def __init__(self):
		self.clients = {}
		self._connection_count = 0
		self._lock = threading.Lock()
		self.chunk_tracker = ChunkTracker()
		self._start_cleanup_task()

	def _start_cleanup_task(self):
		async def cleanup_periodically():
			while True:
				await asyncio.sleep(60)
				self.chunk_tracker.cleanup_old_chunks()
		asyncio.create_task(cleanup_periodically())

	def add_client(self, client_id: str, client: WebSocketHandler) -> bool:
		with self._lock:
			if client_id in self.clients: self.remove_client(client_id)
			if self._connection_count >= DEFAULT_CONFIG['websocket']['max_connections']: return False
			self.clients[client_id] = client
			self._connection_count += 1
			return True

	def remove_client(self, client_id: str):
		with self._lock:
			if client_id in self.clients:
				try: self.clients[client_id].close()
				except: pass
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
			if not await self.send_to_client(client_id, message): dead_clients.append(client_id)
		else:
			for cid, client in list(self.clients.items()):
				if cid != sender_id:
					try:
						if not client.ws_connection or not client.ws_connection.client_terminated:
							await client.write_message(message)
						else: dead_clients.append(cid)
					except Exception: dead_clients.append(cid)
		for cid in dead_clients: self.remove_client(cid)

class HealthHandler(BaseHandler):
	manager = None
	start_time = time.time()
	async def get(self):
		self.write({"status": "healthy","connections": len(self.manager.clients),"max_connections": DEFAULT_CONFIG['websocket']['max_connections'],"uptime": time.time() - self.start_time})

class DataHandler(BaseHandler):
	async def get(self): self.write({"data": "example"})
	async def post(self): self.write({"received": json.loads(self.request.body)})

class SecureWebSocketHandler(WebSocketHandler):
	def initialize(self, manager: ConnectionManager):
		self.manager = manager
		self.client_id = None
		self.is_closed = False
		self.connection_ready = False

	def check_origin(self, origin): return True

	async def open(self):
		try:
			self.client_id = str(uuid.uuid4().hex)
			if not self.manager.add_client(self.client_id, self):
				self.close(reason="Connection limit reached")
				return
			self.connection_ready = True
			if self.ws_connection and not self.ws_connection.client_terminated: await self.send_connection_info()
			else: self.on_close()
		except Exception as e:
			logger.error(f"Open error: {str(e)}")
			self.close(reason="Internal server error")

	async def send_connection_info(self):
		if not self.connection_ready or self.is_closed: return
		try:
			await self.write_message(json.dumps({"type": "connection","client_id": self.client_id}))
		except Exception: await self.close()

	async def on_message(self, message):
		try:
			data = json.loads(message)
			if data.get('type') == 'chunked_message':
				message_id = data.get('messageId')
				chunk_index = data.get('chunkIndex')
				total_chunks = data.get('totalChunks')
				payload = data.get('payload')
				if message_id and chunk_index is not None and total_chunks and payload:
					is_complete = self.manager.chunk_tracker.add_chunk(message_id, chunk_index, total_chunks, payload, self.client_id)
					await self.write_message(json.dumps({"type": "chunk_ack","messageId": message_id,"chunkIndex": chunk_index,"status": "received"}))
					if is_complete:
						logger.info(f"All chunks received for message ID {message_id}, reassembling")
						complete_message, sender_id = self.manager.chunk_tracker.get_complete_message(message_id)
						if complete_message:
							await self.write_message(json.dumps({"type": "chunked_message_complete","messageId": message_id,"status": "complete"}))
							await self.manager.broadcast(sender_id, json.dumps(complete_message), data.get('client_id'))
							logger.info(f"Successfully processed and broadcast complete message {message_id}")
					return
			if data.get('type') == 'chunks_complete':
				message_id = data.get('messageId')
				logger.info(f"Client reported all chunks sent for message {message_id}")
				await self.write_message(json.dumps({"type": "chunks_complete_ack","messageId": message_id,"status": "received"}))
				return
			await self.manager.broadcast(self.client_id, message, data.get('client_id'))
		except json.JSONDecodeError: logger.error("Invalid JSON message received")
		except Exception as e:
			logger.error(f"Message handling error: {str(e)}")
			import traceback
			logger.error(traceback.format_exc())

	def on_close(self):
		if not self.is_closed:
			self.is_closed = True
			self.connection_ready = False
			if self.client_id: self.manager.remove_client(self.client_id)

class WebSocketServer:
	def __init__(self):
		self.manager = ConnectionManager()
		HealthHandler.manager = self.manager
		self.server = None

	def create_app(self):
		ssl_options = None
		if all(DEFAULT_CONFIG['security'].values()):
			ssl_options = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
			ssl_options.load_cert_chain(DEFAULT_CONFIG['security']['ssl_cert_path'],DEFAULT_CONFIG['security']['ssl_key_path'])
		frontend_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "frontend", "build")
		if os.path.exists(frontend_path): pass
		else: logger.warning(f"Frontend path does not exist: {frontend_path}")
		return Application([
			(r"/health", HealthHandler),
			(r"/api", DataHandler),
			(r"/ws", SecureWebSocketHandler, {"manager": self.manager}),
			(r"/(.*)", StaticFileHandler, {"path": frontend_path,"default_filename": "index.html"}),
		], debug=False, ssl_options=ssl_options)

	async def start(self, port=None):
		app = self.create_app()
		try:
			self.server = app.listen(port or DEFAULT_CONFIG['websocket']['port'],address="0.0.0.0",max_buffer_size=1073741824,max_body_size=1073741824)
			logger.info(f"Server started at 0.0.0.0:{port or DEFAULT_CONFIG['websocket']['port']}")
		except OSError as e:
			if "Address already in use" in str(e):
				logger.error(f"Port busy error: {e}")
				return
			else: raise

	async def stop(self):
		if self.server:
			self.server.stop()
			await self.server.close_all_connections()
			self.server = None

async def main():
	server = WebSocketServer()
	try:
		await server.start()
		while True: await asyncio.sleep(1)
	except KeyboardInterrupt: await server.stop()
	except Exception as e: logger.error(f"Server error: {e}")

if __name__ == "__main__":
	try: asyncio.run(main())
	except KeyboardInterrupt: pass
	finally: logger.info("Server shutdown complete")