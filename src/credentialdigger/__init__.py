import importlib.metadata

from .client import Client
from .client_postgres import PgClient
from .client_sqlite import SqliteClient


__version__ = importlib.metadata.version('credentialdigger')
