"""Export the in-memory graph as a standalone interactive HTML network view (vis-network)."""
from __future__ import annotations

import json
from pathlib import Path

from .model import Graph
from .schema import LABELS, RELATIONSHIPS

STYLE = {
    "Module": ("#7c3aed", 34), "BusinessProcess": ("#db2777", 26), "BusinessConcept": ("#ea580c", 18),
    "BusinessRule": ("#ca8a04", 14), "Form": ("#2563eb", 24), "UserControl": ("#0891b2", 20),
    "FormMethod": ("#16a34a", 9), "Control": ("#84cc16", 7), "DTClass": ("#0d9488", 14), "DTMethod": ("#14b8a6", 8),
    "DTProperty": ("#5eead4", 6), "DAClass": ("#047857", 14), "DAMethod": ("#10b981", 8),
    "StoredProcedure": ("#dc2626", 13),
    "Table": ("#475569", 13), "Column": ("#94a3b8", 5),
}
DEFAULT_HIDDEN_LABELS = ["Column", "DTProperty", "Control"]
DEFAULT_HIDDEN_RELS = ["USES_COLUMN", "REFERENCES", "SETS", "PASSES"]
SKIP_PROPS = {"text", "embedding", "embedding_hash", "kind"}


def export_html(g: Graph, path: Path, title: str = "SpectrumERP Knowledge Graph") -> Path:
    nodes = []
    for n in g.nodes.values():
        props = {k: v for k, v in n.props.items() if k not in SKIP_PROPS}
        if isinstance(props.get("code"), str) and len(props["code"]) > 6000:
            props["code"] = props["code"][:6000] + "\n… (truncated)"
        nodes.append({"id": n.id, "label": n.label, "name": n.props.get("title") or n.props.get("name", n.id),
                      "planned": n.props.get("status") == "planned", "props": props})
    edges = [{"from": e.src, "to": e.dst, "type": e.type,
              "props": {k: v for k, v in e.props.items()}} for e in g.edges.values()]
    data = {
        "title": title, "nodes": nodes, "edges": edges, "style": STYLE,
        "layers": {k: v["layer"] for k, v in LABELS.items()},
        "labelMeans": {k: v["means"] for k, v in LABELS.items()},
        "relMeans": {k: v["means"] for k, v in RELATIONSHIPS.items()},
        "derived": [k for k, v in RELATIONSHIPS.items() if v.get("derived")],
        "hiddenLabels": DEFAULT_HIDDEN_LABELS, "hiddenRels": DEFAULT_HIDDEN_RELS,
    }
    payload = json.dumps(data, default=str).replace("</", "<\\/")
    path.write_text(TEMPLATE.replace("__TITLE__", title).replace("__DATA__", payload), encoding="utf-8")
    return path


