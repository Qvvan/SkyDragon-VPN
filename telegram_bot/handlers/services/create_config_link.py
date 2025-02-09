from utils.encode_link import encrypt_part


async def create_config_link(user_id: int, sub_id: int):
    encoded_user_id = encrypt_part(str(user_id) + "|" + str(sub_id))
    url = "https://skydragonvpn.ru/sub/"

    return url + encoded_user_id