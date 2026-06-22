"""
SecuPulse - Dashboard temps réel (Flask)
==========================================
Sert une page web qui réaffiche la posture de sécurité et la rafraîchit
automatiquement. Historise le score à chaque scan pour tracer une courbe
d'évolution dans le temps.

Lancement :
    pip install flask
    python3 dashboard.py
    -> http://127.0.0.1:5000

Auteur : Omar Benmansour
"""

from __future__ import annotations
import json
import os
from datetime import datetime
from flask import Flask, jsonify, render_template_string

from collectors import collect_all
from report import calcul_score, niveau_global, COULEURS_SEV
from collections import defaultdict

app = Flask(__name__)
HISTORIQUE = "historique_scores.json"


def enregistrer_score(score: int) -> list[dict]:
    """Ajoute le score courant à l'historique et le retourne."""
    histo = []
    if os.path.exists(HISTORIQUE):
        try:
            with open(HISTORIQUE, encoding="utf-8") as f:
                histo = json.load(f)
        except (json.JSONDecodeError, OSError):
            histo = []
    histo.append({"date": datetime.now().strftime("%d/%m %H:%M"), "score": score})
    histo = histo[-20:]  # on garde les 20 derniers points
    with open(HISTORIQUE, "w", encoding="utf-8") as f:
        json.dump(histo, f, ensure_ascii=False, indent=2)
    return histo


@app.route("/api/posture")
def api_posture():
    """Renvoie les données de posture au format JSON (consommé par le front)."""
    findings = collect_all("demo")          # passer "reel" en production
    score = calcul_score(findings)
    histo = enregistrer_score(score)

    par_sev = defaultdict(int)
    for f in findings:
        par_sev[f.severite] += 1

    data = {
        "score": score,
        "niveau": niveau_global(score)[0],
        "couleur": niveau_global(score)[1],
        "date": datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
        "total": len(findings),
        "severites": {s: par_sev.get(s, 0) for s in ["CRITIQUE", "ELEVE", "MOYEN", "FAIBLE", "INFO"]},
        "historique": histo,
        "findings": [
            {"categorie": f.categorie, "titre": f.titre, "severite": f.severite,
             "couleur": COULEURS_SEV[f.severite], "objets": len(f.objets),
             "reco": f.recommandation}
            for f in sorted(findings, key=lambda x: ["CRITIQUE","ELEVE","MOYEN","FAIBLE","INFO"].index(x.severite))
        ],
    }
    return jsonify(data)


