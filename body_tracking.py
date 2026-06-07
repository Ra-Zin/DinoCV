import cv2
import mediapipe as mp
from mediapipe.tasks import python
from mediapipe.tasks.python import vision
import urllib.request
import os

# State boxes
landmarker = None
jump_line_y = 0.55
last_hip_y = None
missing_frames = 0
max_missing = 15          # INCREASED from 10
cooldown = 0
cooldown_max = 25

# for ducking
duck_line_y = 0.85
duck_active = False

# NEW: History buffer for smooth, non-jittery hip tracking
hip_history = []
HISTORY_SIZE = 13

POSE_CONNECTIONS = [
    (11, 12), (11, 13), (13, 15), (12, 14), (14, 16),
    (11, 23), (12, 24), (23, 24), (23, 25), (24, 26),
    (25, 27), (26, 28), (27, 29), (28, 30), (29, 31), (30, 32)
]

def setup_tracker(start_line_y=0.55, start_duck_line_y=0.85):
    global landmarker, jump_line_y, duck_line_y, last_hip_y, missing_frames
    global cooldown, hip_history, duck_active

    jump_line_y = start_line_y
    duck_line_y = start_duck_line_y
    last_hip_y = None
    missing_frames = 0
    cooldown = 0
    hip_history = []
    duck_active = False

    model_url = "https://storage.googleapis.com/mediapipe-models/pose_landmarker/pose_landmarker_lite/float16/1/pose_landmarker_lite.task"
    model_path = "pose_landmarker_lite.task"

    if not os.path.exists(model_path):
        print("Downloading pose model...")
        urllib.request.urlretrieve(model_url, model_path)
        print("Done!")

    base_options = python.BaseOptions(model_asset_path=model_path)
    options = vision.PoseLandmarkerOptions(base_options=base_options)
    landmarker = vision.PoseLandmarker.create_from_options(options)

def process_frame(frame):
    # NEW: added duck_line_y and duck_active
    global last_hip_y, missing_frames, cooldown, jump_line_y, hip_history, duck_line_y, duck_active

    h, w = frame.shape[:2]
    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb)
    result = landmarker.detect(mp_image)

    hip_y = 0.0
    hips_visible = False
    raw_hip_y = 0.0

    # --- DETECT & DRAW ---
    if result.pose_landmarks:
        for landmarks in result.pose_landmarks:
            # Draw green dots (lowered threshold to 0.3 for distance)
            for lm in landmarks:
                if lm.visibility > 0.3:
                    cx = int(lm.x * w)
                    cy = int(lm.y * h)
                    cv2.circle(frame, (cx, cy), 5, (0, 255, 0), -1)

            # Draw green skeleton
            for connection in POSE_CONNECTIONS:
                start_idx, end_idx = connection
                if start_idx < len(landmarks) and end_idx < len(landmarks):
                    start = landmarks[start_idx]
                    end = landmarks[end_idx]
                    if start.visibility > 0.3 and end.visibility > 0.3:
                        x1 = int(start.x * w)
                        y1 = int(start.y * h)
                        x2 = int(end.x * w)
                        y2 = int(end.y * h)
                        cv2.line(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)

            # Get hips
            left_hip = landmarks[23]
            right_hip = landmarks[24]

            # LOWERED threshold: 0.3 instead of 0.5
            if left_hip.visibility > 0.3 and right_hip.visibility > 0.3:
                hips_visible = True
                raw_hip_y = (left_hip.y + right_hip.y) / 2

                # Draw red hip dots
                left_x = int(left_hip.x * w)
                left_y = int(left_hip.y * h)
                right_x = int(right_hip.x * w)
                right_y = int(right_hip.y * h)
                cv2.circle(frame, (left_x, left_y), 10, (0, 0, 255), -1)
                cv2.circle(frame, (right_x, right_y), 10, (0, 0, 255), -1)

                # Add to history buffer
                hip_history.append(raw_hip_y)
                if len(hip_history) > HISTORY_SIZE:
                    hip_history.pop(0)

                # MEDIAN FILTER: takes the middle value of sorted history
                sorted_hist = sorted(hip_history)
                mid = len(sorted_hist) // 2
                if len(sorted_hist) % 2 == 0:
                    hip_y = (sorted_hist[mid - 1] + sorted_hist[mid]) / 2
                else:
                    hip_y = sorted_hist[mid]

                last_hip_y = hip_y
                missing_frames = 0

    # --- FALLBACK (extended to 15 frames) ---
    if not hips_visible:
        missing_frames += 1
        if missing_frames <= max_missing and last_hip_y is not None:
            hip_y = last_hip_y
            hips_visible = True
            hip_history.append(hip_history[-1] if hip_history else last_hip_y)
            if len(hip_history) > HISTORY_SIZE:
                hip_history.pop(0)
        else:
            last_hip_y = None
            hip_history = []
    else:
        missing_frames = 0

    # --- COOLDOWN ---
    if cooldown > 0:
        cooldown -= 1

    # --- JUMP DETECTION ---
    jump_triggered = False
    if hips_visible and hip_y < jump_line_y and cooldown == 0:
        jump_triggered = True
        cooldown = cooldown_max

    # --- DUCK DETECTION  <-- NEW BLOCK ---
    if hips_visible:
        if hip_y > duck_line_y:
            duck_active = True
        elif hip_y < duck_line_y - 0.05:   # 0.05 buffer so it doesn't flicker
            duck_active = False
    else:
        duck_active = False

    # --- DRAW DEBUG LINES & TEXT  <-- MODIFIED ---
    jump_px = int(jump_line_y * h)
    duck_px = int(duck_line_y * h)

    cv2.line(frame, (0, jump_px), (w, jump_px), (255, 0, 0), 3)   # Blue = jump line
    cv2.line(frame, (0, duck_px), (w, duck_px), (0, 0, 255), 3)  # Red = duck line  <-- NEW

    cv2.putText(frame, f"hip: {hip_y:.3f}", (20, 40),
                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 0), 2)
    cv2.putText(frame, f"jump: {jump_line_y:.2f}", (20, 70),
                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 0), 2)
    cv2.putText(frame, f"duck: {duck_line_y:.2f}", (20, 100),   # <-- NEW
                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 0), 2)

    # --- RETURN  <-- MODIFIED ---
    return jump_triggered, duck_active, hip_y, hips_visible, frame

def adjust_line(delta):
    global jump_line_y
    jump_line_y = max(0.0, min(1.0, jump_line_y + delta))