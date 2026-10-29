"""SQLite bağlantısı, şema ve bozuk dosya kurtarma.

Tarihler `yyyy-MM-dd` metni olarak saklanır; `ORDER BY date` ve `BETWEEN` doğru çalışır.
Bağlantı ana iş parçacığında kullanılır (`check_same_thread` varsayılanı açık). Şema değişikliği:
`SCHEMA_VERSION`'ı artır, `_migrate`'e adım ekle, bellek içi DB'de test et, docs/wiki/veri-katmani.md'yi güncelle.

Kaynak: mobil `app_database.dart` (2026-10-29), Android'e özgü kısımlar çıkarıldı.
"""

import sqlite3
from datetime import datetime
from pathlib import Path

from app.core import paths
from app.core.logger import logger

FILE_NAME = "namaz_takip.db"
SCHEMA_VERSION = 1
MEMORY = ":memory:"

# SQLite 3 dosya başlığının ilk 16 baytı: "SQLite format 3\0".
_SQLITE_HEADER_MAGIC = b"SQLite format 3\x00"
_SQLITE_HEADER_MIN_LENGTH = 100
_BACKUP_INFIX = ".bozuk-"
_DB_FILE_SUFFIXES = ("", "-wal", "-shm", "-journal")


class DatabaseVersionError(RuntimeError):
    """Veritabanı bu uygulamadan daha yeni bir şema sürümüyle yazılmış."""


class AppDatabase:
    def __init__(
        self,
        connection: sqlite3.Connection,
        corrupted_backup_path: "Path | None" = None,
        path: "Path | None" = None,
    ):
        self.connection = connection
        # Veritabanı dosyasının yolu; bellek içi veritabanında None (günlük yedek alınmaz).
        self.path = path
        # Açılışta bozuk dosya yedeklenip sıfırlandıysa yedeğin tam yolu; normal açılışta None.
        self.corrupted_backup_path = corrupted_backup_path

    # ---- Açılış ---------------------------------------------------------------------

    @classmethod
    def open(cls, path: "str | Path | None" = None, now: "datetime | None" = None) -> "AppDatabase":
        """Veritabanını açar. Dosya bozuksa silmeden önce yedekler ve temiz bir veritabanı açar."""
        if path is not None and str(path) == MEMORY:
            return cls(_open_connection(MEMORY))

        db_path = Path(path) if path is not None else paths.db_path()
        if not db_path.is_file():
            return cls(_open_connection(db_path), path=db_path)

        original = db_path.read_bytes()
        if not _has_valid_header(original):
            logger.warning("Veritabanı başlığı geçersiz, yedeklenip sıfırlanacak: %s", db_path)
            return cls._recover(db_path, original, now)

        connection = None
        try:
            connection = _open_connection(db_path)
            healthy = _is_healthy(connection)
        except sqlite3.DatabaseError:
            logger.exception("Veritabanı açılamadı, yedeklenip sıfırlanacak: %s", db_path)
            healthy = False
        except DatabaseVersionError:
            if connection is not None:
                connection.close()
            raise

        if healthy:
            return cls(connection, path=db_path)
        if connection is not None:
            connection.close()
        logger.warning("Veritabanı sağlıksız, yedeklenip sıfırlanacak: %s", db_path)
        return cls._recover(db_path, original, now)

    @classmethod
    def open_in_memory(cls) -> "AppDatabase":
        """Test için bellek içi veritabanı."""
        return cls.open(MEMORY)

    @classmethod
    def _recover(cls, db_path: Path, original: bytes, now: "datetime | None") -> "AppDatabase":
        _delete_old_backups(db_path)
        stamp = (now or datetime.now()).strftime("%Y%m%d-%H%M%S")
        backup = db_path.with_name(f"{db_path.name}{_BACKUP_INFIX}{stamp}")
        backup.write_bytes(original)
        for suffix in _DB_FILE_SUFFIXES:
            leftover = Path(f"{db_path}{suffix}")
            if leftover.exists():
                leftover.unlink()
        return cls(_open_connection(db_path), corrupted_backup_path=backup, path=db_path)

    def backup_to(self, target: Path) -> None:
        """Veritabanının tutarlı bir kopyasını `target`a yazar (SQLite yedekleme API'si, açıkken de güvenli).

        Önce `.partial` dosyasına yazılır, bitince yerine taşınır; yarım kalan yedek `target` adıyla durmaz.
        """
        partial = target.with_name(target.name + ".partial")
        destination = sqlite3.connect(str(partial))
        try:
            self.connection.backup(destination)
        finally:
            destination.close()
        partial.replace(target)

    def close(self) -> None:
        self.connection.close()


# ---- Yardımcılar ---------------------------------------------------------------------


def _has_valid_header(data: bytes) -> bool:
    return len(data) >= _SQLITE_HEADER_MIN_LENGTH and data.startswith(_SQLITE_HEADER_MAGIC)


def _delete_old_backups(db_path: Path) -> None:
    """Yeni yedek yazılmadan önce eski `.bozuk-*` yedeklerini siler; yalnızca son bozuk kopya tutulur."""
    prefix = f"{db_path.name}{_BACKUP_INFIX}"
    for entry in db_path.parent.iterdir():
        if entry.is_file() and entry.name.startswith(prefix):
            entry.unlink()


def _open_connection(target: "str | Path") -> sqlite3.Connection:
    connection = sqlite3.connect(str(target), isolation_level=None)  # otomatik commit
    try:
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
        _migrate(connection)
    except BaseException:
        # Windows'ta açık bağlantı dosyanın yedeklenip silinmesini engeller: hata olsa da kapat.
        connection.close()
        raise
    return connection


def _is_healthy(connection: sqlite3.Connection) -> bool:
    integrity = connection.execute("PRAGMA integrity_check").fetchone()
    if integrity is None or integrity[0] != "ok":
        return False
    table = connection.execute("SELECT name FROM sqlite_master WHERE type = 'table' AND name = 'prayers'").fetchone()
    return table is not None


def _migrate(connection: sqlite3.Connection) -> None:
    version = connection.execute("PRAGMA user_version").fetchone()[0]
    if version > SCHEMA_VERSION:
        raise DatabaseVersionError(
            f"Veritabanı şema sürümü ({version}) bu uygulamanın sürümünden ({SCHEMA_VERSION}) yeni."
        )
    if version < 1:
        _create_schema_v1(connection)
    connection.execute(f"PRAGMA user_version = {SCHEMA_VERSION}")


def _create_schema_v1(connection: sqlite3.Connection) -> None:
    connection.executescript(
        """
        CREATE TABLE IF NOT EXISTS prayers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT NOT NULL,
            prayer TEXT NOT NULL,
            status INTEGER NOT NULL DEFAULT 0,
            is_congregation INTEGER NOT NULL DEFAULT 0,
            marked_at TEXT,
            compensated_at TEXT,
            UNIQUE(date, prayer)
        );
        CREATE INDEX IF NOT EXISTS idx_prayers_date ON prayers(date);
        CREATE INDEX IF NOT EXISTS idx_prayers_status ON prayers(status);
        CREATE TABLE IF NOT EXISTS settings (
            key TEXT PRIMARY KEY,
            value TEXT NOT NULL
        );
        """
    )
