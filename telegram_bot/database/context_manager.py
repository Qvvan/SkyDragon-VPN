import traceback

from database.db_methods import MethodsManager
from database.init_db import get_database
from logger.logging_config import logger


class DatabaseContextManager:
    def __init__(self):
        self.db = get_database()  # Используем singleton
        self.session = None
        self.methods = None

    async def __aenter__(self) -> MethodsManager:
        try:
            # Создаем сессию через async context manager
            self.session = self.db.Session()
            self.methods = MethodsManager(self.session)
            return self.methods
        except Exception as e:
            await logger.log_error(f"Error initializing DatabaseContextManager: {e}", e)
            raise

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session is None:
            return
            
        try:
            if exc_type:
                await logger.log_error(f"Exception occurred: {exc_type} - {exc_val}", exc_val)
                traceback.print_tb(exc_tb)
                await self.session.rollback()
        except Exception as e:
            await logger.log_error(f"Error during rollback: {e}", e)
        finally:
            try:
                await self.session.close()
            except Exception as e:
                await logger.log_error(f"Error closing session: {e}", e)

