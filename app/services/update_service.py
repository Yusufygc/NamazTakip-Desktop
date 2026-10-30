"""Güncelleme denetimi: GitHub'ın son sürüm kaydını okuyup kurulu sürümle karşılaştırır, kurulum dosyasını indirir. Qt içe aktarmaz.

Güvenlik ve gizlilik:
- Tek istek: `GET https://api.github.com/repos/<depo>/releases/latest`. Kimlik bilgisi, kullanıcı verisi ya da kullanıcı kimliği
  gönderilmez (yalnızca `User-Agent: NamazTakip/<sürüm>`). Kapatma: Ayarlar ya da `NAMAZ_TAKIP_NO_UPDATE_CHECK=1`.
- Yanıt boyutu ve süre sınırlıdır; yanıttaki adresler yalnızca `https://github.com/<depo>/...` ise kabul edilir (sahte adres
  içeren yanıt reddedilir). Sürüm notu düz metin olarak gösterilir.
- Kurulum dosyası yalnızca kullanıcı "Güncelle" derse indirilir: adres yalnızca bu deponun `releases/download/` yoludur, boyut ve SHA-256
  özeti doğrulanır (GitHub'ın verdiği `digest` ya da Release'teki `.sha256` dosyası; ikisi de yoksa güncelleme reddedilir), uyuşmazsa
  dosya silinir. Sonra kurulum dosyası sabit argümanlarla (kabuk yok) başlatılır; uygulama kapanır, kurulum üstüne yazar ve uygulama
  yeniden açılır (Inno `Check: RelaunchAfterUpdate`). Bu kontroller kaldırılmaz. Ayrıntı: docs/wiki/guncelleme.md
"""

import contextlib
import hashlib
import json
import os
import re
import subprocess
import tempfile
import urllib.error
import urllib.request
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import urlparse

from app.core.strings import UpdateStrings
from app.version import RELEASE_REPO, __version__

API_URL = "https://api.github.com/repos/{repo}/releases/latest"
API_HOST = "api.github.com"
TIMEOUT_SECONDS = 8
MAX_RESPONSE_BYTES = 1_000_000
MAX_NOTES_CHARS = 4000
INSTALLER_PATTERN = re.compile(r"^NamazTakip-Setup-[0-9.]+\.exe$")
MAX_INSTALLER_BYTES = 400 * 1024 * 1024
DOWNLOAD_CHUNK_BYTES = 64 * 1024
DOWNLOAD_TIMEOUT_SECONDS = 30
UPDATE_DIR_NAME = "NamazTakipUpdate"
USER_AGENT_NAME = "NamazTakip"
OPT_OUT_ENV = "NAMAZ_TAKIP_NO_UPDATE_CHECK"
BLOCKED_WINERRORS = (4551, 1260)  # 4551: Uygulama Denetimi ilkesi engelledi; 1260: grup ilkesi engelledi
_VERSION = re.compile(r"v?(\d+)\.(\d+)\.(\d+)")
_SHA256 = re.compile(r"^\s*([0-9a-fA-F]{64})(?:\s|$)")
_DOWNLOAD_HOSTS = ("github.com", "githubusercontent.com")


class UpdateCheckError(Exception):
    """Denetim yapılamadı (ağ yok, GitHub hatası, bozuk yanıt); mesaj kullanıcıya gösterilebilir."""


class InstallerBlockedError(UpdateCheckError):
    """Windows (Akıllı Uygulama Denetimi) kurulum dosyasının başlatılmasına izin vermedi. Dosya indirildi ve doğrulandı:
    kullanıcı Gezgin'den çift tıklayarak kurabilir (ya da bir süre sonra yeniden deneyebilir)."""

    def __init__(self, path: Path):
        super().__init__(UpdateStrings.BLOCKED)
        self.path = path


@dataclass(frozen=True)
class UpdateInfo:
    version: str  # "0.2.0"
    tag: str  # "v0.2.0"
    page_url: str  # sürüm sayfası
    download_url: str  # kurulum dosyası; yoksa boş (sayfa açılır)
    asset_name: str
    size: int
    notes: str
    published: str  # "2026-10-30"
    sha256: str = ""  # GitHub'ın verdiği özet ("sha256:" önekiz); yoksa checksum_url'deki dosyadan okunur
    checksum_url: str = ""  # Release'teki `<kurulum>.sha256` dosyası


