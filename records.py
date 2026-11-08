# Bu file (dosya) hazır; değiştirmeniz gerekmiyor.
#
# data klasöründeki file'ları okuyan ve onlara satır ekleyen
# function'lar (fonksiyon) burada; app.py ve kontrol.py bunları
# kullanıyor. transactions.csv'yi okuyan load_transactions ise bank.py'nin
# sonunda, hazır function'ların arasında duruyor. Buradakiler de file
# okumaya örnek olabilir; yalnız bozuk bir satırı sessizce atlıyorlar,
# load_transactions gibi saymıyorlar.


CUSTOMERS_HEADER = "customer_no,name,salt,password_hash"
ACCOUNTS_HEADER = "iban,customer_no,currency"
CARDS_HEADER = "card_id,customer_no,limit,cut_day"
ACTIVITY_HEADER = "date,card_id,kind,merchant,category,amount"
RATES_HEADER = "date,currency,buy,sell"
ALIASES_HEADER = "alias,iban"
ORDERS_HEADER = "sender,day,receiver,amount,description"
LOANS_HEADER = "loan_id,customer_no,principal,monthly_rate,months,start"
BUDGETS_HEADER = "customer_no,category,amount"
BRANCHES_HEADER = "code,name"


def load_customers(file_name):
    """customers.csv'yi okur; her müşterinin adını, salt'ını ve hash'ini
    tutan {müşteri no: (ad, salt, hash)} dict'ini (sözlük) return eder.
    Müşteri numarası int (tam sayı). salt ve hash 2. görevde anlatılıyor;
    şifrenin kendisi file'da yok.
    """
    customers = {}
    with open(file_name, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line == CUSTOMERS_HEADER:
                continue
            try:
                number, name, salt, password_hash = line.split(",")
                customers[int(number)] = (name, salt, password_hash)
            except ValueError:
                continue
    return customers


def load_accounts(file_name):
    """accounts.csv'yi okur; (iban, customer_no, currency) tuple'larının
    (demet) list'ini (liste) return eder. currency "TL", "USD" ya da
    "EUR".
    """
    accounts = []
    with open(file_name, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line == ACCOUNTS_HEADER:
                continue
            try:
                iban, number, currency = line.split(",")
                accounts.append((iban, int(number), currency))
            except ValueError:
                continue
    return accounts


def load_cards(file_name):
    """cards.csv'yi okur; (card_id, customer_no, limit, cut_day)
    tuple'larının list'ini return eder. card_id kartın son dört hanesi,
    str (karakter dizisi); limit TL; cut_day hesap kesim günü.
    """
    cards = []
    with open(file_name, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line == CARDS_HEADER:
                continue
            try:
                card_id, number, limit, cut_day = line.split(",")
                cards.append((card_id, int(number), int(limit), int(cut_day)))
            except ValueError:
                continue
    return cards


def load_card_activity(file_name):
    """card_activity.csv'yi okur; (date, card_id, kind, merchant,
    category, amount) tuple'larının list'ini return eder. kind "spend"
    (harcama) ya da "payment" (karta yapılan ödeme); amount TL, int.
    """
    activity = []
    with open(file_name, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line == ACTIVITY_HEADER:
                continue
            try:
                parts = line.split(",")
                date, card_id, kind, merchant, category, amount = parts
                activity.append((date, card_id, kind, merchant, category,
                                 int(amount)))
            except ValueError:
                continue
    return activity


def load_rates(file_name):
    """rates.csv'yi okur; {döviz: [(date, buy, sell), ...]} dict'ini return
    eder. buy bankanın dövizi aldığı, sell sattığı kur; ikisi de float
    (gerçek sayı).
    """
    rates = {}
    with open(file_name, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line == RATES_HEADER:
                continue
            try:
                date, currency, buy, sell = line.split(",")
                row = (date, float(buy), float(sell))
            except ValueError:
                continue
            if currency in rates:
                rates[currency].append(row)
            else:
                rates[currency] = [row]
    return rates


def load_aliases(file_name):
    """aliases.csv'yi okur; {e-posta: IBAN} dict'ini return eder (Kolay
    Adres).
    """
    aliases = {}
    with open(file_name, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line == ALIASES_HEADER:
                continue
            try:
                alias, iban = line.split(",")
                aliases[alias] = iban
            except ValueError:
                continue
    return aliases


def load_orders(file_name):
    """orders.csv'yi okur; otomatik ödeme talimatlarını (sender, day,
    receiver, amount, description) tuple'larının list'i olarak return
    eder. day ayın kaçı, amount TL; ikisi de int.
    """
    orders = []
    with open(file_name, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line == ORDERS_HEADER:
                continue
            try:
                sender, day, receiver, amount, description = line.split(",")
                orders.append((sender, int(day), receiver, int(amount),
                               description))
            except ValueError:
                continue
    return orders


def load_loans(file_name):
    """loans.csv'yi okur; (loan_id, customer_no, principal, monthly_rate,
    months, start) tuple'larının list'ini return eder. monthly_rate
    float, start kredinin çekildiği gün.
    """
    loans = []
    with open(file_name, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line == LOANS_HEADER:
                continue
            try:
                parts = line.split(",")
                loan_id, number, principal, rate, months, start = parts
                loans.append((loan_id, int(number), int(principal),
                              float(rate), int(months), start))
            except ValueError:
                continue
    return loans


def load_budgets(file_name):
    """budgets.csv'yi okur; {müşteri no: {kategori: aylık bütçe}}
    dict'ini return eder.
    """
    budgets = {}
    with open(file_name, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line == BUDGETS_HEADER:
                continue
            try:
                number, category, amount = line.split(",")
                number = int(number)
                amount = int(amount)
            except ValueError:
                continue
            if number in budgets:
                budgets[number][category] = amount
            else:
                budgets[number] = {category: amount}
    return budgets


def save_budgets(file_name, budgets):
    """Bütün bütçeleri file'a baştan yazar ("w" modu)."""
    with open(file_name, "w", encoding="utf-8") as f:
        f.write(BUDGETS_HEADER + "\n")
        for number in budgets:
            for category in budgets[number]:
                amount = budgets[number][category]
                f.write(f"{number},{category},{amount}\n")


def load_branches(file_name):
    """branches.csv'yi okur; {şube kodu: şube adı} dict'ini return eder."""
    branches = {}
    with open(file_name, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line == BRANCHES_HEADER:
                continue
            try:
                code, name = line.split(",")
                branches[code] = name
            except ValueError:
                continue
    return branches


def latest_rate(rates, currency, today):
    """today'den sonra olmayan en son günün (date, buy, sell) kurunu
    return eder; hiç yoksa None.
    """
    found = None
    for row in rates.get(currency, []):
        if row[0] <= today:
            found = row
    return found


def make_iban(bank_code, account_number):
    """5 haneli banka kodundan ve 16 haneli hesap numarasından, kontrol
    haneleri doğru bir TR IBAN'ı kurar.
    """
    rest = bank_code + "0" + account_number
    check = 98 - int(rest + "292700") % 97
    if check < 10:
        return "TR0" + str(check) + rest
    return "TR" + str(check) + rest


def add_line(file_name, header, fields):
    """file'ın sonuna, alanları virgülle ayrılmış bir satır ekler. File
    yoksa ya da boşsa önce başlığını yazar.
    """
    try:
        with open(file_name, encoding="utf-8") as f:
            empty = True
            for line in f:
                if line.strip() != "":
                    empty = False
                    break
    except FileNotFoundError:
        empty = True
    with open(file_name, "a", encoding="utf-8") as f:
        if empty:
            f.write(header + "\n")
        text = ""
        for field in fields:
            if text != "":
                text += ","
            text += str(field)
        f.write(text + "\n")
