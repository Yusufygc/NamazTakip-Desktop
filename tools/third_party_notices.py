"""THIRD_PARTY_NOTICES.md üretir: dağıtılan uygulamanın içindeki üçüncü taraf bileşenlerin lisansları.

Kullanım (bağımlılık değişince yeniden üret; `tests/test_release_packaging.py` dosyanın güncelliğini denetler):
    python tools/third_party_notices.py

Kaynak: `requirements.txt` (çalışma zamanı) ve `requirements-build.txt` (PyInstaller); lisans metinleri kurulu paketlerin
`dist-info` klasöründen alınır. MIT/BSD gibi "bildirimi kopyada bulundur" isteyen lisanslarda tam metin gömülür;
LGPL bileşenlerde tam metin yerine resmî adres ve kaynak kodun nereden alınacağı yazılır.
"""

import re
from importlib import metadata
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "THIRD_PARTY_NOTICES.md"

# paket -> (lisans, kaynak adresi, tam metin gömülsün mü)
COMPONENTS = {
    "PySide6": ("LGPL-3.0-only (Qt for Python)", "https://pyside.org", False),
    "PySide6-Essentials": ("LGPL-3.0-only (Qt for Python)", "https://pyside.org", False),
    "PySide6-Addons": ("LGPL-3.0-only (Qt for Python)", "https://pyside.org", False),
    "shiboken6": ("LGPL-3.0-only (Qt for Python)", "https://pyside.org", False),
    "adhanpy": ("MIT", "https://github.com/alphahm/adhanpy", True),
}

HEADER = """# Üçüncü taraf bileşenler ve lisansları

Namaz Takip'in kendi lisansı [LICENSE](LICENSE) dosyasındadır (tüm hakları saklıdır); aşağıdaki bileşenler kendi lisansları
altındadır ve bu lisanslar Namaz Takip'in lisansını değiştirmez. Dağıtılan uygulama (PyInstaller paketi) bu bileşenleri içerir.
Bu dosya `python tools/third_party_notices.py` ile üretilir.

## Qt (PySide6 / shiboken6): LGPL-3.0

Arayüz Qt 6 ile (Qt for Python) çizilir; Qt, **GNU LGPL sürüm 3** koşulları altında kullanılır
([metin](https://www.gnu.org/licenses/lgpl-3.0.html)). Uygulama klasör olarak dağıtılır (`--onedir`): Qt kütüphaneleri `_internal`
klasöründe ayrı dosyalardır ve değiştirilmiş bir Qt sürümüyle değiştirilebilir (yeniden bağlama hakkı). Uygulamanın kullanmadığı Qt
modülleri (WebEngine, Qt3D, Charts, Multimedia vb.) paketten çıkarılır; kalanlar değiştirilmez. Qt ve PySide6 kaynak kodu:
<https://code.qt.io> ve <https://pyside.org>. Qt'nin ticari lisansı kullanılmaz.

## Python ve PyInstaller

- **Python** ([PSF License](https://docs.python.org/3/license.html)): paketlenmiş yorumlayıcı ve standart kitaplık.
- **PyInstaller** ([GPL-2.0-or-later, derlenen uygulamanın dağıtımına izin veren özel istisnayla](https://github.com/pyinstaller/pyinstaller/blob/develop/COPYING.txt)):
  yalnızca paketleme aracı ve açılış yükleyicisi; paketlenen uygulamaya GPL bulaşmaz.

"""


def license_text(distribution: metadata.Distribution) -> str:
    """Paketin lisans dosyası (`dist-info/LICENSE` ya da `dist-info/licenses/…`); yoksa boş."""
    for file in distribution.files or []:
        name = str(file).replace("\\", "/")
        inside_dist_info = ".dist-info/" in name
        if inside_dist_info and Path(name).name.upper().startswith(("LICENSE", "COPYING")):
            return distribution.locate_file(file).read_text(encoding="utf-8").strip()
    return ""


def render() -> str:
    lines = [HEADER.rstrip("\n"), "", "## Python paketleri", ""]
    for package, (license_name, url, embed) in COMPONENTS.items():
        distribution = metadata.distribution(package)
        lines += [f"### {package} {distribution.version}", "", f"- Lisans: {license_name}", f"- Kaynak: <{url}>", ""]
        if embed:
            lines += ["```text", license_text(distribution), "```", ""]
    return "\n".join(lines).rstrip("\n") + "\n"


def requirement_versions() -> dict:
    """`requirements.txt` ve `requirements-build.txt` içindeki `paket==sürüm` satırları (paket adı küçük harfle)."""
    versions = {}
    for name in ("requirements.txt", "requirements-build.txt"):
        for line in (ROOT / name).read_text(encoding="utf-8").splitlines():
            match = re.match(r"^([A-Za-z0-9_.-]+)==([^;\s]+)", line)
            if match:
                versions[match.group(1).lower().replace("_", "-")] = match.group(2)
    return versions


if __name__ == "__main__":
    OUTPUT.write_bytes(render().encode("utf-8"))
    print("Yazıldı:", OUTPUT)
