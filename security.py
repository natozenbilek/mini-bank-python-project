# Bu file (dosya) hazır; değiştirmeniz gerekmiyor.
#
# bank.py şifreleri saklarken buradaki iki function'ı (fonksiyon)
# kullanacak (2. görev). İçlerinde derste görmediğimiz hashlib ve secrets
# module'leri (modül) var; Python'la birlikte geliyorlar. Siz yalnız
# function'ları çağıracaksınız, tıpkı math.sqrt() gibi:
#     import security
#     security.sha256("kedi123")


import hashlib
import secrets


def sha256(text):
    """text'in SHA-256 hash'ini 64 karakterlik bir str (karakter dizisi)
    olarak return eder.

    Hash'i bir parmak izi gibi düşünün: aynı text her zaman aynı hash'i
    verir; text'te tek bir harf değişirse hash bambaşka olur. Hash'ten
    text'i geri bulmanın bilinen bir yolu yok.

    >>> sha256("kedi123")[:16]
    'f2bd50407c5e5e69'
    >>> sha256("kedi124")[:16]
    '6d2ba67fbbe65bf9'
    """
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def make_salt():
    """Rastgele, 16 karakterlik bir salt return eder: "9f2c41d07ab3e5c8"
    gibi. Her çağırdığınızda başka bir salt çıkar.

    salt, şifrenin önüne eklenen rastgele bir str. Her müşterinin salt'ı
    başka olduğu için aynı şifreyi seçen iki müşterinin hash'i de farklı
    çıkar.
    """
    return secrets.token_hex(8)
