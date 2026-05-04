import cv2
import depthai as dai
import mediapipe as mp
import numpy as np
import yaml

with open("config.yaml") as f:
    config = yaml.safe_load(f)

class CameraEdge:
    def __init__(self):
        pipeline = dai.Pipeline()
        cam_rgb = pipeline.create(dai.node.ColorCamera)
        cam_rgb.setResolution(dai.ColorCameraProperties.SensorResolution.THE_1080_P)
        cam_rgb.setInterleaved(False)
        cam_rgb.setBoardSocket(dai.CameraBoardSocket.CAM_A)

        mono_left = pipeline.create(dai.node.MonoCamera)
        mono_left.setResolution(dai.MonoCameraProperties.SensorResolution.THE_400_P)
        mono_left.setBoardSocket(dai.CameraBoardSocket.CAM_B)

        mono_right = pipeline.create(dai.node.MonoCamera)
        mono_right.setResolution(dai.MonoCameraProperties.SensorResolution.THE_400_P)
        mono_right.setBoardSocket(dai.CameraBoardSocket.CAM_C)

        stereo = pipeline.create(dai.node.StereoDepth)
        stereo.setDefaultProfilePreset(dai.node.StereoDepth.PresetMode.HIGH_DENSITY)
        stereo.setDepthAlign(dai.CameraBoardSocket.CAM_A)
        mono_left.out.link(stereo.left)
        mono_right.out.link(stereo.right)

        xout_rgb = pipeline.create(dai.node.XLinkOut)
        xout_rgb.setStreamName("rgb")
        cam_rgb.video.link(xout_rgb.input)

        xout_depth = pipeline.create(dai.node.XLinkOut)
        xout_depth.setStreamName("depth")
        stereo.depth.link(xout_depth.input)

        self.device = dai.Device(pipeline)
        self.q_rgb = self.device.getOutputQueue(name="rgb", maxSize=4, blocking=False)
        self.q_depth = self.device.getOutputQueue(name="depth", maxSize=4, blocking=False)

        calib = self.device.readCalibration()
        intrinsics = calib.getCameraIntrinsics(dai.CameraBoardSocket.CAM_A, dai.Size(1920, 1080))
        self.fx = intrinsics[0][0]
        self.fy = intrinsics[1][1]
        self.cx = intrinsics[0][2]
        self.cy = intrinsics[1][2]

        self.mp_pose = mp.solutions.pose
        self.pose = self.mp_pose.Pose(
            static_image_mode=False,
            model_complexity=1,
            min_detection_confidence=0.6,
            min_tracking_confidence=0.6
        )
        self.H_cam = config["camera"]["position_hauteur_sol_m"]

    def _pixel_to_3d(self, x, y, depth_frame_mm):
        if x < 0 or y < 0 or x >= depth_frame_mm.shape[1] or y >= depth_frame_mm.shape[0]:
            return None
        Z = depth_frame_mm[y, x] / 1000.0
        if Z <= 0.1:
            return None
        X = (x - self.cx) * Z / self.fx
        Y = (y - self.cy) * Z / self.fy
        return (X, Y, Z)

    def _landmark_to_3d(self, landmark, depth_frame):
        h, w = depth_frame.shape
        x_px = int(landmark.x * w)
        y_px = int(landmark.y * h)
        return self._pixel_to_3d(x_px, y_px, depth_frame)

    def mesurer(self):
        mesures = {
            "taille": 0.0, "hanches": 0.0, "epaules": 0.0,
            "profondeur_assise": 0.0, "hauteur_poplitee": 0.0,
            "hauteur_dossier": 0.0, "status": "non_detecte"
        }

        in_rgb = self.q_rgb.get()
        in_depth = self.q_depth.get()
        frame_rgb = in_rgb.getCvFrame()
        depth_frame = in_depth.getFrame()

        rgb = cv2.cvtColor(frame_rgb, cv2.COLOR_BGR2RGB)
        results = self.pose.process(rgb)
        if not results.pose_landmarks:
            return mesures

        lm = results.pose_landmarks.landmark
        indices = {
            "tete": 0, "epaule_g": 11, "epaule_d": 12,
            "hanche_g": 23, "hanche_d": 24,
            "genou_g": 25, "genou_d": 26,
            "cheville_g": 27, "cheville_d": 28,
            "pied_g": 31, "pied_d": 32
        }
        p3d = {}
        for nom, idx in indices.items():
            p3d[nom] = self._landmark_to_3d(lm[idx], depth_frame)

        required = ["hanche_g", "hanche_d", "epaule_g", "epaule_d",
                    "genou_g", "genou_d", "cheville_g", "cheville_d",
                    "tete", "pied_g", "pied_d"]
        if any(p3d[p] is None for p in required):
            mesures["status"] = "points_manquants"
            return mesures

        hg = np.array(p3d["hanche_g"]); hd = np.array(p3d["hanche_d"])
        mesures["hanches"] = round(np.linalg.norm(hg - hd) * 100, 1)

        eg = np.array(p3d["epaule_g"]); ed = np.array(p3d["epaule_d"])
        mesures["epaules"] = round(np.linalg.norm(eg - ed) * 100, 1)

        pg = np.array(p3d["hanche_g"]); pd = np.array(p3d["hanche_d"])
        gg = np.array(p3d["genou_g"]); gd = np.array(p3d["genou_d"])
        dist_g = np.linalg.norm(pg - gg); dist_d = np.linalg.norm(pd - gd)
        mesures["profondeur_assise"] = round(((dist_g + dist_d) / 2) * 100, 1)

        genou_y = (p3d["genou_g"][1] + p3d["genou_d"][1]) / 2
        cheville_y = (p3d["cheville_g"][1] + p3d["cheville_d"][1]) / 2
        mesures["hauteur_poplitee"] = round((self.H_cam - genou_y - (self.H_cam - cheville_y)) * 100, 1)

        epaule_y = (p3d["epaule_g"][1] + p3d["epaule_d"][1]) / 2
        hanche_y = (p3d["hanche_g"][1] + p3d["hanche_d"][1]) / 2
        mesures["hauteur_dossier"] = round(abs(epaule_y - hanche_y) * 100, 1)

        tete_y = p3d["tete"][1]
        pied_y = (p3d["pied_g"][1] + p3d["pied_d"][1]) / 2
        hauteur_tete = self.H_cam - tete_y
        hauteur_pieds = self.H_cam - pied_y
        mesures["taille"] = round((hauteur_tete - hauteur_pieds) * 100, 1)

        mesures["status"] = "ok"
        return mesures

    def fermer(self):
        self.device.close()


