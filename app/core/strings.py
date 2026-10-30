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

    @staticmethod
    def pre_title(prayer_name: str, minutes: int) -> str:
        return f"{prayer_name} vaktine {minutes} dk kaldı"

    @staticmethod
    def pre_body(time_text: str) -> str:
        return f"Vakit girişi: {time_text}"


class MissedStrings:
    """Açılışta "uygulama kapalıyken giren vakitleri kıldınız mı?" diyaloğu ve gizli başlatma bildirimi."""

    NOTIFICATION_TITLE = "İşaretlenmemiş vakitler var"
    NOTIFICATION_BODY = "Uygulama kapalıyken giren vakitleri işaretlemek için dokunun."
    TITLE = "Bu vakitleri kıldınız mı?"
    BODY = "Uygulama kapalıyken şu vakitler girdi. İşaretlemezseniz gün bitince kaza listesine düşer."
    PERFORMED = "Kıldım"
    MISSED = "Kılmadım"
    LATER = "Sonra"
    ROW_SEMANTICS = "%1 namazı, %2"


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


class SettingsStrings:
    """Ayarlar ekranı. `%1` yer tutucusunu QML `.arg()` doldurur."""

    SECTION_NOTIFICATIONS = "Bildirimler"
    NOTIFICATIONS = "Bildirimler"
    NOTIFICATIONS_SUBTITLE = 'Vakitten önce haber, ezan vakti ve "kıldın mı" hatırlatmaları'
    PRE_REMINDER = "Vakitten önce haber ver"
    PRE_REMINDER_SUBTITLE = "Yeni vakit girmeden kaç dakika önce"
    PRE_REMINDER_OFF = "Kapalı"
    REMINDER_DELAY = "Hatırlatma süresi"
    REMINDER_DELAY_SUBTITLE = "Ezandan kaç dakika sonra"
    MINUTES = "%1 dk"

    SECTION_LOCATION = "Konum ve Vakitler"
    LOCATION_IN_USE = "Vakit hesabında kullanılan konum"
    NO_CITY = "Şehir seçilmedi"
    CALC_METHOD = "Hesaplama yöntemi"

    SECTION_DESKTOP = "Masaüstü"
    AUTOSTART = "Windows açılışında başlat"
    AUTOSTART_SUBTITLE = "Bilgisayar açılınca uygulama tepside çalışmaya başlar"
    CLOSE_TO_TRAY = "Pencereyi kapatınca tepsiye küçült"
    CLOSE_TO_TRAY_SUBTITLE = "Kapatınca uygulama kapanmaz; vakit bildirimleri gelmeye devam eder"

    SECTION_THEME = "Tema"
    THEME_SEMANTICS = "Tema: %1"
    # Tema anahtarı -> (ad, alt başlık). Mobil `SettingsStrings.themeName/themeSubtitle` ile aynı.
    THEMES = {
        "default": ("Varsayılan", "Selçuklu Zümrüdü"),
        "dark": ("Koyu", "Gece Kubbesi"),
        "ocean": ("Okyanus", "İznik Çinisi"),
        "rose": ("Gül Kurusu", "Bordo & Gül"),
        "gold": ("Altın", "Tezhip Altını"),
    }


class TrayStrings:
    """Sistem tepsisi menüsü, ipucu ve ilk kapatma bilgisi. `%1`, `%2` yer tutucularını QML `.arg()` doldurur."""

    SHOW = "Göster"
    HIDE = "Gizle"
    NEXT_PRAYER = "Sıradaki: %1 %2"
    NOTIFICATIONS_ON = "Bildirimler: Açık"
    NOTIFICATIONS_OFF = "Bildirimler: Kapalı"
    QUIT = "Çıkış"
    TOOLTIP = "Namaz Takip  •  Sıradaki: %1 %2"
    TOOLTIP_IDLE = "Namaz Takip"
    HINT_TITLE = "Namaz Takip tepside çalışıyor"
    HINT_BODY = (
        "Pencereyi kapattınız; uygulama arka planda çalışmaya devam eder ve vakit bildirimlerini gösterir. "
        "Tamamen kapatmak için tepsi simgesinden Çıkış'ı seçin."
    )


class AutostartPromptStrings:
    """İlk açılışta "Windows açılınca başlasın mı?" sorusu."""

    TITLE = "Windows açılınca başlasın mı?"
    BODY = (
        "Vakit bildirimlerinin gelmesi için uygulamanın bilgisayar açıldığında tepside çalışması gerekir. "
        "Bunu sonradan Ayarlar'dan değiştirebilirsiniz."
    )
    YES = "Evet, başlasın"
    NO = "Hayır"


