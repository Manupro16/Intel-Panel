from websockets import connect
import logging
import base64
import json

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

MAX_SIZE = 1024 * 1024 * 10  # 10 MB


class WebSocketManager:
    def __init__(self, cache, lcu_calls, ssl, observer_manager, message_handler):
        self.cache = cache
        self.ssl = ssl
        self.lcu_calls = lcu_calls
        self.observer_manager = observer_manager
        self.message_handler = message_handler

    async def start_websocket(self):
        while True:
            credentials = self.cache.get_client_credentials()
            uri = f"wss://127.0.0.1:{credentials['port']}"
            headers = [("Authorization",
                        'Basic ' + base64.b64encode(('riot:' + credentials['password']).encode()).decode())]
            async with connect(uri, extra_headers=headers, ssl=self.ssl,
                               max_size=MAX_SIZE) as websocket:
                logging.info("WebSocket connection established.")
                await websocket.send(json.dumps([5, "OnJsonApiEvent"]))
                async for message in websocket:
                    await self.message_handler.handle_message(message)
