import cv2
import mediapipe as mp
import numpy as np

# Mediapipe Hand Tracking modelini chaqiramiz
mp_hands = mp.solutions.hands
mp_drawing = mp.solutions.drawing_utils

# Rasm chizish uchun bo'sh canvas
canvas = np.zeros((480, 640, 3), dtype=np.uint8)

# Kamera ochish
cap = cv2.VideoCapture(0)

# Chizish rejimi
drawing = False
prev_x, prev_y = None, None

with mp_hands.Hands(min_detection_confidence=0.7, min_tracking_confidence=0.7, max_num_hands=1) as hands:
    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break

        frame = cv2.flip(frame, 1)
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

        # Mediapipe bilan kaftni aniqlash
        result = hands.process(rgb_frame)

        if result.multi_hand_landmarks:
            for hand_landmarks in result.multi_hand_landmarks:
                # Qo‘l skeletini chizish
                mp_drawing.draw_landmarks(frame, hand_landmarks, mp_hands.HAND_CONNECTIONS)

                # Ko'rsatkich barmoq uchi koordinatalarini olish
                h, w, _ = frame.shape
                index_finger_tip = hand_landmarks.landmark[8]
                x, y = int(index_finger_tip.x * w), int(index_finger_tip.y * h)

                # Agar barmoq birinchi marta aniqlansa
                if prev_x is None or prev_y is None:
                    prev_x, prev_y = x, y

                # Agar barmoqni bosib turgan bo‘lsak (chizish rejimi)
                if drawing:
                    cv2.line(canvas, (prev_x, prev_y), (x, y), (255, 0, 0), 5)
                
                prev_x, prev_y = x, y

        # Rasm va chizilgan narsalarni birlashtirish
        frame = cv2.addWeighted(frame, 0.5, canvas, 0.5, 0)

        cv2.imshow("Qo'l harakati bilan chizish", frame)

        key = cv2.waitKey(1) & 0xFF
        if key == ord("q"):  # Chiqish
            break
        elif key == ord("d"):  # Chizish rejimini yoqish/o‘chirish
            drawing = not drawing
        elif key == ord("c"):  # Canvasni tozalash
            canvas[:] = 0

cap.release()
cv2.destroyAllWindows()