class UpdateStrings:
    """Uygulama içi güncelleme: servis/köprü iletileri (Python) ve pencere/kart metinleri (QML `%1` ile)."""

    # Servis ve köprü iletileri (kullanıcıya gösterilebilir)
    CHECKING = "Güncellemeler denetleniyor…"
    CHECK_FAILED = "Güncelleme denetimi yapılamadı."
    DOWNLOAD_FAILED = "Güncelleme indirilemedi."
    INSTALL_FAILED = "Kurulum başlatılamadı."
    RELEASE_PAGE_HINT = "Sürüm sayfası tarayıcıda açılır."
    UNTRUSTED_RELEASE_ADDRESS = "Sürüm kaydındaki adres güvenilir değil, yok sayıldı."
    REDIRECTED = "Beklenmeyen bir adrese yönlendirildi."
    RATE_LIMITED = "GitHub istek sınırına ulaşıldı; biraz sonra yeniden deneyin."
    UNREACHABLE = "GitHub'a ulaşılamadı. İnternet bağlantınızı denetleyin."
    RESPONSE_TOO_LARGE = "Yanıt beklenenden büyük, yok sayıldı."
    RESPONSE_UNREADABLE = "GitHub yanıtı okunamadı."
    SERVER_UNREACHABLE = "Güncelleme sunucusuna ulaşılamadı."
    NO_INSTALLER = "Bu sürümde kurulum dosyası yok; sürüm sayfasından indirin."
    NO_CHECKSUM = "Kurulum dosyasının SHA-256 özeti bulunamadı; güvenlik için güncelleme iptal edildi."
    DOWNLOAD_TOO_LARGE = "İndirilen dosya beklenenden büyük; iptal edildi."
    DOWNLOAD_INCOMPLETE = "İndirilen dosya eksik; boyut uyuşmuyor."
    DOWNLOAD_UNVERIFIED = "İndirilen dosya doğrulanamadı; özet uyuşmuyor."
    WINDOWS_ONLY = "Otomatik kurulum yalnızca Windows'ta desteklenir."
    INSTALLER_MISSING = "Kurulum dosyası bulunamadı."
    BLOCKED = (
        "Windows (Akıllı Uygulama Denetimi) kurulum dosyasını şimdilik engelledi. Dosya indirildi ve doğrulandı; "
        "klasörde gösterildi: çift tıklayarak kurabilirsiniz. Olmazsa birkaç dakika sonra yeniden deneyin."
    )
    WAITING_FOR_WINDOWS = (
        "Windows (Akıllı Uygulama Denetimi) kurulum dosyasını denetliyor; engel kalkınca kurulum kendiliğinden başlayacak. Bekleniyor…"
    )

    @staticmethod
    def up_to_date(version: str) -> str:
        return f"Güncelsiniz: v{version} en son sürüm."

    @staticmethod
    def new_version(version: str) -> str:
        return f"Yeni sürüm var: v{version}"

    @staticmethod
    def http_error(code: int) -> str:
        return f"GitHub yanıt hatası ({code})."

    @staticmethod
    def download_error(reason: str) -> str:
        return f"Güncelleme indirilemedi: {reason}"

    @staticmethod
    def launch_error(reason: str) -> str:
        return f"Kurulum başlatılamadı: {reason}"

    # Pencere ve Ayarlar kartı (QML `.arg()` ile doldurulur)
    DIALOG_TITLE = "Yeni sürüm var"
    HEADLINE = "Namaz Takip v%1 yayınlandı"
    VERSIONS = "Kurulu sürüm: v%1"
    PUBLISHED = "  •  Yayın tarihi: %1"
    FILE = "İndirilecek dosya: %1"
    EXPLANATION = (
        "Güncelle: kurulum dosyası indirilir ve SHA-256 özeti doğrulanır, uygulama kapanır, kurulum üstüne yazar ve "
        "uygulama yeniden açılır. Verileriniz ve yedekleriniz korunur."
    )
    SKIP = "Bu Sürümü Atla"
    LATER = "Sonra"
    STOP_WAITING = "Beklemeyi Bırak"
    RELEASE_PAGE = "Sürüm Sayfası"
    UPDATE = "Güncelle"
    DOWNLOADING = "İndiriliyor… %1%"
    WAITING_BUTTON = "Windows bekleniyor…"
    NOTIFICATION_TITLE = "Yeni sürüm var"
    NOTIFICATION_BODY = "Namaz Takip v%1 yayınlandı. Güncellemek için pencereyi açın."
    SECTION = "Güncellemeler"
    CHECK_ON_START = "Açılışta güncellemeyi denetle"
    CHECK_ON_START_SUBTITLE = "GitHub'a yalnızca son sürüm sorulur; kimlik ya da kullanım bilgisi gönderilmez"
    CURRENT_VERSION = "Kurulu sürüm: v%1"
    CHECK_NOW = "Şimdi Denetle"


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
    TAGLINE = "Günlük namazlarınızı kolayca takip edin"

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
        "settings": {
            "sectionNotifications": SettingsStrings.SECTION_NOTIFICATIONS,
            "notifications": SettingsStrings.NOTIFICATIONS,
            "notificationsSubtitle": SettingsStrings.NOTIFICATIONS_SUBTITLE,
            "preReminder": SettingsStrings.PRE_REMINDER,
            "preReminderSubtitle": SettingsStrings.PRE_REMINDER_SUBTITLE,
            "preReminderOff": SettingsStrings.PRE_REMINDER_OFF,
            "reminderDelay": SettingsStrings.REMINDER_DELAY,
            "reminderDelaySubtitle": SettingsStrings.REMINDER_DELAY_SUBTITLE,
            "minutes": SettingsStrings.MINUTES,
            "sectionLocation": SettingsStrings.SECTION_LOCATION,
            "locationInUse": SettingsStrings.LOCATION_IN_USE,
            "noCity": SettingsStrings.NO_CITY,
            "calcMethod": SettingsStrings.CALC_METHOD,
            "sectionDesktop": SettingsStrings.SECTION_DESKTOP,
            "autostart": SettingsStrings.AUTOSTART,
            "autostartSubtitle": SettingsStrings.AUTOSTART_SUBTITLE,
            "closeToTray": SettingsStrings.CLOSE_TO_TRAY,
            "closeToTraySubtitle": SettingsStrings.CLOSE_TO_TRAY_SUBTITLE,
            "sectionTheme": SettingsStrings.SECTION_THEME,
            "themeSemantics": SettingsStrings.THEME_SEMANTICS,
            "themes": {key: {"name": name, "subtitle": subtitle} for key, (name, subtitle) in SettingsStrings.THEMES.items()},
        },
        "tray": {
            "show": TrayStrings.SHOW,
            "hide": TrayStrings.HIDE,
            "nextPrayer": TrayStrings.NEXT_PRAYER,
            "notificationsOn": TrayStrings.NOTIFICATIONS_ON,
            "notificationsOff": TrayStrings.NOTIFICATIONS_OFF,
            "quit": TrayStrings.QUIT,
            "tooltip": TrayStrings.TOOLTIP,
            "tooltipIdle": TrayStrings.TOOLTIP_IDLE,
            "hintTitle": TrayStrings.HINT_TITLE,
            "hintBody": TrayStrings.HINT_BODY,
        },
        "autostart": {
            "title": AutostartPromptStrings.TITLE,
            "body": AutostartPromptStrings.BODY,
            "yes": AutostartPromptStrings.YES,
            "no": AutostartPromptStrings.NO,
        },
        "update": {
            "dialogTitle": UpdateStrings.DIALOG_TITLE,
            "headline": UpdateStrings.HEADLINE,
            "versions": UpdateStrings.VERSIONS,
            "published": UpdateStrings.PUBLISHED,
            "file": UpdateStrings.FILE,
            "explanation": UpdateStrings.EXPLANATION,
            "skip": UpdateStrings.SKIP,
            "later": UpdateStrings.LATER,
            "stopWaiting": UpdateStrings.STOP_WAITING,
            "releasePage": UpdateStrings.RELEASE_PAGE,
            "update": UpdateStrings.UPDATE,
            "downloading": UpdateStrings.DOWNLOADING,
            "waitingButton": UpdateStrings.WAITING_BUTTON,
            "notificationTitle": UpdateStrings.NOTIFICATION_TITLE,
            "notificationBody": UpdateStrings.NOTIFICATION_BODY,
            "section": UpdateStrings.SECTION,
            "checkOnStart": UpdateStrings.CHECK_ON_START,
            "checkOnStartSubtitle": UpdateStrings.CHECK_ON_START_SUBTITLE,
            "currentVersion": UpdateStrings.CURRENT_VERSION,
            "checkNow": UpdateStrings.CHECK_NOW,
        },
        "missed": {
            "notificationTitle": MissedStrings.NOTIFICATION_TITLE,
            "notificationBody": MissedStrings.NOTIFICATION_BODY,
            "title": MissedStrings.TITLE,
            "body": MissedStrings.BODY,
            "performed": MissedStrings.PERFORMED,
            "missed": MissedStrings.MISSED,
            "later": MissedStrings.LATER,
            "rowSemantics": MissedStrings.ROW_SEMANTICS,
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
            "tagline": CommonStrings.TAGLINE,
            "versionLabel": CommonStrings.version_label(),
        },
    }
