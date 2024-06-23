import asyncio


class ObserverManager:
    def __init__(self):
        self._observers = []

    def add_observer(self, observer):
        if observer not in self._observers:
            self._observers.append(observer)

    def remove_observer(self, observer):
        try:
            self._observers.remove(observer)
        except ValueError:
            pass

    def notify(self, key, **kwargs):
        print(f"Notifying observers with key: {key}")
        for observer in self._observers:
            method = getattr(observer, key, None)
            if callable(method):
                if asyncio.iscoroutinefunction(method):
                    asyncio.create_task(method(**kwargs))

                else:
                    method(**kwargs)
