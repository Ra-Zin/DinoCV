import cv2

cap = None
width = 0
height = 0

def init_camera(source = 0, w = 800, h = 800):
    global cap, width, height

    cap = cv2.VideoCapture(source)

    cap.set(cv2.CAP_PROP_FRAME_WIDTH, w)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, h)

    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

def read_frame():
    global cap

    success, frame = cap.read()

    if success:
        frame = cv2.flip(frame, 1)

    return success, frame

def release_camera():
    global cap

    cap.release()
    cap.destroyAllWindows()