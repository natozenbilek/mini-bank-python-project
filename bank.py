# Introduction to Python, Proje ödevi
# Kendi bankanızı kurun
# IEEE Hacettepe University Student Branch, Güz 2026
#
# Bu projenin sonunda küçük bir bankanın internet bankacılığını yazmış
# olacaksınız: müşteriler şifreyle giriyor; aynı şubeye, başka şubelere
# ve başka bankalara para gönderiyor; kredi kartıyla alışveriş yapıp
# ekstresine bakıyor; döviz alıyor, kredi taksitini hesaplıyor, ATM'den
# kartsız para çekiyor. Uygulamanın ekranı hazır; arkasındaki hesapların
# çoğunu bu file'da (dosya) siz yazacaksınız. 5. görevin bir parçası da
# testlerim.py: orada kendi testlerinizi yazacaksınız.
#
# Projede 5 görev var, her biri 4 puan: toplam 20 puan. Projeyi tek
# başınıza, iki ya da üç kişilik bir grupla yapabilirsiniz.
#
# Son gün: 30 Kasım 2026 Pazartesi, 23.59
# Proje ödevi teslim formu: https://forms.gle/GoDQP1oTpEdeC2RD6
# Proje reposu:
# https://github.com/natozenbilek/mini-bank-python-project
#
# Bu file bankanın motoru: hesap yapan function'ları (fonksiyon) burada
# siz yazacaksınız. app.py bu file'ı import edip function'larınızı
# çağırıyor ve sonuçları tarayıcıda, bankanızın ekranında gösteriyor.
# File'ın sonundaki "Hazır function'lar" bölümünü biz yazdık. Görevlerin
# en uzun dört function'ı da orada hazır duruyor: load_transactions,
# transfer, due_orders ve atm_withdraw. Oradaki function'ları uygulama da
# kullanıyor; onları değiştirmeyin ama okuyun, bazıları sizin yazdığınız
# function'ları çağırıyor.
#
# Proje Ders 4'le (10 Kasım) açılıyor ama görevler Ders 5'in (17 Kasım)
# list (liste), tuple (demet), dict (sözlük) ve set (küme) konularını da
# kullanıyor: bunları gerektiren her function'ın docstring'inde, yani def
# satırının altındaki açıklamada, bir "Ders 5 notu" var; kısa
# açıklamaları da README'nin "Ders 5'ten önce" bölümünde.
#
# Başlamadan önce proje klasörünün tamamını, data ve ui klasörleriyle
# birlikte, PyCharm'da açın. Klasördeki file'lar yerlerini değiştirmeden
# aynı klasörde durmalı.
#
# Her görevde
# 1. Function'ların docstring'ini okuyun. Docstring, def satırının hemen
#    altında üç tırnak arasında duran açıklama; görev orada yazıyor.
#    Docstring'deki örneklerde ">>>" ile başlayan satırı Python
#    çalıştırır; çoğu zaman bu bir call (çağrı). "..." ile başlayan
#    satırlar onun devamıdır: uzun bir satır böyle bölünür. Başında
#    ">>>" ya da "..." olmayan ilk satır, call'un return ettiği değerdir;
#    örnekte print varsa ekrana yazılandır. rows = [...] gibi bir isme
#    değer atayan satırın altında bir şey yazmaz.
# 2. "# TODO" satırını ve pass'i silip yerlerine kodunuzu yazın.
# 3. kontrol.py'yi PyCharm'da açıp Run deyin. Her görevin yanına ✓ ya
#    da ✗ yazar; ✗ ise neyin eksik olduğunu da söyler.
# 4. app.py'yi açıp Run deyin: bankanız tarayıcıda açılır ve yazdığınız
#    görevin bölümü artık çalışır. bank.py'yi değiştirip kaydettikten
#    sonra tarayıcıda sayfayı yenilemeniz yeter.
# 5. Bitince proje klasörünü zip'leyip formdaki "Ödev dosyası" alanına
#    yükleyin. Grupla yaptıysanız herkes kendi hesabından aynı zip'i
#    yükler; formdaki "Katkınız" alanına da herkes kendi payını yazar.
#
# bank.py'yi Run ile çalıştırmak bir şey yazdırmaz: file'da yalnızca
# function'lar var. Denemelerinizi bank.py'de function'ların dışına
# değil, testlerim.py'ye yazın. Bu file'a henüz bir şey yazmasanız da
# app.py ve kontrol.py onu hatasız import eder; o zaman sizin
# function'larınız None return eder ve uygulamada o bölümün yerinde
# "Bu bölüm 1. görevi yazınca açılacak" gibi bir kutu durur.
#
# Yalnızca Ders 1, 2, 3, 4 ve 5'te gördüğümüz yapıları kullanın.
# security.py ve dates.py hazır; içlerinde derste görmediğimiz
# module'ler (modül) var, ama siz yalnız function'larını çağıracaksınız.

# random'u (Ders 4) hazır atm_withdraw kullanıyor; bu satırı silmeyin.
import random

# Görevlerde buraya import satırları ekleyeceksiniz: 2. görevde
# "import security", 4. görevde "import dates".


# Bankanın kuralları. Bu sayılar kurgusal; gerçek bir bankanın kuralı
# değil. Hesap kesim, asgari ödeme gibi sözcüklerin anlamı README'deki
# "Bankacılık sözcükleri" tablosunda.
# BANK_CODE: bankamızın IBAN'lardaki 5 haneli kodu
# BRANCH_FEE: başka bir şubeye havale masrafı, TL
# EFT_FEE: başka bir bankaya gönderirken kesilen masraf, TL
# DAILY_LIMIT: bir hesaptan bir günde gönderilebilecek en çok TL
# ATM_LIMIT: bir hesaptan bir günde ATM'den çekilebilecek en çok TL
# ROUNDS: şifrenin hash'i çıkarılırken sha256 kaç kez üst üste uygulanır
# MIN_PERCENT: asgari ödeme, ekstre borcunun yüzde kaçı
# DUE_DAYS: son ödeme günü, hesap kesimden kaç gün sonra
# TAX_PERCENT: vadeli mevduatın faizinden kesilen vergi, yüzde
# RECENT_SIZE: "son gönderdikleriniz"de en çok kaç alıcı durur
# NOTES: ATM'deki banknotlar, büyükten küçüğe
BANK_CODE = "12345"
BRANCH_FEE = 2
EFT_FEE = 5
DAILY_LIMIT = 50000
ATM_LIMIT = 10000
ROUNDS = 1000
MIN_PERCENT = 20
DUE_DAYS = 10
TAX_PERCENT = 15
RECENT_SIZE = 5
NOTES = [200, 100, 50, 20, 10]

# Rakam ve harf kontrollerinde kullanılan karakterler
DIGITS = "0123456789"
LETTERS = "abcçdefgğhıijklmnoöprsştuüvyzqwx"


# 1. Kayıtlar ve şubeler

# Bankanın bütün para hareketlerini data/transactions.csv'den hazır
# load_transactions okuyor (file'ın sonunda, "Hazır function'lar"
# bölümünde). Bu görevin function'ları onun verdiği transactions
# list'iyle çalışıyor.

# Bankanızın adı ve rengi uygulamanın başlığında görünür. Rengi
# "#0e7490" gibi, # ve altı haneyle yazın; renk kodlarını internette
# "renk seçici" diye aratarak bulabilirsiniz.
# TODO: Örnek Bank'ı ve rengini kendi bankanızınkiyle değiştirin.
BANK_NAME = "Örnek Bank"
BANK_COLOR = "#2f5d8a"


def balances(transactions):
    """Her hesabın bakiyesini bulur; dict return eder.

    Ders 5 notu: dict, get() ve for'da unpacking Ders 5'te (17 Kasım); kısa
    açıklamaları README'nin "Ders 5'ten önce" bölümünde.

    Dict'in key'i (anahtar) hesap (IBAN ya da NAKIT gibi bir sözcük),
    value'su (değer) o hesabın bakiyesi. Her hareket, gönderenin
    bakiyesinden amount kadar düşer, alıcının bakiyesine amount kadar
    ekler. Bir hesap dict'te henüz yoksa bakiyesi 0'dan başlar: get()'i
    hatırlayın.

    Adım adım:
    1. Boş bir dict kurun, örneğin money = {}.
    2. Her (date, sender, receiver, amount, description) için:
           money[sender] = money.get(sender, 0) - amount
           money[receiver] = money.get(receiver, 0) + amount
    3. Dict'i return edin.

    >>> balances([("2026-09-01", "NAKIT", "A", 100, "Burs"),
    ...           ("2026-09-02", "A", "B", 30, "Yemek")])
    {'NAKIT': -100, 'A': 70, 'B': 30}
    """
    # TODO
    pass


