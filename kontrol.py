# Proje ödevi kontrolü: bank.py'de sizin yazdığınız function'ları (fonksiyon) görev görev, küçük
# örneklerle dener ve testlerim.py'yi de çalıştırır; bank.py'nin sonundaki hazır function'lara bakmaz.
# PyCharm'da bu file'ı (dosya) açıp Run deyin. bank.py, testlerim.py, security.py, dates.py ve records.py bu
# file'la aynı klasörde olmalı. Not vermez, yol gösterir. data klasöründeki file'lara dokunmaz:
# function'larınızı kendi küçük deneme file'larıyla, geçici bir klasörde dener; testlerim.py'yi de projenin
# geçici bir kopyasında çalıştırır. Bankanızın ekranını görmek için app.py'yi çalıştırın.
import ast
import builtins
import contextlib
import io
import json
import math
import os
import pathlib
import re
import shutil
import subprocess
import sys
import tempfile
import traceback
import types

import records

HERE = pathlib.Path(__file__).resolve().parent
ENGINE = HERE / "bank.py"
TESTS = HERE / "testlerim.py"
DATA = HERE / "data"
TIMEOUT = 20        # saniye: bir görevin denemesi bundan uzun sürerse yarıda kesilir
TEST_TIMEOUT = 8    # saniye: testlerim.py için aynısı
MARK = "KONTROL-SONUCU "

TASKS = {
    1: "1. Kayıtlar ve şubeler",
    2: "2. Güvenli giriş",
    3: "3. Para gönderme ve talimatlar",
    4: "4. Kredi kartı ve döküm",
    5: "5. Döviz, kredi, ATM ve raporunuz",
}

# bank.py'nin başındaki kurallar; aşağıdaki beklenen sonuçlar bu değerlerle hesaplandı.
RULES = {"BANK_CODE": "12345", "BRANCH_FEE": 2, "EFT_FEE": 5, "DAILY_LIMIT": 50000, "ATM_LIMIT": 10000,
         "ROUNDS": 1000, "MIN_PERCENT": 20, "DUE_DAYS": 10, "DIGITS": "0123456789",
         "LETTERS": "abcçdefgğhıijklmnoöprsştuüvyzqwx"}
HEADER = "date,sender,receiver,amount,description"
CUSTOMERS_HEADER = "customer_no,name,salt,password_hash"
TODAY = "2026-11-08"


make_iban = records.make_iban   # kontrol haneleri mod 97'ye göre doğru bir TR IBAN'ı kurar


def one_digit_off(iban):
    """Son rakamı değiştirilmiş, yani bir rakamı yanlış yazılmış IBAN."""
    return iban[:-1] + str((int(iban[-1]) + 1) % 10)


# Deneme hesapları. Şube kodu IBAN'ın 11-14. karakterleri: 0101 Kızılay, 0102 Beytepe, 0103 Sıhhiye.
A = "TR571234500101100100000001"    # Zehra, Kızılay, TL
C = "TR301234500101100100000002"    # Zehra, Kızılay, USD
A2 = "TR481234500101100300000001"   # Emre, Kızılay, TL
B = "TR121234500102100200000001"    # Eren, Beytepe, TL
B_EUR = "TR551234500102100200000003"   # Eren, Beytepe, EUR
D = "TR111234500103100400000001"    # Mehmet, Sıhhiye, TL
D_USD = "TR811234500103100400000002"   # Mehmet, Sıhhiye, USD
E = "TR021234500103100600000001"    # Fatih, Sıhhiye, TL
H = "TR031234500101101300000001"    # Adnan, Kızılay, TL
H_USD = make_iban("12345", "0102101300000002")   # Adnan'ın Beytepe'deki USD hesabı
N = "TR551234500102101400000001"    # Engin, Beytepe, TL; hiç hareketi yok
X = "TR136789005500123400001234"    # başka bir bankada bir hesap
GHOST = make_iban("12345", "0103109900000001")   # geçerli ama bankamızda böyle bir hesap yok
LETTERED = "TR31678900AB00CD0000012345"   # hesap numarasında harf olan geçerli bir IBAN
NOT_TR = "DE461234500101100100000001"     # mod 97'den geçen ama TR olmayan bir IBAN

FILE_FUNCTIONS = ("register", "change_password", "save_transaction")
UNKNOWN_NO = 1099   # login'in denendiği, customers'ta olmayan numara


class Problem(Exception):
    """Bir görevde bulunan eksik; mesajı öğrenciye gösterilir."""


class DataFile(Exception):
    """bank.py, kontrol sırasında data klasöründeki bir file'ı açmak istedi."""


def short(value, limit=90):
    if type(value) is set and value:
        items = []
        for item in value:
            items.append(repr(item))
        items.sort()
        text = "{" + ", ".join(items) + "}"
    else:
        text = repr(value)
    return text if len(text) <= limit else text[:limit] + " ..."


def sentence(text):
    """Error message'ın son satırı; geçici klasörün yolu kısaltılmış, sonunda tek bir nokta."""
    if TMP["path"]:
        text = text.replace(TMP["path"] + os.sep, "")
    return text if text[-1:] in (".", "?", "!") else text + "."


TMP = {"path": ""}   # child'ın geçici klasörü


def type_name(value):
    """Değerin tipinin adı: list (liste), dict (sözlük), NoneType gibi."""
    return type(value).__name__


def equal(got, want):
    """got, want'la aynı mı? Tiplere de bakar: 24.0, 24'ün; list de tuple'ın (demet) yerini tutmaz."""
    if type(want) is bool:
        return got is want
    if type(want) is int:
        return type(got) is int and got == want
    if type(want) is float:
        return type(got) in (int, float) and math.isclose(got, want, rel_tol=1e-9, abs_tol=1e-9)
    if type(want) in (tuple, list):
        return type(got) is type(want) and len(got) == len(want) and all(equal(g, w) for g, w in zip(got, want))
    if type(want) is dict:
        return type(got) is dict and set(got) == set(want) and all(equal(got[k], want[k]) for k in want)
    return type(got) is type(want) and got == want


def with_hint(text, hint):
    note = shadow_note(SHADOW["name"])
    if note:
        hint = f"{note} {hint}" if hint else note
    return f"{text} {hint}" if hint else text


def bank_line(error):
    """Hatanın bank.py'deki satır numarası; bulunamazsa None."""
    if isinstance(error, SyntaxError) and error.filename and pathlib.Path(error.filename).name == "bank.py":
        return error.lineno
    line = None
    for frame in traceback.extract_tb(error.__traceback__):
        if pathlib.Path(frame.filename).name == "bank.py":
            line = frame.lineno
    return line


IMPORT_HINT = " bank.py'nin başına import {0} satırını yazın; yeri file'ın başındaki yorumda gösteriliyor."
# import random sizin yazdığınız bir satır değil: bank.py'nin başında hazır duruyor, ATM'nin işlem numarası için
# hazır kod kullanıyor. Silinmişse 5. görevin satırının altında bu uyarı çıkar; görevin ✓ ya da ✗ almasını
# değiştirmez.
RANDOM_WARNING = ("  Uyarı: bank.py'nin başındaki import random satırı silinmiş. Hazır kod ATM'nin işlem numarasını "
                  "random ile veriyor; satırı yerine geri koyun, yoksa uygulamada ATM'den para çekilemez.")


def error_hint(name, error):
    """Sık yapılan hatalar için kısa bir ipucu; yoksa boş str (karakter dizisi)."""
    text = str(error)
    if isinstance(error, UnboundLocalError):
        return " Bu variable'a (değişken) function'ın içinde, kullanmadan önce bir değer verin."
    if isinstance(error, NameError):
        missing = getattr(error, "name", None)
        if missing in ("security", "dates"):
            return IMPORT_HINT.format(missing)
        return " Python bu adı tanımıyor: yazımına bakın; bir variable'sa kullanmadan önce ona bir değer verin."
    if isinstance(error, KeyError):
        key = error.args[0] if error.args else None
        if name == "login" and key == UNKNOWN_NO:
            return (f" {UNKNOWN_NO} customers'ta yok: önce if customer_no in customers ile bakın, yoksa \"unknown\" "
                    "return edin.")
        if name == "login":
            return " Bu müşterinin failed'da henüz sayısı yok: failed.get(customer_no, 0) ile 0'dan başlayın."
        if name in ("balances", "category_totals"):
            return " Bu key (anahtar) dict'te henüz yok: get() ile 0'dan başlayın, dict.get(key, 0) gibi."
        if name == "branch_report" and isinstance(key, str) and key[:2] == "TR":
            return (" Hiç hareketi olmayan bir hesabın balances'ta key'i yok: bakiyeyi money.get(iban, 0) ile "
                    "alın.")
        if name == "branch_report":
            return (" Bu şube dict'te henüz yok: şube dict'te yoksa {customer_no} ile yeni bir set (küme) koyun, "
                    "varsa add() ile ekleyin; toplam için totals.get(branch, 0).")
        if name == "resolve_receiver":
            return (" Önce text.lower() in aliases ile bakın: aliases'ta olmayan bir key'le aliases[...] KeyError "
                    "verir.")
        return " Bu key dict'te yok."
    if isinstance(error, FileNotFoundError) and name in FILE_FUNCTIONS:
        return (" open()'a file'ın adını elle yazmayın, function'a verilen file_name'i verin: kontrol.py "
                "function'ı kendi deneme file'ıyla çağırıyor.")
    if isinstance(error, (UnicodeDecodeError, UnicodeEncodeError)):
        return " File'ı açarken encoding=\"utf-8\" yazın: open(file_name, encoding=\"utf-8\") gibi."
    if isinstance(error, ValueError) and name == "iban_valid":
        return (" int() rakam olmayan bir karakterde ValueError verir. Harfleri önce ord() ile sayıya çevirin; "
                "\"-\" ya da boşluk gibi çevrilemeyenler için int()'li satırı try'ın içine alın, except ValueError'da "
                "False return edin.")
    if isinstance(error, IndexError) and name == "iban_valid":
        return " Önce uzunluğa bakın: uzunluk 26 değilse hemen False return edin."
    if isinstance(error, AttributeError) and "'dict' object has no attribute 'add'" in text:
        return " {} boş bir dict'tir; set'i {customer_no} gibi bir item'la (eleman) ya da set() ile kurun."
    if isinstance(error, TypeError) and "unsupported operand" in text and "'dict'" in text and "'set'" in text:
        return " {} boş bir dict'tir; boş bir set set() ile kurulur."
    if isinstance(error, TypeError) and "'int' object is not iterable" in text and name == "branch_report":
        return " Tek item'lı bir set {customer_no} diye kurulur; set(customer_no) bir int'te (tam sayı) hata verir."
    if isinstance(error, AttributeError) and "'Card' object" in text:
        return " __init__'te self.card_id, self.limit ve self.debt attribute'larını (özellik) kurun."
    if isinstance(error, TypeError) and "NoneType" in text and name in ("balances", "category_totals", "login"):
        return " Key dict'te yoksa dict.get(key) None verir; 0'dan başlamak için dict.get(key, 0) yazın."
    if isinstance(error, ZeroDivisionError) and name == "my_report":
        return " Raporunuz boş bir list'le de çalışmalı: bölmeden önce bölenin 0 olmadığına bakın."
    if isinstance(error, ZeroDivisionError) and name == "months_to_goal":
        return (" monthly_rate 0 da olabilir: birikimi ay ay toplayan bir while loop'u (döngü) yazın, "
                "monthly_rate'e bölmeyin.")
    if "NoneType" in text:
        return (" Bu satırda kullandığınız bir değer None: çağırdığınız bir function henüz bir şey return etmiyor "
                "olabilir.")
    if isinstance(error, RecursionError):
        return " Function kendini çağırıyor olabilir."
    if isinstance(error, EOFError):
        return " input() kullanmayın: function'ın ihtiyacı olan her şey parameter'larıyla (parametre) geliyor."
    if isinstance(error, SystemExit):
        return " exit() çağırmayın; function sonucunu return etsin."
    if isinstance(error, TypeError) and "append() takes exactly one argument" in text:
        return (" append() tek bir item alır: tuple eklerken iki kat parantez yazın, "
                "lines.append((date, merchant, amount)) gibi.")
    if isinstance(error, TypeError) and "positional argument" in text:
        return (" def satırını, parameter'larıyla birlikte, olduğu gibi bırakın; app.py ve kontrol.py onlarla "
                "çağırıyor.")
    return ""


# Bu function'larda tuple'ın alanları parameter'larla aynı adı taşıyor: for satırına docstring'deki adlar
# yazılırsa parameter'ın değeri kaybolur. Böyle bir function ✗ alırsa ipucu önce bunu söyler.
SHADOW_FUNCTIONS = ("owner_of", "replay_card", "statement", "category_totals", "places")
OTHER_NAMES = {"card_id": "owner", "iban": "account"}
SHADOW = {"name": ""}   # şu an denenen function, SHADOW_FUNCTIONS'tan biriyse


def and_list(words):
    """["a", "b", "c"] için "a, b ve c"."""
    if len(words) == 1:
        return words[0]
    return ", ".join(words[:-1]) + " ve " + words[-1]


def names_in(target):
    """for satırındaki ya da = işaretinin solundaki adlar, soldan sağa."""
    found = []
    for node in ast.walk(target):
        if isinstance(node, ast.Name):
            found.append((node.lineno, node.col_offset, node.id))
    found.sort()
    return [name for line, column, name in found]


def reused_note(names, inner):
    """names yeniden kullanılmış; inner True ise iç içe iki for'da, değilse parameter'larda."""
    others = [OTHER_NAMES[name] for name in names if name in OTHER_NAMES]
    example = f" (örneğin {and_list(others)})" if others else ""
    if not inner and len(names) == 1:
        return (f"for satırında {names[0]} adını yeniden kullanmışsınız: parameter'ın değeri kayboldu; for "
                f"satırında başka bir ad seçin{example}.")
    if not inner:
        return (f"for satırında {and_list(names)} adlarını yeniden kullanmışsınız: parameter'ların değerleri "
                f"kayboldu; for satırında başka adlar seçin{example}.")
    if len(names) == 1:
        return (f"İçteki for satırında {names[0]} adını yeniden kullanmışsınız: dıştaki loop'ta ona verilen değer "
                f"kayboldu; içteki for satırında başka bir ad seçin{example}.")
    return (f"İçteki for satırında {and_list(names)} adlarını yeniden kullanmışsınız: dıştaki loop'ta onlara "
            f"verilen değerler kayboldu; içteki for satırında başka adlar seçin{example}.")


def shadow_note(name):
    """name function'ında bir for satırı bir parameter'ın ya da dıştaki for'un bir adını yeniden kullanıyorsa
    bunu söyleyen cümle; yoksa boş str."""
    if name not in SHADOW_FUNCTIONS:
        return ""
    try:
        with open(ENGINE, encoding="utf-8", errors="replace") as f:
            tree = ast.parse(f.read())
    except (OSError, SyntaxError, ValueError):
        return ""
    for func in tree.body:
        if not isinstance(func, ast.FunctionDef) or func.name != name:
            continue
        params = []
        for arg in func.args.posonlyargs + func.args.args + func.args.kwonlyargs:
            params.append(arg.arg)
        loops = []
        for node in ast.walk(func):
            if isinstance(node, ast.For):
                loops.append((node.lineno, node.col_offset, len(loops), node))
        loops.sort()
        for line, column, number, loop in loops:
            reused = [found for found in names_in(loop.target) if found in params]
            if reused:
                return reused_note(reused, False)
        for line, column, number, loop in loops:
            outer = names_in(loop.target)
            for statement in loop.body:
                if isinstance(statement, ast.Assign):
                    for target in statement.targets:
                        outer += names_in(target)
            for statement in loop.body:
                for inner in ast.walk(statement):
                    if isinstance(inner, ast.For):
                        reused = [found for found in names_in(inner.target) if found in outer]
                        if reused:
                            return reused_note(reused, True)
    return ""


