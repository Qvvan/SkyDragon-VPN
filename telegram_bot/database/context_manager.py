from database.db_methods import MethodsManager
from database.init_db import DataBase


class DatabaseContextManager:
    def __init__(self):
        self.db = DataBase()
        self.session = None
        self.methods = None

    async def __aenter__(self):
        try:
            self.session = self.db.Session()
            self.methods = MethodsManager(self.session)
            return self.methods
        except Exception as e:
            print(f"Error initializing DatabaseContextManager: {e}")
            raise

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        try:
            if exc_type:
                print(f"Exception occurred: {exc_type} - {exc_val}")
                await self.session.rollback()
        finally:
            await self.session.close()

