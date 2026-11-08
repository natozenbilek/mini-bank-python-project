# Projeyi GitHub'da göstermek

Bu adımlar isteğe bağlı ve puan getirmez. Projenizi kendi repository'nizde, yani file'larının (dosya) durduğu bir GitHub sayfasında göstermek isterseniz diye yazıldı. Ödevi indirdiğiniz sayfa da bir repository. Kurulum gerekmiyor; hepsi tarayıcıdan yapılıyor. GitHub'ı hiç kullanmadıysanız adımları sırayla izleyin.

## 1. Hesap açmak

github.com'da **Sign up** ile bir hesap açın. Sonra **Settings** sayfasının **Emails** bölümünde **Keep my email addresses private** kutusunu işaretleyin: e-posta adresiniz yüklediğiniz file'larla birlikte herkese görünmez.

## 2. Repository açmak

Sağ üstteki **+** düğmesinden **New repository** deyin. Adını siz koyun, örneğin `mini-bank` ya da `python-bank`; `odev` ya da `proje` gibi bir ad koymayın, bu sayfa işlerinizi gösterdiğiniz yer. README eklemeyin; kendi README.md'nizi 3. adımda yükleyeceksiniz.

**Private** seçin. **Public** bir repository'deki kodu herkes görür; son günden önce açılırsa çözümünüz başkalarına gider. 30 Kasım'dan sonra repository'nin **Settings** sayfasından **Public** yapın. Sonra **Create repository** deyin.

## 3. File'ları yüklemek

Repository boşken sayfadaki **uploading an existing file** bağlantısına tıklayın; daha önce file yüklediyseniz **Add file**, **Upload files** deyin. Proje klasöründeki file'ları ve `data` ile `ui` klasörlerini sürükleyip bırakın; klasörler içindekilerle birlikte gelir. `__pycache__` klasörünü, `README-sablon.md`'yi ve `GITHUB.md`'yi yüklemeyin. `img` klasörüne de gerek yok: içindeki kart ve ekran görüntüleri ödevin açıklamasına ait. Altta yaptığınız değişikliği anlatan kısa bir açıklama yazıp **Commit changes** deyin.

`data/customers.csv`'ye dikkat: uygulamada başka bir yerde de kullandığınız bir şifreyle yeni müşteri olduysanız bu file'ı o haliyle yüklemeyin. File'da şifrenin kendisi yok, ama hash'i ve salt'ı var; tahmin edilebilir bir şifre bunlardan bulunabilir. Önce uygulamadaki **Verileri ilk haline döndür** düğmesine basın. Uygulamanın deneme şifreleri (`kedi123` gibi) sorun değil; zaten ödevin README'sinde yazıyorlar. Hiçbir file'da gerçek bir şifre, kart ya da TC kimlik numarası olmasın.

## 4. Ekran görüntüleri

Bankanızın iki ekran görüntüsünü yükleyin: Hesaplarım'ı `ekran.png`, Raporum'u `raporum.png` adıyla. README'nizdeki resimler onlar. Görüntülerde yalnız uygulamanın kurgusal verisi görünsün.

## 5. README

`README-sablon.md`'yi doldurup `README.md` adıyla yükleyin; repository'nin ön sayfası o olur. Teslimde bunu yaptıysanız `README.md`'niz hazır. Bankanızın neler yaptığı, kendi raporunuz ve testleriniz orada anlatılıyor.

## 6. Grupla çalışmak

Repository'yi gruptan bir kişi açar ve repository'nin **Settings** sayfasının **Collaborators** bölümünde **Add people** ile öbür üyeleri GitHub kullanıcı adlarıyla davet eder. Davet edilen üye, gelen e-postadan ya da GitHub bildiriminden daveti kabul edince yükleme yapabilir. Her üye kendi hesabından en az bir değişiklik yükleyince repository'nin sayfasındaki **Contributors** listesinde görünür.

Birlikte yazdığınız bir değişikliği yüklerken açıklamanın en altına her ortağınız için bir satır ekleyebilirsiniz; GitHub değişikliği hepinizin adına gösterir:

```text
Co-authored-by: Ad Soyad <ortağınızın no-reply adresi>
```

No-reply adresi, ortağınızın **Settings**, **Emails** sayfasında görünen ve `@users.noreply.github.com` ile biten adres.

## 7. Profilde sabitlemek

Profil sayfanızda **Customize your pins** deyip bu repository'yi seçin; profilinize gelen herkes önce onu görür.

## Verinin lisansı

`data` klasöründeki file'lar kurgusal ve CC0 1.0 ile serbest; kendi repository'nize koyabilirsiniz. Ekran, `app.py`, `kontrol.py`, hazır module'ler (modül) ve `bank.py`'nin sonundaki hazır function'lar (fonksiyon) dersin; README'nizde hazır geldiklerini yazın, şablondaki cümle bunu söylüyor.
