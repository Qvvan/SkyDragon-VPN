import base64

import aiohttp
from aiohttp import ClientTimeout

from ssh_tunnel_manager import SSHTunnelManager


class BaseKeyManager:
    def __init__(self, server_ip):
        self.server_ip = server_ip
        self.tunnel_manager = SSHTunnelManager()

    async def _get_sub_3x_ui(self, sub_id):
        tunnel_port = await self.tunnel_manager.get_tunnel_port(self.server_ip)
        if not tunnel_port:
            return None
        url = f"https://localhost:{tunnel_port}/sub/{sub_id}"

        connector = aiohttp.TCPConnector(ssl=False)
        async with aiohttp.ClientSession(connector=connector) as session:
            async with session.get(url, timeout=ClientTimeout(total=10)) as response:
                if response.status == 200:
                    base64_response = await response.text()
                    try:
                        decoded_configs = base64.b64decode(base64_response).decode('utf-8')
                        return decoded_configs
                    except Exception as decode_error:
                        print(f"Ошибка декодирования base64: {decode_error}")
                        return base64_response
                else:
                    print(f"HTTP {response.status} для {url}")
