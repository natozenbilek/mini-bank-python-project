# Veri

Bu klasördeki on bir CSV file'ının (dosya) hepsi kurgusal: müşteriler, hesaplar, şubeler, IBAN'lar, para hareketleri, kartlar, krediler ve kurlar bu proje için üretildi, gerçek bir kişiyle ya da bankayla ilgileri yok. Banka kodu 12345 bizim bankanın, 67890 başka bir bankanın; ikisi de uyduruldu. Her file'ın ilk satırı başlık, alanlar virgülle ayrılıyor, tarihler `2026-11-08` biçiminde. Tutarlar tam sayı; kurlar ve faiz oranları ondalık noktalı sayı.

| File | Satır | İçinde |
|---|---|---|
| `customers.csv` | 14 | müşteriler, şifrelerin salt'ı ve hash'i |
| `accounts.csv` | 20 | hesaplar: IBAN, sahibi, para birimi |
| `branches.csv` | 3 | şubeler |
| `transactions.csv` | 233 ve 6 bozuk | para hareketleri |
| `aliases.csv` | 14 | Kolay Adres'ler: e-posta ve IBAN |
| `orders.csv` | 8 | otomatik ödeme talimatları |
| `loans.csv` | 4 | krediler |
| `cards.csv` | 12 | kredi kartları |
| `card_activity.csv` | 452 | kart harcamaları ve karta ödemeler |
| `budgets.csv` | 10 | müşterilerin aylık bütçeleri |
| `rates.csv` | 138 | günlük USD ve EUR kurları |

Satır sayılarına başlık girmiyor. `initial/` klasöründe bu on bir file'ın ilk hali duruyor; ekrandaki **Verileri ilk haline döndür** düğmesi onları buraya geri kopyalıyor. `initial/`'daki file'ları değiştirmeyin.

Uygulama yaptığınız işlemleri bu file'lara yazıyor: gönderdiğiniz para, masraflar, ATM'den çekimler, döviz alım satımı ve kart ödemeleri `transactions.csv`'ye; yeni müşteri `customers.csv`'ye, onun TL hesabı `accounts.csv`'ye; kart harcamaları ve ödemeleri `card_activity.csv`'ye; yeni Kolay Adres `aliases.csv`'ye, yeni talimat `orders.csv`'ye ekleniyor. Şifre değiştirmek `customers.csv`'yi, bütçe koymak `budgets.csv`'yi baştan yazıyor. `branches.csv`, `loans.csv`, `cards.csv` ve `rates.csv`'ye uygulama dokunmuyor.

## customers.csv

14 müşteri, numaraları 1001'den 1014'e: Zehra, Eren, Emre, Mehmet, İrem, Fatih, Fatma, Ömer, Nur, Batu, Harun, Raşit, Adnan ve Engin.

| Sütun | İçinde |
|---|---|
| `customer_no` | müşteri numarası |
| `name` | müşterinin adı |
| `salt` | müşteriye özel, rastgele 16 karakterlik salt |
| `password_hash` | şifrenin hash'i, 64 karakter; 2. görevin `hash_password`'ünün sonucu |

Şifrelerin kendisi hiçbir file'da yok. Deneme için üç müşterinin şifresi ödevin README'sinde yazıyor.

## accounts.csv

20 hesap: her müşterinin bir TL hesabı var; Zehra, Mehmet, Fatih ve Nur'un birer USD, Eren ile Fatma'nın birer EUR hesabı da var.

| Sütun | İçinde |
|---|---|
| `iban` | hesabın IBAN'ı, örneğin Zehra'nın TL hesabı `TR571234500101100100000001` |
| `customer_no` | hesabın sahibi |
| `currency` | `TL`, `USD` ya da `EUR` |

