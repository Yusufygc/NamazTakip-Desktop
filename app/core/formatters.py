"""Saat ve süre biçimlendirme. Qt içe aktarmaz."""

import math
from datetime import datetime, timedelta


def format_time(moment: datetime) -> str:
    """`HH:mm`"""
    return f"{moment.hour:02d}:{moment.minute:02d}"


def format_countdown(remaining: timedelta) -> str:
    """`HH:mm:ss`. Saniye yukarı yuvarlanır; negatif süre 00:00:00 olur."""
    total = max(0, math.ceil(remaining.total_seconds()))
    hours, rest = divmod(total, 3600)
    minutes, seconds = divmod(rest, 60)
    return f"{hours:02d}:{minutes:02d}:{seconds:02d}"
