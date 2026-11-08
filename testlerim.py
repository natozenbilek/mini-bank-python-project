# Introduction to Python, Proje ödevi: testlerim.py (5. görev)
#
# Bu file'da (dosya) bank.py'deki function'larınızı (fonksiyon) kendiniz
# deneyeceksiniz. assert bir şartı sınar: şart True ise bir şey olmaz,
# False ise program AssertionError ile durur ve hangi satırda durduğunu
# söyler (Ders 3).
#
# 1. En az beş assert yazın; bu assert'ler bank.py'deki en az üç farklı
#    function'ı denesin. Her assert docstring'lerdeki örneklerden başka
#    bir girdi kullansın. Örnek:
#        assert bank.installments(100, 3) == [34, 33, 33]
#    Ders 5 notu: list (liste) ve tuple (demet) Ders 5'te (17 Kasım);
#    kısa açıklamaları README'nin "Ders 5'ten önce" bölümünde.
# 2. Bütün assert'lerden sonra print ile "Bütün testler geçti."
#    yazdırın.
# 3. Sonra bir IBAN deneme loop'u (döngü) yazın: while True ile
#    input'tan bir IBAN alın, soru "IBAN (çıkmak için boş bırakın): "
#    olsun. Boş satır gelirse break ile loop'tan çıkın; değilse
#    boşlukları silip büyük harfe çevirin ve bank.iban_valid'e göre
#    "Geçerli" ya da "Geçersiz" yazdırın.
#
# Run deyip deneyin. kontrol.py de bu file'ı çalıştırıp en az beş assert
# olduğuna, bunların en az üç farklı function'ı denediğine,
# "Bütün testler geçti." yazdığına ve IBAN loop'unun çalıştığına bakıyor
# (5. görev).

import bank

# TODO: en az beş assert

# TODO: "Bütün testler geçti." yazdırın

# TODO: IBAN deneme loop'u