def parse_version(text: "str | None") -> "tuple[int, int, int] | None":
    """`v0.2.0` / `0.2.0` -> (0, 2, 0). Ön sürüm (`0.2.0-rc1`) ve biçimsiz metin None döner."""
    match = _VERSION.fullmatch((text or "").strip())
    if not match:
        return None
    major, minor, patch = (int(part) for part in match.groups())
    return major, minor, patch


def is_newer(candidate: str, current: str = __version__) -> bool:
    new, old = parse_version(candidate), parse_version(current)
    return new is not None and old is not None and new > old


def updates_disabled_by_environment() -> bool:
    return os.environ.get(OPT_OUT_ENV, "").strip().lower() in ("1", "true", "yes")


def _trusted_url(url: object, repo: str) -> str:
    """Yalnızca bu depoya ait https://github.com adresi; aksi hâlde boş."""
    if not isinstance(url, str):
        return ""
    parsed = urlparse(url)
    if parsed.scheme == "https" and parsed.hostname == "github.com" and parsed.path.startswith(f"/{repo}/"):
        return url
    return ""


_HEADING = re.compile(r"^\s{0,3}#{1,6}\s*", re.MULTILINE)
_BULLET = re.compile(r"^(\s*)[*+]\s+", re.MULTILINE)


def plain_notes(markdown: str) -> str:
    """GitHub'ın Markdown sürüm notunu düz metne indirger (`## Başlık` -> `Başlık`, `**kalın**` -> `kalın`, `* madde` -> `- madde`)."""
    text = _BULLET.sub(r"\1- ", _HEADING.sub("", markdown.replace("\r\n", "\n")))
    return text.replace("**", "").replace("__", "").strip()


def _installer_asset(data: dict, repo: str) -> tuple[str, str, int, str, str]:
    """(ad, indirme adresi, boyut, SHA-256, `.sha256` dosyası adresi); kurulum dosyası yoksa boş değerler."""
    assets = [asset for asset in data.get("assets") or [] if isinstance(asset, dict)]
    for asset in assets:
        name = asset.get("name")
        url = _trusted_url(asset.get("browser_download_url"), repo)
        if isinstance(name, str) and INSTALLER_PATTERN.match(name) and url:
            size = asset.get("size")
            digest = asset.get("digest") if isinstance(asset.get("digest"), str) else ""
            sha256 = digest.removeprefix("sha256:").lower() if digest.startswith("sha256:") else ""
            checksum = next(
                (_trusted_url(other.get("browser_download_url"), repo) for other in assets if other.get("name") == name + ".sha256"), ""
            )
            return name, url, size if isinstance(size, int) and size > 0 else 0, sha256, checksum
    return "", "", 0, "", ""


def release_to_update(data: object, current: str = __version__, repo: str = RELEASE_REPO) -> "UpdateInfo | None":
    """GitHub sürüm kaydından `UpdateInfo`; taslak, ön sürüm, daha eski / aynı sürüm ya da güvenilmez adres için None."""
    if not isinstance(data, dict) or data.get("draft") or data.get("prerelease"):
        return None
    tag = data.get("tag_name")
    if not isinstance(tag, str) or not is_newer(tag, current):
        return None
    page_url = _trusted_url(data.get("html_url"), repo)
    if not page_url:
        raise UpdateCheckError(UpdateStrings.UNTRUSTED_RELEASE_ADDRESS)
    name, download_url, size, sha256, checksum_url = _installer_asset(data, repo)
    notes = data.get("body") if isinstance(data.get("body"), str) else ""
    published = data.get("published_at") if isinstance(data.get("published_at"), str) else ""
    return UpdateInfo(
        version=tag.lstrip("v"),
        tag=tag,
        page_url=page_url,
        download_url=download_url,
        asset_name=name,
        size=size,
        notes=plain_notes(notes)[:MAX_NOTES_CHARS],
        published=published[:10],
        sha256=sha256,
        checksum_url=checksum_url,
    )


