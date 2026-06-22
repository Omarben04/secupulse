"""
SecuPulse - Moteur de scoring & rapport HTML
=============================================
Calcule un score de posture (0-100) à partir des findings,
puis génère un rapport HTML autonome (un seul fichier, aucune dépendance).

Auteur : Omar Benmansour
"""

from __future__ import annotations
from datetime import datetime
from collections import defaultdict
from collectors import collect_all, Finding, SEVERITES


def calcul_score(findings: list[Finding]) -> int:
    """Score 100 = parfait. On retire des points selon la sévérité des findings.

    Le malus par finding est plafonné pour éviter qu'un seul constat
    multi-objets fasse chuter tout le score. Le nombre d'objets n'ajoute
    qu'un léger surcoût (facteur amorti), ce qui donne un score plus lisible.
    """
    AMORTISSEMENT = 0.55
    malus = 0.0
    for f in findings:
        base = SEVERITES.get(f.severite, 0)
        # surcoût amorti : +20% par objet au-delà du 1er, plafonné à x2
        facteur = min(2.0, 1 + 0.2 * max(0, len(f.objets) - 1))
        malus += base * facteur
    score = max(0, round(100 - malus * AMORTISSEMENT))
    return score


def niveau_global(score: int) -> tuple[str, str]:
    """Retourne (libellé, couleur) selon le score."""
    if score >= 80:
        return "BON", "#16a34a"
    if score >= 60:
        return "À SURVEILLER", "#ca8a04"
    if score >= 40:
        return "INSUFFISANT", "#ea580c"
    return "CRITIQUE", "#dc2626"


COULEURS_SEV = {
    "CRITIQUE": "#dc2626",
    "ELEVE": "#ea580c",
    "MOYEN": "#ca8a04",
    "FAIBLE": "#0891b2",
    "INFO": "#64748b",
}


