"""Kullanıcıya görünen merkezi Türkçe metinler. QML'de ve Python'da sabit metin yazılmaz.

Kaynak: mobil `lib/core/strings/*.dart` (2026-10-30). Bu dosyaya yalnızca kullanılan metinler eklenir;
ekran metinleri ilgili ekran yazılırken buraya gelir. Qt içe aktarmaz.
"""

from datetime import date

from app.core.domain.prayer import PrayerType
from app.core.domain.prayer_times import CalcMethod
from app.core.text_utils import turkish_upper
from app.version import APP_NAME, __version__


class PrayerStrings:
    FAJR = "Sabah"
    SUNRISE = "Güneş"
    DHUHR = "Öğle"
    ASR = "İkindi"
    MAGHRIB = "Akşam"
    ISHA = "Yatsı"

    _NAMES = {
        PrayerType.FAJR: FAJR,
        PrayerType.DHUHR: DHUHR,
        PrayerType.ASR: ASR,
        PrayerType.MAGHRIB: MAGHRIB,
        PrayerType.ISHA: ISHA,
    }

    @classmethod
    def name(cls, prayer: PrayerType) -> str:
        return cls._NAMES[prayer]


class CalcMethodStrings:
    _NAMES = {
        CalcMethod.DIYANET: "Diyanet (Türkiye)",
        CalcMethod.MWL: "Müslüman Dünya Birliği",
        CalcMethod.EGYPTIAN: "Mısır Genel Otoritesi",
        CalcMethod.KARACHI: "Karaçi İslam Bilimleri Üniv.",
        CalcMethod.UMM_AL_QURA: "Ümmü'l-Kura (Mekke)",
        CalcMethod.NORTH_AMERICA: "Kuzey Amerika (ISNA)",
    }

    @classmethod
    def name(cls, method: CalcMethod) -> str:
        return cls._NAMES[method]


class DateStrings:
    MONTHS = (
        "Ocak",
        "Şubat",
        "Mart",
        "Nisan",
        "Mayıs",
        "Haziran",
        "Temmuz",
        "Ağustos",
        "Eylül",
        "Ekim",
        "Kasım",
        "Aralık",
    )

    @classmethod
    def long(cls, day: date) -> str:
        """`25 Ocak 2026`"""
        return f"{day.day} {cls.MONTHS[day.month - 1]} {day.year}"


class NotificationStrings:
    """Bildirimlerde ikon/emoji kullanılmaz; uygulama ikonu sistem tarafından gösterilir."""

    @staticmethod
    def adhan_title(prayer_name: str) -> str:
        return f"{prayer_name} Vakti"

    @staticmethod
    def adhan_body(prayer_name: str) -> str:
        return f"{prayer_name} vakti girdi."

    @staticmethod
    def reminder_title(prayer_name: str) -> str:
        return f"{prayer_name} Namazını Kıldınız mı?"

    REMINDER_BODY = "Namazınızı işaretlemek için dokunun."


class QazaStrings:
    """Kaza ekranı ve geçmiş borç planlayıcı. `%1`, `%2` yer tutucularını QML `.arg()` doldurur."""

    AUTO_DETECTED = "Otomatik tespit"
    MARKED_MISSED = "Kılınmadı olarak işaretlendi"

    EMPTY_TITLE = "Kaza namazınız yok"
    EMPTY_SUBTITLE = "Allah kabul etsin."
    OVERVIEW_TITLE = "Kaza Borcu Özeti"
    TOTAL_PRAYERS_LABEL = "Kaza Vakti"
    DAILY_TARGET_LABEL = "Günlük Hedef"
    DAILY_TARGET_VALUE = "Günde %1 Vakit"
    ESTIMATED_FINISH = "Hedefinize uyarsanız tahmini bitiş: %1 (%2 gün)"
    PLANNER_BUTTON = "Geçmiş Borç Hesapla / Hedef Belirle"
    BACKLOG_SECTION_TITLE = "GEÇMİŞ YILLAR KAZA BORCU (VAKİT BAZLI)"
    TRACKED_SECTION_TITLE = "GÜNLÜK TAKİPTEN DÜŞEN KAZA NAMAZLARI"
    DECREMENT_BACKLOG = "1 Kaza Düş"
    REMAINING_PRAYER_COUNT = "%1 vakit kaldı"
    BADGE = "%1 Kaza"
    COMPENSATE = "Kaza Et"
    CONFIRM_TITLE = "Kaza Namazı"
    CONFIRM_YES = "Evet, Kıldım"
    CONFIRM_BODY = "%1 tarihli %2 namazını kaza ettiniz mi?"
    WIZARD_TITLE = "Geçmiş Kaza Borcu & Hedef"
    WIZARD_SUBTITLE = (
        "Uygulamayı kurmadan önceki yıllardan kalan tahmini borcunuzu yıl/ay/gün olarak hesaplayabilir "
        "veya vakit sayılarını doğrudan girebilirsiniz."
    )
    WIZARD_YEARS = "Yıl"
    WIZARD_MONTHS = "Ay"
    WIZARD_DAYS = "Gün"
    WIZARD_APPLY_DURATION = "Süreden Hesapla ve Vakitlere Ekle"
    WIZARD_DAILY_TARGET = "Günlük Kaza Kılma Hedefi"
    WIZARD_SAVE = "Kaza Planını Kaydet"