def account_history(transactions, iban):
    """iban'ın hareketlerini, en yenisi başta, (date, other, amount,
    description) tuple'larının list'i olarak return eder.

    Ders 5 notu: list, insert(), tuple ve for'da unpacking
    Ders 5'te (17 Kasım); kısa açıklamaları README'nin "Ders 5'ten önce"
    bölümünde.

    other karşı taraftır: hesap gönderense receiver, alıcıysa sender.
    Hesaba giren para artı, çıkan para eksi işaretli olur: hesap
    gönderense amount yerine 0 - amount yazın. iban'ın olmadığı
    hareketler girmez. En yeni hareket en başta olsun: append() yerine
    insert(0, ...) ile list'in başına ekleyin.

    >>> rows = [("2026-09-01", "NAKIT", "A", 100, "Burs"),
    ...         ("2026-09-02", "A", "B", 30, "Yemek"),
    ...         ("2026-09-03", "C", "D", 5, "Çay")]
    >>> account_history(rows, "A")
    [('2026-09-02', 'B', -30, 'Yemek'), ('2026-09-01', 'NAKIT', 100, 'Burs')]
    """
    # TODO
    pass


def owner_of(accounts, iban):
    """iban'ın sahibinin müşteri numarasını return eder; iban bankamızda
    yoksa None return eder.

    Ders 5 notu: list ve for'da unpacking Ders 5'te (17 Kasım); kısa
    açıklamaları README'nin "Ders 5'ten önce" bölümünde.

    accounts, (iban, customer_no, currency) tuple'larının list'i
    (records.load_accounts verir). None "hiçbir şey" demek (Ders 4): bir
    function bulamadığını None ile söyler, çağıran da sonucu
    "is None" ile sorar.

    iban bu function'ın parameter'ı (parametre); for satırında aynı adı
    kullanırsanız aradığınız IBAN kaybolur. Tuple'daki IBAN'a account
    gibi başka bir ad verin:
        for account, customer_no, currency in accounts:

    >>> accounts = [("TR571234500101100100000001", 1001, "TL")]
    >>> owner_of(accounts, "TR571234500101100100000001")
    1001
    >>> owner_of(accounts, "TR136789005500123400001234") is None
    True
    """
    # TODO
    pass


def branch_report(accounts, money):
    """Şube raporu: her şubenin müşteri sayısını ve TL hesaplarındaki
    toplam parayı bulur; (branch, customers, total) tuple'larının
    list'ini, toplamı en büyük şube başta olacak biçimde return eder.

    Ders 5 notu: dict, get(), set, add(), list, append(), sort(), tuple ve
    for'da unpacking Ders 5'te (17 Kasım); kısa açıklamaları README'nin
    "Ders 5'ten önce" bölümünde. Set'leri bir dict'in value'su olarak tutup
    d[key].add(...) ile büyütmek ise README'nin "Dict içinde set" bölümünde.

    Şube kodu, IBAN'daki hesap numarasının ilk dört hanesidir:
    iban[10:14]. money, balances'ın dict'i. Hiç hareketi olmayan bir hesap
    money'de yoktur; bakiyesini money.get(iban, 0) ile alın.

    Bir müşterinin aynı şubede birden çok hesabı (TL ve USD gibi)
    olabilir. Müşterileri bir kez saymak için her şubenin müşterilerini
    bir set'te toplayın ve set'leri key'i şube kodu olan bir dict'te
    tutun: şube dict'te yoksa {customer_no} ile yeni bir set koyun, varsa
    add() ile ekleyin. Müşteri sayısına bütün hesaplar, toplama yalnız TL
    hesaplarının bakiyesi girer.

    Sonra her şube için (0 - total, branch, müşteri sayısı) tuple'larını
    bir list'e koyup sort() ile sıralayın ve (branch, customers, total)
    biçimine çevirin; 0 - total en büyük toplamı başa getirir.

    >>> accounts = [("TR571234500101100100000001", 1001, "TL"),
    ...             ("TR301234500101100100000002", 1001, "USD"),
    ...             ("TR121234500102100200000001", 1002, "TL"),
    ...             ("TR481234500101100300000001", 1003, "TL")]
    >>> money = {"TR571234500101100100000001": 300,
    ...          "TR301234500101100100000002": 50,
    ...          "TR121234500102100200000001": 900,
    ...          "TR481234500101100300000001": 100}
    >>> branch_report(accounts, money)
    [('0102', 1, 900), ('0101', 2, 400)]
    """
    # TODO
    pass


# 2. Güvenli giriş

def password_ok(password, name):
    """Yeni bir şifrenin bankanın kurallarına uyup uymadığına bakar;
    (ok, message) tuple'ını return eder.

    Ders 5 notu: tuple Ders 5'te (17 Kasım); kısa açıklaması README'nin
    "Ders 5'ten önce" bölümünde.

    Kurallar, sırayla; ilk uymayan kuralın mesajı döner:
    1. En az 8 karakter: (False, "Şifre en az 8 karakter olmalı.")
    2. En az bir rakam: (False, "Şifrede en az bir rakam olmalı.")
    3. En az bir harf: (False, "Şifrede en az bir harf olmalı.")
    4. Virgül yok, çünkü file'da alanları virgül ayırıyor:
       (False, "Şifrede virgül olmamalı.")
    5. Müşterinin adı şifrenin içinde geçmiyor (ikisini de lower() ile
       küçük harfe çevirip in ile bakın):
       (False, "Şifre adınızı içermemeli.")
    Hepsine uyuyorsa (True, "Şifre uygun.").

    Bir karakter DIGITS'in içindeyse rakamdır; lower() edilmiş hali
    LETTERS'ın içindeyse harftir. Şifrenin karakterlerini bir for
    loop'uyla (döngü) gezin. Loop'tan önce iki variable'a (değişken)
    False verin: has_digit = False ve has_letter = False. Loop'ta rakam
    görünce has_digit'i, harf görünce has_letter'ı True yapın.

    >>> password_ok("kedi123", "Zehra")
    (False, 'Şifre en az 8 karakter olmalı.')
    >>> password_ok("zehra2026", "Zehra")
    (False, 'Şifre adınızı içermemeli.')
    >>> password_ok("martı2026", "Zehra")
    (True, 'Şifre uygun.')
    """
    # TODO
    pass


def hash_password(password, salt):
    """Şifrenin hash'ini return eder.

    Banka şifrenin kendisini hiçbir yere yazmaz; yalnız hash'ini saklar.
    Hash'i security.sha256() çıkarıyor: aynı text her zaman aynı hash'i
    verir, hash'ten text'i geri bulmanın bilinen bir yolu yok. Giriş
    yapılırken girilen şifrenin hash'i yeniden çıkarılıp saklanan hash'le
    karşılaştırılır.

    salt, her müşteriye özel rastgele bir str (karakter dizisi). Şifreye
    eklendiği için aynı şifreyi kullanan iki müşterinin hash'i farklı
    çıkar. sha256'yı ROUNDS kez üst üste uygulamak da şifreyi deneye
    deneye bulmaya çalışan birini ROUNDS kat yavaşlatır.

    Formül:
        text = password
        ROUNDS kez tekrarlayın:  text = security.sha256(salt + text)
        text'i return edin.

    Bu function için bank.py'nin başına "import security" yazın.

    >>> hash_password("kedi123", "9f2c41d07ab3e5c8")[:16]
    '8025d5c5cf79144e'
    """
    # TODO
    pass


