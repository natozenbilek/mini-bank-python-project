# Bu file (dosya) hazır; değiştirmeniz gerekmiyor.
#
# app.py bankanızın uygulamasını çalıştırır. PyCharm'da bu file'ı açıp
# Run deyin; bankanız tarayıcınızda açılır. Durdurmak için PyCharm'daki
# kırmızı Stop düğmesine basın.
#
# Uygulama yalnız sizin bilgisayarınızda çalışır: 127.0.0.1 adresi
# bilgisayarınızın kendisi demek, internete bir şey gönderilmez. Ekrandaki
# her sayı bank.py'deki function'lardan (fonksiyon) geliyor.
# bank.py'yi değiştirip kaydettikten sonra tarayıcıda sayfayı yenilemeniz
# yeter; app.py'yi yeniden başlatmanız gerekmez.
#
# İçinde http.server, json ve importlib gibi derste görmediğimiz
# module'ler (modül) var; bu file'ı okumanız gerekmiyor.

import datetime
import dis
import http.server
import importlib
import json
import os
import pathlib
import secrets
import shutil
import sys
import threading
import time
import traceback
import types
import urllib.parse
import webbrowser

HERE = pathlib.Path(__file__).resolve().parent
DATA = HERE / "data"
UI = HERE / "ui"
sys.path.insert(0, str(HERE))
os.chdir(HERE)

import dates  # noqa: E402
import records  # noqa: E402

FILES = {
    "customers": DATA / "customers.csv",
    "accounts": DATA / "accounts.csv",
    "transactions": DATA / "transactions.csv",
    "cards": DATA / "cards.csv",
    "activity": DATA / "card_activity.csv",
    "rates": DATA / "rates.csv",
    "aliases": DATA / "aliases.csv",
    "orders": DATA / "orders.csv",
    "loans": DATA / "loans.csv",
    "budgets": DATA / "budgets.csv",
    "branches": DATA / "branches.csv",
}
TRANSACTIONS_HEADER = "date,sender,receiver,amount,description"
# What the student writes in bank.py, and in which task: the functions
# and the import lines at the top of the file.
TASK_OF = {
    "BANK_NAME": 1, "balances": 1, "account_history": 1, "owner_of": 1,
    "branch_report": 1, "password_ok": 2, "hash_password": 2,
    "register": 2, "login": 2, "change_password": 2, "iban_valid": 3,
    "mask_iban": 3, "resolve_receiver": 3, "save_transaction": 3,
    "Card": 4, "Card.available": 4, "Card.spend": 4, "Card.pay": 4,
    "replay_card": 4, "statement": 4, "payment_info": 4,
    "installments": 4, "category_totals": 4, "places": 4,
    "new_places": 4, "buy_foreign": 5, "sell_foreign": 5, "rate_text": 5,
    "loan_installment": 5, "months_to_goal": 5, "my_report": 5,
    "import security": 2, "import dates": 4,
}
# The ready functions at the end of bank.py ("Hazır function'lar"); the
# first four were the longest functions of tasks 1, 3 and 5. Three of
# them call a student's function and return None while it still does:
# their part waits for that function and its task (WAITS_FOR). transfer
# and atm_withdraw call several and never return None: their part waits
# while one of those is still empty, # TODO and pass as bank.py comes,
# and names the first one in NEEDS. Ready code that needs a module waits
# for that module's import line.
READY = ["load_transactions", "transfer", "due_orders", "atm_withdraw",
         "monthly_flow", "add_alias", "update_recent", "double_charges",
         "top_categories", "subscriptions", "budget_warnings",
         "spread_loss", "deposit_interest", "payment_plan",
         "upcoming_payments", "banknotes", "luhn_valid"]
WAITS_FOR = {"subscriptions": "places", "payment_plan": "loan_installment",
             "spread_loss": "buy_foreign"}
NEEDS = {"transfer": ["balances", "owner_of", "iban_valid",
                      "save_transaction"],
         "atm_withdraw": ["balances", "save_transaction"]}
# Two ready parts belong to a task whose functions they do not call; they
# wait for those the same way, before what NEEDS lists. The monthly in and
# out on Hesaplarım waits, like the accounts and the movements beside it,
# for balances and account_history (task 1); the ATM's withdrawal, like
# its tab, for every student function of task 5.
OPENS_WITH = {"monthly_flow": ["balances", "account_history"],
              "atm_withdraw": ["buy_foreign", "sell_foreign", "rate_text",
                               "loan_installment", "months_to_goal",
                               "my_report"]}
# "import random" is ready code's line at the top of bank.py, for the
# transaction number of atm_withdraw; the students do not write it. When
# it is gone, the ATM says so before atm_withdraw runs, so nothing is
# written; a NameError on random gets the same hint.
READY_IMPORTS = {"random": "atm_withdraw"}
CURRENCY_INDEX = {"TL": 1, "USD": 2, "EUR": 3}
DEFAULT_BRANCH = "0101"
CATEGORIES = ["market", "yemek", "ulaşım", "eğlence", "kitap", "giyim",
              "sağlık", "abonelik"]

# The docstring example of hash_password: login must say "ok" for it,
# otherwise task 2 is not done yet and the demo list stays open.
LOGIN_SALT = "9f2c41d07ab3e5c8"
LOGIN_HASH = ("8025d5c5cf79144e718eb9cbf17877f3"
              "f8de778b9daf9998e57e712d2c1debc1")

# A student function that runs longer than LIMIT seconds is stopped (an
# infinite loop would keep LOCK and freeze every page). A request waits
# at most LOCK_WAIT seconds for the one before it.
LIMIT = 5
LOCK_WAIT = 12
LOOP_NOTE = ("Bu function bitmedi, app.py onu yarıda kesti: içindeki bir "
             "loop (döngü) hiç bitmiyor olabilir. while'ın şartı bir "
             "noktada False oluyor mu, break satırına ulaşılıyor mu, "
             "bakın.")
IMPORT_LOOP_NOTE = ("bank.py import edilirken bitmedi, app.py onu yarıda "
                    "kesti: bir function'ın içinde olmayan bir satır hiç "
                    "bitmiyor olabilir, en dışta kalmış bir while gibi.")
STUCK_NOTE = ("Önceki istek bitmedi: bank.py'deki bir loop bitmiyor "
              "ya da bir input() cevap bekliyor olabilir. "
              "Düzeltin, sonra app.py'yi durdurup yeniden Run deyin.")
LOCKED_NOTE = ("başka bir programda (Excel gibi) açık olabilir; kapatıp "
               "yeniden deneyin.")
IMPORT_NOTE = (". bank.py'nin başına import {0} satırını yazın ({1}. "
               "görev).")
READY_NONE_NOTE = (". Hazır kodun çağırdığı function'larınızdan biri None "
                   "return ediyor olabilir; kontrol.py'yi çalıştırın.")
READY_IMPORT_NOTE = ("bank.py'nin başındaki import {0} satırı silinmiş. "
                     "Hazır {1} onu kullanıyor; satırı yerine geri koyun.")

LOCK = threading.Lock()
SESSIONS = {}
FAILED = {}
STATE = {"bank": None}
STOPPED = {}  # stopped in this request: {name: (function, line)}


class Todo(Exception):
    """A student function is still empty: it returned None."""

    def __init__(self, name):
        super().__init__(name)
        self.name = name


class StudentError(Exception):
    """A student function raised an error or returned the wrong thing."""

    def __init__(self, name, message, line=None):
        super().__init__(message)
        self.name = name
        self.message = message
        self.line = line


