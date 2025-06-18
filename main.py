#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Générateur de QR Code pour Paiement des Arbitres de Handball
Version 1.0 - Interface restructurée avec template séparé et sauvegarde temps réel

Fonctionnalités principales :
- Génération de QR codes sécurisés pour arbitres
- Template d'email personnalisable dans un onglet dédié
- Historique complet des générations
- Sauvegarde automatique temps réel des paramètres
- Normalisation des données pour éviter les doublons
"""

import hashlib
import json
import re
import sys
import os
import urllib.parse
from datetime import datetime
from pathlib import Path

import qrcode
import unicodedata
from PyQt5.QtCore import Qt, QDate, QTime, QSettings, QTimer
from PyQt5.QtGui import QPixmap, QFont, QCursor, QIcon
from PyQt5.QtWidgets import (QApplication, QMainWindow, QTabWidget, QWidget,
                             QVBoxLayout, QHBoxLayout, QFormLayout, QLineEdit,
                             QPushButton, QLabel, QTextEdit, QMessageBox,
                             QFileDialog, QDateEdit, QTimeEdit, QTableWidget, QTableWidgetItem, QHeaderView,
                             QGroupBox, QDialog)

def resource_path(relative_path):
    """
    Obtient le chemin absolu vers une ressource, fonctionne en dev ET après build PyInstaller.

    En développement : utilise le chemin relatif normal
    Après build PyInstaller : utilise le dossier temporaire _MEIPASS

    Args:
        relative_path (str): Chemin relatif vers la ressource (ex: "handball.png")

    Returns:
        str: Chemin absolu vers la ressource
    """
    try:
        # PyInstaller crée un dossier temporaire et stocke le chemin dans _MEIPASS
        base_path = sys._MEIPASS
    except AttributeError:
        # Mode développement normal
        base_path = os.path.abspath(".")

    full_path = os.path.join(base_path, relative_path)

    return full_path

class QRCodePopup(QDialog):
    """
    Popup plein écran pour afficher le QR code en grand format.
    Permet de voir les détails du QR code et facilite le scan sur mobile.
    """

    def __init__(self, qr_pixmap, parent=None):
        super().__init__(parent)
        self.qr_pixmap = qr_pixmap
        self.init_ui()

    def init_ui(self):
        """Initialise l'interface de la popup plein écran"""
        # Configuration de la fenêtre en plein écran
        self.setWindowTitle("QR Code - Vue Agrandie")
        self.setWindowFlags(Qt.Dialog | Qt.WindowMaximizeButtonHint | Qt.WindowCloseButtonHint)
        self.setModal(True)

        # Layout principal
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)

        # En-tête avec titre et instructions
        header_layout = QVBoxLayout()

        instruction = QLabel("💡 Scannez ce QR code avec votre téléphone pour ouvrir l'email pré-rempli")
        instruction.setAlignment(Qt.AlignCenter)
        instruction.setObjectName("popupInstruction")
        instruction.setWordWrap(True)
        header_layout.addWidget(instruction)

        layout.addLayout(header_layout)

        # Zone QR code principale qui s'étend
        self.qr_display = QLabel()
        self.qr_display.setAlignment(Qt.AlignCenter)
        self.qr_display.setObjectName("popupQRDisplay")
        self.qr_display.setMinimumHeight(400)

        # Affichage du QR code
        self.update_qr_display()

        # Le QR code prend tout l'espace disponible
        layout.addWidget(self.qr_display, 1)

        # Boutons en bas
        button_layout = QHBoxLayout()
        button_layout.addStretch()

        # Bouton pour maximiser/restaurer
        self.toggle_fullscreen_btn = QPushButton("📺 Plein Écran")
        self.toggle_fullscreen_btn.setObjectName("secondaryBtn")
        self.toggle_fullscreen_btn.clicked.connect(self.toggle_fullscreen)
        button_layout.addWidget(self.toggle_fullscreen_btn)

        # Bouton fermer
        close_btn = QPushButton("❌ Fermer")
        close_btn.clicked.connect(self.close)
        button_layout.addWidget(close_btn)

        button_layout.addStretch()
        layout.addLayout(button_layout)

        # Application des styles
        self.apply_popup_styles()

    def apply_popup_styles(self):
        """Applique les styles spécifiques à la popup"""
        self.setStyleSheet("""
            QDialog {
                background-color: #f8f9fa;
            }
            
            QLabel#popupTitle {
                font-size: 24px;
                font-weight: bold;
                color: #2E4057;
                margin: 10px;
            }
            
            QLabel#popupInstruction {
                font-size: 16px;
                color: #666;
                margin: 5px 0 20px 0;
                padding: 10px;
                background-color: #e3f2fd;
                border-radius: 8px;
            }
            
            QLabel#popupQRDisplay {
                background-color: white;
                border: 3px solid #4CAF50;
                border-radius: 12px;
                padding: 20px;
                margin: 10px;
            }
            
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                padding: 12px 24px;
                border-radius: 6px;
                font-weight: bold;
                font-size: 14px;
                min-width: 120px;
                margin: 5px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
            QPushButton:pressed {
                background-color: #3e8e41;
            }
            
            QPushButton#secondaryBtn {
                background-color: #2196F3;
            }
            QPushButton#secondaryBtn:hover {
                background-color: #1976D2;
            }
        """)

    def update_qr_display(self):
        """Met à jour l'affichage du QR code selon la taille de la fenêtre"""
        if not self.qr_pixmap:
            return

        # Calcul de la taille optimale
        display_size = self.qr_display.size()
        if display_size.width() <= 0 or display_size.height() <= 0:
            # Taille par défaut si pas encore affiché
            qr_size = 500
        else:
            available_size = min(display_size.width() - 60, display_size.height() - 60)
            qr_size = max(300, min(available_size, 800))

        # Redimensionnement et affichage
        scaled_pixmap = self.qr_pixmap.scaled(
            qr_size, qr_size, Qt.KeepAspectRatio, Qt.SmoothTransformation
        )
        self.qr_display.setPixmap(scaled_pixmap)

    def toggle_fullscreen(self):
        """Bascule entre mode fenêtré et plein écran"""
        if self.isFullScreen():
            self.showNormal()
            self.toggle_fullscreen_btn.setText("📺 Plein Écran")
        else:
            self.showFullScreen()
            self.toggle_fullscreen_btn.setText("🪟 Mode Fenêtre")

    def resizeEvent(self, event):
        """Redimensionne le QR code lors du changement de taille de fenêtre"""
        super().resizeEvent(event)
        self.update_qr_display()

    def keyPressEvent(self, event):
        """Gestion des touches clavier"""
        if event.key() == Qt.Key_Escape:
            if self.isFullScreen():
                self.showNormal()
                self.toggle_fullscreen_btn.setText("📺 Plein Écran")
            else:
                self.close()
        elif event.key() == Qt.Key_F11:
            self.toggle_fullscreen()
        else:
            super().keyPressEvent(event)