def fetch_latest_release(repo: str = RELEASE_REPO, current: str = __version__) -> "dict | None":
    """En son yayınlanmış sürümün kaydı; hiç sürüm yoksa (404) None."""
    request = urllib.request.Request(
        API_URL.format(repo=repo),
        headers={"Accept": "application/vnd.github+json", "User-Agent": f"{USER_AGENT_NAME}/{current}"},
    )
    try:
        with urllib.request.urlopen(request, timeout=TIMEOUT_SECONDS) as response:
            if urlparse(response.geturl()).hostname != API_HOST:
                raise UpdateCheckError(UpdateStrings.REDIRECTED)
            body = response.read(MAX_RESPONSE_BYTES + 1)
    except urllib.error.HTTPError as error:
        if error.code == 404:
            return None
        if error.code in (403, 429):
            raise UpdateCheckError(UpdateStrings.RATE_LIMITED) from error
        raise UpdateCheckError(UpdateStrings.http_error(error.code)) from error
    except (urllib.error.URLError, TimeoutError, OSError) as error:
        raise UpdateCheckError(UpdateStrings.UNREACHABLE) from error
    if len(body) > MAX_RESPONSE_BYTES:
        raise UpdateCheckError(UpdateStrings.RESPONSE_TOO_LARGE)
    try:
        return json.loads(body.decode("utf-8"))
    except (UnicodeDecodeError, ValueError) as error:
        raise UpdateCheckError(UpdateStrings.RESPONSE_UNREADABLE) from error


def check_for_update(
    current: str = __version__,
    repo: str = RELEASE_REPO,
    fetch: "Callable[..., dict | None]" = fetch_latest_release,
) -> "UpdateInfo | None":
    """Daha yeni bir sürüm varsa `UpdateInfo`, yoksa None; denetlenemezse `UpdateCheckError` fırlatır."""
    return release_to_update(fetch(repo, current), current, repo)


# ---- İndirme ve kurulum (uygulama içi güncelleme) ---------------------------------------------------------------------

ProgressCallback = Callable[[int], None]


def parse_checksum_file(text: str) -> str:
    """`<64 hane> *dosya` biçimindeki özet dosyasından SHA-256; biçim bozuksa boş."""
    match = _SHA256.match(text or "")
    return match.group(1).lower() if match else ""


def update_directory() -> Path:
    return Path(tempfile.gettempdir()) / UPDATE_DIR_NAME


def _host_allowed(url: str) -> bool:
    parsed = urlparse(url)
    host = parsed.hostname or ""
    return parsed.scheme == "https" and any(host == allowed or host.endswith("." + allowed) for allowed in _DOWNLOAD_HOSTS)


def _open_download(url: str, opener: Callable = urllib.request.urlopen):
    request = urllib.request.Request(url, headers={"User-Agent": f"{USER_AGENT_NAME}/{__version__}"})
    try:
        response = opener(request, timeout=DOWNLOAD_TIMEOUT_SECONDS)
    except (urllib.error.URLError, TimeoutError, OSError) as error:
        raise UpdateCheckError(UpdateStrings.SERVER_UNREACHABLE) from error
    if not _host_allowed(response.geturl()):
        response.close()
        raise UpdateCheckError(UpdateStrings.REDIRECTED)
    return response


def _expected_sha256(info: UpdateInfo, opener: Callable) -> str:
    if info.sha256:
        return info.sha256.lower()
    if info.checksum_url:
        with _open_download(info.checksum_url, opener) as response:
            return parse_checksum_file(response.read(1024).decode("utf-8", errors="replace"))
    return ""