class Refusal(Exception):
    """The app itself refuses a request: wrong input, not logged in."""


class TooSlow(BaseException):
    """Raised inside a student function that runs longer than LIMIT. A
    BaseException, so that an "except Exception" in bank.py lets it
    through."""


def today():
    fixed = os.environ.get("MINIBANK_TODAY")
    if fixed:
        return fixed
    return datetime.date.today().isoformat()


def bank_line(error):
    """The line of bank.py where the error happened, or None."""
    if isinstance(error, SyntaxError) and error.filename and \
            error.filename.endswith("bank.py"):
        return error.lineno
    found = None
    for frame in traceback.extract_tb(error.__traceback__):
        if frame.filename.endswith("bank.py"):
            found = frame.lineno
    return found


def debugging():
    """True under a debugger (PyCharm's Debug): a pause at a breakpoint
    must not be taken for an infinite loop."""
    if sys.gettrace() is not None or "pydevd" in sys.modules:
        return True
    monitoring = getattr(sys, "monitoring", None)
    return monitoring is not None and \
        monitoring.get_tool(monitoring.DEBUGGER_ID) is not None


def run_student(func, args):
    """Runs func(*args) for at most LIMIT seconds: a trace function checks
    the clock on every line and raises TooSlow inside the student's code
    when the time is up."""
    if debugging():
        return func(*args)
    deadline = time.monotonic() + LIMIT

    def tracer(frame, event, arg):
        if time.monotonic() > deadline:
            raise TooSlow()
        return tracer

    sys.settrace(tracer)
    try:
        return func(*args)
    finally:
        sys.settrace(None)


def load_bank():
    """Imports bank.py from scratch, so the newest saved version is used.
    importlib.reload would keep a function that was deleted from bank.py.
    """
    sys.modules.pop("bank", None)
    STATE["bank"] = None
    try:
        STATE["bank"] = run_student(importlib.import_module, ("bank",))
    except TooSlow as error:
        sys.modules.pop("bank", None)
        raise StudentError("bank.py", IMPORT_LOOP_NOTE, bank_line(error))
    except Exception as error:
        sys.modules.pop("bank", None)
        raise StudentError("bank.py", f"bank.py import edilemedi: "
                           f"{type(error).__name__}: {error}",
                           bank_line(error))
    return STATE["bank"]


def describe(error):
    text = f"{type(error).__name__}: {error}"
    if isinstance(error, PermissionError):
        text += ". Bu file " + LOCKED_NOTE
    return text


def locked(error):
    """The message for a data file that app.py itself could not write."""
    name = "bir file"
    if getattr(error, "filename", None):
        name = pathlib.Path(error.filename).name
    return f"data klasöründeki {name} {LOCKED_NOTE}"


def generic(error):
    return (f"Beklenmeyen bir hata: {describe(error)}. bank.py'deki bir "
            "function beklenen biçimde bir değer return etmemiş olabilir; "
            "kontrol.py'yi çalıştırın.")


def missing_import(error):
    """The module whose import line bank.py lacks ("dates" for NameError:
    name 'dates' is not defined), or None."""
    if not isinstance(error, NameError) or \
            isinstance(error, UnboundLocalError):
        return None
    name = getattr(error, "name", None)
    if f"import {name}" in TASK_OF:
        return name
    return None


def ready_import(error):
    """The module of a ready import line that a NameError names ("random"
    for NameError: name 'random' is not defined), or None."""
    if not isinstance(error, NameError) or \
            isinstance(error, UnboundLocalError):
        return None
    name = getattr(error, "name", None)
    if name in READY_IMPORTS:
        return name
    return None


def in_ready_code(error):
    """True when the error happened in one of bank.py's ready functions."""
    name = None
    for frame in traceback.extract_tb(error.__traceback__):
        if frame.filename.endswith("bank.py"):
            name = frame.name
    return name in READY


def culprit(name, error):
    """The function an error is shown under: when a ready function called
    a student's function and the error happened in that one, the
    student's function; otherwise name."""
    if name not in READY:
        return name
    found = None
    for frame in traceback.extract_tb(error.__traceback__):
        if frame.filename.endswith("bank.py"):
            found = frame.name
    if found in TASK_OF:
        return found
    return name


def guarded(name, func, args):
    """Runs a student function; its errors become StudentError. A function
    stopped once in this request is not run again. A missing import line
    is named: ready code waits for it as for an empty function, the
    student's own code gets its error with a hint. A deleted ready import
    line gets the hint of READY_IMPORT_NOTE."""
    if name in STOPPED:
        function, line = STOPPED[name]
        raise StudentError(function, LOOP_NOTE, line)
    try:
        return run_student(func, args)
    except TooSlow as error:
        STOPPED[name] = (culprit(name, error), bank_line(error))
        raise StudentError(STOPPED[name][0], LOOP_NOTE, STOPPED[name][1])
    except Exception as error:
        module = missing_import(error)
        if module is not None and in_ready_code(error):
            raise Todo("import " + module)
        message = describe(error)
        deleted = ready_import(error)
        if module is not None:
            message += IMPORT_NOTE.format(module,
                                          TASK_OF["import " + module])
        elif deleted is not None:
            message += ". " + READY_IMPORT_NOTE.format(
                deleted, READY_IMPORTS[deleted])
        elif "NoneType" in message and in_ready_code(error):
            message += READY_NONE_NOTE
        raise StudentError(culprit(name, error), message, bank_line(error))


def empty(name):
    """True while a function of bank.py does nothing but return None, as
    bank.py comes: its body is still # TODO and pass."""
    code = getattr(getattr(STATE["bank"], name, None), "__code__", None)
    if code is None:
        return False
    for op in dis.get_instructions(code):
        if op.opname in ("RESUME", "NOP", "CACHE", "RETURN_VALUE"):
            continue
        if op.opname in ("LOAD_CONST", "RETURN_CONST") and \
                op.argval is None:
            continue
        return False
    return True


def needs(name):
    """A ready function of OPENS_WITH or NEEDS waits for the first student
    function there that is still empty, in that order. A ready function of
    READY_IMPORTS is not run without its module either."""
    for need in OPENS_WITH.get(name, []) + NEEDS.get(name, []):
        if empty(need):
            raise Todo(need)
    for module, user in READY_IMPORTS.items():
        found = getattr(STATE["bank"], module, None)
        if user == name and not isinstance(found, types.ModuleType):
            raise StudentError(name, READY_IMPORT_NOTE.format(module, name))


def call(name, *args, allow_none=False):
    """Calls a function of bank.py; turns None and errors into Todo and
    StudentError. A ready function returns None while the student's
    function it calls does; the Todo names that function. A ready
    function of OPENS_WITH or NEEDS is not run while one it waits for is
    still empty."""
    bank = STATE["bank"]
    func = getattr(bank, name, None)
    if func is None:
        raise StudentError(name, f"bank.py'de {name} adında bir function "
                           "yok. def satırının adını değiştirmeyin.")
    needs(name)
    result = guarded(name, func, args)
    if result is None and not allow_none:
        raise Todo(WAITS_FOR.get(name, name))
    return result


def method(card, name, *args):
    """Calls a method of the student's Card object."""
    func = getattr(card, name, None)
    if func is None:
        raise StudentError("Card." + name, f"Card'da {name} adında bir "
                           "method yok.")
    result = guarded("Card." + name, func, args)
    if result is None:
        raise Todo("Card." + name)
    return result