IBAN'ların hepsi kontrol hanelerine göre geçerli (mod 97, 3. görev). 16 haneli hesap numarası üç parçadan oluşuyor: şube kodu (4 hane), müşteri numarası (4 hane) ve hesabın sırası (8 hane). Zehra'nın TL hesabında bunlar `0101`, `1001` ve `00000001`. TL hesaplarının numarası 1, USD hesaplarınınki 2, EUR hesaplarınınki 3 ile bitiyor. Uygulamada yeni müşteri olunca ya da bir dövizi ilk kez alınca buraya yeni bir hesap eklenir.

## branches.csv

Bankanın üç şubesi.

| Sütun | İçinde |
|---|---|
| `code` | şube kodu: IBAN'daki hesap numarasının ilk dört hanesi, `iban[10:14]` |
| `name` | şubenin adı |

Şubeler: `0101` Kızılay (Zehra, Emre, İrem, Nur, Adnan), `0102` Beytepe (Eren, Ömer, Batu, Engin), `0103` Sıhhiye (Mehmet, Fatih, Fatma, Harun, Raşit).

## transactions.csv

1 Eylül ile 7 Kasım 2026 arasındaki 233 para hareketi ve bilerek bozulmuş 6 satır.

| Sütun | İçinde |
|---|---|
| `date` | tarih |
| `sender` | parayı gönderen |
| `receiver` | parayı alan |
| `amount` | tutar, tam sayı |
| `description` | açıklama, örneğin `Burs`, `Kira`, `ATM'den çekim` |

