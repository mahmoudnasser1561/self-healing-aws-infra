from pathlib import Path

from flask import Blueprint, current_app, jsonify

bp = Blueprint("api", __name__)

VERSION_FILE = Path(__file__).resolve().parent.parent / "VERSION"


def _version():
    return VERSION_FILE.read_text().strip() if VERSION_FILE.is_file() else "dev"


@bp.get("/components")
def components():
    database = current_app.extensions["database"]
    with database.connection() as conn, conn.cursor() as cur:
        cur.execute("SELECT id, name, tier, description FROM components ORDER BY id")
        rows = cur.fetchall()
    return jsonify(components=rows)


@bp.get("/health")
def health():
    database = current_app.extensions["database"]
    try:
        with database.connection() as conn, conn.cursor() as cur:
            cur.execute(
                "SELECT now() AS db_time, (SELECT count(*) FROM components) AS total"
            )
            row = cur.fetchone()
    except Exception:
        current_app.logger.exception("health check failed")
        return jsonify(status="unavailable", version=_version()), 503
    return jsonify(
        status="ok",
        version=_version(),
        db_time=row["db_time"].isoformat(),
        components=row["total"],
    )
