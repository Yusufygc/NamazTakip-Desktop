"""Windows açılışında başlatma: `HKCU\\Software\\Microsoft\\Windows\\CurrentVersion\\Run` kaydı.

Yönetici izni gerekmez. **Kayıt yalnızca paketlenmiş (donmuş) exe için değiştirilir**: geliştirme ortamında
`python main.py` yolu kayda yazılmaz ve var olan kayıt silinmez (kurulu uygulamanın kaydı bozulmasın).
Kurallar: docs/wiki/bildirim-ve-tepsi.md.
"""

import sys
from collections.abc import Callable
from typing import Protocol

from app.core.logger import logger

RUN_KEY = r"Software\Microsoft\Windows\CurrentVersion\Run"
VALUE_NAME = "NamazTakip"
AUTOSTART_ARG = "--autostart"


class RegistryBackend(Protocol):
    def get(self, name: str) -> "str | None": ...

    def set(self, name: str, value: str) -> None: ...

    def delete(self, name: str) -> bool: ...


class WinRegistry:
    """`HKEY_CURRENT_USER` altındaki bir anahtarda (varsayılan: Run) metin değerleri okur/yazar/siler."""

    def __init__(self, key_path: str = RUN_KEY):
        self._key_path = key_path

    def get(self, name: str) -> "str | None":
        import winreg

        try:
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, self._key_path, 0, winreg.KEY_READ) as key:
                value, _type = winreg.QueryValueEx(key, name)
        except FileNotFoundError:
            return None
        return str(value)

    def set(self, name: str, value: str) -> None:
        import winreg

        with winreg.CreateKeyEx(winreg.HKEY_CURRENT_USER, self._key_path, 0, winreg.KEY_SET_VALUE) as key:
            winreg.SetValueEx(key, name, 0, winreg.REG_SZ, value)

    def delete(self, name: str) -> bool:
        """Değer silindiyse True, zaten yoksa False."""
        import winreg

        try:
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, self._key_path, 0, winreg.KEY_SET_VALUE) as key:
                winreg.DeleteValue(key, name)
        except FileNotFoundError:
            return False
        return True


def frozen_executable() -> "str | None":
    """Paketlenmiş exe'nin yolu; geliştirme ortamında None."""
    return sys.executable if getattr(sys, "frozen", False) else None


class AutostartService:
    def __init__(
        self,
        registry: "RegistryBackend | None" = None,
        executable: Callable[[], "str | None"] = frozen_executable,
    ):
        self._registry = registry if registry is not None else WinRegistry()
        self._executable = executable

    def command(self) -> "str | None":
        """Run değerine yazılacak komut: `"<exe>" --autostart`; geliştirme ortamında None."""
        exe = self._executable()
        return None if exe is None else f'"{exe}" {AUTOSTART_ARG}'

    def is_registered(self) -> bool:
        return self._registry.get(VALUE_NAME) is not None

    def apply(self, enabled: bool) -> bool:
        """Kaydı ister duruma getirir. Kayıt değiştirilemediyse (geliştirme ortamı) False döner."""
        command = self.command()
        if command is None:
            logger.info("Geliştirme ortamında autostart kaydı değiştirilmez (ayar yalnızca saklanır).")
            return False
        if enabled:
            if self._registry.get(VALUE_NAME) != command:
                self._registry.set(VALUE_NAME, command)
            return True
        self._registry.delete(VALUE_NAME)
        return True

    def sync(self, enabled: "bool | None") -> bool:
        """Açılışta ayarla kaydı uyumlu tutar: açıksa yolu yeniler (klasör taşınmış olabilir), kapalıysa siler.

        `None` (henüz sorulmadı) hiçbir şey yapmaz.
        """
        if enabled is None:
            return False
        return self.apply(enabled)
