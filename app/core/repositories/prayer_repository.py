"""Namaz işaretleri: okuma, upsert ve kaza listesi. SQL yalnızca burada, parametrik.

Kaynak: mobil `prayer_repository.dart` (2026-10-29). Kurallar: docs/wiki/takip-gunu-ve-kaza.md.
"""

import sqlite3
from collections.abc import Callable
from datetime import date, datetime

from app.core.database import AppDatabase
from app.core.domain.dates import date_key, parse_date_key
from app.core.domain.models import PrayerRecord, QazaItem
from app.core.domain.prayer import PrayerStatus, PrayerType
from app.core.domain.qaza import derive_qaza_items


def _default_clock() -> datetime:
    return datetime.now().astimezone()


class PrayerRepository:
    def __init__(self, database: AppDatabase, clock: Callable[[], datetime] = _default_clock):
        self._db = database
        self._clock = clock

    @staticmethod
    def _from_row(row: sqlite3.Row) -> PrayerRecord:
        return PrayerRecord(
            date=parse_date_key(row["date"]),
            prayer=PrayerType.from_key(row["prayer"]),
            status=PrayerStatus.from_code(row["status"]),
            is_congregation=bool(row["is_congregation"]),
        )

    def records_for_date(self, day: date) -> dict[PrayerType, PrayerRecord]:
        rows = self._db.connection.execute("SELECT * FROM prayers WHERE date = ?", (date_key(day),)).fetchall()
        records = [self._from_row(row) for row in rows]
        return {record.prayer: record for record in records}

    def records_between(self, first: date, last: date) -> list[PrayerRecord]:
        rows = self._db.connection.execute(
            "SELECT * FROM prayers WHERE date BETWEEN ? AND ?", (date_key(first), date_key(last))
        ).fetchall()
        return [self._from_row(row) for row in rows]

    def _upsert(self, day: date, prayer: PrayerType, status: PrayerStatus, congregation: bool = False) -> None:
        stamp = self._clock().isoformat(timespec="seconds")
        compensated_at = stamp if status == PrayerStatus.COMPENSATED else None
        # UNIQUE(date, prayer): aynı vakit tekrar işaretlenince çift kayıt oluşmaz, son işaret geçerlidir.
        self._db.connection.execute(
            """
            INSERT INTO prayers (date, prayer, status, is_congregation, marked_at, compensated_at)
            VALUES (?, ?, ?, ?, ?, ?)
            ON CONFLICT(date, prayer) DO UPDATE SET
                status = excluded.status,
                is_congregation = excluded.is_congregation,
                marked_at = excluded.marked_at,
                compensated_at = excluded.compensated_at
            """,
            (date_key(day), prayer.key, status.code, 1 if congregation else 0, stamp, compensated_at),
        )

    def mark_performed(self, day: date, prayer: PrayerType, congregation: bool = False) -> None:
        self._upsert(day, prayer, PrayerStatus.PERFORMED, congregation)

    def mark_missed(self, day: date, prayer: PrayerType) -> None:
        self._upsert(day, prayer, PrayerStatus.MISSED)

    def mark_compensated(self, day: date, prayer: PrayerType) -> None:
        self._upsert(day, prayer, PrayerStatus.COMPENSATED)

    def qaza_items(self, first_day: date, today: date) -> list[QazaItem]:
        """Kaza listesi (türetilir, tabloda tutulmaz). Kural: `derive_qaza_items`."""
        return derive_qaza_items(self.records_between(first_day, today), first_day, today)
