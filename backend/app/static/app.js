const fmtNum = (n, digits = 2) => {
  if (n === null || n === undefined || Number.isNaN(n)) return "—";
  const abs = Math.abs(n);
  if (abs >= 1e9) return (n / 1e9).toFixed(digits) + "B";
  if (abs >= 1e6) return (n / 1e6).toFixed(digits) + "M";
  if (abs >= 1e3) return (n / 1e3).toFixed(digits) + "K";
  return Number(n).toFixed(digits);
};

const fmtPrice = (n) => {
  if (n === null || n === undefined || Number.isNaN(n)) return "—";
  const x = Number(n);
  const digits = x >= 1000 ? 2 : x >= 1 ? 4 : 6;
  return x.toFixed(digits);
};

const fmtPct = (n) => {
  if (n === null || n === undefined || Number.isNaN(n)) return "—";
  const x = Number(n);
  const sign = x > 0 ? "+" : "";
  return sign + x.toFixed(2) + "%";
};

const cellClassForPct = (n) => {
  if (n === null || n === undefined || Number.isNaN(n)) return "cellNeu";
  if (n > 0) return "cellPos";
  if (n < 0) return "cellNeg";
  return "cellNeu";
};

async function fetchJson(url) {
  const resp = await fetch(url, { headers: { "Accept": "application/json" } });
  if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
  return await resp.json();
}

function renderCard(exchange, data) {
  const tpl = document.getElementById("exchangeCardTemplate");
  const node = tpl.content.firstElementChild.cloneNode(true);
  node.querySelector(".exchangeName").textContent = exchange.toUpperCase();
  node.querySelector(".meta").textContent = `контрактов: ${data.items.length}`;

  const tbody = node.querySelector("tbody");
  tbody.textContent = "";

  for (const it of data.items) {
    const tr = document.createElement("tr");

    const tdSym = document.createElement("td");
    tdSym.className = "colSymbol mono";
    tdSym.textContent = it.symbol;

    const tdPrice = document.createElement("td");
    tdPrice.className = "mono";
    tdPrice.textContent = fmtPrice(it.price);

    const tdOi = document.createElement("td");
    tdOi.className = "mono";
    tdOi.textContent = fmtNum(it.oi, 2);

    const td5 = document.createElement("td");
    td5.className = `mono ${cellClassForPct(it.chg_5m)}`;
    td5.textContent = fmtPct(it.chg_5m);

    const td1 = document.createElement("td");
    td1.className = `mono ${cellClassForPct(it.chg_1h)}`;
    td1.textContent = fmtPct(it.chg_1h);

    const td24 = document.createElement("td");
    td24.className = `mono ${cellClassForPct(it.chg_24h)}`;
    td24.textContent = fmtPct(it.chg_24h);

    tr.appendChild(tdSym);
    tr.appendChild(tdPrice);
    tr.appendChild(tdOi);
    tr.appendChild(td5);
    tr.appendChild(td1);
    tr.appendChild(td24);
    tbody.appendChild(tr);
  }

  return node;
}

async function refreshAll() {
  const grid = document.getElementById("grid");
  const status = document.getElementById("status");
  const sortBy = document.getElementById("sortBy").value;
  const order = document.getElementById("order").value;
  const limit = Number(document.getElementById("limit").value || 50);

  status.textContent = "обновляю…";
  const t0 = Date.now();
  try {
    const ex = await fetchJson("/api/exchanges");
    const exchanges = ex.exchanges || [];

    const results = await Promise.allSettled(
      exchanges.map((e) => fetchJson(`/api/oi?exchange=${encodeURIComponent(e)}&sort_by=${encodeURIComponent(sortBy)}&order=${encodeURIComponent(order)}&limit=${encodeURIComponent(limit)}`))
    );

    grid.textContent = "";
    for (let i = 0; i < exchanges.length; i++) {
      const e = exchanges[i];
      const r = results[i];
      if (r.status === "fulfilled") {
        grid.appendChild(renderCard(e, r.value));
      } else {
        const err = document.createElement("div");
        err.className = "card";
        err.style.padding = "12px";
        err.textContent = `${e.toUpperCase()}: ошибка загрузки данных`;
        grid.appendChild(err);
      }
    }

    const ms = Date.now() - t0;
    status.textContent = `готово (${ms}ms)`;
  } catch (e) {
    status.textContent = `ошибка: ${e?.message || e}`;
  }
}

document.getElementById("refresh").addEventListener("click", refreshAll);
document.getElementById("sortBy").addEventListener("change", refreshAll);
document.getElementById("order").addEventListener("change", refreshAll);
document.getElementById("limit").addEventListener("change", refreshAll);

// auto-refresh every 30s
setInterval(() => refreshAll().catch(() => {}), 30000);
refreshAll().catch(() => {});