def shadow_checked(name, check, *args):
    """check'i çalıştırır. name ✗ alırsa ve for satırında bir ad yeniden kullanılmışsa ipucu bunu da söyler."""
    SHADOW["name"] = name
    try:
        check(*args)
    except Problem as p:
        note = shadow_note(name)
        if note and note not in str(p):
            raise Problem(f"{sentence(str(p))} {note}") from None
        raise
    finally:
        SHADOW["name"] = ""


def run(name, func, args, label=None, allow_none=False):
    """func'ı çağırır, ekrana yazdıklarını yakalar. (dönen değer, yazdırdıkları) döndürür."""
    shown = label if label is not None else ", ".join(short(a, 40) for a in args)
    out = io.StringIO()
    try:
        with contextlib.redirect_stdout(out):
            result = func(*args)
    except DataFile as e:
        line = bank_line(e)
        where = f" (bank.py, {line}. satır)" if line else ""
        raise Problem(f"{name}, kendisine verilen file'ı değil, data klasöründeki {e} file'ını açıyor{where}. "
                      "open()'a file'ın adını elle yazmayın, function'a verilen file_name'i verin: kontrol.py "
                      "function'ı kendi deneme file'ıyla çağırıyor.") from None
    except (Exception, SystemExit) as e:
        last = traceback.format_exception_only(type(e), e)[-1].strip()
        line = bank_line(e)
        where = f" (bank.py, {line}. satır)" if line else ""
        raise Problem(f"{name}({shown}) hata verdi{where}: {sentence(last)}{error_hint(name, e)}") from None
    if result is None and not allow_none:
        if out.getvalue().strip():
            raise Problem(f"{name} None return ediyor; sonucu ekrana yazdırıyor ama return etmiyor. print, "
                          "return'ün yerini tutmaz: function'ın sonuna bir return satırı yazın.")
        raise Problem(f"{name} None return ediyor. Henüz kod yazmadıysanız # TODO'nun yerine yazın; yazdıysanız "
                      "function'ın sonunda return satırı var mı, bakın. print, return'ün yerini tutmaz.")
    return result, out.getvalue()


def bank_module():
    import bank
    return bank


def call(name, *args, label=None, allow_none=False):
    """bank'taki function'ı çağırır. (dönen değer, yazdırdıkları) döndürür."""
    func = getattr(bank_module(), name, None)
    if not callable(func):
        raise Problem(f"bank.py'de {name} adında bir function yok. def satırının adını değiştirmeyin.")
    return run(name, func, args, label, allow_none)


FAILED = object()   # quiet()'in "çağrılamadı ya da hata verdi" sonucu


def quiet(name, *args):
    """bank'taki function'ı sessizce çağırır; yoksa ya da hata verirse FAILED döner."""
    func = getattr(bank_module(), name, None)
    if not callable(func):
        return FAILED
    try:
        with contextlib.redirect_stdout(io.StringIO()):
            return func(*args)
    except Exception:
        return FAILED


def check_rules(*names):
    """bank.py'nin başındaki kuralların değişmediğine bakar."""
    bank = bank_module()
    for name in names:
        have = getattr(bank, name, None)
        if not equal(have, RULES[name]):
            raise Problem(f"bank.py'nin başındaki kurallardan {name} {short(RULES[name])} olmalı, sizinki: "
                          f"{short(have)}. Bu değerleri değiştirmeyin; uygulama ve kontrol.py onlarla hesaplıyor.")


def write_file(path, text):
    with open(path, "w", encoding="utf-8") as f:
        f.write(text)


def read_file(path):
    if not os.path.exists(path):
        return ""
    with open(path, encoding="utf-8", errors="replace") as f:
        return f.read()


def csv_line(fields):
    text = ""
    for field in fields:
        if text != "":
            text += ","
        text += str(field)
    return text + "\n"


def garbled(text):
    """utf-8 bir metin başka bir encoding'le okunmuş gibi mi duruyor?"""
    for mark in ("Ã", "Ä", "Å", "�"):
        if mark in text:
            return True
    return False


def check_tuple(got, size, name, what):
    """got size item'lı bir tuple mı? Değilse bunu söyler."""
    if type(got) is not tuple or len(got) != size:
        raise Problem(f"{name} bir {what} tuple'ı return etmeli, sizinki: {short(got)}")


def check_rows(got, size, name, what, kind=list):
    """got, size item'lı tuple'ların list'i mi? Değilse bunu söyler."""
    if type(got) is not kind:
        raise Problem(f"{name} bir {kind.__name__} return etmeli, sizinki: {type_name(got)} {short(got)}")
    for row in got:
        if type(row) is not tuple or len(row) != size:
            raise Problem(f"{name}: list'teki her item bir {what} tuple'ı olmalı, sizinki: {short(row)}")


def require(ok, text):
    """Bir function başka bir görevin function'ını kullanıyorsa, o çalışmadan önce bunu söyler."""
    if not ok:
        raise Problem(text)


# 1. Kayıtlar ve şubeler

def is_color(value):
    if not isinstance(value, str) or len(value) != 7 or value[0] != "#":
        return False
    for ch in value[1:]:
        if ch not in "0123456789abcdefABCDEF":
            return False
    return True


def check_name_and_color():
    bank = bank_module()
    name = getattr(bank, "BANK_NAME", None)
    if not isinstance(name, str) or name.strip() == "":
        raise Problem("BANK_NAME bankanızın adı, boş olmayan bir str olmalı: BANK_NAME = \"...\" satırına kendi "
                      f"bankanızın adını yazın. Sizinki: {short(name)}")
    if name.strip() == "Örnek Bank":
        raise Problem("BANK_NAME henüz \"Örnek Bank\". BANK_NAME = \"...\" satırına kendi bankanızın adını yazın; "
                      "uygulamanın başlığında bu ad görünür.")
    color = getattr(bank, "BANK_COLOR", None)
    if not is_color(color):
        raise Problem("BANK_COLOR \"#0e7490\" gibi, # ve altı haneyle yazılmalı; haneler 0-9 rakamları ve a-f "
                      f"harfleri. Sizinki: {short(color)}")
    if color.lower() == "#2f5d8a":
        raise Problem("BANK_COLOR henüz Örnek Bank'ın rengi: kendi bankanızın rengini yazın.")


BAL_DOC = [("2026-09-01", "NAKIT", "A", 100, "Burs"), ("2026-09-02", "A", "B", 30, "Yemek")]
BAL_IN = [("2026-10-01", "NAKIT", "A", 500, "Burs"), ("2026-10-02", "A", "B", 120, "Kahve"),
          ("2026-10-03", "B", "A", 20, "Borç"), ("2026-10-04", "A", "MASRAF", 5, "EFT masrafı")]
BALANCES_CASES = [(BAL_DOC, "docstring'deki örnek"), (BAL_IN, "dört hareket"), ([], "boş list")]


def check_balances():
    for i, (transactions, label) in enumerate(BALANCES_CASES):
        results = BALANCES_RESULTS[i]
        want = results["want"]
        got, _ = call("balances", list(transactions), label=label)
        if type(got) is not dict:
            raise Problem(f"balances bir dict return etmeli, sizinki: {type_name(got)} {short(got)}")
        if equal(got, want):
            continue
        nonzero = {}
        for key in got:
            if got[key] != 0:
                nonzero[key] = got[key]
        shown = f"balances({label}) beklenen: {short(want)}, sizinki: {short(got)}."
        if len(transactions) > 1 and equal(got, results["first_only"]):
            raise Problem(f"{shown} Yalnız ilk hareket uygulanmış: return satırı loop'un içinde kalmış. return'ü "
                          "for'un dışına, function'ın sonuna alın.")
        if equal(got, results["flipped"]):
            raise Problem(f"{shown} İşaretler ters: her hareket gönderenin bakiyesinden düşer, alıcının bakiyesine "
                          "eklenir.")
        if equal(nonzero, results["receivers_only"]):
            raise Problem(f"{shown} Her hareket gönderenin bakiyesinden de düşmeli: "
                          "money[sender] = money.get(sender, 0) - amount.")
        if equal(got, results["overwritten"]):
            raise Problem(f"{shown} Bakiyeyi her harekette baştan yazmayın, önceki bakiyenin üstüne ekleyin: "
                          "dict[receiver] = dict.get(receiver, 0) + amount.")
        raise Problem(shown)


HIST_DOC = [("2026-09-01", "NAKIT", "A", 100, "Burs"), ("2026-09-02", "A", "B", 30, "Yemek"),
            ("2026-09-03", "C", "D", 5, "Çay")]
HIST_IN = [("2026-10-01", "NAKIT", A, 2000, "Burs"), ("2026-10-02", A, B, 150, "Kahve"),
           ("2026-10-03", B, D, 70, "Yemek"), ("2026-10-04", A, "KART-4821", 300, "Kart ödemesi"),
           ("2026-10-05", B, A, 200, "Kira payı"), ("2026-10-06", A, "MASRAF", 2, "Şubeler arası havale masrafı")]
HISTORY_CASES = [(HIST_DOC, "A", "docstring'deki örnek"), (HIST_IN, A, "altı hareket"), (HIST_IN, X, "altı hareket")]


def check_account_history():
    for i, (transactions, iban, label) in enumerate(HISTORY_CASES):
        results = HISTORY_RESULTS[i]
        want = results["want"]
        got, _ = call("account_history", list(transactions), iban, label=f"{label}, {iban!r}")
        if equal(got, want):
            continue
        check_rows(got, 4, "account_history", "(date, other, amount, description)")
        hint = ""
        if len(want) > 1 and got == want[-1:]:
            hint = ("Yalnız ilk hareket girmiş: return satırı loop'un içinde kalmış. return'ü for'un dışına, "
                    "function'ın sonuna alın.")
        elif got == results["oldest_first"]:
            hint = "En yeni hareket en başta olmalı: append() yerine insert(0, ...) ile list'in başına ekleyin."
        elif got in (results["unsigned"], results["unsigned_oldest_first"]):
            hint = "Hesaptan çıkan para eksi işaretli olmalı: hesap gönderense amount yerine 0 - amount yazın."
        elif got == results["flipped"]:
            hint = "İşaretler ters: hesaba giren para artı, hesaptan çıkan para eksi olur."
        elif len(got) > len(want):
            hint = "iban'ın gönderen ya da alıcı olmadığı hareketler girmez."
        else:
            for row in got:
                if row[1] == iban:
                    hint = "other karşı taraftır: hesap gönderense receiver, alıcıysa sender; iban'ın kendisi değil."
        raise Problem(with_hint(f"account_history({label}, {iban!r}) beklenen: {short(want, 200)}, sizinki: "
                                f"{short(got, 200)}.", hint))


OWNER_ACCOUNTS = [(A, 1001, "TL"), (C, 1001, "USD"), (B, 1002, "TL"), (A2, 1003, "TL")]


def check_owner_of():
    cases = [(A, 1001, "list'teki ilk hesap"), (B, 1002, "list'teki üçüncü hesap"), (A2, 1003, "list'teki son hesap"),
             (C, 1001, "bir USD hesabı")]
    for i, (iban, want, label) in enumerate(cases):
        got, _ = call("owner_of", list(OWNER_ACCOUNTS), iban, label=f"dört hesap, {iban!r}", allow_none=i > 0)
        if equal(got, want):
            continue
        shown = f"owner_of(dört hesap, {iban!r}) {want} return etmeli, sizinki: {short(got)}; bu IBAN {label}."
        hint = ""
        if got is None:
            hint = ("Loop ilk hesapta bitiyor olabilir: return None'ı for'un dışına, function'ın sonuna alın; "
                    "bütün hesaplara baktıktan sonra None return edin.")
        elif type(got) is tuple or got in (iban, "TL", "USD"):
            hint = "Hesabın tuple'ını ya da IBAN'ını değil, sahibinin müşteri numarasını return edin: customer_no."
        elif got == str(want):
            hint = "Müşteri numarası int olarak return edilmeli; accounts'taki gibi."
        raise Problem(with_hint(shown, hint))
    for iban, accounts, label in [(X, OWNER_ACCOUNTS, "dört hesap"), (GHOST, OWNER_ACCOUNTS, "dört hesap"),
                                  (A, [], "boş list")]:
        got, _ = call("owner_of", list(accounts), iban, label=f"{label}, {iban!r}", allow_none=True)
        if got is None:
            continue
        raise Problem(f"owner_of({label}, {iban!r}): bu IBAN'la bir hesap yok, None return etmeli; sizinki: "
                      f"{short(got)}. Bulamayınca {short(got)} değil None return edin: for loop'u bitince "
                      "return None. Çağıran sonucu \"is None\" ile soruyor.")


BR_DOC_ACCOUNTS = [(A, 1001, "TL"), (C, 1001, "USD"), (B, 1002, "TL"), (A2, 1003, "TL")]
BR_DOC_MONEY = {A: 300, C: 50, B: 900, A2: 100}
BR_ACCOUNTS = [(A, 1001, "TL"), (C, 1001, "USD"), (A2, 1003, "TL"), (B, 1002, "TL"), (B_EUR, 1002, "EUR"),
               (D, 1004, "TL"), (D_USD, 1004, "USD"), (E, 1006, "TL"), (H, 1013, "TL"), (H_USD, 1013, "USD"),
               (N, 1014, "TL")]
BR_MONEY = {A: 4000, C: 56, A2: 1500, B: 2500, B_EUR: 30, D: 3200, D_USD: 120, E: 1200, H: 900, H_USD: 15}
BR_TIE_ACCOUNTS = [(A, 1001, "TL"), (B, 1002, "TL"), (D, 1004, "TL")]
BR_TIE_MONEY = {A: 500, B: 500, D: 800}
BRANCH_CASES = [(BR_DOC_ACCOUNTS, BR_DOC_MONEY, "docstring'deki örnek"),
                (BR_ACCOUNTS, BR_MONEY, "üç şubede on bir hesap"),
                (BR_TIE_ACCOUNTS, BR_TIE_MONEY, "toplamı eşit iki şube")]


def check_branch_report():
    for i, (accounts, money, label) in enumerate(BRANCH_CASES):
        results = BRANCH_RESULTS[i]
        want = results["want"]
        got, _ = call("branch_report", list(accounts), dict(money), label=label)
        if equal(got, want):
            continue
        check_rows(got, 3, "branch_report", "(branch, customers, total)")
        hint = ""
        if got and type(got[0][1]) is set:
            hint = "customers, müşteri sayısı; bir int olmalı: set'in kendisini değil, len() ile büyüklüğünü koyun."
        elif got and type(got[0][1]) is int and type(got[0][2]) is int and got[0][2] < 0:
            hint = (f"Toplamı geri çevirin: sort()'tan sonra tuple'daki eksi sayıyı 0'dan çıkarın; 0 - ({got[0][2]}) "
                    f"yeniden {0 - got[0][2]} olur.")
        elif equal(got, results["accounts_counted"]):
            hint = ("Bir müşterinin aynı şubede iki hesabı (TL ve USD gibi) olabilir: müşterileri her şube için bir "
                    "set'te toplayıp len() ile sayın; hesapları değil, müşterileri sayın.")
        elif equal(got, results["all_currencies"]):
            hint = "Toplama yalnız TL hesaplarının bakiyesi girer; USD ve EUR hesapları girmez."
        elif equal(got, results["tl_accounts_only"]):
            hint = ("Müşteri sayısına bütün hesaplar girer: yalnız USD hesabı olan müşteri de o şubenin müşterisi. "
                    "Yalnız toplama TL hesapları girer.")
        elif len(got) == len(want) and sorted(got) == sorted(want) and \
                [row[2] for row in got] == [row[2] for row in want]:
            hint = ("Toplamı eşit şubeler şube koduna göre sıralanır: reverse() kullanmayın; (0 - total, branch, "
                    "müşteri sayısı) tuple'larını sort() edin.")
        elif len(got) == len(want) and sorted(got) == sorted(want):
            hint = ("Toplamı en büyük şube başta olmalı: (0 - total, branch, müşteri sayısı) tuple'larını bir "
                    "list'e koyup sort() edin; 0 - total en büyük toplamı başa getirir.")
        elif got and len(got[0]) == 3 and got[0][0] == want[0][0] and got[0][1] == want[0][2]:
            hint = "Tuple'lar (branch, customers, total) sırasıyla olmalı: şube kodu, müşteri sayısı, toplam."
        raise Problem(with_hint(f"branch_report({label}) beklenen: {short(want, 200)}, sizinki: {short(got, 200)}.",
                                hint))


