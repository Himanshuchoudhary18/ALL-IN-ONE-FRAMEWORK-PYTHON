"""Optional database adapters. Callers own clients via context managers."""
from contextlib import contextmanager
from uuid import uuid4

from sqlalchemy import create_engine, text


class SQLDatabase:
    """SQLite, PostgreSQL or MySQL; use named parameters, never interpolate SQL."""
    def __init__(self, url):
        self.engine = create_engine(url, pool_pre_ping=True)

    def query(self, statement, parameters=None):
        with self.engine.connect() as connection:
            return [dict(row) for row in connection.execute(text(statement), parameters or {}).mappings()]

    def execute(self, statement, parameters=None):
        with self.engine.begin() as connection:
            return connection.execute(text(statement), parameters or {}).rowcount

    def close(self):
        self.engine.dispose()

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()


@contextmanager
def mongo_database(uri, database, timeout_ms=10000):
    from pymongo import MongoClient
    with MongoClient(uri, serverSelectionTimeoutMS=timeout_ms) as client:
        client.admin.command("ping")
        yield client[database]


@contextmanager
def redis_client(url):
    from redis import Redis
    client = Redis.from_url(url, decode_responses=True, socket_timeout=10, socket_connect_timeout=10)
    try:
        client.ping()
        yield client
    finally:
        client.close()


@contextmanager
def firestore_client(credentials_path=None):
    import firebase_admin
    from firebase_admin import credentials, firestore
    credential = credentials.Certificate(credentials_path) if credentials_path else credentials.ApplicationDefault()
    app = firebase_admin.initialize_app(credential, name=f"qa-{uuid4().hex}")
    client = None
    try:
        client = firestore.client(app=app)
        yield client
    finally:
        if client is not None:
            client.close()
        firebase_admin.delete_app(app)
