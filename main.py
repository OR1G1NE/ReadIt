"""
Application OCR + Synthèse Vocale pour Personnes Malvoyantes
Fonctionnalités:
- Capture d'image depuis la caméra
- Prévisualisation temps réel de la caméra (desktop)
- Reconnaissance de texte (OCR)
- Lecture vocale du texte détecté
- Interface accessible et simple
"""

import os
import cv2
import threading
from datetime import datetime
from pathlib import Path
import numpy as np

from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.popup import Popup
from kivy.uix.progressbar import ProgressBar
from kivy.uix.tabbedpanel import TabbedPanel, TabbedPanelItem
from kivy.uix.image import Image
from kivy.clock import Clock
from kivy.logger import Logger
from kivy.core.window import Window
from kivy.metrics import dp
from kivy.graphics.texture import Texture

# Imports conditionnels selon la plateforme
try:
    import pytesseract
    TESSERACT_AVAILABLE = True
except ImportError:
    TESSERACT_AVAILABLE = False
    Logger.warning("OCR: pytesseract non disponible")

try:
    import pyttsx3
    TTS_DESKTOP_AVAILABLE = True
except ImportError:
    TTS_DESKTOP_AVAILABLE = False
    Logger.warning("TTS: pyttsx3 non disponible")

try:
    from plyer import tts, camera
    from kivy.utils import platform
    PLYER_AVAILABLE = True
    IS_MOBILE = platform in ('android', 'ios')
except ImportError:
    PLYER_AVAILABLE = False
    IS_MOBILE = False
    Logger.warning("Mobile: plyer non disponible")


