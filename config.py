import os

class Config:
    @staticmethod
    def get(key, default=None):
        return os.getenv(key, default)

    @staticmethod
    def load_config():
        # Here you can specify any required environment variables
        required_vars = ['DATABASE_URL', 'API_KEY']
        for var in required_vars:
            if not Config.get(var):
                raise ValueError(f'Environment variable {var} is not set.')