def register(customers, name, password, file_name):
    """Yeni bir müşteri kaydeder; yeni müşterinin numarasını return eder.

    Ders 5 notu: dict ve tuple Ders 5'te (17 Kasım); kısa açıklamaları
    README'nin "Ders 5'ten önce" bölümünde.

    customers, {müşteri no: (ad, salt, hash)} dict'i; müşteri numarası int
    (tam sayı). file_name, müşterilerin tutulduğu file
    (data/customers.csv).

    Adım adım:
    1. Yeni numara, en büyük müşteri numarasının bir fazlası. Bir
       variable'a 1000 verip customers'ın her key'ine bakın;
       key ondan büyükse variable o key olsun. Sonunda bir ekleyin. Hiç
       müşteri yoksa yeni numara 1001 olur.
    2. salt = security.make_salt()
    3. password'ün hash'ini hash_password ile bu salt'la çıkarın.
    4. customers'a yeni numarayla (name, salt, hash) tuple'ını ekleyin.
    5. file_name'i "a" moduyla açıp sonuna bir satır ekleyin:
           1015,Büşra,9f2c41d07ab3e5c8,8025d5c5...
       (hash burada kısaltıldı; file'a 64 karakterin hepsi yazılır)
       Alanlar virgülle ayrılır, satır \n ile biter. Şifrenin kendisi
       hiçbir yere yazılmaz. File'ı encoding="utf-8" ile açın:
       open(file_name, "a", encoding="utf-8") gibi. Yazmazsanız Türkçe
       harfler Windows'ta bozulur.
    6. Yeni numarayı return edin.
    """
    # TODO
    pass


def login(customers, failed, customer_no, password):
    """Girişi dener; "ok", "wrong", "locked" ya da "unknown" return eder.

    Ders 5 notu: dict, get() ve unpacking Ders 5'te (17 Kasım); kısa
    açıklamaları README'nin "Ders 5'ten önce" bölümünde.

    customers, {müşteri no: (ad, salt, hash)} dict'i. failed, {müşteri no:
    üst üste yanlış deneme sayısı} dict'i; uygulama onu açık kaldığı
    sürece tutar.

    Kurallar:
    - customer_no customers'ta yoksa "unknown".
    - O müşterinin üst üste 3 yanlış denemesi olduysa, şifre doğru olsa
      bile "locked": hesap kilitli.
    - Girilen şifrenin hash'i, müşterinin kendi salt'ıyla çıkarılınca
      saklanan hash'e eşitse giriş doğru: failed'daki sayıyı 0 yapın ve
      "ok" return edin.
    - Değilse failed'daki sayıyı bir artırın (yoksa 0'dan başlar: get()).
      Sayı 3 olduysa "locked", olmadıysa "wrong" return edin.

    >>> salt = "9f2c41d07ab3e5c8"
    >>> customers = {1001: ("Zehra", salt, hash_password("kedi123", salt))}
    >>> failed = {}
    >>> login(customers, failed, 1001, "kedi123")
    'ok'
    >>> login(customers, failed, 1001, "kedi")
    'wrong'
    >>> login(customers, failed, 1002, "kedi123")
    'unknown'
    """
    # TODO
    pass


def change_password(customers, customer_no, old_password, new_password,
                    file_name):
    """Müşterinin şifresini değiştirir; True ya da False return eder.

    Ders 5 notu: dict, tuple ve unpacking Ders 5'te (17 Kasım); kısa
    açıklamaları README'nin "Ders 5'ten önce" bölümünde.

    Adım adım:
    1. Eski şifreyi login'deki gibi deneyin: hash'i müşterinin salt'ıyla
       çıkarılınca saklanan hash'e eşit değilse False return edin.
    2. Yeni bir salt alın (security.make_salt()) ve yeni şifrenin
       hash'ini bu salt'la çıkarın. customers'ta müşterinin tuple'ını
       (ad, yeni salt, yeni hash) yapın.
    3. file_name'i "w" moduyla açıp bütün müşterileri yeniden yazın:
       önce başlık satırı customer_no,name,salt,password_hash, sonra her
       müşteri için bir satır. Başlık da dahil her satır \n ile biter.
       "w" file'ı baştan yazar, eski satırların hepsi silinir; bu yüzden
       yalnız değişeni değil, herkesi yazmalısınız. File'ı
       encoding="utf-8" ile açın: open(file_name, "w", encoding="utf-8")
       gibi. Yazmazsanız Türkçe harfler Windows'ta bozulur.
    4. True return edin.
    """
    # TODO
    pass


# 3. Para gönderme ve talimatlar

# Para gönderen transfer ile bugün ödenecek talimatları bulan due_orders
# hazır; file'ın sonundaki "Hazır function'lar" bölümünde. transfer,
# alıcının IBAN'ına bu görevde yazacağınız iban_valid ile bakıyor ve
# yeni hareketleri save_transaction ile yazıyor; bakiyeyi balances'la
# bulup alıcının hesabını owner_of'la arıyor (1. görev).

def iban_valid(iban):
    """IBAN'ın kontrol hanelerine bakar; True ya da False return eder.

    Türkiye'deki bir IBAN 26 karakterdir: "TR", 2 kontrol hanesi, 5 haneli
    banka kodu, 1 yedek hane (0) ve 16 karakterlik hesap numarası. Bu
    bankada hesap numarasının ilk dört hanesi şube kodu. Kontrol haneleri
    bütün ülkelerde aynı formülle (mod 97) hesaplanır; bir karakteri
    yanlış yazılmış IBAN bu formülden geçmez.

    Formül:
    1. Uzunluk 26 değilse ya da ilk iki karakter "TR" değilse False.
    2. İlk dört karakteri sona taşıyın: iban[4:] + iban[:4]
    3. Bu str'nin karakterlerini bir for loop'uyla gezip yeni bir str
       kurun: rakam (DIGITS'in içinde olan) olduğu gibi eklenir, harf
       sayıya çevrilip eklenir: A 10, B 11, ..., Z 35. Harfin sayısı
       ord(char) - ord("A") + 10; ord() bir karakterin kodunu verir
       (Ders 2). Örneğin "TR", "2927" olur; gerçek IBAN'ların hesap
       numarasında da harf olabilir.
    4. Yeni str'yi int()'e çevirin. int() çeviremezse ValueError verir
       (örneğin IBAN'da "-" ya da boşluk varsa); o zaman False.
    5. Sayının 97'ye bölümünden kalan 1'se True, değilse False.

    >>> iban_valid("TR571234500101100100000001")
    True
    >>> iban_valid("TR571234500101100100000002")
    False
    """
    # TODO
    pass


def mask_iban(iban):
    """IBAN'ın yalnız ilk ve son dört karakterini gösterip arasına yıldız
    koyar; başka birinin IBAN'ı ekranda böyle görünür.

    İlk dört karakter iban[:4]; son dört karakter eksi index'le (indis)
    dilimlenir: iban[-4:]. Aradaki 18 karakterin yerine "*" * 18 gelir
    (str'yi tekrarlamak, Ders 2).

    >>> mask_iban("TR121234500102100200000001")
    'TR12******************0001'
    """
    # TODO
    pass


def resolve_receiver(aliases, text):
    """Alıcı kutusuna yazılanı IBAN'a çevirir; IBAN'ı str olarak return
    eder.

    Ders 5 notu: dict Ders 5'te (17 Kasım); kısa açıklaması README'nin
    "Ders 5'ten önce" bölümünde.

    Kolay Adres'te para, IBAN yerine bir e-posta adresine de gönderilir.
    aliases, {e-posta: IBAN} dict'i. Adım adım:
    1. text'in başındaki ve sonundaki boşlukları strip() ile silin.
    2. text'in lower() edilmiş hali aliases'ta bir key ise o key'in
       value'sunu return edin.
    3. Değilse text bir IBAN'dır: içindeki boşlukları replace(" ", "")
       ile silip upper() ile büyük harfe çevirerek return edin.

    >>> aliases = {"zehra@ornek.test": "TR571234500101100100000001"}
    >>> resolve_receiver(aliases, " Zehra@ornek.test ")
    'TR571234500101100100000001'
    >>> resolve_receiver(aliases, "tr12 1234 5001 0210 0200 0000 01")
    'TR121234500102100200000001'
    """
    # TODO
    pass


