/* Mini bank: the ready-made screen of the bank app. Students do not edit
   this file. Every number on the screen comes from bank.py through the
   JSON API of app.py; this file only asks for it and shows it.

   API shapes (see app.py):
   - top level: {"fatal": {message, function, line}}, {"todo": {task,
     function}}, {"refused": "..."}; otherwise the page or the action
     result.
   - page sections: {"ok": data}, {"todo": {task, function}} or
     {"error": {task, function, message, line}}. Each section is drawn
     on its own part of the screen, so one unfinished task never blanks a
     whole tab: the part waits with a "todo" box, or shows the error and
     its line in bank.py. */
"use strict";

(function () {
  const DEFAULT_NAME = "Örnek Bank";
  const DEFAULT_COLOR = "#2f5d8a";
  /* The bank's rules as bank.py states them (BANK_CODE, BRANCH_FEE, ...).
     They are only used in texts on the screen; bank.py decides. */
  const OUR_BANK_CODE = "12345";
  const BRANCH_FEE = 2;
  const EFT_FEE = 5;
  const DAILY_LIMIT = 50000;
  const ATM_LIMIT = 10000;
  const TEST_CARD = "4111 1111 1111 1111";
  const FALLBACK_CATEGORIES = ["market", "yemek", "ulaşım", "eğlence",
    "kitap", "giyim", "sağlık", "abonelik"];
  const TOKEN_KEY = "minibank.session";
  const BRAND_KEY = "minibank.brand";
  const VISIBLE_MOVES = 8;
  const PUBLIC_PATHS = ["/api/state", "/api/login", "/api/demo_login",
    "/api/register", "/api/iban_check", "/api/fx_quote", "/api/loan",
    "/api/installments", "/api/deposit", "/api/card_number", "/api/goal",
    "/api/reset"];
  const DIGITS = "[0-9]+";
  const SIGNED = "-?[0-9]+";
  const DECIMAL = "[0-9]+([.,][0-9]+)?";
  const DIGITS_TITLE = "Yalnız rakam yazın, nokta ya da virgül koymadan.";
  const DECIMAL_TITLE = "2 ya da 2,5 gibi bir sayı yazın.";
  const PASSWORD_RULES = "En az 8 karakter; içinde en az bir rakam ve " +
    "bir harf olsun, virgül ve adınız olmasın.";
  const SHAPE_TEXT = "Bu bölüm gösterilemedi: bank.py'den gelen değer " +
    "beklenen biçimde değil.";
  const WAIT_MS = 20000;

  const TABS = [
    { id: "hesaplar", label: "Hesaplarım", task: 1, icon: "wallet",
      render: renderAccounts },
    { id: "subeler", label: "Şubeler", task: 1, icon: "pin",
      render: renderBranches },
    { id: "gonder", label: "Para gönder", task: 3, icon: "send",
      render: renderTransfer },
    { id: "kartlar", label: "Kartlarım", task: 4, icon: "card",
      render: renderCards },
    { id: "dokum", label: "Döküm", task: 4, icon: "chart",
      render: renderBreakdown },
    { id: "doviz", label: "Döviz", task: 5, icon: "exchange",
      render: renderFx },
    { id: "kredi", label: "Kredi ve birikim", task: 5, icon: "percent",
      render: renderLoans },
    { id: "atm", label: "ATM", task: 5, icon: "atm", render: renderAtm },
    { id: "rapor", label: "Raporum", task: 5, icon: "report",
      render: renderReport },
    { id: "ayarlar", label: "Ayarlar", task: 2, icon: "sliders",
      render: renderSettings }
  ];

  const app = {
    token: "",
    state: null,
    view: "",
    tab: "",
    breakdownCard: "",
    prefill: null,
    paid: [],
    branch: null,
    waits: {},
    surveyed: false
  };

  const main = document.getElementById("main");

  /* Formatting */

  const numberFormat = new Intl.NumberFormat("tr-TR",
    { maximumFractionDigits: 2 });
  const signedFormat = new Intl.NumberFormat("tr-TR",
    { maximumFractionDigits: 2, signDisplay: "exceptZero" });
  const rateFormat = new Intl.NumberFormat("tr-TR",
    { minimumFractionDigits: 2, maximumFractionDigits: 4 });
  const dayFormat = new Intl.DateTimeFormat("tr-TR",
    { day: "2-digit", month: "2-digit", year: "numeric", timeZone: "UTC" });
  const longFormat = new Intl.DateTimeFormat("tr-TR",
    { day: "numeric", month: "long", year: "numeric", timeZone: "UTC" });
  const todayFormat = new Intl.DateTimeFormat("tr-TR",
    { day: "numeric", month: "long", year: "numeric", weekday: "long",
      timeZone: "UTC" });
  const monthFormat = new Intl.DateTimeFormat("tr-TR",
    { month: "long", year: "numeric", timeZone: "UTC" });

  function isNumber(value) {
    return typeof value === "number" && isFinite(value);
  }

  function isObject(value) {
    return Boolean(value) && typeof value === "object" &&
      !Array.isArray(value);
  }

  function show(value) {
    if (value === null || value === undefined) {
      return "";
    }
    return String(value);
  }

  function num(value) {
    return isNumber(value) ? numberFormat.format(value) : show(value);
  }

  /* money(5) is "5 TL"; money(5, "USD") is "5 USD"; money(5, "") has no
     unit, for an account whose currency is not known yet. */
  function money(value, currency) {
    const unit = currency === undefined || currency === null ? "TL"
      : currency;
    return (num(value) + " " + unit).trim();
  }

  function signedMoney(value, currency) {
    const unit = currency === undefined || currency === null ? "TL"
      : currency;
    const text = isNumber(value) ? signedFormat.format(value) : show(value);
    return (text + " " + unit).trim();
  }

  function rate(value) {
    return isNumber(value) ? rateFormat.format(value) : show(value);
  }

  function parseDate(text) {
    const found = /^(\d{4})-(\d{2})(?:-(\d{2}))?$/.exec(show(text));
    if (!found) {
      return null;
    }
    const day = found[3] ? Number(found[3]) : 1;
    return new Date(Date.UTC(Number(found[1]), Number(found[2]) - 1, day));
  }

  function fmtDate(text, format) {
    const date = parseDate(text);
    return date ? format.format(date) : show(text);
  }

  function monthName(text) {
    return cap(fmtDate(text, monthFormat));
  }

  function cap(text) {
    text = show(text);
    return text.charAt(0).toLocaleUpperCase("tr-TR") + text.slice(1);
  }

  function cleanIban(text) {
    return show(text).replace(/\s+/g, "").toUpperCase();
  }

  function groupIban(text) {
    return cleanIban(text).replace(/(.{4})(?=.)/g, "$1 ");
  }

  function party(code) {
    const text = show(code);
    if (text === "NAKIT") {
      return "Nakit";
    }
    if (text === "MASRAF") {
      return "Banka masrafı";
    }
    if (text === "DOVIZ") {
      return "Döviz kasası";
    }
    const card = /^KART-(\w+)$/.exec(text);
    if (card) {
      return "Kart " + card[1];
    }
    const loan = /^KREDI-(\w+)$/.exec(text);
    if (loan) {
      return "Kredi " + loan[1];
    }
    if (/^TR\d{24}$/.test(text)) {
      return groupIban(text);
    }
    return text;
  }

  /* Small DOM helpers */

  function add(element, child) {
    if (child === null || child === undefined || child === false) {
      return;
    }
    if (Array.isArray(child)) {
      child.forEach(function (item) { add(element, item); });
      return;
    }
    element.append(child instanceof Node ? child
      : document.createTextNode(String(child)));
  }

  function h(tag, props) {
    const element = document.createElement(tag);
    if (props) {
      Object.keys(props).forEach(function (key) {
        const value = props[key];
        if (value === null || value === undefined || value === false) {
          return;
        }
        if (key === "class") {
          element.className = value;
        } else if (key.slice(0, 2) === "on" && typeof value === "function") {
          element.addEventListener(key.slice(2), value);
        } else if (value === true) {
          element.setAttribute(key, "");
        } else {
          element.setAttribute(key, String(value));
        }
      });
    }
    for (let i = 2; i < arguments.length; i++) {
      add(element, arguments[i]);
    }
    return element;
  }

  function fill(target) {
    target.replaceChildren();
    for (let i = 1; i < arguments.length; i++) {
      add(target, arguments[i]);
    }
    if (target.getAttribute("role") === "tabpanel") {
      openFirst(target);
    }
  }

  /* A part that only waits for a task ("... görevi yazınca açılacak")
     moves below the parts that are open, so that a tab first shows what
     already works. */
  function waiting(node) {
    if (node.classList.contains("note-todo")) {
      return true;
    }
    if (!node.classList.contains("part")) {
      return false;
    }
    const rest = Array.from(node.children).filter(function (child) {
      return !child.classList.contains("section-head");
    });
    return rest.length > 0 && rest.every(function (child) {
      return child.classList.contains("note-todo");
    });
  }

  function openFirst(target) {
    Array.from(target.children).filter(waiting).forEach(function (node) {
      target.append(node);
    });
  }

  const SVG_NS = "http://www.w3.org/2000/svg";

  /* Line icons on a 24 px grid, drawn with the text colour. The notes
     have a plain glyph each; the rest are the tabs and a few buttons. */
  const ICONS = {
    todo: "M9 7l-5 5 5 5M15 7l5 5-5 5",
    error: "M7 7l10 10M17 7L7 17",
    bad: "M7 7l10 10M17 7L7 17",
    warn: "M12 5v9M12 18.5v.5",
    ok: "M5 12.5l4.5 4.5L19 7.5",
    info: "M12 10.5v7M12 6.5v.5",
    bank: "M3.5 9.5L12 4.5l8.5 5zM5.5 12v5.5M10 12v5.5M14 12v5.5" +
      "M18.5 12v5.5M3.5 20.5h17",
    wallet: "M5 6.5h14a1.5 1.5 0 0 1 1.5 1.5v9.5a1.5 1.5 0 0 1-1.5 1.5H5" +
      "a1.5 1.5 0 0 1-1.5-1.5V8A1.5 1.5 0 0 1 5 6.5zM20.5 10.5H17" +
      "a2 2 0 0 0 0 4h3.5M6.5 6.5l8.6-2.4a1 1 0 0 1 1.3 1v1.4",
    pin: "M12 21c-3.5-3.6-6.5-7-6.5-10.5a6.5 6.5 0 0 1 13 0" +
      "c0 3.5-3 6.9-6.5 10.5zM12 8a2.5 2.5 0 1 0 0 5a2.5 2.5 0 1 0 0-5z",
    send: "M20.5 3.5L10 14M20.5 3.5l-6.5 17-4-6.5-6.5-4z",
    card: "M4.5 5.5h15A1.5 1.5 0 0 1 21 7v10a1.5 1.5 0 0 1-1.5 1.5h-15" +
      "A1.5 1.5 0 0 1 3 17V7a1.5 1.5 0 0 1 1.5-1.5zM3 10h18M6.5 15h3",
    chart: "M4 4v16h16M8.5 16.5v-4M13 16.5V7.5M17.5 16.5v-6",
    exchange: "M4 8.5h15M15.5 5l3.5 3.5-3.5 3.5M20 15.5H5M8.5 12L5 15.5" +
      " 8.5 19",
    percent: "M18.5 5.5l-13 13M7.5 5a2.5 2.5 0 1 0 0 5a2.5 2.5 0 1 0 0-5z" +
      "M16.5 14a2.5 2.5 0 1 0 0 5a2.5 2.5 0 1 0 0-5z",
    atm: "M4.5 4h15A1.5 1.5 0 0 1 21 5.5v3A1.5 1.5 0 0 1 19.5 10h-15" +
      "A1.5 1.5 0 0 1 3 8.5v-3A1.5 1.5 0 0 1 4.5 4zM7 7h10M7.5 10v10h9V10" +
      "M12 13a1.5 1.5 0 1 0 0 3a1.5 1.5 0 1 0 0-3z",
    report: "M6.5 3h7.5l4.5 4.5v12A1.5 1.5 0 0 1 17 21H6.5A1.5 1.5 0 0 1 5" +
      " 19.5v-15A1.5 1.5 0 0 1 6.5 3zM14 3v4.5h4.5M8.5 12.5h7M8.5 16.5h7",
    sliders: "M4 7h9M17 7h3M15 4.5v5M4 17h3M11 17h9M9 14.5v5",
    login: "M14.5 3.5H18A1.5 1.5 0 0 1 19.5 5v14a1.5 1.5 0 0 1-1.5 1.5h-3.5" +
      "M10 16.5l4.5-4.5L10 7.5M14.5 12H4"
  };

  function icon(name, size) {
    const svg = document.createElementNS(SVG_NS, "svg");
    svg.setAttribute("viewBox", "0 0 24 24");
    svg.setAttribute("width", String(size || 18));
    svg.setAttribute("height", String(size || 18));
    svg.setAttribute("aria-hidden", "true");
    svg.setAttribute("focusable", "false");
    svg.setAttribute("class", "icon");
    const path = document.createElementNS(SVG_NS, "path");
    path.setAttribute("d", ICONS[name] || ICONS.info);
    path.setAttribute("fill", "none");
    path.setAttribute("stroke", "currentColor");
    path.setAttribute("stroke-width", "1.75");
    path.setAttribute("stroke-linecap", "round");
    path.setAttribute("stroke-linejoin", "round");
    svg.append(path);
    return svg;
  }

  /* Charts. Every chart draws numbers that a table or a text right next
     to it also gives, so screen readers skip the drawing. Bars start at
     zero; hovering a bar shows its value. */

  function svgNode(tag, attrs) {
    const element = document.createElementNS(SVG_NS, tag);
    Object.keys(attrs || {}).forEach(function (key) {
      element.setAttribute(key, String(attrs[key]));
    });
    for (let i = 2; i < arguments.length; i++) {
      if (arguments[i]) {
        element.append(arguments[i]);
      }
    }
    return element;
  }

  function svgTitle(text) {
    const title = document.createElementNS(SVG_NS, "title");
    title.textContent = text;
    return title;
  }

  /* A thin horizontal bar: share (0 to 1) of its track is filled. kind
     picks the colour: "rest" grey, "over" red, otherwise blue. */
  function meter(share, title, kind, restTitle) {
    let part = isNumber(share) ? Math.max(0, Math.min(1, share)) : 0;
    if (part > 0 && part < 0.01) {
      part = 0.01;
    }
    return svgNode("svg", { class: "meter" + (kind ? " is-" + kind : ""),
      width: "100%", height: "8", "aria-hidden": "true", focusable: "false" },
    svgNode("rect", { class: "meter-track", width: "100%", height: "100%" },
      restTitle ? svgTitle(restTitle) : null),
    part > 0 ? svgNode("rect", { class: "meter-fill",
      width: (part * 100).toFixed(2) + "%", height: "100%" },
    title ? svgTitle(title) : null) : null);
  }

  /* 1, 2, 2,5 or 5 times a power of ten: the grid step of an axis. */
  function niceStep(rough) {
    const power = Math.pow(10, Math.floor(Math.log10(rough)));
    const steps = [1, 2, 2.5, 5, 10];
    for (let i = 0; i < steps.length; i++) {
      if (steps[i] * power >= rough) {
        return steps[i] * power;
      }
    }
    return 10 * power;
  }

  /* A column chart with one value axis. keys: [{ label, kind }];
     groups: [{ label, bars: [{ value, title }] }] with one bar per key.
     The bars of a group stand side by side, or on top of each other when
     stacked is true. unit names the axis, corner names the bottom row. */
  function columnChart(unit, keys, groups, stacked, corner) {
    let top = 0;
    groups.forEach(function (group) {
      let size = 0;
      group.bars.forEach(function (bar) {
        if (isNumber(bar.value) && bar.value > 0) {
          size = stacked ? size + bar.value : Math.max(size, bar.value);
        }
      });
      top = Math.max(top, size);
    });
    if (groups.length === 0 || top <= 0) {
      return null;
    }
    const step = niceStep(top / 4);
    const max = step * Math.ceil(top / step - 1e-9);
    const ticks = [];
    for (let value = 0; value <= max + step / 2; value += step) {
      ticks.push(value);
    }
    const plot = svgNode("svg", { viewBox: "0 0 100 100",
      preserveAspectRatio: "none", focusable: "false" });
    ticks.forEach(function (value) {
      if (value > 0) {
        const y = 100 - value / max * 100;
        plot.append(svgNode("line", { class: "chart-grid", x1: 0, x2: 100,
          y1: y, y2: y, "vector-effect": "non-scaling-stroke" }));
      }
    });
    const slot = 100 / groups.length;
    groups.forEach(function (group, i) {
      const across = stacked ? 1 : group.bars.length;
      const band = slot * 0.5;
      const width = band / across;
      let base = 0;
      group.bars.forEach(function (bar, j) {
        const value = isNumber(bar.value) && bar.value > 0 ? bar.value : 0;
        const height = value / max * 100;
        const x = i * slot + (slot - band) / 2 + (stacked ? 0 : j * width);
        const kind = keys[j] ? keys[j].kind : "main";
        if (height > 0) {
          plot.append(svgNode("rect", { class: "chart-bar is-" + kind,
            x: x.toFixed(3), y: (100 - base - height).toFixed(3),
            width: (stacked ? band : width * 0.9).toFixed(3),
            height: height.toFixed(3) }, svgTitle(bar.title)));
        }
        if (stacked) {
          base += height;
        }
      });
    });
    return h("figure", { class: "chart", "aria-hidden": "true" },
      h("span", { class: "chart-unit" }, unit),
      h("ul", { class: "chart-keys" }, keys.map(function (key) {
        return h("li", null, h("span", { class: "key is-" + key.kind }),
          key.label);
      })),
      h("div", { class: "chart-ticks" }, ticks.map(function (value) {
        return h("span", null, num(value));
      })),
      h("div", { class: "chart-plot" }, plot),
      h("span", { class: "chart-unit" }, corner || ""),
      h("div", { class: "chart-x", style: "grid-template-columns: repeat(" +
        groups.length + ", minmax(0, 1fr))" }, groups.map(function (group) {
        return h("span", null, group.label);
      })));
  }

  function note(kind, content) {
    return h("div", { class: "note note-" + kind },
      icon(kind), h("div", { class: "note-body" }, content));
  }

  function hasLine(info) {
    return info.line !== null && info.line !== undefined && info.line !== "";
  }

  /* Whether a problem points into bank.py. app.py's own problems (a data
     file that Excel holds, a request that never ended) have neither a
     function nor a line. */
  function located(info) {
    return Boolean(info.function) || hasLine(info);
  }

  /* "bank.py, 123. satır (statement)" from {function, line}. */
  function where(info) {
    let text = "bank.py";
    if (hasLine(info)) {
      text += ", " + info.line + ". satır";
    }
    if (info.function && info.function !== "bank.py") {
      text += " (" + info.function + ")";
    }
    return text;
  }

  function problemNodes(info) {
    if (!located(info)) {
      return [show(info.message)];
    }
    return [h("strong", null, where(info) + ":"), " ",
      h("code", null, show(info.message))];
  }

  /* A part waits for a function of bank.py or, when ready code needs a
     module, for its import line ("import dates"). */
  function todoText(info, action) {
    const task = info.task ? info.task + ". görevi" : "ilgili görevi";
    const start = action ? "Bu işlem " + task + " yazınca çalışacak"
      : "Bu bölüm " + task + " yazınca açılacak";
    const name = show(info.function);
    if (name.indexOf("import ") === 0) {
      return start + ": bank.py'nin başına " + name + " satırını yazın.";
    }
    return start + ": bank.py'de " + name + ".";
  }

  function todoNote(info, action) {
    return note("todo", todoText(info || {}, action));
  }

  function errorNote(info) {
    return note("error", problemNodes(info || {}));
  }

  /* Draws one page section: its data, its todo box or its error. */
  function sectionView(result, render) {
    if (result && typeof result === "object") {
      if (Object.prototype.hasOwnProperty.call(result, "ok")) {
        try {
          return render(result.ok);
        } catch (error) {
          return note("error", SHAPE_TEXT);
        }
      }
      if (result.todo) {
        return todoNote(result.todo, false);
      }
      if (result.error) {
        return errorNote(result.error);
      }
    }
    return note("error", "Bu bölüm için beklenmeyen bir cevap geldi.");
  }

  function sectionOk(result) {
    return Boolean(result && typeof result === "object" &&
      Object.prototype.hasOwnProperty.call(result, "ok"));
  }

  /* A note for an answer that is not a normal result, or null. */
  function answerProblem(data, action) {
    if (!data || typeof data !== "object" || data.sessionGone) {
      return note("warn", "Oturumunuz kapanmış; yeniden giriş yapın.");
    }
    if (data.offline) {
      return note("error", offlineText(data.offline));
    }
    if (data.fatal) {
      return errorNote(data.fatal);
    }
    if (data.todo) {
      return todoNote(data.todo, action);
    }
    if (typeof data.refused === "string") {
      return note("warn", data.refused);
    }
    return null;
  }

  /* Message areas under forms. "later" waits a moment so that a screen
     reader announces a message put into a freshly drawn area. */
  function say(area, node, later) {
    area.replaceChildren();
    if (!node) {
      return;
    }
    if (later) {
      setTimeout(function () {
        if (area.isConnected) {
          area.replaceChildren(node);
        }
      }, 80);
    } else {
      area.append(node);
    }
  }

  function messageArea() {
    return h("div", { class: "say", "aria-live": "polite" });
  }

  function flashNote(area, message) {
    if (message) {
      say(area, note(message.kind, message.text), true);
    }
  }

  function field(id, label, control, hint) {
    let hintNode = null;
    if (hint) {
      const hintId = id + "-hint";
      const before = control.getAttribute("aria-describedby");
      control.setAttribute("aria-describedby",
        before ? before + " " + hintId : hintId);
      hintNode = h("p", { class: "hint", id: hintId }, hint);
    }
    return h("div", { class: "field" },
      h("label", { for: id }, label), control, hintNode);
  }

  function input(id, props) {
    return h("input", Object.assign({ id: id, name: id, type: "text",
      autocomplete: "off", spellcheck: "false" }, props || {}));
  }

  function amountInput(id, props) {
    return input(id, Object.assign({ inputmode: "numeric", pattern: DIGITS,
      title: DIGITS_TITLE, required: true }, props || {}));
  }

  function decimalInput(id, props) {
    return input(id, Object.assign({ inputmode: "decimal", pattern: DECIMAL,
      title: DECIMAL_TITLE, required: true }, props || {}));
  }

  function choice(id, options, chosen) {
    return h("select", { id: id, name: id },
      options.map(function (option) {
        return h("option", { value: option.value,
          selected: option.value === chosen }, option.label);
      }));
  }

  function categoryChoice(id, categories) {
    return h("select", { id: id, name: id, required: true },
      h("option", { value: "" }, "Kategori seçin"),
      categories.map(function (name) {
        return h("option", { value: name }, cap(name));
      }));
  }

  function currencyChoice(id, chosen) {
    return choice(id, [{ value: "USD", label: "USD (Amerikan doları)" },
      { value: "EUR", label: "EUR (Euro)" }], chosen || "USD");
  }

  function accountChoice(id, accounts, chosen) {
    return choice(id, accounts.map(function (account) {
      return { value: cleanIban(account.iban),
        label: groupIban(account.iban) + " · " + money(account.balance) };
    }), chosen);
  }

  function primary(label, iconName) {
    return h("button", { type: "submit", class: "btn btn-primary" },
      iconName ? icon(iconName) : null, label);
  }

  function quickButton(label, onclick) {
    return h("button", { type: "button", class: "btn btn-small btn-secondary",
      onclick: onclick }, label);
  }

  function badge(task) {
    if (!task) {
      return null;
    }
    const mark = h("span", { class: "badge", "data-task": task },
      h("span", { class: "sr-only" }, ", "), task + ". görev",
      h("span", { class: "badge-done" },
        h("span", { "aria-hidden": "true" }, " ✓"),
        h("span", { class: "sr-only" }, ", tamam")));
    mark.classList.toggle("is-done", finished(task));
    return mark;
  }

  /* Finished tasks. A waiting or failing section of an answer names its
     task. Right after login the app asks each page once, one after the
     other; from then on a task whose number no answer names is finished,
     and its markers read "1. görev ✓". Later answers keep this current.
     buy_foreign, sell_foreign and months_to_goal run only behind buttons,
     so the survey also asks the two calculators that call them, with fixed
     sample inputs (SURVEY_BODY); neither writes anything. Without them task
     5 could read ✓ while one of those three functions is still empty. */
  const SURVEY = ["/api/accounts", "/api/branches", "/api/orders",
    "/api/cards", "/api/fx", "/api/fx_quote", "/api/loans", "/api/goal",
    "/api/report"];
  const SURVEY_BODY = {
    "/api/fx_quote": { currency: "USD", tl_amount: "1000" },
    "/api/goal": { goal: "12000", monthly: "1000", rate: "1" }
  };

  function tasksIn(value, found) {
    if (Array.isArray(value)) {
      value.forEach(function (item) { tasksIn(item, found); });
    } else if (isObject(value)) {
      ["todo", "error"].forEach(function (key) {
        const info = value[key];
        if (isObject(info) && isNumber(info.task) && info.task > 0 &&
            found.indexOf(info.task) < 0) {
          found.push(info.task);
        }
      });
      Object.keys(value).forEach(function (key) {
        tasksIn(value[key], found);
      });
    }
    return found;
  }

  function noteAnswer(path, data) {
    if (!isObject(data) || data.offline || data.sessionGone) {
      return;
    }
    /* bank.py could not even be loaded: no task counts as finished. */
    app.waits[path] = data.fatal ? [1, 2, 3, 4, 5] : tasksIn(data, []);
    markTasks();
  }

  function named(task) {
    return Object.keys(app.waits).some(function (path) {
      return app.waits[path].indexOf(task) >= 0;
    });
  }

  /* Until task 1 is written most pages stop at it and never reach the
     parts of the later tasks; only the login (task 2) does not need it. */
  function finished(task) {
    return app.surveyed && !named(task) && (task === 2 || !named(1));
  }

  function markTasks() {
    document.querySelectorAll(".badge[data-task]").forEach(function (mark) {
      mark.classList.toggle("is-done",
        finished(Number(mark.getAttribute("data-task"))));
    });
  }

  async function survey() {
    const token = app.token;
    const current = function () {
      return app.view === "app" && app.token === token;
    };
    for (let i = 0; i < SURVEY.length && current(); i++) {
      const data = SURVEY[i] === "/api/accounts" ? await getAccounts()
        : await post(SURVEY[i], SURVEY_BODY[SURVEY[i]]);
      const cards = isObject(data) && Array.isArray(data.cards)
        ? data.cards : [];
      if (SURVEY[i] === "/api/cards" && isObject(cards[0]) && current()) {
        await post("/api/breakdown", { card_id: show(cards[0].card_id) });
      }
    }
    if (current()) {
      app.surveyed = true;
      markTasks();
    }
  }

  function panelHead(title, sub) {
    return h("div", { class: "panel-head" },
      h("h2", null, title), sub ? h("p", null, sub) : null);
  }

  /* One titled part of a tab. A part that belongs to another task than
     its tab carries that task's badge. */
  function partCard(id, title, task, sub) {
    const titleId = id + "-title";
    const card = h("section", { class: "card stack part",
      "aria-labelledby": titleId },
    h("div", { class: "section-head" },
      h("h3", { id: titleId, class: "part-title" }, title, badge(task)),
      sub ? h("p", null, sub) : null));
    for (let i = 4; i < arguments.length; i++) {
      add(card, arguments[i]);
    }
    return card;
  }

  function stat(label, value) {
    return h("div", { class: "stat" }, h("dt", null, label),
      h("dd", null, value));
  }

  function chips(list, empty) {
    if (list.length === 0) {
      return h("p", { class: "muted" }, empty);
    }
    return h("ul", { class: "chips" }, list.map(function (text) {
      return h("li", { class: "chip" }, text);
    }));
  }

  function tableHead(columns) {
    return h("thead", null, h("tr", null, columns.map(function (column) {
      return h("th", { scope: "col", class: column[1] ? "num" : null },
        column[0]);
    })));
  }

  async function busy(button, work) {
    button.disabled = true;
    button.setAttribute("aria-busy", "true");
    try {
      return await work();
    } finally {
      button.disabled = false;
      button.removeAttribute("aria-busy");
    }
  }

  /* Session token, kept for this browser tab only */

  function loadToken() {
    try {
      app.token = window.sessionStorage.getItem(TOKEN_KEY) || "";
    } catch (error) {
      app.token = "";
    }
  }

  function setToken(value) {
    app.token = value || "";
    try {
      if (app.token) {
        window.sessionStorage.setItem(TOKEN_KEY, app.token);
      } else {
        window.sessionStorage.removeItem(TOKEN_KEY);
      }
    } catch (error) {
      /* Storage is blocked: the token stays in memory only. */
    }
  }

  /* Talking to app.py */

  async function reachable() {
    try {
      const response = await fetch("/style.css", { cache: "no-store" });
      return response.ok;
    } catch (error) {
      return false;
    }
  }

  /* A request that gets no answer in WAIT_MS is given up: a function of
     bank.py that never ends would otherwise leave the page loading for
     ever. app.py itself stops a long loop sooner and answers. */
  async function post(path, body, options) {
    let data = null;
    const stop = new AbortController();
    const timer = setTimeout(function () { stop.abort(); }, WAIT_MS);
    try {
      const response = await fetch(path, {
        method: "POST",
        headers: { "Content-Type": "application/json",
          "X-Session": app.token },
        body: JSON.stringify(body || {}),
        cache: "no-store",
        signal: stop.signal
      });
      try {
        data = await response.json();
      } catch (error) {
        data = null;
      }
      if (!data || typeof data !== "object" || Array.isArray(data)) {
        data = { offline: stop.signal.aborted ? "slow" : "crash" };
      }
    } catch (error) {
      if (stop.signal.aborted) {
        data = { offline: "slow" };
      } else {
        data = { offline: (await reachable()) ? "crash" : "down" };
      }
    } finally {
      clearTimeout(timer);
    }
    const quiet = options && options.quiet;
    if (!quiet && typeof data.refused === "string" &&
        PUBLIC_PATHS.indexOf(path) < 0 && (await sessionGone())) {
      return { sessionGone: true };
    }
    noteAnswer(path, data);
    return data;
  }

  /* Standing orders are paid by the first /api/accounts call of the day,
     whichever tab makes it; what was paid is kept here so that Hesaplarım
     can still show it. */
  async function getAccounts() {
    const data = await post("/api/accounts");
    remember(data);
    return data;
  }

  function remember(data) {
    if (!isObject(data)) {
      return;
    }
    if (isObject(data.branch)) {
      app.branch = data.branch;
    }
    const run = data.orders_run;
    if (!sectionOk(run) || !Array.isArray(run.ok)) {
      return;
    }
    run.ok.forEach(function (order) {
      if (!isObject(order)) {
        return;
      }
      const key = [order.description, order.receiver, order.amount].join("|");
      app.paid = app.paid.filter(function (old) { return old.key !== key; });
      app.paid.push(Object.assign({ key: key }, order));
    });
  }

  function offlineText(kind) {
    if (kind === "slow") {
      return "Cevap gelmedi: bank.py'deki bir loop (döngü) bitmiyor ya da " +
        "bir input() cevap bekliyor olabilir. Düzeltin, sonra app.py'yi " +
        "durdurup yeniden Run deyin.";
    }
    if (kind === "crash") {
      return "Uygulama bu isteği tamamlayamadı. Hatanın ayrıntısı " +
        "PyCharm'da, app.py'nin çalıştığı Run penceresinde.";
    }
    return "Uygulamaya ulaşılamadı. app.py çalışıyor mu? PyCharm'da " +
      "app.py'yi açıp Run deyin, sonra sayfayı yenileyin.";
  }

  /* The banner at the top */

  function showBanner(lines) {
    const holder = document.getElementById("banner-text");
    holder.replaceChildren(icon("error"),
      h("div", { class: "banner-lines" }, lines));
    document.getElementById("banner").hidden = false;
  }

  function showFatal(fatal) {
    fatal = fatal || {};
    if (!located(fatal)) {
      showBanner([h("p", null, problemNodes(fatal))]);
      return;
    }
    showBanner([h("p", null, problemNodes(fatal)),
      h("p", null, "bank.py'yi düzeltip kaydedin, sonra sayfayı " +
        "yenileyin.")]);
  }

  function showOffline(kind) {
    showBanner([h("p", null, offlineText(kind))]);
  }

  function hideBanner() {
    document.getElementById("banner").hidden = true;
    document.getElementById("banner-text").replaceChildren();
  }

  /* Whole page answers. Returns true when data is a normal page; otherwise
     puts the right message into target, after the prefix nodes. */
  function pageOk(target, prefix, data) {
    if (data.sessionGone) {
      return false;
    }
    if (data.offline) {
      showOffline(data.offline);
      fill(target, prefix, note("error", offlineText(data.offline)));
      return false;
    }
    if (data.fatal) {
      showFatal(data.fatal);
      fill(target, prefix, located(data.fatal)
        ? note("error", "Bu bölüm açılamadı: bank.py'de bir hata var. " +
          "Hatanın yeri sayfanın en üstünde yazıyor.")
        : errorNote(data.fatal));
      return false;
    }
    hideBanner();
    if (data.todo) {
      fill(target, prefix, todoNote(data.todo, false));
      return false;
    }
    if (typeof data.refused === "string") {
      fill(target, prefix, note("warn", data.refused));
      return false;
    }
    return true;
  }

  /* Action answers. Returns true when the caller should read the result. */
  function actionOk(area, data) {
    if (data.sessionGone) {
      return false;
    }
    if (data.offline) {
      showOffline(data.offline);
      say(area, note("error", offlineText(data.offline)));
      return false;
    }
    if (data.fatal) {
      showFatal(data.fatal);
      say(area, errorNote(data.fatal));
      return false;
    }
    if (data.todo) {
      say(area, todoNote(data.todo, true));
      return false;
    }
    if (typeof data.refused === "string") {
      say(area, note("warn", data.refused));
      return false;
    }
    return true;
  }

  /* Brand: name and colour from bank.py */

  function hexRgb(color) {
    const value = parseInt(color.slice(1), 16);
    return [(value >> 16) & 255, (value >> 8) & 255, value & 255];
  }

  function rgbHex(rgb) {
    return "#" + rgb.map(function (part) {
      return part.toString(16).padStart(2, "0");
    }).join("");
  }

  function luminance(rgb) {
    const parts = rgb.map(function (part) {
      const c = part / 255;
      return c <= 0.03928 ? c / 12.92 : Math.pow((c + 0.055) / 1.055, 2.4);
    });
    return 0.2126 * parts[0] + 0.7152 * parts[1] + 0.0722 * parts[2];
  }

  function contrast(a, b) {
    const la = luminance(a);
    const lb = luminance(b);
    return (Math.max(la, lb) + 0.05) / (Math.min(la, lb) + 0.05);
  }

  function mix(a, b, share) {
    return a.map(function (part, i) {
      return Math.round(part + (b[i] - part) * share);
    });
  }

  function applyBrand(name, color) {
    if (typeof name !== "string" || name.trim() === "") {
      name = DEFAULT_NAME;
    }
    name = name.trim();
    if (typeof color !== "string" || !/^#[0-9a-f]{6}$/i.test(color)) {
      color = DEFAULT_COLOR;
    }
    const white = [255, 255, 255];
    const ink = [23, 33, 43];
    const black = [0, 0, 0];
    const brand = hexRgb(color);
    const onBrand = contrast(brand, white) >= contrast(brand, ink)
      ? white : ink;
    const soft = mix(brand, white, 0.9);
    let strong = brand;
    for (let i = 0; i < 40 && contrast(strong, soft) < 4.6; i++) {
      strong = mix(strong, black, 0.08);
    }
    const style = document.documentElement.style;
    style.setProperty("--brand", color);
    style.setProperty("--on-brand", rgbHex(onBrand));
    style.setProperty("--brand-soft", rgbHex(soft));
    style.setProperty("--brand-ink", rgbHex(strong));
    style.setProperty("--brand-edge", rgbHex(mix(brand, black, 0.18)));
    document.getElementById("brand-name").textContent = name;
    document.title = name;
    try {
      /* The tab icon: the bank icon of the top bar on the bank's colour. */
      const svg = "<svg xmlns='http://www.w3.org/2000/svg' " +
        "viewBox='0 0 32 32'>" +
        "<rect width='32' height='32' rx='3' fill='" + color + "'/>" +
        "<path d='" + ICONS.bank + "' transform='translate(4 4)' " +
        "fill='none' stroke='" + rgbHex(onBrand) + "' stroke-width='2' " +
        "stroke-linecap='round' stroke-linejoin='round'/></svg>";
      document.getElementById("favicon").setAttribute("href",
        "data:image/svg+xml," + encodeURIComponent(svg));
    } catch (error) {
      /* Only the tab icon is missing; the bank itself still opens. */
    }
    try {
      window.sessionStorage.setItem(BRAND_KEY,
        JSON.stringify({ name: name, color: color }));
    } catch (error) {
      /* Not needed for anything important. */
    }
  }

  function lastBrand() {
    try {
      const saved = JSON.parse(window.sessionStorage.getItem(BRAND_KEY));
      if (saved && typeof saved === "object") {
        return saved;
      }
    } catch (error) {
      /* Nothing saved. */
    }
    return { name: DEFAULT_NAME, color: DEFAULT_COLOR };
  }

  function bankName() {
    return document.getElementById("brand-name").textContent;
  }

  function todayText() {
    return app.state && app.state.today ? show(app.state.today) : "";
  }

  function applyState(state) {
    applyBrand(state.bank_name, state.bank_color);
    document.getElementById("today").textContent =
      state.today ? fmtDate(state.today, todayFormat) : "";
    const who = document.getElementById("who");
    const customer = state.customer;
    if (customer && typeof customer === "object") {
      document.getElementById("who-name").textContent = show(customer.name);
      document.getElementById("who-no").textContent =
        "Müşteri no " + show(customer.no);
      who.hidden = false;
    } else {
      who.hidden = true;
    }
  }

  /* Start, login and logout */

  async function boot(flash) {
    const hadToken = app.token !== "";
    const state = await post("/api/state");
    if (state.offline) {
      showOffline(state.offline);
      showStopped();
      return;
    }
    if (state.fatal) {
      showFatal(state.fatal);
      showStopped();
      return;
    }
    hideBanner();
    app.state = state;
    applyState(state);
    if (state.customer) {
      showApp(flash);
      return;
    }
    setToken("");
    if (!flash && hadToken) {
      flash = { login: { kind: "warn",
        text: "Oturumunuz kapanmış; yeniden giriş yapın." } };
    }
    showLogin(flash);
  }

  async function sessionGone() {
    if (app.view !== "app") {
      return true;
    }
    const state = await post("/api/state", null, { quiet: true });
    if (app.view !== "app") {
      return true;
    }
    if (state.offline || state.fatal || state.customer) {
      return false;
    }
    app.state = state;
    setToken("");
    applyState(state);
    showLogin({ login: { kind: "warn",
      text: "Oturumunuz kapanmış; yeniden giriş yapın." } });
    return true;
  }

  function showStopped() {
    app.view = "stopped";
    document.getElementById("who").hidden = true;
    fill(main, h("section", { class: "card stopped" },
      h("h1", null, "Bankanız şu an açılamıyor"),
      h("p", null, "Sayfanın en üstündeki sorunu giderdikten sonra yeniden " +
        "deneyin."),
      h("div", { class: "actions" },
        h("button", { type: "button", class: "btn btn-primary",
          onclick: function () { boot(); } }, "Yeniden dene"))));
  }

  function showLogin(flash) {
    flash = flash || {};
    app.view = "login";
    app.tab = "";
    /* The next login starts at Hesaplarım, not at the last tab. */
    try {
      if (window.location.hash) {
        window.history.replaceState(null, "", window.location.pathname +
          window.location.search);
      }
    } catch (error) {
      /* The address bar keeps its old hash. */
    }
    const state = app.state || {};
    const login = state.login;
    const ready = !login || typeof login !== "object" || sectionOk(login);

    const loginArea = messageArea();
    const loginCard = h("section", { class: "card",
      "aria-labelledby": "login-title" },
    h("h2", { id: "login-title" }, "Giriş yap"));

    if (ready) {
      const number = input("login-no", { inputmode: "numeric",
        autocomplete: "username", pattern: DIGITS, title: DIGITS_TITLE,
        required: true, value: flash.prefill || null });
      const password = input("login-password", { type: "password",
        autocomplete: "current-password", required: true });
      const button = primary("Giriş yap", "login");
      const form = h("form", { class: "form" },
        field("login-no", "Müşteri numarası", number),
        field("login-password", "Şifre", password),
        h("div", { class: "actions" }, button), loginArea);
      form.addEventListener("submit", async function (event) {
        event.preventDefault();
        const data = await busy(button, function () {
          return post("/api/login", { customer_no: number.value.trim(),
            password: password.value });
        });
        if (!actionOk(loginArea, data)) {
          return;
        }
        if (data.status === "ok" && data.session) {
          setToken(data.session);
          boot({ focus: true });
          return;
        }
        const kind = data.status === "locked" ? "error" : "warn";
        say(loginArea, note(kind,
          show(data.message || "Giriş yapılamadı.")));
        password.value = "";
        password.focus();
      });
      loginCard.append(h("p", { class: "muted" },
        "Müşteri numaranız ve şifrenizle girin."), form,
      h("p", { class: "muted" }, "Deneme şifreleri: 1001 kedi123, " +
        "1002 deniz42, 1003 kalem7."));
      if (flash.focus) {
        setTimeout(function () { number.focus(); }, 0);
      }
    } else {
      if (login.error) {
        loginCard.append(errorNote(login.error));
      } else {
        loginCard.append(note("todo",
          "2. görev yazılınca şifreyle giriş açılır."));
      }
      loginCard.append(h("p", null,
        "Şimdilik listeden bir müşteri seçerek girebilirsiniz:"),
      demoList(state.demo, loginArea), loginArea);
      if (flash.focus) {
        setTimeout(function () {
          const first = loginCard.querySelector(".demo-btn");
          if (first) {
            first.focus();
          }
        }, 0);
      }
    }
    if (flash.login) {
      say(loginArea, note(flash.login.kind, flash.login.text), true);
    }

    fill(main, h("div", { class: "login" },
      h("div", { class: "login-intro" },
        h("h1", null, bankName() + " internet şubesi"),
        h("p", null, "Hesaplarınız, kartlarınız, para gönderme, döviz, " +
          "kredi ve ATM işlemleriniz burada.")),
      h("div", { class: "grid" }, loginCard,
        registerCard(ready, flash.register))));
  }

  function demoList(demo, area) {
    const people = Array.isArray(demo) ? demo : [];
    if (people.length === 0) {
      return h("p", { class: "muted" }, "Listede müşteri yok.");
    }
    return h("ul", { class: "demo-list" }, people.map(function (person) {
      const button = h("button", { type: "button", class: "demo-btn" },
        h("strong", null, show(person.name)), h("span", null,
          show(person.no)));
      button.addEventListener("click", async function () {
        const data = await busy(button, function () {
          return post("/api/demo_login", { customer_no: person.no });
        });
        if (typeof data.refused === "string") {
          boot({ login: { kind: "warn", text: data.refused } });
          return;
        }
        if (!actionOk(area, data)) {
          return;
        }
        if (data.session) {
          setToken(data.session);
          boot({ focus: true });
        }
      });
      return h("li", null, button);
    }));
  }

  function registerCard(ready, flash) {
    const area = messageArea();
    const name = input("register-name", { maxlength: "20", required: true });
    const password = input("register-password", { type: "password",
      autocomplete: "new-password", required: true });
    const button = primary("Müşteri ol");
    const form = h("form", { class: "form" },
      field("register-name", "Adınız", name),
      field("register-password", "Şifre", password, PASSWORD_RULES),
      h("div", { class: "actions" }, button), area);
    form.addEventListener("submit", async function (event) {
      event.preventDefault();
      const data = await busy(button, function () {
        return post("/api/register", { name: name.value,
          password: password.value });
      });
      if (!actionOk(area, data)) {
        return;
      }
      if (!data.ok) {
        say(area, note("warn", show(data.message) ||
          "Bu şifre bankanın kurallarına uymuyor."));
        password.focus();
        return;
      }
      const number = show(data.customer_no);
      const message = [
        "Kaydınız açıldı. Müşteri numaranız ", h("strong", null, number),
        ". TL hesabınızın IBAN'ı ",
        h("span", { class: "iban" }, groupIban(data.iban)),
        "; hesabınıza 1.000 TL hoş geldin hediyesi yattı. ",
        ready ? "Bu numara ve şifrenizle giriş yapabilirsiniz."
          : "Şifreyle giriş 2. görev yazılınca açılır; şimdilik listeden " +
            "seçerek girebilirsiniz."
      ];
      const state = await post("/api/state");
      if (!state.offline && !state.fatal) {
        app.state = state;
        applyState(state);
      }
      showLogin({ register: message, prefill: number });
    });
    if (flash) {
      say(area, note("ok", flash), true);
    }
    return h("section", { class: "card", "aria-labelledby": "register-title" },
      h("h2", { id: "register-title" }, "Yeni müşteri ol"),
      h("p", { class: "muted" }, "Kayıt olunca bir müşteri numarası ve bir TL " +
        "hesabı alırsınız."),
      form);
  }

  async function logout() {
    await post("/api/logout", null, { quiet: true });
    setToken("");
    boot({ login: { kind: "ok", text: "Çıkış yaptınız." }, focus: true });
  }

  async function resetData() {
    const sure = window.confirm("Bütün veriler ilk haline dönecek: " +
      "yaptığınız gönderimler, harcamalar ve yeni müşteri kayıtları " +
      "silinecek. Emin misiniz?");
    if (!sure) {
      return;
    }
    const button = document.getElementById("reset");
    const data = await busy(button, function () {
      return post("/api/reset", null, { quiet: true });
    });
    if (data.offline) {
      showOffline(data.offline);
      return;
    }
    if (data.fatal) {
      showFatal(data.fatal);
      return;
    }
    setToken("");
    boot({ login: { kind: "ok", text: "Veriler ilk haline döndü." },
      focus: true });
  }

  /* The app after login: tabs */

  function showApp(flash) {
    app.view = "app";
    app.paid = [];
    app.branch = null;
    app.prefill = null;
    app.waits = { "/api/state": app.waits["/api/state"] || [] };
    app.surveyed = false;
    const tablist = h("div", { class: "tabs", role: "tablist",
      "aria-label": "Bölümler" });
    const panels = h("div", { class: "panels" });
    TABS.forEach(function (tab) {
      tablist.append(h("button", { type: "button", role: "tab",
        class: "tab", id: "tab-" + tab.id, "aria-controls": "panel-" + tab.id,
        "aria-selected": "false", tabindex: "-1",
        onclick: function () { selectTab(tab.id, false, true); } },
      icon(tab.icon, 20), h("span", { class: "tab-text" },
        h("span", { class: "tab-label" }, tab.label), badge(tab.task))));
      panels.append(h("section", { class: "panel", role: "tabpanel",
        id: "panel-" + tab.id, "aria-labelledby": "tab-" + tab.id,
        hidden: true }));
    });
    tablist.addEventListener("keydown", function (event) {
      let index = -1;
      TABS.forEach(function (tab, i) {
        if (tab.id === app.tab) {
          index = i;
        }
      });
      let next = -1;
      if (event.key === "ArrowRight") {
        next = (index + 1) % TABS.length;
      } else if (event.key === "ArrowLeft") {
        next = (index - 1 + TABS.length) % TABS.length;
      } else if (event.key === "Home") {
        next = 0;
      } else if (event.key === "End") {
        next = TABS.length - 1;
      }
      if (next < 0) {
        return;
      }
      event.preventDefault();
      selectTab(TABS[next].id, true, true);
    });
    fill(main, tablist, panels);
    const wanted = window.location.hash.slice(1);
    let first = TABS[0].id;
    TABS.forEach(function (tab) {
      if (tab.id === wanted) {
        first = tab.id;
      }
    });
    selectTab(first, Boolean(flash && flash.focus), false);
    survey();
  }

  function selectTab(id, focus, byUser) {
    app.tab = id;
    let chosen = null;
    TABS.forEach(function (tab) {
      const button = document.getElementById("tab-" + tab.id);
      const panel = document.getElementById("panel-" + tab.id);
      const on = tab.id === id;
      button.setAttribute("aria-selected", on ? "true" : "false");
      button.tabIndex = on ? 0 : -1;
      panel.hidden = !on;
      if (on) {
        chosen = tab;
        if (focus) {
          button.focus();
        }
      }
    });
    if (byUser) {
      const strip = document.querySelector(".tabs");
      const top = strip.parentElement.offsetTop;
      if (window.scrollY > top) {
        window.scrollTo(0, top);
      }
    }
    try {
      window.history.replaceState(null, "", "#" + id);
    } catch (error) {
      /* The address bar keeps its old hash. */
    }
    chosen.render(document.getElementById("panel-" + id));
  }

  function rerender(id, flash) {
    if (app.view !== "app") {
      return;
    }
    TABS.forEach(function (tab) {
      if (tab.id === id) {
        tab.render(document.getElementById("panel-" + id), flash);
      }
    });
  }

  /* Each render takes a ticket; an answer that arrives after a newer
     render started is thrown away. */
  function ticket(element) {
    element.ticket = (element.ticket || 0) + 1;
    return element.ticket;
  }

  function stale(element, number) {
    return element.ticket !== number || !element.isConnected;
  }

  function loading(panel, head) {
    if (!panel.firstChild) {
      fill(panel, head, h("p", { class: "loading" }, "Yükleniyor"));
    }
  }

  /* Shared pieces of the accounts answer */

  function tlAccounts(data) {
    if (!sectionOk(data.accounts)) {
      return null;
    }
    const ok = data.accounts.ok;
    const found = [];
    if (ok && Array.isArray(ok.accounts)) {
      ok.accounts.forEach(function (account) {
        if (isObject(account) && account.currency === "TL") {
          found.push(account);
        }
      });
    }
    return found;
  }

  function aliasNames(list) {
    const names = [];
    (Array.isArray(list) ? list : []).forEach(function (row) {
      if (isObject(row) && row.alias) {
        names.push(show(row.alias));
      }
    });
    return names;
  }

  function tlIbanOf(data) {
    if (!isObject(data)) {
      return "";
    }
    const accounts = tlAccounts(data);
    if (accounts && accounts.length) {
      return cleanIban(accounts[0].iban);
    }
    const aliases = Array.isArray(data.aliases) ? data.aliases : [];
    for (let i = 0; i < aliases.length; i++) {
      if (isObject(aliases[i]) && aliases[i].iban) {
        return cleanIban(aliases[i].iban);
      }
    }
    return "";
  }

  /* Hesaplarım (task 1) */

  async function renderAccounts(panel) {
    const number = ticket(panel);
    const head = panelHead("Hesaplarım", "Bakiyeleriniz, her ay " +
      "hesaplarınıza giren ve çıkan para, hesap hareketleriniz.");
    loading(panel, head);
    const data = await getAccounts();
    if (stale(panel, number) || !pageOk(panel, [head], data)) {
      return;
    }
    fill(panel, head, factsRow(data), paidCard(data.orders_run),
      recentCard(data.recent), accountsView(data));
  }

  function fact(label, value) {
    return h("li", { class: "chip-line" }, label + ":",
      h("strong", null, value));
  }

  function factsRow(data) {
    const items = [];
    const branch = data.branch;
    if (isObject(branch) && branch.code) {
      items.push(fact("Şubeniz", show(branch.name) + " (" +
        show(branch.code) + ")"));
    }
    const aliases = aliasNames(data.aliases);
    if (aliases.length) {
      items.push(fact(aliases.length > 1 ? "Kolay Adresleriniz"
        : "Kolay Adresiniz", aliases.join(", ")));
    }
    if (sectionOk(data.accounts) && isObject(data.accounts.ok) &&
        data.accounts.ok.skipped !== undefined) {
      items.push(fact("Atlanan bozuk satır", num(data.accounts.ok.skipped)));
    }
    if (sectionOk(data.orders_run) && app.paid.length === 0) {
      items.push(fact("Bugün ödenecek talimat", "yok"));
    }
    return items.length ? h("ul", { class: "facts-row" }, items) : null;
  }

  function paidCard(run) {
    const title = "Bugünkü otomatik ödemeler";
    if (!sectionOk(run)) {
      return partCard("paid", title, 3, null, sectionView(run, null));
    }
    if (!Array.isArray(run.ok)) {
      return partCard("paid", title, 3, null, note("error", SHAPE_TEXT));
    }
    if (app.paid.length === 0) {
      return null;
    }
    let failed = false;
    app.paid.forEach(function (order) {
      if (!order.ok) {
        failed = true;
      }
    });
    return partCard("paid", title, 3, "Talimatlarınızdan günü bugün olanlar.",
      h("ul", { class: "moves" }, app.paid.map(paidItem)),
      failed ? h("p", { class: "hint" }, "Ödenemeyen talimat, bugün " +
        "Hesaplarım'ı her açtığınızda yeniden denenir.") : null);
  }

  function paidItem(order) {
    const good = Boolean(order.ok);
    return h("li", { class: "move" },
      h("div", { class: "move-main" },
        h("span", { class: "move-desc" }, show(order.description) ||
          "Talimat"),
        h("span", { class: "move-meta" }, "Alıcı: " + party(order.receiver)),
        h("span", { class: good ? "status is-ok" : "status is-bad" },
          icon(good ? "ok" : "warn"),
          h("span", null, good ? show(order.message)
            : "Ödenemedi: " + show(order.message)))),
      h("span", { class: "amount" }, money(order.amount)));
  }

  function recentCard(result) {
    return partCard("recent", "Son gönderdikleriniz", 3,
      "Birine basınca Para gönder bu alıcıyla açılır.",
      sectionView(result, recentView));
  }

  function recentView(list) {
    if (!Array.isArray(list)) {
      throw new Error("not a list");
    }
    if (list.length === 0) {
      return h("p", { class: "muted" }, "Henüz kimseye para göndermediniz.");
    }
    return h("ul", { class: "recent-list" }, list.map(function (row) {
      row = isObject(row) ? row : {};
      const iban = cleanIban(row.iban);
      let name = show(row.name);
      if (!name) {
        name = iban.slice(4, 9) === OUR_BANK_CODE ? "Hesap"
          : "Başka banka hesabı";
      }
      return h("li", null, h("button", { type: "button", class: "recent-btn",
        "aria-label": "Para gönder: " + name + ", " + show(row.masked),
        onclick: function () { sendTo(iban); } },
      h("strong", null, name),
      h("span", { class: "iban" }, show(row.masked))));
    }));
  }

  function sendTo(iban) {
    app.prefill = { receiver: iban };
    selectTab("gonder", false, true);
  }

  function labelledNote(title, result) {
    if (sectionOk(result)) {
      return null;
    }
    return h("div", { class: "stack-tight" }, h("h4", null, title),
      sectionView(result, null));
  }

  /* Balances come from the accounts section, the movements and the
     monthly table from their own sections; each account gets one card
     and a missing part shows its todo box inside that card. */
  function accountsView(data) {
    const entries = [];
    const seen = {};
    const addEntry = function (iban, currency, balance, known) {
      iban = cleanIban(iban);
      if (!iban || seen[iban]) {
        return;
      }
      seen[iban] = true;
      entries.push({ iban: iban, currency: currency, balance: balance,
        known: known });
    };
    const accountsOk = sectionOk(data.accounts);
    if (accountsOk) {
      const ok = data.accounts.ok;
      if (!isObject(ok) || !Array.isArray(ok.accounts)) {
        return partCard("accounts", "Hesaplarınız", null, null,
          note("error", SHAPE_TEXT));
      }
      ok.accounts.forEach(function (account) {
        if (isObject(account)) {
          addEntry(account.iban, show(account.currency), account.balance,
            true);
        }
      });
      if (entries.length === 0) {
        return h("p", { class: "card muted" },
          "Adınıza açılmış bir hesap yok.");
      }
    } else {
      [data.history, data.flow].forEach(function (result) {
        if (sectionOk(result) && isObject(result.ok)) {
          Object.keys(result.ok).forEach(function (iban) {
            addEntry(iban, "", null, false);
          });
        }
      });
    }
    if (entries.length === 0) {
      return partCard("accounts", "Hesaplarınız", null, null,
        labelledNote("Bakiyeler", data.accounts),
        labelledNote("Hesap hareketleri", data.history),
        labelledNote("Aylık giren ve çıkan", data.flow));
    }
    return [accountsOk ? null : labelledNote("Bakiyeler", data.accounts),
      entries.map(function (entry) { return accountCard(entry, data); })];
  }

  function copyButton(text) {
    const button = h("button", { type: "button", class: "btn-link" },
      "IBAN'ı kopyala");
    button.addEventListener("click", async function () {
      let done = false;
      try {
        await navigator.clipboard.writeText(text);
        done = true;
      } catch (error) {
        done = false;
      }
      button.textContent = done ? "Kopyalandı" : "Kopyalanamadı";
      setTimeout(function () { button.textContent = "IBAN'ı kopyala"; },
        1800);
    });
    return button;
  }

  function accountCard(entry, data) {
    const iban = entry.iban;
    const currency = entry.currency;
    const titleId = "account-" + iban;
    const flowId = "flow-" + iban;
    return h("article", { class: "card account", "aria-labelledby": titleId },
      h("div", { class: "account-head" },
        h("div", { class: "account-id" },
          h("h3", { id: titleId }, currency ? currency + " hesabı" : "Hesap"),
          h("p", { class: "iban" }, groupIban(iban)),
          copyButton(iban)),
        entry.known ? h("div", { class: "balance" },
          h("span", { class: "balance-label" }, "Bakiye"),
          h("span", { class: "balance-value amount" },
            money(entry.balance, currency))) : null),
      h("div", { class: "account-body" },
        h("div", { class: "stack-tight" },
          h("h4", null, "Hesap hareketleri"),
          sectionView(data.history, function (all) {
            return movesView(all, iban, currency);
          })),
        h("div", { class: "stack-tight" },
          h("h4", { id: flowId }, "Aylık giren ve çıkan"),
          sectionView(data.flow, function (all) {
            return flowView(all, iban, currency, flowId);
          }))));
  }

  function movesView(all, iban, currency) {
    if (!isObject(all)) {
      throw new Error("not a dict");
    }
    const rows = Array.isArray(all[iban]) ? all[iban] : [];
    if (rows.length === 0) {
      return h("p", { class: "muted" }, "Bu hesapta henüz hareket yok.");
    }
    const item = function (row) { return moveItem(row, currency); };
    const first = rows.slice(0, VISIBLE_MOVES);
    const rest = rows.slice(VISIBLE_MOVES);
    return [h("ul", { class: "moves" }, first.map(item)),
      rest.length === 0 ? null
        : h("details", { class: "more" },
          h("summary", null, "Daha eski hareketler (" + rest.length + ")"),
          h("ul", { class: "moves" }, rest.map(item)))];
  }

  function moveItem(row, currency) {
    row = isObject(row) ? row : {};
    const amount = row.amount;
    const outgoing = isNumber(amount) && amount < 0;
    return h("li", { class: "move" },
      h("div", { class: "move-main" },
        h("span", { class: "move-desc" },
          show(row.description) || "Açıklama yok"),
        h("span", { class: "move-meta" }, fmtDate(row.date, dayFormat) +
          " · " + (outgoing ? "Alıcı: " : "Gönderen: ") + party(row.other))),
      h("span", { class: outgoing ? "amount" : "amount is-in" },
        signedMoney(amount, currency)));
  }

  function flowView(all, iban, currency, labelId) {
    if (!isObject(all)) {
      throw new Error("not a dict");
    }
    const rows = Array.isArray(all[iban]) ? all[iban] : [];
    if (rows.length === 0) {
      return h("p", { class: "muted" }, "Bu hesapta henüz hareket yok.");
    }
    const chart = columnChart(currency || "", [
      { label: "Giren", kind: "in" }, { label: "Çıkan", kind: "out" }],
    rows.map(function (row) {
      row = isObject(row) ? row : {};
      const name = monthName(row.month);
      return { label: rows.length > 4 ? name.slice(0, 3) : name,
        bars: [{ value: row.in, title: name + ", giren: " +
          money(row.in, currency) },
        { value: row.out, title: name + ", çıkan: " +
          money(row.out, currency) }] };
    }), false);
    return [chart, h("div", { class: "table-wrap" }, h("table",
      { class: "flow", "aria-labelledby": labelId },
      tableHead([["Ay"], ["Giren", true], ["Çıkan", true], ["Fark", true]]),
      h("tbody", null, rows.map(function (row) {
        row = isObject(row) ? row : {};
        let diff = null;
        if (isNumber(row.in) && isNumber(row.out)) {
          diff = row.in - row.out;
        }
        return h("tr", null,
          h("th", { scope: "row" }, monthName(row.month)),
          h("td", { class: "num is-in" }, money(row.in, currency)),
          h("td", { class: "num" }, money(row.out, currency)),
          h("td", { class: diff > 0 ? "num is-in" : "num" },
            diff === null ? "" : signedMoney(diff, currency)));
      }))))];
  }

  /* Şubeler (task 1) */

  async function renderBranches(panel) {
    const number = ticket(panel);
    const head = panelHead("Şubeler", "Bankanın şubeleri: her şubenin " +
      "müşteri sayısı ve TL hesaplarındaki toplam para.");
    loading(panel, head);
    const answers = await Promise.all([post("/api/branches"),
      getAccounts()]);
    const data = answers[0];
    if (stale(panel, number) || !pageOk(panel, [head], data)) {
      return;
    }
    const mine = isObject(app.branch) ? show(app.branch.code) : "";
    fill(panel, head,
      partCard("branch-report", "Şube raporu", null,
        "Toplamı en büyük şube başta.",
        sectionView(data.branches, function (list) {
          return branchTable(list, mine);
        })),
      ibanParts(tlIbanOf(answers[1])));
  }

  function branchTable(list, mine) {
    if (!Array.isArray(list)) {
      throw new Error("not a list");
    }
    if (list.length === 0) {
      return h("p", { class: "muted" }, "Raporda şube yok.");
    }
    let largest = 0;
    list.forEach(function (row) {
      if (isObject(row) && isNumber(row.total) && row.total > largest) {
        largest = row.total;
      }
    });
    return h("div", { class: "table-wrap" }, h("table",
      { class: "branches", "aria-labelledby": "branch-report-title" },
      tableHead([["Şube"], ["Şube kodu"], ["Müşteri", true],
        ["TL hesaplarındaki toplam", true]]),
      h("tbody", null, list.map(function (row) {
        row = isObject(row) ? row : {};
        let share = 0;
        if (isNumber(row.total) && largest > 0 && row.total > 0) {
          share = row.total / largest;
        }
        const own = mine !== "" && show(row.code) === mine;
        return h("tr", { class: own ? "is-mine" : null },
          h("th", { scope: "row" }, show(row.name),
            own ? h("span", { class: "tag tag-brand" }, "Sizin şubeniz")
              : null),
          h("td", null, h("span", { class: "iban" }, show(row.code))),
          h("td", { class: "num" }, num(row.customers)),
          h("td", { class: "num" },
            h("span", { class: "amount" }, money(row.total)),
            h("span", { class: "cell-bar" }, meter(share, show(row.name) +
              ": " + money(row.total)))));
      }))));
  }

  function ibanParts(iban) {
    if (!/^TR\d{24}$/.test(iban)) {
      return null;
    }
    const parts = [
      [iban.slice(0, 4), "Ülke ve kontrol"],
      [iban.slice(4, 9), "Banka kodu"],
      [iban.slice(9, 10), "Yedek hane"],
      [iban.slice(10, 14), "Şube kodu", true],
      [iban.slice(14, 18), "Müşteri no"],
      [iban.slice(18), "Hesap sırası"]
    ];
    return partCard("iban-parts", "IBAN'ınızın parçaları", null,
      "Şube kodu, hesap numarasının ilk dört hanesidir: iban[10:14]. " +
      "Havalede gönderenle alıcının şube kodu aynıysa masraf yok.",
      h("ol", { class: "iban-parts" }, parts.map(function (part) {
        return h("li", { class: part[2] ? "is-branch" : null },
          h("span", { class: "iban-part" }, part[0]),
          h("span", { class: "iban-label" }, part[1]));
      })));
  }

  /* Para gönder (task 3) */

  async function renderTransfer(panel, flash) {
    flash = flash || {};
    const number = ticket(panel);
    const head = panelHead("Para gönder", "Havale, EFT ya da Kolay " +
      "Adres'le gönderim; her ay tekrarlanan ödemeler için talimat.");
    const fees = feeBoxes();
    loading(panel, [head, fees]);
    const answers = await Promise.all([getAccounts(), post("/api/orders")]);
    const data = answers[0];
    if (stale(panel, number) || !pageOk(panel, [head, fees], data)) {
      return;
    }
    const accounts = tlAccounts(data);
    fill(panel, head, fees,
      h("div", { class: "split" }, transferCard(data, accounts, fees, flash),
        aliasCard(data, flash)),
      ordersCard(answers[1], data, accounts, flash));
    usePrefill();
  }

  function feeBoxes() {
    return h("div", { class: "stack-tight" },
      h("ul", { class: "fees", "aria-label": "Gönderim masrafları" },
        feeBox("same", "Aynı şubeye havale", "Masrafsız"),
        feeBox("branch", "Başka şubeye havale", money(BRANCH_FEE)),
        feeBox("eft", "Başka bankaya EFT", money(EFT_FEE))),
      h("p", { class: "hint" }, "Bir hesaptan günde en çok " +
        money(DAILY_LIMIT) + " gönderilebilir."));
  }

  function feeBox(kind, label, value) {
    return h("li", { class: "fee", "data-fee": kind },
      h("span", { class: "fee-label" }, label), h("strong", null, value));
  }

  function markFee(fees, kind) {
    fees.querySelectorAll("[data-fee]").forEach(function (box) {
      box.classList.toggle("is-active",
        box.getAttribute("data-fee") === kind);
    });
  }

  function transferCard(data, accounts, fees, flash) {
    let body = null;
    if (accounts === null) {
      body = sectionView(data.accounts, null);
    } else if (accounts.length === 0) {
      body = h("p", { class: "muted" },
        "Gönderim yapabileceğiniz bir TL hesabınız yok.");
    } else {
      body = transferForm(accounts, fees, flash);
    }
    return partCard("send", "Yeni gönderim", null, null, body);
  }

  function transferForm(accounts, fees, flash) {
    const area = messageArea();
    const from = accountChoice("send-from", accounts, flash.sender);
    const to = input("send-to", { required: true, autocapitalize: "off" });
    const hint = h("p", { class: "hint", id: "send-to-hint" },
      "IBAN ya da alıcının Kolay Adres'i (e-posta adresi).");
    const status = h("p", { class: "iban-status", id: "send-to-status",
      "aria-live": "polite" });
    to.setAttribute("aria-describedby", "send-to-hint send-to-status");
    const amount = amountInput("send-amount", { pattern: SIGNED });
    const description = input("send-description", { maxlength: "40",
      required: true });
    const button = primary("Gönder", "send");
    const form = h("form", { class: "form" },
      field("send-from", "Gönderen hesap", from),
      h("div", { class: "field" },
        h("label", { for: "send-to" }, "Alıcı"), to, hint, status),
      h("div", { class: "row-2" },
        field("send-amount", "Tutar (TL)", amount),
        field("send-description", "Açıklama", description)),
      h("div", { class: "actions" }, button), area);

    watchReceiver(to, status, from, fees);
    form.addEventListener("submit", async function (event) {
      event.preventDefault();
      const data = await busy(button, function () {
        return post("/api/transfer", { sender: from.value,
          receiver: to.value, amount: amount.value.trim(),
          description: description.value });
      });
      if (!actionOk(area, data)) {
        return;
      }
      if (data.ok) {
        rerender("gonder", { sender: from.value,
          send: { kind: "ok", text: show(data.message) } });
      } else {
        say(area, note("warn", show(data.message)));
      }
    });
    flashNote(area, flash.send);
    return form;
  }

  function usePrefill() {
    const wanted = app.prefill;
    app.prefill = null;
    const to = document.getElementById("send-to");
    if (!wanted || !to) {
      return;
    }
    to.value = groupIban(wanted.receiver);
    to.dispatchEvent(new Event("input"));
    const amount = document.getElementById("send-amount");
    if (amount) {
      amount.focus();
    }
  }

  function ibanStatus(element, field, kind, content) {
    element.className = "iban-status" + (kind ? " is-" + kind : "");
    element.replaceChildren();
    field.setAttribute("aria-invalid", kind === "bad" ? "true" : "false");
    if (!content) {
      return;
    }
    const icons = { ok: "ok", bad: "bad", todo: "todo", error: "error" };
    add(element, icons[kind] ? icon(icons[kind]) : null);
    add(element, h("span", null, content));
  }

  /* Live receiver check while the user types: app.py resolves a Kolay
     Adres with resolve_receiver and checks the IBAN with iban_valid
     (task 3). The fee depends on the sender too, so a change of the
     sender redraws the last answer. */
  function watchReceiver(field, status, sender, fees) {
    let timer = null;
    let round = 0;
    let last = null;

    function draw() {
      markFee(fees, "");
      if (!last) {
        return;
      }
      const data = last.data;
      const mail = last.text.indexOf("@") >= 0;
      if (data.sessionGone) {
        return;
      }
      if (data.offline) {
        ibanStatus(status, field, "error", offlineText(data.offline));
        return;
      }
      if (data.fatal) {
        showFatal(data.fatal);
        ibanStatus(status, field, "error", problemNodes(data.fatal));
        return;
      }
      if (data.todo) {
        ibanStatus(status, field, "todo", "Alıcı kontrolü " +
          (data.todo.task || 3) + ". görevi yazınca açılacak: bank.py'de " +
          show(data.todo.function) + ".");
        return;
      }
      if (typeof data.refused === "string") {
        ibanStatus(status, field, "hint", data.refused);
        return;
      }
      const iban = cleanIban(data.iban);
      if (!data.valid) {
        ibanStatus(status, field, "bad", mail
          ? "Bu Kolay Adres bir hesaba bağlı değil."
          : "Geçersiz IBAN: bir karakteri yanlış yazılmış olabilir.");
        return;
      }
      if (iban === sender.value) {
        ibanStatus(status, field, "bad", "Bu, gönderen hesabın kendisi.");
        return;
      }
      if (!data.same_bank) {
        markFee(fees, "eft");
        ibanStatus(status, field, "ok", "Geçerli IBAN, başka bir bankada. " +
          "EFT masrafı " + money(EFT_FEE) + ".");
        return;
      }
      if (data.currency && data.currency !== "TL") {
        ibanStatus(status, field, "bad", "Bu bir " + show(data.currency) +
          " hesabı; yalnız TL hesaplarına para gönderebilirsiniz.");
        return;
      }
      if (!data.name) {
        ibanStatus(status, field, "bad",
          "Bankamızda bu IBAN'la bir hesap yok.");
        return;
      }
      const same = iban.slice(10, 14) === show(sender.value).slice(10, 14);
      markFee(fees, same ? "same" : "branch");
      ibanStatus(status, field, "ok", [
        "Alıcı: ", h("strong", null, show(data.name)), ", ",
        h("span", { class: "iban" }, show(data.masked)), ", ",
        show(data.branch) + " şubesi. ",
        same ? "Aynı şube: masrafsız."
          : "Başka şube: " + money(BRANCH_FEE) + " masraf."]);
    }

    field.addEventListener("input", function () {
      clearTimeout(timer);
      round += 1;
      const mine = round;
      last = null;
      markFee(fees, "");
      const text = field.value.trim();
      if (text === "") {
        ibanStatus(status, field, "", null);
        return;
      }
      if (text.indexOf("@") >= 0) {
        if (!/^[^@\s]+@[^@\s]+\.[^@\s]+$/.test(text)) {
          ibanStatus(status, field, "hint", "Kolay Adres, ad@alan.uzantı " +
            "gibi bir e-posta adresidir.");
          return;
        }
      } else if (cleanIban(text).length !== 26) {
        ibanStatus(status, field, "hint", "IBAN 26 karakterdir; şu an " +
          cleanIban(text).length + ".");
        return;
      }
      timer = setTimeout(async function () {
        const data = await post("/api/iban_check", { iban: text });
        if (mine !== round) {
          return;
        }
        last = { text: text, data: data };
        draw();
      }, 250);
    });
    sender.addEventListener("change", draw);
  }

  function aliasCard(data, flash) {
    const area = messageArea();
    const alias = input("alias-new", { required: true, maxlength: "60",
      inputmode: "email", autocapitalize: "off" });
    const button = primary("Kolay Adres ekle");
    const form = h("form", { class: "form" },
      field("alias-new", "E-posta adresi", alias,
        "Adres TL hesabınıza bağlanır."),
      h("div", { class: "actions" }, button), area);
    form.addEventListener("submit", async function (event) {
      event.preventDefault();
      const answer = await busy(button, function () {
        return post("/api/alias_add", { alias: alias.value });
      });
      if (!actionOk(area, answer)) {
        return;
      }
      if (answer.ok) {
        rerender("gonder", { alias: { kind: "ok",
          text: show(answer.message) } });
      } else {
        say(area, note("warn", show(answer.message)));
      }
    });
    flashNote(area, flash.alias);
    return partCard("alias", "Kolay Adres", null, "Size para gönderecek " +
      "kişi IBAN'ınız yerine e-posta adresinizi yazabilir.",
    h("div", { class: "stack-tight" }, h("h4", null, "Adresleriniz"),
      chips(aliasNames(data.aliases), "Henüz bir Kolay Adresiniz yok.")),
    form);
  }

  function ordersCard(answer, data, accounts, flash) {
    const problem = answerProblem(answer, false);
    let list = null;
    if (!problem) {
      list = Array.isArray(answer.orders) ? answer.orders : [];
    }
    let form = null;
    if (accounts === null) {
      form = sectionView(data.accounts, null);
    } else if (accounts.length === 0) {
      form = h("p", { class: "muted" },
        "Talimat verebileceğiniz bir TL hesabınız yok.");
    } else {
      form = orderForm(accounts, flash);
    }
    return partCard("orders", "Talimatlarım", null, "Günü gelen talimat, " +
      "o gün Hesaplarım'ı açtığınızda kendiliğinden ödenir.",
    h("div", { class: "split" },
      h("div", { class: "stack-tight" }, h("h4", null, "Talimatlarınız"),
        problem || ordersTable(list)),
      h("div", { class: "stack-tight" }, h("h4", null, "Yeni talimat"),
        form)));
  }

  function ordersTable(list) {
    if (list.length === 0) {
      return h("p", { class: "muted" }, "Talimatınız yok.");
    }
    return h("div", { class: "table-wrap" }, h("table",
      { "aria-labelledby": "orders-title" },
      tableHead([["Ayın günü", true], ["Alıcı"], ["Açıklama"],
        ["Tutar", true]]),
      h("tbody", null, list.map(function (row) {
        row = isObject(row) ? row : {};
        return h("tr", null,
          h("td", { class: "num" }, show(row.day)),
          h("td", null, h("span", { class: "iban" }, party(row.receiver))),
          h("td", null, show(row.description)),
          h("td", { class: "num" }, money(row.amount)));
      }))));
  }

  function orderForm(accounts, flash) {
    const area = messageArea();
    const from = accountChoice("order-from", accounts, flash.orderSender);
    const to = input("order-to", { required: true, autocapitalize: "off" });
    const day = amountInput("order-day", { maxlength: "2" });
    const amount = amountInput("order-amount");
    const description = input("order-description", { maxlength: "40",
      required: true });
    const button = primary("Talimat ekle");
    const form = h("form", { class: "form" },
      field("order-from", "Gönderen hesap", from),
      field("order-to", "Alıcı", to, "IBAN ya da Kolay Adres."),
      h("div", { class: "row-2" },
        field("order-day", "Ayın kaçında", day, "1 ile 28 arası."),
        field("order-amount", "Tutar (TL)", amount)),
      field("order-description", "Açıklama", description),
      h("div", { class: "actions" }, button), area);
    form.addEventListener("submit", async function (event) {
      event.preventDefault();
      const data = await busy(button, function () {
        return post("/api/order_add", { sender: from.value,
          receiver: to.value, day: day.value.trim(),
          amount: amount.value.trim(), description: description.value });
      });
      if (!actionOk(area, data)) {
        return;
      }
      if (data.ok) {
        rerender("gonder", { orderSender: from.value,
          order: { kind: "ok", text: show(data.message) } });
      } else {
        say(area, note("warn", show(data.message)));
      }
    });
    flashNote(area, flash.order);
    return form;
  }

  /* Kartlarım (task 4) */

  async function categoriesOf(answer) {
    const data = await answer;
    return isObject(data) && Array.isArray(data.categories)
      ? data.categories : FALLBACK_CATEGORIES;
  }

  async function renderCards(panel, flash) {
    const number = ticket(panel);
    const head = panelHead("Kartlarım",
      "Kredi kartlarınızın limiti, borcu ve son ekstresi.");
    loading(panel, head);
    const answers = await Promise.all([post("/api/cards"),
      categoriesOf(post("/api/fx"))]);
    const data = answers[0];
    if (stale(panel, number) || !pageOk(panel, [head], data)) {
      return;
    }
    const cards = Array.isArray(data.cards) ? data.cards : [];
    if (cards.length === 0) {
      fill(panel, head, h("p", { class: "card muted" },
        "Adınıza kayıtlı bir kredi kartı yok."));
      return;
    }
    fill(panel, head, h("div", { class: "stack" },
      cards.map(function (card) {
        return cardBlock(isObject(card) ? card : {}, answers[1], flash || {});
      })));
  }

  function cardBlock(card, categories, flash) {
    const id = show(card.card_id);
    const titleId = "card-title-" + id;
    let doubles = [];
    if (sectionOk(card.doubles) && Array.isArray(card.doubles.ok)) {
      doubles = card.doubles.ok;
    }
    return h("article", { class: "card cardbox",
      "aria-labelledby": titleId },
    h("h3", { id: titleId }, "Kredi kartı, son dört hane " + id),
    h("div", { class: "cardbox-grid" },
      h("div", { class: "stack" },
        h("div", { class: "plastic", "aria-hidden": "true" },
          h("span", { class: "plastic-bank" }, bankName()),
          h("span", { class: "plastic-no" }, "•••• " + id)),
        h("dl", { class: "facts" },
          h("dt", null, "Limit"), h("dd", null, money(card.limit)),
          h("dt", null, "Hesap kesim"),
          h("dd", null, "Her ayın " + show(card.cut_day) + ". günü")),
        sectionView(card.state, function (state) {
          return cardState(state, card.limit);
        }),
        h("div", { class: "stack-tight" },
          h("h4", null, "Çift çekim kontrolü"),
          sectionView(card.doubles, doublesView)),
        spendForm(id, categories, flash),
        payForm(id, card, flash)),
      h("div", { class: "stack" },
        h("h4", null, "Son ekstre"),
        sectionView(card.statement, function (bill) {
          return statementView(bill, doubles);
        }))));
  }

  function cardState(state, limit) {
    if (!isObject(state)) {
      throw new Error("not a dict");
    }
    const available = state.available;
    let used = 0;
    if (isNumber(state.debt) && isNumber(limit) && limit > 0) {
      used = state.debt / limit;
    }
    /* The filled part is the debt; the rest of the track is what can
       still be spent. */
    return h("div", { class: "limit" },
      h("div", { class: "limit-row" },
        h("span", null, h("span", { class: "key is-track" }),
          "Kullanılabilir limit"),
        h("strong", { class: "amount" }, money(available))),
      meter(used, "Kart borcu: " + money(state.debt), "",
        "Kullanılabilir limit: " + money(available)),
      h("div", { class: "limit-row" },
        h("span", { class: "muted" }, h("span", { class: "key is-main" }),
          "Kart borcu"),
        h("span", { class: "amount" }, money(state.debt))));
  }

  function doublesView(list) {
    if (!Array.isArray(list)) {
      throw new Error("not a list");
    }
    if (list.length === 0) {
      return h("p", { class: "muted" }, "Bu kartta aynı gün, aynı yerden, " +
        "aynı tutarda iki kez çekilmiş bir harcama yok.");
    }
    return note("warn", [
      h("p", null, h("strong", null, list.length === 1
        ? "Bir harcama iki kez çekilmiş:"
        : list.length + " harcama iki kez çekilmiş:")),
      h("ul", { class: "plain-list" }, list.map(function (row) {
        row = isObject(row) ? row : {};
        return h("li", null, fmtDate(row.date, longFormat) + ", " +
          show(row.merchant) + ", " + money(row.amount));
      })),
      h("p", null, "İkinci çekim büyük olasılıkla bir hata; ekstrenize " +
        "itiraz edebilirsiniz.")]);
  }

  function lineKey(row) {
    return [row.date, row.merchant, row.amount].join("|");
  }

  function statementView(bill, doubles) {
    if (!isObject(bill)) {
      throw new Error("not a dict");
    }
    const lines = Array.isArray(bill.lines) ? bill.lines : [];
    const twice = {};
    doubles.forEach(function (row) {
      if (isObject(row)) {
        twice[lineKey(row)] = true;
      }
    });
    const seen = {};
    const rows = lines.map(function (line) {
      line = isObject(line) ? line : {};
      const key = lineKey(line);
      seen[key] = (seen[key] || 0) + 1;
      const second = twice[key] === true && seen[key] >= 2;
      return h("tr", { class: second ? "is-double" : null },
        h("td", null, fmtDate(line.date, dayFormat)),
        h("td", null, show(line.merchant),
          second ? h("span", { class: "tag tag-warn" }, "Çift çekim")
            : null),
        h("td", { class: "num" }, money(line.amount)));
    });
    return h("div", { class: "statement" },
      h("p", { class: "muted" }, "Dönem: " + fmtDate(bill.start, longFormat) +
        " ile " + fmtDate(bill.end, longFormat) + " arası"),
      h("dl", { class: "stats" },
        stat("Ekstre borcu", money(bill.total)),
        stat("Asgari ödeme", money(bill.minimum)),
        stat("Son ödeme günü", fmtDate(bill.due, longFormat))),
      lines.length === 0
        ? h("p", { class: "muted" }, "Bu dönemde harcama yok.")
        : h("details", { class: "lines", open: true },
          h("summary", null, "Ekstredeki harcamalar (" + lines.length + ")"),
          h("div", { class: "table-wrap" }, h("table", { class: "lines-table" },
            tableHead([["Tarih"], ["İşyeri"], ["Tutar", true]]),
            h("tbody", null, rows)))));
  }

  function spendForm(id, categories, flash) {
    const area = messageArea();
    const prefix = "spend-" + id;
    const merchant = input(prefix + "-merchant", { maxlength: "30",
      required: true });
    const category = categoryChoice(prefix + "-category", categories);
    const amount = amountInput(prefix + "-amount");
    const button = primary("Harca");
    const form = h("form", { class: "form subcard",
      "aria-labelledby": prefix + "-title" },
    h("h4", { id: prefix + "-title" }, "Harcama yap"),
    field(prefix + "-merchant", "İşyeri", merchant),
    h("div", { class: "row-2" },
      field(prefix + "-category", "Kategori", category),
      field(prefix + "-amount", "Tutar (TL)", amount)),
    h("div", { class: "actions" }, button), area);
    form.addEventListener("submit", async function (event) {
      event.preventDefault();
      const data = await busy(button, function () {
        return post("/api/card_spend", { card_id: id,
          merchant: merchant.value, category: category.value,
          amount: amount.value.trim() });
      });
      if (!actionOk(area, data)) {
        return;
      }
      if (data.ok) {
        rerender("kartlar", { card: id, form: "spend",
          note: { kind: "ok", text: show(data.message) } });
      } else {
        say(area, note("warn", show(data.message)));
      }
    });
    if (flash.card === id && flash.form === "spend") {
      flashNote(area, flash.note);
    }
    return form;
  }

  function payForm(id, card, flash) {
    const area = messageArea();
    const prefix = "pay-" + id;
    const amount = amountInput(prefix + "-amount");
    const button = primary("Öde");
    let debt = null;
    let minimum = null;
    if (sectionOk(card.state) && isObject(card.state.ok) &&
        isNumber(card.state.ok.debt)) {
      debt = card.state.ok.debt;
    }
    if (sectionOk(card.statement) && isObject(card.statement.ok) &&
        isNumber(card.statement.ok.minimum)) {
      minimum = card.statement.ok.minimum;
    }
    const quick = h("div", { class: "quick" });
    const fillWith = function (value) {
      return function () {
        amount.value = String(value);
        amount.focus();
      };
    };
    if (minimum !== null && minimum > 0) {
      let value = Math.ceil(minimum);
      if (debt !== null && debt < value) {
        value = Math.round(debt);
      }
      if (value > 0) {
        quick.append(quickButton("Asgari ödeme: " + money(value),
          fillWith(value)));
      }
    }
    if (debt !== null && debt > 0) {
      quick.append(quickButton("Bütün borç: " + money(debt),
        fillWith(Math.round(debt))));
    }
    const form = h("form", { class: "form subcard",
      "aria-labelledby": prefix + "-title" },
    h("h4", { id: prefix + "-title" }, "Borç öde"),
    field(prefix + "-amount", "Tutar (TL)", amount,
      "Ödeme TL hesabınızdan çekilir."),
    quick.firstChild ? quick : null,
    debt === 0 ? h("p", { class: "muted" }, "Bu kartın borcu yok.") : null,
    h("div", { class: "actions" }, button), area);
    form.addEventListener("submit", async function (event) {
      event.preventDefault();
      const data = await busy(button, function () {
        return post("/api/card_pay", { card_id: id,
          amount: amount.value.trim() });
      });
      if (!actionOk(area, data)) {
        return;
      }
      if (data.ok) {
        rerender("kartlar", { card: id, form: "pay",
          note: { kind: "ok", text: show(data.message) } });
      } else {
        say(area, note("warn", show(data.message)));
      }
    });
    if (flash.card === id && flash.form === "pay") {
      flashNote(area, flash.note);
    }
    return form;
  }

  /* Döküm (task 4) */

  async function renderBreakdown(panel) {
    const number = ticket(panel);
    const head = panelHead("Harcama dökümü", "Kartınızın son üç aydaki " +
      "harcamaları, abonelikleriniz ve bütçeleriniz.");
    loading(panel, head);
    const answers = await Promise.all([post("/api/cards"),
      categoriesOf(post("/api/fx"))]);
    const data = answers[0];
    if (stale(panel, number) || !pageOk(panel, [head], data)) {
      return;
    }
    const categories = answers[1];
    const ids = [];
    (Array.isArray(data.cards) ? data.cards : []).forEach(function (card) {
      if (isObject(card) && card.card_id !== undefined) {
        ids.push(show(card.card_id));
      }
    });
    if (ids.length === 0) {
      fill(panel, head, h("p", { class: "card muted" },
        "Adınıza kayıtlı bir kredi kartı yok."));
      return;
    }
    if (ids.indexOf(app.breakdownCard) < 0) {
      app.breakdownCard = ids[0];
    }
    const picker = choice("breakdown-card", ids.map(function (id) {
      return { value: id, label: "Kart, son dört hane " + id };
    }), app.breakdownCard);
    const body = h("div", { class: "stack" });
    picker.addEventListener("change", function () {
      app.breakdownCard = picker.value;
      loadBreakdown(body, categories, null);
    });
    fill(panel, head, h("div", { class: "stack" },
      h("div", { class: "toolbar" }, field("breakdown-card", "Kart", picker)),
      body));
    loadBreakdown(body, categories, null);
  }

  async function loadBreakdown(body, categories, flash) {
    const number = ticket(body);
    if (!body.firstChild) {
      fill(body, h("p", { class: "loading" }, "Yükleniyor"));
    }
    const data = await post("/api/breakdown",
      { card_id: app.breakdownCard });
    if (stale(body, number) || !pageOk(body, [], data)) {
      return;
    }
    fill(body,
      sectionView(data.totals, function (list) {
        return monthsView(list, categories);
      }),
      h("div", { class: "grid" },
        partCard("subs", "Abonelikler", null, "Üç ayın her birinde " +
          "harcama yapılan yerler. Her ay aynı yere yapılan ödeme çoğu " +
          "zaman bir aboneliktir.",
        sectionView(data.subscriptions, function (list) {
          return placesView(list, "Üç ayın hepsinde harcama yapılan bir " +
            "yer yok.");
        })),
        partCard("fresh", "Bu ay ilk kez", null, "Bu ay ilk kez harcama " +
          "yaptığınız yerler: önceki iki ayda bu yerlerde harcamanız yok.",
        sectionView(data.new_places, function (list) {
          return placesView(list, "Bu ay ilk kez harcama yaptığınız bir " +
            "yer yok.");
        }))),
      budgetCard(data, categories, body, flash || {}));
    openFirst(body);
  }

  function monthsView(list, categories) {
    if (!Array.isArray(list)) {
      throw new Error("not a list");
    }
    let largest = 0;
    list.forEach(function (month) {
      const totals = isObject(month) ? month.totals : null;
      if (isObject(totals)) {
        Object.keys(totals).forEach(function (key) {
          if (isNumber(totals[key]) && totals[key] > largest) {
            largest = totals[key];
          }
        });
      }
    });
    return h("div", { class: "stack" },
      h("p", { class: "muted" }, "Renkli çubuklar, o ayın en çok harcanan " +
        "üç kategorisi."),
      h("div", { class: "months" }, list.map(function (month) {
        return monthCard(isObject(month) ? month : {}, categories, largest);
      })));
  }

  function monthCard(month, categories, largest) {
    const totals = isObject(month.totals) ? month.totals : {};
    const top = Array.isArray(month.top) ? month.top : [];
    const topNames = top.map(function (pair) {
      return show(Array.isArray(pair) ? pair[0] : pair);
    });
    const order = [];
    categories.forEach(function (name) {
      if (Object.prototype.hasOwnProperty.call(totals, name)) {
        order.push(name);
      }
    });
    Object.keys(totals).forEach(function (name) {
      if (order.indexOf(name) < 0) {
        order.push(name);
      }
    });
    let sum = 0;
    order.forEach(function (name) {
      if (isNumber(totals[name])) {
        sum += totals[name];
      }
    });
    const titleId = "month-" + show(month.month);
    return h("section", { class: "card month", "aria-labelledby": titleId },
      h("div", { class: "month-head" },
        h("h3", { id: titleId }, monthName(month.month)),
        h("span", null, "Toplam " + money(sum))),
      order.length === 0
        ? h("p", { class: "muted" }, "Bu ay harcama yok.")
        : h("ul", { class: "bars" }, order.map(function (name) {
          const value = totals[name];
          let share = 0;
          if (isNumber(value) && largest > 0 && value > 0) {
            share = value / largest;
          }
          const isTop = topNames.indexOf(name) >= 0;
          return h("li", { class: isTop ? "bar-row is-top" : "bar-row" },
            h("span", { class: "bar-label" }, cap(name)),
            meter(share, cap(name) + ": " + money(value),
              isTop ? "" : "rest"),
            h("span", { class: "bar-value" }, money(value)));
        })),
      h("div", null,
        h("h4", null, "En çok harcanan üç kategori"),
        top.length === 0
          ? h("p", { class: "muted" }, "Liste boş.")
          : h("ol", { class: "top-list" }, top.map(function (pair) {
            const name = Array.isArray(pair) ? pair[0] : pair;
            const value = Array.isArray(pair) ? pair[1] : "";
            return h("li", null, h("span", { class: "top-row" },
              h("span", null, cap(name)),
              h("span", { class: "amount" },
                value === "" ? "" : money(value))));
          }))));
  }

  function placesView(list, empty) {
    if (!Array.isArray(list)) {
      throw new Error("not a list");
    }
    return chips(list.map(show), empty);
  }

  function budgetCard(data, categories, body, flash) {
    const area = messageArea();
    const category = categoryChoice("budget-category", categories);
    const amount = amountInput("budget-amount");
    const button = primary("Bütçeyi kaydet");
    const form = h("form", { class: "form" },
      h("div", { class: "row-2" },
        field("budget-category", "Kategori", category),
        field("budget-amount", "Aylık bütçe (TL)", amount,
          "0 yazarsanız o kategorinin bütçesi kalkar.")),
      h("div", { class: "actions" }, button), area);
    form.addEventListener("submit", async function (event) {
      event.preventDefault();
      const answer = await busy(button, function () {
        return post("/api/budget_set", { category: category.value,
          amount: amount.value.trim() });
      });
      if (!actionOk(area, answer)) {
        return;
      }
      if (answer.ok) {
        loadBreakdown(body, categories, { budget: { kind: "ok",
          text: show(answer.message) } });
      } else {
        say(area, note("warn", show(answer.message)));
      }
    });
    flashNote(area, flash.budget);
    const budgets = isObject(data.budgets) ? data.budgets : {};
    const names = [];
    categories.forEach(function (name) {
      if (Object.prototype.hasOwnProperty.call(budgets, name)) {
        names.push(cap(name) + ": " + money(budgets[name]));
      }
    });
    return partCard("budget", "Bütçe uyarıları", null, "Aylık bütçesinin " +
      "yüzde 80'ine gelen ya da onu aşan kategoriler.",
    sectionView(data.warnings, warningsView),
    h("div", { class: "split" },
      h("div", { class: "stack-tight" }, h("h4", null, "Aylık bütçeleriniz"),
        chips(names, "Henüz bütçe koymadınız.")),
      h("div", { class: "stack-tight" }, h("h4", null, "Bütçe koy"), form)));
  }

  function warningsView(list) {
    if (!Array.isArray(list)) {
      throw new Error("not a list");
    }
    return h("div", { class: "months" }, list.map(function (month) {
      month = isObject(month) ? month : {};
      const items = Array.isArray(month.warnings) ? month.warnings : [];
      const titleId = "warn-" + show(month.month);
      return h("section", { class: "subcard stack-tight",
        "aria-labelledby": titleId },
      h("h4", { id: titleId }, monthName(month.month)),
      items.length === 0
        ? h("p", { class: "muted" }, "Bu ay uyarı yok.")
        : h("ul", { class: "budget-list" }, items.map(budgetRow)));
    }));
  }

  function budgetRow(row) {
    row = isObject(row) ? row : {};
    const percent = isNumber(row.percent) ? row.percent : 0;
    let state = "";
    if (percent > 100) {
      state = ", aşıldı";
    } else if (percent === 100) {
      state = ", doldu";
    }
    return h("li", { class: percent >= 100 ? "budget-row is-over"
      : "budget-row is-near" },
    h("div", { class: "budget-top" },
      h("span", { class: "budget-name" }, cap(row.category)),
      h("strong", null, "%" + num(percent) + state)),
    meter(percent / 100, cap(row.category) + ": %" + num(percent),
      percent >= 100 ? "over" : ""),
    h("span", { class: "budget-detail" }, money(row.spent) +
      " harcandı, bütçe " + money(row.budget)));
  }

  /* Döviz (task 5) */

  async function renderFx(panel, flash) {
    flash = flash || {};
    const number = ticket(panel);
    const head = panelHead("Döviz", "Alış, bankanın dövizi sizden aldığı " +
      "kur; satış, size sattığı kur. Aradaki farka kur makası denir.");
    loading(panel, head);
    const answers = await Promise.all([post("/api/fx"), getAccounts()]);
    const data = answers[0];
    if (stale(panel, number) || !pageOk(panel, [head], data)) {
      return;
    }
    fill(panel, head, h("div", { class: "grid" },
      ratesCard(data, answers[1]), buyForm(flash), sellForm(flash)));
  }

  function ratesCard(data, accounts) {
    const rates = Array.isArray(data.rates) ? data.rates : [];
    const date = rates.length && isObject(rates[0]) ? rates[0].date : null;
    let balances = null;
    if (isObject(accounts) && sectionOk(accounts.accounts) &&
        isObject(accounts.accounts.ok) &&
        Array.isArray(accounts.accounts.ok.accounts) &&
        accounts.accounts.ok.accounts.length) {
      balances = h("dl", { class: "facts" },
        accounts.accounts.ok.accounts.map(function (account) {
          account = isObject(account) ? account : {};
          return [h("dt", null, show(account.currency) + " hesabı"),
            h("dd", null, money(account.balance, show(account.currency)))];
        }));
    }
    return partCard("rates", "Güncel kurlar", null, date
      ? fmtDate(date, longFormat) + " kurları, 1 birim için."
      : "Bugün için kur yok.",
    sectionView(data.texts, rateLines),
    balances ? h("h4", null, "Bakiyeleriniz") : null, balances);
  }

  function rateLines(list) {
    if (!Array.isArray(list)) {
      throw new Error("not a list");
    }
    if (list.length === 0) {
      return h("p", { class: "muted" }, "Bugün için kur yok.");
    }
    return h("ul", { class: "rate-lines" }, list.map(function (line) {
      return h("li", null, show(line));
    }));
  }

  function quoteNote(data, tlAmount) {
    const currency = show(data.currency);
    if (isNumber(data.units) && data.units < 1) {
      return note("warn", money(tlAmount) + " bir " + currency +
        " almaya yetmiyor: 1 " + currency + " " + rate(data.sell) + " TL.");
    }
    return note("info", [h("strong", null, money(tlAmount)), " ile ",
      h("strong", null, num(data.units) + " " + currency),
      " alırsınız ve ", h("strong", null, money(data.cost)),
      " ödersiniz; bunları hemen bozdurursanız ",
      h("strong", null, money(data.back)),
      " geri alırsınız, yani kur makası yüzünden ",
      h("strong", null, money(data.loss)), " kaybedersiniz."]);
  }

  function buyForm(flash) {
    const area = messageArea();
    const quoteArea = messageArea();
    const currency = currencyChoice("buy-currency", flash.currency);
    const amount = amountInput("buy-amount");
    const quoteButton = h("button", { type: "button",
      class: "btn btn-secondary" }, "Hesapla");
    const button = primary("Satın al");
    const form = h("form", { class: "card form",
      "aria-labelledby": "buy-title" },
    h("h3", { id: "buy-title" }, "Döviz al"),
    h("div", { class: "row-2" },
      field("buy-currency", "Döviz", currency),
      field("buy-amount", "Harcanacak TL", amount)),
    quoteArea,
    h("div", { class: "actions" }, quoteButton, button),
    h("p", { class: "hint" }, "Önce Hesapla ile ne alacağınızı görün. " +
      "Para TL hesabınızdan çekilir."),
    area);
    quoteButton.addEventListener("click", async function () {
      if (!form.reportValidity()) {
        return;
      }
      const tlAmount = Number(amount.value.trim());
      const data = await busy(quoteButton, function () {
        return post("/api/fx_quote", { currency: currency.value,
          tl_amount: amount.value.trim() });
      });
      if (!actionOk(quoteArea, data)) {
        return;
      }
      say(quoteArea, quoteNote(data, tlAmount));
    });
    form.addEventListener("submit", async function (event) {
      event.preventDefault();
      const data = await busy(button, function () {
        return post("/api/fx_buy", { currency: currency.value,
          tl_amount: amount.value.trim() });
      });
      if (!actionOk(area, data)) {
        return;
      }
      if (data.ok) {
        rerender("doviz", { form: "buy", currency: currency.value,
          note: { kind: "ok", text: show(data.message) } });
      } else {
        say(area, note("warn", show(data.message)));
      }
    });
    if (flash.form === "buy") {
      flashNote(area, flash.note);
    }
    return form;
  }

  function sellForm(flash) {
    const area = messageArea();
    const currency = currencyChoice("sell-currency", flash.sellCurrency);
    const units = amountInput("sell-units");
    const button = primary("Bozdur");
    const form = h("form", { class: "card form",
      "aria-labelledby": "sell-title" },
    h("h3", { id: "sell-title" }, "Döviz bozdur"),
    h("div", { class: "row-2" },
      field("sell-currency", "Döviz", currency),
      field("sell-units", "Kaç birim", units)),
    h("div", { class: "actions" }, button),
    h("p", { class: "hint" }, "Banka dövizi alış kurundan alır; karşılığı " +
      "TL hesabınıza geçer."),
    area);
    form.addEventListener("submit", async function (event) {
      event.preventDefault();
      const data = await busy(button, function () {
        return post("/api/fx_sell", { currency: currency.value,
          units: units.value.trim() });
      });
      if (!actionOk(area, data)) {
        return;
      }
      if (data.ok) {
        rerender("doviz", { form: "sell", sellCurrency: currency.value,
          note: { kind: "ok", text: show(data.message) } });
      } else {
        say(area, note("warn", show(data.message)));
      }
    });
    if (flash.form === "sell") {
      flashNote(area, flash.note);
    }
    return form;
  }

  /* Kredi ve birikim (task 5; Taksit hesapla task 4). The calculators
     are drawn once and keep their last result when the tab is left;
     Kredilerim and Yaklaşan ödemeler are asked again on every visit. */

  function renderLoans(panel) {
    if (!panel.firstChild) {
      const top = h("div", { class: "grid loan-top" });
      fill(panel,
        panelHead("Kredi ve birikim", "Kredileriniz, yaklaşan " +
          "ödemeleriniz ve kredi, mevduat, birikim, taksit hesapları."),
        top, loanCalculator(),
        h("div", { class: "grid" }, depositCard(), goalCard(),
          installmentsCard()));
    }
    loadLoanTop(panel.querySelector(".loan-top"));
  }

  async function loadLoanTop(top) {
    const number = ticket(top);
    if (!top.firstChild) {
      fill(top, h("p", { class: "loading" }, "Yükleniyor"));
    }
    const data = await post("/api/loans");
    if (stale(top, number) || !pageOk(top, [], data)) {
      return;
    }
    fill(top,
      partCard("my-loans", "Kredilerim", null, null,
        sectionView(data.loans, loansView)),
      partCard("upcoming", "Yaklaşan ödemeler (30 gün)", null, "Bugünden " +
        "başlayarak 30 gün içinde ödenecek kart borçları ve kredi " +
        "taksitleri.",
      sectionView(data.upcoming, upcomingView)));
  }

  function loansView(list) {
    if (!Array.isArray(list)) {
      throw new Error("not a list");
    }
    if (list.length === 0) {
      return h("p", { class: "muted" }, "Adınıza kayıtlı bir kredi yok.");
    }
    return h("div", { class: "stack" }, list.map(function (loan) {
      loan = isObject(loan) ? loan : {};
      let share = 0;
      if (isNumber(loan.paid) && isNumber(loan.months) && loan.months > 0) {
        share = Math.max(0, Math.min(1, loan.paid / loan.months));
      }
      return h("article", { class: "loan" },
        h("div", { class: "month-head" },
          h("h4", null, "Kredi " + show(loan.loan_id)),
          h("span", null, "Çekildiği gün: " +
            fmtDate(loan.start, longFormat))),
        h("dl", { class: "stats" },
          stat("Çekilen", money(loan.principal)),
          stat("Aylık faiz", "%" + num(loan.rate)),
          stat("Aylık taksit", money(loan.payment)),
          stat("Kalan borç", money(loan.remaining))),
        h("div", { class: "limit" },
          h("div", { class: "limit-row" },
            h("span", null, "Ödenen taksit"),
            h("strong", { class: "amount" }, num(loan.paid) + " / " +
              num(loan.months))),
          meter(share, "Ödenen taksit: " + num(loan.paid) + " / " +
            num(loan.months))));
    }));
  }

  function upcomingView(list) {
    if (!Array.isArray(list)) {
      throw new Error("not a list");
    }
    if (list.length === 0) {
      return h("p", { class: "muted" }, "Önümüzdeki 30 günde ödemeniz yok.");
    }
    const today = todayText();
    return h("ul", { class: "moves" }, list.map(function (row) {
      row = isObject(row) ? row : {};
      return h("li", { class: "move" },
        h("div", { class: "move-main" },
          h("span", { class: "move-desc" }, show(row.what)),
          h("span", { class: "move-meta" }, fmtDate(row.date, longFormat),
            show(row.date) === today ? h("span", { class: "tag tag-warn" },
              "Bugün") : null)),
        h("span", { class: "amount" }, money(row.amount)));
    }));
  }

  function loanCalculator() {
    const area = messageArea();
    const result = h("div", { class: "stack", "aria-live": "polite" });
    const principal = amountInput("loan-principal", { value: "12000" });
    const monthly = decimalInput("loan-rate", { value: "2" });
    const months = amountInput("loan-months", { value: "12" });
    const button = primary("Hesapla");
    const form = h("form", { class: "form" },
      h("div", { class: "row-3" },
        field("loan-principal", "Çekilecek tutar (TL)", principal,
          "1.000 ile 10.000.000 TL arası."),
        field("loan-rate", "Aylık faiz (yüzde)", monthly,
          "Ayda yüzde kaç: 2 ya da 2,5 gibi."),
        field("loan-months", "Taksit sayısı (ay)", months,
          "1 ile 120 arası.")),
      h("div", { class: "actions" }, button), area);
    form.addEventListener("submit", async function (event) {
      event.preventDefault();
      const data = await busy(button, function () {
        return post("/api/loan", { principal: principal.value.trim(),
          rate: monthly.value.trim(), months: months.value.trim() });
      });
      if (!actionOk(area, data)) {
        result.replaceChildren();
        return;
      }
      say(area, null);
      fill(result, loanView(data));
    });
    return partCard("loan", "Kredi hesaplayıcı", null, "Eşit taksitli bir " +
      "kredinin aylık taksiti ve ödeme planı.", form, result);
  }

  function loanView(data) {
    const plan = Array.isArray(data.plan) ? data.plan : [];
    const columns = [["Ay", true], ["Tarih"], ["Taksit", true],
      ["Faiz", true], ["Anapara", true], ["Kalan borç", true]];
    return [h("dl", { class: "stats" },
      stat("Aylık taksit", money(data.payment)),
      stat("Toplam geri ödeme", money(data.total)),
      stat("Toplam faiz", money(data.interest))),
    h("h4", { id: "plan-title" }, "Ödeme planı"),
    plan.length === 0 ? null : planChart(plan),
    plan.length === 0 ? h("p", { class: "muted" }, "Ödeme planı boş.")
      : h("div", { class: "table-wrap tall" }, h("table",
        { "aria-labelledby": "plan-title" },
        tableHead(columns),
        h("tbody", null, plan.map(function (row) {
          row = isObject(row) ? row : {};
          return h("tr", null,
            h("td", { class: "num" }, show(row.month)),
            h("td", null, fmtDate(row.date, dayFormat)),
            h("td", { class: "num" }, money(row.payment)),
            h("td", { class: "num" }, money(row.interest)),
            h("td", { class: "num" }, money(row.principal_part)),
            h("td", { class: "num" }, money(row.remaining)));
        }))))];
  }

  /* Each instalment as one column: its principal part at the bottom and
     its interest on top. A long plan labels only some of its months. */
  function planChart(plan) {
    const every = Math.ceil(plan.length / 12);
    return columnChart("TL", [{ label: "Anapara", kind: "main" },
      { label: "Faiz", kind: "second" }],
    plan.map(function (row, i) {
      row = isObject(row) ? row : {};
      const month = show(row.month);
      const shown = every === 1 || i === 0 || (i + 1) % every === 0;
      return { label: shown ? month : "",
        bars: [{ value: row.principal_part, title: month + ". ay, anapara: " +
          money(row.principal_part) },
        { value: row.interest, title: month + ". ay, faiz: " +
          money(row.interest) }] };
    }), true, "Ay");
  }

  /* A small calculator card: a form and a live result area. */
  function calculator(id, title, task, sub, fields, path, values, draw) {
    const area = messageArea();
    const result = h("div", { class: "stack-tight", "aria-live": "polite" });
    const button = primary("Hesapla");
    const form = h("form", { class: "form" }, fields,
      h("div", { class: "actions" }, button), area);
    form.addEventListener("submit", async function (event) {
      event.preventDefault();
      const data = await busy(button, function () {
        return post(path, values());
      });
      if (!actionOk(area, data)) {
        result.replaceChildren();
        return;
      }
      say(area, null);
      fill(result, draw(data));
    });
    return partCard(id, title, task, sub, form, result);
  }

  function depositCard() {
    const principal = amountInput("deposit-principal", { value: "10000" });
    const yearly = decimalInput("deposit-rate", { value: "40" });
    const days = amountInput("deposit-days", { value: "32" });
    return calculator("deposit", "Vadeli mevduat", null, "Faizden yüzde " +
      "15 vergi kesilir; bu bankanın kuralı.",
    [field("deposit-principal", "Yatırılan para (TL)", principal),
      h("div", { class: "row-2" },
        field("deposit-rate", "Yıllık faiz (yüzde)", yearly),
        field("deposit-days", "Vade (gün)", days))],
    "/api/deposit", function () {
      return { principal: principal.value.trim(),
        rate: yearly.value.trim(), days: days.value.trim() };
    }, function (data) {
      return h("dl", { class: "stats" },
        stat("Brüt faiz", money(data.gross)),
        stat("Vergi", money(data.tax)),
        stat("Net faiz", money(data.net)),
        stat("Vade sonunda", money(data.total)));
    });
  }

  function goalCard() {
    const goal = amountInput("goal-amount", { value: "10000" });
    const monthly = amountInput("goal-monthly", { value: "1000" });
    const yearly = decimalInput("goal-rate", { value: "2" });
    return calculator("goal", "Birikim hedefi", null, "Her ay aynı " +
      "parayı biriktirirseniz ve birikiminiz faizle büyürse hedefe kaç " +
      "ayda ulaşırsınız?",
    [field("goal-amount", "Hedef (TL)", goal),
      h("div", { class: "row-2" },
        field("goal-monthly", "Her ay (TL)", monthly),
        field("goal-rate", "Aylık faiz (yüzde)", yearly, "0 da olur."))],
    "/api/goal", function () {
      return { goal: goal.value.trim(), monthly: monthly.value.trim(),
        rate: yearly.value.trim() };
    }, function (data) {
      return note("ok", h("strong", null, "Hedefe " + num(data.months) +
        " ayda ulaşırsınız."));
    });
  }

  function installmentsCard() {
    const amount = amountInput("inst-amount", { value: "1000" });
    const count = amountInput("inst-count", { value: "3", maxlength: "2" });
    return calculator("installments", "Taksit hesapla", 4, "Bir " +
      "alışverişi eşit taksitlere böler; bölünmeyen kalan, ilk " +
      "taksitlere birer lira olarak eklenir.",
    h("div", { class: "row-2" },
      field("inst-amount", "Alışveriş (TL)", amount),
      field("inst-count", "Taksit sayısı", count, "1 ile 36 arası.")),
    "/api/installments", function () {
      return { amount: amount.value.trim(), count: count.value.trim() };
    }, function (data) {
      const parts = Array.isArray(data.parts) ? data.parts : [];
      let total = 0;
      parts.forEach(function (part) {
        if (isNumber(part)) {
          total += part;
        }
      });
      return [h("p", null, num(parts.length) + " taksit, toplam " +
        money(total) + "."),
      h("ul", { class: "chips" }, parts.map(function (part, i) {
        return h("li", { class: "chip" }, (i + 1) + ". taksit: " +
          money(part));
      }))];
    });
  }

  /* ATM (task 5) */

  async function renderAtm(panel, flash) {
    flash = flash || {};
    const number = ticket(panel);
    const head = panelHead("ATM", "Kartsız para çekme ve kart numarası " +
      "kontrolü.");
    loading(panel, head);
    const data = await getAccounts();
    if (stale(panel, number) || !pageOk(panel, [head], data)) {
      return;
    }
    fill(panel, head, h("div", { class: "grid" }, atmCard(data, flash),
      cardNumberCard()));
  }

  /* A QR-like picture for the ATM card; it only decorates. */
  function qrArt() {
    const size = 25;
    const svg = document.createElementNS(SVG_NS, "svg");
    svg.setAttribute("viewBox", "0 0 " + size + " " + size);
    svg.setAttribute("width", "92");
    svg.setAttribute("height", "92");
    svg.setAttribute("aria-hidden", "true");
    svg.setAttribute("focusable", "false");
    svg.setAttribute("class", "qr");
    const inFinder = function (x, y) {
      return (x < 8 && y < 8) || (x > size - 9 && y < 8) ||
        (x < 8 && y > size - 9);
    };
    let d = "";
    [[0, 0], [size - 7, 0], [0, size - 7]].forEach(function (corner) {
      const x = corner[0];
      const y = corner[1];
      d += "M" + x + " " + y + "h7v7h-7zM" + (x + 1) + " " + (y + 1) +
        "v5h5v-5zM" + (x + 2) + " " + (y + 2) + "h3v3h-3z";
    });
    for (let y = 0; y < size; y++) {
      for (let x = 0; x < size; x++) {
        const mixed = ((x + 3) * 73856093 ^ (y + 5) * 19349663) >>> 0;
        if (!inFinder(x, y) && mixed % 7 < 3) {
          d += "M" + x + " " + y + "h1v1h-1z";
        }
      }
    }
    const path = document.createElementNS(SVG_NS, "path");
    path.setAttribute("d", d);
    path.setAttribute("fill", "currentColor");
    path.setAttribute("fill-rule", "evenodd");
    svg.append(path);
    return svg;
  }

  function atmResult(result) {
    const notes = Array.isArray(result.notes) ? result.notes : [];
    return note("ok", [
      h("p", null, h("strong", null, show(result.message))),
      notes.length === 0 ? null : h("p", null, "Banknotlarınız:"),
      notes.length === 0 ? null : h("ul", { class: "banknotes" },
        notes.map(function (row) {
          row = isObject(row) ? row : {};
          return h("li", { class: "banknote" },
            h("span", { class: "banknote-value" }, money(row.note)),
            h("span", null, "× " + num(row.count)));
        }))]);
  }

  function atmCard(data, flash) {
    const area = messageArea();
    const accounts = tlAccounts(data);
    const amount = amountInput("atm-amount", { pattern: SIGNED });
    const button = primary("Para çek", "atm");
    const quick = h("div", { class: "quick" }, [100, 200, 500, 1000].map(
      function (value) {
        return quickButton(money(value), function () {
          amount.value = String(value);
          amount.focus();
        });
      }));
    const form = h("form", { class: "form" },
      field("atm-amount", "Tutar (TL)", amount, "10'un katı olmalı; bir " +
        "hesaptan günde en çok " + money(ATM_LIMIT) + " çekilir."),
      quick, h("div", { class: "actions" }, button), area);
    form.addEventListener("submit", async function (event) {
      event.preventDefault();
      const answer = await busy(button, function () {
        return post("/api/atm", { amount: amount.value.trim() });
      });
      if (!actionOk(area, answer)) {
        return;
      }
      if (answer.ok) {
        rerender("atm", { atm: { message: answer.message,
          notes: answer.notes } });
      } else {
        say(area, note("warn", show(answer.message)));
      }
    });
    if (flash.atm) {
      say(area, atmResult(flash.atm), true);
    }
    let account = null;
    if (accounts === null) {
      account = sectionView(data.accounts, null);
    } else if (accounts.length) {
      account = [h("span", { class: "muted" }, "Çekilecek hesap"),
        h("span", { class: "iban" }, groupIban(accounts[0].iban)),
        h("span", { class: "atm-balance amount" }, "Bakiye " +
          money(accounts[0].balance))];
    }
    return partCard("atm", "QR ile para çek", null, "Gerçekte ATM'nin " +
      "ekranındaki QR kodu bankanızın uygulamasıyla okutursunuz; burada " +
      "tutarı yazıp Para çek'e basmanız yeter.",
    h("div", { class: "atm-top" }, qrArt(),
      h("div", { class: "atm-account" }, account)),
    form,
    h("p", { class: "hint" }, "ATM'de 200, 100, 50, 20 ve 10 TL'lik " +
      "banknot var."));
  }

  function cardNumberCard() {
    const area = messageArea();
    const number = input("card-number", { inputmode: "numeric",
      maxlength: "23", required: true });
    const button = primary("Kontrol et");
    const sample = h("button", { type: "button", class: "btn btn-secondary",
      onclick: function () {
        number.value = TEST_CARD;
        number.focus();
      } }, "Deneme numarasını yaz");
    const form = h("form", { class: "form" },
      field("card-number", "Kart numarası", number, "Kart şirketlerinin " +
        "denemeler için yayımladığı " + TEST_CARD + " geçerlidir; son " +
        "haneyi değiştirip yeniden deneyin."),
      h("div", { class: "actions" }, button, sample), area);
    form.addEventListener("submit", async function (event) {
      event.preventDefault();
      const data = await busy(button, function () {
        return post("/api/card_number", { number: number.value });
      });
      if (!actionOk(area, data)) {
        return;
      }
      say(area, data.valid
        ? note("ok", "Geçerli bir kart numarası: kontrol hanesi tutuyor.")
        : note("warn", "Geçersiz kart numarası: kontrol hanesi tutmuyor " +
          "ya da numara 16 haneli değil."));
    });
    return partCard("card-check", "Kart numarası kontrolü", null, "Kart " +
      "numarasının son hanesi bir kontrol hanesidir; bir rakamı yanlış " +
      "yazılmış numara kontrolden geçmez.", form);
  }

  /* Raporum (task 5) */

  async function renderReport(panel) {
    const number = ticket(panel);
    const head = panelHead("Raporum",
      "bank.py'deki my_report'un hazırladığı tablo.");
    loading(panel, head);
    const data = await post("/api/report");
    if (stale(panel, number) || !pageOk(panel, [head], data)) {
      return;
    }
    fill(panel, head, h("section", { class: "card" },
      sectionView(data.report, reportView)));
  }

  function reportView(report) {
    if (!isObject(report)) {
      throw new Error("not a dict");
    }
    const rows = Array.isArray(report.rows) ? report.rows : [];
    let width = 1;
    rows.forEach(function (row) {
      if (Array.isArray(row) && row.length > width) {
        width = row.length;
      }
    });
    const numeric = /^[-+]?\d[\d.,]*$/;
    return h("div", { class: "stack" },
      h("h3", { id: "report-title" }, show(report.title) || "Raporum"),
      rows.length === 0
        ? h("p", { class: "muted" }, "Raporunuzda henüz satır yok.")
        : h("div", { class: "table-wrap" }, h("table", { class: "report",
          "aria-labelledby": "report-title" },
          h("tbody", null, rows.map(function (row) {
            const cells = Array.isArray(row) ? row : [row];
            const tds = [];
            for (let i = 0; i < width; i++) {
              const text = i < cells.length ? show(cells[i]) : "";
              tds.push(h("td", { class: numeric.test(text) ? "num" : null },
                text));
            }
            return h("tr", null, tds);
          })))));
  }

  /* Ayarlar (task 2) */

  function renderSettings(panel) {
    fill(panel, panelHead("Ayarlar", "Şifrenizi buradan değiştirirsiniz."),
      h("div", { class: "narrow" }, passwordCard()));
  }

  function passwordCard() {
    const area = messageArea();
    const old = input("password-old", { type: "password",
      autocomplete: "current-password", required: true });
    const fresh = input("password-new", { type: "password",
      autocomplete: "new-password", required: true });
    const again = input("password-again", { type: "password",
      autocomplete: "new-password", required: true });
    const button = primary("Şifremi değiştir");
    const customer = app.state && isObject(app.state.customer)
      ? show(app.state.customer.no) : "";
    const form = h("form", { class: "form" },
      h("input", { type: "text", name: "username", value: customer,
        autocomplete: "username", hidden: true, tabindex: "-1",
        "aria-hidden": "true" }),
      field("password-old", "Şu anki şifreniz", old),
      field("password-new", "Yeni şifre", fresh, PASSWORD_RULES),
      field("password-again", "Yeni şifre, bir kez daha", again),
      h("div", { class: "actions" }, button), area);
    form.addEventListener("submit", async function (event) {
      event.preventDefault();
      if (fresh.value !== again.value) {
        say(area, note("warn", "Yeni şifre iki kutuda aynı olmalı."));
        again.focus();
        return;
      }
      const data = await busy(button, function () {
        return post("/api/password", { old: old.value, new: fresh.value });
      });
      if (!actionOk(area, data)) {
        return;
      }
      if (data.ok) {
        old.value = "";
        fresh.value = "";
        again.value = "";
        say(area, note("ok", show(data.message) || "Şifreniz değişti."));
      } else {
        say(area, note("warn", show(data.message)));
      }
    });
    return partCard("password", "Şifre değiştir", null, "Banka şifrenizi " +
      "saklamaz; yalnız hash'ini (özetini) saklar.", form);
  }

  /* Start */

  document.getElementById("logout").addEventListener("click", logout);
  document.getElementById("reset").addEventListener("click", resetData);
  document.getElementById("banner-reload").addEventListener("click",
    function () { window.location.reload(); });
  window.addEventListener("unhandledrejection", function () {
    showBanner([h("p", null, "Ekranda beklenmeyen bir sorun çıktı; " +
      "sayfayı yenileyin.")]);
  });

  loadToken();
  const saved = lastBrand();
  applyBrand(saved.name, saved.color);
  boot();
}());