class CameraPreview(BoxLayout):
    """Widget de prévisualisation de la caméra"""
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.orientation = 'vertical'
        self.padding = dp(10)
        self.spacing = dp(10)
        
        # Variables caméra
        self.camera = None
        self.camera_active = False
        self.capture_event = None
        
        # Interface de prévisualisation
        self.build_preview_ui()
        
    def build_preview_ui(self):
        """Construit l'interface de prévisualisation"""
        
        # Titre
        title = Label(
            text="Prévisualisation Caméra",
            size_hint_y=None,
            height=dp(40),
            font_size=dp(18),
            halign='center'
        )
        title.bind(size=title.setter('text_size'))
        self.add_widget(title)
        
        # Zone d'affichage de la caméra
        self.camera_display = Image(
            size_hint=(1, 0.8),
            allow_stretch=True,
            keep_ratio=True
        )
        # Image par défaut
        self.camera_display.source = 'data/logo/kivy-icon-32.png'  # Image par défaut Kivy
        self.add_widget(self.camera_display)
        
        # Boutons de contrôle
        control_layout = BoxLayout(
            orientation='horizontal',
            size_hint_y=None,
            height=dp(60),
            spacing=dp(10)
        )
        
        self.start_btn = Button(
            text="Démarrer Caméra",
            font_size=dp(16),
            background_color=(0.2, 0.8, 0.2, 1)
        )
        self.start_btn.bind(on_press=self.start_camera)
        control_layout.add_widget(self.start_btn)
        
        self.stop_btn = Button(
            text="Arrêter Caméra",
            font_size=dp(16),
            background_color=(0.8, 0.2, 0.2, 1),
            disabled=True
        )
        self.stop_btn.bind(on_press=self.stop_camera)
        control_layout.add_widget(self.stop_btn)
        
        self.add_widget(control_layout)
        
        # Informations
        self.info_label = Label(
            text="Cliquez sur 'Démarrer Caméra' pour voir la prévisualisation",
            size_hint_y=None,
            height=dp(40),
            font_size=dp(14),
            color=(0.7, 0.7, 0.7, 1),
            halign='center'
        )
        self.info_label.bind(size=self.info_label.setter('text_size'))
        self.add_widget(self.info_label)
    
    def start_camera(self, *args):
        """Démarre la prévisualisation de la caméra"""
        if self.camera_active:
            return
            
        try:
            self.camera = cv2.VideoCapture(0)
            if not self.camera.isOpened():
                self.info_label.text = "Erreur: Impossible d'ouvrir la caméra"
                return
            
            # Configuration de la caméra
            self.camera.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
            self.camera.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
            self.camera.set(cv2.CAP_PROP_FPS, 30)
            
            self.camera_active = True
            self.start_btn.disabled = True
            self.stop_btn.disabled = False
            self.info_label.text = "Caméra active - Prévisualisation en cours"
            
            # Démarrer la capture périodique
            self.capture_event = Clock.schedule_interval(self.update_camera, 1.0/30.0)
            
        except Exception as e:
            Logger.error(f"Erreur démarrage caméra: {e}")
            self.info_label.text = f"Erreur: {e}"
    
    def stop_camera(self, *args):
        """Arrête la prévisualisation de la caméra"""
        if not self.camera_active:
            return
            
        self.camera_active = False
        
        # Arrêter la capture
        if self.capture_event:
            self.capture_event.cancel()
            self.capture_event = None
        
        # Libérer la caméra
        if self.camera:
            self.camera.release()
            self.camera = None
        
        # Réinitialiser l'interface
        self.start_btn.disabled = False
        self.stop_btn.disabled = True
        self.info_label.text = "Caméra arrêtée"
        
        # Remettre l'image par défaut
        self.camera_display.source = 'data/logo/kivy-icon-32.png'
    
    def update_camera(self, dt):
        """Met à jour l'affichage de la caméra"""
        if not self.camera_active or not self.camera:
            return False
        
        try:
            ret, frame = self.camera.read()
            if not ret:
                return True
            
            # Redimensionner le frame pour l'affichage
            frame = cv2.resize(frame, (640, 480))
            
            # Convertir BGR vers RGB
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            
            # Convertir en texture Kivy
            buf = frame_rgb.tobytes()
            texture = Texture.create(size=(640, 480))
            texture.blit_buffer(buf, colorfmt='rgb', bufferfmt='ubyte')
            texture.flip_vertical()
            
            # Mettre à jour l'affichage
            self.camera_display.texture = texture
            
        except Exception as e:
            Logger.error(f"Erreur mise à jour caméra: {e}")
            return False
        
        return True
    
    def capture_current_frame(self):
        """Capture le frame actuel et le sauvegarde"""
        if not self.camera_active or not self.camera:
            return None
        
        try:
            ret, frame = self.camera.read()
            if not ret:
                return None
            
            # Créer le dossier de capture
            capture_dir = Path("captures")
            capture_dir.mkdir(exist_ok=True)
            
            # Sauvegarder l'image
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            image_path = capture_dir / f"preview_capture_{timestamp}.jpg"
            cv2.imwrite(str(image_path), frame)
            
            Logger.info(f"Image capturée depuis prévisualisation: {image_path}")
            return str(image_path)
            
        except Exception as e:
            Logger.error(f"Erreur capture frame: {e}")
            return None
    
    def cleanup(self):
        """Nettoyage lors de la fermeture"""
        self.stop_camera()


