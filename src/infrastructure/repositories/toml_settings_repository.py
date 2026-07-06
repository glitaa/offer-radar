import sys
if sys.version_info >= (3, 11):
    import tomllib
else:
    import tomli as tomllib

from pathlib import Path
from src.domain.interfaces import SettingsRepository
from src.domain.models import Settings

class TOMLSettingsRepository(SettingsRepository):
    def __init__(self, file_path: str = "config.toml"):
        self.file_path = Path(file_path)

    def get_settings(self) -> Settings:
        if not self.file_path.exists():
            settings = Settings()
            self.save_settings(settings)
            return settings
            
        try:
            with open(self.file_path, "rb") as f:
                data = tomllib.load(f)
            
            # Use defaults for missing fields
            settings = Settings()
            if "language" in data:
                settings.language = data["language"]
            if "auto_open_browser" in data:
                settings.auto_open_browser = data["auto_open_browser"]
                
            return settings
        except tomllib.TOMLDecodeError:
            settings = Settings()
            self.save_settings(settings)
            return settings

    def save_settings(self, settings: Settings) -> None:
        toml_content = (
            f'language = "{settings.language}"\n'
            f'auto_open_browser = {"true" if settings.auto_open_browser else "false"}\n'
        )
        with open(self.file_path, "w", encoding="utf-8") as f:
            f.write(toml_content)
