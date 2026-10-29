"""Uygulama ve tepsi simgelerini üretir: `app/ui/assets/app.ico` (çok boyutlu) ve `tray.png`.

Simge: zümrüt yeşili yuvarlak kare üstünde altın 8 köşeli Selçuklu yıldızı (arayüzdeki `star8` motifi).
Kullanım: `python tools/make_icons.py` (proje kökünden). Qt gerektirir; ekran gerekmez.
"""

import math
import os
import struct
import sys
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtCore import QBuffer, QByteArray, QIODevice, QPointF, Qt  # noqa: E402
from PySide6.QtGui import QBrush, QColor, QGuiApplication, QImage, QPainter, QPainterPath, QPen  # noqa: E402

ASSETS = Path(__file__).resolve().parent.parent / "app" / "ui" / "assets"
ICO_SIZES = (16, 24, 32, 48, 64, 128, 256)
BACKGROUND = QColor("#1B5E43")
GOLD = QColor("#C89D3C")


def star_path(size: int) -> QPainterPath:
    """8 köşeli yıldız (dış yarıçap 0,40, iç yarıçap 0,185 · boyut)."""
    center = size / 2
    outer, inner = size * 0.40, size * 0.185
    path = QPainterPath()
    for k in range(16):
        angle = math.radians(k * 22.5 - 90)
        radius = outer if k % 2 == 0 else inner
        point = QPointF(center + radius * math.cos(angle), center + radius * math.sin(angle))
        path.moveTo(point) if k == 0 else path.lineTo(point)
    path.closeSubpath()
    return path


def render(size: int) -> QImage:
    image = QImage(size, size, QImage.Format.Format_ARGB32)
    image.fill(Qt.GlobalColor.transparent)
    painter = QPainter(image)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    painter.setPen(Qt.PenStyle.NoPen)
    painter.setBrush(QBrush(BACKGROUND))
    painter.drawRoundedRect(0, 0, size, size, size * 0.22, size * 0.22)
    painter.setBrush(QBrush(GOLD))
    painter.setPen(QPen(GOLD, max(1.0, size / 64)))
    painter.drawPath(star_path(size))
    painter.end()
    return image


def png_bytes(image: QImage) -> bytes:
    data = QByteArray()
    buffer = QBuffer(data)
    buffer.open(QIODevice.OpenModeFlag.WriteOnly)
    image.save(buffer, "PNG")
    buffer.close()
    return bytes(data)


def build_ico(sizes) -> bytes:
    """PNG kareli ICO dosyası (Windows Vista+ ve Qt okur)."""
    frames = [(size, png_bytes(render(size))) for size in sizes]
    header = struct.pack("<HHH", 0, 1, len(frames))
    offset = 6 + 16 * len(frames)
    entries, payload = b"", b""
    for size, data in frames:
        dimension = 0 if size >= 256 else size  # 0 = 256
        entries += struct.pack("<BBBBHHII", dimension, dimension, 0, 0, 1, 32, len(data), offset)
        payload += data
        offset += len(data)
    return header + entries + payload


def main() -> int:
    app = QGuiApplication.instance() or QGuiApplication(sys.argv)  # noqa: F841 (QPainter için gerekli)
    ASSETS.mkdir(parents=True, exist_ok=True)
    (ASSETS / "app.ico").write_bytes(build_ico(ICO_SIZES))
    render(64).save(str(ASSETS / "tray.png"), "PNG")
    print(f"Yazıldı: {ASSETS / 'app.ico'}, {ASSETS / 'tray.png'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
