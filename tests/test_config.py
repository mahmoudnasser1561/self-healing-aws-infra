from app.config import load_config, load_version


def test_defaults_point_at_a_local_database_over_ssl():
    config = load_config({})

    assert (config.db_host, config.db_port, config.db_name) == (
        "localhost",
        5432,
        "app",
    )
    assert config.db_sslmode == "require"


def test_values_come_from_the_environment():
    config = load_config({"DB_HOST": "db.internal", "DB_PORT": "6543", "DB_NAME": "x"})

    assert (config.db_host, config.db_port, config.db_name) == (
        "db.internal",
        6543,
        "x",
    )


def test_version_is_read_from_the_release_file(tmp_path):
    version_file = tmp_path / "VERSION"
    version_file.write_text("abc123\n")

    assert load_version(version_file) == "abc123"
    assert load_version(tmp_path / "missing") == "dev"
