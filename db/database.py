from pathlib import Path
from playhouse.sqlite_ext import SqliteExtDatabase

from config import DATABASE_NAME

DATABASE_URL = str(Path(__file__).resolve().parent) + DATABASE_NAME

db = SqliteExtDatabase(DATABASE_URL, check_same_thread=False)