PAGE = """<!DOCTYPE html>
<html lang="fr"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>SecuPulse — Dashboard temps réel</title>
<style>
  *{margin:0;padding:0;box-sizing:border-box}
  body{font-family:-apple-system,'Segoe UI',Roboto,sans-serif;background:#0f172a;color:#e2e8f0}
  .wrap{max-width:1100px;margin:0 auto;padding:28px 22px}
  header{display:flex;justify-content:space-between;align-items:center;margin-bottom:24px;flex-wrap:wrap;gap:12px}
  .logo{font-size:1.5rem;font-weight:800}.logo span{color:#14b8a6}
  .live{display:flex;align-items:center;gap:8px;font-size:.85rem;color:#94a3b8}
  .dot{width:9px;height:9px;border-radius:50%;background:#14b8a6;animation:pulse 1.6s infinite}
  @keyframes pulse{0%{opacity:1}50%{opacity:.3}100%{opacity:1}}
  .top{display:grid;grid-template-columns:280px 1fr;gap:18px;margin-bottom:18px}
  .card{background:#1e293b;border-radius:14px;padding:22px}
  .score-num{font-size:4rem;font-weight:800;text-align:center;line-height:1}
  .score-lbl{text-align:center;font-weight:700;margin-top:6px;letter-spacing:.5px}
  .score-sub{text-align:center;color:#64748b;font-size:.8rem;margin-top:8px}
  .sev-grid{display:grid;grid-template-columns:repeat(5,1fr);gap:10px;height:100%}
  .sev{background:#0f172a;border-radius:10px;padding:14px 8px;text-align:center;display:flex;flex-direction:column;justify-content:center}
  .sev-num{font-size:1.8rem;font-weight:800}.sev-lbl{font-size:.65rem;color:#94a3b8;font-weight:600;margin-top:4px}
  h2{font-size:1rem;margin-bottom:14px;color:#cbd5e1}
  .chart{display:flex;align-items:flex-end;gap:6px;height:120px;padding-top:10px}
  .bar{flex:1;background:linear-gradient(180deg,#14b8a6,#0d9488);border-radius:4px 4px 0 0;min-height:4px;position:relative}
  .bar span{position:absolute;top:-18px;left:50%;transform:translateX(-50%);font-size:.65rem;color:#94a3b8}
  .finding{background:#0f172a;border-radius:10px;padding:12px 14px;margin-bottom:8px;display:flex;align-items:center;gap:12px}
  .badge{font-size:.62rem;font-weight:700;padding:3px 9px;border-radius:6px;color:#fff;white-space:nowrap}
  .f-title{font-weight:600;font-size:.9rem}.f-reco{font-size:.78rem;color:#94a3b8;margin-top:2px}
  .f-cat{font-size:.7rem;color:#64748b}
</style></head>
<body><div class="wrap">
  <header>
    <div class="logo">Secu<span>Pulse</span> · Dashboard</div>
    <div class="live"><span class="dot"></span> Temps réel — actualisé toutes les 10 s · <span id="date"></span></div>
  </header>
  <div class="top">
    <div class="card">
      <div class="score-num" id="score">--</div>
      <div class="score-lbl" id="niveau">—</div>
      <div class="score-sub" id="total"></div>
    </div>
    <div class="card"><div class="sev-grid" id="sevs"></div></div>
  </div>
  <div class="card" style="margin-bottom:18px">
    <h2>Évolution du score</h2>
    <div class="chart" id="chart"></div>
  </div>
  <div class="card">
    <h2>Constats prioritaires</h2>
    <div id="findings"></div>
  </div>
</div>
<script>
async function refresh(){
  try{
    const r = await fetch('/api/posture'); const d = await r.json();
    document.getElementById('score').textContent = d.score;
    document.getElementById('score').style.color = d.couleur;
    const n = document.getElementById('niveau'); n.textContent = d.niveau; n.style.color = d.couleur;
    document.getElementById('total').textContent = d.total + ' constats analysés';
    document.getElementById('date').textContent = d.date;
    const cols={CRITIQUE:'#dc2626',ELEVE:'#ea580c',MOYEN:'#ca8a04',FAIBLE:'#0891b2',INFO:'#64748b'};
    document.getElementById('sevs').innerHTML = Object.entries(d.severites).map(([k,v])=>
      `<div class="sev"><div class="sev-num" style="color:${cols[k]}">${v}</div><div class="sev-lbl">${k}</div></div>`).join('');
    const max=Math.max(100,...d.historique.map(h=>h.score));
    document.getElementById('chart').innerHTML = d.historique.map(h=>
      `<div class="bar" style="height:${(h.score/max*100)}%"><span>${h.score}</span></div>`).join('');
    document.getElementById('findings').innerHTML = d.findings.slice(0,6).map(f=>
      `<div class="finding"><span class="badge" style="background:${f.couleur}">${f.severite}</span>
       <div><div class="f-title">${f.titre} <span class="f-cat">· ${f.categorie}</span></div>
       <div class="f-reco">${f.reco}</div></div></div>`).join('');
  }catch(e){console.error(e);}
}
refresh(); setInterval(refresh, 10000);
</script>
</body></html>"""


@app.route("/")
def index():
    return render_template_string(PAGE)


if __name__ == "__main__":
    print("SecuPulse Dashboard -> http://127.0.0.1:5000")
    app.run(debug=False, port=5000)
