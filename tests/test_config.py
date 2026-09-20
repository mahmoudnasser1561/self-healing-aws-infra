from app.config import load_settings, load_version


def test_settings_default_to_a_local_database_and_small_pages():
    settings = load_settings({})

    assert (settings.db_host, settings.db_port, settings.db_sslmode) == (
        "localhost",
        5432,
        "require",
    )
    assert (settings.default_limit, settings.max_limit) == (20, 100)


def test_settings_are_read_from_the_environment():
    settings = load_settings(
        {"DB_HOST": "db.internal", "DB_PORT": "6543", "MAX_PAGE_SIZE": "50"}
    )

    assert (settings.db_host, settings.db_port, settings.max_limit) == (
        "db.internal",
        6543,
        50,
    )


def test_version_is_read_from_the_release_file(tmp_path):
    version_file = tmp_path / "VERSION"
    version_file.write_text("abc123\n")

    assert load_version(version_file) == "abc123"
    assert load_version(tmp_path / "missing") == "dev"
