import kivy
kivy.require('2.3.1')
from kivy.app import App
from kivy.uix.screenmanager import Screen
from kivy.lang import Builder
from kivy.clock import Clock
from kivy.graphics.texture import Texture
import threading
import cv2
import traceback
import sys
from kivy.config import Config
Config.set('graphics', 'fullscreen', 'auto')
Config.set('graphics', 'borderless', 1)
Config.write()
try:
    Builder.load_file("ui.kv")
except Exception as e:
    print("ERREUR chargement ui.kv :", e)
    traceback.print_exc()
    sys.exit(1)

try:
    from sensors import Capteurs
except Exception as e:
    print("ERREUR import Capteurs :", e)
    traceback.print_exc()
    sys.exit(1)

from recommander import recommander
from imprimer import imprimer_ticket
from database import init_db

class CabineScreen(Screen):
    def __init__(self, **kwargs):
        print("Initialisation CabineScreen...")
        super().__init__(**kwargs)
        try:
            init_db()
            self.capteurs = Capteurs()
            print("Capteurs initialisés.")
        except Exception as e:
            print("ERREUR init capteurs :", e)
            traceback.print_exc()
            # Mode secours
            from sensors import CameraSimulee, GPIO, HX711
            import yaml
            with open("config.yaml") as f:
                config = yaml.safe_load(f)
            class CapteursSimules:
                def __init__(self):
                    self.hx = HX711(5,6)
                    self.hx.set_reading_format("MSB","MSB")
                    self.hx.set_reference_unit(config["capteurs"]["calibration_poids"])
                    self.hx.reset()
                    self.pir_pin = 17
                    GPIO.setmode(GPIO.BCM)
                    GPIO.setup(self.pir_pin, GPIO.IN)
                    self.camera_sim = CameraSimulee()
                    self.camera_stream = self.camera_sim
                    self.reel = False
                def personne_presente(self):
                    return True
                def lire_poids(self):
                    return self.hx.get_weight(5)
                def mesurer_tout(self):
                    m = self.camera_sim.mesurer()
                    m["poids"] = round(self.lire_poids(), 1)
                    m["imc"] = round(m["poids"] / ((m["taille"]/100)**2), 1)
                    return m
                def nettoyer(self):
                    pass
            self.capteurs = CapteursSimules()
            print("Mode secours activé.")

        self.dernieres_mesures = {}
        self.fauteuil = None
        self.mesure_en_cours = False
        Clock.schedule_interval(self.update_avatar, 1/30)
        Clock.schedule_interval(self.verifier_presence, 1.0)
        print("CabineScreen prêt.")

    def update_avatar(self, dt):
        try:
            frame, _ = self.capteurs.camera_stream.get_annotated_frame()
            buf = cv2.flip(frame, 0).tobytes()
            texture = Texture.create(size=(frame.shape[1], frame.shape[0]), colorfmt='bgr')
            texture.blit_buffer(buf, colorfmt='bgr', bufferfmt='ubyte')
            self.ids.avatar.texture = texture
        except Exception as e:
            print("update_avatar error:", e)

    def verifier_presence(self, dt):
        if self.capteurs.personne_presente() and not self.mesure_en_cours:
            self.mesure_en_cours = True
            self.ids.lbl_mesures.text = "Mesure en cours..."
            threading.Thread(target=self.sequence_mesure, daemon=True).start()

    def sequence_mesure(self):
        try:
            m = self.capteurs.mesurer_tout()
            self.dernieres_mesures = m
            self.fauteuil = recommander(m)
        except Exception as e:
            print("Erreur mesure :", e)
        finally:
            self.mesure_en_cours = False
            Clock.schedule_once(lambda dt: self.mettre_a_jour_ui(), 0)

    def mettre_a_jour_ui(self):
        m = self.dernieres_mesures
        if not m or m.get("status") != "ok":
            self.ids.lbl_mesures.text = "Mesure impossible."
            return
        txt = (
            f"Taille : {m['taille']} cm\n"
            f"Poids  : {m['poids']} kg\n"
            f"Hanches : {m['hanches']} cm\n"
            f"Épaules : {m['epaules']} cm\n"
            f"Prof. assise : {m['profondeur_assise']} cm\n"
            f"Haut. poplitée : {m['hauteur_poplitee']} cm\n"
            f"Haut. dossier : {m['hauteur_dossier']} cm\n"
            f"IMC    : {m['imc']}"
        )
        self.ids.lbl_mesures.text = txt
        self.ids.lbl_reco.text = f"FAUTEUIL : {self.fauteuil['nom']}" if self.fauteuil else "Aucun modèle adapté"

    def imprimer(self):
        if self.dernieres_mesures:
            imprimer_ticket(self.dernieres_mesures, self.fauteuil)
            self.ids.lbl_mesures.text += "\nTicket PDF généré !"

class CabineApp(App):
    def build(self):
        print("Construction de l'app...")
        return CabineScreen()

if __name__ == "__main__":
    print("Lancement de l'application...")
    try:
        CabineApp().run()
    except Exception as e:
        print("Erreur fatale :", e)
        traceback.print_exc()