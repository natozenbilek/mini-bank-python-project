# Bu file (dosya) hazır; değiştirmeniz gerekmiyor.
#
# Bu projede tarihler "2026-11-08" biçiminde str (karakter dizisi). Böyle
# yazılmış iki tarihi < ve > ile karşılaştırabilirsiniz: önce yıl, sonra
# ay, sonra gün yazdığı için "2026-09-30" < "2026-10-01" True verir.
# Bir tarihin ayını slicing (dilimleme) ile alırsınız:
# "2026-10-15"[:7] "2026-10" verir.
#
# Gün ya da ay eklemek gibi hesaplar için aşağıdaki function'ları (fonksiyon)
# kullanın. İçlerinde derste görmediğimiz datetime module'ü (modül) var;
# siz yalnız çağıracaksınız, tıpkı math.sqrt() gibi:
#     import dates
#     dates.add_days("2026-10-15", 10)


import calendar
import datetime


def add_days(date, days):
    """date'e days gün ekler; yeni tarihi str olarak return eder.

    >>> add_days("2026-10-25", 10)
    '2026-11-04'
    """
    day = datetime.date.fromisoformat(date) + datetime.timedelta(days=days)
    return day.isoformat()


def add_months(date, months):
    """date'e months ay ekler. O ayda o gün yoksa ayın son günü olur.

    >>> add_months("2026-11-08", 3)
    '2027-02-08'
    >>> add_months("2026-01-31", 1)
    '2026-02-28'
    """
    day = datetime.date.fromisoformat(date)
    index = day.year * 12 + day.month - 1 + months
    year = index // 12
    month = index % 12 + 1
    last = calendar.monthrange(year, month)[1]
    return datetime.date(year, month, min(day.day, last)).isoformat()


def statement_period(cut_day, today):
    """Son kapanan ekstrenin (start, end) tarihlerini return eder.

    cut_day kartın hesap kesim günü (1 ile 28 arası). Bir ekstre, bir
    önceki hesap kesimin ertesi gününden bu hesap kesim gününe kadar
    yapılan harcamaları kapsar. Bu ayın hesap kesim günü geçtiyse son
    kapanan ekstre bu ayınki, geçmediyse geçen ayınki.

    >>> statement_period(5, "2026-11-08")
    ('2026-10-06', '2026-11-05')
    >>> statement_period(15, "2026-11-08")
    ('2026-09-16', '2026-10-15')
    """
    day = datetime.date.fromisoformat(today)
    end = datetime.date(day.year, day.month, cut_day)
    if end >= day:
        end = datetime.date.fromisoformat(add_months(end.isoformat(), -1))
    start = add_days(add_months(end.isoformat(), -1), 1)
    return start, end.isoformat()


def month_names(today, count):
    """today'in ayıyla biten count ayı, eskiden yeniye, "2026-09" gibi
    str'lerin list'i (liste) olarak return eder.

    >>> month_names("2026-11-08", 3)
    ['2026-09', '2026-10', '2026-11']
    """
    names = []
    for back in range(count - 1, -1, -1):
        names.append(add_months(today[:8] + "01", -back)[:7])
    return names
