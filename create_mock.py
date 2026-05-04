with open("mock_gpio.py", "w") as f:
    f.write('''BCM = "BCM"
IN = "IN"
OUT = "OUT"
HIGH = True
LOW = False

_gpio_state = {}

def setmode(mode):
    pass

def setup(pin, mode, pull_up_down=None):
    _gpio_state[pin] = LOW

def input(pin):
    return _gpio_state.get(pin, LOW)

def output(pin, state):
    _gpio_state[pin] = state

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
''')