class NavStrings:
    HOME = "Vakitler"
    QAZA = "Kaza"
    SETTINGS = "Ayarlar"


class HomeStrings:
    """`%1`, `%2` yer tutucularını QML `"metin %1".arg(değer)` ile doldurur."""

    NO_TIMES = "Vakit bilgisi yok"
    NEXT_PRAYER = "Sıradaki Namaz: %1"
    NEXT_BADGE = "SIRADAKİ VAKİT"
    NEXT_TAG = "Sıradaki"
    SUNRISE_TAG = "Güneş Doğuşu"
    CONGREGATION_BADGE = "Cemaatle"
    PERFORMED = "Kılındı"
    COMPENSATED = "Kaza edildi"
    MISSED = "Kılınmadı"
    PENDING = "Bekliyor"
    TODAY_PRAYERS = "BUGÜNÜN NAMAZLARI  •  %1"
    DAY_PRAYERS = "NAMAZLAR  •  %1"
    COMPLETED_SUMMARY = "%1 / %2 Vakit Eda Edildi"
    PREVIOUS_DAY = "Önceki gün"
    NEXT_DAY = "Sonraki gün"
    GO_TODAY = "Bugüne dön"
    FUTURE_DAY_NOTE = "Gelecek gün: yalnızca vakitler gösterilir."
    COUNTDOWN_SEMANTICS = "%1 vaktine %2 kaldı"
    PRAYER_SEMANTICS = "%1 vakti saat %2, %3"


class PrayerDialogStrings:
    """"X namazını kıldınız mı?" diyaloğu."""

    QUESTION = "KILDINIZ MI?"
    CONGREGATION = "Cemaatle kıldım"
    CONGREGATION_HINT = "Cemaat sevabıyla kaydedilir"
    PERFORMED = "Kıldım"
    MISSED = "Kılmadım"
    DISMISS = "Vazgeç"

    @staticmethod
    def title(prayer_name: str) -> str:
        return f"{turkish_upper(prayer_name)} NAMAZINI"


class LocationStrings:
    NEEDED = "Namaz vakitleri için şehrinizi seçin."
    CHOOSE_CITY = "Şehir seç"
    PICKER_TITLE = "Şehir Seç"
    SEARCH_HINT = "Şehir ara"
    NO_RESULTS = "Eşleşen şehir yok"


class CommonStrings:
    APP_NAME = APP_NAME
    CANCEL = "İptal"
    DISMISS = "Vazgeç"
    COMING_SOON = "Bu ekran sonraki aşamada eklenecek."

    @staticmethod
    def version_label(version: str = __version__) -> str:
        return f"Sürüm {version}"