def expect(value, kind, name, what):
    if not isinstance(value, kind):
        raise StudentError(name, f"{name} {what} return etmeli; sizinki "
                           f"{type(value).__name__}: {short(value)}")
    return value


def short(value, limit=80):
    text = repr(value)
    if len(text) > limit:
        return text[:limit] + "..."
    return text


def task_of(name):
    """The task of a student's function or import line; a ready function
    that calls a student's function belongs to that function's task."""
    return TASK_OF.get(WAITS_FOR.get(name, name), 0)


def section(work):
    """Runs one part of a page; a missing task only hides that part."""
    try:
        value = work()
        json.dumps(value, ensure_ascii=False, allow_nan=False)
        return {"ok": value}
    except Todo as todo:
        return {"todo": {"task": task_of(todo.name),
                         "function": todo.name}}
    except StudentError as error:
        return {"error": {"task": task_of(error.name),
                          "function": error.name,
                          "message": error.message, "line": error.line}}
    except Refusal:
        raise
    except PermissionError as error:
        return {"error": {"task": 0, "function": "",
                          "message": locked(error), "line": None}}
    except Exception as error:
        return {"error": {"task": 0, "function": "",
                          "message": generic(error),
                          "line": bank_line(error)}}


def pair(value, name, what):
    """Checks that a student function returned a tuple of two items."""
    if not isinstance(value, tuple) or len(value) != 2:
        raise StudentError(name, f"{name} {what} return etmeli; sizinki: "
                           f"{short(value)}")
    return value


def whole(value):
    """An int, but not True or False."""
    return isinstance(value, int) and not isinstance(value, bool)


def checked_plan(plan):
    """Checks the rows of payment_plan before app.py reads them."""
    expect(plan, list, "payment_plan", "bir list")
    for row in plan:
        if not isinstance(row, tuple) or len(row) != 5:
            raise StudentError("payment_plan", "payment_plan'daki her item "
                               "(month, payment, interest, principal_part, "
                               f"remaining) tuple'ı olmalı; sizinki: "
                               f"{short(row)}")
    return plan


def line_count(path):
    """The number of non-empty lines of a data file."""
    count = 0
    with open(path, encoding="utf-8") as f:
        for line in f:
            if line.strip() != "":
                count += 1
    return count


def written(name, before):
    """After a successful transfer or ATM withdrawal transactions.csv must
    have a new line; otherwise save_transaction did not write it."""
    if line_count(FILES["transactions"]) <= before:
        raise StudentError("save_transaction", f"{name} (True, ...) return "
                           "etti ama transactions.csv'ye yeni bir satır "
                           f"yazılmadı. Hazır {name} hareketi "
                           "save_transaction ile yazıyor; save_transaction "
                           "(3. görev) file_name'i \"a\" moduyla açıp "
                           "sonuna bir satır eklemeli.")


# Reading the data

def transactions_of_bank():
    result = call("load_transactions", str(FILES["transactions"]))
    expect(result, tuple, "load_transactions", "bir (transactions, skipped) "
           "tuple'ı")
    if len(result) != 2 or not isinstance(result[0], list):
        raise StudentError("load_transactions", "load_transactions bir "
                           "(transactions, skipped) tuple'ı return etmeli; "
                           f"sizinki: {short(result)}")
    for row in result[0][:3]:
        if not isinstance(row, tuple) or len(row) != 5:
            raise StudentError("load_transactions", "transactions'daki her "
                               "item (date, sender, receiver, amount, "
                               "description) tuple'ı olmalı; sizinki: "
                               f"{short(row)}")
    return result


def balances_of(transactions):
    result = call("balances", transactions)
    return expect(result, dict, "balances", "bir dict")


def customer_accounts(customer_no):
    found = []
    for iban, owner, currency in records.load_accounts(FILES["accounts"]):
        if owner == customer_no:
            found.append((iban, currency))
    return found


def customer_cards(customer_no):
    found = []
    for card_id, owner, limit, cut_day in records.load_cards(FILES["cards"]):
        if owner == customer_no:
            found.append((card_id, limit, cut_day))
    return found


def card_of(customer_no, card_id):
    for found_id, limit, cut_day in customer_cards(customer_no):
        if found_id == card_id:
            return found_id, limit, cut_day
    raise Refusal("Bu kart sizin değil.")


def iban_of(customer_no, currency):
    for iban, found in customer_accounts(customer_no):
        if found == currency:
            return iban
    return None


def new_account(customer_no, currency):
    """Opens an account in the customer's branch (a new customer: 0101)."""
    bank = STATE["bank"]
    branch = DEFAULT_BRANCH
    tl_iban = iban_of(customer_no, "TL")
    if tl_iban is not None:
        branch = tl_iban[10:14]
    number = f"{branch}{customer_no:04d}{CURRENCY_INDEX[currency]:08d}"
    iban = records.make_iban(bank.BANK_CODE, number)
    records.add_line(FILES["accounts"], records.ACCOUNTS_HEADER,
                     (iban, customer_no, currency))
    return iban


def replayed_card(card_id, limit, activity):
    card = call("replay_card", card_id, limit, activity)
    if isinstance(card, STATE["bank"].Card) and \
            getattr(card, "debt", None) is None:
        raise Todo("Card")
    if not hasattr(card, "debt"):
        raise StudentError("replay_card", "replay_card bir Card return "
                           f"etmeli; sizinki: {short(card)}")
    return card


# Pages

def page_state(session):
    bank = STATE["bank"]
    name = getattr(bank, "BANK_NAME", "Örnek Bank")
    color = getattr(bank, "BANK_COLOR", "#2f5d8a")
    if not isinstance(name, str) or name.strip() == "":
        name = "Örnek Bank"
    if not isinstance(color, str) or len(color) != 7 or color[0] != "#":
        color = "#2f5d8a"
    customer = None
    if session in SESSIONS:
        number = SESSIONS[session]
        people = records.load_customers(FILES["customers"])
        if number in people:
            customer = {"no": number, "name": people[number][0]}
    ready = login_ready()
    demo = []
    if "ok" not in ready:
        for number, row in records.load_customers(
                FILES["customers"]).items():
            demo.append({"no": number, "name": row[0]})
    return {"bank_name": name, "bank_color": color, "today": today(),
            "customer": customer, "login": ready, "demo": demo}


def login_ready():
    """Task 2 is done when login says "ok" for the docstring example of
    hash_password. Until then the login part waits and the demo list
    stays open, so the other tabs can still be used."""
    def work():
        status = call("login", {1: ("x", LOGIN_SALT, LOGIN_HASH)}, {}, 1,
                      "kedi123")
        if status != "ok":
            raise StudentError("login", "hash_password ya da login henüz "
                               "doğru çalışmıyor: doğru şifre denenince "
                               f"login {short(status)} return etti, \"ok\" "
                               "olmalı. kontrol.py'yi çalıştırın.")
        return status
    return section(work)


def run_orders(customer_no):
    """Pays this customer's standing orders that are due today. The part
    waits for what transfer calls even on a day with no order due."""
    needs("transfer")
    transactions, skipped = transactions_of_bank()
    mine = [iban for iban, currency in customer_accounts(customer_no)]
    orders = []
    for order in records.load_orders(FILES["orders"]):
        if order[0] in mine:
            orders.append(order)
    due = call("due_orders", orders, transactions, today())
    expect(due, list, "due_orders", "bir list")
    done = []
    for order in due:
        sender, day, receiver, amount, description = order
        result = pair(call("transfer", transactions,
                           records.load_accounts(FILES["accounts"]),
                           str(FILES["transactions"]), today(), sender,
                           receiver, amount, description),
                      "transfer", "bir (ok, message) tuple'ı")
        done.append({"description": description, "amount": amount,
                     "receiver": receiver, "ok": bool(result[0]),
                     "message": str(result[1])})
    return done