# Her görev parça parça denenir. Her parça bir tuple'dır: (denediği adlar, deneyen function, ona verilenler).
# Adlar app.py'deki TASK_OF'un adlarıdır; kuralları ve testlerim.py'yi deneyen parçaların adı yok. Görevin
# satırına ilk ✗ alan parçanın notu yazılır; satır, görevin adlarından kaçının geçtiğini de söyler.

def task_1(tmp):
    return [(("BANK_NAME",), check_name_and_color, ()),
            (("balances",), check_balances, ()),
            (("account_history",), check_account_history, ()),
            (("owner_of",), shadow_checked, ("owner_of", check_owner_of)),
            (("branch_report",), check_branch_report, ())]


# 2. Güvenli giriş

SHORT = (False, "Şifre en az 8 karakter olmalı.")
NO_DIGIT = (False, "Şifrede en az bir rakam olmalı.")
NO_LETTER = (False, "Şifrede en az bir harf olmalı.")
COMMA = (False, "Şifrede virgül olmamalı.")
HAS_NAME = (False, "Şifre adınızı içermemeli.")
GOOD = (True, "Şifre uygun.")
RULE_ORDER = [SHORT, NO_DIGIT, NO_LETTER, COMMA, HAS_NAME]
PASSWORDS = [
    ("kedi123", "Zehra", SHORT, ""),
    ("zehra2026", "Zehra", HAS_NAME, "Adı ve şifreyi lower() ile küçük harfe çevirip bakın: name.lower() in "
                                     "password.lower()."),
    ("martı2026", "Zehra", GOOD, ""),
    ("abcdefg1", "Emre", GOOD, "8 karakterlik bir şifre uygundur: şifre len(password) < 8 ise kısa, <= değil."),
    ("abcdefgh", "Emre", NO_DIGIT, "Şifrede en az bir rakam olmalı: karakterlerden biri DIGITS'in içindeyse rakamdır."),
    ("12345678", "Emre", NO_LETTER, ""),
    ("2026!?#*", "Batu", NO_LETTER, "Bir karakter, lower() edilmiş hali LETTERS'ın içindeyse harftir; !, ?, # ve * "
                                    "harf değil."),
    ("1234,678", "Emre", NO_LETTER, ""),
    ("kalem,2026", "Emre", COMMA, ""),
    ("emre,2026x", "Emre", COMMA, ""),
    ("2026EMREx", "Emre", HAS_NAME, "Adı ve şifreyi lower() ile küçük harfe çevirip bakın: name.lower() in "
                                    "password.lower()."),
    ("KALEM2026", "Batu", GOOD, "Büyük harfler de harftir: karakterin lower() edilmiş haline bakın, char.lower() "
                                "in LETTERS."),
    ("çiçek2026", "Batu", GOOD, "ç, ğ, ı, ö, ş ve ü de harftir: karakteri LETTERS'ta arayın."),
]


def check_password_ok():
    for password, name, want, hint in PASSWORDS:
        got, _ = call("password_ok", password, name)
        if equal(got, want):
            continue
        check_tuple(got, 2, "password_ok", "(ok, message)")
        shown = f"password_ok({password!r}, {name!r}) {want!r} return etmeli, sizinki: {short(got, 120)}."
        if got in RULE_ORDER and want in RULE_ORDER and RULE_ORDER.index(got) > RULE_ORDER.index(want):
            hint = ("Kurallar docstring'deki sırayla denenir; ilk uymayan kuralın mesajı döner: uzunluk, rakam, "
                    "harf, virgül, ad.")
        elif type(got[0]) is not bool:
            hint = "ok True ya da False olmalı."
        elif got[0] is want[0] and got[1] != want[1]:
            hint = f"message docstring'deki cümleyle aynı olmalı: {want[1]!r}."
        raise Problem(with_hint(shown, hint))


def expected_hash(password, salt, rounds=1000, salt_first=True):
    """hash_password'ün docstring'indeki formülle beklenen hash'i bulur. register ve change_password rastgele
    bir salt seçtiği için bu hash önceden hesaplanıp beklenen sonuçların tablolarına yazılamıyor."""
    import security
    text = password
    for i in range(rounds):
        if salt_first:
            text = security.sha256(salt + text)
        else:
            text = security.sha256(text + salt)
    return text


PAIRS = [("kedi123", "9f2c41d07ab3e5c8"), ("deniz42", "0a1b2c3d4e5f6789"), ("Gizli şifre 7", "ffffffffffffffff")]


def check_hash_password():
    import security
    for password, salt in PAIRS:
        want = expected_hash(password, salt)
        got, _ = call("hash_password", password, salt)
        if equal(got, want):
            continue
        shown = f"hash_password({password!r}, {salt!r})"
        if type(got) is not str:
            raise Problem(f"{shown} bir str return etmeli: sha256'nın verdiği 64 karakterlik hash. Sizinki: "
                          f"{type_name(got)} {short(got)}")
        if got == expected_hash(password, salt, salt_first=False):
            raise Problem(f"{shown}: salt'ı başa koyun: text = security.sha256(salt + text). Sizinki "
                          "text + salt'ın hash'ini çıkarıyor.")
        if got == security.sha256(salt + password) or got == security.sha256(password + salt):
            raise Problem(f"{shown}: sha256'yı ROUNDS kez, her turda bir önceki turun sonucuna uygulayın: "
                          "text = password ile başlayın, loop'ta text = security.sha256(salt + text). Sizinki "
                          "yalnız bir tur.")
        if got == expected_hash(password, salt, 999) or got == expected_hash(password, salt, 1001):
            raise Problem(f"{shown}: loop tam ROUNDS kez dönmeli: for i in range(ROUNDS). Sizinki bir tur eksik "
                          "ya da fazla.")
        if got == security.sha256(password):
            raise Problem(f"{shown}: yalnız şifrenin hash'i değil; salt'ı ekleyin ve ROUNDS kez dönün: "
                          "text = security.sha256(salt + text).")
        if got == password:
            raise Problem(f"{shown} şifrenin kendisini return ediyor; hash'ini return etmeli.")
        raise Problem(f"{shown} beklenen değerin ilk 16 karakteri: {want[:16]!r}, sizinki: {got[:16]!r}. Formül: "
                      "text = password; ROUNDS kez text = security.sha256(salt + text); return text.")


def check_number(got, want, label, hints):
    if equal(got, want):
        return
    if type(got) is not int:
        raise Problem(f"register yeni müşterinin numarasını int olarak return etmeli; {label} sizinki: "
                      f"{type_name(got)} {short(got)}")
    hint = hints.get(got, "")
    raise Problem(f"register, {label}: yeni numara {want} olmalı, sizinki: {got}.{hint}")


def check_new_customer(customers, number, name, password, path, before, label):
    """register'ın customers'a ve file'a eklediklerine bakar; yeni müşterinin salt'ını döndürür."""
    if number not in customers:
        raise Problem(f"register yeni müşteriyi customers'a eklemedi; {label} customers[{number}] = (name, salt, "
                      "hash) olmalı.")
    entry = customers[number]
    if type(entry) is not tuple or len(entry) != 3:
        raise Problem(f"customers'taki value (değer) bir (name, salt, hash) tuple'ı olmalı, sizinki: {short(entry)}")
    have_name, salt, hashed = entry
    if have_name != name:
        raise Problem(f"customers[{number}] (name, salt, hash) sırasıyla olmalı; ilk item ad, {name!r}. Sizinki: "
                      f"{short(entry)}")
    if type(salt) is not str or salt == "":
        raise Problem(f"salt security.make_salt()'ın verdiği str olmalı; customers[{number}]'teki sizinki: "
                      f"{short(salt)}")
    if hashed == password:
        raise Problem("register şifrenin kendisini saklıyor; yalnız hash'ini saklayın: hash_password(password, "
                      "salt).")
    if hashed != expected_hash(password, salt):
        raise Problem(f"customers[{number}]'teki hash, hash_password({password!r}, salt) olmalı; salt da "
                      "security.make_salt()'tan gelen ve aynı tuple'a yazdığınız salt.")
    text = read_file(path)
    if text == before:
        raise Problem("register file'a satır eklemedi: file_name'i \"a\" moduyla açıp sonuna yeni müşterinin "
                      "satırını yazın.")
    if not text.startswith(before):
        raise Problem("register file'daki eski satırları sildi: file'ı \"w\" ile değil, \"a\" moduyla açın; \"a\" "
                      "yeni satırı sona ekler.")
    added = text[len(before):]
    if password in added:
        raise Problem("Şifrenin kendisi file'a yazılmamalı; satırda yalnız numara, ad, salt ve hash olsun.")
    line = f"{number},{name},{salt},{hashed}\n"
    if added == line.rstrip("\n"):
        raise Problem("register satırı \\n ile bitirmeli; yoksa sonraki müşteri aynı satıra yazılır.")
    if added.startswith(CUSTOMERS_HEADER):
        raise Problem("register yalnız yeni müşterinin satırını eklemeli; başlığı yeniden yazmayın.")
    if added != line:
        if garbled(added):
            raise Problem("Türkçe harfler bozuk yazılmış: file'ı open(file_name, \"a\", encoding=\"utf-8\") ile "
                          f"açın. Eklenen satır: {added!r}")
        raise Problem(f"register'ın eklediği satır beklenen: {line!r}, sizinki: {added!r}. Alanları virgülle, "
                      "aralarına boşluk koymadan yazın; salt ve hash, customers'a eklediklerinizle aynı olmalı.")
    return salt


def check_register(tmp):
    s1, s2 = "9f2c41d07ab3e5c8", "0a1b2c3d4e5f6789"
    h1, h2 = expected_hash("kedi123", s1), expected_hash("deniz42", s2)
    path = os.path.join(tmp, "customers.csv")
    before = f"{CUSTOMERS_HEADER}\n1001,Zehra,{s1},{h1}\n1005,İrem,{s2},{h2}\n"
    write_file(path, before)
    customers = {1001: ("Zehra", s1, h1), 1005: ("İrem", s2, h2)}
    label = "1001 ve 1005 numaralı iki müşteri varken"
    got, _ = call("register", customers, "Nur", "yildiz64", path, label=f"{label}, \"Nur\", \"yildiz64\"")
    count_hint = (" Yeni numara müşteri sayısından değil, en büyük müşteri numarasından bulunur: 1005'in bir "
                  "fazlası.")
    check_number(got, 1006, label, {1003: count_hint, 1002: count_hint,
                                    1005: " En büyük numarayı bulduktan sonra bir ekleyin."})
    salt = check_new_customer(customers, 1006, "Nur", "yildiz64", path, before, label)
    before = read_file(path)
    label = "1006'dan sonra"
    got, _ = call("register", customers, "Büşra", "lale88", path, label=f"{label}, \"Büşra\", \"lale88\"")
    check_number(got, 1007, label, {})
    salt_2 = check_new_customer(customers, 1007, "Büşra", "lale88", path, before, label)
    if salt_2 == salt:
        raise Problem("İki yeni müşterinin salt'ı aynı çıktı: her müşteri için salt = security.make_salt() ile yeni "
                      "bir salt alın.")
    empty = os.path.join(tmp, "empty.csv")
    before = CUSTOMERS_HEADER + "\n"
    write_file(empty, before)
    label = "hiç müşteri yokken"
    fresh = {}
    got, _ = call("register", fresh, "Ali", "deniz42", empty, label=f"{label}, \"Ali\", \"deniz42\"")
    start_hint = " Hiç müşteri yoksa yeni numara 1001: variable'ı 1000'den başlatıp sonunda bir ekleyin."
    check_number(got, 1001, label, {1: start_hint, 0: start_hint, 1000: start_hint})
    check_new_customer(fresh, 1001, "Ali", "deniz42", empty, before, label)
    mixed = os.path.join(tmp, "mixed.csv")
    before = f"{CUSTOMERS_HEADER}\n1009,Batu,{s1},{h1}\n1003,Emre,{s2},{h2}\n"
    write_file(mixed, before)
    label = "1009 ve 1003 numaralı iki müşteri, bu sırayla, varken"
    got, _ = call("register", {1009: ("Batu", s1, h1), 1003: ("Emre", s2, h2)}, "Raşit", "fener19", mixed,
                  label=f"{label}, \"Raşit\", \"fener19\"")
    check_number(got, 1010, label, {1004: " Key'ler sırayla gelmeyebilir: her key'e bakıp en büyüğünü bulun; son "
                                          "key'in bir fazlası değil."})


def check_login():
    s1, s2 = "9f2c41d07ab3e5c8", "0a1b2c3d4e5f6789"
    customers = {1001: ("Zehra", s1, expected_hash("kedi123", s1)), 1002: ("Eren", s2, expected_hash("deniz42", s2))}
    failed = {}
    wrong_password = ("Girilen şifrenin hash'ini müşterinin kendi salt'ıyla çıkarıp saklanan hash'le karşılaştırın: "
                      "name, salt, stored = customers[customer_no]; hash_password(password, salt) == stored.")
    steps = [
        (1001, "kedi123", "ok", "1001 doğru şifreyle girerken", {"wrong": wrong_password}),
        (1002, "deniz", "wrong", "1002 yanlış şifreyle girerken", {}),
        (UNKNOWN_NO, "kedi123", "unknown", f"customers'ta olmayan {UNKNOWN_NO} ile girerken",
         {"wrong": "customers'ta olmayan numarada \"unknown\" return edin."}),
        (1002, "deniz42", "ok", "1002 bir yanlış denemeden sonra doğru şifreyle girerken", {}),
        (1002, "deniz", "wrong", "1002 yanlış şifreyle girerken", {}),
        (1002, "deniz4", "wrong", "1002 üst üste ikinci yanlış denemede", {}),
        (1002, "Deniz42", "locked", "1002 üst üste üçüncü yanlış denemede",
         {"wrong": "Üçüncü yanlış denemede sayı 3 olur; login o denemede \"locked\" return etmeli."}),
        (1002, "deniz42", "locked", "1002 kilitlendikten sonra doğru şifreyle girerken",
         {"ok": "Kilitli hesaba doğru şifreyle de girilmemeli: şifreye bakmadan önce failed'daki sayı 3 mü, "
                "bakın."}),
        (1001, "kedi123", "ok", "1002 kilitliyken 1001 doğru şifreyle girerken",
         {"locked": "Kilit yalnız o müşterinin: failed'da her müşterinin kendi sayısı var, failed[customer_no]."}),
    ]
    counts = [0, 1, 1, 0, 1, 2, 3, 3, 3]
    for (number, password, want, situation, hints), count in zip(steps, counts):
        label = f"customers, failed, {number}, {password!r}"
        got, _ = call("login", customers, failed, number, password, label=label)
        if got != want or type(got) is not str:
            if got not in ("ok", "wrong", "locked", "unknown"):
                raise Problem(f"login \"ok\", \"wrong\", \"locked\" ya da \"unknown\" return etmeli; {situation} "
                              f"sizinki: {short(got)}")
            raise Problem(with_hint(f"login, {situation}: {want!r} return etmeli, sizinki: {got!r}.",
                                    hints.get(got, "")))
        if number == UNKNOWN_NO and UNKNOWN_NO in failed:
            raise Problem(f"customers'ta olmayan bir numarada failed'a dokunmayın; {UNKNOWN_NO} failed'a eklenmiş. "
                          "Numara yoksa hemen \"unknown\" return edin.")
        have = failed.get(1002, 0)
        if number == 1002 and want == "wrong" and have != count:
            raise Problem(f"login, {situation}: failed'da 1002'nin sayısı {count} olmalı, sizinki: {short(have)}. "
                          "Yanlış denemede sayıyı bir artırın: failed[customer_no] = failed.get(customer_no, 0) + 1.")
        if number == 1002 and want == "ok" and have != 0:
            raise Problem(f"login, {situation}: failed'da 1002'nin sayısı 0 olmalı, sizinki: {short(have)}. Doğru "
                          "girişte sayıyı 0 yapın: failed[customer_no] = 0. Kilit üst üste yanlış denemeler için.")