TEMPLATE = r"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>__TITLE__</title>
<script src="https://cdnjs.cloudflare.com/ajax/libs/vis-network/9.1.9/standalone/umd/vis-network.min.js"></script>
<style>
  :root { --bg:#f8fafc; --panel:#ffffff; --fg:#0f172a; --muted:#64748b; --line:#e2e8f0; --accent:#2563eb; --code:#f1f5f9; }
  @media (prefers-color-scheme: dark) { :root { --bg:#0b1220; --panel:#111827; --fg:#e5e7eb; --muted:#94a3b8; --line:#1f2937; --accent:#60a5fa; --code:#0f172a; } }
  * { box-sizing:border-box; }
  body { margin:0; font:13px/1.45 system-ui,-apple-system,Segoe UI,Roboto,sans-serif; background:var(--bg); color:var(--fg); height:100vh; display:flex; flex-direction:column; }
  header { display:flex; gap:12px; align-items:center; padding:8px 14px; border-bottom:1px solid var(--line); background:var(--panel); flex-wrap:wrap; }
  header h1 { font-size:15px; margin:0 8px 0 0; }
  header input[type=search] { padding:5px 8px; border:1px solid var(--line); border-radius:6px; background:var(--bg); color:var(--fg); width:280px; }
  header button { padding:5px 10px; border:1px solid var(--line); border-radius:6px; background:var(--bg); color:var(--fg); cursor:pointer; }
  header button:hover { border-color:var(--accent); }
  .stat { color:var(--muted); }
  main { flex:1; display:flex; min-height:0; }
  #side { width:250px; overflow:auto; border-right:1px solid var(--line); background:var(--panel); padding:10px 12px; }
  #side h3 { font-size:11px; text-transform:uppercase; letter-spacing:.05em; color:var(--muted); margin:14px 0 6px; }
  #side label { display:flex; align-items:center; gap:6px; padding:2px 0; cursor:pointer; white-space:nowrap; }
  .dot { width:10px; height:10px; border-radius:50%; flex:none; }
  .cnt { margin-left:auto; color:var(--muted); font-size:11px; }
  #net { flex:1; min-width:0; }
  #detail { width:420px; overflow:auto; border-left:1px solid var(--line); background:var(--panel); padding:12px 14px; }
  #detail h2 { font-size:15px; margin:0 0 2px; word-break:break-word; }
  .pill { display:inline-block; padding:1px 8px; border-radius:10px; color:#fff; font-size:11px; margin-right:4px; }
  .muted { color:var(--muted); }
  table.props { border-collapse:collapse; width:100%; margin-top:8px; }
  table.props td { border-top:1px solid var(--line); padding:3px 4px; vertical-align:top; word-break:break-word; }
  table.props td:first-child { color:var(--muted); width:110px; }
  pre { background:var(--code); padding:8px; border-radius:6px; overflow:auto; max-height:420px; font-size:11.5px; white-space:pre; }
  .doc { white-space:pre-wrap; }
  .nb a { color:var(--accent); cursor:pointer; text-decoration:none; }
  .nb a:hover { text-decoration:underline; }
  .nb li { margin:1px 0; }
  .nb ul { margin:2px 0 8px; padding-left:18px; }
  .hint { color:var(--muted); font-size:12px; }
  @media (max-width: 900px) { #side, #detail { display:none; } }
</style>
</head>
<body>
<header>
  <h1>__TITLE__</h1>
  <input id="q" type="search" list="names" placeholder="Search nodes (name or id)…">
  <datalist id="names"></datalist>
  <button id="fit">Fit</button>
  <button id="all">Show all</button>
  <button id="reset">Default view</button>
  <label class="stat"><input type="checkbox" id="phys" checked> physics</label>
  <span class="stat" id="stat"></span>
</header>
<main>
  <aside id="side"></aside>
  <div id="net"></div>
  <aside id="detail"><p class="hint">Click a node to see its documentation, code and neighbours.<br><br>
    Double-click a node to focus on its neighbourhood (depth set below). Use the toggles on the left to show
    layers and relationship types; dense types (columns, parameters, controls) start hidden.</p>
    <p class="hint">Focus depth: <select id="depth"><option>1</option><option selected>2</option><option>3</option></select></p></aside>
</main>
<script>
const D = __DATA__;
const byId = new Map(D.nodes.map(n => [n.id, n]));
const labels = [...new Set(D.nodes.map(n => n.label))];
const layerOrder = ["functional", "bridge", "code", "data"];
labels.sort((a, b) => layerOrder.indexOf(D.layers[a]) - layerOrder.indexOf(D.layers[b]) || a.localeCompare(b));
const rels = [...new Set(D.edges.map(e => e.type))].sort();
const shownLabels = new Set(labels.filter(l => !D.hiddenLabels.includes(l)));
const shownRels = new Set(rels.filter(r => !D.hiddenRels.includes(r)));
let focusSet = null;

const nodesDS = new vis.DataSet(D.nodes.map(n => {
  const [color, size] = D.style[n.label] || ["#999", 8];
  return { id: n.id, label: ["Module","BusinessProcess","Form","UserControl","BusinessConcept"].includes(n.label) ? n.name : undefined,
           title: `${n.label}: ${n.name}`, size, shape: "dot",
           color: { background: color, border: n.planned ? "#94a3b8" : color, highlight: { background: color, border: "#111" } },
           opacity: n.planned ? 0.45 : 1, shapeProperties: { borderDashes: n.planned ? [4, 3] : false },
           borderWidth: n.planned ? 2 : 1, font: { size: 12, color: getComputedStyle(document.body).color } };
}));
const edgesDS = new vis.DataSet(D.edges.map((e, i) => ({
  id: i, from: e.from, to: e.to, type: e.type, title: e.type, arrows: { to: { enabled: true, scaleFactor: .4 } },
  dashes: D.derived.includes(e.type), color: { color: "rgba(100,116,139,.35)", highlight: "#2563eb" }, width: .6 })));

const nodesView = new vis.DataView(nodesDS, { filter: n => shownLabels.has(byId.get(n.id).label) && (!focusSet || focusSet.has(n.id)) });
const edgesView = new vis.DataView(edgesDS, { filter: e => shownRels.has(e.type) });
const net = new vis.Network(document.getElementById("net"), { nodes: nodesView, edges: edgesView }, {
  physics: { solver: "forceAtlas2Based", forceAtlas2Based: { gravitationalConstant: -45, springLength: 90, avoidOverlap: .3 },
             stabilization: { iterations: 250 } },
  interaction: { hover: true, tooltipDelay: 120, hideEdgesOnDrag: true },
  layout: { improvedLayout: false } });
net.once("stabilizationIterationsDone", () => { net.setOptions({ physics: { enabled: false } }); document.getElementById("phys").checked = false; });

function refresh() { nodesView.refresh(); edgesView.refresh(); stat(); }
function stat() { document.getElementById("stat").textContent = `${nodesView.length} / ${D.nodes.length} nodes · ${edgesView.getIds().length} edges shown` + (focusSet ? " · focus mode" : ""); }

// ---- sidebar toggles ----
const side = document.getElementById("side");
const labelCounts = {}; D.nodes.forEach(n => labelCounts[n.label] = (labelCounts[n.label] || 0) + 1);
const relCounts = {}; D.edges.forEach(e => relCounts[e.type] = (relCounts[e.type] || 0) + 1);
let html = "";
let lastLayer = null;
for (const l of labels) {
  if (D.layers[l] !== lastLayer) { lastLayer = D.layers[l]; html += `<h3>${lastLayer} layer</h3>`; }
  html += `<label title="${(D.labelMeans[l] || "").replace(/"/g, "&quot;")}"><input type="checkbox" data-l="${l}" ${shownLabels.has(l) ? "checked" : ""}>
    <span class="dot" style="background:${(D.style[l] || ["#999"])[0]}"></span>${l}<span class="cnt">${labelCounts[l]}</span></label>`;
}
html += `<h3>relationships <span class="muted">(dashed = derived)</span></h3>`;
for (const r of rels) html += `<label title="${(D.relMeans[r] || "").replace(/"/g, "&quot;")}"><input type="checkbox" data-r="${r}" ${shownRels.has(r) ? "checked" : ""}>${r}<span class="cnt">${relCounts[r]}</span></label>`;
side.innerHTML = html;
side.addEventListener("change", ev => {
  const t = ev.target;
  if (t.dataset.l) t.checked ? shownLabels.add(t.dataset.l) : shownLabels.delete(t.dataset.l);
  if (t.dataset.r) t.checked ? shownRels.add(t.dataset.r) : shownRels.delete(t.dataset.r);
  refresh();
});
function syncChecks() { side.querySelectorAll("input").forEach(i => i.checked = i.dataset.l ? shownLabels.has(i.dataset.l) : shownRels.has(i.dataset.r)); }

// ---- details ----
const esc = s => String(s).replace(/[&<>]/g, c => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;" }[c]));
function showDetail(id) {
  const n = byId.get(id); if (!n) return;
  const color = (D.style[n.label] || ["#999"])[0];
  const p = n.props;
  let h = `<span class="pill" style="background:${color}">${n.label}</span>${n.planned ? '<span class="pill" style="background:#94a3b8">planned</span>' : ""}
    <h2>${esc(n.name)}</h2><div class="muted">${esc(n.id)}</div>`;
  if (p.summary) h += `<p>${esc(p.summary)}</p>`;
  if (p.doc) h += `<div class="doc">${esc(p.doc)}</div>`;
  const rows = Object.entries(p).filter(([k]) => !["summary", "doc", "code", "name", "title"].includes(k));
  if (rows.length) h += `<table class="props">${rows.map(([k, v]) => `<tr><td>${esc(k)}</td><td>${esc(Array.isArray(v) ? v.join(", ") : v)}</td></tr>`).join("")}</table>`;
  const groups = {};
  D.edges.forEach(e => {
    if (e.from === id) (groups[`${e.type} →`] ||= []).push([e.to, e.props]);
    if (e.to === id) (groups[`← ${e.type}`] ||= []).push([e.from, e.props]);
  });
  h += `<h3 style="margin-top:14px">Neighbours</h3><div class="nb">`;
  for (const [k, list] of Object.entries(groups).sort()) {
    h += `<b>${esc(k)}</b> <span class="muted">(${list.length})</span><ul>` + list.slice(0, 60).map(([oid, ep]) => {
      const o = byId.get(oid); const extra = Object.entries(ep || {}).filter(([kk]) => !["derived", "lines", "line"].includes(kk))
        .map(([kk, vv]) => `${kk}=${Array.isArray(vv) ? vv.join("/") : vv}`).join(", ");
      return `<li><a data-id="${esc(oid)}">${esc(o ? o.name : oid)}</a> <span class="muted">${o ? o.label : ""}${extra ? " · " + esc(extra).slice(0, 120) : ""}</span></li>`;
    }).join("") + (list.length > 60 ? `<li class="muted">… ${list.length - 60} more</li>` : "") + `</ul>`;
  }
  h += `</div>`;
  if (p.code) h += `<h3>Code</h3><pre>${esc(p.code)}</pre>`;
  const det = document.getElementById("detail");
  det.innerHTML = h; det.scrollTop = 0;
}
document.getElementById("detail").addEventListener("click", ev => { const id = ev.target.dataset && ev.target.dataset.id; if (id) goTo(id); });

function goTo(id) {
  const n = byId.get(id); if (!n) return;
  if (!shownLabels.has(n.label)) { shownLabels.add(n.label); syncChecks(); }
  if (focusSet && !focusSet.has(id)) focusSet = null;
  refresh();
  showDetail(id);
  setTimeout(() => { net.selectNodes([id]); net.focus(id, { scale: 1.2, animation: { duration: 400 } }); }, 50);
}
function focusOn(id, depth) {
  const adj = new Map();
  D.edges.forEach(e => { if (!shownRels.has(e.type)) return;
    (adj.get(e.from) || adj.set(e.from, []).get(e.from)).push(e.to);
    (adj.get(e.to) || adj.set(e.to, []).get(e.to)).push(e.from); });
  focusSet = new Set([id]); let frontier = [id];
  for (let d = 0; d < depth; d++) { const next = []; frontier.forEach(x => (adj.get(x) || []).forEach(y => { if (!focusSet.has(y)) { focusSet.add(y); next.push(y); } })); frontier = next; }
  focusSet.forEach(x => shownLabels.add(byId.get(x).label)); syncChecks();
  refresh(); net.setOptions({ physics: { enabled: true } }); document.getElementById("phys").checked = true;
  setTimeout(() => net.fit({ animation: true }), 600);
}
net.on("click", p => { if (p.nodes.length) showDetail(p.nodes[0]); });
net.on("doubleClick", p => { if (p.nodes.length) focusOn(p.nodes[0], +document.getElementById("depth").value); });

// ---- header ----
document.getElementById("names").innerHTML = D.nodes.map(n => `<option value="${esc(n.id)}">${esc(n.name)} (${n.label})</option>`).join("");
document.getElementById("q").addEventListener("change", ev => {
  const v = ev.target.value.trim().toLowerCase(); if (!v) return;
  const hit = byId.get(ev.target.value) || D.nodes.find(n => n.id.toLowerCase() === v || n.name.toLowerCase() === v)
           || D.nodes.find(n => n.name.toLowerCase().includes(v) || n.id.toLowerCase().includes(v));
  if (hit) goTo(hit.id);
});
document.getElementById("fit").onclick = () => net.fit({ animation: true });
document.getElementById("all").onclick = () => { focusSet = null; labels.forEach(l => shownLabels.add(l)); rels.forEach(r => shownRels.add(r)); syncChecks(); refresh(); };
document.getElementById("reset").onclick = () => { focusSet = null; shownLabels.clear(); labels.filter(l => !D.hiddenLabels.includes(l)).forEach(l => shownLabels.add(l));
  shownRels.clear(); rels.filter(r => !D.hiddenRels.includes(r)).forEach(r => shownRels.add(r)); syncChecks(); refresh(); net.fit({ animation: true }); };
document.getElementById("phys").onchange = ev => net.setOptions({ physics: { enabled: ev.target.checked } });
stat();
</script>
</body>
</html>
"""