def page_accounts(customer_no):
    orders = section(lambda: run_orders(customer_no))

    def work():
        transactions, skipped = transactions_of_bank()
        money = balances_of(transactions)
        accounts = []
        for iban, currency in customer_accounts(customer_no):
            accounts.append({"iban": iban, "currency": currency,
                             "balance": money.get(iban, 0)})
        return {"accounts": accounts, "skipped": skipped}

    def history():
        transactions, skipped = transactions_of_bank()
        result = {}
        for iban, currency in customer_accounts(customer_no):
            found = call("account_history", transactions, iban)
            expect(found, list, "account_history", "bir list")
            rows = []
            for row in found:
                if not isinstance(row, tuple) or len(row) != 4:
                    raise StudentError("account_history", "account_history'"
                                       "deki her item (date, other, amount,"
                                       " description) tuple'ı olmalı; "
                                       f"sizinki: {short(row)}")
                date, other, amount, description = row
                rows.append({"date": date, "other": other,
                             "amount": amount, "description": description})
            result[iban] = rows
        return result

    def flow():
        transactions, skipped = transactions_of_bank()
        result = {}
        for iban, currency in customer_accounts(customer_no):
            found = call("monthly_flow", transactions, iban)
            expect(found, dict, "monthly_flow", "bir dict")
            months = []
            for month in sorted(found):
                money_in, money_out = pair(found[month], "monthly_flow",
                                           "her ay için bir (giren, çıkan) "
                                           "tuple'ı")
                months.append({"month": month, "in": money_in,
                               "out": money_out})
            result[iban] = months
        return result
    aliases = []
    for alias, iban in records.load_aliases(FILES["aliases"]).items():
        if (iban, "TL") in customer_accounts(customer_no):
            aliases.append({"alias": alias, "iban": iban})
    tl_iban = iban_of(customer_no, "TL")
    branch = {"code": "", "name": ""}
    if tl_iban is not None:
        code = tl_iban[10:14]
        branch = {"code": code, "name": records.load_branches(
            FILES["branches"]).get(code, code)}
    return {"orders_run": orders, "accounts": section(work),
            "history": section(history), "flow": section(flow),
            "aliases": aliases, "branch": branch,
            "recent": section(lambda: recent_of(customer_no))}


def names_by_iban():
    people = records.load_customers(FILES["customers"])
    names = {}
    for iban, owner, currency in records.load_accounts(FILES["accounts"]):
        if owner in people:
            names[iban] = people[owner][0]
    return names


def recent_of(customer_no):
    """The last receivers, built with the student's update_recent."""
    transactions, skipped = transactions_of_bank()
    mine = [iban for iban, currency in customer_accounts(customer_no)]
    recent = []
    for date, sender, receiver, amount, description in transactions:
        if sender in mine and receiver[:2] == "TR" and \
                receiver not in mine:
            recent = call("update_recent", recent, receiver)
            expect(recent, list, "update_recent", "bir list")
    names = names_by_iban()
    rows = []
    for iban in recent:
        masked = call("mask_iban", iban)
        rows.append({"iban": iban, "masked": masked,
                     "name": names.get(iban, "")})
    return rows


def page_branches():
    def work():
        transactions, skipped = transactions_of_bank()
        money = balances_of(transactions)
        report = call("branch_report",
                      records.load_accounts(FILES["accounts"]), money)
        expect(report, list, "branch_report", "bir list")
        names = records.load_branches(FILES["branches"])
        rows = []
        for row in report:
            if not isinstance(row, tuple) or len(row) != 3:
                raise StudentError("branch_report", "branch_report'taki her "
                                   "item (branch, customers, total) tuple'ı "
                                   f"olmalı; sizinki: {short(row)}")
            if not whole(row[1]):
                raise StudentError("branch_report", "customers, şubenin "
                                   "müşteri sayısı, bir int olmalı: set'in "
                                   "kendisini değil, len() ile büyüklüğünü "
                                   f"koyun. Sizinki: {short(row[1])}")
            if not whole(row[2]):
                raise StudentError("branch_report", "total, şubenin TL "
                                   "hesaplarındaki toplam para, bir int "
                                   f"olmalı; sizinki: {short(row[2])}")
            rows.append({"code": row[0], "name": names.get(row[0], row[0]),
                         "customers": row[1], "total": row[2]})
        return rows
    return {"branches": section(work)}


def page_orders(customer_no):
    mine = [iban for iban, currency in customer_accounts(customer_no)]
    rows = []
    for sender, day, receiver, amount, description in records.load_orders(
            FILES["orders"]):
        if sender in mine:
            rows.append({"sender": sender, "day": day, "receiver": receiver,
                         "amount": amount, "description": description})
    return {"orders": rows}


def page_cards(customer_no):
    result = {"cards": []}
    activity = records.load_card_activity(FILES["activity"])
    for card_id, limit, cut_day in customer_cards(customer_no):
        def state(card_id=card_id, limit=limit):
            card = replayed_card(card_id, limit, activity)
            available = method(card, "available")
            return {"debt": card.debt, "available": available}

        def bill(card_id=card_id, cut_day=cut_day):
            start, end = dates.statement_period(cut_day, today())
            lines, total = pair(call("statement", activity, card_id, start,
                                     end), "statement",
                                "bir (lines, total) tuple'ı")
            if not isinstance(lines, list):
                raise StudentError("statement", "statement'ın lines'ı bir "
                                   f"list olmalı; sizinki: {short(lines)}")
            rows = []
            for line in lines:
                if not isinstance(line, tuple) or len(line) != 3:
                    raise StudentError("statement", "statement'ın lines'ındaki"
                                       " her item (date, merchant, amount) "
                                       "tuple'ı olmalı; sizinki: "
                                       f"{short(line)}")
                date, merchant, amount = line
                rows.append({"date": date, "merchant": merchant,
                             "amount": amount})
            minimum, due = pair(call("payment_info", total, end),
                                "payment_info", "bir (minimum, due) tuple'ı")
            return {"start": start, "end": end, "lines": rows,
                    "total": total, "minimum": minimum, "due": due}

        def doubles(card_id=card_id):
            found = call("double_charges", activity, card_id)
            expect(found, list, "double_charges", "bir list")
            rows = []
            for row in found:
                if not isinstance(row, tuple) or len(row) != 3:
                    raise StudentError("double_charges", "double_charges'"
                                       "taki her item (date, merchant, "
                                       "amount) tuple'ı olmalı; sizinki: "
                                       f"{short(row)}")
                rows.append({"date": row[0], "merchant": row[1],
                             "amount": row[2]})
            return rows
        result["cards"].append({"card_id": card_id, "limit": limit,
                                "cut_day": cut_day, "state": section(state),
                                "statement": section(bill),
                                "doubles": section(doubles)})
    return result


def card_bills(customer_no, activity):
    bills = []
    for card_id, limit, cut_day in customer_cards(customer_no):
        start, end = dates.statement_period(cut_day, today())
        lines, total = pair(call("statement", activity, card_id, start, end),
                            "statement", "bir (lines, total) tuple'ı")
        minimum, due = pair(call("payment_info", total, end),
                            "payment_info", "bir (minimum, due) tuple'ı")
        bills.append((card_id, due, minimum))
    return bills