def customers_text(customers):
    text = CUSTOMERS_HEADER + "\n"
    for number in customers:
        name, salt, hashed = customers[number]
        text += f"{number},{name},{salt},{hashed}\n"
    return text


def check_change_password(tmp):
    s1, s2, s3 = "9f2c41d07ab3e5c8", "0a1b2c3d4e5f6789", "ffffffffffffffff"
    customers = {1001: ("Zehra", s1, expected_hash("kedi123", s1)), 1002: ("Eren", s2, expected_hash("deniz42", s2)),
                 1003: ("Emre", s3, expected_hash("kalem7", s3))}
    path = os.path.join(tmp, "musteriler.csv")
    old_text = customers_text(customers)
    write_file(path, old_text)
    saved = dict(customers)
    label = "customers, 1002, \"deniz\", \"deniz2026\", file"
    got, _ = call("change_password", customers, 1002, "deniz", "deniz2026", path, label=label, allow_none=True)
    if got is not False:
        if got is True:
            raise Problem("change_password eski şifre yanlışken False return etmeli, sizinki True: eski şifrenin "
                          "hash'ini müşterinin salt'ıyla çıkarın; saklanan hash'e eşit değilse hemen False return "
                          "edin.")
        raise Problem(f"change_password True ya da False return etmeli; eski şifre yanlışken sizinki: {short(got)}")
    if customers != saved or read_file(path) != old_text:
        raise Problem("change_password eski şifre yanlışken customers'a da file'a da dokunmamalı; önce eski şifreye "
                      "bakın, yanlışsa hemen False return edin.")
    label = "customers, 1002, \"deniz42\", \"deniz2026\", file"
    got, _ = call("change_password", customers, 1002, "deniz42", "deniz2026", path, label=label)
    if got is not True:
        if got is False:
            raise Problem("change_password eski şifre doğruyken True return etmeli, sizinki False: eski şifrenin "
                          "hash'ini müşterinin kendi salt'ıyla çıkarıp saklanan hash'le karşılaştırın, login'deki "
                          "gibi.")
        raise Problem(f"change_password True ya da False return etmeli; eski şifre doğruyken sizinki: {short(got)}")
    for number in (1001, 1003):
        if customers.get(number) != saved[number]:
            raise Problem(f"change_password yalnız şifresi değişen müşterinin tuple'ını değiştirmeli; {number} "
                          "numaralı müşterininki de değişti.")
    entry = customers.get(1002)
    if entry == saved[1002]:
        raise Problem("change_password customers'ı değiştirmedi: customers[customer_no] = (ad, yeni salt, yeni "
                      "hash) yazın.")
    if type(entry) is not tuple or len(entry) != 3:
        raise Problem(f"customers'taki value bir (name, salt, hash) tuple'ı olmalı, sizinki: {short(entry)}")
    name, salt, hashed = entry
    if name != "Eren":
        raise Problem(f"customers[1002] (name, salt, hash) sırasıyla olmalı; ilk item ad, 'Eren'. Sizinki: "
                      f"{short(entry)}")
    if salt == s2:
        raise Problem("Şifre değişince salt da yenilenmeli: new_salt = security.make_salt() ile yeni bir salt alın, "
                      "yeni şifrenin hash'ini onunla çıkarın.")
    if type(salt) is not str or salt == "":
        raise Problem(f"salt security.make_salt()'ın verdiği str olmalı; sizinki: {short(salt)}")
    if hashed == "deniz2026":
        raise Problem("change_password yeni şifrenin kendisini saklıyor; yalnız hash'ini saklayın.")
    if hashed == expected_hash("deniz42", salt):
        raise Problem("customers'a eski şifrenin hash'i yazılmış: yeni şifrenin (new_password) hash'ini çıkarın.")
    if hashed != expected_hash("deniz2026", salt):
        raise Problem("customers[1002]'deki hash, hash_password(new_password, new_salt) olmalı; new_salt da aynı "
                      "tuple'a yazdığınız yeni salt.")
    want = customers_text(customers)
    text = read_file(path)
    if text == want:
        return
    lines = text.splitlines(True)
    want_lines = want.splitlines(True)
    if "deniz2026" in text:
        raise Problem("Şifrenin kendisi file'a yazılmamalı; satırlarda yalnız numara, ad, salt ve hash olsun.")
    if text == old_text:
        raise Problem("change_password file'ı yeniden yazmadı: file_name'i \"w\" moduyla açıp önce başlık satırını, "
                      "sonra customers'taki her müşteri için bir satır yazın.")
    if text.startswith(old_text):
        raise Problem("change_password eski satırları silmedi: file'ı \"a\" ile değil, \"w\" moduyla açın; \"w\" "
                      "file'ı baştan yazar.")
    if text == want.replace("\n", "") or text == want.rstrip("\n") or len(lines) < len(want_lines) and \
            text.replace("\n", "") == want.replace("\n", ""):
        raise Problem("change_password her satırı \\n ile bitirmeli; yoksa satırlar birbirine karışır.")
    if not lines or lines[0] != want_lines[0]:
        raise Problem("change_password önce başlık satırını yazmalı: customer_no,name,salt,password_hash ve \\n. "
                      f"Sizin file'ınızın ilk satırı: {short(lines[0] if lines else '', 80)}")
    if len(lines) < len(want_lines):
        raise Problem(f"File'da {len(want_lines) - 1} müşteri olmalı, sizinkinde {len(lines) - 1} var: \"w\" "
                      "file'ı baştan yazar, eski satırların hepsi silinir; başlıktan sonra customers'taki her müşteri "
                      "için bir satır yazın, yalnız değişeni değil.")
    if len(lines) == len(want_lines) and sorted(lines[1:]) == sorted(want_lines[1:]):
        return
    if garbled(text):
        raise Problem("Türkçe harfler bozuk yazılmış: file'ı open(file_name, \"w\", encoding=\"utf-8\") ile açın.")
    raise Problem(f"change_password'ün yazdığı file beklenen: {short(want, 200)}, sizinki: {short(text, 200)}. "
                  "Her müşteri için numara,ad,salt,hash satırı; alanlar virgülle, aralarında boşluk yok.")


def task_2(tmp):
    return [((), check_rules, ("ROUNDS", "DIGITS", "LETTERS")),
            (("password_ok",), check_password_ok, ()),
            (("hash_password",), check_hash_password, ()),
            (("register",), check_register, (tmp,)),
            (("login",), check_login, ()),
            (("change_password",), check_change_password, (tmp,))]


# 3. Para gönderme ve talimatlar

IBAN_FORMULA = ("Formül: ilk dört karakteri sona taşıyın, iban[4:] + iban[:4]; rakamlar olduğu gibi kalır, harfler "
                "ord(char) - ord(\"A\") + 10 ile sayıya çevrilir (T 29, R 27; \"TR\" \"2927\" olur); çıkan str "
                "int()'e çevrilir ve 97'ye bölümünden kalan 1'se True.")
IBAN_VALID = [
    (A, "docstring'deki örnek"),
    (X, "başka bir bankanın geçerli bir IBAN'ı"),
    (E, "kontrol haneleri 02 olan geçerli bir IBAN"),
    (LETTERED, "hesap numarasında harf olan geçerli bir IBAN"),
]
IBAN_INVALID = [
    (one_digit_off(A), "Bir rakamı yanlış yazılmış.", IBAN_FORMULA),
    (make_iban("12345", "010110010000001"), "Uzunluğu 25 karakter.",
     "Uzunluk 26 değilse False return edin: if len(iban) != 26."),
    (make_iban("12345", "01011001000000011"), "Uzunluğu 27 karakter.",
     "Uzunluk 26 değilse False return edin: if len(iban) != 26."),
    ("", "Boş str.", "Uzunluk 26 değilse False return edin: if len(iban) != 26."),
    (NOT_TR, "TR ile başlamıyor; kontrol haneleri başka bir ülkeninki gibi doğru.",
     "İlk iki karakter \"TR\" değilse False return edin: iban[:2] != \"TR\"."),
    (A[:12] + "-" + A[13:], "İçinde rakam yerine bir \"-\" var.",
     "\"-\" sayıya çevrilemez: int() ValueError verir; except ValueError'da False return edin."),
    (A[:16] + " " + A[17:], "İçinde rakam yerine bir boşluk var.",
     "Boşluk sayıya çevrilemez: int() ValueError verir; except ValueError'da False return edin."),
    (LETTERED[:12] + "C" + LETTERED[13:], "Hesap numarasındaki bir harf değiştirilmiş.", IBAN_FORMULA),
]


def check_iban_valid():
    for i, (iban, label) in enumerate(IBAN_VALID):
        got, _ = call("iban_valid", iban, allow_none=i > 0)
        if got is True:
            continue
        if got is False:
            hint = IBAN_FORMULA
            if iban == LETTERED:
                hint = ("Hesap numarasında harf olabilir: harfleri de ord(char) - ord(\"A\") + 10 ile sayıya çevirin, "
                        "yalnız \"TR\"yi değil. " + IBAN_FORMULA)
            raise Problem(f"iban_valid({iban!r}) True return etmeli, sizinki False; bu {label}. {hint}")
        raise Problem(f"iban_valid True ya da False return etmeli; geçerli {iban!r} için sizinki: {short(got)}")
    for iban, situation, hint in IBAN_INVALID:
        got, _ = call("iban_valid", iban, allow_none=True)
        if got is False:
            continue
        if got is True:
            raise Problem(f"iban_valid({iban!r}) False return etmeli, sizinki True. {situation} {hint}")
        raise Problem(f"iban_valid({iban!r}) False return etmeli, sizinki: {short(got)}. Her durumda True ya da "
                      "False return edin.")


MASK_CASES = [B, A, X]


def check_mask_iban():
    for i, iban in enumerate(MASK_CASES):
        want = MASK_RESULTS[i]["want"]
        got, _ = call("mask_iban", iban)
        if equal(got, want):
            continue
        shown = f"mask_iban({iban!r}) {want!r} return etmeli, sizinki: {short(got)}."
        hint = ""
        if type(got) is not str:
            hint = "Yıldızlı IBAN bir str olmalı."
        elif got == iban:
            hint = "IBAN'ın kendisini değil, yıldızlı halini return edin."
        elif got[:4] != iban[:4]:
            hint = "İlk dört karakter iban[:4]."
        elif got.count("*") == 18 and got[-4:] != iban[-4:]:
            hint = "Son dört karakter eksi index'le (indis) dilimlenir: iban[-4:]."
        else:
            hint = "Aradaki 18 karakterin yerine \"*\" * 18 gelir; sonuç da 26 karakter olur."
        raise Problem(with_hint(shown, hint))


ALIASES = {"zehra@ornek.test": A, "eren@ornek.test": B}
RESOLVE = [
    (" Zehra@ornek.test ", A, "Önce strip() ile baştaki ve sondaki boşlukları silin, sonra lower() edilmiş halini "
                              "aliases'ta arayın."),
    ("eren@ornek.test", B, "text aliases'ta bir key'se o key'in value'sunu, yani bağlı olduğu IBAN'ı return edin."),
    ("EREN@ORNEK.TEST", B, "aliases'ın key'leri küçük harfli: text.lower() aliases'ta mı, ona bakın."),
    ("tr12 1234 5001 0210 0200 0000 01", B, "text bir IBAN'sa boşluklarını replace(\" \", \"\") ile silip upper() "
                                            "ile büyük harfe çevirin."),
    ("  TR57 1234 5001 0110 0100 0000 01  ", A, "Baştaki ve sondaki boşlukları strip(), aradakileri "
                                                "replace(\" \", \"\") siler."),
    ("batu@ornek.test", "BATU@ORNEK.TEST", "Kolay Adres aliases'ta yoksa text bir IBAN sayılır: boşluklarını silip "
                                           "upper() ile return edin; geçersiz bir IBAN olduğu için uygulama ona para "
                                           "göndermez."),
]


def check_resolve_receiver():
    for i, (text, want, hint) in enumerate(RESOLVE):
        got, _ = call("resolve_receiver", dict(ALIASES), text, label=f"iki Kolay Adres, {text!r}", allow_none=i > 0)
        if equal(got, want):
            continue
        if got is None:
            hint = f"resolve_receiver her durumda bir str return etmeli. {hint}"
        elif type(got) is not str:
            hint = f"resolve_receiver bir str return etmeli. {hint}"
        elif got in ALIASES:
            hint = "Key'i değil, value'yu return edin: aliases[text.lower()]."
        raise Problem(with_hint(f"resolve_receiver(iki Kolay Adres, {text!r}) {want!r} return etmeli, sizinki: "
                                f"{short(got)}.", hint))


def check_save_transaction(tmp):
    path = os.path.join(tmp, "hareketler.csv")
    write_file(path, f"{HEADER}\n2026-11-01,NAKIT,{A},1000,Burs\n")
    for transaction in [(TODAY, A, B, 250, "Kira payı"), (TODAY, A, "MASRAF", 5, "EFT masrafı")]:
        old = read_file(path)
        call("save_transaction", path, transaction, label=f"deneme file'ı, {short(transaction, 200)}",
             allow_none=True)
        text = read_file(path)
        line = csv_line(transaction)
        if text == old:
            raise Problem("save_transaction file'a bir satır eklemedi. Henüz kod yazmadıysanız # TODO'nun yerine "
                          "yazın; yazdıysanız open()'a file_name'i verdiğinize bakın: open(file_name, \"a\", "
                          "encoding=\"utf-8\").")
        if not text.startswith(old):
            raise Problem("save_transaction file'daki eski satırları sildi: file'ı \"w\" ile değil, \"a\" moduyla "
                          "açın; \"a\" yeni satırı sona ekler.")
        added = text[len(old):]
        if added == line.rstrip("\n"):
            raise Problem("save_transaction satırı \\n ile bitirmeli; yoksa sonraki hareket aynı satıra yazılır.")
        if added.startswith(HEADER):
            raise Problem("save_transaction yalnız hareketin satırını eklemeli; başlığı yeniden yazmayın.")
        if added != line:
            if garbled(added):
                raise Problem("Türkçe harfler bozuk yazılmış: file'ı open(file_name, \"a\", encoding=\"utf-8\") ile "
                              "açın.")
            raise Problem(f"save_transaction'ın eklediği satır beklenen: {line!r}, sizinki: {added!r}. Alanları "
                          "virgülle, aralarına boşluk koymadan yazın.")


def task_3(tmp):
    return [((), check_rules, ("BANK_CODE", "BRANCH_FEE", "EFT_FEE", "DAILY_LIMIT", "DIGITS")),
            (("iban_valid",), check_iban_valid, ()),
            (("mask_iban",), check_mask_iban, ()),
            (("resolve_receiver",), check_resolve_receiver, ()),
            (("save_transaction",), check_save_transaction, (tmp,))]


