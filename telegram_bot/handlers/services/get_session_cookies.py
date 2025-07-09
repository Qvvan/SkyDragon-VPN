import asyncio

import aiohttp

from config_data.config import MY_SECRET_URL, LOGIN_X_UI_PANEL, PASSWORD_X_UI_PANEL, PORT_X_UI
from logger.logging_config import logger

cookies_store = {}
RETRIES = 2
DELAY = 1


async def get_session_cookie(server_ip: str):
    if server_ip == "150.241.94.108":
        return
    if server_ip in cookies_store:
        if await make_request_with_cookies(server_ip):
            return cookies_store[server_ip]


    url = f"https://{server_ip}:{PORT_X_UI}/{MY_SECRET_URL}/login"
    payload = {
        "username": LOGIN_X_UI_PANEL,
        "password": PASSWORD_X_UI_PANEL
    }
    timeout = aiohttp.ClientTimeout(connect=3, total=10)

    for attempt in range(RETRIES):
        try:
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.post(url, data=payload, ssl=False) as response:
                    if response.status == 200:
                        cookies = response.cookies
                        cookies_store[server_ip] = cookies
                        return cookies
        except asyncio.TimeoutError:
            await logger.info("Request timed out. Retrying...")
        except aiohttp.ClientError as e:
            await logger.info(f"Error making request: {e}")

        if attempt < RETRIES - 1:
            await logger.info(f"Retrying after {DELAY} seconds...")
            await asyncio.sleep(DELAY)
    await logger.log_error("Error getting session cookie", None)
    return None


async def make_request_with_cookies(server_ip):
    if server_ip == "150.241.94.108":
        return

    cookies = cookies_store.get(server_ip)
    if not cookies:
        print(f"No cookies available for {server_ip}")
        return None

    url = f"https://{server_ip}:{PORT_X_UI}/{MY_SECRET_URL}/panel/"
    timeout = aiohttp.ClientTimeout(connect=3, total=10)

    try:
        async with aiohttp.ClientSession(timeout=timeout) as session:
            try:
                async with session.get(url, cookies=cookies, ssl=False) as response:
                    return response.status == 200
            except Exception as e:
                await logger.info(f"Error making request: {e}")
    except aiohttp.ClientError as e:
        await logger.info(f"Error making request: {e}")
        await logger.log_error(f"Error making request with cookies", e)

    return None