class EmailTemplatePopup(QDialog):
    """
    Popup dédiée pour afficher l'aperçu du template email.
    Permet de voir le rendu final avec des données d'exemple.
    """

    def __init__(self, template_content, test_data, parent=None):
        super().__init__(parent)
        self.template_content = template_content
        self.test_data = test_data
        self.init_ui()

    def init_ui(self):
        """Initialise l'interface de la popup de test template"""
        self.setWindowTitle("Test du Template Email")
        self.setWindowFlags(Qt.Dialog | Qt.WindowMaximizeButtonHint | Qt.WindowCloseButtonHint)
        self.setModal(True)
        self.resize(800, 600)

        # Layout principal
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)

        # En-tête avec titre et informations
        header_layout = QVBoxLayout()

        instruction = QLabel("💡 Voici comment l'email apparaîtra avec des données d'exemple")
        instruction.setAlignment(Qt.AlignCenter)
        instruction.setObjectName("popupInstruction")
        instruction.setWordWrap(True)
        header_layout.addWidget(instruction)

        layout.addLayout(header_layout)

        # Informations de l'email (destinataire, objet)
        email_info_group = QGroupBox("📬 Informations Email")
        email_info_layout = QVBoxLayout(email_info_group)

        email_details = QLabel(f"""
<b>À :</b> moi@handball.com<br>
<b>Objet :</b> Versement IBAN<br>
<b>Variables utilisées :</b> {', '.join([f'{{{k}}}' for k in self.test_data.keys()])}
        """)
        email_details.setObjectName("emailDetails")
        email_details.setWordWrap(True)
        email_info_layout.addWidget(email_details)

        layout.addWidget(email_info_group)

        # Zone d'affichage du contenu de l'email
        content_group = QGroupBox("📝 Contenu de l'Email")
        content_layout = QVBoxLayout(content_group)

        # Zone de texte pour afficher le template rendu
        self.email_preview = QTextEdit()
        self.email_preview.setReadOnly(True)
        self.email_preview.setObjectName("emailPreview")

        # Générer et afficher le contenu
        try:
            rendered_content = self.template_content.format(**self.test_data)
            self.email_preview.setPlainText(rendered_content)
        except Exception as e:
            self.email_preview.setPlainText(f"❌ Erreur dans le template :\n{str(e)}")

        content_layout.addWidget(self.email_preview, 1)
        layout.addWidget(content_group, 1)

        # Boutons en bas
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        #
        # # Bouton copier le contenu
        # copy_btn = QPushButton("📋 Copier le Contenu")
        # copy_btn.setObjectName("secondaryBtn")
        # copy_btn.clicked.connect(self.copy_content)
        # button_layout.addWidget(copy_btn)

        # Bouton fermer
        close_btn = QPushButton("❌ Fermer")
        close_btn.clicked.connect(self.close)
        button_layout.addWidget(close_btn)

        button_layout.addStretch()
        layout.addLayout(button_layout)

        # Application des styles
        self.apply_popup_styles()

    def apply_popup_styles(self):
        """Applique les styles spécifiques à la popup de template"""
        self.setStyleSheet("""
            QDialog {
                background-color: #f8f9fa;
            }
            
            QLabel#popupTitle {
                font-size: 24px;
                font-weight: bold;
                color: #2E4057;
                margin: 10px;
            }
            
            QLabel#popupInstruction {
                font-size: 16px;
                color: #666;
                margin: 5px 0 20px 0;
                padding: 10px;
                background-color: #e3f2fd;
                border-radius: 8px;
            }
            
            QLabel#emailDetails {
                font-size: 14px;
                color: #444;
                padding: 10px;
                background-color: #fff3e0;
                border-radius: 6px;
            }
            
            QTextEdit#emailPreview {
                font-family: 'Consolas', 'Monaco', 'Courier New', monospace;
                font-size: 13px;
                line-height: 1.4;
                padding: 15px;
                border: 2px solid #4CAF50;
                border-radius: 8px;
                background-color: #ffffff;
            }
            
            QGroupBox {
                font-weight: bold;
                border: 2px solid #cccccc;
                border-radius: 8px;
                margin-top: 1ex;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
            }
            
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                padding: 12px 24px;
                border-radius: 6px;
                font-weight: bold;
                font-size: 14px;
                min-width: 120px;
                margin: 5px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
            QPushButton:pressed {
                background-color: #3e8e41;
            }
            
            QPushButton#secondaryBtn {
                background-color: #2196F3;
            }
            QPushButton#secondaryBtn:hover {
                background-color: #1976D2;
            }
        """)

    def keyPressEvent(self, event):
        """Gestion des touches clavier"""
        if event.key() == Qt.Key_Escape:
            self.close()
        elif event.key() == Qt.Key_Return or event.key() == Qt.Key_Enter:
            if event.modifiers() & Qt.ControlModifier:
                self.copy_content()
        else:
            super().keyPressEvent(event)

class ClickableQRLabel(QLabel):
    """
    Label QR code cliquable avec curseur loupe au survol.
    Émet un signal lors du clic pour ouvrir la popup.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent_window = parent
        self.setObjectName("clickableQRLabel")

    def enterEvent(self, event):
        """Change le curseur en loupe au survol"""
        if self.pixmap() and not self.pixmap().isNull():
            self.setCursor(QCursor(Qt.PointingHandCursor))
        super().enterEvent(event)

    def leaveEvent(self, event):
        """Remet le curseur normal"""
        self.setCursor(QCursor(Qt.ArrowCursor))
        super().leaveEvent(event)

    def mousePressEvent(self, event):
        """Ouvre la popup au clic si un QR code est affiché"""
        if event.button() == Qt.LeftButton and self.pixmap() and not self.pixmap().isNull():
            if hasattr(self.parent_window, 'show_qr_popup'):
                self.parent_window.show_qr_popup()
        super().mousePressEvent(event)

class NoScrollDateEdit(QDateEdit):
    """QDateEdit personnalisé sans défilement à la molette"""

    def wheelEvent(self, event):
        # Ignorer l'événement de la molette sur le widget au survol
        event.ignore()

class NoScrollTimeEdit(QTimeEdit):
    """QTimeEdit personnalisé sans défilement à la molette"""

    def wheelEvent(self, event):
        # Ignorer l'événement de la molette sur le widget au survol
        event.ignore()


class ArbitreQRGenerator(QMainWindow):
    """
    Application principale pour la génération de QR codes pour arbitres de handball.

    L'application permet de :
    - Générer des QR codes sécurisés avec clé de vérification
    - Personnaliser le template d'email
    - Conserver un historique des générations
    - Sauvegarder automatiquement les paramètres
    """

    def __init__(self):
        super().__init__()

        # Icone de l'application
        self.setWindowIcon(QIcon(resource_path("qr.png")))

        # Configuration du sel secret pour le hachage de sécurité
        self.SEL_SECRET = "HANDBALL_ARBITRE_2025_SECRET_SALT"

        # Configuration QSettings pour la sauvegarde des paramètres utilisateur
        self.settings = QSettings("HandballApp", "ArbitreQRGenerator")

        # Fichier d'historique des générations
        self.history_file = "qr_history.json"
        self.generation_history = self.load_history()

        # Template d'email par défaut avec variables remplaçables
        self.default_email_template = """Bonjour,

