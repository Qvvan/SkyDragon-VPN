from utils.encode_link import encrypt_part


async def create_config_link(user_id: int):
    encoded_user_id = encrypt_part(str(user_id))
    url = "https://skydragonvpn/sub/"

    return url + encoded_user_id