def page_loans(customer_no):
    loans = []
    for loan in records.load_loans(FILES["loans"]):
        if loan[1] == customer_no:
            loans.append(loan)

    def details():
        rows = []
        for loan_id, owner, principal, rate, months, start in loans:
            payment = call("loan_installment", principal, rate, months)
            plan = checked_plan(call("payment_plan", principal, rate,
                                     months))
            paid = 0
            remaining = principal
            for row in plan:
                if dates.add_months(start, row[0]) <= today():
                    paid += 1
                    remaining = row[4]
            rows.append({"loan_id": loan_id, "principal": principal,
                         "rate": rate, "months": months, "start": start,
                         "payment": payment, "paid": paid,
                         "remaining": remaining})
        return rows

    def upcoming():
        activity = records.load_card_activity(FILES["activity"])
        bills = card_bills(customer_no, activity)
        plans = []
        for loan_id, owner, principal, rate, months, start in loans:
            plan = checked_plan(call("payment_plan", principal, rate,
                                     months))
            plans.append((loan_id, start, plan))
        found = call("upcoming_payments", bills, plans, today(), 30)
        expect(found, list, "upcoming_payments", "bir list")
        rows = []
        for row in found:
            if not isinstance(row, tuple) or len(row) != 3:
                raise StudentError("upcoming_payments", "upcoming_payments'"
                                   "taki her item (date, what, amount) "
                                   f"tuple'ı olmalı; sizinki: {short(row)}")
            rows.append({"date": row[0], "what": row[1], "amount": row[2]})
        return rows
    return {"loans": section(details), "upcoming": section(upcoming)}


def page_fx(customer_no):
    rates = records.load_rates(FILES["rates"])
    rows = []
    for currency in ["USD", "EUR"]:
        found = records.latest_rate(rates, currency, today())
        if found is not None:
            rows.append({"currency": currency, "date": found[0],
                         "buy": found[1], "sell": found[2]})

    def texts():
        result = []
        for row in rows:
            text = call("rate_text", row["currency"], row["buy"],
                        row["sell"])
            expect(text, str, "rate_text", "bir str")
            result.append(text)
        return result
    return {"rates": rows, "texts": section(texts),
            "categories": CATEGORIES}


def page_breakdown(customer_no, card_id):
    card_id, limit, cut_day = card_of(customer_no, card_id)
    activity = records.load_card_activity(FILES["activity"])
    months = dates.month_names(today(), 3)

    def totals():
        result = []
        for month in months:
            found = call("category_totals", activity, card_id, month)
            expect(found, dict, "category_totals", "bir dict")
            top = call("top_categories", found, 3)
            expect(top, list, "top_categories", "bir list")
            result.append({"month": month, "totals": found,
                           "top": [list(pair) for pair in top]})
        return result

    def subs():
        found = call("subscriptions", activity, card_id, months)
        expect(found, set, "subscriptions", "bir set")
        return sorted(found)

    def fresh():
        found = call("new_places", activity, card_id, months[-1],
                     months[:-1])
        expect(found, set, "new_places", "bir set")
        return sorted(found)

    budgets = records.load_budgets(FILES["budgets"]).get(customer_no, {})

    def warnings():
        result = []
        for month in months:
            found = call("category_totals", activity, card_id, month)
            rows = call("budget_warnings", found, budgets)
            expect(rows, list, "budget_warnings", "bir list")
            items = []
            for row in rows:
                if not isinstance(row, tuple) or len(row) != 4:
                    raise StudentError("budget_warnings", "budget_warnings'"
                                       "deki her item (category, spent, "
                                       "budget, percent) tuple'ı olmalı; "
                                       f"sizinki: {short(row)}")
                items.append({"category": row[0], "spent": row[1],
                              "budget": row[2], "percent": row[3]})
            result.append({"month": month, "warnings": items})
        return result
    return {"card_id": card_id, "months": months, "totals": section(totals),
            "subscriptions": section(subs), "new_places": section(fresh),
            "budgets": budgets, "warnings": section(warnings)}


def page_report(customer_no):
    def work():
        transactions, skipped = transactions_of_bank()
        mine = []
        ibans = [iban for iban, currency in customer_accounts(customer_no)]
        for row in transactions:
            if row[1] in ibans or row[2] in ibans:
                mine.append(row)
        cards = [card_id for card_id, l, c in customer_cards(customer_no)]
        activity = []
        for row in records.load_card_activity(FILES["activity"]):
            if row[1] in cards:
                activity.append(row)
        result = call("my_report", mine, activity)
        if not isinstance(result, tuple) or len(result) != 2 or \
                not isinstance(result[0], str) or \
                not isinstance(result[1], list):
            raise StudentError("my_report", "my_report bir (title, rows) "
                               "tuple'ı return etmeli: title bir str, rows "
                               f"bir list. Sizinki: {short(result)}")
        rows = []
        for row in result[1]:
            if isinstance(row, (tuple, list)):
                rows.append([str(item) for item in row])
            else:
                rows.append([str(row)])
        return {"title": result[0], "rows": rows}
    return {"report": section(work)}


# Actions

def number_text(value):
    """12000 -> 12.000, as Turkish writes it."""
    text = f"{value:,}" if isinstance(value, int) else str(value)
    return text.replace(",", ".")


def text_field(body, key, label, limit):
    value = str(body.get(key, "")).strip().replace(",", " ")
    if value == "":
        raise Refusal(f"{label} boş kalmamalı.")
    if len(value) > limit:
        raise Refusal(f"{label} en fazla {limit} karakter olmalı.")
    return value


def int_field(body, key, label, low, high):
    try:
        value = int(str(body.get(key, "")).strip())
    except ValueError:
        raise Refusal(f"{label} için bir tam sayı yazın.")
    if value < low or value > high:
        raise Refusal(f"{label} {number_text(low)} ile {number_text(high)} "
                      "arasında olmalı.")
    return value


def float_field(body, key, label, low, high):
    try:
        value = float(str(body.get(key, "")).replace(",", ".").strip())
    except ValueError:
        raise Refusal(f"{label} için bir sayı yazın.")
    if value < low or value > high:
        raise Refusal(f"{label} {number_text(low)} ile {number_text(high)} "
                      "arasında olmalı.")
    return value


def do_login(body):
    number = int_field(body, "customer_no", "Müşteri numarası", 1, 999999)
    password = str(body.get("password", ""))
    customers = records.load_customers(FILES["customers"])
    status = call("login", customers, FAILED, number, password)
    messages = {
        "ok": "Hoş geldiniz.",
        "wrong": "Şifre yanlış. Üst üste 3 yanlış denemede hesap kilitlenir.",
        "locked": "Hesap kilitli: üst üste 3 yanlış deneme oldu. Kilit, "
                  "app.py'yi yeniden başlatınca ya da verileri ilk haline "
                  "döndürünce açılır.",
        "unknown": "Bu numarayla bir müşteri yok.",
    }
    if status not in messages:
        raise StudentError("login", "login \"ok\", \"wrong\", \"locked\" ya "
                           f"da \"unknown\" return etmeli; sizinki: "
                           f"{short(status)}")
    session = None
    if status == "ok":
        session = secrets.token_hex(16)
        SESSIONS[session] = number
    return {"status": status, "message": messages[status],
            "session": session}


