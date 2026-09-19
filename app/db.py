import contextlib
import json
import os

import boto3
import psycopg2
from psycopg2.extras import RealDictCursor

from .seed import COMPONENTS, INSERT, SCHEMA


class Database:
    def __init__(self):
        self._ready = False

    def _credentials(self):
        if os.environ.get("DB_PASSWORD"):
            return os.environ.get("DB_USER", "postgres"), os.environ["DB_PASSWORD"]
        client = boto3.client(
            "secretsmanager", region_name=os.environ.get("AWS_REGION", "us-east-1")
        )
        secret = client.get_secret_value(SecretId=os.environ["DB_SECRET_ARN"])
        data = json.loads(secret["SecretString"])
        return data["username"], data["password"]

    def _prepare(self, conn):
        if self._ready:
            return
        with conn.cursor() as cur:
            cur.execute(SCHEMA)
            cur.executemany(INSERT, COMPONENTS)
        conn.commit()
        self._ready = True

    @contextlib.contextmanager
    def connection(self):
        user, password = self._credentials()
        conn = psycopg2.connect(
            host=os.environ["DB_HOST"],
            port=int(os.environ.get("DB_PORT", "5432")),
            dbname=os.environ.get("DB_NAME", "app"),
            user=user,
            password=password,
            sslmode=os.environ.get("DB_SSLMODE", "require"),
            connect_timeout=3,
            cursor_factory=RealDictCursor,
        )
        try:
            self._prepare(conn)
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()
