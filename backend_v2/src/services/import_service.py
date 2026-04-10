from src.core.config import Config


class ImportService:
    __slots__ = ("_config",)

    def __init__(self, config: Config) -> None:
        self._config = config

    def public_sub_url(self, encrypted_part: str) -> str:
        return f"{self._config.app.PUBLIC_BASE_URL.rstrip('/')}/sub/{encrypted_part}"

    def happ_deeplink(self, encrypted_part: str) -> str:
        return f"happ://add/{self.public_sub_url(encrypted_part)}"

    def route_deeplink(self, platform: str, app_name: str, encrypted_part: str) -> str:
        if app_name == "happ":
            return self.happ_deeplink(encrypted_part)
        return f"v2raytun://import/{self.public_sub_url(encrypted_part)}"

    def platform_apps(self, platform: str, encrypted_part: str) -> list[dict[str, str]]:
        store_map = {
            "iphone": [
                {"app_name": "Happ (RU App Store)", "store_url": "https://apps.apple.com/ru/app/happ-proxy-utility-plus/id6746188973"},
                {"app_name": "Happ (EU/US App Store)", "store_url": "https://apps.apple.com/us/app/happ-proxy-utility/id6504287215"},
            ],
            "android": [
                {"app_name": "Happ (Google Play)", "store_url": "https://play.google.com/store/apps/details?id=com.happproxy"},
            ],
            "windows": [
                {"app_name": "Happ", "store_url": "https://github.com/Happ-proxy/happ-desktop/releases/latest/download/setup-Happ.x64.exe"},
            ],
            "macos": [
                {"app_name": "Happ (RU App Store)", "store_url": "https://apps.apple.com/ru/app/happ-proxy-utility-plus/id6746188973"},
                {"app_name": "Happ (EU/US App Store)", "store_url": "https://apps.apple.com/us/app/happ-proxy-utility/id6504287215"},
            ],
        }
        apps = []
        for item in store_map.get(platform, []):
            apps.append(
                {
                    "app_name": item["app_name"],
                    "store_url": item["store_url"],
                    "import_url": self.route_deeplink(platform, "happ", encrypted_part),
                }
            )
        return apps