def ui_strings() -> dict:
    """QML'e `strings` olarak açılan iç içe sözlük. Anahtarlar camelCase'tir."""
    return {
        "nav": {"home": NavStrings.HOME, "qaza": NavStrings.QAZA, "settings": NavStrings.SETTINGS},
        "home": {
            "noTimes": HomeStrings.NO_TIMES,
            "nextPrayer": HomeStrings.NEXT_PRAYER,
            "nextBadge": HomeStrings.NEXT_BADGE,
            "nextTag": HomeStrings.NEXT_TAG,
            "sunriseTag": HomeStrings.SUNRISE_TAG,
            "congregationBadge": HomeStrings.CONGREGATION_BADGE,
            "performed": HomeStrings.PERFORMED,
            "compensated": HomeStrings.COMPENSATED,
            "missed": HomeStrings.MISSED,
            "pending": HomeStrings.PENDING,
            "todayPrayers": HomeStrings.TODAY_PRAYERS,
            "dayPrayers": HomeStrings.DAY_PRAYERS,
            "completedSummary": HomeStrings.COMPLETED_SUMMARY,
            "previousDay": HomeStrings.PREVIOUS_DAY,
            "nextDay": HomeStrings.NEXT_DAY,
            "goToday": HomeStrings.GO_TODAY,
            "futureDayNote": HomeStrings.FUTURE_DAY_NOTE,
            "countdownSemantics": HomeStrings.COUNTDOWN_SEMANTICS,
            "prayerSemantics": HomeStrings.PRAYER_SEMANTICS,
        },
        "dialog": {
            "question": PrayerDialogStrings.QUESTION,
            "congregation": PrayerDialogStrings.CONGREGATION,
            "congregationHint": PrayerDialogStrings.CONGREGATION_HINT,
            "performed": PrayerDialogStrings.PERFORMED,
            "missed": PrayerDialogStrings.MISSED,
            "dismiss": PrayerDialogStrings.DISMISS,
        },
        "qaza": {
            "autoDetected": QazaStrings.AUTO_DETECTED,
            "markedMissed": QazaStrings.MARKED_MISSED,
            "emptyTitle": QazaStrings.EMPTY_TITLE,
            "emptySubtitle": QazaStrings.EMPTY_SUBTITLE,
            "overviewTitle": QazaStrings.OVERVIEW_TITLE,
            "totalPrayersLabel": QazaStrings.TOTAL_PRAYERS_LABEL,
            "dailyTargetLabel": QazaStrings.DAILY_TARGET_LABEL,
            "dailyTargetValue": QazaStrings.DAILY_TARGET_VALUE,
            "estimatedFinish": QazaStrings.ESTIMATED_FINISH,
            "plannerButton": QazaStrings.PLANNER_BUTTON,
            "backlogSectionTitle": QazaStrings.BACKLOG_SECTION_TITLE,
            "trackedSectionTitle": QazaStrings.TRACKED_SECTION_TITLE,
            "decrementBacklog": QazaStrings.DECREMENT_BACKLOG,
            "remainingPrayerCount": QazaStrings.REMAINING_PRAYER_COUNT,
            "badge": QazaStrings.BADGE,
            "compensate": QazaStrings.COMPENSATE,
            "confirmTitle": QazaStrings.CONFIRM_TITLE,
            "confirmYes": QazaStrings.CONFIRM_YES,
            "confirmBody": QazaStrings.CONFIRM_BODY,
            "wizardTitle": QazaStrings.WIZARD_TITLE,
            "wizardSubtitle": QazaStrings.WIZARD_SUBTITLE,
            "wizardYears": QazaStrings.WIZARD_YEARS,
            "wizardMonths": QazaStrings.WIZARD_MONTHS,
            "wizardDays": QazaStrings.WIZARD_DAYS,
            "wizardApplyDuration": QazaStrings.WIZARD_APPLY_DURATION,
            "wizardDailyTarget": QazaStrings.WIZARD_DAILY_TARGET,
            "wizardSave": QazaStrings.WIZARD_SAVE,
        },
        "location": {
            "needed": LocationStrings.NEEDED,
            "chooseCity": LocationStrings.CHOOSE_CITY,
            "pickerTitle": LocationStrings.PICKER_TITLE,
            "searchHint": LocationStrings.SEARCH_HINT,
            "noResults": LocationStrings.NO_RESULTS,
        },
        "common": {
            "appName": CommonStrings.APP_NAME,
            "cancel": CommonStrings.CANCEL,
            "dismiss": CommonStrings.DISMISS,
            "comingSoon": CommonStrings.COMING_SOON,
            "versionLabel": CommonStrings.version_label(),
        },
    }
