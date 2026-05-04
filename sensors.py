import time
import sys
import threading

# Simulation GPIO (inchangée, je la garde entière)
if sys.platform == "win32":
    class GPIO:
        BCM = "BCM"
        IN = "IN"
        OUT = "OUT"
        HIGH = True
        LOW = False
        _state = {}

        @staticmethod
        def setmode(mode):
            pass

        @staticmethod
        def setup(pin, mode, pull_up_down=None):
            GPIO._state[pin] = GPIO.LOW

        @staticmethod
        def input(pin):
            return GPIO._state.get(pin, GPIO.LOW)

        @staticmethod
        def output(pin, state):
            GPIO._state[pin] = state

        @staticmethod
        def cleanup():
            pass

    class HX711:
        def __init__(self, dout, pd_sck):
            self.dout = dout
            self.pd_sck = pd_sck
            self.reference_unit = 1

        def set_reading_format(self, byte_format, bit_format):
            pass

        def set_reference_unit(self, ref_unit):
            self.reference_unit = ref_unit

        def reset(self):
            pass

        def get_weight(self, times=5):
            import random
            return 70.0 + random.uniform(-0.5, 0.5)

        def read_average(self, times=10):
            return self.get_weight(times) * self.reference_unit

else:
    import RPi.GPIO as GPIO
    from hx711 import HX711

import yaml
from edge_camera import CameraEdge, CameraStream

with open("config.yaml") as f:
    config = yaml.safe_load(f)

class CameraSimulee:
    """Simule une caméra pour le développement sans matériel."""
    def __init__(self):
        self.timer = 0

    def get_annotated_frame(self):
        # Dessine un stickman simple qui bouge un peu
        import numpy as np
        import cv2
        frame = np.zeros((480, 640, 3), dtype=np.uint8)
        # Fond sombre
        frame[:] = (10, 5, 20)
        # Stickman animé (coordonnées x, y)
        t = self.timer * 0.1
        head = (320, 100 + int(10 * np.sin(t)))
        neck = (320, 180)
        shoulder_l = (280, 200)
        shoulder_r = (360, 200)
        elbow_l = (250, 250 + int(10 * np.cos(t)))
        elbow_r = (390, 250 + int(10 * np.sin(t)))
        hand_l = (230, 300)
        hand_r = (410, 300)
        hip_l = (290, 350)
        hip_r = (350, 350)
        knee_l = (280, 430)
        knee_r = (360, 430)
        foot_l = (260, 470)
        foot_r = (380, 470)

        color = (0, 255, 255)
        cv2.circle(frame, head, 15, color, 2)
        cv2.line(frame, neck, shoulder_l, color, 2)
        cv2.line(frame, neck, shoulder_r, color, 2)
        cv2.line(frame, shoulder_l, elbow_l, color, 2)
        cv2.line(frame, shoulder_r, elbow_r, color, 2)
        cv2.line(frame, elbow_l, hand_l, color, 2)
        cv2.line(frame, elbow_r, hand_r, color, 2)
        cv2.line(frame, neck, (320, 280), color, 2)
        cv2.line(frame, (320, 280), hip_l, color, 2)
        cv2.line(frame, (320, 280), hip_r, color, 2)
        cv2.line(frame, hip_l, knee_l, color, 2)
        cv2.line(frame, hip_r, knee_r, color, 2)
        cv2.line(frame, knee_l, foot_l, color, 2)
        cv2.line(frame, knee_r, foot_r, color, 2)

        self.timer += 1
        return frame, {
            "taille": 170.0,
            "hanches": 38.0,
            "epaules": 45.0,
            "profondeur_assise": 44.0,
            "hauteur_poplitee": 42.0,
            "hauteur_dossier": 40.0,
            "status": "ok"
        }

    def mesurer(self):
        return self.get_annotated_frame()[1]

    def fermer(self):
        pass


class Capteurs:
    def __init__(self):
        self.hx = HX711(dout=5, pd_sck=6)
        self.hx.set_reading_format("MSB", "MSB")
        self.hx.set_reference_unit(config["capteurs"]["calibration_poids"])
        self.hx.reset()
        time.sleep(1)

        self.pir_pin = 17
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(self.pir_pin, GPIO.IN)

        # Essayer d'initialiser la vraie caméra, sinon simuler
        try:
            camera_edge = CameraEdge()
            self.camera_stream = CameraStream(camera_edge)
            self.camera = camera_edge  # pour les mesures complètes
            self.reel = True
            print("Caméra OAK-D connectée, mode réel.")
        except RuntimeError:
            self.camera_sim = CameraSimulee()
            self.camera_stream = self.camera_sim  # la simulee a aussi get_annotated_frame
            self.reel = False
            print("⚠ Pas de caméra, mode simulation.")

    def personne_presente(self):
        # Simulation : toujours présente pour test (à adapter)
        return True  # Pour la démo, la personne est toujours là
        # Sinon :
        # if GPIO.input(self.pir_pin) == GPIO.HIGH: return True
        # p = self.hx.get_weight(3)
        # return p > config["seuils"]["poids_min_kg"]

    def attendre_personne(self):
        while not self.personne_presente():
            time.sleep(0.2)
        time.sleep(config["seuils"]["stabilisation_secondes"])

    def lire_poids(self):
        return self.hx.get_weight(5)

    def mesurer_tout(self):
        """Mesure complète (avec caméra réelle ou simulée)."""
        if self.reel:
            mesures = self.camera.mesurer()
        else:
            mesures = self.camera_sim.mesurer()
        poids = round(self.lire_poids(), 1)
        taille_m = mesures.get("taille", 0) / 100.0
        imc = round(poids / (taille_m ** 2), 1) if taille_m > 0 else 0
        mesures["poids"] = poids
        mesures["imc"] = imc
        return mesures

    def nettoyer(self):
        if self.reel:
            self.camera.fermer()
        GPIO.cleanup()