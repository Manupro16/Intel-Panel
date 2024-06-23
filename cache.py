import logging
from threading import RLock


logger = logging.getLogger(__name__)


class Cache:
    def __init__(self, observer_manager):
        self.observer_manager = observer_manager
        self.cache = {}
        self.cache_lock = RLock()
        self.client_status = False
        self.client_credentials = {
            "port": "",
            "password": "",
        }

    # Basic cache operations
    def set(self, key, value):
        with self.cache_lock:
            self.cache[key] = value

    def get(self, key):
        with self.cache_lock:
            return self.cache.get(key)

    def update(self, key, new_value):
        with self.cache_lock:
            if key not in self.cache or self.cache[key] != new_value:
                try:
                    self.cache[key] = new_value
                    self.observer_manager.notify('update_ui', function=key, value=new_value)  # Notify observers of update
                    logger.info(f"Cache updated for key: {key}")  # Log successful update
                except Exception as e:
                    logger.error(f"Failed to update cache for key: {key} with error: {str(e)}")
            else:
                logger.debug(f"No change for key: {key}, not updating.")

    def delete(self, key):
        with self.cache_lock:
            self.cache.pop(key, None)

    def clear(self):
        with self.cache_lock:
            self.cache.clear()

    # Client-specific settings
    def set_client_credentials(self, port: str, password: str):
        with self.cache_lock:
            self.client_credentials['port'] = port
            self.client_credentials['password'] = password

    def get_client_credentials(self):
        with self.cache_lock:
            return self.client_credentials

    def set_client_status(self, status):
        with self.cache_lock:
            self.client_status = status

    def get_client_status(self):
        with self.cache_lock:
            return self.client_status

    # Helper functions to deal with nested structures
    def get_nested(self, *args):
        with self.cache_lock:
            cache = self.cache
            for arg in args:
                cache = cache.get(arg)
                if cache is None:
                    return None
                if isinstance(cache, dict) and 'value' in cache:
                    cache = cache['value']
            return cache

    def get_champion_name(self, champ_id):
        """Retrieve the champion's name from the cached champion data using the champion ID."""
        with self.cache_lock:
            champs_data = self.cache.get('champs_data', {})
            for champ_key, champ_info in champs_data.items():
                if champ_info.get('key') == str(champ_id):
                    return champ_info.get('name', 'Unknown')
            return 'Unknown'
