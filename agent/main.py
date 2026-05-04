import asyncio, json, sys, os, cv2, base64
from pathlib import Path
if getattr(sys, 'frozen', False):
    BASE = Path(sys.executable).parent
else:
    BASE = Path(__file__).parent
os.chdir(BASE)

from sensors import Capteurs

capteurs = Capteurs()

async def handler(websocket):
    while True:
        try:
            frame, mesures = capteurs.camera_stream.get_annotated_frame()
            ret, jpeg = cv2.imencode('.jpg', frame)
            jpeg_b64 = base64.b64encode(jpeg.tobytes()).decode()
            await websocket.send(json.dumps({"image": jpeg_b64, "mesures": mesures}))
        except:
            break
        await asyncio.sleep(0.03)

async def main():
    try:
        import websockets
    except ImportError:
        print("Installez websockets : pip install websockets")
        sys.exit(1)
    print("Agent démarré sur ws://localhost:9001")
    async with websockets.serve(handler, "127.0.0.1", 9001):
        await asyncio.Future()

if __name__ == "__main__":
    asyncio.run(main())