def save_transaction(file_name, transaction):
    """Bir para hareketini file'ın sonuna ekler; bir şey return etmez.

    Ders 5 notu: tuple ve unpacking Ders 5'te (17 Kasım); kısa açıklamaları
    README'nin "Ders 5'ten önce" bölümünde.

    transaction (date, sender, receiver, amount, description) tuple'ı.
    File'ı "a" moduyla açın ve sonuna transactions.csv'deki biçimde bir
    satır yazın: alanlar virgülle ayrılır, satır \n ile biter.
        2026-11-08,TR...,TR...,250,Kira payı
    File'ı encoding="utf-8" ile açın: open(file_name, "a", encoding="utf-8")
    gibi. Yazmazsanız Türkçe harfler Windows'ta bozulur.
    """
    # TODO
    pass


# 4. Kredi kartı ve döküm

class Card:
    """Bir kredi kartı: limiti ve borcu var.

    Attribute'ları (özellik): card_id (kartın son dört hanesi, str), limit
    (TL) ve debt (borç, TL; yeni kartta 0). available() kullanılabilir
    limiti verir: limit - debt. spend() ve pay() işlemi yapabilirse True,
    yapamazsa hiçbir şeyi değiştirmeden False return eder.

    >>> card = Card("4821", 1000)
    >>> card.spend(700)
    True
    >>> card.spend(400)
    False
    >>> card.available()
    300
    >>> card.pay(200)
    True
    >>> card.debt
    500
    """

    def __init__(self, card_id, limit):
        """Yeni bir kart: card_id ve limit verilenler, debt 0."""
        # TODO
        pass

    def available(self):
        """Kullanılabilir limiti return eder: limit - debt."""
        # TODO
        pass

    def spend(self, amount):
        """amount TL'lik bir harcama. amount kullanılabilir limitten
        büyükse False return eder; değilse amount'u borca ekler ve True
        return eder.
        """
        # TODO
        pass

    def pay(self, amount):
        """Karta amount TL ödeme. amount borçtan büyükse False return
        eder; değilse amount'u borçtan düşer ve True return eder.
        """
        # TODO
        pass


def replay_card(card_id, limit, activity):
    """Kartın bütün hareketlerini sırayla uygular; kartı return eder.

    Ders 5 notu: list ve for'da unpacking Ders 5'te (17 Kasım); kısa
    açıklamaları README'nin "Ders 5'ten önce" bölümünde.

    activity, (date, card_id, kind, merchant, category, amount)
    tuple'larının list'i. merchant harcamanın yapıldığı yer (ödemede
    "-"), category harcamanın kategorisi; kind "spend" (harcama) ya da
    "payment" (karta ödeme). Başka kartların hareketleri de bu list'te.

    Adım adım:
    1. card_id ve limit'le bir Card kurun.
    2. Her hareket için: card_id'si bu kartınki değilse sonrakine geçin.
       kind "spend" ise kartın spend()'ini, "payment" ise pay()'ini
       amount'la çağırın.
    3. Kartı return edin. Uygulama borcu card.debt'ten okuyor.

    for satırında card_id adını yeniden kullanmayın, yoksa parameter'ın
    değeri kaybolur ve başka kartların hareketleri de bu karta işlenir.
    Tuple'daki card_id'ye owner gibi başka bir ad verin:
        for date, owner, kind, merchant, category, amount in activity:

    >>> activity = [("2026-10-01", "4821", "spend", "Kampüs Kafe",
    ...              "yemek", 300),
    ...             ("2026-10-02", "7310", "spend", "Kitapçı", "kitap", 90),
    ...             ("2026-10-20", "4821", "payment", "-", "-", 100)]
    >>> replay_card("4821", 1000, activity).debt
    200
    """
    # TODO
    pass


def statement(activity, card_id, start, end):
    """Kartın ekstresi; (lines, total) tuple'ını return eder.

    Ders 5 notu: list, append(), sum(), tuple ve for'da unpacking
    Ders 5'te (17 Kasım); kısa açıklamaları README'nin "Ders 5'ten önce"
    bölümünde.

    lines, card_id'nin start ile end arasındaki (ikisi de dahil)
    harcamalarının (date, merchant, amount) tuple'ları, activity'deki
    sırayla. total bu harcamaların toplamı: tutarları ayrı bir list'e de
    ekleyip sonunda sum() ile toplayın. Ödemeler (kind "payment")
    ekstreye girmez. Tarihler str; "2026-10-01" >= start gibi
    karşılaştırabilirsiniz.

    for satırında card_id adını yeniden kullanmayın, yoksa parameter'ın
    değeri kaybolur: tuple'daki card_id'ye owner gibi başka bir ad verin.

    >>> activity = [("2026-09-30", "4821", "spend", "Market", "market", 80),
    ...             ("2026-10-01", "4821", "spend", "Kafe", "yemek", 300),
    ...             ("2026-10-02", "7310", "spend", "Kitapçı", "kitap", 90),
    ...             ("2026-10-15", "4821", "spend", "Sinema", "eğlence",
    ...              150)]
    >>> statement(activity, "4821", "2026-10-01", "2026-10-31")
    ([('2026-10-01', 'Kafe', 300), ('2026-10-15', 'Sinema', 150)], 450)
    """
    # TODO
    pass


def payment_info(total, end):
    """Ekstrenin asgari ödemesini ve son ödeme gününü bulur; (minimum,
    due) tuple'ını return eder.

    Ders 5 notu: tuple Ders 5'te (17 Kasım); kısa açıklaması README'nin
    "Ders 5'ten önce" bölümünde.

    total ekstrenin toplamı, end ekstrenin son günü, yani hesap kesim
    günü. Formül (bu bankanın kuralı):
        minimum = total * MIN_PERCENT // 100
        due = end'den DUE_DAYS gün sonrası
    Gün eklemek için dates module'ündeki dates.add_days(date, days)'i
    kullanın; bank.py'nin başına "import dates" yazın.

    >>> payment_info(450, "2026-10-15")
    (90, '2026-10-25')
    """
    # TODO
    pass


def installments(amount, count):
    """amount TL'lik bir alışverişi count eşit taksite böler; taksitlerin
    list'ini return eder.

    Ders 5 notu: list ve append() Ders 5'te (17 Kasım); kısa açıklamaları
    README'nin "Ders 5'ten önce" bölümünde.

    Taksitler tam sayı; bölünmeyen kalan ilk taksitlere birer TL olarak
    dağıtılır:
        base = amount // count
        rest = amount % count
    İlk rest taksit base + 1, öbürleri base.

    >>> installments(1000, 3)
    [334, 333, 333]
    >>> installments(1200, 4)
    [300, 300, 300, 300]
    """
    # TODO
    pass


def category_totals(activity, card_id, month):
    """Kartın bir aydaki harcamalarını kategoriye göre toplar; dict
    return eder.

    Ders 5 notu: dict, get() ve for'da unpacking Ders 5'te (17 Kasım); kısa
    açıklamaları README'nin "Ders 5'ten önce" bölümünde.

    month "2026-10" gibi; card_id'nin, tarihinin ilk yedi karakteri
    (date[:7]) month olan "spend" hareketleri girer. Dict'in key'i
    kategori, value'su o kategorideki harcamaların toplamı.

    for satırında card_id adını yeniden kullanmayın, yoksa parameter'ın
    değeri kaybolur: tuple'daki card_id'ye owner gibi başka bir ad verin.

    >>> activity = [("2026-10-01", "4821", "spend", "Kafe", "yemek", 300),
    ...             ("2026-10-02", "7310", "spend", "Kitapçı", "kitap", 90),
    ...             ("2026-10-03", "4821", "spend", "Lokanta", "yemek",
    ...              120),
    ...             ("2026-10-15", "4821", "spend", "Sinema", "eğlence",
    ...              150),
    ...             ("2026-11-01", "4821", "spend", "Kafe", "yemek", 60)]
    >>> category_totals(activity, "4821", "2026-10")
    {'yemek': 420, 'eğlence': 150}
    """
    # TODO
    pass


