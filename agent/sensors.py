import time, sys, yaml
from edge_camera import CameraEdge, CameraStream

with open("config.yaml") as f:
    config = yaml.safe_load(f)

class GPIO:
    BCM = "BCM"; IN = "IN"; OUT = "OUT"; HIGH = True; LOW = False
    _state = {}
    @staticmethod
    def setmode(mode): pass
    @staticmethod
    def setup(pin, mode, pull_up_down=None): GPIO._state[pin] = GPIO.LOW
    @staticmethod
    def input(pin): return GPIO._state.get(pin, GPIO.LOW)
    @staticmethod
    def output(pin, state): GPIO._state[pin] = state
    @staticmethod
    def cleanup(): pass

class HX711:
    def __init__(self, dout, pd_sck):
        self.ref_unit = config["capteurs"]["calibration_poids"]
    def set_reading_format(self, a, b): pass
    def set_reference_unit(self, r): self.ref_unit = r
    def reset(self): pass
    def get_weight(self, times=5):
        import random
        return 70.0 + random.uniform(-0.5,0.5)

class Capteurs:
    def __init__(self):
        self.hx = HX711(5,6)
        self.hx.reset()
        self.pir_pin = 17
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(self.pir_pin, GPIO.IN)
        try:
            self.camera = CameraEdge()
            self.camera_stream = CameraStream(self.camera)
            self.reel = True
            print("Caméra OAK-D connectée")
        except:
            print("Mode simulation (pas de caméra)")
            from edge_camera import CameraSimulee
            self.camera_sim = CameraSimulee()
            self.camera_stream = self.camera_sim
            self.reel = False
    def personne_presente(self):
        return True
    def mesurer_tout(self):
        return self.camera_stream.get_annotated_frame()[1]
