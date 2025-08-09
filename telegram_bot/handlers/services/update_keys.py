from database.context_manager import DatabaseContextManager
from handlers.services.create_keys import encode_numbers, generate_deterministic_uuid
from handlers.services.key_create import BaseKeyManager
from logger.logging_config import logger


async def update_keys(user_id, subscription_id: str, status: bool):
    async with DatabaseContextManager() as session:
        try:
            servers = await session.servers.get_all_servers()
            for server in servers:
                if server.hidden == 1:
                    continue
                try:
                    base = BaseKeyManager(server.server_ip)
                    sub_uuid = encode_numbers(user_id, int(subscription_id))
                    client_id = generate_deterministic_uuid(user_id, int(subscription_id))
                    await base.update_key_enable(user_id, sub_uuid, status, client_id)
                except Exception as e:
                    await logger.log_error(
                        f"Error updating keys for server {server.server_ip}, subscription ID: {subscription_id}", e)
        except Exception as e:
            await logger.log_error(f"Error fetching servers from the database", e)

