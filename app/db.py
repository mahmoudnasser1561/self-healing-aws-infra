import contextlib
import json
from pathlib import Path

import boto3
import psycopg2
from psycopg2.extras import RealDictCursor

SCHEMA = (Path(__file__).resolve().parent / "schema.sql").read_text()
CONNECT_TIMEOUT_SECONDS = 3


class Database:
    def __init__(self, settings, credentials_loader=None):
        self._settings = settings
        self._load_credentials = credentials_loader or self._read_credentials
        self._secrets = None
        self._schema_ready = False

    def _read_credentials(self):
        settings = self._settings
        if settings.db_password:
            return settings.db_user, settings.db_password
        if self._secrets is None:
            self._secrets = boto3.client(
                "secretsmanager", region_name=settings.aws_region
            )
        secret = self._secrets.get_secret_value(SecretId=settings.db_secret_arn)
        data = json.loads(secret["SecretString"])
        return data["username"], data["password"]

    def _ensure_schema(self, conn):
        if self._schema_ready:
            return
        with conn.cursor() as cur:
            cur.execute(SCHEMA)
        conn.commit()
        self._schema_ready = True

    @contextlib.contextmanager
    def connection(self):
        user, password = self._load_credentials()
        settings = self._settings
        conn = psycopg2.connect(
            host=settings.db_host,
            port=settings.db_port,
            dbname=settings.db_name,
            user=user,
            password=password,
            sslmode=settings.db_sslmode,
            connect_timeout=CONNECT_TIMEOUT_SECONDS,
            cursor_factory=RealDictCursor,
        )
        try:
            self._ensure_schema(conn)
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()
