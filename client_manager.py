import asyncio
import logging
from websockets import exceptions
from client_request import LCUManager

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


class ClientManager:
    def __init__(self, cache, observer_manager, lcu_calls, websocket_manager):
        self.cache = cache
        self.observer_manager = observer_manager
        self.observer_manager.add_observer(self)
        self.lcu_calls = lcu_calls
        self.lcu_manager = LCUManager(cache=self.cache)
        self.websocket_manager = websocket_manager

    async def check_client_status(self) -> bool:
        print('check_client_status')
        if not self.cache.get_client_status():
            response = await self.lcu_manager.fetch_credentials()
            if response:
                await self.lcu_calls.get_client_data()
                self.cache.set_client_status(True)
                self.observer_manager.notify("update_loading_text")
                await asyncio.sleep(2)  # Consider reducing sleep duration
                self.observer_manager.notify("update_client_phases", value="main_menu")
                return True
            else:
                return False
        return True

    async def start_back_end_operations(self):
        try:
            if await self.check_client_status():
                await self.websocket_manager.start_websocket()
            else:
                print('here')
                self.observer_manager.notify(key="client_not_open_restart",
                                             message="Client not open or credentials not found.")
        except exceptions.ConnectionClosed as e:
            logging.error(f"Unexpected error: {e}")
            self.observer_manager.notify(key="client_not_open_restart",
                                         message="Client not open or credentials not found.")
        except Exception as e:
            logging.error(f"Unexpected error: {e}")
            self.observer_manager.notify(key="client_not_open_restart",
                                         message="Client not open or credentials not found.")
