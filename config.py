from decouple import config


class Config(object):

    LANGUAGES = ['en', 'fi', 'fa', 'el', 'it', 'zh']

    # MariaDB mysql database settings
    MYSQL_USER = config('MYSQL_USER')
    MYSQL_PASSWORD = config('MYSQL_PASSWORD')
    MYSQL_SERVER = config('MYSQL_SERVER')
    MYSQL_DB = config('MYSQL_DB')

    SQLALCHEMY_DATABASE_URI = f"mysql+pymysql://{MYSQL_USER}:{MYSQL_PASSWORD}@{MYSQL_SERVER}/{MYSQL_DB}?charset=utf8mb4"

    SQLALCHEMY_TRACK_MODIFICATIONS = False

    SQLALCHEMY_ENGINE_OPTIONS = {
        "pool_pre_ping": True,
        "pool_recycle": 60,
        "max_overflow": 30,
        "pool_size": 20
    }

    TEMPLATES_AUTO_RELOAD = True

    DEBUG = False
