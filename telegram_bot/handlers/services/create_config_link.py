from config_data.config import PUBLIC_BASE_URL
from utils.encode_link import encrypt_part


async def create_config_link(user_id: int, sub_id: int):
    sub_uuid = encrypt_part(str(user_id) + "|" + str(sub_id))
    return f"{PUBLIC_BASE_URL}/sub/{sub_uuid}"
