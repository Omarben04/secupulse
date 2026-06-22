# SecuPulse — Tableau de bord automatisé de posture sécurité

> Prototype d'outil d'automatisation conçu pour offrir à une DSI une **vision instantanée et chiffrée** de la sécurité de son système d'information, sans intervention manuelle.

## Le problème

Quand un SI est en cours de construction ou de consolidation, il est difficile de répondre rapidement à la question : **« Où en est ma sécurité, là, maintenant ? »**
Les informations sont éclatées : comptes Active Directory, ports réseau, état des postes, sauvegardes… Faire le tour à la main prend des heures et n'est jamais à jour.

## La solution

SecuPulse collecte automatiquement des indicateurs de sécurité, calcule un **score de posture sur 100**, et génère un **rapport HTML lisible** (exécutable en boucle, ex. chaque lundi matin par mail).

### Domaines analysés
- **Active Directory** : comptes inactifs, comptes à privilèges, mots de passe sans expiration
- **Réseau** : services à risque exposés (RDP, SMB, Telnet), segmentation VLAN
- **Postes & serveurs** : niveau de patch, antivirus, chiffrement disque
- **Sauvegardes** : conformité à la règle 3-2-1

Chaque constat est noté par sévérité (CRITIQUE → INFO) et accompagné d'une **recommandation actionnable**.

## Architecture

```
secupulse/
├── collectors.py   # Collecte des données (mode démo + hooks réels)
├── report.py       # Scoring + génération du rapport HTML
└── rapport_secupulse.html   # Sortie générée
```

- **Mode démo** : données simulées réalistes, pour présenter l'outil sans accès au SI.
- **Mode réel** : chaque collecteur expose un point d'branchement documenté
  (`Get-ADUser` pour l'AD, `Nmap` pour le réseau, Intune/WMI pour les postes, API Veeam pour les sauvegardes).

## Utilisation

```bash
python3 report.py
# -> génère rapport_secupulse.html + affiche le score dans la console
```

## Stack
Python 3 (standard library uniquement pour le cœur), HTML/CSS pour le rapport.
Aucune dépendance externe en mode démo → portable, auditable, facile à déployer.

## Pistes d'évolution
- Branchement réel AD / Nmap / Intune / Veeam
- Historisation du score (courbe de progression dans le temps)
- Envoi automatique par mail (SMTP) et planification (cron / tâche planifiée)
- Export PDF et intégration à un SIEM (Wazuh)

---
*Conçu par Omar Benmansour — étudiant en cybersécurité & infrastructures, dans une logique d'automatisation et de gain de temps opérationnel pour la DSI.*

## Dashboard temps réel

En complément du rapport statique, un **dashboard web temps réel** (Flask) affiche le score en continu,
historise son évolution et liste les constats prioritaires.

```bash
pip install flask
python3 dashboard.py
# -> http://127.0.0.1:5000
```

Le dashboard consomme une API interne `/api/posture` qui renvoie les données au format JSON,
ce qui permet de brancher facilement d'autres outils de visualisation.
