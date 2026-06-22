"""
SecuPulse - Collecteurs de données de posture sécurité
=======================================================
Chaque collecteur retourne une liste de "findings" (constats).
Mode DEMO : données simulées réalistes (pour présentation sans accès SI).
Mode REEL : hooks prêts à brancher (PowerShell AD, Nmap, WMI...).

Auteur : Omar Benmansour
"""

from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime, timedelta
import random


# --- Modèle de donnée commun -------------------------------------------------

SEVERITES = {"CRITIQUE": 14, "ELEVE": 8, "MOYEN": 4, "FAIBLE": 1, "INFO": 0}


@dataclass
class Finding:
    """Un constat de sécurité unitaire."""
    categorie: str          # ex: "Active Directory"
    titre: str              # ex: "Comptes admin sans MFA"
    severite: str           # CRITIQUE / ELEVE / MOYEN / FAIBLE / INFO
    detail: str             # description lisible
    objets: list = field(default_factory=list)   # éléments concernés
    recommandation: str = ""

    @property
    def poids(self) -> int:
        return SEVERITES.get(self.severite, 0) * max(1, len(self.objets))


# --- Collecteur Active Directory --------------------------------------------

def collect_active_directory(mode: str = "demo") -> list[Finding]:
    """Analyse l'hygiène des comptes AD.

    Mode REEL (à implémenter chez le client) :
        PowerShell: Get-ADUser -Filter * -Properties LastLogonDate, PasswordNeverExpires, Enabled
        -> parser la sortie JSON et alimenter les findings.
    """
    if mode == "reel":
        # Hook réel — exemple de commande à exécuter sur un DC :
        # ps = "Get-ADUser -Filter * -Properties LastLogonDate,PasswordNeverExpires,Enabled,AdminCount | ConvertTo-Json"
        # result = subprocess.run(["powershell", "-Command", ps], capture_output=True, text=True)
        # ... parsing ...
        raise NotImplementedError("Brancher Get-ADUser ici lors du déploiement.")

    # --- Mode démo : jeu de données réaliste ---
    findings = []

    comptes_inactifs = ["j.martin", "compta_temp", "stagiaire2024", "old_admin", "test_sql"]
    findings.append(Finding(
        categorie="Active Directory",
        titre="Comptes inactifs > 90 jours non désactivés",
        severite="ELEVE",
        detail="Des comptes n'ont pas été utilisés depuis plus de 90 jours mais restent actifs. "
               "Surface d'attaque inutile (comptes dormants = cible idéale).",
        objets=comptes_inactifs,
        recommandation="Désactiver automatiquement après 90j d'inactivité, supprimer après 180j."
    ))

    admins = ["administrateur", "admin_reseau", "svc_backup", "p.durand"]
    findings.append(Finding(
        categorie="Active Directory",
        titre="Comptes à privilèges élevés",
        severite="MOYEN",
        detail="Nombre de comptes membres de groupes d'administration. À maintenir au strict minimum.",
        objets=admins,
        recommandation="Appliquer le principe du moindre privilège, séparer comptes admin/usage quotidien."
    ))

    pwd_never = ["svc_backup", "svc_sql", "administrateur"]
    findings.append(Finding(
        categorie="Active Directory",
        titre="Mots de passe qui n'expirent jamais",
        severite="ELEVE",
        detail="Comptes avec l'option 'PasswordNeverExpires'. Un mot de passe statique compromis reste valable indéfiniment.",
        objets=pwd_never,
        recommandation="Activer l'expiration ou migrer vers des comptes de service gérés (gMSA)."
    ))

    return findings


# --- Collecteur Réseau (scan ports) -----------------------------------------