def places(activity, card_id, month):
    """card_id'nin month ayında harcama yaptığı yerlerin set'ini return
    eder.

    Ders 5 notu: set(), add() ve for'da unpacking Ders 5'te (17 Kasım); kısa
    açıklamaları README'nin "Ders 5'ten önce" bölümünde.

    month "2026-10" gibi; tarihinin ilk yedi karakteri (date[:7]) month
    olan "spend" hareketlerinin merchant'ları set'e girer. Aynı yer set'te
    bir kez durur.

    for satırında card_id adını yeniden kullanmayın, yoksa parameter'ın
    değeri kaybolur: tuple'daki card_id'ye owner gibi başka bir ad verin.

    >>> activity = [("2026-10-01", "4821", "spend", "Kafe", "yemek", 80),
    ...             ("2026-10-09", "4821", "spend", "Kafe", "yemek", 60),
    ...             ("2026-10-12", "4821", "spend", "Sinema", "eğlence",
    ...              150)]
    >>> places(activity, "4821", "2026-10") == {"Kafe", "Sinema"}
    True
    """
    # TODO
    pass


def new_places(activity, card_id, month, previous):
    """month ayında ilk kez harcama yapılan yerlerin set'ini return eder.

    Ders 5 notu: list, set(), set'lerin birleşimi (|) ve farkı (-)
    Ders 5'te (17 Kasım); kısa açıklamaları README'nin "Ders 5'ten önce"
    bölümünde.

    previous, month'tan önceki ayların list'i. Önceki ayların yerlerini
    tek bir set'te birleştirin (|): önce before = set() yazın ({} boş bir
    dict olur), sonra previous'taki her ay için
        before = before | places(activity, card_id, ay)
    En sonda bu ayın yerlerinden before'u çıkarın (fark, -).

    >>> activity = [("2026-09-03", "4821", "spend", "Kafe", "yemek", 80),
    ...             ("2026-10-01", "4821", "spend", "Kafe", "yemek", 60),
    ...             ("2026-10-12", "4821", "spend", "Sinema", "eğlence",
    ...              150)]
    >>> new_places(activity, "4821", "2026-10", ["2026-09"])
    {'Sinema'}
    """
    # TODO
    pass


# 5. Döviz, kredi, ATM ve raporunuz

# QR ile ATM'den para çeken atm_withdraw hazır; file'ın sonundaki "Hazır
# function'lar" bölümünde. Bakiyeyi balances'la (1. görev) buluyor,
# çekimi save_transaction'la (3. görev) yazıyor.

def buy_foreign(tl_amount, sell_rate):
    """tl_amount TL ile kaç birim döviz alınır? (units, cost) tuple'ını
    return eder.

    Ders 5 notu: tuple Ders 5'te (17 Kasım); kısa açıklaması README'nin
    "Ders 5'ten önce" bölümünde.

    Banka dövizi satış kurundan (sell_rate) satar: 1 dolar 41.20 TL gibi.
    Yalnız tam birim alınır.
        units = int(tl_amount // sell_rate)
        cost = round(units * sell_rate)     (ödenen TL, tam sayı)

    >>> buy_foreign(1000, 41.2)
    (24, 989)
    """
    # TODO
    pass


def sell_foreign(units, buy_rate):
    """units birim dövizi bozdurunca ele kaç TL geçer? Banka dövizi alış
    kurundan (buy_rate) alır; sonucu round() ile tam sayıya yuvarlayıp
    return edin.

    >>> sell_foreign(24, 40.0)
    960
    """
    # TODO
    pass


def rate_text(currency, buy, sell):
    """Bir dövizin kur satırını str olarak return eder; kurlar noktadan
    sonra iki basamakla yazılır.

    f-string'de {buy:.2f}, buy'ı noktadan sonra iki basamakla yazar
    (Ders 2): 41.2, "41.20" olur.

    >>> rate_text("USD", 41.2, 42.034)
    'USD: alış 41.20 TL, satış 42.03 TL'
    """
    # TODO
    pass


def loan_installment(principal, monthly_rate, months):
    """Eşit taksitli bir kredinin aylık taksitini return eder (TL, tam
    sayı).

    principal çekilen para, monthly_rate aylık faiz yüzde olarak (2,
    ayda yüzde 2 demek; 0'dan büyük), months taksit sayısı. Formül:
        r = monthly_rate / 100
        taksit = principal * r * (1 + r) ** months / ((1 + r) ** months - 1)
    Sonucu round() ile tam sayıya yuvarlayın.

    >>> loan_installment(12000, 2, 12)
    1135
    """
    # TODO
    pass


def months_to_goal(goal, monthly, monthly_rate):
    """Her ay monthly TL biriktiren biri, birikimi aylık yüzde
    monthly_rate faizle büyürken goal TL'ye kaç ayda ulaşır? Ay sayısını
    return eder.

    Kaç kez döneceğini baştan bilmediğimiz için while loop'u (Ders 3):
        saved = 0
        months = 0
        saved goal'den küçük olduğu sürece:
            saved = saved + saved * monthly_rate / 100 + monthly
            months += 1
    monthly 0'dan büyük olmalı; değilse loop hiç bitmez.

    >>> months_to_goal(1000, 300, 0)
    4
    >>> months_to_goal(10000, 1000, 2)
    10
    """
    # TODO
    pass


def my_report(transactions, activity):
    """Sizin raporunuz: (title, rows) tuple'ını return eder. Uygulamanın
    "Raporum" sekmesinde bir tablo olarak görünür.

    Ders 5 notu: list, tuple, dict, items() ve sort() Ders 5'te (17 Kasım);
    kısa açıklamaları README'nin "Ders 5'ten önce" bölümünde.

    transactions ve activity, giriş yapan müşterinin kendi hesap
    hareketleri ve kart hareketleri (öbür müşterilerinki yok). title
    raporun başlığı, bir str; rows tablonun satırları, tuple'ların list'i.
    Her tuple bir satır: ("2026-10", 1840) gibi.

    Ne göstereceği sizin fikriniz. Örnekler: en büyük beş harcamanız,
    kategorilere göre toplam harcamanız, her kategorideki en büyük
    harcamanız, en çok harcama yaptığınız gün. Bu dört fikirden birini
    seçebilirsiniz; yalnız aşağıdaki "aylara göre kart harcamaları"
    örneğini kullanmayın, o sizin raporunuz sayılmaz. Hangi IBAN'ın sizin
    olduğu my_report'a gelmiyor; gelen parayla giden parayı ayırmanız
    gereken bir rapor seçmeyin. Kartı olmayan bir müşteride activity boş
    bir list gelir; raporunuz o zaman da çalışmalı.

    Örnek: aylara göre kart harcamaları
        ('Aylara göre kart harcamam', [('2026-09', 1840), ('2026-10', 2215)])
    """
    # TODO
    pass


# Hazır function'lar
#
# Bu bölümdeki function'ları biz yazdık; uygulama onları da kullanıyor,
# değiştirmeyin. İlk dördü görevlerin en uzun function'ları:
# load_transactions 1. görevden, transfer ve due_orders 3. görevden,
# atm_withdraw 5. görevden. transfer ve atm_withdraw sizin yazdığınız
# function'ları çağırıyor: bakiyeyi balances'la buluyor, yeni hareketi
# save_transaction'la yazıyorlar. Görevlerdeki fikirlerin başka yerlerde
# nasıl kullanıldığını görmek için hepsini okuyabilirsiniz.


# 1. görevin hazır function'ı: load_transactions

