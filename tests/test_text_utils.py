from app.core.text_utils import fold_turkish, turkish_upper


def test_turkish_upper_i_ve_dotsuz_i_kurali():
    assert turkish_upper("İkindi") == "İKİNDİ"
    assert turkish_upper("ikindi") == "İKİNDİ"
    assert turkish_upper("Yatsı") == "YATSI"
    assert turkish_upper("Öğle") == "ÖĞLE"
    assert turkish_upper("Akşam") == "AKŞAM"
    assert turkish_upper("Sabah") == "SABAH"


def test_python_upper_tuzagi_gercek():
    # Neden turkish_upper var: stok upper() Türkçe'de yanlış sonuç verir.
    assert "ikindi".upper() == "IKINDI"


def test_fold_turkish_buyuk_kucuk_ve_harf_farkini_yok_sayar():
    assert fold_turkish("İstanbul") == fold_turkish("istanbul") == "istanbul"
    assert fold_turkish("Şanlıurfa") == "sanliurfa"
    assert fold_turkish("IĞDIR") == "igdir"
    assert fold_turkish("Hakkâri") == "hakkari"
    assert fold_turkish("Çanakkale").find(fold_turkish("cana")) == 0


def test_fold_turkish_tum_illerde_kendini_bulur():
    from app.core.domain.cities import CITIES

    folded = [fold_turkish(c.city) for c in CITIES]
    assert len(set(folded)) == 81  # katlama iki ili birbirine çakıştırmaz

    def search(text: str) -> list[str]:
        return [c.city for c in CITIES if fold_turkish(text) in fold_turkish(c.city)]

    assert search("istanbul") == ["İstanbul"]
    assert search("igdir") == ["Iğdır"]
    assert search("SANLIURFA") == ["Şanlıurfa"]
    assert search("hakkari") == ["Hakkâri"]