def collect_network(mode: str = "demo") -> list[Finding]:
    """Détecte les ports/services exposés inattendus.

    Mode REEL :
        Nmap: nmap -sS -p- <plage> -oX scan.xml  (puis parser le XML)
        ou python-nmap.
    """
    if mode == "reel":
        # import nmap; nm = nmap.PortScanner(); nm.scan('192.168.1.0/24', '1-1024')
        raise NotImplementedError("Brancher le scan Nmap ici lors du déploiement.")

    findings = []

    ports_risque = [
        "192.168.10.12:3389 (RDP exposé)",
        "192.168.10.45:23 (Telnet — protocole non chiffré)",
        "192.168.10.7:445 (SMB)",
    ]
    findings.append(Finding(
        categorie="Réseau",
        titre="Services à risque exposés",
        severite="CRITIQUE",
        detail="Des services sensibles sont accessibles sur le réseau. RDP et SMB sont des vecteurs majeurs "
               "de ransomware ; Telnet transmet les identifiants en clair.",
        objets=ports_risque,
        recommandation="Fermer Telnet, restreindre RDP/SMB par VLAN + firewall, activer le NLA sur RDP."
    ))

    findings.append(Finding(
        categorie="Réseau",
        titre="Équipements sans segmentation VLAN",
        severite="MOYEN",
        detail="Postes utilisateurs et serveurs sur le même segment. Un poste compromis peut atteindre les serveurs.",
        objets=["VLAN unique détecté : 192.168.10.0/24"],
        recommandation="Segmenter : VLAN Serveurs / VLAN Postes / VLAN Invités, filtrage inter-VLAN sur pfSense."
    ))

    return findings


# --- Collecteur Postes de travail -------------------------------------------

def collect_endpoints(mode: str = "demo") -> list[Finding]:
    """État des postes : mises à jour, antivirus, chiffrement."""
    if mode == "reel":
        # WMI / Intune / GPO report : patch level, Defender status, BitLocker status
        raise NotImplementedError("Brancher l'inventaire Intune/WMI ici lors du déploiement.")

    findings = []

    non_patches = ["PC-COMPTA-03", "PC-RH-01", "SRV-FILE-02"]
    findings.append(Finding(
        categorie="Postes & Serveurs",
        titre="Machines sans mises à jour récentes (>30j)",
        severite="ELEVE",
        detail="Machines n'ayant pas reçu de correctifs depuis plus de 30 jours. Vulnérables aux exploits connus.",
        objets=non_patches,
        recommandation="Mettre en place un cycle de patch management mensuel (WSUS / Intune)."
    ))

    sans_av = ["PC-ATELIER-05"]
    findings.append(Finding(
        categorie="Postes & Serveurs",
        titre="Machines sans antivirus actif",
        severite="CRITIQUE",
        detail="Endpoint sans protection antivirus détectée.",
        objets=sans_av,
        recommandation="Déployer Microsoft Defender via GPO/Intune sur 100% du parc."
    ))

    sans_chiffrement = ["PC-COMPTA-03", "PC-DIR-01"]
    findings.append(Finding(
        categorie="Postes & Serveurs",
        titre="Postes portables non chiffrés",
        severite="MOYEN",
        detail="Portables sans chiffrement disque. Vol = fuite de données directe.",
        objets=sans_chiffrement,
        recommandation="Activer BitLocker via GPO, séquestre des clés dans l'AD."
    ))

    return findings


# --- Collecteur Sauvegardes -------------------------------------------------

def collect_backups(mode: str = "demo") -> list[Finding]:
    """Vérifie l'état des sauvegardes (règle 3-2-1)."""
    if mode == "reel":
        raise NotImplementedError("Brancher l'API Veeam/Cohesity ici lors du déploiement.")

    findings = []
    findings.append(Finding(
        categorie="Sauvegarde",
        titre="Pas de copie hors-site (règle 3-2-1 incomplète)",
        severite="ELEVE",
        detail="Sauvegardes présentes localement mais aucune copie externalisée détectée. "
               "Un ransomware chiffrant le NAS détruirait aussi les sauvegardes.",
        objets=["Backup local OK", "Copie hors-site MANQUANTE", "Test de restauration : jamais effectué"],
        recommandation="Appliquer 3-2-1 : 3 copies, 2 supports, 1 hors-site (immutable/air-gap)."
    ))
    return findings


def collect_all(mode: str = "demo") -> list[Finding]:
    """Lance tous les collecteurs."""
    findings = []
    for collector in (collect_active_directory, collect_network,
                      collect_endpoints, collect_backups):
        findings.extend(collector(mode))
    return findings


if __name__ == "__main__":
    for f in collect_all():
        print(f"[{f.severite:8}] {f.categorie:18} | {f.titre} ({len(f.objets)} objet(s))")