Je suis l'arbitre du match suivant :

- Équipe 1 : {EQUIPE1}
- Équipe 2 : {EQUIPE2}
- Date : {DATE}
- Heure : {HEURE}

Clé de sécurité : {CLE}

IBAN : _______________________

(ou veuillez joindre un PDF contenant votre IBAN)

Merci."""

        # IMPORTANT: Timer créé AVANT init_ui() car les connecteurs l'utilisent
        # Timer pour la sauvegarde différée (évite de sauvegarder à chaque frappe)
        self.save_timer = QTimer()
        self.save_timer.timeout.connect(self.save_current_settings)
        self.save_timer.setSingleShot(True)

        # Initialisation de l'interface utilisateur
        self.init_ui()

        # Chargement automatique des derniers paramètres sauvegardés
        self.load_settings()

    def init_ui(self):
        """Initialise l'interface utilisateur avec tous les onglets"""
        self.setWindowTitle("Générateur QR Code - Arbitres Handball v1.0")
        self.setGeometry(100, 100, 1000, 800)  # Taille optimisée pour le nouvel agencement

        # Widget central contenant les onglets
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        layout = QVBoxLayout(central_widget)

        # Création du widget à onglets
        self.tab_widget = QTabWidget()
        layout.addWidget(self.tab_widget)

        # Création de tous les onglets
        self.create_generation_tab()      # Onglet 1: Génération de QR Code
        self.create_verification_tab()    # Onglet 2: Vérification de clé
        self.create_template_tab()        # Onglet 3: Template Email
        self.create_history_tab()         # Onglet 4: Historique des générations

        # Application du style CSS
        self.apply_styles()

    def apply_styles(self):
        """Applique les styles CSS harmonisés à l'interface"""
        self.setStyleSheet("""
            /* === STYLE PRINCIPAL === */
            QMainWindow {
                background-color: #f5f5f5;
            }
            
            /* === TITRE PRINCIPAL === */
            QLabel#titleLabel {
                margin: 10px; 
                color: #2E4057;
            }
            
            /* === ONGLETS === */
            QTabWidget::pane {
                border: 1px solid #cccccc;
                background-color: white;
            }
            QTabBar::tab {
                background-color: #e0e0e0;
                padding: 8px 16px;
                margin-right: 2px;
            }
            QTabBar::tab:selected {
                background-color: #4CAF50;
                color: white;
            }
            
            /* === BOUTONS PRIMAIRES (actions principales) === */
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 5px;
                font-weight: bold;
                font-size: 13px;
                min-width: 100px;
                min-height: 25px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
            QPushButton:pressed {
                background-color: #3e8e41;
            }
            QPushButton:disabled {
                background-color: #cccccc;
                color: #666666;
            }
            
            /* === BOUTONS SECONDAIRES === */
            QPushButton#secondaryBtn {
                background-color: #2196F3;
                min-width: 100px;
                min-height: 25px;
                padding: 8px 16px;
                font-size: 13px;
                border-radius: 5px;
                font-weight: bold;
                color: white;
                border: none;
            }
            QPushButton#secondaryBtn:hover {
                background-color: #1976D2;
            }
            QPushButton#secondaryBtn:pressed {
                background-color: #1565C0;
            }
            
            /* === BOUTONS D'ATTENTION/WARNING === */
            QPushButton#warningBtn {
                background-color: #FF9800;
                min-width: 100px;
                min-height: 25px;
                padding: 8px 16px;
                font-size: 13px;
                border-radius: 5px;
                font-weight: bold;
                color: white;
                border: none;
            }
            QPushButton#warningBtn:hover {
                background-color: #F57C00;
            }
            QPushButton#warningBtn:pressed {
                background-color: #EF6C00;
            }
            
            /* === BOUTONS SPÉCIAUX (vérification, génération) === */
            QPushButton#specialBtn {
                background-color: #2196F3;
                min-width: 100px;
                min-height: 25px;
                padding: 8px 16px;
                font-size: 13px;
                border-radius: 5px;
                font-weight: bold;
                color: white;
                border: none;
            }
            QPushButton#specialBtn:hover {
                background-color: #1976D2;
            }
            QPushButton#specialBtn:pressed {
                background-color: #1565C0;
            }
            
            /* === CHAMPS DE SAISIE === */
            QLineEdit, QDateEdit, QTimeEdit {
                padding: 6px;
                border: 1px solid #ddd;
                border-radius: 4px;
                font-size: 13px;
            }
            QLineEdit:focus, QDateEdit:focus, QTimeEdit:focus {
                border-color: #4CAF50;
                outline: none;
            }
            
            /* === ZONE DE TEXTE === */
            QTextEdit {
                border: 1px solid #ddd;
                border-radius: 4px;
                font-size: 13px;
            }
            QTextEdit:focus {
                border-color: #4CAF50;
            }
            
            /* === TEMPLATE EMAIL === */
            QTextEdit#emailTemplate {
                font-family: 'Consolas', 'Monaco', 'Courier New', monospace;
                font-size: 13px;
                line-height: 1.4;
                padding: 15px;
                border: 2px solid #ddd;
                border-radius: 8px;
                background-color: #ffffff;
            }
            QTextEdit#emailTemplate:focus {
                border-color: #4CAF50;
            }
            
            /* === GROUPES === */
            QGroupBox {
                font-weight: bold;
                border: 2px solid #cccccc;
                border-radius: 8px;
                margin-top: 1ex;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
            }
            
            /* === ZONE QR CODE === */
            QLabel#qrLabel {
                border: 2px dashed #ccc; 
                background-color: #fafafa;
            }
            
            /* === QR CODE CLIQUABLE === */
            QLabel#clickableQRLabel {
                border: 2px dashed #ccc; 
                background-color: #fafafa;
                transition: all 0.3s ease;
            }
            QLabel#clickableQRLabel:hover {
                border: 2px solid #4CAF50;
                background-color: #f0f8f0;
                border-style: solid;
            }
            
            /* === CLÉ DE SÉCURITÉ === */
            QLabel#keyDisplay {
                font-family: monospace; 
                font-size: 14px; 
                color: #333; 
                padding: 10px;
            }
            
            /* === RÉSULTAT VÉRIFICATION VALIDE === */
            QLabel#verifyValid {
                border: 2px solid #4CAF50;
                background-color: #e8f5e8;
                color: #2e7d32;
                font-size: 18px;
                font-weight: bold;
                border-radius: 8px;
                padding: 20px;
            }
            
            /* === RÉSULTAT VÉRIFICATION INVALIDE === */
            QLabel#verifyInvalid {
                border: 2px solid #f44336;
                background-color: #ffebee;
                color: #c62828;
                font-size: 18px;
                font-weight: bold;
                border-radius: 8px;
                padding: 20px;
            }
            
            /* === RÉSULTAT VÉRIFICATION NEUTRE === */
            QLabel#verifyNeutral {
                border: 2px solid #ddd;
                background-color: #fafafa;
                font-size: 18px;
                font-weight: bold;
                border-radius: 8px;
                padding: 30px;
            }
            
            /* === DÉTAILS VÉRIFICATION === */
            QTextEdit#verifyDetails {
                background-color: #f9f9f9;
                border: 1px solid #ddd;
                border-radius: 4px;
                font-family: monospace;
                font-size: 12px;
                padding: 10px;
            }
            
            /* === INFORMATIONS VARIABLES === */
            QLabel#variablesInfo {
                color: #555;
                font-size: 13px;
                padding: 15px;
                background-color: #f0f8ff;
                border-radius: 4px;
            }
            
            /* === INSTRUCTION TEMPLATE === */
            QLabel#templateInstruction {
                color: #666; 
                font-size: 11px; 
                margin-bottom: 5px;
            }
            
            /* === COMPTEUR CARACTÈRES === */
            QLabel#charCountGreen {
                color: #4caf50; 
                font-size: 11px;
            }
            QLabel#charCountOrange {
                color: #ff9800; 
                font-size: 11px;
            }
            QLabel#charCountRed {
                color: #f44336; 
                font-size: 11px; 
                font-weight: bold;
            }
            
            /* === STATISTIQUES === */
            QLabel#stats {
                color: #666;
                font-size: 12px;
            }
        """)

    def create_generation_tab(self):
        """
        Crée l'onglet de génération de QR Code.
        Contient uniquement le formulaire et l'affichage du QR code.
        Layout optimisé : formulaire taille minimale + QR code extensible.
        """
        tab = QWidget()
        self.tab_widget.addTab(tab, "🔗 Génération QR Code")

        layout = QVBoxLayout(tab)

        # === Groupe : Formulaire des informations du match ===
        # Taille fixe minimale - ne s'étend pas en plein écran
        form_group = QGroupBox("📝 Informations du Match")
        form_group.setSizePolicy(form_group.sizePolicy().Preferred, form_group.sizePolicy().Fixed)
        form_layout = QFormLayout(form_group)

        # Champ Équipe 1 avec sauvegarde automatique
        self.equipe1_input = QLineEdit()
        self.equipe1_input.setPlaceholderText("Ex: Les Aigles Rouges")
        self.equipe1_input.textChanged.connect(self.on_form_change)
        form_layout.addRow("Équipe 1:", self.equipe1_input)

        # Champ Équipe 2 avec sauvegarde automatique
        self.equipe2_input = QLineEdit()
        self.equipe2_input.setPlaceholderText("Ex: Les Lions Bleus")
        self.equipe2_input.textChanged.connect(self.on_form_change)
        form_layout.addRow("Équipe 2:", self.equipe2_input)

        # Sélecteur de date avec sauvegarde automatique
        self.date_input = NoScrollDateEdit()
        self.date_input.setDate(QDate.currentDate())
        self.date_input.setCalendarPopup(True)
        self.date_input.dateChanged.connect(self.on_form_change)
        form_layout.addRow("Date du match:", self.date_input)

        # Sélecteur d'heure avec sauvegarde automatique
        self.heure_input = NoScrollTimeEdit()
        self.heure_input.setTime(QTime(18, 30))
        self.heure_input.timeChanged.connect(self.on_form_change)
        form_layout.addRow("Heure du match:", self.heure_input)

        # Ajout du formulaire sans stretch (garde sa taille minimale)
        layout.addWidget(form_group)

        # === Bouton de génération ===
        # Taille fixe - ne prend pas d'espace supplémentaire
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        self.generate_btn = QPushButton("🔗 Générer QR Code")
        self.generate_btn.clicked.connect(self.generate_qr_code)
        btn_layout.addWidget(self.generate_btn)

        btn_layout.addStretch()
        layout.addLayout(btn_layout)

        # === Groupe : Affichage du QR Code généré ===
        # Ce groupe va prendre TOUT l'espace restant disponible
        qr_group = QGroupBox("📱 QR Code Généré")
        qr_layout = QVBoxLayout(qr_group)

        # Zone d'affichage de l'image QR - S'ÉTEND pour remplir l'espace
        self.qr_label = ClickableQRLabel(self)
        self.qr_label.setAlignment(Qt.AlignCenter)
        self.qr_label.setMinimumHeight(300)  # Hauteur minimale
        self.qr_label.setObjectName("qrLabel")
        self.qr_label.setText("Le QR Code apparaîtra ici après génération\n\n💡 Cliquez sur le QR code pour l'agrandir")
        self.qr_label.setScaledContents(False)  # Garde les proportions du QR code

        # Le QR label prend tout l'espace vertical disponible avec stretch = 1
        qr_layout.addWidget(self.qr_label, 1)

        # Affichage de la clé de sécurité générée - Taille fixe
        self.key_display = QLabel()
        self.key_display.setAlignment(Qt.AlignCenter)
        self.key_display.setObjectName("keyDisplay")
        self.key_display.setSizePolicy(self.key_display.sizePolicy().Preferred, self.key_display.sizePolicy().Fixed)
        qr_layout.addWidget(self.key_display)

        # Bouton de sauvegarde du QR code - Taille fixe
        save_layout = QHBoxLayout()
        save_layout.addStretch()

        self.save_btn = QPushButton("💾 Sauvegarder QR Code")
        self.save_btn.clicked.connect(self.save_qr_code)
        self.save_btn.setEnabled(False)  # Désactivé tant qu'aucun QR n'est généré
        save_layout.addWidget(self.save_btn)

        save_layout.addStretch()
        qr_layout.addLayout(save_layout)

        # Ajout du groupe QR avec stretch = 1 pour qu'il prenne tout l'espace restant
        layout.addWidget(qr_group, 1)

    def create_verification_tab(self):
        """
        Crée l'onglet de vérification des clés de sécurité.

        IMPORTANT: Cet onglet est le SEUL moyen de vérifier l'authenticité d'une clé,
        car les clés ne sont affichées nulle part ailleurs dans l'application.
        Il est essentiel pour valider les emails reçus des arbitres.
        Layout optimisé pour utiliser tout l'espace disponible.
        """
        tab = QWidget()
        self.tab_widget.addTab(tab, "✅ Vérification Clé")

        layout = QVBoxLayout(tab)

        # === Groupe : Formulaire de vérification ===
        # Taille fixe - ne s'étend pas pour laisser place au résultat
        form_group = QGroupBox("🔍 Données à Vérifier")
        form_group.setSizePolicy(form_group.sizePolicy().Preferred, form_group.sizePolicy().Fixed)
        form_layout = QFormLayout(form_group)

        # Champs pour la vérification (séparés des champs de génération)
        self.verif_equipe1 = QLineEdit()
        self.verif_equipe1.setPlaceholderText("Équipe 1 du match à vérifier")
        form_layout.addRow("Équipe 1:", self.verif_equipe1)

        self.verif_equipe2 = QLineEdit()
        self.verif_equipe2.setPlaceholderText("Équipe 2 du match à vérifier")
        form_layout.addRow("Équipe 2:", self.verif_equipe2)

        self.verif_date = NoScrollDateEdit()
        self.verif_date.setDate(QDate.currentDate())
        self.verif_date.setCalendarPopup(True)
        form_layout.addRow("Date du match:", self.verif_date)

        self.verif_heure = NoScrollTimeEdit()
        self.verif_heure.setTime(QTime(18, 30))
        form_layout.addRow("Heure du match:", self.verif_heure)

        self.key_to_verify = QLineEdit()
        self.key_to_verify.setPlaceholderText("Clé à vérifier (10 caractères)")
        self.key_to_verify.setMaxLength(10)
        self.key_to_verify.setObjectName("keyToVerify")
        form_layout.addRow("Clé à vérifier:", self.key_to_verify)

        layout.addWidget(form_group)

        # === Bouton de vérification ===
        # Taille fixe
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        self.verify_btn = QPushButton("🔍 Vérifier Clé")
        self.verify_btn.setObjectName("specialBtn")
        self.verify_btn.clicked.connect(self.verify_key)
        btn_layout.addWidget(self.verify_btn)

        btn_layout.addStretch()
        layout.addLayout(btn_layout)

        # === Zone d'affichage du résultat ÉTENDUE ===
        # Cette zone prend TOUT l'espace vertical restant
        result_group = QGroupBox("📊 Résultat de la Vérification")
        result_layout = QVBoxLayout(result_group)

        # Zone de résultat principal - plus grande
        self.verification_result = QLabel()
        self.verification_result.setAlignment(Qt.AlignCenter)
        self.verification_result.setMinimumHeight(150)  # Plus grand qu'avant (120 → 150)
        self.verification_result.setObjectName("verifyNeutral")
        self.verification_result.setText("Entrez les données du match et la clé à vérifier")
        result_layout.addWidget(self.verification_result)

        # Zone de détails supplémentaires qui s'étend
        self.verification_details = QTextEdit()
        self.verification_details.setReadOnly(True)
        self.verification_details.setMaximumHeight(200)
        self.verification_details.setObjectName("verifyDetails")
        self.verification_details.setPlaceholderText("Les détails de la vérification apparaîtront ici...")
        result_layout.addWidget(self.verification_details)

        # Le groupe résultat prend tout l'espace restant avec stretch = 1
        layout.addWidget(result_group, 1)

    def create_template_tab(self):
        """
        Crée l'onglet dédié à la configuration du template d'email.
        Permet de personnaliser le contenu de l'email généré.
        Layout optimisé pour une édition confortable du template.
        """
        tab = QWidget()
        self.tab_widget.addTab(tab, "📧 Template Email")

        layout = QVBoxLayout(tab)

        # === Informations sur les variables disponibles ===
        # Section compacte en haut
        info_group = QGroupBox("🏷️ Variables Disponibles")
        info_group.setSizePolicy(info_group.sizePolicy().Preferred, info_group.sizePolicy().Fixed)
        info_layout = QVBoxLayout(info_group)

        variables_info = QLabel("""
<b>Variables remplacées automatiquement dans le template :</b><br>
• <code>{EQUIPE1}</code> - Nom de la première équipe<br>
• <code>{EQUIPE2}</code> - Nom de la deuxième équipe<br>  
• <code>{DATE}</code> - Date du match (format YYYY-MM-DD)<br>
• <code>{HEURE}</code> - Heure du match (format HH:MM)<br>
• <code>{CLE}</code> - Clé de sécurité générée (10 caractères)
        """)
        variables_info.setObjectName("variablesInfo")
        variables_info.setWordWrap(True)
        info_layout.addWidget(variables_info)

        layout.addWidget(info_group)

        # === Zone d'édition du template ÉTENDUE ===
        # Cette section prend TOUT l'espace vertical restant
        template_group = QGroupBox("🖊️ Template Email Personnalisable")
        template_layout = QVBoxLayout(template_group)

        # Instruction d'utilisation compacte
        instruction_label = QLabel("💡 <i>Modifiez le template ci-dessous. Les variables seront automatiquement remplacées lors de la génération.</i>")
        instruction_label.setObjectName("templateInstruction")
        instruction_label.setWordWrap(True)
        template_layout.addWidget(instruction_label)

        # Zone de texte pour éditer le template - TRÈS GRANDE
        self.email_template = QTextEdit()
        self.email_template.setPlainText(self.default_email_template)
        self.email_template.setObjectName("emailTemplate")
        self.email_template.textChanged.connect(self.on_template_change)

        # La zone d'édition prend tout l'espace disponible avec stretch = 1
        template_layout.addWidget(self.email_template, 1)

        # === Boutons de gestion du template ===
        # Section compacte en bas
        template_btn_layout = QHBoxLayout()

        # Bouton pour réinitialiser le template par défaut
        reset_template_btn = QPushButton("🔄 Réinitialiser Template")
        reset_template_btn.setObjectName("warningBtn")
        reset_template_btn.clicked.connect(self.reset_template)
        template_btn_layout.addWidget(reset_template_btn)

        template_btn_layout.addStretch()

        # Indicateur de caractères
        self.char_count_label = QLabel("Caractères: 0")
        self.char_count_label.setObjectName("charCountGreen")
        template_btn_layout.addWidget(self.char_count_label)

        template_btn_layout.addStretch()

        # Bouton pour tester le template avec des données d'exemple
        test_template_btn = QPushButton("🧪 Tester Template")
        test_template_btn.setObjectName("secondaryBtn")
        test_template_btn.clicked.connect(self.test_template)
        template_btn_layout.addWidget(test_template_btn)

        template_layout.addLayout(template_btn_layout)

        # Le groupe template prend tout l'espace restant avec stretch = 1
        layout.addWidget(template_group, 1)

        # Mise à jour initiale du compteur de caractères
        self.update_char_count()

    def create_history_tab(self):
        """
        Crée l'onglet d'historique des générations de QR codes.
        Affiche un tableau avec toutes les générations passées.
        """
        tab = QWidget()
        self.tab_widget.addTab(tab, "📚 Historique")

        layout = QVBoxLayout(tab)

        # === En-tête avec titre et boutons de gestion ===
        header_layout = QHBoxLayout()

        history_title = QLabel("📚 Historique des QR Codes Générés")
        history_title.setFont(QFont("", 14, QFont.Bold))
        header_layout.addWidget(history_title)

        header_layout.addStretch()

        # Bouton pour vider l'historique
        clear_btn = QPushButton("🗑️ Vider l'historique")
        clear_btn.setObjectName("warningBtn")
        clear_btn.clicked.connect(self.clear_history)
        header_layout.addWidget(clear_btn)

        layout.addLayout(header_layout)

        # === Tableau d'historique ===
        # SÉCURITÉ: Les clés ne sont volontairement PAS affichées dans l'historique
        # pour éviter qu'elles soient visibles et réutilisables par des tiers
        # L'onglet vérification reste le seul moyen de valider une clé reçue
        self.history_table = QTableWidget()
        self.history_table.setColumnCount(4)  # Suppression de la colonne clé pour la sécurité
        self.history_table.setHorizontalHeaderLabels([
            "Date/Heure Génération", "Équipe 1", "Équipe 2", "Match (Date/Heure)"
        ])

        # Configuration de la table pour un affichage optimal (sans colonne clé)
        header = self.history_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)  # Date génération
        header.setSectionResizeMode(1, QHeaderView.Stretch)           # Équipe 1
        header.setSectionResizeMode(2, QHeaderView.Stretch)           # Équipe 2
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents)  # Date match

        layout.addWidget(self.history_table)

        # === Zone de statistiques ===
        stats_layout = QHBoxLayout()
        self.stats_label = QLabel()
        self.stats_label.setObjectName("stats")
        self.update_stats()
        stats_layout.addWidget(self.stats_label)
        stats_layout.addStretch()

        layout.addLayout(stats_layout)

        # Chargement initial de l'historique
        self.refresh_history()

    def normalize_string(self, text):
        """
        Normalise une chaîne de caractères pour éviter les doublons.

        Args:
            text (str): Texte à normaliser

        Returns:
            str: Texte normalisé (minuscules, sans accents, espaces multiples supprimés)
        """
        if not text:
            return ""

        # Suppression des espaces en début/fin et conversion en minuscules
        text = text.strip().lower()

        # Suppression des accents et caractères spéciaux
        text = unicodedata.normalize('NFD', text)
        text = ''.join(c for c in text if unicodedata.category(c) != 'Mn')

        # Suppression des caractères non-alphanumériques (sauf espaces)
        text = re.sub(r'[^a-z0-9\s]', '', text)

        # Remplacement des espaces multiples par un seul espace
        text = re.sub(r'\s+', ' ', text)

        return text.strip()

    def on_form_change(self):
        """
        Appelée à chaque modification d'un champ du formulaire.
        Déclenche une sauvegarde différée des paramètres.
        """
        # Arrêt du timer précédent et redémarrage pour éviter de sauvegarder trop souvent
        self.save_timer.stop()
        self.save_timer.start(500)  # Sauvegarde après 500ms d'inactivité

    def on_template_change(self):
        """
        Appelée à chaque modification du template email.
        Déclenche une sauvegarde différée du template et met à jour le compteur.
        """
        self.on_form_change()  # Utilise le même mécanisme de sauvegarde différée
        self.update_char_count()  # Met à jour le compteur de caractères

    def update_char_count(self):
        """
        Met à jour le compteur de caractères du template.
        """
        if hasattr(self, 'email_template') and hasattr(self, 'char_count_label'):
            char_count = len(self.email_template.toPlainText())
            self.char_count_label.setText(f"Caractères: {char_count:,}")

            # Changement de classe CSS selon la longueur
            if char_count > 1000:
                self.char_count_label.setObjectName("charCountRed")
            elif char_count > 500:
                self.char_count_label.setObjectName("charCountOrange")
            else:
                self.char_count_label.setObjectName("charCountGreen")

            # Réappliquer le style après changement d'objectName
            self.char_count_label.style().unpolish(self.char_count_label)
            self.char_count_label.style().polish(self.char_count_label)

    def generate_security_key(self, equipe1, equipe2, date, heure):
        """
        Génère la clé de sécurité SHA256 avec normalisation des données.

        Args:
            equipe1 (str): Nom de la première équipe
            equipe2 (str): Nom de la deuxième équipe
            date (str): Date du match (YYYY-MM-DD)
            heure (str): Heure du match (HH:MM)

        Returns:
            str: Clé de sécurité (10 premiers caractères hexadécimaux en majuscules)
        """
        # Normalisation des noms d'équipes pour éviter les variations
        normalized_equipe1 = self.normalize_string(equipe1)
        normalized_equipe2 = self.normalize_string(equipe2)

        # Construction de la chaîne à hacher avec le format standardisé
        data_string = f"{normalized_equipe1};{normalized_equipe2};{date};{heure};{self.SEL_SECRET}"

        # Calcul du hash SHA256
        hash_object = hashlib.sha256(data_string.encode('utf-8'))
        hash_hex = hash_object.hexdigest()

        # Retour des 10 premiers caractères en majuscules
        return hash_hex[:10].upper()

    def create_mailto_link(self, equipe1, equipe2, date, heure, security_key):
        """
        Crée le lien mailto avec l'email pré-rempli selon le template personnalisé.

        Args:
            equipe1 (str): Nom de la première équipe
            equipe2 (str): Nom de la deuxième équipe
            date (str): Date du match
            heure (str): Heure du match
            security_key (str): Clé de sécurité

        Returns:
            str: Lien mailto formaté
        """
        subject = "Versement IBAN"

        # Utilisation du template personnalisé avec remplacement des variables
        template = self.email_template.toPlainText()
        body = template.format(
            EQUIPE1=equipe1.strip(),  # Utilisation des noms originaux (non normalisés) pour l'affichage
            EQUIPE2=equipe2.strip(),
            DATE=date,
            HEURE=heure,
            CLE=security_key
        )

        # Encodage URL pour compatibilité avec les clients email
        mailto_link = f"mailto:moi@handball.com?subject={urllib.parse.quote(subject)}&body={urllib.parse.quote(body)}"
        return mailto_link

    def generate_qr_code(self):
        """
        Génère le QR Code complet avec validation, normalisation et sauvegarde.
        Cette méthode orchestre tout le processus de génération.

        SÉCURITÉ: La clé de sécurité n'est volontairement PAS affichée à l'écran
        pour garantir qu'elle ne soit accessible que via le scan du QR code.
        """
        # === Validation des champs obligatoires ===
        equipe1_raw = self.equipe1_input.text().strip()
        equipe2_raw = self.equipe2_input.text().strip()

        if not equipe1_raw or not equipe2_raw:
            QMessageBox.warning(self, "Erreur", "Veuillez remplir les noms des deux équipes.")
            return

        # === Récupération et formatage des données ===
        date = self.date_input.date().toString("yyyy-MM-dd")
        heure = self.heure_input.time().toString("HH:mm")

        # === Génération de la clé de sécurité (avec normalisation interne) ===
        security_key = self.generate_security_key(equipe1_raw, equipe2_raw, date, heure)

        # === Création du lien mailto ===
        mailto_link = self.create_mailto_link(equipe1_raw, equipe2_raw, date, heure, security_key)

        # === Génération du QR Code ===
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(mailto_link)
        qr.make(fit=True)

        # === Création et sauvegarde temporaire de l'image ===
        qr_image = qr.make_image(fill_color="black", back_color="white")
        temp_path = "temp_qr.png"
        qr_image.save(temp_path)

        # === Affichage dans l'interface avec adaptation dynamique ===
        pixmap = QPixmap(temp_path)

        # Calcul de la taille optimale pour le QR code selon l'espace disponible
        # Le QR code s'adapte à la taille de la zone d'affichage
        label_size = self.qr_label.size()
        available_size = min(label_size.width() - 20, label_size.height() - 20)  # Marge de 20px

        # Taille minimale de 200px, mais peut aller jusqu'à l'espace disponible
        qr_size = max(200, min(available_size, 800))  # Maximum 800px même en très grand écran

        scaled_pixmap = pixmap.scaled(qr_size, qr_size, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        self.qr_label.setPixmap(scaled_pixmap)

        # === Information de sécurité (VOLONTAIREMENT sans afficher la clé) ===
        # Note sécurité: La clé n'est pas affichée pour éviter qu'elle soit vue sans scanner le QR code
        # Cela garantit que seul celui qui scanne le QR code a accès à la clé de vérification
        self.key_display.setText("🔐 Clé de sécurité intégrée dans le QR Code (non affichée pour des raisons de sécurité)\n\n💡 Cliquez sur le QR Code ci-dessus pour l'agrandir")

        # === Stockage pour la sauvegarde et le redimensionnement ===
        self.current_qr_image = qr_image
        self.current_qr_pixmap = pixmap  # Stockage du pixmap original pour redimensionnement
        self.current_match_info = f"{self.normalize_string(equipe1_raw)}_vs_{self.normalize_string(equipe2_raw)}_{date}_{heure.replace(':', 'h')}"

        # === Activation du bouton de sauvegarde ===
        self.save_btn.setEnabled(True)

        # === Ajout à l'historique ===
        self.add_to_history(equipe1_raw, equipe2_raw, date, heure, security_key)

        # === Notification de succès ===
        QMessageBox.information(self, "Succès", "QR Code généré avec succès !")

    def add_to_history(self, equipe1, equipe2, date, heure, security_key):
        """
        Ajoute une nouvelle génération à l'historique.

        SÉCURITÉ: La clé est sauvegardée dans le fichier JSON pour traçabilité,
        mais n'est jamais affichée dans l'interface utilisateur.

        Args:
            equipe1 (str): Nom de la première équipe
            equipe2 (str): Nom de la deuxième équipe
            date (str): Date du match
            heure (str): Heure du match
            security_key (str): Clé de sécurité générée (sauvegardée mais non affichée)
        """
        entry = {
            "timestamp": datetime.now().isoformat(),
            "equipe1": equipe1.strip(),
            "equipe2": equipe2.strip(),
            "date": date,
            "heure": heure,
            "security_key": security_key,
            # Note: template_used supprimé selon les spécifications
        }

        # Ajout en début de liste (plus récent en premier)
        self.generation_history.append(entry)
        self.save_history()
        self.refresh_history()

    def show_qr_popup(self):
        """
        Affiche le QR code dans une popup plein écran.
        Permet un affichage agrandi pour faciliter le scan.
        """
        if not hasattr(self, 'current_qr_pixmap') or not self.current_qr_pixmap:
            QMessageBox.information(self, "Information", "Aucun QR Code à afficher.\nVeuillez d'abord générer un QR Code.")
            return

        # Création et affichage de la popup
        popup = QRCodePopup(self.current_qr_pixmap, self)
        popup.exec_()

    def save_qr_code(self):
        """
        Sauvegarde le QR Code généré dans un fichier PNG.
        Propose un nom de fichier automatique basé sur les données du match.
        """
        if not hasattr(self, 'current_qr_image'):
            QMessageBox.warning(self, "Erreur", "Aucun QR Code à sauvegarder.")
            return

        # Nom de fichier suggéré basé sur les informations du match
        suggested_name = f"QR_Arbitre_{self.current_match_info}.png"

        # Dialogue de sauvegarde avec filtre sur les images PNG
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Sauvegarder le QR Code",
            suggested_name,
            "Images PNG (*.png);;Tous les fichiers (*)"
        )

        if file_path:
            try:
                self.current_qr_image.save(file_path)
                QMessageBox.information(self, "Succès", f"QR Code sauvegardé dans :\n{file_path}")
            except Exception as e:
                QMessageBox.critical(self, "Erreur", f"Impossible de sauvegarder le fichier :\n{str(e)}")

    def verify_key(self):
        """
        Vérifie la validité d'une clé de sécurité en la recalculant.
        Compare la clé fournie avec la clé attendue pour les données saisies.
        """
        # === Récupération et validation des données ===
        equipe1 = self.verif_equipe1.text().strip()
        equipe2 = self.verif_equipe2.text().strip()
        key_to_check = self.key_to_verify.text().strip().upper()

        if not equipe1 or not equipe2 or not key_to_check:
            QMessageBox.warning(self, "Erreur", "Veuillez remplir tous les champs.")
            return

        if len(key_to_check) != 10:
            QMessageBox.warning(self, "Erreur", "La clé doit contenir exactement 10 caractères.")
            return

        # === Récupération de la date et heure ===
        date = self.verif_date.date().toString("yyyy-MM-dd")
        heure = self.verif_heure.time().toString("HH:mm")

        # === Génération de la clé attendue ===
        expected_key = self.generate_security_key(equipe1, equipe2, date, heure)

        # === Comparaison et affichage du résultat ===
        if key_to_check == expected_key:
            self.verification_result.setText("✅ CLÉ VALIDE")
            self.verification_result.setObjectName("verifyValid")
        else:
            self.verification_result.setText("❌ CLÉ INVALIDE")
            self.verification_result.setObjectName("verifyInvalid")

        # Réappliquer le style après changement d'objectName
        self.verification_result.style().unpolish(self.verification_result)
        self.verification_result.style().polish(self.verification_result)

        # === Affichage des détails dans la zone dédiée ===
        # Afficher seulement les 4 derniers caractères de la clé attendue
        masked_expected_key = "******" + expected_key[-4:]  # Masque les 6 premiers, affiche les 4 derniers

        details_text = f"""DÉTAILS DE LA VÉRIFICATION
{'='*50}

📊 RÉSULTAT: {'✅ VALIDE' if key_to_check == expected_key else '❌ INVALIDE'}

🔑 CLÉS:
   • Clé fournie    : {key_to_check}
   • Clé attendue   : {masked_expected_key}

🏐 MATCH:
   • Équipe 1       : {equipe1}
   • Équipe 2       : {equipe2}  
   • Date           : {date}
   • Heure          : {heure}
   
🕐 Vérification effectuée le {datetime.now().strftime('%d/%m/%Y à %H:%M:%S')}
        """

        self.verification_details.setPlainText(details_text)

        # Notification popup optionnelle pour les cas critiques
        if key_to_check != expected_key:
            QMessageBox.warning(
                self,
                "Clé Invalide Détectée",
                f"⚠️ ATTENTION: La clé fournie ne correspond pas au match.\n\n"
                f"Cela peut indiquer:\n"
                f"• Une erreur de saisie\n"
                f"• Une tentative de fraude\n"
                f"• Des données de match incorrectes\n\n"
                f"Vérifiez attentivement les informations saisies."
            )

    def reset_template(self):
        """
        Remet le template d'email à sa valeur par défaut.
        """
        self.email_template.setPlainText(self.default_email_template)
        QMessageBox.information(self, "Template réinitialisé", "Le template a été remis à sa valeur par défaut.")

    def test_template(self):
        """
        Teste le template avec des données d'exemple pour vérifier le rendu.
        Affiche le résultat dans une popup dédiée.
        """
        # Données d'exemple pour le test
        test_data = {
            'EQUIPE1': 'Les Aigles Rouges',
            'EQUIPE2': 'Les Lions Bleus',
            'DATE': '2025-06-20',
            'HEURE': '18:30',
            'CLE': 'ABC123DEF0'
        }

        # Récupération du template actuel
        template = self.email_template.toPlainText()

        # Affichage dans une popup dédiée
        popup = EmailTemplatePopup(template, test_data, self)
        popup.exec_()

    def load_history(self):
        """
        Charge l'historique des générations depuis le fichier JSON.

        Returns:
            list: Liste des entrées d'historique
        """
        try:
            if Path(self.history_file).exists():
                with open(self.history_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except Exception as e:
            pass
        return []

    def save_history(self):
        """
        Sauvegarde l'historique des générations dans le fichier JSON.
        """
        try:
            with open(self.history_file, 'w', encoding='utf-8') as f:
                json.dump(self.generation_history, f, indent=2, ensure_ascii=False)
        except Exception as e:
            pass

    def refresh_history(self):
        """
        Actualise l'affichage du tableau d'historique avec les dernières données.

        SÉCURITÉ: Les clés de sécurité ne sont volontairement pas affichées
        pour maintenir la sécurité du système et l'utilité de l'onglet vérification.
        """
        self.history_table.setRowCount(len(self.generation_history))

        # Affichage en ordre inverse (plus récent en premier)
        for row, entry in enumerate(reversed(self.generation_history)):
            # Colonne 0: Date/Heure de génération
            timestamp = datetime.fromisoformat(entry["timestamp"])
            self.history_table.setItem(row, 0, QTableWidgetItem(
                timestamp.strftime("%d/%m/%Y %H:%M")
            ))

            # Colonne 1: Équipe 1
            self.history_table.setItem(row, 1, QTableWidgetItem(entry["equipe1"]))

            # Colonne 2: Équipe 2
            self.history_table.setItem(row, 2, QTableWidgetItem(entry["equipe2"]))

            # Colonne 3: Date et heure du match
            match_info = f"{entry['date']} {entry['heure']}"
            self.history_table.setItem(row, 3, QTableWidgetItem(match_info))

            # Note: Clé de sécurité volontairement omise pour des raisons de sécurité

        # Mise à jour des statistiques
        self.update_stats()

    def clear_history(self):
        """
        Vide complètement l'historique après confirmation de l'utilisateur.
        """
        reply = QMessageBox.question(
            self,
            "Confirmation",
            "Êtes-vous sûr de vouloir vider tout l'historique ?\n\nCette action est irréversible.",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            self.generation_history = []
            self.save_history()
            self.refresh_history()
            QMessageBox.information(self, "Succès", "Historique vidé avec succès.")

    def update_stats(self):
        """
        Met à jour l'affichage des statistiques d'utilisation.
        """
        total = len(self.generation_history)
        today = datetime.now().date()

        # Comptage des générations du jour
        today_count = sum(1 for entry in self.generation_history
                          if datetime.fromisoformat(entry["timestamp"]).date() == today)

        self.stats_label.setText(f"📊 Total: {total} QR codes générés | Aujourd'hui: {today_count}")

    def save_current_settings(self):
        """
        Sauvegarde automatique des paramètres actuels dans QSettings.
        Appelée automatiquement lors des modifications de l'interface.
        """
        # Sauvegarde des champs du formulaire avec strip automatique
        self.settings.setValue("equipe1", self.equipe1_input.text().strip())
        self.settings.setValue("equipe2", self.equipe2_input.text().strip())
        self.settings.setValue("date", self.date_input.date())
        self.settings.setValue("heure", self.heure_input.time())

        # Sauvegarde du template personnalisé
        self.settings.setValue("email_template", self.email_template.toPlainText())

    def load_settings(self):
        """
        Charge automatiquement les derniers paramètres sauvegardés au démarrage.
        Restaure l'état de l'interface à la fermeture précédente.
        """
        # Chargement des champs du formulaire
        equipe1 = self.settings.value("equipe1", "")
        if equipe1:
            self.equipe1_input.setText(equipe1)

        equipe2 = self.settings.value("equipe2", "")
        if equipe2:
            self.equipe2_input.setText(equipe2)

        # Chargement de la date (par défaut: aujourd'hui)
        saved_date = self.settings.value("date", QDate.currentDate())
        self.date_input.setDate(saved_date)

        # Chargement de l'heure (par défaut: 18:30)
        saved_time = self.settings.value("heure", QTime(18, 30))
        self.heure_input.setTime(saved_time)

        # Chargement du template email personnalisé
        saved_template = self.settings.value("email_template", "")
        if saved_template:
            self.email_template.setPlainText(saved_template)

    def resizeEvent(self, event):
        """
        Événement appelé lors du redimensionnement de la fenêtre.
        Redimensionne le QR code pour s'adapter à l'espace disponible.
        """
        super().resizeEvent(event)

        # Redimensionnement du QR code si un QR code est affiché
        if hasattr(self, 'current_qr_pixmap') and self.current_qr_pixmap:
            self.resize_qr_code()

    def resize_qr_code(self):
        """
        Redimensionne le QR code affiché selon l'espace disponible.
        Appelée lors du redimensionnement de la fenêtre.
        """
        if not hasattr(self, 'current_qr_pixmap') or not self.current_qr_pixmap:
            return

        # Calcul de la taille optimale selon l'espace disponible
        label_size = self.qr_label.size()
        available_size = min(label_size.width() - 40, label_size.height() - 40)  # Marge de 40px

        # Taille minimale de 200px, mais peut aller jusqu'à l'espace disponible
        qr_size = max(200, min(available_size, 800))  # Maximum 800px même en très grand écran

        # Redimensionnement et affichage
        scaled_pixmap = self.current_qr_pixmap.scaled(
            qr_size, qr_size, Qt.KeepAspectRatio, Qt.SmoothTransformation
        )
        self.qr_label.setPixmap(scaled_pixmap)

    def closeEvent(self, event):
        """
        Événement appelé à la fermeture de l'application.
        Sauvegarde automatiquement les derniers paramètres.
        """
        # Sauvegarde finale des paramètres
        self.save_current_settings()
        event.accept()

def main():
    """
    Fonction principale de l'application.
    Initialise Qt et lance la fenêtre principale.
    """
    app = QApplication(sys.argv)
    app.setApplicationName("Générateur QR Code Arbitres")
    app.setApplicationVersion("2.0")

    # Création et affichage de la fenêtre principale
    window = ArbitreQRGenerator()
    window.show()

    # Démarrage de la boucle d'événements Qt
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
