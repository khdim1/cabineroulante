import pyttsx3
import threading

_engine = None

def _get_engine():
    global _engine
    if _engine is None:
        _engine = pyttsx3.init()
        _engine.setProperty('rate', 150)   # vitesse
        _engine.setProperty('volume', 1.0)
    return _engine

def dire(texte):
    """Parle dans un thread séparé pour ne pas bloquer l'interface."""
    def parler():
        engine = _get_engine()
        engine.say(texte)
        engine.runAndWait()
    threading.Thread(target=parler, daemon=True).start()