def do_demo_login(body):
    if "ok" in login_ready():
        raise Refusal("2. görev yazıldı; numaranız ve şifrenizle girin.")
    number = int_field(body, "customer_no", "Müşteri numarası", 1, 999999)
    if number not in records.load_customers(FILES["customers"]):
        raise Refusal("Bu numarayla bir müşteri yok.")
    session = secrets.token_hex(16)
    SESSIONS[session] = number
    return {"status": "ok", "session": session}


def do_register(body):
    name = text_field(body, "name", "Ad", 20)
    password = str(body.get("password", ""))
    good, message = pair(call("password_ok", password, name), "password_ok",
                         "bir (ok, message) tuple'ı")
    if not good:
        return {"ok": False, "message": str(message)}
    customers = records.load_customers(FILES["customers"])
    before = len(customers)
    number = call("register", customers, name, password,
                  str(FILES["customers"]))
    if not isinstance(number, int):
        raise StudentError("register", "register yeni müşterinin numarasını "
                           f"int olarak return etmeli; sizinki: "
                           f"{short(number)}")
    again = records.load_customers(FILES["customers"])
    if number not in again:
        raise StudentError("register", "register yeni müşteriyi "
                           "customers.csv'ye yazmadı.")
    if len(again) != before + 1:
        raise StudentError("register", "register customers.csv'deki eski "
                           f"müşterileri sildi: file'da {len(again)} müşteri "
                           f"var, {before + 1} olmalı. file_name'i \"a\" "
                           "moduyla açın, sonra verileri ilk haline "
                           "döndürün.")
    iban = new_account(number, "TL")
    records.add_line(FILES["transactions"], TRANSACTIONS_HEADER,
                     (today(), "NAKIT", iban, 1000, "Hoş geldin hediyesi"))
    return {"ok": True, "customer_no": number, "iban": iban}


def do_password(customer_no, body):
    old = str(body.get("old", ""))
    new = str(body.get("new", ""))
    customers = records.load_customers(FILES["customers"])
    name = customers[customer_no][0]
    good, message = pair(call("password_ok", new, name), "password_ok",
                         "bir (ok, message) tuple'ı")
    if not good:
        return {"ok": False, "message": str(message)}
    changed = call("change_password", customers, customer_no, old, new,
                   str(FILES["customers"]))
    if changed is not True:
        return {"ok": False, "message": "Eski şifre yanlış."}
    again = records.load_customers(FILES["customers"])
    if len(again) != len(customers):
        raise StudentError("change_password", "change_password customers.csv"
                           "'ye bütün müşterileri yazmadı: file'da "
                           f"{len(again)} müşteri var, {len(customers)} "
                           "olmalı.")
    return {"ok": True, "message": "Şifreniz değişti."}


def do_transfer(customer_no, body):
    sender = str(body.get("sender", ""))
    if (sender, "TL") not in customer_accounts(customer_no):
        raise Refusal("Yalnız kendi TL hesabınızdan gönderebilirsiniz.")
    aliases = records.load_aliases(FILES["aliases"])
    receiver = call("resolve_receiver", aliases, str(body.get("receiver", "")))
    expect(receiver, str, "resolve_receiver", "bir str")
    only_tl(receiver)
    amount = int_field(body, "amount", "Tutar", -10 ** 9, 10 ** 9)
    description = text_field(body, "description", "Açıklama", 40)
    transactions, skipped = transactions_of_bank()
    before = line_count(FILES["transactions"])
    result = call("transfer", transactions,
                  records.load_accounts(FILES["accounts"]),
                  str(FILES["transactions"]), today(), sender, receiver,
                  amount, description)
    pair(result, "transfer", "bir (ok, message) tuple'ı")
    if result[0]:
        written("transfer", before)
    return {"ok": bool(result[0]), "message": str(result[1]),
            "receiver": receiver}


def currency_of(iban):
    """The currency of an account of our bank; None for any other IBAN."""
    for found, owner, currency in records.load_accounts(FILES["accounts"]):
        if found == iban:
            return currency
    return None


def only_tl(receiver):
    """Money in TL goes only to TL accounts: transfer adds the amount to
    the receiver's balance as it is, whatever its currency."""
    currency = currency_of(receiver)
    if currency is not None and currency != "TL":
        raise Refusal("Yalnız TL hesaplarına para gönderebilirsiniz.")


def do_order_add(customer_no, body):
    sender = str(body.get("sender", ""))
    if (sender, "TL") not in customer_accounts(customer_no):
        raise Refusal("Talimat yalnız kendi TL hesabınızdan verilir.")
    aliases = records.load_aliases(FILES["aliases"])
    receiver = call("resolve_receiver", aliases, str(body.get("receiver", "")))
    if not call("iban_valid", receiver):
        return {"ok": False, "message": "Alıcının IBAN'ı geçersiz."}
    only_tl(receiver)
    day = int_field(body, "day", "Gün", 1, 28)
    amount = int_field(body, "amount", "Tutar", 1, 10 ** 6)
    description = text_field(body, "description", "Açıklama", 40)
    records.add_line(FILES["orders"], records.ORDERS_HEADER,
                     (sender, day, receiver, amount, description))
    return {"ok": True, "message": f"Talimat eklendi: her ayın {day}. günü "
            f"{amount} TL."}


def do_iban_check(body):
    aliases = records.load_aliases(FILES["aliases"])
    iban = call("resolve_receiver", aliases, str(body.get("iban", "")))
    expect(iban, str, "resolve_receiver", "bir str")
    valid = call("iban_valid", iban)
    same_bank = iban[4:9] == STATE["bank"].BANK_CODE
    answer = {"valid": bool(valid), "iban": iban, "same_bank": same_bank,
              "name": "", "masked": "", "branch": "", "currency": ""}
    if valid and same_bank:
        answer["currency"] = currency_of(iban) or ""
    if valid and same_bank and answer["currency"] in ("", "TL"):
        answer["name"] = names_by_iban().get(iban, "")
        answer["masked"] = call("mask_iban", iban)
        answer["branch"] = records.load_branches(FILES["branches"]).get(
            iban[10:14], iban[10:14])
    return answer


def do_card_spend(customer_no, body):
    card_id, limit, cut_day = card_of(customer_no, str(body.get("card_id")))
    merchant = text_field(body, "merchant", "İşyeri", 30)
    category = str(body.get("category", ""))
    if category not in CATEGORIES:
        raise Refusal("Bir kategori seçin.")
    amount = int_field(body, "amount", "Tutar", 1, 10 ** 7)
    activity = records.load_card_activity(FILES["activity"])
    card = replayed_card(card_id, limit, activity)
    if not method(card, "spend", amount):
        return {"ok": False, "message": "Kullanılabilir limit yetmiyor."}
    records.add_line(FILES["activity"], records.ACTIVITY_HEADER,
                     (today(), card_id, "spend", merchant, category, amount))
    return {"ok": True, "message": "Harcama yapıldı."}