def download_installer(
    info: UpdateInfo,
    progress: "ProgressCallback | None" = None,
    opener: Callable = urllib.request.urlopen,
    directory: "Path | None" = None,
) -> Path:
    """Kurulum dosyasını geçici klasöre indirir; boyut ya da SHA-256 uyuşmazsa dosyayı silip `UpdateCheckError` verir."""
    if not info.download_url or not INSTALLER_PATTERN.match(info.asset_name):
        raise UpdateCheckError(UpdateStrings.NO_INSTALLER)
    expected = _expected_sha256(info, opener)
    if not expected:
        raise UpdateCheckError(UpdateStrings.NO_CHECKSUM)
    target_dir = directory or update_directory()
    target_dir.mkdir(parents=True, exist_ok=True)
    target = target_dir / info.asset_name
    limit = min(info.size, MAX_INSTALLER_BYTES) if info.size else MAX_INSTALLER_BYTES
    digest, received = hashlib.sha256(), 0
    try:
        with _open_download(info.download_url, opener) as response, target.open("wb") as out:
            while chunk := response.read(DOWNLOAD_CHUNK_BYTES):
                received += len(chunk)
                if received > limit:
                    raise UpdateCheckError(UpdateStrings.DOWNLOAD_TOO_LARGE)
                out.write(chunk)
                digest.update(chunk)
                if progress is not None and info.size > 0:
                    progress(min(100, received * 100 // info.size))
        if info.size and received != info.size:
            raise UpdateCheckError(UpdateStrings.DOWNLOAD_INCOMPLETE)
        if digest.hexdigest() != expected:
            raise UpdateCheckError(UpdateStrings.DOWNLOAD_UNVERIFIED)
    except UpdateCheckError:
        target.unlink(missing_ok=True)
        raise
    except OSError as error:
        target.unlink(missing_ok=True)
        raise UpdateCheckError(UpdateStrings.download_error(error.strerror or str(error))) from error
    return target


def _shell_execute(installer: Path, parameters: str) -> None:
    """Gezgin'de çift tıklamayla aynı yol (ShellExecute); doğrudan süreç oluşturma engellendiğinde ikinci deneme."""
    import ctypes

    result = ctypes.windll.shell32.ShellExecuteW(None, "open", str(installer), parameters, str(installer.parent), 1)
    if result <= 32:
        raise OSError(result, "ShellExecute başarısız")


def launch_installer(installer: Path, popen: Callable = subprocess.Popen, shell_execute: Callable = _shell_execute) -> None:
    """Kurulumu uygulamadan bağımsız başlatır (kabuk yok, sabit argümanlar); çağıran uygulamayı kapatmalıdır.

    `/SILENT`: ilerleme penceresiyle sormadan kurar, çalışan uygulamayı kapatır, kurulumdan sonra uygulama yeniden açılır
    (Inno betiğindeki `Check: RelaunchAfterUpdate`). Sessiz kurulum hata göstermez: neden `install.log` içindedir.
    """
    if os.name != "nt":
        raise UpdateCheckError(UpdateStrings.WINDOWS_ONLY)
    if not INSTALLER_PATTERN.match(installer.name) or not installer.is_file():
        raise UpdateCheckError(UpdateStrings.INSTALLER_MISSING)
    flags = getattr(subprocess, "DETACHED_PROCESS", 0) | getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0)
    log = installer.with_name("install.log")
    try:
        popen([str(installer), "/SILENT", "/SUPPRESSMSGBOXES", "/CLOSEAPPLICATIONS", f"/LOG={log}"], close_fds=True, creationflags=flags)
    except OSError as error:
        if getattr(error, "winerror", None) not in BLOCKED_WINERRORS:
            raise UpdateCheckError(UpdateStrings.launch_error(error.strerror or str(error))) from error
        try:  # Gezgin yolu: doğrudan başlatma engellense de çift tıklama çalışabilir
            shell_execute(installer, f'/SILENT /SUPPRESSMSGBOXES /CLOSEAPPLICATIONS "/LOG={log}"')
        except OSError:
            raise InstallerBlockedError(installer) from error


def cleanup_update_directory(directory: "Path | None" = None) -> None:
    """Önceki güncellemeden kalan indirilmiş kurulum dosyalarını siler (açılışta, en iyi çaba)."""
    target = directory or update_directory()
    if not target.is_dir():
        return
    for path in target.iterdir():
        if path.is_file() and (INSTALLER_PATTERN.match(path.name) or path.name == "install.log"):
            with contextlib.suppress(OSError):  # kurulum dosyası hâlâ kilitli olabilir; sonraki açılışta yeniden denenir
                path.unlink()