def generer_html(findings: list[Finding], organisation: str = "Groupe Lemoine") -> str:
    score = calcul_score(findings)
    libelle, couleur = niveau_global(score)
    date = datetime.now().strftime("%d/%m/%Y à %H:%M")

    # Comptage par sévérité
    par_sev = defaultdict(int)
    for f in findings:
        par_sev[f.severite] += 1

    # Regroupement par catégorie
    par_cat = defaultdict(list)
    for f in findings:
        par_cat[f.categorie].append(f)

    # Ordre de tri des sévérités
    ordre = ["CRITIQUE", "ELEVE", "MOYEN", "FAIBLE", "INFO"]

    cartes_sev = ""
    for sev in ordre:
        n = par_sev.get(sev, 0)
        cartes_sev += f"""
        <div class="sev-card" style="border-top:4px solid {COULEURS_SEV[sev]}">
            <div class="sev-num" style="color:{COULEURS_SEV[sev]}">{n}</div>
            <div class="sev-lbl">{sev}</div>
        </div>"""

    sections = ""
    for cat, items in par_cat.items():
        items_sorted = sorted(items, key=lambda x: ordre.index(x.severite))
        lignes = ""
        for f in items_sorted:
            objets_html = "".join(f"<li>{o}</li>" for o in f.objets)
            lignes += f"""
            <div class="finding">
                <div class="finding-head">
                    <span class="badge" style="background:{COULEURS_SEV[f.severite]}">{f.severite}</span>
                    <span class="finding-title">{f.titre}</span>
                </div>
                <p class="finding-detail">{f.detail}</p>
                <ul class="finding-objs">{objets_html}</ul>
                <p class="finding-reco"><strong>Recommandation :</strong> {f.recommandation}</p>
            </div>"""
        sections += f"""
        <section class="cat">
            <h2>{cat} <span class="cat-count">{len(items)} constat(s)</span></h2>
            {lignes}
        </section>"""

    # Jauge circulaire (SVG)
    circonf = 2 * 3.14159 * 70
    offset = circonf * (1 - score / 100)

    return f"""<!DOCTYPE html>
<html lang="fr">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>SecuPulse — Rapport de posture sécurité</title>
<style>
    * {{ margin:0; padding:0; box-sizing:border-box; }}
    body {{ font-family: -apple-system, 'Segoe UI', Roboto, sans-serif; background:#f1f5f9; color:#0f172a; line-height:1.5; }}
    .wrap {{ max-width:1000px; margin:0 auto; padding:32px 20px; }}
    header.top {{ display:flex; justify-content:space-between; align-items:center; margin-bottom:28px; flex-wrap:wrap; gap:16px; }}
    .logo {{ font-size:1.6rem; font-weight:800; letter-spacing:-0.5px; }}
    .logo span {{ color:#2563eb; }}
    .meta {{ font-size:0.85rem; color:#64748b; text-align:right; }}
    .hero {{ background:#fff; border-radius:16px; padding:32px; display:flex; align-items:center; gap:40px; box-shadow:0 1px 3px rgba(0,0,0,.08); margin-bottom:24px; flex-wrap:wrap; }}
    .gauge {{ position:relative; width:170px; height:170px; flex-shrink:0; }}
    .gauge svg {{ transform:rotate(-90deg); }}
    .gauge-txt {{ position:absolute; inset:0; display:flex; flex-direction:column; align-items:center; justify-content:center; }}
    .gauge-score {{ font-size:2.6rem; font-weight:800; color:{couleur}; }}
    .gauge-max {{ font-size:0.8rem; color:#94a3b8; }}
    .hero-info h1 {{ font-size:1.3rem; margin-bottom:6px; }}
    .hero-status {{ display:inline-block; padding:6px 16px; border-radius:999px; color:#fff; font-weight:700; font-size:0.9rem; background:{couleur}; margin:8px 0; }}
    .hero-info p {{ color:#475569; font-size:0.92rem; max-width:480px; }}
    .sev-grid {{ display:grid; grid-template-columns:repeat(5,1fr); gap:12px; margin-bottom:28px; }}
    .sev-card {{ background:#fff; border-radius:12px; padding:18px 10px; text-align:center; box-shadow:0 1px 3px rgba(0,0,0,.06); }}
    .sev-num {{ font-size:2rem; font-weight:800; }}
    .sev-lbl {{ font-size:0.72rem; color:#64748b; font-weight:600; letter-spacing:0.5px; }}
    section.cat {{ background:#fff; border-radius:14px; padding:24px; margin-bottom:20px; box-shadow:0 1px 3px rgba(0,0,0,.06); }}
    section.cat h2 {{ font-size:1.1rem; margin-bottom:16px; display:flex; justify-content:space-between; align-items:center; border-bottom:2px solid #f1f5f9; padding-bottom:10px; }}
    .cat-count {{ font-size:0.78rem; font-weight:500; color:#94a3b8; }}
    .finding {{ padding:16px; border-radius:10px; background:#f8fafc; margin-bottom:12px; border-left:3px solid #e2e8f0; }}
    .finding-head {{ display:flex; align-items:center; gap:10px; margin-bottom:8px; }}
    .badge {{ color:#fff; font-size:0.68rem; font-weight:700; padding:3px 10px; border-radius:6px; letter-spacing:0.5px; }}
    .finding-title {{ font-weight:700; font-size:0.98rem; }}
    .finding-detail {{ font-size:0.88rem; color:#475569; margin-bottom:8px; }}
    .finding-objs {{ list-style:none; display:flex; flex-wrap:wrap; gap:6px; margin-bottom:8px; }}
    .finding-objs li {{ background:#e2e8f0; font-size:0.78rem; padding:3px 10px; border-radius:6px; font-family:monospace; }}
    .finding-reco {{ font-size:0.85rem; color:#0f172a; background:#eff6ff; padding:8px 12px; border-radius:8px; }}
    footer {{ text-align:center; color:#94a3b8; font-size:0.8rem; margin-top:28px; }}
</style>
</head>
<body>
<div class="wrap">
    <header class="top">
        <div class="logo">Secu<span>Pulse</span></div>
        <div class="meta">
            Rapport généré le {date}<br>
            Organisation : <strong>{organisation}</strong> · Mode démonstration
        </div>
    </header>

    <div class="hero">
        <div class="gauge">
            <svg width="170" height="170">
                <circle cx="85" cy="85" r="70" fill="none" stroke="#e2e8f0" stroke-width="14"/>
                <circle cx="85" cy="85" r="70" fill="none" stroke="{couleur}" stroke-width="14"
                    stroke-linecap="round" stroke-dasharray="{circonf:.0f}" stroke-dashoffset="{offset:.0f}"/>
            </svg>
            <div class="gauge-txt">
                <div class="gauge-score">{score}</div>
                <div class="gauge-max">/ 100</div>
            </div>
        </div>
        <div class="hero-info">
            <h1>Posture de sécurité du SI</h1>
            <span class="hero-status">{libelle}</span>
            <p>Ce rapport synthétise l'état de sécurité du système d'information à partir de
            {len(findings)} constats automatisés (Active Directory, réseau, postes, sauvegardes).
            Chaque exécution recalcule le score et met en évidence les actions prioritaires.</p>
        </div>
    </div>

    <div class="sev-grid">{cartes_sev}</div>

    {sections}

    <footer>
        SecuPulse — Prototype d'automatisation de la posture sécurité · Conçu par Omar Benmansour<br>
        Données simulées à des fins de démonstration. Version réelle branchable sur AD / Nmap / Intune / Veeam.
    </footer>
</div>
</body>
</html>"""


if __name__ == "__main__":
    findings = collect_all("demo")
    html = generer_html(findings)
    with open("rapport_secupulse.html", "w", encoding="utf-8") as fh:
        fh.write(html)
    score = calcul_score(findings)
    print(f"Rapport généré : rapport_secupulse.html")
    print(f"Score de posture : {score}/100 — {niveau_global(score)[0]}")
    print(f"{len(findings)} constats analysés.")