def do_card_pay(customer_no, body):
    card_id, limit, cut_day = card_of(customer_no, str(body.get("card_id")))
    amount = int_field(body, "amount", "Tutar", 1, 10 ** 7)
    iban = iban_of(customer_no, "TL")
    transactions, skipped = transactions_of_bank()
    if balances_of(transactions).get(iban, 0) < amount:
        return {"ok": False, "message": "TL hesabınızın bakiyesi yetmiyor."}
    activity = records.load_card_activity(FILES["activity"])
    card = replayed_card(card_id, limit, activity)
    if not method(card, "pay", amount):
        return {"ok": False, "message": "Borçtan fazla ödeyemezsiniz."}
    records.add_line(FILES["activity"], records.ACTIVITY_HEADER,
                     (today(), card_id, "payment", "-", "-", amount))
    records.add_line(FILES["transactions"], TRANSACTIONS_HEADER,
                     (today(), iban, "KART-" + card_id, amount,
                      "Kart ödemesi"))
    return {"ok": True, "message": "Ödeme yapıldı."}


def rate_of(currency):
    if currency not in ("USD", "EUR"):
        raise Refusal("Döviz USD ya da EUR olmalı.")
    found = records.latest_rate(records.load_rates(FILES["rates"]),
                                currency, today())
    if found is None:
        raise Refusal("Bu tarih için kur yok.")
    return found


def bought(tl_amount, sell):
    """buy_foreign's (units, cost); both must be int before they are
    shown or written to transactions.csv."""
    units, cost = pair(call("buy_foreign", tl_amount, sell), "buy_foreign",
                       "bir (units, cost) tuple'ı")
    if not whole(units) or not whole(cost):
        raise StudentError("buy_foreign", "buy_foreign'ın units'i ve cost'u "
                           "int olmalı: units = int(tl_amount // "
                           "sell_rate), cost = round(units * sell_rate). "
                           f"Sizinki: {short((units, cost))}")
    return units, cost


def sold(units, buy):
    """sell_foreign's TL, which must be an int too."""
    tl = call("sell_foreign", units, buy)
    if not whole(tl):
        raise StudentError("sell_foreign", "sell_foreign int return etmeli: "
                           "round(units * buy_rate). Sizinki: "
                           f"{short(tl)}")
    return tl


def do_fx_quote(body):
    currency = str(body.get("currency", ""))
    tl_amount = int_field(body, "tl_amount", "TL tutarı", 1, 10 ** 7)
    date, buy, sell = rate_of(currency)
    units, cost = bought(tl_amount, sell)
    back = sold(units, buy)
    loss = call("spread_loss", tl_amount, buy, sell)
    return {"currency": currency, "date": date, "buy": buy, "sell": sell,
            "units": units, "cost": cost, "back": back, "loss": loss}


def do_fx_buy(customer_no, body):
    currency = str(body.get("currency", ""))
    tl_amount = int_field(body, "tl_amount", "TL tutarı", 1, 10 ** 7)
    date, buy, sell = rate_of(currency)
    units, cost = bought(tl_amount, sell)
    if units < 1:
        return {"ok": False, "message": "Bu para bir birime yetmiyor."}
    tl_iban = iban_of(customer_no, "TL")
    transactions, skipped = transactions_of_bank()
    if balances_of(transactions).get(tl_iban, 0) < cost:
        return {"ok": False, "message": "TL hesabınızın bakiyesi yetmiyor."}
    fx_iban = iban_of(customer_no, currency)
    if fx_iban is None:
        fx_iban = new_account(customer_no, currency)
    text = f"{currency} alımı"
    records.add_line(FILES["transactions"], TRANSACTIONS_HEADER,
                     (today(), tl_iban, "DOVIZ", cost, text))
    records.add_line(FILES["transactions"], TRANSACTIONS_HEADER,
                     (today(), "DOVIZ", fx_iban, units, text))
    return {"ok": True, "message": f"{units} {currency} alındı, {cost} TL "
            "ödendi."}


def do_fx_sell(customer_no, body):
    currency = str(body.get("currency", ""))
    units = int_field(body, "units", "Döviz miktarı", 1, 10 ** 7)
    date, buy, sell = rate_of(currency)
    fx_iban = iban_of(customer_no, currency)
    if fx_iban is None:
        return {"ok": False, "message": f"{currency} hesabınız yok."}
    transactions, skipped = transactions_of_bank()
    if balances_of(transactions).get(fx_iban, 0) < units:
        return {"ok": False, "message": f"{currency} hesabınızda bu kadar "
                "yok."}
    tl = sold(units, buy)
    text = f"{currency} satışı"
    records.add_line(FILES["transactions"], TRANSACTIONS_HEADER,
                     (today(), fx_iban, "DOVIZ", units, text))
    records.add_line(FILES["transactions"], TRANSACTIONS_HEADER,
                     (today(), "DOVIZ", iban_of(customer_no, "TL"), tl, text))
    return {"ok": True, "message": f"{units} {currency} bozduruldu, {tl} TL "
            "hesabınıza geçti."}


def do_loan(body):
    principal = int_field(body, "principal", "Kredi tutarı", 1000, 10 ** 7)
    rate = float_field(body, "rate", "Aylık faiz", 0.01, 20)
    months = int_field(body, "months", "Vade", 1, 120)
    payment = call("loan_installment", principal, rate, months)
    plan = checked_plan(call("payment_plan", principal, rate, months))
    rows = []
    for row in plan:
        month, paid, interest, part, remaining = row
        rows.append({"month": month,
                     "date": dates.add_months(today(), month),
                     "payment": paid, "interest": interest,
                     "principal_part": part, "remaining": remaining})
    total = 0
    for row in rows:
        total += row["payment"]
    return {"payment": payment, "plan": rows, "total": total,
            "interest": total - principal}


def do_alias_add(customer_no, body):
    iban = iban_of(customer_no, "TL")
    aliases = records.load_aliases(FILES["aliases"])
    result = pair(call("add_alias", aliases, str(body.get("alias", "")),
                       iban, str(FILES["aliases"])),
                  "add_alias", "bir (ok, message) tuple'ı")
    return {"ok": bool(result[0]), "message": str(result[1])}


def do_atm(customer_no, body):
    amount = int_field(body, "amount", "Tutar", -10 ** 7, 10 ** 7)
    iban = iban_of(customer_no, "TL")
    transactions, skipped = transactions_of_bank()
    before = line_count(FILES["transactions"])
    result = pair(call("atm_withdraw", transactions,
                       str(FILES["transactions"]), today(), iban, amount),
                  "atm_withdraw", "bir (ok, message) tuple'ı")
    notes = []
    if result[0]:
        written("atm_withdraw", before)
        found = call("banknotes", amount)
        expect(found, list, "banknotes", "bir list")
        for row in found:
            if not isinstance(row, tuple) or len(row) != 2:
                raise StudentError("banknotes", "banknotes'taki her item "
                                   "(note, count) tuple'ı olmalı; sizinki: "
                                   f"{short(row)}")
            notes.append({"note": row[0], "count": row[1]})
    return {"ok": bool(result[0]), "message": str(result[1]),
            "notes": notes}


def do_card_number(body):
    valid = call("luhn_valid", str(body.get("number", "")))
    return {"valid": bool(valid)}


def do_goal(body):
    goal = int_field(body, "goal", "Hedef", 1, 10 ** 8)
    monthly = int_field(body, "monthly", "Aylık birikim", 1, 10 ** 7)
    rate = float_field(body, "rate", "Aylık faiz", 0, 20)
    if goal > monthly * 1200:
        raise Refusal("Bu aylık birikimle hedefe 100 yılda da "
                      "ulaşılmıyor; aylık birikimi artırın.")
    months = call("months_to_goal", goal, monthly, rate)
    return {"months": months}


def do_installments(body):
    amount = int_field(body, "amount", "Tutar", 1, 10 ** 7)
    count = int_field(body, "count", "Taksit sayısı", 1, 36)
    parts = call("installments", amount, count)
    expect(parts, list, "installments", "bir list")
    return {"parts": parts}