# 4. Kredi kartı ve döküm

def new_card(card_id, limit):
    cls = getattr(bank_module(), "Card", None)
    if not isinstance(cls, type):
        raise Problem("bank.py'de Card adında bir class (sınıf) yok. class satırının adını değiştirmeyin.")
    card, _ = run("Card", cls, [card_id, limit])
    for name in ("card_id", "limit", "debt"):
        if not hasattr(card, name):
            raise Problem("Card'ın card_id, limit ve debt attribute'ları olmalı: __init__'te "
                          "self.card_id = card_id, self.limit = limit ve self.debt = 0 yazın.")
    if card.card_id != card_id or card.limit != limit:
        raise Problem(f"Card({card_id!r}, {limit}) için card_id {card_id!r} ve limit {limit} olmalı; sizinki: "
                      f"card_id {short(card.card_id)}, limit {short(card.limit)}")
    if not equal(card.debt, 0):
        raise Problem(f"Yeni bir kartta debt 0 olmalı; Card({card_id!r}, {limit})'de sizinki: {short(card.debt)}. "
                      "Her kartın kendi borcu olmalı: __init__'te self.debt = 0 yazın, borcu self.debt'le değiştirin.")
    return card


def method(card, name, *args):
    func = getattr(card, name, None)
    if not callable(func):
        raise Problem(f"Card'da {name} adında bir method (metot) yok. def satırının adını değiştirmeyin.")
    result, _ = run("Card." + name, func, args)
    return result


def check_card():
    card = new_card("4821", 1000)
    steps = [
        ("available", None, 1000, 0, "Yeni kartta kullanılabilir limit, limitin tamamı: return self.limit - "
                                     "self.debt."),
        ("spend", 700, True, 700, ""),
        ("available", None, 300, 700, "available limit - debt return etmeli: 1000 - 700 = 300."),
        ("spend", 400, False, 700, "Kullanılabilir limit limit - debt, yani 300 TL; limitin tamamı değil. Ondan "
                                   "büyük bir harcamada False return edin, borcu değiştirmeyin."),
        ("spend", 300, True, 1000, "Kullanılabilir limite eşit bir harcama yapılabilir: amount kullanılabilir "
                                   "limitten büyükse False."),
        ("available", None, 0, 1000, ""),
        ("pay", 200, True, 800, ""),
        ("pay", 900, False, 800, "Borçtan büyük bir ödeme yapılamaz: amount borçtan büyükse False return edin, "
                                 "borcu değiştirmeyin."),
        ("pay", 800, True, 0, "Borcun tamamı ödenebilir: amount borçtan büyükse False."),
    ]
    own = "Her kartın kendi borcu olmalı: borcu self.debt'le tutun, Card.debt'le değil."
    other = None
    for name, amount, want, debt, hint in steps:
        old = card.debt
        if amount is None:
            got = method(card, name)
            shown = f"Card(\"4821\", 1000) kartında, borç {old} TL iken, {name}()"
        else:
            got = method(card, name, amount)
            shown = f"Card(\"4821\", 1000) kartında, borç {old} TL iken, {name}({amount})"
        if not equal(got, want):
            if type(want) is bool and type(got) is not bool:
                hint = f"{name} işlemi yapabilirse True, yapamazsa False return etmeli."
            raise Problem(with_hint(f"{shown} {want!r} return etmeli; sizinki: {short(got)}.", hint))
        have = card.debt
        if amount is not None and not equal(have, debt):
            hint = ""
            if type(have) is not int or type(old) is not int:
                hint = " debt bir tam sayı olmalı."
            elif want is False:
                hint = f" {name} False return ederken borcu değiştirmemeli."
            elif name == "spend" and have == old:
                hint = " spend harcamayı borca eklemeli: self.debt = self.debt + amount."
            elif name == "spend" and have == amount:
                hint = (f" Harcama önceki borcun üstüne eklenmeli: self.debt = self.debt + amount. =+ yazılırsa borç "
                        f"yalnız son harcama, {amount} olur.")
            elif name == "pay" and have == 0 - amount:
                hint = f" Ödeme borçtan düşmeli: self.debt = self.debt - amount. =- yazılırsa borç {have} olur."
            elif name == "pay" and have == old:
                hint = " pay ödemeyi borçtan düşmeli: self.debt = self.debt - amount."
            elif name == "pay" and have == old + amount:
                hint = " Ödeme borçtan düşer, borca eklenmez: self.debt = self.debt - amount."
            raise Problem(f"{shown} call'undan sonra debt {debt} olmalı, sizinki: {short(have)}.{hint}")
        if other is None and name == "spend":
            other = new_card("7310", 500)
            if not equal(card.debt, debt):
                raise Problem(f"Yeni bir kart kurmak öbür kartın borcunu değiştirmemeli: Card(\"7310\", 500) "
                              f"kurulunca Card(\"4821\", 1000) kartının borcu {debt} yerine {short(card.debt)} "
                              f"oldu. {own}")
            available = method(other, "available")
            if not equal(available, 500):
                raise Problem(f"Yeni Card(\"7310\", 500) kartında available() 500 return etmeli, sizinki: "
                              f"{short(available)}. {own}")
    if not equal(other.debt, 0):
        raise Problem(f"Bir kartta harcama yapılınca öbür kartın borcu değişmemeli; Card(\"7310\", 500) kartının borcu "
                      f"{short(other.debt)} oldu. {own}")


DOC_ACT = [("2026-10-01", "4821", "spend", "Kampüs Kafe", "yemek", 300),
           ("2026-10-02", "7310", "spend", "Kitapçı", "kitap", 90),
           ("2026-10-20", "4821", "payment", "-", "-", 100)]
REPLAY_ACT = [("2026-10-01", "4821", "spend", "Kampüs Kafe", "yemek", 550),
              ("2026-10-02", "7310", "spend", "Giyim Mağazası", "giyim", 800),
              ("2026-10-10", "4821", "payment", "-", "-", 350),
              ("2026-10-12", "4821", "spend", "Ayakkabıcı", "giyim", 800),
              ("2026-10-14", "7310", "payment", "-", "-", 650),
              ("2026-10-20", "4821", "payment", "-", "-", 3000),
              ("2026-10-25", "4821", "spend", "Sinema Salonu", "eğlence", 150)]
IN_ORDER = ("Hareketleri activity'deki sırayla, tek bir loop'ta uygulayın; önce bütün harcamalar sonra ödemeler "
            "değil.")
CALL_PAY = "kind \"payment\" ise kartın pay()'ini çağırın, spend()'ini değil."
APPLY_PAY = "Ödemeleri de uygulayın: kind \"payment\" ise kartın pay()'ini amount'la çağırın."
SKIP_OTHERS = "Başka kartların hareketlerini atlayın: card_id'si bu kartınki değilse continue."
SWAPPED = "kind \"spend\" ise spend(), \"payment\" ise pay() çağrılmalı; sizinkinde ikisi yer değiştirmiş."
ONE_CARD = ("Hareketleri loop'tan önce kurduğunuz tek bir karta uygulayın; her harekette yeni bir kart kurulursa "
            "önceki hareketler kaybolur.")
# Sık yapılan yanlışların bu iki örnekte verdiği borçlar
DOC_HINTS = {400: CALL_PAY, 300: APPLY_PAY, 290: SKIP_OTHERS, 100: SWAPPED, 0: ONE_CARD}
REPLAY_HINTS = {350: IN_ORDER, 900: CALL_PAY, 700: APPLY_PAY, 500: SKIP_OTHERS, 200: SWAPPED, 150: ONE_CARD,
                0: ONE_CARD}


def check_replay():
    for activity, limit, want, label, hints in [(DOC_ACT, 1000, 200, "docstring'deki örnek", DOC_HINTS),
                                                (REPLAY_ACT, 1000, 1000, "yedi hareket, iki kart", REPLAY_HINTS)]:
        got, _ = call("replay_card", "4821", limit, list(activity), label=f"\"4821\", {limit}, {label}")
        if type(got) in (int, float):
            raise Problem(f"replay_card kartı return etmeli, borcu değil: return card. Sizinki: {short(got)}")
        if not hasattr(got, "debt"):
            raise Problem(f"replay_card bir Card return etmeli: return card. Sizinki: {type_name(got)} {short(got)}")
        if not equal(got.debt, want):
            hint = ""
            if type(got.debt) is int:
                hint = hints.get(got.debt, "")
            raise Problem(with_hint(f"replay_card(\"4821\", {limit}, {label}).debt {want} olmalı, sizinki: "
                                    f"{short(got.debt)}.", hint))


STATEMENT_ACT = [("2026-09-15", "4821", "spend", "Mahalle Market", "market", 80),
                 ("2026-09-16", "4821", "spend", "Kampüs Kafe", "yemek", 300),
                 ("2026-09-20", "7310", "spend", "Kitapçı", "kitap", 90),
                 ("2026-10-01", "4821", "payment", "-", "-", 200),
                 ("2026-10-07", "4821", "spend", "Dizi Kutusu", "abonelik", 149),
                 ("2026-10-15", "4821", "spend", "Sinema Salonu", "eğlence", 150),
                 ("2026-10-16", "4821", "spend", "Taksi", "ulaşım", 70)]
STATEMENT_WANT = ([("2026-09-16", "Kampüs Kafe", 300), ("2026-10-07", "Dizi Kutusu", 149),
                   ("2026-10-15", "Sinema Salonu", 150)], 599)
STATEMENT_DOC = [("2026-09-30", "4821", "spend", "Market", "market", 80),
                 ("2026-10-01", "4821", "spend", "Kafe", "yemek", 300),
                 ("2026-10-02", "7310", "spend", "Kitapçı", "kitap", 90),
                 ("2026-10-15", "4821", "spend", "Sinema", "eğlence", 150)]
STATEMENT_DOC_WANT = ([("2026-10-01", "Kafe", 300), ("2026-10-15", "Sinema", 150)], 450)


def check_statement():
    for activity, start, end, want, label in [
            (STATEMENT_DOC, "2026-10-01", "2026-10-31", STATEMENT_DOC_WANT, "docstring'deki örnek"),
            (STATEMENT_ACT, "2026-09-16", "2026-10-15", STATEMENT_WANT, "yedi hareket")]:
        shown = f"statement({label}, \"4821\", {start!r}, {end!r})"
        got, _ = call("statement", list(activity), "4821", start, end, label=f"{label}, \"4821\", {start!r}, {end!r}")
        if equal(got, want):
            continue
        check_tuple(got, 2, "statement", "(lines, total)")
        lines, total = got
        if type(lines) is not list:
            raise Problem(f"lines bir list olmalı, sizinki: {type_name(lines)} {short(lines)}")
        for line in lines:
            if type(line) is not tuple or len(line) != 3:
                raise Problem(f"lines'taki her item bir (date, merchant, amount) tuple'ı olmalı, sizinki: "
                              f"{short(line)}")
        if lines != want[0]:
            dates_in = []
            for line in lines:
                dates_in.append(line[0])
            hint = ""
            if start not in dates_in and want[0][0][0] == start:
                hint = "start günü de ekstreye girer: date >= start."
            elif end not in dates_in and want[0][-1][0] == end:
                hint = "end günü de ekstreye girer: date <= end."
            elif "2026-10-01" in dates_in and activity is STATEMENT_ACT:
                hint = "Ödemeler (kind \"payment\") ekstreye girmez; yalnız \"spend\" hareketleri."
            elif "2026-09-20" in dates_in or "2026-10-02" in dates_in:
                hint = "Yalnız card_id'nin harcamaları girer; başka kartlarınkiler girmez."
            elif "2026-09-15" in dates_in or "2026-10-16" in dates_in or "2026-09-30" in dates_in:
                hint = "Yalnız start ile end arasındaki harcamalar girer."
            raise Problem(with_hint(f"{shown}: lines beklenen: {short(want[0], 200)}, sizinki: {short(lines, 200)}.",
                                    hint))
        raise Problem(f"{shown}: total, lines'taki amount'ların toplamı olmalı: {want[1]}, sizinki: {short(total)}")


PAYMENT_INFO_CASES = [(450, "2026-10-15"), (1234, "2026-11-25"), (99, "2026-12-28"), (0, "2026-10-05")]


def check_payment_info():
    check_rules("MIN_PERCENT", "DUE_DAYS")
    for i, (total, end) in enumerate(PAYMENT_INFO_CASES):
        results = PAYMENT_INFO_RESULTS[i]
        want = results["want"]
        got, _ = call("payment_info", total, end)
        if equal(got, want):
            continue
        shown = f"payment_info({total}, {end!r})"
        check_tuple(got, 2, "payment_info", "(minimum, due)")
        minimum, due = got
        if not equal(minimum, want[0]):
            hint = ""
            if type(minimum) is float:
                hint = " // ile bölün: asgari ödeme tam sayı, total * MIN_PERCENT // 100."
            elif minimum == 0 and total > 0:
                hint = " Önce çarpın, sonra bölün: total * MIN_PERCENT // 100. MIN_PERCENT // 100 tek başına 0 verir."
            elif minimum == results["divided_first"]:
                hint = " Önce çarpın, sonra bölün: total * MIN_PERCENT // 100."
            elif minimum == results["rounded"]:
                hint = " // ile bölün; // aşağı yuvarlar, round() değil: total * MIN_PERCENT // 100."
            raise Problem(f"{shown}: minimum {want[0]} olmalı, sizinki: {short(minimum)}.{hint}")
        hint = " due = dates.add_days(end, DUE_DAYS)."
        if due == end:
            hint = " end'e DUE_DAYS gün ekleyin: dates.add_days(end, DUE_DAYS)."
        raise Problem(f"{shown}: due (son ödeme günü) {want[1]!r} olmalı, sizinki: {short(due)}.{hint}")


INSTALLMENT_CASES = [(1000, 3), (1200, 4), (100, 7), (999, 1)]


def check_installments():
    for i, (amount, count) in enumerate(INSTALLMENT_CASES):
        want = INSTALLMENT_RESULTS[i]["want"]
        got, _ = call("installments", amount, count)
        if equal(got, want):
            continue
        shown = f"installments({amount}, {count}) {want} return etmeli, sizinki: {short(got)}."
        hint = ""
        if type(got) is not list:
            hint = "installments taksitlerin list'ini return etmeli."
        elif len(got) != count:
            hint = f"count taksit olmalı: {count} item."
        elif got and type(got[0]) is float:
            hint = "Taksitler tam sayı: base = amount // count."
        elif got == list(reversed(want)):
            hint = "Kalan ilk taksitlere dağıtılır: ilk rest taksit base + 1, öbürleri base."
        elif sum(got) != amount:
            hint = "Taksitlerin toplamı amount olmalı: kalanı (amount % count) birer TL olarak ilk taksitlere dağıtın."
        else:
            hint = "Kalanı birer TL olarak dağıtın: ilk rest taksit base + 1, öbürleri base."
        raise Problem(with_hint(shown, hint))


TOTALS_ACT = [("2026-09-30", "4821", "spend", "Mahalle Market", "market", 200),
              ("2026-10-01", "4821", "spend", "Kampüs Kafe", "yemek", 300),
              ("2026-10-03", "4821", "spend", "Köşe Lokanta", "yemek", 120),
              ("2026-10-05", "7310", "spend", "Kitapçı", "kitap", 90),
              ("2026-10-07", "4821", "spend", "Dizi Kutusu", "abonelik", 149),
              ("2026-10-15", "4821", "payment", "-", "-", 500),
              ("2026-10-31", "4821", "spend", "Sinema Salonu", "eğlence", 150),
              ("2026-11-01", "4821", "spend", "Kampüs Kafe", "yemek", 60)]