Gönderen ve alan ya bir IBAN ya da şu sözcüklerden biri: `NAKIT` (şubeden ya da ATM'den yatırılan ya da çekilen para), `MASRAF` (bankanın kestiği masraf), `DOVIZ` (döviz alım satımında bankanın döviz kasası), `KART-4821` gibi (o karta yapılan ödeme), `KREDI-K1` gibi (o kredinin taksiti ya da kullanımı). Tutar TL hesaplarında TL, USD ve EUR hesaplarında o dövizin birimi: örneğin 11 Eylül'de `DOVIZ`'den Zehra'nın USD hesabına giden 28, 28 dolar demek.

Hareketler: 56 para yatırma (hesap açılışı, burs, maaş, harçlık), 35 ATM'den çekim, müşteriler arasında 30 havale (dördü harçlık talimatı), 67890 kodlu başka bir bankaya 18 kira EFT'si, 18 EFT masrafı, 20 şubeler arası havale masrafı, 24 kart ödemesi, 8 kredi satırı (6 taksit, K3 ve K4'ün kullanımı) ve 24 döviz satırı (12 alım ya da bozdurma, her biri iki satır). Her EFT'nin hemen arkasında 5 TL'lik bir `MASRAF` satırı, başka bir şubeye giden her havalenin arkasında 2 TL'lik bir `MASRAF` satırı var.

Bozuk satırları `bank.py`'deki hazır `load_transactions` atlayıp sayıyor. Birinde dört parça var (açıklama yok), birinde altı parça var (açıklamanın içinde virgül var); dördünde de tutar bir tam sayı değil: `1.500`, `beşyüz`, boş ve `12O0` (sıfır yerine O harfi). `load_transactions` bu 6 satırı atlar. Öbür on file'da bozuk satır yok.

## aliases.csv

Kolay Adres: her müşterinin TL hesabına bağlı bir e-posta adresi, örneğin `zehra@ornek.test`. `.test` denemelere ayrılmış bir alan adı; bu adresler hiçbir gerçek adrese gitmez.

| Sütun | İçinde |
|---|---|
| `alias` | e-posta adresi, küçük harfle |
| `iban` | adresin bağlı olduğu IBAN |

## orders.csv

8 otomatik ödeme talimatı: Eren, Mehmet, Fatih, Fatma, Nur ve Harun'un her ayın 5'inde başka bankadaki ev sahibine gönderdiği kira; Mehmet'ten Emre'ye her ayın 10'unda 1500 TL, Fatih'ten Batu'ya her ayın 15'inde 1000 TL harçlık.

| Sütun | İçinde |
|---|---|
| `sender` | parayı gönderen IBAN |
| `day` | ayın kaçında gönderildiği |
| `receiver` | alıcının IBAN'ı |
| `amount` | tutar, TL |
| `description` | açıklama: `Kira` ya da `Harçlık` |

Uygulama bir talimatı, günü geldiğinde talimatı veren müşteri Hesaplarım'ı açınca öder.

## loans.csv

4 kredi.

| Sütun | İçinde |
|---|---|
| `loan_id` | kredinin adı, `K1` gibi |
| `customer_no` | krediyi çeken müşteri |
| `principal` | çekilen para, TL |
| `monthly_rate` | aylık faiz, yüzde olarak: `3.2`, ayda yüzde 3,2 demek |
| `months` | taksit sayısı |
| `start` | kredinin çekildiği gün; taksitler her ay bu günde ödeniyor |

| Kredi | Müşteri | Tutar | Aylık faiz | Taksit | Başlangıç |
|---|---|---|---|---|---|
| K1 | Eren | 60000 TL | yüzde 3,2 | 12 | 15 Temmuz 2026 |
| K2 | Mehmet | 150000 TL | yüzde 2,9 | 24 | 10 Mart 2026 |
| K3 | Fatma | 40000 TL | yüzde 3,5 | 9 | 20 Eylül 2026 |
| K4 | Nur | 25000 TL | yüzde 3,4 | 6 | 1 Ekim 2026 |

## cards.csv

12 kredi kartı: Harun ile Raşit dışında her müşterinin bir kartı var.

| Sütun | İçinde |
|---|---|
| `card_id` | kartın son dört hanesi, örneğin Zehra'nın kartı `4821` |
| `customer_no` | kartın sahibi |
| `limit` | kartın limiti, TL |
| `cut_day` | hesap kesim günü, ayın kaçı olduğu |

## card_activity.csv

Kartların 1 Eylül ile 7 Kasım 2026 arasındaki 452 hareketi: 428 harcama ve 24 karta ödeme. Hiçbir harcama kartın limitini, hiçbir ödeme kartın borcunu aşmıyor.

| Sütun | İçinde |
|---|---|
| `date` | tarih |
| `card_id` | kartın son dört hanesi |
| `kind` | `spend` (harcama) ya da `payment` (karta ödeme) |
| `merchant` | harcamanın yapıldığı yer; ödemede `-` |
| `category` | `market`, `yemek`, `ulaşım`, `eğlence`, `kitap`, `giyim`, `sağlık` ya da `abonelik`; ödemede `-` |
| `amount` | tutar, TL |

Abonelikler (Dizi Kutusu, Müzik Kutusu, Bulut Depo, Spor Salonu) her ayın 7'sinde çekiliyor. İki kartta birer çift çekim var: 4821'de 10 Ekim'de Oyun Mağazası'ndan 300 TL, 8417'de 24 Eylül'de Kart Dolum'dan 160 TL. Yerlerin adları uyduruldu.

## budgets.csv

Zehra, Eren, Emre ve Mehmet'in bazı kategoriler için koyduğu aylık bütçeler. Uygulamada bütçe koyunca bu file baştan yazılır.

| Sütun | İçinde |
|---|---|
| `customer_no` | müşteri |
| `category` | kategori, `card_activity.csv`'dekilerden biri |
| `amount` | o kategori için aylık bütçe, TL |

## rates.csv

USD ve EUR kurları, 1 Eylül ile 8 Kasım 2026 arasındaki her gün için iki satır. Kurlar kurgusal; 8 Kasım'dan sonraki günlerde uygulama son kuru kullanıyor.

| Sütun | İçinde |
|---|---|
| `date` | tarih |
| `currency` | `USD` ya da `EUR` |
| `buy` | bankanın dövizi aldığı kur, TL |
| `sell` | bankanın dövizi sattığı kur, TL |

## Lisans

Bu klasördeki bütün file'lar kurgusal ve [CC0 1.0](https://creativecommons.org/publicdomain/zero/1.0/deed.tr) ile serbest: kendi reponuza koyabilir, istediğiniz gibi kullanabilirsiniz.