def do_deposit(body):
    principal = int_field(body, "principal", "Yatırılan para", 100, 10 ** 8)
    rate = float_field(body, "rate", "Yıllık faiz", 0.01, 200)
    days = int_field(body, "days", "Vade", 1, 3650)
    result = call("deposit_interest", principal, rate, days)
    if not isinstance(result, tuple) or len(result) != 3:
        raise StudentError("deposit_interest", "deposit_interest bir (gross,"
                           f" tax, net) tuple'ı return etmeli; sizinki: "
                           f"{short(result)}")
    gross, tax, net = result
    return {"gross": gross, "tax": tax, "net": net,
            "total": principal + net}


def do_budget_set(customer_no, body):
    category = str(body.get("category", ""))
    if category not in CATEGORIES:
        raise Refusal("Bir kategori seçin.")
    amount = int_field(body, "amount", "Bütçe", 0, 10 ** 7)
    budgets = records.load_budgets(FILES["budgets"])
    mine = budgets.get(customer_no, {})
    if amount == 0:
        mine.pop(category, None)
    else:
        mine[category] = amount
    budgets[customer_no] = mine
    records.save_budgets(FILES["budgets"], budgets)
    return {"ok": True, "message": "Bütçe kaydedildi."}


def do_reset():
    for name in FILES:
        shutil.copyfile(DATA / "initial" / FILES[name].name, FILES[name])
    SESSIONS.clear()
    FAILED.clear()
    return {"ok": True}


# The web server

STATIC = {"/": ("index.html", "text/html; charset=utf-8"),
          "/app.js": ("app.js", "text/javascript; charset=utf-8"),
          "/style.css": ("style.css", "text/css; charset=utf-8")}


class Handler(http.server.BaseHTTPRequestHandler):

    def log_message(self, format, *args):
        pass

    def send(self, status, body, kind):
        try:
            self.send_response(status)
            self.send_header("Content-Type", kind)
            self.send_header("Cache-Control", "no-store")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
        except ConnectionError:
            pass  # the page stopped waiting (it waits 20 s at most)

    def send_json(self, value):
        body = json.dumps(value, ensure_ascii=False).encode("utf-8")
        self.send(200, body, "application/json; charset=utf-8")

    def session(self):
        return self.headers.get("X-Session", "")

    def do_GET(self):
        url = urllib.parse.urlparse(self.path)
        if url.path in STATIC:
            name, kind = STATIC[url.path]
            self.send(200, (UI / name).read_bytes(), kind)
            return
        query = dict(urllib.parse.parse_qsl(url.query))
        self.api(url.path, query)

    def do_POST(self):
        length = int(self.headers.get("Content-Length", "0"))
        try:
            body = json.loads(self.rfile.read(length) or b"{}")
        except ValueError:
            body = {}
        self.api(urllib.parse.urlparse(self.path).path, body)

    def api(self, path, body):
        # One request at a time. If the one before never ends (an input()
        # in bank.py waits, or a loop under the debugger), answer anyway.
        if not LOCK.acquire(timeout=LOCK_WAIT):
            self.send_json({"fatal": {"message": STUCK_NOTE, "function": "",
                                      "line": None}})
            return
        try:
            STOPPED.clear()
            self.respond(path, body)
        finally:
            LOCK.release()

    def respond(self, path, body):
        try:
            if path == "/api/reset":
                self.send_json(do_reset())
                return
            load_bank()
            answer = self.route(path, body)
            json.dumps(answer, ensure_ascii=False, allow_nan=False)
            self.send_json(answer)
        except StudentError as error:
            self.send_json({"fatal": {"message": error.message,
                                      "function": error.name,
                                      "line": error.line}})
        except Todo as todo:
            self.send_json({"todo": {"task": task_of(todo.name),
                                     "function": todo.name}})
        except Refusal as refusal:
            self.send_json({"refused": str(refusal)})
        except PermissionError as error:
            self.send_json({"fatal": {"message": locked(error),
                                      "function": "", "line": None}})
        except Exception as error:
            self.send_json({"fatal": {"message": generic(error),
                                      "function": "",
                                      "line": bank_line(error)}})

    def route(self, path, body):
        public = {
            "/api/state": lambda: page_state(self.session()),
            "/api/login": lambda: do_login(body),
            "/api/demo_login": lambda: do_demo_login(body),
            "/api/register": lambda: do_register(body),
            "/api/iban_check": lambda: do_iban_check(body),
            "/api/fx_quote": lambda: do_fx_quote(body),
            "/api/loan": lambda: do_loan(body),
            "/api/installments": lambda: do_installments(body),
            "/api/deposit": lambda: do_deposit(body),
            "/api/card_number": lambda: do_card_number(body),
            "/api/goal": lambda: do_goal(body),
        }
        if path in public:
            return public[path]()
        customer_no = SESSIONS.get(self.session())
        if customer_no is None:
            raise Refusal("Önce giriş yapın.")
        private = {
            "/api/logout": lambda: {"ok": SESSIONS.pop(self.session(), 0)},
            "/api/accounts": lambda: page_accounts(customer_no),
            "/api/cards": lambda: page_cards(customer_no),
            "/api/fx": lambda: page_fx(customer_no),
            "/api/breakdown": lambda: page_breakdown(
                customer_no, str(body.get("card_id", ""))),
            "/api/report": lambda: page_report(customer_no),
            "/api/orders": lambda: page_orders(customer_no),
            "/api/order_add": lambda: do_order_add(customer_no, body),
            "/api/loans": lambda: page_loans(customer_no),
            "/api/password": lambda: do_password(customer_no, body),
            "/api/budget_set": lambda: do_budget_set(customer_no, body),
            "/api/branches": page_branches,
            "/api/alias_add": lambda: do_alias_add(customer_no, body),
            "/api/atm": lambda: do_atm(customer_no, body),
            "/api/transfer": lambda: do_transfer(customer_no, body),
            "/api/card_spend": lambda: do_card_spend(customer_no, body),
            "/api/card_pay": lambda: do_card_pay(customer_no, body),
            "/api/fx_buy": lambda: do_fx_buy(customer_no, body),
            "/api/fx_sell": lambda: do_fx_sell(customer_no, body),
        }
        if path in private:
            return private[path]()
        raise Refusal("Böyle bir sayfa yok.")


class Server(http.server.ThreadingHTTPServer):
    # On Windows SO_REUSEADDR lets a second app.py bind a port that is in
    # use; without it the bind fails and main() tries the next port.
    allow_reuse_address = os.name != "nt"


def main():
    try:
        sys.stdout.reconfigure(errors="replace")
    except AttributeError:
        pass
    port = int(os.environ.get("MINIBANK_PORT", "8000"))
    server = None
    for candidate in range(port, port + 20):
        try:
            server = Server(("127.0.0.1", candidate), Handler)
            break
        except OSError:
            continue
    if server is None:
        print("Uygulama açılamadı: 8000-8019 arası portların hepsi dolu.")
        return
    address = f"http://127.0.0.1:{server.server_address[1]}/"
    print("Bankanız açık:", address, flush=True)
    print("Durdurmak için PyCharm'daki kırmızı Stop düğmesine basın.",
          flush=True)
    if os.environ.get("MINIBANK_NO_BROWSER") != "1":
        webbrowser.open(address)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    server.server_close()


if __name__ == "__main__":
    main()
