from src.domain.models import Settings
from src.infrastructure.repositories.toml_settings_repository import (
    TOMLSettingsRepository,
)


def test_missing_file_creates_default(tmp_path):
    config_file = tmp_path / "config.toml"
    repo = TOMLSettingsRepository(str(config_file))

    # Assert file does not exist initially
    assert not config_file.exists()

    settings = repo.get_settings()

    # Assert defaults are correct
    assert settings.language == "en"
    assert settings.auto_open_browser is True
    assert settings.active_sources == ["olx"]

    # Assert file was created
    assert config_file.exists()
    content = config_file.read_text(encoding="utf-8")
    assert 'language = "en"' in content
    assert 'active_sources = ["olx"]' in content


def test_save_settings_writes_to_file(tmp_path):
    config_file = tmp_path / "config.toml"
    repo = TOMLSettingsRepository(str(config_file))

    custom_settings = Settings(
        language="pl", auto_open_browser=False, active_sources=["olx", "otodom"]
    )
    repo.save_settings(custom_settings)

    assert config_file.exists()
    content = config_file.read_text(encoding="utf-8")
    assert 'language = "pl"' in content
    assert "auto_open_browser = false" in content
    assert 'active_sources = ["olx", "otodom"]' in content


def test_invalid_file_recreates_default(tmp_path):
    config_file = tmp_path / "config.toml"

    # Write malformed TOML
    config_file.write_text("language = [", encoding="utf-8")

    repo = TOMLSettingsRepository(str(config_file))
    settings = repo.get_settings()

    # Assert defaults are returned
    assert settings.language == "en"
    assert settings.auto_open_browser is True

    # Assert file was overwritten with valid TOML
    content = config_file.read_text(encoding="utf-8")
    assert 'language = "en"' in content
    assert "auto_open_browser = true" in content
    assert "language = [" not in content
