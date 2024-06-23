import re
import psutil
import asyncio

# Precompiled regex patterns
PORT_RE = re.compile(r'--app-port=(?P<port>[0-9]*)')
PASSWORD_RE = re.compile(r'--remoting-auth-token=(?P<password>[\w-]*)')


class LCUManager:
    def __init__(self, cache):
        self.cache = cache

    async def fetch_credentials(self) -> bool:
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(None, self.get_process_info)

        if result:
            pid, port, password = result
            self.cache.set_client_credentials(port=port, password=password)
            return True

        return False

    @staticmethod
    def get_process_info():
        for proc in psutil.process_iter(attrs=['pid', 'name', 'cmdline']):
            if proc.info['name'] in ['LeagueClientUx.exe', 'LeagueClientUx']:
                cmd_line = ' '.join(proc.info['cmdline'])
                port = PORT_RE.search(cmd_line)
                password = PASSWORD_RE.search(cmd_line)
                if port and password:
                    return proc.info['pid'], port.group('port'), password.group('password')
        return None