TOTALS_WANT = {"yemek": 420, "abonelik": 149, "eğlence": 150}
TOTALS_DOC = [("2026-10-01", "4821", "spend", "Kafe", "yemek", 300),
              ("2026-10-03", "4821", "spend", "Lokanta", "yemek", 120),
              ("2026-10-15", "4821", "spend", "Sinema", "eğlence", 150),
              ("2026-11-01", "4821", "spend", "Kafe", "yemek", 60)]


def check_category_totals():
    cases = [(TOTALS_DOC, "2026-10", {"yemek": 420, "eğlence": 150}, "docstring'deki örnek"),
             (TOTALS_ACT, "2026-10", TOTALS_WANT, "sekiz hareket"),
             (TOTALS_ACT, "2026-12", {}, "sekiz hareket")]
    for activity, month, want, label in cases:
        got, _ = call("category_totals", list(activity), "4821", month, label=f"{label}, \"4821\", {month!r}")
        if equal(got, want):
            continue
        shown = f"category_totals({label}, \"4821\", {month!r})"
        if type(got) is not dict:
            raise Problem(f"category_totals bir dict return etmeli, sizinki: {type_name(got)} {short(got)}")
        hint = ""
        if "-" in got:
            hint = "Ödemeler (kind \"payment\") girmez; yalnız \"spend\" hareketleri."
        elif "kitap" in got:
            hint = "Yalnız card_id'nin harcamaları girer."
        elif "market" in got or got.get("yemek") == 480:
            hint = "Yalnız o ayın harcamaları girer: date[:7] == month."
        elif "Kampüs Kafe" in got or "Kafe" in got:
            hint = "Dict'in key'i kategori (category), merchant değil."
        elif len(got) == 1 and len(want) > 1 and got.get(activity[0][4]) == activity[0][5]:
            hint = ("Yalnız ilk harcama sayılmış: return satırı loop'un içinde kalmış. return'ü for'un dışına, "
                    "function'ın sonuna alın.")
        elif got.get("yemek") in (120, 60):
            hint = ("Aynı kategorideki harcamaları toplayın: totals[category] = totals.get(category, 0) + amount; "
                    "her harcamada baştan yazmayın.")
        raise Problem(with_hint(f"{shown} beklenen: {short(want)}, sizinki: {short(got)}.", hint))


PLACES_ACT = [("2026-09-07", "4821", "spend", "Dizi Kutusu", "abonelik", 149),
              ("2026-09-07", "4821", "spend", "Müzik Kutusu", "abonelik", 59),
              ("2026-09-12", "4821", "spend", "Kampüs Kafe", "yemek", 80),
              ("2026-09-20", "4821", "payment", "-", "-", 300),
              ("2026-09-25", "7310", "spend", "Bulut Depo", "abonelik", 29),
              ("2026-10-07", "4821", "spend", "Dizi Kutusu", "abonelik", 149),
              ("2026-10-07", "4821", "spend", "Müzik Kutusu", "abonelik", 59),
              ("2026-10-11", "4821", "spend", "Sinema Salonu", "eğlence", 150),
              ("2026-10-20", "4821", "payment", "-", "-", 400),
              ("2026-10-25", "7310", "spend", "Bulut Depo", "abonelik", 29),
              ("2026-11-07", "4821", "spend", "Dizi Kutusu", "abonelik", 149),
              ("2026-11-09", "4821", "spend", "Kitapçı", "kitap", 120),
              ("2026-11-20", "4821", "payment", "-", "-", 250),
              ("2026-11-25", "7310", "spend", "Bulut Depo", "abonelik", 29)]
PLACES_DOC = [("2026-10-01", "4821", "spend", "Kafe", "yemek", 80),
              ("2026-10-09", "4821", "spend", "Kafe", "yemek", 60),
              ("2026-10-12", "4821", "spend", "Sinema", "eğlence", 150)]


def set_result(name, shown, got):
    """got bir set değilse bunu söyler."""
    if got is None:
        raise Problem(f"{shown} boş bir set return etmeli: set(). Sizinki None; bu durumda da return satırına "
                      "ulaşıldığına bakın.")
    if type(got) is dict and not got:
        raise Problem(f"{shown} boş bir set return etmeli: set(). {{}} boş bir dict'tir.")
    if type(got) is not set:
        raise Problem(f"{name} bir set return etmeli, sizinki: {type_name(got)} {short(got)}")


PLACES_CASES = [(PLACES_DOC, "4821", "2026-10", "docstring'deki örnek"),
                (PLACES_ACT, "4821", "2026-10", "on dört hareket"),
                (PLACES_ACT, "7310", "2026-09", "on dört hareket"),
                (PLACES_ACT, "4821", "2026-12", "on dört hareket")]


def check_places():
    for i, (activity, card_id, month, label) in enumerate(PLACES_CASES):
        results = PLACES_RESULTS[i]
        want = results["want"]
        got, _ = call("places", list(activity), card_id, month, label=f"{label}, {card_id!r}, {month!r}",
                      allow_none=not want)
        if equal(got, want):
            continue
        shown = f"places({label}, {card_id!r}, {month!r})"
        set_result("places", shown, got)
        hint = ""
        if "-" in got:
            hint = "Yalnız \"spend\" hareketlerinin merchant'ları girer; ödemelerinki girmez."
        elif "Bulut Depo" in got and card_id != "7310":
            hint = "Yalnız card_id'nin harcamaları girer."
        elif got == results["every_month"]:
            hint = "Yalnız o ayın harcamaları girer: date[:7] == month."
        raise Problem(with_hint(f"{shown} beklenen: {short(want)}, sizinki: {short(got)}.", hint))


NEW_DOC = [("2026-09-03", "4821", "spend", "Kafe", "yemek", 80),
           ("2026-10-01", "4821", "spend", "Kafe", "yemek", 60),
           ("2026-10-12", "4821", "spend", "Sinema", "eğlence", 150)]
NEW_ACT = [("2026-09-03", "4821", "spend", "Kampüs Kafe", "yemek", 80),
           ("2026-09-07", "4821", "spend", "Dizi Kutusu", "abonelik", 149),
           ("2026-10-07", "4821", "spend", "Dizi Kutusu", "abonelik", 149),
           ("2026-10-11", "4821", "spend", "Sinema Salonu", "eğlence", 150),
           ("2026-10-15", "7310", "spend", "Kitapçı", "kitap", 90),
           ("2026-11-02", "4821", "spend", "Kampüs Kafe", "yemek", 60),
           ("2026-11-07", "4821", "spend", "Dizi Kutusu", "abonelik", 149),
           ("2026-11-09", "4821", "spend", "Kitapçı", "kitap", 120),
           ("2026-11-20", "4821", "payment", "-", "-", 400)]


NEW_PLACES_CASES = [(NEW_DOC, "4821", "2026-10", ["2026-09"], "docstring'deki örnek"),
                    (NEW_ACT, "4821", "2026-11", ["2026-09", "2026-10"], "dokuz hareket"),
                    (NEW_ACT, "4821", "2026-10", [], "dokuz hareket"),
                    (NEW_ACT, "4821", "2026-12", ["2026-11"], "dokuz hareket")]


def check_new_places():
    for i, (activity, card_id, month, previous, label) in enumerate(NEW_PLACES_CASES):
        results = NEW_PLACES_RESULTS[i]
        want = results["want"]
        got, _ = call("new_places", list(activity), card_id, month, list(previous),
                      label=f"{label}, \"{card_id}\", {month!r}, {previous}", allow_none=not want)
        if equal(got, want):
            continue
        shown = f"new_places({label}, \"{card_id}\", {month!r}, {previous})"
        set_result("new_places", shown, got)
        hint = ""
        if len(previous) > 1 and got == results["last_month_only"]:
            hint = ("Önceki ayların hepsinin yerlerini birleştirin: before = before | places(...); yalnız son ayı "
                    "ya da kesişimi (&) değil, birleşimi (|).")
        elif not previous and not got:
            hint = "previous boşsa bu ayın bütün yerleri yenidir: before = set() ile başlayın."
        elif got == results["this_month"] and previous:
            hint = ("before, önceki ayların yerlerinin birleşimi olmalı: before = set() ile başlayıp her ay için "
                    "before = before | places(...); sonra bu ayın yerlerinden çıkarın (fark, -).")
        elif "Kitapçı" not in got and "Kitapçı" in want:
            hint = ("Önceki aylarda yalnız card_id'nin gittiği yerler sayılır: previous'taki her ay için "
                    "before = before | places(activity, card_id, ay).")
        raise Problem(with_hint(f"{shown} beklenen: {short(want)}, sizinki: {short(got)}.", hint))


def task_4(tmp):
    return [(("Card",), new_card, ("4821", 1000)),
            (("Card.available", "Card.spend", "Card.pay"), check_card, ()),
            (("replay_card",), shadow_checked, ("replay_card", check_replay)),
            (("statement",), shadow_checked, ("statement", check_statement)),
            (("payment_info",), check_payment_info, ()),
            (("installments",), check_installments, ()),
            (("category_totals",), shadow_checked, ("category_totals", check_category_totals)),
            (("places",), shadow_checked, ("places", check_places)),
            (("new_places",), check_new_places, ())]


# 5. Döviz, kredi, ATM ve raporunuz

BUY_CASES = [(1000, 41.2), (5000, 48.64), (2500, 41.76), (40, 41.7)]


def check_buy_foreign():
    for i, (tl, rate) in enumerate(BUY_CASES):
        results = BUY_RESULTS[i]
        want = results["want"]
        got, _ = call("buy_foreign", tl, rate)
        if equal(got, want):
            continue
        shown = f"buy_foreign({tl}, {rate})"
        check_tuple(got, 2, "buy_foreign", "(units, cost)")
        units, cost = got
        if type(units) is not int:
            raise Problem(f"{shown}: units bir int olmalı, yalnız tam birim alınır: units = int(tl_amount // "
                          f"sell_rate). Sizinki: {short(units)}")
        if units != want[0]:
            hint = ""
            if units == results["rounded_units"]:
                hint = " // aşağı yuvarlar; round() yukarı da yuvarlayabilir: int(tl_amount // sell_rate)."
            raise Problem(f"{shown}: units {want[0]} olmalı, sizinki: {units}.{hint}")
        if type(cost) is not int:
            raise Problem(f"{shown}: cost round() ile tam sayıya yuvarlanmalı: cost = round(units * sell_rate). "
                          f"Sizinki: {short(cost)}")
        hint = ""
        if cost == tl:
            hint = " cost, alınan birimlerin TL karşılığı: round(units * sell_rate); tl_amount'un tamamı değil."
        raise Problem(f"{shown}: cost {want[1]} olmalı, sizinki: {cost}.{hint}")


SELL_CASES = [(24, 40.0), (102, 47.67), (7, 40.93)]


def check_sell_foreign():
    for i, (units, rate) in enumerate(SELL_CASES):
        results = SELL_RESULTS[i]
        want = results["want"]
        got, _ = call("sell_foreign", units, rate)
        if equal(got, want):
            continue
        shown = f"sell_foreign({units}, {rate})"
        if type(got) is not int:
            raise Problem(f"{shown} round() ile tam sayıya yuvarlanmış bir int return etmeli: round(units * "
                          f"buy_rate). Sizinki: {short(got)}")
        hint = ""
        if got == results["truncated"]:
            hint = f" round() ile yuvarlayın; int() aşağı keser: {units} * {rate} = {results['product_text']}."
        raise Problem(f"{shown} {want} return etmeli, sizinki: {got}.{hint}")


RATE_CASES = [("USD", 41.2, 42.034), ("EUR", 48.6, 49.0), ("USD", 40.996, 41.5)]


def check_rate_text():
    for i, (currency, buy, sell) in enumerate(RATE_CASES):
        results = RATE_RESULTS[i]
        want = results["want"]
        got, _ = call("rate_text", currency, buy, sell)
        if equal(got, want):
            continue
        hint = ""
        if type(got) is not str:
            hint = "rate_text bir str return etmeli."
        elif got in (results["plain"], results["rounded"]):
            hint = ("Kurları noktadan sonra iki basamakla yazın: f-string'de {buy:.2f}; 41.2 \"41.20\", 49.0 \"49.00\" "
                    "olur.")
        elif got == results["swapped"]:
            hint = "Önce alış (buy), sonra satış (sell) kuru yazılır."
        raise Problem(with_hint(f"rate_text({currency!r}, {buy}, {sell}) {want!r} return etmeli, sizinki: "
                                f"{short(got)}.", hint))


LOAN_CASES = [(12000, 2, 12), (3000, 2, 3), (50000, 3.5, 24), (10000, 1.25, 1)]


def check_loan_installment():
    for i, (principal, rate, months) in enumerate(LOAN_CASES):
        results = LOAN_RESULTS[i]
        want = results["want"]
        got, _ = call("loan_installment", principal, rate, months)
        if equal(got, want):
            continue
        shown = f"loan_installment({principal}, {rate}, {months})"
        if type(got) is not int:
            raise Problem(f"{shown} round() ile tam sayıya yuvarlanmış bir int return etmeli, sizinki: {short(got)}")
        hint = ""
        if got == results["truncated"]:
            hint = f" round() ile yuvarlayın; int() aşağı keser: taksit {results['exact_text']}."
        elif got == results["rate_not_divided"]:
            hint = " monthly_rate yüzde olarak verilir: önce r = monthly_rate / 100."
        elif got == results["no_parentheses"]:
            hint = " Paydanın parantezini unutmayın: ((1 + r) ** months - 1)."
        raise Problem(f"{shown} {want} return etmeli, sizinki: {got}. Formül: r = monthly_rate / 100; "
                      f"taksit = principal * r * (1 + r) ** months / ((1 + r) ** months - 1).{hint}")


GOAL_CASES = [(1000, 300, 0), (10000, 1000, 2), (900, 300, 0), (5000, 400, 1.5), (50000, 2500, 3)]


def check_months_to_goal():
    for i, (goal, monthly, rate) in enumerate(GOAL_CASES):
        results = GOAL_RESULTS[i]
        want = results["want"]
        got, _ = call("months_to_goal", goal, monthly, rate)
        if equal(got, want):
            continue
        shown = f"months_to_goal({goal}, {monthly}, {rate}) {want} return etmeli, sizinki: {short(got)}."
        hint = ""
        if type(got) is not int:
            hint = "Ay sayısını, yani months'u return edin; bir int."
        elif got == results["or_equal"]:
            hint = "saved goal'e eşit olunca hedefe ulaşılmıştır: saved < goal olduğu sürece dönün, <= değil."
        elif got == want - 1 or got == want + 1:
            hint = "months 0'dan başlar ve her turda bir artar: saved = 0, months = 0; loop'ta months += 1."
        elif rate and got == results["rate_not_divided"]:
            hint = "monthly_rate yüzde olarak verilir: saved * monthly_rate / 100."
        raise Problem(with_hint(shown, hint))


REPORT_TRANSACTIONS = [("2026-09-01", "NAKIT", A, 4400, "Hesap açılışı"), ("2026-09-03", "NAKIT", A, 3500, "Burs"),
                       ("2026-09-10", A, B, 250, "Kitap parası"), ("2026-09-12", A, "NAKIT", 600, "ATM'den çekim"),
                       ("2026-09-20", A, "DOVIZ", 989, "USD alımı"), ("2026-09-20", "DOVIZ", C, 24, "USD alımı"),
                       ("2026-10-03", "NAKIT", A, 3500, "Burs"), ("2026-10-08", A, X, 1200, "Kira payı"),
                       ("2026-10-08", A, "MASRAF", 5, "EFT masrafı"),
                       ("2026-10-22", A, "KART-4821", 900, "Kart ödemesi"),
                       ("2026-11-03", "NAKIT", A, 3500, "Burs"), ("2026-11-05", B, A, 300, "Kahve")]
