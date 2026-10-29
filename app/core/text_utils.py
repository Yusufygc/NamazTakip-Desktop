"""Türkçe harf yardımcıları.

Python `"ikindi".upper()` sonucu `"IKINDI"` verir; `"İ".lower()` ise birleşik nokta üretir.
Bu yüzden büyütme ve arama katlaması burada elle yapılır. Kaynak: mobil `text_utils.dart`.
"""

_FOLD_MAP = str.maketrans(
    {
        "ı": "i",
        "ş": "s",
        "ğ": "g",
        "ü": "u",
        "ö": "o",
        "ç": "c",
        "â": "a",
    }
)


def turkish_upper(text: str) -> str:
    """Türkçe kurallarına göre büyük harfe çevirir: `i → İ`, `ı → I` ("İkindi" → "İKİNDİ")."""
    return text.replace("i", "İ").replace("ı", "I").upper()


def fold_turkish(text: str) -> str:
    """Arama için Türkçe harfleri ve büyük/küçük farkını yok sayar.

    `İstanbul` ile `istanbul`, `Şanlıurfa` ile `sanliurfa`, `IĞDIR` ile `igdir` aynı katlanır.
    """
    return text.replace("İ", "i").replace("I", "ı").lower().translate(_FOLD_MAP)
