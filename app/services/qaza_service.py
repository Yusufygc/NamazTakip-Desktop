"""Kaza servisi: liste, kaza etme ve geçmiş borç planı. Qt içe aktarmaz."""

from dataclasses import dataclass
from datetime import date

from app.core.domain.models import QazaDebtPlan, QazaItem
from app.core.domain.prayer import PrayerType
from app.core.domain.qaza import add_duration_to_backlog, clamp_backlog, clamp_daily_target, decrement_backlog
from app.core.repositories.prayer_repository import PrayerRepository
from app.services.prayer_service import PrayerService
from app.services.settings_service import SettingsService


@dataclass(frozen=True)
class QazaSummary:
    auto_count: int  # günlük takipten düşen kaza sayısı
    backlog_total: int  # geçmiş yıllar borcu
    grand_total: int
    daily_target: int
    estimated_days: "int | None"
    estimated_date: "date | None"


class QazaService:
    def __init__(self, prayers: PrayerRepository, settings: SettingsService, prayer_service: PrayerService):
        self._prayers = prayers
        self._settings = settings
        self._prayer_service = prayer_service

    def items(self) -> list[QazaItem]:
        return self._prayers.qaza_items(self._prayer_service.tracking_start, self._prayer_service.tracking_day())

    def compensate(self, item: QazaItem) -> None:
        """Vakti kaza edildi olarak işaretler; listeden çıkar ve zamanında kılınmış sayılmaz."""
        self._prayers.mark_compensated(item.date, item.prayer)

    @property
    def plan(self) -> QazaDebtPlan:
        return QazaDebtPlan(self._settings.qaza_backlog, self._settings.qaza_daily_target)

    def summary(self) -> QazaSummary:
        plan = self.plan
        auto_count = len(self.items())
        today = self._prayer_service.tracking_day()
        return QazaSummary(
            auto_count=auto_count,
            backlog_total=plan.total_backlog,
            grand_total=plan.grand_total(auto_count),
            daily_target=plan.daily_target,
            estimated_days=plan.estimated_days_to_finish(auto_count),
            estimated_date=plan.estimated_completion_date(auto_count, today),
        )

    def save_plan(self, backlog: dict[PrayerType, int], daily_target: int) -> None:
        self._settings.set_qaza_backlog({p: clamp_backlog(backlog.get(p, 0)) for p in PrayerType})
        self._settings.set_qaza_daily_target(clamp_daily_target(daily_target))

    def decrement_backlog(self, prayer: PrayerType, step: int = 1) -> None:
        self._settings.set_qaza_backlog(decrement_backlog(self._settings.qaza_backlog, prayer, step))

    @staticmethod
    def preview_duration(
        backlog: dict[PrayerType, int], years: int = 0, months: int = 0, days: int = 0
    ) -> dict[PrayerType, int]:
        """Süreyi verilen sayılara ekler; kaydetmez (kullanıcı "Planı Kaydet" ile onaylar)."""
        return add_duration_to_backlog(backlog, years, months, days)
