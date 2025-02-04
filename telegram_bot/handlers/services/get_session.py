import datetime

import requests

from config_data.config import PASSWORD_MY_NALOG, INN

# Константы
AUTH_URL = "https://lknpd.nalog.ru/api/v1/auth/lkfl"
REFRESH_URL = "https://lknpd.nalog.ru/api/v1/auth/token"

INN = INN
PASSWORD = PASSWORD_MY_NALOG
DEVICE_INFO = {
    "sourceDeviceId": "J-MjzxGohXTuMYECozz6v",
    "sourceType": "WEB",
    "appVersion": "1.0.0",
    "metaDetails": {}
}

token_data = None  # Храним текущую сессию


def get_token():
    global token_data
    payload = {
        "username": INN,
        "password": PASSWORD,
        "deviceInfo": DEVICE_INFO
    }
    response = requests.post(AUTH_URL, json=payload)
    if response.status_code == 200:
        data = response.json()
        token_data = {
            "token": data["token"],
            "refresh_token": data["refreshToken"],
            "expires_at": datetime.datetime.fromisoformat(data["tokenExpireIn"][:-1])
        }
        return token_data
    else:
        raise Exception(f"Ошибка при получении токена: {response.status_code}, {response.text}")


def refresh_token():
    global token_data
    payload = {
        "refreshToken": token_data["refresh_token"],
        "deviceInfo": DEVICE_INFO
    }
    response = requests.post(REFRESH_URL, json=payload)
    if response.status_code == 200:
        data = response.json()
        token_data = {
            "token": data["token"],
            "refresh_token": data["refreshToken"],
            "expires_at": datetime.datetime.fromisoformat(data["tokenExpireIn"][:-1])
        }
        return token_data
    else:
        raise Exception(f"Ошибка при обновлении токена: {response.status_code}, {response.text}")


def get_valid_token():
    global token_data
    if token_data is None or datetime.datetime.utcnow() >= token_data["expires_at"]:
        return refresh_token() if token_data else get_token()
    return token_data