class OCRVoiceApp(TabbedPanel):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.do_default_tab = False
        
        # Variables d'état
        self.current_text = ""
        self.is_processing = False
        self.tts_engine = None
        
        # Initialisation TTS
        self.init_tts()
        
        # Interface utilisateur avec onglets
        self.build_ui()
        
        # Configuration des raccourcis clavier pour l'accessibilité
        Window.bind(on_key_down=self.on_keyboard_down)
    
    def init_tts(self):
        """Initialise le moteur de synthèse vocale"""
        try:
            if TTS_DESKTOP_AVAILABLE and not IS_MOBILE:
                self.tts_engine = pyttsx3.init()
                # Configuration voix française si disponible
                voices = self.tts_engine.getProperty('voices')
                for voice in voices:
                    if 'french' in voice.name.lower() or 'fr' in voice.id.lower():
                        self.tts_engine.setProperty('voice', voice.id)
                        break
                self.tts_engine.setProperty('rate', 150)  # Vitesse de lecture
                Logger.info("TTS: Moteur pyttsx3 initialisé")
            elif PLYER_AVAILABLE and IS_MOBILE:
                Logger.info("TTS: Utilisation de plyer.tts pour mobile")
            else:
                Logger.warning("TTS: Aucun moteur disponible")
        except Exception as e:
            Logger.error(f"TTS: Erreur d'initialisation - {e}")
    
    def build_ui(self):
        """Construit l'interface utilisateur avec onglets"""
        
        # Onglet principal OCR
        ocr_tab = TabbedPanelItem(text="OCR Lecteur")
        ocr_content = self.build_ocr_tab()
        ocr_tab.add_widget(ocr_content)
        self.add_widget(ocr_tab)
        
        # Onglet prévisualisation caméra (seulement sur desktop)
        if not IS_MOBILE:
            camera_tab = TabbedPanelItem(text="Caméra")
            self.camera_preview = CameraPreview()
            camera_tab.add_widget(self.camera_preview)
            self.add_widget(camera_tab)
        
        # Définir l'onglet par défaut
        self.default_tab = ocr_tab
    
    def build_ocr_tab(self):
        """Construit l'onglet OCR principal"""
        layout = BoxLayout(orientation='vertical', padding=dp(20), spacing=dp(15))
        
        # Titre
        title = Label(
            text="Lecteur Vocal OCR",
            size_hint_y=None,
            height=dp(60),
            font_size=dp(24),
            halign='center'
        )
        title.bind(size=title.setter('text_size'))
        layout.add_widget(title)
        
        # Instructions
        instructions = Label(
            text="Appuyez sur 'Capturer' pour prendre une photo et lire le texte",
            size_hint_y=None,
            height=dp(80),
            font_size=dp(16),
            halign='center',
            text_size=(None, None)
        )
        instructions.bind(size=instructions.setter('text_size'))
        layout.add_widget(instructions)
        
        # Boutons de capture
        capture_layout = BoxLayout(
            orientation='horizontal',
            size_hint_y=None,
            height=dp(80),
            spacing=dp(10)
        )
        
        # Bouton capture normale
        self.capture_btn = Button(
            text="Capturer et Lire (Espace)",
            font_size=dp(18),
            background_color=(0.2, 0.6, 0.8, 1)
        )
        self.capture_btn.bind(on_press=self.capture_and_read)
        capture_layout.add_widget(self.capture_btn)
        
        # Bouton capture depuis prévisualisation (desktop seulement)
        if not IS_MOBILE:
            self.preview_capture_btn = Button(
                text="Capturer de la Prévisualisation (P)",
                font_size=dp(18),
                background_color=(0.6, 0.4, 0.8, 1)
            )
            self.preview_capture_btn.bind(on_press=self.capture_from_preview)
            capture_layout.add_widget(self.preview_capture_btn)
        
        layout.add_widget(capture_layout)
        
        # Barre de progression
        self.progress = ProgressBar(
            max=100,
            size_hint_y=None,
            height=dp(20),
            opacity=0
        )
        layout.add_widget(self.progress)
        
        # Zone de texte détecté
        self.text_display = TextInput(
            text="Le texte détecté apparaîtra ici...",
            multiline=True,
            readonly=True,
            size_hint_y=0.4,
            font_size=dp(14)
        )
        layout.add_widget(self.text_display)
        
        # Boutons secondaires
        btn_layout = BoxLayout(
            orientation='horizontal',
            size_hint_y=None,
            height=dp(60),
            spacing=dp(10)
        )
        
        # Bouton relire
        self.repeat_btn = Button(
            text="Relire (R)",
            font_size=dp(16),
            background_color=(0.4, 0.7, 0.4, 1),
            disabled=True
        )
        self.repeat_btn.bind(on_press=self.repeat_text)
        btn_layout.add_widget(self.repeat_btn)
        
        # Bouton arrêter
        self.stop_btn = Button(
            text="Arrêter (S)",
            font_size=dp(16),
            background_color=(0.8, 0.4, 0.4, 1),
            disabled=True
        )
        self.stop_btn.bind(on_press=self.stop_speech)
        btn_layout.add_widget(self.stop_btn)
        
        # Bouton aide
        help_btn = Button(
            text="Aide (H)",
            font_size=dp(16),
            background_color=(0.6, 0.6, 0.6, 1)
        )
        help_btn.bind(on_press=self.show_help)
        btn_layout.add_widget(help_btn)
        
        layout.add_widget(btn_layout)
        
        # Message d'état
        self.status_label = Label(
            text="Prêt",
            size_hint_y=None,
            height=dp(30),
            font_size=dp(14),
            color=(0.7, 0.7, 0.7, 1)
        )
        layout.add_widget(self.status_label)
        
        return layout
    
    def on_keyboard_down(self, window, key, scancode, codepoint, modifier):
        """Gestion des raccourcis clavier pour l'accessibilité"""
        if key == 32:  # Espace
            self.capture_and_read()
        elif key == 112:  # P
            if not IS_MOBILE:
                self.capture_from_preview()
        elif key == 114:  # R
            self.repeat_text()
        elif key == 115:  # S
            self.stop_speech()
        elif key == 104:  # H
            self.show_help()
        return True
    
    def capture_and_read(self, *args):
        """Lance la capture normale et la lecture"""
        if self.is_processing:
            return
        
        self.is_processing = True
        self.update_status("Capture en cours...")
        self.show_progress(True)
        
        # Exécution asynchrone pour éviter le blocage de l'UI
        threading.Thread(target=self._capture_process, daemon=True).start()
    
    def capture_from_preview(self, *args):
        """Capture depuis la prévisualisation et lit le texte"""
        if self.is_processing or IS_MOBILE:
            return
        
        if not hasattr(self, 'camera_preview'):
            self.update_status("Erreur: Prévisualisation non disponible")
            return
        
        self.is_processing = True
        self.update_status("Capture depuis prévisualisation...")
        self.show_progress(True)
        
        # Exécution asynchrone
        threading.Thread(target=self._preview_capture_process, daemon=True).start()
    
    def _preview_capture_process(self):
        """Processus de capture depuis la prévisualisation"""
        try:
            # Capture depuis la prévisualisation
            Clock.schedule_once(lambda dt: self.update_progress(30), 0)
            image_path = self.camera_preview.capture_current_frame()
            
            if not image_path:
                Clock.schedule_once(lambda dt: self.on_process_error("Échec de la capture depuis prévisualisation"), 0)
                return
            
            # OCR
            Clock.schedule_once(lambda dt: self.update_status("Analyse du texte..."), 0)
            Clock.schedule_once(lambda dt: self.update_progress(70), 0)
            
            text = self.extract_text(image_path)
            
            # Finalisation
            Clock.schedule_once(lambda dt: self.update_progress(100), 0)
            Clock.schedule_once(lambda dt: self.on_text_extracted(text), 0.5)
            
        except Exception as e:
            Logger.error(f"Erreur de traitement prévisualisation: {e}")
            Clock.schedule_once(lambda dt: self.on_process_error(str(e)), 0)
    
    def _capture_process(self):
        """Processus de capture normale et OCR en arrière-plan"""
        try:
            # Étape 1: Capture d'image
            Clock.schedule_once(lambda dt: self.update_progress(20), 0)
            image_path = self.capture_image()
            
            if not image_path:
                Clock.schedule_once(lambda dt: self.on_process_error("Échec de la capture"), 0)
                return
            
            # Étape 2: OCR
            Clock.schedule_once(lambda dt: self.update_status("Analyse du texte..."), 0)
            Clock.schedule_once(lambda dt: self.update_progress(60), 0)
            
            text = self.extract_text(image_path)
            
            # Étape 3: Finalisation
            Clock.schedule_once(lambda dt: self.update_progress(100), 0)
            Clock.schedule_once(lambda dt: self.on_text_extracted(text), 0.5)
            
        except Exception as e:
            Logger.error(f"Erreur de traitement: {e}")
            Clock.schedule_once(lambda dt: self.on_process_error(str(e)), 0)
    
    def capture_image(self):
        """Capture une image depuis la caméra"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            
            if IS_MOBILE and PLYER_AVAILABLE:
                # Capture mobile avec Plyer
                image_path = f"/storage/emulated/0/Pictures/ocr_capture_{timestamp}.jpg"
                camera.take_picture(filename=image_path, on_complete=self._on_camera_complete)
                return image_path
            else:
                # Capture desktop avec OpenCV
                cap = cv2.VideoCapture(0)
                if not cap.isOpened():
                    Logger.error("Impossible d'ouvrir la caméra")
                    return None
                
                ret, frame = cap.read()
                cap.release()
                
                if ret:
                    # Créer le dossier de capture
                    capture_dir = Path("captures")
                    capture_dir.mkdir(exist_ok=True)
                    
                    image_path = capture_dir / f"capture_{timestamp}.jpg"
                    cv2.imwrite(str(image_path), frame)
                    Logger.info(f"Image capturée: {image_path}")
                    return str(image_path)
                else:
                    Logger.error("Échec de la capture d'image")
                    return None
                    
        except Exception as e:
            Logger.error(f"Erreur de capture: {e}")
            return None
    
    def _on_camera_complete(self, filename):
        """Callback pour la capture mobile"""
        Logger.info(f"Capture mobile terminée: {filename}")
    
    def extract_text(self, image_path):
        """Extrait le texte de l'image avec OCR"""
        if not TESSERACT_AVAILABLE:
            return "OCR non disponible - pytesseract requis"
        
        try:
            # Configuration Tesseract pour le français
            custom_config = r'--oem 3 --psm 6 -l fra+eng'
            
            # Préprocessing de l'image pour améliorer l'OCR
            image = cv2.imread(image_path)
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            
            # Amélioration du contraste
            gray = cv2.convertScaleAbs(gray, alpha=1.2, beta=30)
            
            # Extraction du texte
            text = pytesseract.image_to_string(gray, config=custom_config)
            
            # Nettoyage du texte
            text = text.strip()
            if not text:
                return "Aucun texte détecté dans l'image"
            
            Logger.info(f"Texte extrait: {len(text)} caractères")
            return text
            
        except Exception as e:
            Logger.error(f"Erreur OCR: {e}")
            return f"Erreur d'extraction: {e}"
    
    def on_text_extracted(self, text):
        """Appelé quand le texte est extrait avec succès"""
        self.current_text = text
        self.text_display.text = text
        self.update_status("Lecture en cours...")
        
        # Activation des boutons
        self.repeat_btn.disabled = False
        self.stop_btn.disabled = False
        
        # Lecture automatique
        self.speak_text(text)
        
        # Masquer la progression
        self.show_progress(False)
        self.is_processing = False
    
    def on_process_error(self, error_msg):
        """Appelé en cas d'erreur"""
        self.update_status(f"Erreur: {error_msg}")
        self.speak_text(f"Erreur: {error_msg}")
        self.show_progress(False)
        self.is_processing = False
    
    def speak_text(self, text):
        """Lit le texte à voix haute"""
        try:
            if TTS_DESKTOP_AVAILABLE and self.tts_engine and not IS_MOBILE:
                # TTS desktop
                def speak():
                    self.tts_engine.say(text)
                    self.tts_engine.runAndWait()
                    Clock.schedule_once(lambda dt: self.on_speech_finished(), 0)
                
                threading.Thread(target=speak, daemon=True).start()
                
            elif PLYER_AVAILABLE and IS_MOBILE:
                # TTS mobile
                tts.speak(text)
                Clock.schedule_once(lambda dt: self.on_speech_finished(), 3)
                
            else:
                Logger.warning("Aucun moteur TTS disponible")
                self.update_status("TTS non disponible")
                
        except Exception as e:
            Logger.error(f"Erreur TTS: {e}")
            self.update_status(f"Erreur de lecture: {e}")
    
    def on_speech_finished(self):
        """Appelé quand la lecture est terminée"""
        self.update_status("Lecture terminée")
        self.stop_btn.disabled = True
    
    def repeat_text(self, *args):
        """Relit le dernier texte"""
        if self.current_text:
            self.stop_btn.disabled = False
            self.update_status("Relecture...")
            self.speak_text(self.current_text)
    
    def stop_speech(self, *args):
        """Arrête la lecture en cours"""
        try:
            if TTS_DESKTOP_AVAILABLE and self.tts_engine and not IS_MOBILE:
                self.tts_engine.stop()
            self.update_status("Lecture arrêtée")
            self.stop_btn.disabled = True
        except Exception as e:
            Logger.error(f"Erreur arrêt TTS: {e}")
    
    def show_help(self, *args):
        """Affiche l'aide"""
        help_text = """
Raccourcis clavier:
• Espace: Capturer et lire
• P: Capturer de la prévisualisation (desktop)
• R: Relire le texte
• S: Arrêter la lecture  
• H: Afficher cette aide

Onglets:
• OCR Lecteur: Fonctions principales
• Caméra: Prévisualisation temps réel (desktop)

L'application capture une image, détecte le texte et le lit à voix haute.
Assurez-vous d'avoir un bon éclairage et un texte lisible.
        """
        
        popup = Popup(
            title="Aide - Lecteur Vocal OCR",
            content=Label(text=help_text.strip(), text_size=(dp(400), None), halign='left'),
            size_hint=(0.8, 0.7)
        )
        popup.open()
        
        # Lecture de l'aide
        self.speak_text("Aide affichée. " + help_text.replace("•", "").replace("\n", " "))
    
    def update_status(self, message):
        """Met à jour le message d'état"""
        self.status_label.text = message
        Logger.info(f"Status: {message}")
    
    def update_progress(self, value):
        """Met à jour la barre de progression"""
        self.progress.value = value
    
    def show_progress(self, show):
        """Affiche/masque la barre de progression"""
        self.progress.opacity = 1 if show else 0
        if not show:
            self.progress.value = 0


