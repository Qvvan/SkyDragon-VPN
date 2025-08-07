# ssh_tunnel_manager.py
import asyncio
import subprocess
import os
import shutil
from typing import Dict, Optional

from config_data.config import PORT_X_UI


class SSHTunnelManager:
    """
    Простой менеджер SSH туннелей для всех серверов.
    Создает один туннель на сервер и переиспользует его.
    """
    _instance = None
    _tunnels: Dict[str, subprocess.Popen] = {}
    _local_ports: Dict[str, int] = {}

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if not hasattr(self, 'initialized'):
            self.initialized = True
            self._start_port = 20000  # Начальный порт для туннелей
            self._setup_ssh_keys()  # ✅ ДОБАВЛЯЕМ НАСТРОЙКУ КЛЮЧЕЙ

    def _setup_ssh_keys(self):
        """Копирует SSH ключи из смонтированной папки - КАК В РАБОЧЕМ ПРИМЕРЕ"""
        if not os.path.exists('/host_ssh'):
            print("❌ /host_ssh не найден")
            return False

        os.makedirs('/root/.ssh', exist_ok=True)
        os.chmod('/root/.ssh', 0o700)

        for filename in os.listdir('/host_ssh'):
            if os.path.isfile(f'/host_ssh/{filename}'):
                shutil.copy2(f'/host_ssh/{filename}', f'/root/.ssh/{filename}')
                if filename.endswith('.pub'):
                    os.chmod(f'/root/.ssh/{filename}', 0o644)
                else:
                    os.chmod(f'/root/.ssh/{filename}', 0o600)

        print("✅ SSH ключи настроены")
        return True

    async def get_tunnel_port(self, server_ip: str) -> Optional[int]:
        """Получает локальный порт для туннеля к серверу"""
        from logger.logging_config import logger

        if server_ip in self._local_ports:
            process = self._tunnels[server_ip]
            if process.poll() is None:  # Процесс работает
                return self._local_ports[server_ip]
            else:
                # Процесс умер, удаляем из кэша
                del self._tunnels[server_ip]
                del self._local_ports[server_ip]

        # Проверяем что SSH ключ существует
        if not os.path.exists('/root/.ssh/id_ed25519'):
            await logger.log_error(f"SSH ключ не найден: /root/.ssh/id_ed25519", None)
            return None

        # Создаем новый туннель
        local_port = self._start_port + len(self._local_ports)

        # ✅ ИСПОЛЬЗУЕМ ТОЧНО ТУ ЖЕ КОМАНДУ КАК В РАБОЧЕМ ПРИМЕРЕ
        cmd = [
            'ssh', '-N',
            '-i', '/root/.ssh/id_ed25519',
            '-L', f'{local_port}:localhost:{PORT_X_UI}',  # Туннелируем на PORT_X_UI
            '-p', '10022',
            '-o', 'StrictHostKeyChecking=no',
            '-o', 'UserKnownHostsFile=/dev/null',
            f'root@{server_ip}'
        ]

        try:
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )

            await asyncio.sleep(3)  # Ждем установки туннеля

            if process.poll() is None:
                self._tunnels[server_ip] = process
                self._local_ports[server_ip] = local_port
                await logger.info(f"✅ SSH туннель создан: {server_ip} -> localhost:{local_port}")
                return local_port
            else:
                await logger.log_error(f"❌ SSH процесс завершился для {server_ip}", None)
                return None

        except Exception as e:
            await logger.log_error(f"Ошибка создания SSH туннеля для {server_ip}", e)
            return None

    def cleanup(self):
        """Закрывает все туннели"""
        for server_ip, process in self._tunnels.items():
            try:
                process.terminate()
                process.wait(timeout=5)
                print(f"SSH туннель закрыт: {server_ip}")
            except:
                process.kill()
                print(f"SSH туннель принудительно закрыт: {server_ip}")