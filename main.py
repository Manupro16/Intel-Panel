import ssl

from actionControl import ActionController
from cache import Cache
from client_manager import ClientManager
from lcu_api import LCUDataRetriever
from lcu_websocket import WebSocketManager
from message_handler import MessageHandler
from observer import ObserverManager


class App:
    def __init__(self):

        self.cert_path = "riotgames.pem"
        self.ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)

        self.observer = ObserverManager()
        self.cache = Cache(observer_manager=self.observer)
        self.message_handler = MessageHandler(observer_manager=self.observer, cache=self.cache)
        self.lcu_calls = LCUDataRetriever(cache=self.cache, ssl=self.ssl_context)
        self.lcu = WebSocketManager(cache=self.cache, ssl=self.ssl_context, lcu_calls=self.lcu_calls,
                                    observer_manager=self.observer, message_handler=self.message_handler)
        self.action_controller = ActionController(observer_manager=self.observer, api_client_calls=self.lcu_calls)
        self.client_manager = ClientManager(observer_manager=self.observer, cache=self.cache, lcu_calls=self.lcu_calls,
                                            websocket_manager=self.lcu)
    pass




if __name__ == '__main__':
    app = App()
