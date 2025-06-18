# Générateur QR Code - Arbitres Handball

Application PyQt5 pour la génération de QR codes sécurisés destinés aux arbitres de handball. L'application permet de générer des emails pré-remplis avec clés de vérification pour faciliter les demandes de versement IBAN.

## 🚀 Fonctionnalités

- **Génération de QR codes sécurisés** avec clé de vérification SHA256
- **Template d'email personnalisable** avec variables automatiques
- **Vérification des clés de sécurité** pour valider l'authenticité
- **Historique complet** des générations
- **Sauvegarde automatique** des paramètres utilisateur
- **Interface intuitive** avec onglets dédiés

## 📋 Prérequis

- Python 3.7 ou supérieur
- Système d'exploitation : Windows, macOS, ou Linux

## 🛠️ Installation et Configuration

### 1. Cloner ou télécharger le projet

```bash
git clone <votre-repo>
cd arbitre-qr-generator
```

### 2. ⚠️ **CONFIGURATION OBLIGATOIRE** - Personnaliser le code

**AVANT** de lancer l'application, vous **DEVEZ** modifier ces éléments dans `main.py` :

#### A. Changer l'adresse email de destination (ligne ~157)
```python
# TROUVEZ cette ligne dans create_mailto_link() :
mailto_link = f"mailto:moi@handball.com?subject={urllib.parse.quote(subject)}&body={urllib.parse.quote(body)}"

# REMPLACEZ par votre vraie adresse :
mailto_link = f"mailto:VOTRE-EMAIL@votredomaine.com?subject={urllib.parse.quote(subject)}&body={urllib.parse.quote(body)}"
```

#### B. Changer le sel secret (ligne ~33)
```python
# TROUVEZ cette ligne dans __init__() :
self.SEL_SECRET = "HANDBALL_ARBITRE_2025_SECRET_SALT"

# REMPLACEZ par votre sel unique (gardez-le secret !) :
self.SEL_SECRET = "VOTRE_SEL_SECRET_UNIQUE_2025"
```

> **🔐 SÉCURITÉ CRITIQUE :**
> - Le **sel secret** doit être **unique** et **gardé confidentiel**
> - Une fois changé et des QR codes générés, **ne le modifiez plus jamais**
> - L'**adresse email** sera celle qui recevra tous les emails des arbitres

### 3. Créer un environnement virtuel (recommandé)

```bash
# Création de l'environnement virtuel
python -m venv venv

# Activation (Windows)
venv\Scripts\activate

# Activation (macOS/Linux)
source venv/bin/activate
```

### 3. Installer les dépendances

```bash
pip install -r requirements.txt
```

### 4. Ajouter les fichiers d'icônes

Assurez-vous d'avoir ces fichiers dans le répertoire racine :
- `qr.png` - Icône de l'application (format PNG)
- `qr.ico` - Icône pour l'exécutable Windows (format ICO)

## ▶️ Lancement en mode développement

```bash
python main.py
```

## 📦 Création de l'exécutable

### 1. Installer PyInstaller

```bash
pip install pyinstaller
```

### 2. Builder l'exécutable

```bash
# Utilisation du fichier .spec existant
pyinstaller main.spec

# Ou création manuelle (alternative)
pyinstaller --onefile --windowed --icon=qr.ico --add-data "qr.png;." --add-data "qr.ico;." main.py
```

### 3. Récupérer l'exécutable

L'exécutable sera disponible dans :
```
dist/ArbitreQRGenerator.exe    # Windows
dist/ArbitreQRGenerator        # macOS/Linux
```

## 🎯 Utilisation de l'application

### Onglet 1 : Génération QR Code
1. Remplissez les informations du match :
    - Nom des équipes
    - Date et heure du match
2. Cliquez sur **"Générer QR Code"**
3. Le QR code apparaît avec une clé de sécurité intégrée
4. Cliquez sur le QR code pour l'agrandir
5. Sauvegardez le QR code si nécessaire