def load_transactions(file_name):
    """Hazır. file_name adlı file'ı okur; (transactions, skipped)
    tuple'ını return eder. Uygulama bankanın bütün hareketlerini
    data/transactions.csv'den bu function'la okuyor.

    Ders 5 notu: list, append(), split(), tuple ve unpacking
    Ders 5'te (17 Kasım); kısa açıklamaları README'nin "Ders 5'ten önce"
    bölümünde.

    File'ın ilk satırı başlıktır: date,sender,receiver,amount,description.
    Sonraki her satır bir para hareketi: tarih, gönderen, alıcı, tutar ve
    açıklama.
        2026-09-01,NAKIT,TR571234500101100100000001,3000,Burs
    Gönderen ve alıcı ya bir IBAN'dır ya da şu sözcüklerden biri: NAKIT
    (şubeden ya da ATM'den yatırılan ya da çekilen para), MASRAF
    (bankanın kestiği masraf), DOVIZ (döviz alım satımında bankanın döviz
    kasası), KART-4821 gibi (o karta yapılan ödeme), KREDI-K1 gibi (o
    kredinin taksiti ya da kullanımı).

    transactions, (date, sender, receiver, amount, description)
    tuple'larının list'idir. amount int'e çevrilir, öbürleri str olarak
    kalır. Satırlar file'daki sırayla eklenir. skipped, atlanan bozuk
    satır sayısıdır.

    Bozuk satırlar düzeltilmez, atlanıp sayılır. Bir satır iki durumda
    bozuktur: virgüllerden bölününce beş parça çıkmıyorsa ya da amount
    bir tam sayı değilse ("1.500" ya da boş gibi). Başlık satırı bozuk
    sayılmaz. Function ekrana bir şey yazmaz; sayıyı uygulama gösteriyor.
    open()'a file'ın adı elle yazılmaz, file_name verilir; arkasından
    encoding="utf-8" de verilir, verilmezse Türkçe harfler Windows'ta
    bozulur.

    File yoksa (banka yeni açıldıysa) open() FileNotFoundError verir; o
    zaman function ([], 0) return eder. Bunun için with satırı bir try'ın
    içinde duruyor ve except FileNotFoundError onu yakalıyor (Ders 4);
    satırları okuyan ikinci try onun içinde.

    Kodda:
    - Her satır önce line = line.strip() ile temizlenir: satırın
      sonundaki \n silinir. Satır başlığa eşitse continue ile sonraki
      satıra geçilir.
    - Satır parts = line.split(",") ile bölünür, parçalar unpacking ile
      beş isme atanır. Parça sayısı beş değilse unpacking ValueError
      verir; int() da tam sayı olmayan bir str'de ValueError verir.
      İkisini tek bir try ve except ValueError yakalar.

    Örnek: file'ın içi şu dört satırsa (başlık ve üç hareket)
        date,sender,receiver,amount,description
        2026-09-01,NAKIT,TR571234500101100100000001,3000,Burs
        2026-09-02,TR571234500101100100000001,MASRAF,5
        2026-09-03,NAKIT,TR571234500101100100000001,500,Harçlık
    load_transactions şu tuple'ı return eder (ikinci satırda dört parça
    var):
        ([('2026-09-01', 'NAKIT', 'TR571234500101100100000001', 3000,
           'Burs'),
          ('2026-09-03', 'NAKIT', 'TR571234500101100100000001', 500,
           'Harçlık')], 1)
    """
    transactions = []
    skipped = 0
    try:
        with open(file_name, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line == "date,sender,receiver,amount,description":
                    continue
                try:
                    parts = line.split(",")
                    date, sender, receiver, amount, description = parts
                    amount = int(amount)
                except ValueError:
                    skipped += 1
                    continue
                row = (date, sender, receiver, amount, description)
                transactions.append(row)
    except FileNotFoundError:
        return [], 0
    return transactions, skipped


# 3. görevin hazır function'ları: transfer ve due_orders

def transfer(transactions, accounts, file_name, today, sender, receiver,
             amount, description):
    """Hazır. sender hesabından receiver IBAN'ına para gönderir; (ok,
    message) tuple'ını return eder. Uygulama, Para gönder sekmesinde ve
    günü gelen talimatlarda parayı bu function'la gönderiyor. Sizin
    yazdığınız dört function'ı çağırıyor: iban_valid ve save_transaction
    (3. görev), owner_of ve balances (1. görev).

    Ders 5 notu: list, append(), dict, get(), tuple ve for'da unpacking
    Ders 5'te (17 Kasım); kısa açıklamaları README'nin "Ders 5'ten önce"
    bölümünde.

    transactions, bütün hareketlerin list'i; accounts, bankamızdaki
    hesapların list'i (owner_of'a verilir); file_name, transactions.csv.
    today bugünün tarihi, "2026-11-08" gibi. ok True ya da False;
    message kullanıcıya gösterilecek cümle.

    Kurallar, sırayla:
    1. amount 0'dan büyük değilse: (False, "Tutar sıfırdan büyük olmalı.")
    2. receiver geçerli bir IBAN değilse (iban_valid):
       (False, "Alıcının IBAN'ı geçersiz.")
    3. receiver sender'a eşitse: (False, "Aynı hesaba gönderemezsiniz.")
    4. Alıcı ve masraf. Alıcının banka kodu receiver[4:9], şube kodu
       receiver[10:14].
       - Banka kodu BANK_CODE ise para bizim bankada kalır (havale).
         Bankamızda böyle bir hesap yoksa (owner_of None return ederse):
         (False, "Bankamızda bu IBAN'la bir hesap yok.")
         Alıcının şubesi gönderenin şubesiyle (sender[10:14]) aynıysa
         masraf 0; değilse masraf BRANCH_FEE, masrafın adı
         "Şubeler arası havale".
       - Banka kodu başkaysa para başka bir bankaya gidiyor (EFT): masraf
         EFT_FEE, masrafın adı "EFT".
    5. sender'ın bakiyesi (balances ile) amount + masraftan küçükse:
       (False, "Bakiye yetmiyor.")
    6. sender'ın bugün gönderdiklerinin toplamı: transactions'ta tarihi
       today ve göndereni sender olan hareketlerin amount'ları. Bu toplam
       + amount, DAILY_LIMIT'ten büyükse:
       (False, "Günlük limit aşılıyor.")
       for satırında parameter'ların adları (sender, receiver, amount,
       description) yeniden kullanılmıyor, kullanılsa değerleri
       kaybolurdu; hareketler başka adlarla geziliyor:
       for date, who, to, value, text in transactions:
    7. Hepsi tamamsa (today, sender, receiver, amount, description)
       hareketi transactions'a eklenir ve save_transaction ile file'a
       yazılır. Masraf varsa (today, sender, "MASRAF", masraf, masrafın
       adı + " masrafı") hareketi de eklenip yazılır: "EFT masrafı" gibi.
    8. Masraf yoksa (True, "Gönderildi."), varsa
       (True, "Gönderildi. EFT masrafı 5 TL.") gibi return eder: adı ve
       tutarı masrafa göre.
    """
    if amount <= 0:
        return False, "Tutar sıfırdan büyük olmalı."
    if not iban_valid(receiver):
        return False, "Alıcının IBAN'ı geçersiz."
    if receiver == sender:
        return False, "Aynı hesaba gönderemezsiniz."
    fee = 0
    kind = ""
    if receiver[4:9] == BANK_CODE:
        if owner_of(accounts, receiver) is None:
            return False, "Bankamızda bu IBAN'la bir hesap yok."
        if receiver[10:14] != sender[10:14]:
            fee = BRANCH_FEE
            kind = "Şubeler arası havale"
    else:
        fee = EFT_FEE
        kind = "EFT"
    if balances(transactions).get(sender, 0) < amount + fee:
        return False, "Bakiye yetmiyor."
    sent = 0
    for date, who, to, value, text in transactions:
        if date == today and who == sender:
            sent += value
    if sent + amount > DAILY_LIMIT:
        return False, "Günlük limit aşılıyor."
    new = (today, sender, receiver, amount, description)
    transactions.append(new)
    save_transaction(file_name, new)
    if fee == 0:
        return True, "Gönderildi."
    cost = (today, sender, "MASRAF", fee, kind + " masrafı")
    transactions.append(cost)
    save_transaction(file_name, cost)
    return True, f"Gönderildi. {kind} masrafı {fee} TL."


def due_orders(orders, transactions, today):
    """Hazır. Bugün ödenmesi gereken otomatik ödeme talimatlarını list
    olarak return eder. Uygulama günü gelen talimatları bununla bulup
    transfer ile ödüyor.

    Ders 5 notu: list, append() ve unpacking Ders 5'te (17 Kasım); kısa
    açıklamaları README'nin "Ders 5'ten önce" bölümünde.

    orders, (sender, day, receiver, amount, description) tuple'larının
    list'i: sender her ayın day'inci günü receiver'a amount TL gönderir.
    Bir talimat şu durumda bugün ödenir:
    - today'in günü (int(today[8:])) day'e eşitse ve
    - transactions'ta bugün tarihli, göndereni sender, alıcısı receiver
      ve açıklaması description olan bir hareket yoksa (yani bugün daha
      önce ödenmediyse). Böyle bir hareket bulununca arama break ile
      biter (Ders 3).
    Talimatlar orders'taki sırayla döner.

    İki for satırında aynı adlar kullanılmıyor, kullanılsa dıştaki
    talimatın değerleri kaybolurdu. Talimatın gününün adı order_day;
    hareketler de başka adlarla geziliyor:
        for date, who, to, value, text in transactions:

    >>> orders = [("A", 8, "B", 500, "Kira"), ("A", 9, "C", 50, "Spor")]
    >>> due_orders(orders, [], "2026-11-08")
    [('A', 8, 'B', 500, 'Kira')]
    >>> due_orders(orders, [("2026-11-08", "A", "B", 500, "Kira")],
    ...            "2026-11-08")
    []
    """
    due = []
    day = int(today[8:])
    for order in orders:
        sender, order_day, receiver, amount, description = order
        if order_day != day:
            continue
        paid = False
        for date, who, to, value, text in transactions:
            if date != today or who != sender:
                continue
            if to == receiver and text == description:
                paid = True
                break
        if not paid:
            due.append(order)
    return due


# 5. görevin hazır function'ı: atm_withdraw

def atm_withdraw(transactions, file_name, today, iban, amount):
    """Hazır. QR ile ATM'den kartsız para çeker; (ok, message) tuple'ını
    return eder. Sizin yazdığınız balances'ı (1. görev) ve
    save_transaction'ı (3. görev) çağırıyor.

    Ders 5 notu: list, append(), dict, get(), tuple ve for'da unpacking
    Ders 5'te (17 Kasım); kısa açıklamaları README'nin "Ders 5'ten önce"
    bölümünde.

    Kurallar, sırayla:
    1. amount 0'dan büyük değilse ya da 10'un katı değilse (amount % 10
       sıfır değilse): (False, "Tutar 10'un katı olmalı.")
    2. Bugün bu hesaptan ATM'den çekilenlerin toplamı (tarihi today,
       göndereni iban, alıcısı "NAKIT" olan hareketler) + amount,
       ATM_LIMIT'ten büyükse: (False, "Günlük ATM limiti aşılıyor.")
       for satırında amount adı yeniden kullanılmıyor, kullanılsa
       parameter'ın değeri kaybolurdu; hareketin tutarının adı orada
       value.
    3. Bakiye (balances ile) amount'tan küçükse:
       (False, "Bakiye yetmiyor.")
    4. Hepsi tamamsa (today, iban, "NAKIT", amount, "ATM'den çekim")
       hareketi transactions'a eklenir, save_transaction ile yazılır ve
       altı haneli bir işlem numarasıyla şu return edilir:
           (True, "Paranızı alabilirsiniz. İşlem no: 483920")
       İşlem numarası random.randint(100000, 999999) (Ders 4); bunun
       için bank.py'nin başında "import random" satırı var.
    """
    if amount <= 0 or amount % 10 != 0:
        return False, "Tutar 10'un katı olmalı."
    taken = 0
    for date, sender, receiver, value, description in transactions:
        if date == today and sender == iban and receiver == "NAKIT":
            taken += value
    if taken + amount > ATM_LIMIT:
        return False, "Günlük ATM limiti aşılıyor."
    if balances(transactions).get(iban, 0) < amount:
        return False, "Bakiye yetmiyor."
    row = (today, iban, "NAKIT", amount, "ATM'den çekim")
    transactions.append(row)
    save_transaction(file_name, row)
    number = random.randint(100000, 999999)
    return True, f"Paranızı alabilirsiniz. İşlem no: {number}"


# Hesaplarım: her ay giren ve çıkan para

def monthly_flow(transactions, iban):
    """Hazır. iban'a her ay giren ve çıkan parayı {ay: (giren, çıkan)}
    dict'i olarak return eder. Ay, tarihin ilk yedi karakteri: "2026-09"
    gibi. iban'ın hiç hareketi olmayan ay dict'e girmez.

    >>> rows = [("2026-09-01", "NAKIT", "A", 100, "Burs"),
    ...         ("2026-09-02", "A", "B", 30, "Yemek"),
    ...         ("2026-10-04", "A", "B", 20, "Kahve"),
    ...         ("2026-10-05", "C", "D", 5, "Çay")]
    >>> monthly_flow(rows, "A")
    {'2026-09': (100, 30), '2026-10': (0, 20)}
    """
    flow = {}
    for date, sender, receiver, amount, description in transactions:
        month = date[:7]
        money_in, money_out = flow.get(month, (0, 0))
        if receiver == iban:
            flow[month] = (money_in + amount, money_out)
        elif sender == iban:
            flow[month] = (money_in, money_out + amount)
    return flow


# Para gönder: Kolay Adres ve son gönderdikleriniz

def add_alias(aliases, alias, iban, file_name):
    """Hazır. Bir hesaba Kolay Adres (e-posta) bağlar; (ok, message)
    tuple'ını return eder. Adres kurallara uyuyorsa aliases'a eklenir ve
    file_name'e "a" moduyla yazılır.

    >>> add_alias({}, "zehra@@ornek.test", "TR57", "aliases.csv")
    (False, 'E-posta adresinde bir tane @ olmalı.')
    >>> add_alias({}, "zehra@ornek", "TR57", "aliases.csv")
    (False, 'E-posta adresi ad@alan.uzantı gibi olmalı.')
    """
    alias = alias.strip().lower()
    if alias.count("@") != 1:
        return False, "E-posta adresinde bir tane @ olmalı."
    name, domain = alias.split("@")
    if name == "" or domain.count(".") == 0:
        return False, "E-posta adresi ad@alan.uzantı gibi olmalı."
    if "," in alias:
        return False, "E-posta adresinde virgül olmamalı."
    if alias in aliases:
        return False, "Bu adres başka bir hesaba bağlı."
    aliases[alias] = iban
    with open(file_name, "a", encoding="utf-8") as f:
        f.write(f"{alias},{iban}\n")
    return True, "Kolay Adres eklendi."


def update_recent(recent, receiver):
    """Hazır. Son gönderdikleriniz list'ini günceller; yeni list'i return
    eder. receiver list'in başına geçer; list RECENT_SIZE'dan uzunsa en
    eskisi, yani sonuncusu atılır. Function recent'ın kopyasıyla çalıştığı
    için uygulamanın elindeki list değişmez.

    >>> update_recent(["A", "B", "C"], "B")
    ['B', 'A', 'C']
    >>> update_recent(["A", "B", "C", "D", "E"], "F")
    ['F', 'A', 'B', 'C', 'D']
    """
    recent = recent.copy()
    if receiver in recent:
        recent.remove(receiver)
    recent.insert(0, receiver)
    if len(recent) > RECENT_SIZE:
        recent.pop()
    return recent


# Kartlarım ve Döküm: çift çekim, en çok harcananlar, abonelikler ve
# bütçe uyarıları

def double_charges(activity, card_id):
    """Hazır. Kartta aynı gün, aynı yerden, aynı tutarda ikinci kez
    çekilen harcamaları (date, merchant, amount) tuple'larının list'i
    olarak return eder. Görülen harcamalar bir set'te durur; set'te zaten
    olan bir harcama ikinci çekimdir.

    >>> activity = [("2026-10-01", "4821", "spend", "Kafe", "yemek", 80),
    ...             ("2026-10-01", "4821", "spend", "Kafe", "yemek", 80),
    ...             ("2026-10-02", "4821", "spend", "Kafe", "yemek", 80)]
    >>> double_charges(activity, "4821")
    [('2026-10-01', 'Kafe', 80)]
    """
    seen = set()
    doubles = []
    for date, owner, kind, merchant, category, amount in activity:
        if owner != card_id or kind != "spend":
            continue
        key = (date, merchant, amount)
        if key in seen:
            doubles.append(key)
        else:
            seen.add(key)
    return doubles


def top_categories(totals, k):
    """Hazır. En çok harcanan k kategoriyi, büyükten küçüğe, (category,
    total) tuple'larının list'i olarak return eder. totals,
    category_totals'ın verdiği {kategori: toplam} dict'i. Büyükten küçüğe
    dizmek için toplamlar sort()'tan önce 0 - total ile eksiye çevrilir.

    >>> top_categories({"market": 900, "yemek": 300, "kitap": 450}, 2)
    [('market', 900), ('kitap', 450)]
    """
    pairs = []
    for category, total in totals.items():
        pairs.append((0 - total, category))
    pairs.sort()
    top = []
    for negative, category in pairs[:k]:
        top.append((category, 0 - negative))
    return top


def subscriptions(activity, card_id, months):
    """Hazır. Verilen ayların her birinde harcama yapılan yerlerin set'ini
    return eder; her ay aynı yere ödeme çoğu zaman bir aboneliktir.
    Yerleri places (4. görev) buluyor; places henüz None return ediyorsa
    bu function da None return eder.

    >>> activity = [("2026-09-05", "4821", "spend", "Dizi Kutusu",
    ...              "abonelik", 149),
    ...             ("2026-09-09", "4821", "spend", "Kafe", "yemek", 80),
    ...             ("2026-10-05", "4821", "spend", "Dizi Kutusu",
    ...              "abonelik", 149),
    ...             ("2026-10-12", "4821", "spend", "Sinema", "eğlence",
    ...              150)]
    >>> subscriptions(activity, "4821", ["2026-09", "2026-10"])
    {'Dizi Kutusu'}
    """
    if len(months) == 0:
        return set()
    common = places(activity, card_id, months[0])
    if common is None:
        return None
    for month in months[1:]:
        found = places(activity, card_id, month)
        if found is None:
            return None
        common = common & found
    return common


def budget_warnings(totals, budgets):
    """Hazır. Bütçesinin yüzde 80'ine ya da fazlasına gelmiş kategorileri,
    en dolu olandan başlayarak, (category, spent, budget, percent)
    tuple'larının list'i olarak return eder. totals, category_totals'ın
    verdiği {kategori: harcama} dict'i; budgets, müşterinin {kategori:
    aylık bütçe} dict'i.

    >>> budget_warnings({"market": 900, "yemek": 300, "kitap": 450},
    ...                 {"market": 1000, "yemek": 1000, "kitap": 400})
    [('kitap', 450, 400, 112), ('market', 900, 1000, 90)]
    """
    rows = []
    for category, budget in budgets.items():
        spent = totals.get(category, 0)
        percent = spent * 100 // budget
        if percent >= 80:
            rows.append((0 - percent, category, spent, budget))
    rows.sort()
    warnings = []
    for negative, category, spent, budget in rows:
        warnings.append((category, spent, budget, 0 - negative))
    return warnings


# Döviz: kur makası

def spread_loss(tl_amount, buy_rate, sell_rate):
    """Hazır. tl_amount TL'lik döviz alıp hemen geri bozdurunca kaybedilen
    TL'yi return eder. Alış ve satış kuru arasındaki farka kur makası
    denir; banka kazancını buradan yapar. buy_foreign ve sell_foreign'ı
    (5. görev) kullanır; ikisinden biri henüz None return ediyorsa bu
    function da None return eder.

    >>> spread_loss(1000, 40.0, 41.2)
    29
    """
    bought = buy_foreign(tl_amount, sell_rate)
    if bought is None:
        return None
    units, cost = bought
    back = sell_foreign(units, buy_rate)
    if back is None:
        return None
    return cost - back


# Kredi ve birikim: vadeli mevduat, ödeme planı ve yaklaşan ödemeler

def deposit_interest(principal, yearly_rate, days):
    """Hazır. Vadeli mevduatın faizini (gross, tax, net) tuple'ı olarak
    return eder. principal yatırılan para, yearly_rate yıllık faiz yüzde
    olarak, days vade (gün); faizden yüzde TAX_PERCENT vergi kesilir (bu
    bankanın kuralı).

    >>> deposit_interest(10000, 40, 32)
    (351, 52, 299)
    """
    gross = round(principal * yearly_rate / 100 * days / 365)
    tax = gross * TAX_PERCENT // 100
    return gross, tax, gross - tax


def payment_plan(principal, monthly_rate, months):
    """Hazır. Kredinin ödeme planını return eder: her ay için (month,
    payment, interest, principal_part, remaining) tuple'larının list'i.
    Her ay taksitin bir kısmı o ayın faizine, kalanı borca (anaparaya)
    gider; son ay taksit kalan borcu tam kapatır. Taksiti loan_installment
    (5. görev) hesaplıyor; o henüz None return ediyorsa bu function da
    None return eder.

    >>> for row in payment_plan(3000, 2, 3):
    ...     print(row)
    (1, 1040, 60, 980, 2020)
    (2, 1040, 40, 1000, 1020)
    (3, 1040, 20, 1020, 0)
    """
    payment = loan_installment(principal, monthly_rate, months)
    if payment is None:
        return None
    r = monthly_rate / 100
    remaining = principal
    plan = []
    for month in range(1, months + 1):
        interest = round(remaining * r)
        principal_part = payment - interest
        this_payment = payment
        if month == months:
            principal_part = remaining
            this_payment = principal_part + interest
        remaining = remaining - principal_part
        plan.append((month, this_payment, interest, principal_part,
                     remaining))
    return plan


def upcoming_payments(card_bills, loans, today, days):
    """Hazır. Bugünden başlayıp days gün içindeki kart ve kredi
    ödemelerini, tarih sırasıyla, (date, what, amount) tuple'larının
    list'i olarak return eder. card_bills, (card_id, due, minimum)
    tuple'ları; loans, (loan_id, start, plan) tuple'ları. Tarihleri dates
    module'ü hesaplıyor: bank.py'nin başına import dates satırını
    (4. görev) yazmadıysanız bu function NameError verir.

    >>> plan = [(1, 1040, 60, 980, 2020), (2, 1040, 40, 1000, 1020),
    ...         (3, 1040, 20, 1020, 0)]
    >>> found = upcoming_payments([("4821", "2026-11-25", 893)],
    ...                           [("K1", "2026-10-20", plan)],
    ...                           "2026-11-08", 30)
    >>> for row in found:
    ...     print(row)
    ('2026-11-20', 'Kredi K1, 1. taksit', 1040)
    ('2026-11-25', 'Kart 4821 asgari ödeme', 893)
    """
    last = dates.add_days(today, days)
    found = []
    for card_id, due, minimum in card_bills:
        if due >= today and due <= last:
            found.append((due, f"Kart {card_id} asgari ödeme", minimum))
    for loan_id, start, plan in loans:
        for month, payment, interest, part, remaining in plan:
            date = dates.add_months(start, month)
            if date >= today and date <= last:
                found.append((date, f"Kredi {loan_id}, {month}. taksit",
                              payment))
    found.sort()
    return found


# ATM: banknotlar ve kart numarası kontrolü

def banknotes(amount):
    """Hazır. ATM'nin vereceği banknotları, büyükten küçüğe, (note, count)
    tuple'larının list'i olarak return eder; banknotlar NOTES'ta.

    >>> banknotes(380)
    [(200, 1), (100, 1), (50, 1), (20, 1), (10, 1)]
    >>> banknotes(600)
    [(200, 3)]
    """
    result = []
    for note in NOTES:
        count = amount // note
        if count > 0:
            result.append((note, count))
            amount = amount % note
    return result


def luhn_valid(number):
    """Hazır. Kart numarasının son hanesine, yani kontrol hanesine bakar
    (Luhn kontrolü); True ya da False return eder. Bir rakamı yanlış
    yazılmış numara bu kontrolden geçmez.

    Kart şirketlerinin denemeler için yayımladığı numaralar:
    >>> luhn_valid("4111 1111 1111 1111")
    True
    >>> luhn_valid("4111 1111 1111 1112")
    False
    """
    number = number.replace(" ", "")
    if len(number) != 16:
        return False
    for char in number:
        if char in DIGITS:
            continue
        return False
    total = 0
    for char in number[-1::-2]:
        total += int(char)
    for char in number[-2::-2]:
        doubled = int(char) * 2
        if doubled > 9:
            doubled = doubled - 9
        total += doubled
    return total % 10 == 0
