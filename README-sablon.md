<!-- Bu şablonu doldurun; köşeli parantezli yerleri kendi yazınızla değiştirin, bu satırı da silin. Bankanızın iki ekran görüntüsünü bu şablonun yanına, proje klasörüne koyun: Hesaplarım için ekran.png, Raporum için raporum.png. Sonra proje klasöründeki ödev açıklamasını (README.md) silip bu şablonun adını README.md yapın (sağ tık, Refactor, Rename). -->

# [Bankanızın adı]

**Hazırlayanlar:** [adınız soyadınız; grupla yaptıysanız en fazla üç kişinin adı]

[Bir iki cümle: bu proje ne yapıyor? Örneğin: Python'la yazılmış küçük bir bankanın internet bankacılığı. Müşteriler şifreyle giriyor; aynı şubeye, başka şubelere ve başka bankalara para gönderiyor; kredi kartıyla alışveriş yapıyor; döviz alıp bozduruyor, kredi taksitini ve birikim hedefini hesaplıyor, ATM'den QR ile para çekiyor. Ekran tarayıcıda açılıyor, hesapların hepsi `bank.py`'de.]

> Bu bir programlama ödevi. Banka, müşteriler ve bütün sayılar kurgusal; gerçek bir bankayla ilgisi yok.

## Ekran

![Bankanın Hesaplarım ekranı](ekran.png)

[Görüntüde ne var? Hangi müşteriyle girdiniz, bankanıza hangi adı ve rengi verdiniz?]

![Raporum sekmesi](raporum.png)

[Raporunuzun bir cümlelik tanımı.]

[Ekran görüntülerini kendiniz alın: Windows'ta Windows + Shift + S, macOS'ta Command + Shift + 4 ile ekranın bir parçasını seçebilirsiniz. Görüntülerde yalnız uygulamanın kurgusal verisi görünsün; gerçek bir şifre, kart ya da kimlik numarası görünmesin.]

## Neler yapıyor

- **Kayıtlar ve şubeler:** bakiyeler, hesap hareketleri, her ay giren ve çıkan para; bozuk kayıtlar atlanıp sayılıyor; şubeler müşteri sayısına ve toplam paraya göre karşılaştırılıyor.
- **Güvenli giriş:** yeni şifreler kurallara göre denetleniyor; şifreler hash'leri ve salt'larıyla saklanıyor, şifrenin kendisi hiçbir yere yazılmıyor; üst üste üç yanlış denemede hesap kilitleniyor; şifre değiştirilebiliyor.
- **Para gönderme ve talimatlar:** havale, şubeler arası havale ve EFT, IBAN ya da Kolay Adres'le; IBAN'ın kontrol haneleri, bakiye ve günlük limit denetleniyor, masraf şubeye ve bankaya göre kesiliyor; son gönderilenler listesi; otomatik ödeme talimatları.
- **Kredi kartı ve döküm:** limit, borç, ekstre, asgari ödeme, son ödeme günü ve çift çekim; kategori toplamları, abonelikler, ilk kez gidilen yerler ve bütçe uyarıları; taksit hesabı.
- **Döviz ve kredi:** döviz alıp bozdurma ve kur makası; kredi taksiti ve ödeme planı; vadeli mevduat ve birikim hedefi; yaklaşan ödemeler.
- **ATM:** QR ile kartsız para çekme, verilen banknotlar ve işlem numarası; kart numarası kontrolü.
- **Raporum:** [raporunuzun bir cümlelik tanımı]
- **Testler:** `testlerim.py`'de [kaç] assert ve bir IBAN deneme loop'u (döngü).
- [Kendi eklediklerinizi, örneğin Meraklısına'dan yaptıklarınızı, buraya ekleyin.]

Ekran (`ui/`) ile `app.py`, `kontrol.py`, `security.py`, `dates.py` ve `records.py` dersin hazır verdiği file'lar (dosya). Bankanın hesaplarının çoğunu yapan function'lar (fonksiyon) `bank.py`'de, testler `testlerim.py`'de; onları [biz yazdık / ben yazdım]. `bank.py`'nin sonundaki hazır function'lar da dersin.

## Raporum

[Raporunuzun fikri: ne gösteriyor, neden, nasıl hesaplanıyor? Raporum sekmesindeki tablodan birkaç satır da koyabilirsiniz.]

## Nasıl çalıştırılır

1. Klasörü PyCharm'da açın. Python 3.14 yeterli; başka bir şey kurmak gerekmiyor.
2. `app.py`'yi **Run** ile çalıştırın; banka tarayıcıda http://127.0.0.1:8000 adresinde açılır. Durdurmak için **Stop** düğmesine basın.
3. Deneme için 1001 numara ve `kedi123` şifresiyle Zehra olarak girebilir ya da yeni müşteri olabilirsiniz. Deneme şifreleri de kurgusal; yeni müşteri olurken başka bir yerde kullandığınız bir şifreyi yazmayın.
4. `kontrol.py`'yi **Run** ile çalıştırırsanız `bank.py`'deki function'ları dener. `testlerim.py` önce testleri çalıştırır, sonra IBAN sorar; boş bir satır loop'u bitirir.

## Ne öğrendim

[Birkaç cümle: bu projede neyi ilk kez yaptınız, nerede zorlandınız, neyi başka türlü yapardınız?]

## Veri

Müşteriler, hesaplar, şubeler, IBAN'lar, kartlar, harcamalar, krediler ve kurlar kurgusal; IEEE Hacettepe Introduction to Python dersinin proje ödevi için üretildi ve [CC0 1.0](https://creativecommons.org/publicdomain/zero/1.0/deed.tr) ile serbest. Gerçek bir kişiyle ya da bankayla ilgileri yok. Uygulamanın deneme şifreleri de kurgusal.

## Ekip

[İsimleriniz; GitHub kullanıyorsanız kullanıcı adlarınız.]