### Onglet 2 : Vérification Clé
1. Saisissez les informations du match à vérifier
2. Entrez la clé de sécurité reçue (10 caractères)
3. Cliquez sur **"Vérifier Clé"**
4. Le résultat indique si la clé est valide ou non

### Onglet 3 : Template Email
1. Personnalisez le contenu de l'email généré
2. Utilisez les variables disponibles :
    - `{EQUIPE1}` - Nom de la première équipe
    - `{EQUIPE2}` - Nom de la deuxième équipe
    - `{DATE}` - Date du match
    - `{HEURE}` - Heure du match
    - `{CLE}` - Clé de sécurité
3. Testez le template avec des données d'exemple

### Onglet 4 : Historique
- Consultez toutes les générations précédentes
- Visualisez les statistiques d'utilisation
- Videz l'historique si nécessaire

## 🔐 Sécurité

- **Clés SHA256** : Chaque QR code contient une clé unique basée sur un hash sécurisé
- **Normalisation des données** : Évite les doublons et variations de saisie
- **Clés non affichées** : Les clés de sécurité ne sont pas visibles dans l'interface pour éviter leur réutilisation
- **Vérification obligatoire** : Seul l'onglet vérification permet de valider une clé

## 📁 Structure des fichiers

```
arbitre-qr-generator/
├── main.py              # Application principale
├── main.spec            # Configuration PyInstaller
├── requirements.txt     # Dépendances Python
├── qr.png              # Icône application (PNG)
├── qr.ico              # Icône exécutable (ICO)
├── qr_history.json     # Historique des générations (créé automatiquement)
└── README.md           # Ce fichier
```

## 🔧 Dépendances

- **PyQt5** (5.15.11) - Interface graphique
- **qrcode[pil]** (8.2) - Génération des QR codes
- **Pillow** - Traitement d'images (inclus avec qrcode[pil])

## ⚠️ Notes importantes

1. **🔐 CONFIGURATION OBLIGATOIRE** :
    - **Modifiez IMPÉRATIVEMENT** l'adresse email et le sel secret avant tout déploiement
    - Une fois le sel changé et des QR codes générés, **ne le modifiez plus jamais**
    - Gardez votre sel secret **confidentiel** et **sauvegardé** séparément

2. **Fichiers d'icônes** : Assurez-vous que `qr.png` et `qr.ico` sont présents avant de builder

3. **Sauvegarde automatique** : L'application sauvegarde automatiquement les paramètres

4. **Historique local** : L'historique est stocké dans `qr_history.json`

5. **Sécurité des clés** : Les clés ne sont jamais affichées dans l'interface pour des raisons de sécurité

## 🐛 Résolution de problèmes

### L'exécutable ne se lance pas
- Vérifiez que tous les fichiers d'icônes sont présents
- Testez d'abord en mode développement avec `python main.py`

### Erreur de dépendances
```bash
# Réinstallez les dépendances
pip uninstall -r requirements.txt -y
pip install -r requirements.txt
```

### Problème d'encodage
- Assurez-vous que votre système supporte l'UTF-8
- Les fichiers sont configurés pour l'encodage UTF-8

## ✅ Check-list de déploiement

Avant de distribuer votre application, vérifiez :

- [ ] ✅ Adresse email modifiée dans `main.py` (ligne ~157)
- [ ] ✅ Sel secret personnalisé dans `main.py` (ligne ~33)
- [ ] ✅ Fichiers `qr.png` et `qr.ico` présents
- [ ] ✅ Test en mode développement réussi
- [ ] ✅ Build de l'exécutable réussi
- [ ] ✅ Test de l'exécutable final
- [ ] ✅ Sel secret sauvegardé dans un endroit sûr (pas sur le même ordinateur)

## 📞 Support

Pour signaler un bug ou proposer une amélioration, contactez l'équipe de développement ou créez une issue dans le repository du projet.

## 📄 Licence

Ce projet est destiné à un usage interne pour la gestion des arbitres de handball.

---

**Version** : 1.0  
**Dernière mise à jour** : Juin 2025