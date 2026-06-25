import cv2
import mediapipe as mp
import numpy as np
import time
import os

# ---------------- Webcam ----------------
camera = cv2.VideoCapture(0)

os.makedirs("saved_drawings", exist_ok=True)

cv2.namedWindow("Air Writing & Drawing Board", cv2.WINDOW_NORMAL)
cv2.setWindowProperty(
    "Air Writing & Drawing Board",
    cv2.WND_PROP_FULLSCREEN,
    cv2.WINDOW_FULLSCREEN
)

# ---------------- MediaPipe ----------------
mp_hands = mp.solutions.hands
hands = mp_hands.Hands(
    min_detection_confidence=0.7,
    min_tracking_confidence=0.7
)

mp_draw = mp.solutions.drawing_utils

# ---------------- Canvas ----------------
drawing_canvas = None
prev_x, prev_y = 0, 0

# ---------------- Smoothing ----------------
smooth_x, smooth_y = 0, 0
smoothing = 0.35

# ---------------- Tools ----------------
brush_size = 12
current_color = (180, 0, 0)

clear_start = None
exit_start = None
save_start = None

saved_message_time = 0

# ---------------- Main Loop ----------------
while True:

    success, frame = camera.read()
    if not success:
        break

    frame = cv2.flip(frame, 1)
    frame = cv2.resize(frame, (1280, 720))

    h, w, _ = frame.shape

    if drawing_canvas is None:
        drawing_canvas = np.zeros((h, w, 3), dtype=np.uint8)

    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    results = hands.process(rgb)

    # ---------------- Header ----------------
    cv2.putText(
        frame,
        "Air Drawing Board",
        (20, 40),
        cv2.FONT_HERSHEY_SIMPLEX,
        1,
        (0, 255, 0),
        2
    )

    cv2.putText(
        frame,
        "Hold SAVE / CLEAR / EXIT",
        (20, 75),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.6,
        (255, 255, 255),
        2
    )

    # ---------------- Brush Buttons ----------------
    brush_buttons = [
        {"center": (int(w * 0.05), 90), "size": 2},
        {"center": (int(w * 0.10), 90), "size": 5},
        {"center": (int(w * 0.15), 90), "size": 10},
        {"center": (int(w * 0.20), 90), "size": 15}
    ]

    for b in brush_buttons:
        cx, cy = b["center"]
        size = b["size"]

        border_color = (
            (0, 255, 0)
            if brush_size == size
            else (180, 180, 180)
        )

        cv2.circle(frame, (cx, cy), size + 12, border_color, 2)
        cv2.circle(frame, (cx, cy), size, current_color, -1)

    # ---------------- Color Buttons ----------------
    color_buttons = [
        {"color": (0, 0, 180), "center": (int(w * 0.60), 90)},
        {"color": (0, 180, 0), "center": (int(w * 0.65), 90)},
        {"color": (180, 0, 0), "center": (int(w * 0.70), 90)},
        {"color": (0, 180, 180), "center": (int(w * 0.75), 90)}
    ]

    for cbtn in color_buttons:
        cx, cy = cbtn["center"]
        color = cbtn["color"]

        border = 3 if color == current_color else 1

        cv2.circle(frame, (cx, cy), 18, (255, 255, 255), border)
        cv2.circle(frame, (cx, cy), 15, color, -1)

    # ---------------- Buttons ----------------
    save_button = (int(w * 0.72), 20, int(w * 0.80), 70)
    clear_button = (int(w * 0.82), 20, int(w * 0.90), 70)
    exit_button = (int(w * 0.91), 20, int(w * 0.99), 70)

    # SAVE
    cv2.rectangle(
        frame,
        (save_button[0], save_button[1]),
        (save_button[2], save_button[3]),
        (0, 200, 0),
        -1
    )

    cv2.putText(
        frame,
        "SAVE",
        (save_button[0] + 10, 55),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.6,
        (255, 255, 255),
        2
    )

    # CLEAR
    cv2.rectangle(
        frame,
        (clear_button[0], clear_button[1]),
        (clear_button[2], clear_button[3]),
        (0, 140, 255),
        -1
    )

    cv2.putText(
        frame,
        "CLEAR",
        (clear_button[0] + 5, 55),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.6,
        (255, 255, 255),
        2
    )

    # EXIT
    cv2.rectangle(
        frame,
        (exit_button[0], exit_button[1]),
        (exit_button[2], exit_button[3]),
        (0, 0, 255),
        -1
    )

    cv2.putText(
        frame,
        "EXIT",
        (exit_button[0] + 12, 55),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.6,
        (255, 255, 255),
        2
    )

    # Brush Preview
    cv2.circle(
        frame,
        (int(w * 0.50), 90),
        brush_size,
        current_color,
        -1
    )

    # ---------------- Hand Detection ----------------
    if results.multi_hand_landmarks and results.multi_handedness:

        hand = results.multi_hand_landmarks[0]
        label = results.multi_handedness[0].classification[0].label

        if label != "Right":
            continue

        mp_draw.draw_landmarks(
            frame,
            hand,
            mp_hands.HAND_CONNECTIONS
        )

        raw_x = int(hand.landmark[8].x * w)
        raw_y = int(hand.landmark[8].y * h)

        smooth_x = int(
            smooth_x + (raw_x - smooth_x) * smoothing
        )
        smooth_y = int(
            smooth_y + (raw_y - smooth_y) * smoothing
        )

        finger_x, finger_y = smooth_x, smooth_y

        cv2.circle(
            frame,
            (finger_x, finger_y),
            10,
            (0, 255, 0),
            -1
        )

        # Brush Selection
        for b in brush_buttons:
            cx, cy = b["center"]

            if np.hypot(finger_x - cx, finger_y - cy) < 20:
                brush_size = b["size"]

        # Color Selection
        for cbtn in color_buttons:
            cx, cy = cbtn["center"]

            if np.hypot(finger_x - cx, finger_y - cy) < 20:
                current_color = cbtn["color"]

        # SAVE
        if (
            save_button[0] < finger_x < save_button[2]
            and
            save_button[1] < finger_y < save_button[3]
        ):

            if save_start is None:
                save_start = time.time()

            elif time.time() - save_start > 1:

                filename = (
                    f"saved_drawings/"
                    f"drawing_{int(time.time())}.png"
                )

                cv2.imwrite(filename, drawing_canvas)

                print("Saved:", filename)

                saved_message_time = time.time()
                save_start = None

        else:
            save_start = None

        # CLEAR
        if (
            clear_button[0] < finger_x < clear_button[2]
            and
            clear_button[1] < finger_y < clear_button[3]
        ):

            if clear_start is None:
                clear_start = time.time()

            elif time.time() - clear_start > 1:

                drawing_canvas[:] = 0
                prev_x, prev_y = 0, 0
                clear_start = None

        else:
            clear_start = None

        # EXIT
        if (
            exit_button[0] < finger_x < exit_button[2]
            and
            exit_button[1] < finger_y < exit_button[3]
        ):

            if exit_start is None:
                exit_start = time.time()

            elif time.time() - exit_start > 1:
                break

        else:
            exit_start = None

        # Drawing
        toolbar_height = 150

        if finger_y > toolbar_height:

            if prev_x == 0 and prev_y == 0:
                prev_x, prev_y = finger_x, finger_y

            cv2.line(
                drawing_canvas,
                (prev_x, prev_y),
                (finger_x, finger_y),
                current_color,
                brush_size + 8,
                cv2.LINE_AA
            )

            steps = 20

            for i in range(steps):
                x = int(prev_x + (finger_x - prev_x) * i / steps)
                y = int(prev_y + (finger_y - prev_y) * i / steps)

                cv2.circle(
                    drawing_canvas,
                    (x, y),
                    brush_size,
                    current_color,
                    -1,
                    lineType=cv2.LINE_AA
               )

            prev_x, prev_y = finger_x, finger_y

        else:
            prev_x, prev_y = 0, 0

    else:
        prev_x, prev_y = 0, 0

    # Saved Message
    if time.time() - saved_message_time < 2:
        cv2.putText(
            frame,
            "DRAWING SAVED!",
            (500, 40),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.8,
            (0, 255, 0),
            2
        )

    # ---------------- Overlay ----------------
    smooth_canvas = cv2.GaussianBlur(
        drawing_canvas,
        (15, 15),
        0
    )

    frame = cv2.addWeighted(
        frame,
        0.45,
        smooth_canvas,
        1.55,
        0
    )

    cv2.imshow(
        "Air Writing & Drawing Board",
        frame
    )

    if cv2.waitKey(1) & 0xFF == 27:
        break

camera.release()
cv2.destroyAllWindows()