REPORT_ACTIVITY = [("2026-09-07", "4821", "spend", "Dizi Kutusu", "abonelik", 149),
                   ("2026-09-09", "4821", "spend", "Kampüs Kafe", "yemek", 180),
                   ("2026-09-18", "4821", "spend", "Mahalle Market", "market", 640),
                   ("2026-10-07", "4821", "spend", "Dizi Kutusu", "abonelik", 149),
                   ("2026-10-11", "4821", "spend", "Taksi", "ulaşım", 210),
                   ("2026-10-22", "4821", "payment", "-", "-", 900),
                   ("2026-11-07", "4821", "spend", "Dizi Kutusu", "abonelik", 149),
                   ("2026-11-07", "4821", "spend", "Kampüs Kafe", "yemek", 95)]
DOC_TITLE = "Aylara göre kart harcamam"


def check_my_report():
    cases = [(REPORT_TRANSACTIONS, REPORT_ACTIVITY, "bir müşterinin hesap ve kart hareketleri"),
             (REPORT_TRANSACTIONS, [], "kartı olmayan bir müşterinin hareketleri"),
             ([(TODAY, "NAKIT", A, 1000, "Hoş geldin hediyesi")], [], "yeni açılmış, kartı olmayan bir hesap"),
             ([], [], "hiç hareketi olmayan bir müşteri")]
    for transactions, activity, label in cases:
        got, _ = call("my_report", list(transactions), list(activity), label=label)
        check_tuple(got, 2, "my_report", "(title, rows)")
        title, rows = got
        if type(title) is not str or title.strip() == "":
            raise Problem(f"title raporunuzun başlığı, boş olmayan bir str olmalı; sizinki: {short(title)}")
        if title.strip() == DOC_TITLE:
            raise Problem(f"Raporunuzun başlığı docstring'deki örneğin başlığı (\"{DOC_TITLE}\"). Docstring'deki "
                          "örneği değil, kendi raporunuzu yazın.")
        if type(rows) is not list:
            raise Problem(f"rows tablonun satırları, bir list olmalı; {label} için sizinki: {type_name(rows)} "
                          f"{short(rows)}")
        for row in rows:
            if type(row) is not tuple:
                raise Problem(f"rows'taki her satır bir tuple olmalı, (\"2026-10\", 1840) gibi; {label} için "
                              f"sizinki: {short(row)}")


# testlerim.py

TEST_INPUT = ["tr57 1234 5001 0110 0100 0000 01", "TR57 1234 5001 0110 0100 0000 02", ""]
VERDICT = re.compile(r"Geçersiz|Geçerli")
DONE_TEXT = "Bütün testler geçti."


def bank_aliases(tree, functions):
    """testlerim.py bank module'üne (modül) hangi adlarla ulaşıyor: (bank'ın import edildiği adlar,
    {ad: bank'taki adı})."""
    modules = set()
    plain = {}
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name == "bank":
                    modules.add(alias.asname or "bank")
        elif isinstance(node, ast.ImportFrom) and node.module == "bank":
            for alias in node.names:
                if alias.name == "*":
                    for name in functions:
                        plain[name] = name
                else:
                    plain[alias.asname or alias.name] = alias.name
    return modules, plain


def bank_calls(node, modules, plain):
    """node'un içinde çağrılan bank function'larının adları."""
    found = set()
    for inner in ast.walk(node):
        if isinstance(inner, ast.Call):
            func = inner.func
            if isinstance(func, ast.Attribute) and isinstance(func.value, ast.Name) and func.value.id in modules:
                found.add(func.attr)
            elif isinstance(func, ast.Name) and func.id in plain:
                found.add(plain[func.id])
    return found


def tested_functions(tree, functions):
    """(assert sayısı, assert'lerin denediği bank function'ları). Bir assert, bir variable'a atanmış bir
    call'un (çağrı) sonucuna bakıyorsa o call da sayılır: masked = bank.mask_iban(...); assert masked == ...
    """
    modules, plain = bank_aliases(tree, functions)
    via = {}
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign):
            found = bank_calls(node.value, modules, plain)
            if found:
                for target in node.targets:
                    for name in ast.walk(target):
                        if isinstance(name, ast.Name):
                            via[name.id] = via.get(name.id, set()) | found
    count = 0
    tested = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Assert):
            count += 1
            tested |= bank_calls(node.test, modules, plain)
            for name in ast.walk(node.test):
                if isinstance(name, ast.Name) and name.id in via:
                    tested |= via[name.id]
    return count, tested


def iban_loop(tree):
    """testlerim.py'deki while True loop'unu arar: (while True var mı, içinde input var mı, break var mı)."""
    best = (False, False, False)
    for node in ast.walk(tree):
        if isinstance(node, ast.While) and isinstance(node.test, ast.Constant) and node.test.value is True:
            has_input = False
            has_break = False
            for inner in ast.walk(node):
                if isinstance(inner, ast.Call) and isinstance(inner.func, ast.Name) and inner.func.id == "input":
                    has_input = True
                if isinstance(inner, ast.Break):
                    has_break = True
            if (True, has_input, has_break) > best:
                best = (True, has_input, has_break)
    return best


def copy_project(tmp):
    """testlerim.py'nin çalışacağı kopya: projedeki .py file'ları ve data klasörü."""
    copy = os.path.join(tmp, "proje")
    os.mkdir(copy)
    for path in HERE.iterdir():
        if path.suffix == ".py" and path.name != "kontrol.py" and path.is_file():
            shutil.copyfile(path, os.path.join(copy, path.name))
    if DATA.is_dir():
        shutil.copytree(DATA, os.path.join(copy, "data"), ignore=shutil.ignore_patterns("__pycache__"))
    return copy


def error_place(stderr):
    """Hata mesajındaki en içteki testlerim.py ya da bank.py satırı: (file adı, satır no) ya da None."""
    place = None
    for found in re.finditer(r'File "([^"]+)", line (\d+)', stderr):
        name = os.path.basename(found.group(1))
        if name in ("testlerim.py", "bank.py"):
            place = (name, int(found.group(2)))
    return place


def source_line(path, number):
    try:
        with open(path, encoding="utf-8", errors="replace") as f:
            lines = f.read().splitlines()
    except OSError:
        return ""
    if 0 < number <= len(lines):
        return lines[number - 1].strip()
    return ""


def check_testlerim(tmp):
    if not TESTS.exists():
        raise Problem("testlerim.py bulunamadı: proje klasöründeki testlerim.py'yi silmeyin, bank.py ile aynı "
                      "klasörde dursun.")
    with open(TESTS, encoding="utf-8", errors="replace") as f:
        source = f.read()
    try:
        tree = ast.parse(source)
    except SyntaxError as e:
        raise Problem(f"testlerim.py'nin {e.lineno}. satırında bir yanlış var: SyntaxError: {e.msg}. Önce bunu "
                      "düzeltin.") from None
    bank = bank_module()
    functions = []
    for name in vars(bank):
        value = vars(bank)[name]
        if callable(value) and getattr(value, "__module__", None) == "bank":
            functions.append(name)
    count, tested = tested_functions(tree, functions)
    if count == 0:
        raise Problem("testlerim.py'de henüz assert yok: # TODO satırlarının yerine en az beş assert yazın; her biri "
                      "bank.py'deki bir function'ı denesin. Bir örnek, file'ın başındaki yorumda var.")
    if count < 5:
        raise Problem(f"testlerim.py'de {count} assert var. En az beş assert yazın; bu assert'ler bank.py'deki en az "
                      "üç farklı function'ı denesin.")
    if len(tested) < 3:
        names = ", ".join(sorted(tested)) if tested else "hiçbiri"
        raise Problem(f"testlerim.py'deki assert'ler bank.py'nin yalnız {len(tested)} function'ını deniyor "
                      f"({names}); en az üç farklı function'ı deneyin, bank.installments(100, 3) gibi.")
    copy = copy_project(tmp)
    env = dict(os.environ, PYTHONIOENCODING="utf-8", PYTHONDONTWRITEBYTECODE="1")
    given = "".join(line + "\n" for line in TEST_INPUT)
    try:
        done = subprocess.run([sys.executable, "testlerim.py"], cwd=copy, input=given.encode("utf-8"),
                              capture_output=True, env=env, timeout=TEST_TIMEOUT)
    except subprocess.TimeoutExpired:
        raise Problem("testlerim.py bitmedi; kontrol.py beklemeyi bıraktı. IBAN loop'unun içinde input() var mı, "
                      "boş satır gelince break'e ulaşılıyor mu, bakın; başka bir while da hiç bitmiyor olabilir.") \
            from None
    out = done.stdout.decode("utf-8", errors="replace")
    err = done.stderr.decode("utf-8", errors="replace")
    lines = [line for line in err.splitlines() if line.strip()]
    last = lines[-1].strip() if lines else ""
    place = error_place(err)
    ran_out = last.startswith("EOFError")
    if done.returncode != 0 and not ran_out:
        if last == "":
            raise Problem(f"testlerim.py {done.returncode} koduyla bitti: exit() ya da sys.exit() çağırmayın; file "
                          "sonuna kadar çalışsın.")
        if last.startswith("AssertionError") and place and place[0] == "testlerim.py":
            text = source_line(os.path.join(copy, "testlerim.py"), place[1])
            raise Problem(f"testlerim.py'nin {place[1]}. satırındaki assert geçmedi: {text}. Ya beklediğiniz değer "
                          "yanlış ya da denediği function: değeri docstring'deki kurala göre bir de elle hesaplayın.")
        where = f" ({place[0]}, {place[1]}. satır)" if place else ""
        hint = ""
        if "module 'bank' has no attribute" in last:
            hint = " bank.py'de bu adla bir function yok: adını bank.py'deki def satırından bakarak yazın."
        elif last.startswith("NameError"):
            hint = (" Python bu adı tanımıyor: bank.py'deki function'ları bank. ile çağırın, bank.installments(...) "
                    "gibi.")
        elif last.startswith(("ModuleNotFoundError", "ImportError")):
            hint = " testlerim.py bank.py ile aynı klasörde olmalı; ilk satırı import bank."
        raise Problem(f"testlerim.py çalışırken hata verdi{where}: {sentence(last)}{hint}")
    if DONE_TEXT not in out:
        raise Problem(f"testlerim.py \"{DONE_TEXT}\" yazdırmadı: bütün assert'lerden sonra print(\"{DONE_TEXT}\") "
                      "satırını yazın.")
    has_loop, has_input, has_break = iban_loop(tree)
    if not has_loop:
        raise Problem("testlerim.py'de while True ile yazılmış bir IBAN deneme loop'u yok: while True ile input()'tan "
                      "bir IBAN alın, boş satır gelince break ile loop'tan çıkın.")
    if not has_input:
        raise Problem("testlerim.py'deki while True loop'unda input() yok: IBAN'ı her turda input(\"IBAN (çıkmak için "
                      "boş bırakın): \") ile alın.")
    if not has_break:
        raise Problem("testlerim.py'deki while True loop'unda break yok: boş satır gelince (text == \"\") break ile "
                      "loop'tan çıkın.")
    if ran_out:
        raise Problem("testlerim.py'deki loop boş satırda bitmedi, input() bir IBAN daha istedi: boş satır gelince "
                      "(text == \"\") break ile loop'tan çıkın.")
    valid = quiet("iban_valid", "TR571234500101100100000001")
    invalid = quiet("iban_valid", "TR571234500101100100000002")
    require(valid is True and invalid is False, "testlerim.py'deki IBAN loop'u bank.iban_valid'i kullanıyor ama "
                                                "iban_valid henüz doğru çalışmıyor. Önce 3. görevi geçin.")
    verdicts = VERDICT.findall(out)
    shown = f"kontrol.py loop'a sırayla {TEST_INPUT[0]!r}, {TEST_INPUT[1]!r} ve boş bir satır verdi"
    if not verdicts:
        raise Problem(f"{shown}; loop \"Geçerli\" ya da \"Geçersiz\" yazdırmadı. Her IBAN için "
                      "bank.iban_valid'in sonucuna göre print(\"Geçerli\") ya da print(\"Geçersiz\") yazın.")
    if verdicts[:2] == ["Geçersiz", "Geçerli"]:
        raise Problem(f"{shown}; loop geçerli IBAN'a \"Geçersiz\", geçersize \"Geçerli\" yazdı. bank.iban_valid "
                      "True return ederse \"Geçerli\", False return ederse \"Geçersiz\" yazdırın.")
    if verdicts[0] == "Geçersiz":
        raise Problem(f"{shown}; ilk IBAN geçerli ama loop \"Geçersiz\" yazdı. Girilen metnin boşluklarını "
                      "replace(\" \", \"\") ile silip upper() ile büyük harfe çevirin, sonra bank.iban_valid'e verin.")
    if len(verdicts) == 1:
        raise Problem(f"{shown}; loop ikinci IBAN'ı sormadan bitti. Yalnız boş satır gelince break ile çıkın.")
    if verdicts[1] == "Geçerli":
        raise Problem(f"{shown}; ikinci IBAN'ın bir rakamı yanlış ama loop \"Geçerli\" yazdı. bank.iban_valid "
                      "False return ederse \"Geçersiz\" yazdırın.")
    if len(verdicts) > 2:
        raise Problem(f"{shown}; loop boş satıra da bir sonuç yazdırdı. Boş satır gelince önce break ile çıkın, "
                      "iban_valid'e vermeyin.")


def task_5(tmp):
    return [((), check_rules, ("ATM_LIMIT",)),
            (("buy_foreign",), check_buy_foreign, ()),
            (("sell_foreign",), check_sell_foreign, ()),
            (("rate_text",), check_rate_text, ()),
            (("loan_installment",), check_loan_installment, ()),
            (("months_to_goal",), check_months_to_goal, ()),
            (("my_report",), check_my_report, ()),
            ((), check_testlerim, (tmp,))]