class CameraStream:
    def __init__(self, camera_edge):
        self.cam = camera_edge

    def get_annotated_frame(self):
        in_rgb = self.cam.q_rgb.get()
        in_depth = self.cam.q_depth.get()
        frame_rgb = in_rgb.getCvFrame()
        depth_frame = in_depth.getFrame()

        rgb = cv2.cvtColor(frame_rgb, cv2.COLOR_BGR2RGB)
        results = self.cam.pose.process(rgb)
        mesures = {"status": "non_detecte"}

        if results.pose_landmarks:
            mp_draw = mp.solutions.drawing_utils
            mp_draw.draw_landmarks(
                frame_rgb, results.pose_landmarks, mp.solutions.pose.POSE_CONNECTIONS,
                mp_draw.DrawingSpec(color=(0, 255, 255), thickness=2, circle_radius=2),
                mp_draw.DrawingSpec(color=(255, 0, 255), thickness=2, circle_radius=2)
            )
            lm = results.pose_landmarks.landmark
            try:
                h, w, _ = frame_rgb.shape
                tete_y = lm[0].y * h
                pied_g_y = lm[31].y * h
                pied_d_y = lm[32].y * h
                taille_px = abs((pied_g_y + pied_d_y)/2 - tete_y)
                taille_cm = round(taille_px * 0.15, 1)
                mesures = {
                    "taille": taille_cm, "hanches": 0, "epaules": 0,
                    "profondeur_assise": 0, "hauteur_poplitee": 0,
                    "hauteur_dossier": 0, "status": "ok"
                }
            except:
                pass

        return frame_rgb, mesures
