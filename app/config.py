import os
from dataclasses import dataclass
from pathlib import Path

VERSION_FILE = Path(__file__).resolve().parent.parent / "VERSION"


@dataclass(frozen=True)
class Config:
    db_host: str
    db_port: int
    db_name: str
    db_sslmode: str
    db_user: str
    db_password: str
    db_secret_arn: str
    aws_region: str
    version: str


def load_version(path=VERSION_FILE):
    return path.read_text().strip() if path.is_file() else "dev"


def load_config(env=None):
    env = os.environ if env is None else env
    return Config(
        db_host=env.get("DB_HOST", "localhost"),
        db_port=int(env.get("DB_PORT", "5432")),
        db_name=env.get("DB_NAME", "app"),
        db_sslmode=env.get("DB_SSLMODE", "require"),
        db_user=env.get("DB_USER", "postgres"),
        db_password=env.get("DB_PASSWORD", ""),
        db_secret_arn=env.get("DB_SECRET_ARN", ""),
        aws_region=env.get("AWS_REGION", "us-east-1"),
        version=load_version(),
    )
