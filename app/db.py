import json
from pathlib import Path

import boto3
import psycopg2
from psycopg2.extras import RealDictCursor

SCHEMA = (Path(__file__).resolve().parent / "schema.sql").read_text()


class Database:
    def __init__(self, config):
        self.config = config
        self.conn = None

    def _credentials(self):
        if self.config.db_password:
            return self.config.db_user, self.config.db_password
        client = boto3.client("secretsmanager", region_name=self.config.aws_region)
        secret = client.get_secret_value(SecretId=self.config.db_secret_arn)
        data = json.loads(secret["SecretString"])
        return data["username"], data["password"]

    def _connect(self):
        user, password = self._credentials()
        conn = psycopg2.connect(
            host=self.config.db_host,
            port=self.config.db_port,
            dbname=self.config.db_name,
            user=user,
            password=password,
            sslmode=self.config.db_sslmode,
            connect_timeout=3,
            cursor_factory=RealDictCursor,
        )
        conn.autocommit = True
        with conn.cursor() as cur:
            cur.execute(SCHEMA)
        return conn

    def cursor(self):
        if self.conn is None or self.conn.closed:
            self.conn = self._connect()
        return self.conn.cursor()
