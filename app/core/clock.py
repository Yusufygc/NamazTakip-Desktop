"""Şimdiki zaman kaynağı. Testlerde sahte saat verilebilsin diye tek yerde tutulur."""

from collections.abc import Callable
from datetime import datetime

Clock = Callable[[], datetime]


def system_now() -> datetime:
    """Sistem saat diliminde, saat dilimli (aware) şimdiki an."""
    return datetime.now().astimezone()