class OCRVoiceApplication(App):
    """Application principale"""
    
    def build(self):
        self.title = "Lecteur Vocal OCR avec Prévisualisation"
        self.icon = "icon.png"  # Ajoutez votre icône
        return OCRVoiceApp()
    
    def on_start(self):
        """Appelé au démarrage de l'application"""
        Logger.info("Application démarrée")
        
        # Message de bienvenue
        app = self.root
        if IS_MOBILE:
            welcome_msg = "Lecteur Vocal OCR démarré. Appuyez sur Espace pour capturer une image."
        else:
            welcome_msg = "Lecteur Vocal OCR avec prévisualisation démarré. Utilisez l'onglet Caméra pour la prévisualisation ou Espace pour capturer directement."
        app.speak_text(welcome_msg)
    
    def on_stop(self):
        """Appelé à la fermeture de l'application"""
        # Nettoyage de la caméra
        if hasattr(self.root, 'camera_preview'):
            self.root.camera_preview.cleanup()
    
    def on_pause(self):
        """Gestion de la pause (Android)"""
        return True
    
    def on_resume(self):
        """Gestion de la reprise (Android)"""
        pass


if __name__ == "__main__":
    # Configuration pour différentes plateformes
    if IS_MOBILE:
        Logger.info("Exécution sur mobile")
    else:
        Logger.info("Exécution sur desktop avec prévisualisation caméra")
        # Configuration Windows pour Tesseract si nécessaire
        if os.name == 'nt':
            pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
    
    OCRVoiceApplication().run()