# --- beklenen sonuçlar: bir betik yazar, elle değiştirmeyin ---
BALANCES_RESULTS = [
    {
        "want": {"NAKIT": -100, "A": 70, "B": 30},
        "first_only": {"NAKIT": -100, "A": 100},
        "flipped": {"NAKIT": 100, "A": -70, "B": -30},
        "receivers_only": {"A": 100, "B": 30},
        "overwritten": {"NAKIT": -100, "A": -30, "B": 30},
    },
    {
        "want": {"NAKIT": -500, "A": 395, "B": 100, "MASRAF": 5},
        "first_only": {"NAKIT": -500, "A": 500},
        "flipped": {"NAKIT": 500, "A": -395, "B": -100, "MASRAF": -5},
        "receivers_only": {"A": 520, "B": 120, "MASRAF": 5},
        "overwritten": {"NAKIT": -500, "A": -5, "B": -20, "MASRAF": 5},
    },
    {"want": {}, "first_only": {}, "flipped": {}, "receivers_only": {}, "overwritten": {}},
]
HISTORY_RESULTS = [
    {
        "want": [("2026-09-02", "B", -30, "Yemek"), ("2026-09-01", "NAKIT", 100, "Burs")],
        "oldest_first": [("2026-09-01", "NAKIT", 100, "Burs"), ("2026-09-02", "B", -30, "Yemek")],
        "unsigned": [("2026-09-02", "B", 30, "Yemek"), ("2026-09-01", "NAKIT", 100, "Burs")],
        "unsigned_oldest_first": [("2026-09-01", "NAKIT", 100, "Burs"), ("2026-09-02", "B", 30, "Yemek")],
        "flipped": [("2026-09-02", "B", 30, "Yemek"), ("2026-09-01", "NAKIT", -100, "Burs")],
    },
    {
        "want": [
            ("2026-10-06", "MASRAF", -2, "Şubeler arası havale masrafı"),
            ("2026-10-05", "TR121234500102100200000001", 200, "Kira payı"),
            ("2026-10-04", "KART-4821", -300, "Kart ödemesi"),
            ("2026-10-02", "TR121234500102100200000001", -150, "Kahve"),
            ("2026-10-01", "NAKIT", 2000, "Burs"),
        ],
        "oldest_first": [
            ("2026-10-01", "NAKIT", 2000, "Burs"),
            ("2026-10-02", "TR121234500102100200000001", -150, "Kahve"),
            ("2026-10-04", "KART-4821", -300, "Kart ödemesi"),
            ("2026-10-05", "TR121234500102100200000001", 200, "Kira payı"),
            ("2026-10-06", "MASRAF", -2, "Şubeler arası havale masrafı"),
        ],
        "unsigned": [
            ("2026-10-06", "MASRAF", 2, "Şubeler arası havale masrafı"),
            ("2026-10-05", "TR121234500102100200000001", 200, "Kira payı"),
            ("2026-10-04", "KART-4821", 300, "Kart ödemesi"),
            ("2026-10-02", "TR121234500102100200000001", 150, "Kahve"),
            ("2026-10-01", "NAKIT", 2000, "Burs"),
        ],
        "unsigned_oldest_first": [
            ("2026-10-01", "NAKIT", 2000, "Burs"),
            ("2026-10-02", "TR121234500102100200000001", 150, "Kahve"),
            ("2026-10-04", "KART-4821", 300, "Kart ödemesi"),
            ("2026-10-05", "TR121234500102100200000001", 200, "Kira payı"),
            ("2026-10-06", "MASRAF", 2, "Şubeler arası havale masrafı"),
        ],
        "flipped": [
            ("2026-10-06", "MASRAF", 2, "Şubeler arası havale masrafı"),
            ("2026-10-05", "TR121234500102100200000001", -200, "Kira payı"),
            ("2026-10-04", "KART-4821", 300, "Kart ödemesi"),
            ("2026-10-02", "TR121234500102100200000001", 150, "Kahve"),
            ("2026-10-01", "NAKIT", -2000, "Burs"),
        ],
    },
    {"want": [], "oldest_first": [], "unsigned": [], "unsigned_oldest_first": [], "flipped": []},
]
BRANCH_RESULTS = [
    {
        "want": [("0102", 1, 900), ("0101", 2, 400)],
        "accounts_counted": [("0102", 1, 900), ("0101", 3, 400)],
        "all_currencies": [("0102", 1, 900), ("0101", 2, 450)],
        "tl_accounts_only": [("0102", 1, 900), ("0101", 2, 400)],
    },
    {
        "want": [("0101", 3, 6400), ("0103", 2, 4400), ("0102", 3, 2500)],
        "accounts_counted": [("0101", 4, 6400), ("0103", 3, 4400), ("0102", 4, 2500)],
        "all_currencies": [("0101", 3, 6456), ("0103", 2, 4520), ("0102", 3, 2545)],
        "tl_accounts_only": [("0101", 3, 6400), ("0103", 2, 4400), ("0102", 2, 2500)],
    },
    {
        "want": [("0103", 1, 800), ("0101", 1, 500), ("0102", 1, 500)],
        "accounts_counted": [("0103", 1, 800), ("0101", 1, 500), ("0102", 1, 500)],
        "all_currencies": [("0103", 1, 800), ("0101", 1, 500), ("0102", 1, 500)],
        "tl_accounts_only": [("0103", 1, 800), ("0101", 1, 500), ("0102", 1, 500)],
    },
]
MASK_RESULTS = [
    {"want": "TR12******************0001"},
    {"want": "TR57******************0001"},
    {"want": "TR13******************1234"},
]
PAYMENT_INFO_RESULTS = [
    {"want": (90, "2026-10-25"), "divided_first": 80, "rounded": 90},
    {"want": (246, "2026-12-05"), "divided_first": 240, "rounded": 247},
    {"want": (19, "2027-01-07"), "divided_first": 0, "rounded": 20},
    {"want": (0, "2026-10-15"), "divided_first": 0, "rounded": 0},
]
INSTALLMENT_RESULTS = [
    {"want": [334, 333, 333]},
    {"want": [300, 300, 300, 300]},
    {"want": [15, 15, 14, 14, 14, 14, 14]},
    {"want": [999]},
]
PLACES_RESULTS = [
    {"want": {"Kafe", "Sinema"}, "every_month": {"Kafe", "Sinema"}},
    {
        "want": {"Dizi Kutusu", "Müzik Kutusu", "Sinema Salonu"},
        "every_month": {"Dizi Kutusu", "Kampüs Kafe", "Kitapçı", "Müzik Kutusu", "Sinema Salonu"},
    },
    {"want": {"Bulut Depo"}, "every_month": {"Bulut Depo"}},
    {"want": set(), "every_month": {"Dizi Kutusu", "Kampüs Kafe", "Kitapçı", "Müzik Kutusu", "Sinema Salonu"}},
]
NEW_PLACES_RESULTS = [
    {"want": {"Sinema"}, "last_month_only": {"Sinema"}, "this_month": {"Kafe", "Sinema"}},
    {
        "want": {"Kitapçı"},
        "last_month_only": {"Kampüs Kafe", "Kitapçı"},
        "this_month": {"Dizi Kutusu", "Kampüs Kafe", "Kitapçı"},
    },
    {
        "want": {"Dizi Kutusu", "Sinema Salonu"},
        "last_month_only": None,
        "this_month": {"Dizi Kutusu", "Sinema Salonu"},
    },
    {"want": set(), "last_month_only": set(), "this_month": set()},
]
BUY_RESULTS = [
    {"want": (24, 989), "rounded_units": 24},
    {"want": (102, 4961), "rounded_units": 103},
    {"want": (59, 2464), "rounded_units": 60},
    {"want": (0, 0), "rounded_units": 1},
]
SELL_RESULTS = [
    {"want": 960, "truncated": 960, "product_text": "960.00"},
    {"want": 4862, "truncated": 4862, "product_text": "4862.34"},
    {"want": 287, "truncated": 286, "product_text": "286.51"},
]
RATE_RESULTS = [
    {
        "want": "USD: alış 41.20 TL, satış 42.03 TL",
        "plain": "USD: alış 41.2 TL, satış 42.034 TL",
        "rounded": "USD: alış 41.2 TL, satış 42.03 TL",
        "swapped": "USD: alış 42.03 TL, satış 41.20 TL",
    },
    {
        "want": "EUR: alış 48.60 TL, satış 49.00 TL",
        "plain": "EUR: alış 48.6 TL, satış 49.0 TL",
        "rounded": "EUR: alış 48.6 TL, satış 49.0 TL",
        "swapped": "EUR: alış 49.00 TL, satış 48.60 TL",
    },
    {
        "want": "USD: alış 41.00 TL, satış 41.50 TL",
        "plain": "USD: alış 40.996 TL, satış 41.5 TL",
        "rounded": "USD: alış 41.0 TL, satış 41.5 TL",
        "swapped": "USD: alış 41.50 TL, satış 41.00 TL",
    },
]
LOAN_RESULTS = [
    {"want": 1135, "exact_text": "1134.72", "truncated": 1134, "rate_not_divided": 24000, "no_parentheses": 239},
    {"want": 1040, "exact_text": "1040.26", "truncated": 1040, "rate_not_divided": 6231, "no_parentheses": 59},
    {"want": 3114, "exact_text": "3113.64", "truncated": 3113, "rate_not_divided": 175000, "no_parentheses": 1749},
    {"want": 10125, "exact_text": "10125.00", "truncated": 10125, "rate_not_divided": 22500, "no_parentheses": 124},
]
GOAL_RESULTS = [
    {"want": 4, "or_equal": 4, "rate_not_divided": None},
    {"want": 10, "or_equal": 10, "rate_not_divided": 3},
    {"want": 3, "or_equal": 4, "rate_not_divided": None},
    {"want": 12, "or_equal": 12, "rate_not_divided": 4},
    {"want": 16, "or_equal": 16, "rate_not_divided": 3},
]
# --- beklenen sonuçların sonu ---


CHECKS = {1: task_1, 2: task_2, 3: task_3, 4: task_4, 5: task_5}


def guard_data(bank):
    """bank.py'deki open'ı sarar: kontrol sırasında data klasöründeki file'lar açılmaz."""
    real_open = open
    data = DATA.resolve()

    def guarded_open(file, *args, **kwargs):
        if isinstance(file, (str, bytes, os.PathLike)):
            try:
                path = pathlib.Path(os.fsdecode(file)).resolve()
            except (OSError, ValueError):
                path = None
            if path is not None and (path == data or data in path.parents):
                raise DataFile(path.name)
        return real_open(file, *args, **kwargs)

    bank.open = guarded_open


IMPORT_WRITE_NOTE = ("bank.py'nin en dışında data klasörüne yazan bir satır var; denemelerinizi testlerim.py'ye "
                     "taşıyın.")


def import_guard(blocked):
    """bank.py import edilirken kullanılan open. data klasöründeki bir file'ı yazmak için (w, a, x ya da +)
    açmak isteyen call gerçek file'a değil, boş bir file'a yazar; file'ın adı blocked'a eklenir."""
    real_open = builtins.open
    data = DATA.resolve()

    def import_open(file, mode="r", *args, **kwargs):
        writing = False
        if isinstance(file, (str, bytes, os.PathLike)) and isinstance(mode, str):
            for letter in "wax+":
                if letter in mode:
                    writing = True
        if writing:
            try:
                path = pathlib.Path(os.fsdecode(file)).resolve()
            except (OSError, ValueError):
                path = None
            if path is not None and (path == data or data in path.parents):
                blocked.append(path.name)
                return real_open(os.devnull, mode.replace("x", "w"), *args, **kwargs)
        return real_open(file, mode, *args, **kwargs)

    return import_open


def child(task):
    """Ayrı bir süreçte tek görevi dener; sonucu tek satır olarak yazar. 0. görev yalnız import eder."""
    sys.path.insert(0, str(HERE))
    os.chdir(HERE)
    out = io.StringIO()
    blocked = []
    real_open = builtins.open
    builtins.open = import_guard(blocked)
    try:
        with contextlib.redirect_stdout(out):
            import bank
    except (Exception, SystemExit) as e:
        last = traceback.format_exception_only(type(e), e)[-1].strip()
        print(MARK + json.dumps({"import": last, "line": bank_line(e)}))
        return
    finally:
        builtins.open = real_open
    if task == 0:
        # random: bank.py'nin başındaki hazır import random satırı yerinde mi?
        print(MARK + json.dumps({"ok": True, "random": isinstance(getattr(bank, "random", None), types.ModuleType)}))
        return
    if blocked:
        print(MARK + json.dumps({"ok": False, "note": IMPORT_WRITE_NOTE}))
        return
    guard_data(bank)
    tmp = tempfile.mkdtemp(prefix="kontrol-")
    TMP["path"] = tmp
    os.chdir(tmp)
    result = {"ok": True}
    try:
        # Bir parça ✗ alsa da sonrakiler denenir: satır kaç adın geçtiğini söyleyecek. Her parçanın sonucu hemen
        # yazılır; görev yarıda kesilirse de geçen parçalar ve ilk ✗'in notu kaybolmaz.
        for names, check, args in CHECKS[task](tmp):
            part = {"part": list(names), "ok": True}
            try:
                check(*args)
            except Problem as p:
                part = {"part": list(names), "ok": False, "note": str(p)}
            except Exception as e:
                last = traceback.format_exception_only(type(e), e)[-1].strip()
                line = bank_line(e)
                where = f" (bank.py, {line}. satır)" if line else ""
                part = {"part": list(names), "ok": False,
                        "note": f"kontrol.py bu görevi denerken beklenmedik bir hata aldı{where}: {last}"}
            print(MARK + json.dumps(part))
            if result["ok"] and not part["ok"]:
                result = {"ok": False, "note": part["note"]}
    finally:
        os.chdir(HERE)
        shutil.rmtree(tmp, ignore_errors=True)
    print(MARK + json.dumps(result))


TIMEOUT_NOTE = ("Bu görevin denemesi bitmedi; kontrol.py beklemeyi bıraktı. Bir loop hiç bitmiyor olabilir, yani "
                "bir infinite loop'a (sonsuz döngü) girilmiş olabilir: while'ın şartı bir noktada False oluyor mu, "
                "break satırına ulaşılıyor mu, bakın. for ile gezdiğiniz bir list'e loop'un içinde item "
                "ekliyorsanız o loop da bitmez.")


def run_child(task):
    """Görevin sonucunu döndürür; result["parts"], biten parçaların sonuçlarıdır."""
    env = dict(os.environ, PYTHONIOENCODING="utf-8", PYTHONUNBUFFERED="1")
    late = False
    try:
        done = subprocess.run([sys.executable, str(pathlib.Path(__file__).resolve()), "--gorev", str(task)],
                              capture_output=True, stdin=subprocess.DEVNULL, env=env, timeout=TIMEOUT, cwd=HERE)
        out, err = done.stdout, done.stderr
    except subprocess.TimeoutExpired as e:
        late, out, err = True, e.stdout or b"", e.stderr or b""
    parts = []
    result = None
    for line in out.decode("utf-8", errors="replace").splitlines():
        if not line.startswith(MARK):
            continue
        try:
            found = json.loads(line[len(MARK):])
        except ValueError:
            continue
        if "part" in found:
            parts.append(found)
        elif result is None:
            result = found
    if result is None:
        failed = [part for part in parts if not part["ok"]]
        if failed:
            # Yarıda kesilen bir görevin satırına da ilk ✗'in notu yazılır.
            result = {"ok": False, "note": failed[0]["note"]}
        elif late:
            result = {"timeout": True}
        else:
            lines = [ln for ln in err.decode("utf-8", errors="replace").splitlines() if ln.strip()]
            result = {"ok": False, "note": "kontrol tamamlanamadı. Error message'ın (hata mesajı) son satırı: "
                                           + (lines[-1] if lines else "(boş)")}
    result["parts"] = parts
    return result


def print_import_error(result):
    where = f"{result['line']}. satırında" if result.get("line") else "içinde"
    print(f"bank.py import edilirken hata verdi: file'ın {where} bir yanlış var. Error message'ın (hata mesajı) "
          "son satırı:")
    print("    " + result["import"])
    print("Önce bunu düzeltin, sonra kontrolü tekrar çalıştırın.")


def main():
    try:
        sys.stdout.reconfigure(errors="replace")
    except AttributeError:
        pass
    if not ENGINE.exists():
        print("bank.py bulunamadı. kontrol.py ile aynı klasöre koyun.")
        return
    first = run_child(0)
    if first.get("timeout"):
        print("bank.py import edilirken bitmedi; kontrol.py beklemeyi bıraktı. File'da, bir function'ın içinde "
              "olmayan bir satır hiç bitmiyor olabilir, en dışta kalmış bir while gibi. Önce bunu düzeltin, sonra "
              "kontrolü tekrar çalıştırın.")
        return
    if "import" in first:
        print_import_error(first)
        return
    if not first.get("ok"):
        print("bank.py import edilemedi: " + first.get("note", ""))
        return
    passed = 0
    for task, title in TASKS.items():
        result = run_child(task)
        if result.get("timeout"):
            result = {"ok": False, "note": TIMEOUT_NOTE, "parts": result["parts"]}
        if "import" in result:
            print_import_error(result)
            return
        if result["ok"]:
            print(f"✓ {title}")
            passed += 1
        else:
            names = [name for part in CHECKS[task]("") for name in part[0]]
            done = sum(len(part["part"]) for part in result["parts"] if part["ok"])
            print(f"✗ {title} ({done}/{len(names)} tamam): {' '.join(result['note'].split())}")
        if task == 5 and first.get("random") is False:
            print(RANDOM_WARNING)
    print(f"\n{passed} / {len(TASKS)} görev geçti.")


if __name__ == "__main__":
    if len(sys.argv) > 2 and sys.argv[1] == "--gorev":
        child(int(sys.argv[2]))
    else:
        main()
