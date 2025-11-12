# import cv2
# import mediapipe as mp
# import numpy as np
# import time
# import os
# import threading
# import absl.logging
# import google.generativeai as genai
# from PIL import Image
#
# # ================== SETUP ==================
# os.environ["TF_CPP_MIN_LOG_LEVEL"] = "3"
# absl.logging.set_verbosity(absl.logging.ERROR)
#
# mp_hands = mp.solutions.hands
#
# # Gemini setup
# genai.configure(api_key="AIzaSyDWkTV9jzPXj0AmKrKhG5hFf9vMw5_zWeY")
# vlm_model = genai.GenerativeModel("gemini-2.5-flash")
#
# # ================== PARAMETERS ==================
# MOTION_THRESHOLD = 0.01
# COOLDOWN_TIME = 3.0
# TEXT_DISPLAY_TIME = 5.0
#
# # ================== GLOBAL STATES ==================
# analysis_enabled = False
# processing = False
# last_feedback = ""
# last_feedback_time = 0
# last_trigger_time = 0
# prev_center = None
#
# # ================== FUNCTIONS ==================
# def get_hand_center(hand_landmarks):
#     points = np.array([(lm.x, lm.y) for lm in hand_landmarks.landmark])
#     cx, cy = np.mean(points[:, 0]), np.mean(points[:, 1])
#     return (cx, cy)
#
# def draw_text_with_background(frame, text, pos, font_scale=0.7, thickness=2,
#                               text_color=(255, 255, 255), bg_color=(0, 0, 0), alpha=0.6):
#     """Draw readable overlay text with translucent background"""
#     overlay = frame.copy()
#     font = cv2.FONT_HERSHEY_SIMPLEX
#     (text_w, text_h), _ = cv2.getTextSize(text, font, font_scale, thickness)
#     x, y = pos
#     # Background rectangle
#     cv2.rectangle(overlay, (x - 10, y - text_h - 10), (x + text_w + 10, y + 10), bg_color, -1)
#     # Blend with transparency
#     cv2.addWeighted(overlay, alpha, frame, 1 - alpha, 0, frame)
#     # Draw text
#     cv2.putText(frame, text, (x, y), font, font_scale, text_color, thickness, cv2.LINE_AA)
#
# def analyze_frame_with_vlm(frame):
#     """Runs in a background thread to avoid blocking camera"""
#     global last_feedback, last_feedback_time, processing
#     processing = True
#
#     try:
#         image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
#         img_pil = Image.fromarray(image)
#
#         prompt = (
#             "You are a professional ukulele tutor. Analyze this image of a person’s hand "
#             "playing a ukulele. Respond in one or two short lines only. "
#             "Predict which chord it most closely resembles from [F, G, C, Am]. "
#             "Give one quick improvement tip if possible."
#         )
#
#         response = vlm_model.generate_content([prompt, img_pil])
#         feedback = response.text.strip()
#         print("\n🎸 VLM FEEDBACK:", feedback, "\n")
#         last_feedback = feedback
#     except Exception as e:
#         print("Error from VLM:", e)
#         last_feedback = "Error getting feedback from tutor."
#     finally:
#         last_feedback_time = time.time()
#         processing = False
#
# def is_inside_button(x, y, btn_pos):
#     bx, by, bw, bh = btn_pos
#     return bx <= x <= bx + bw and by <= y <= by + bh
#
# # ================== MAIN ==================
# def main():
#     global analysis_enabled, prev_center, last_trigger_time
#
#     cap = cv2.VideoCapture(0)
#     if not cap.isOpened():
#         print("Error: Could not access webcam.")
#         return
#
#     button_pos = (30, 30, 180, 60)  # x, y, w, h
#
#     def click_event(event, x, y, flags, param):
#         global analysis_enabled
#         if event == cv2.EVENT_LBUTTONDOWN and is_inside_button(x, y, button_pos):
#             analysis_enabled = not analysis_enabled
#             print(f"Analysis {'enabled' if analysis_enabled else 'disabled'}")
#
#     cv2.namedWindow("Ukulele AI Tutor")
#     cv2.setMouseCallback("Ukulele AI Tutor", click_event)
#
#     with mp_hands.Hands(
#         static_image_mode=False,
#         max_num_hands=1,
#         min_detection_confidence=0.5,
#         min_tracking_confidence=0.5,
#     ) as hands:
#         while True:
#             ret, frame = cap.read()
#             if not ret:
#                 break
#
#             frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
#             results = hands.process(frame_rgb)
#             overlay = frame.copy()
#             h, w, _ = overlay.shape
#
#             # Draw start/stop button
#             bx, by, bw, bh = button_pos
#             color = (0, 255, 0) if not analysis_enabled else (0, 100, 255)
#             text = "Start Analysis" if not analysis_enabled else "Stop Analysis"
#             cv2.rectangle(overlay, (bx, by), (bx + bw, by + bh), color, -1)
#             cv2.putText(overlay, text, (bx + 10, by + 40),
#                         cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)
#
#             if analysis_enabled and results.multi_hand_landmarks:
#                 for hand_landmarks in results.multi_hand_landmarks:
#                     mp.solutions.drawing_utils.draw_landmarks(
#                         overlay, hand_landmarks, mp_hands.HAND_CONNECTIONS
#                     )
#
#                     center = get_hand_center(hand_landmarks)
#                     if prev_center is not None:
#                         dx = abs(center[0] - prev_center[0])
#                         dy = abs(center[1] - prev_center[1])
#                         motion = np.sqrt(dx**2 + dy**2)
#
#                         if motion > MOTION_THRESHOLD and (time.time() - last_trigger_time) > COOLDOWN_TIME:
#                             print("⚡ Position shift detected!")
#                             last_trigger_time = time.time()
#
#                             if not processing:
#                                 thread = threading.Thread(target=analyze_frame_with_vlm, args=(frame.copy(),))
#                                 thread.start()
#                     prev_center = center
#
#             # Processing indicator
#             if processing:
#                 draw_text_with_background(overlay, "Analyzing... 🎶", (w - 270, 50),
#                                           font_scale=0.7, bg_color=(0, 128, 255))
#
#             # Show AI feedback (with readable overlay)
#             if last_feedback and (time.time() - last_feedback_time) < TEXT_DISPLAY_TIME:
#                 draw_text_with_background(overlay, last_feedback, (50, h - 50),
#                                           font_scale=0.7, bg_color=(30, 30, 30))
#
#             cv2.imshow("Ukulele AI Tutor", overlay)
#
#             key = cv2.waitKey(1) & 0xFF
#             if key == 27:  # ESC
#                 break
#             elif key == ord(' '):  # Spacebar also toggles
#                 analysis_enabled = not analysis_enabled
#                 print(f"Analysis {'enabled' if analysis_enabled else 'disabled'}")
#
#     cap.release()
#     cv2.destroyAllWindows()
#
# if __name__ == "__main__":
#     main()

import cv2
import mediapipe as mp
import numpy as np
import time
import os
import threading
import absl.logging
import google.generativeai as genai
from PIL import Image

# ================== SETUP ==================
os.environ["TF_CPP_MIN_LOG_LEVEL"] = "3"
absl.logging.set_verbosity(absl.logging.ERROR)

mp_hands = mp.solutions.hands

# Gemini setup
genai.configure(api_key="AIzaSyDWkTV9jzPXj0AmKrKhG5hFf9vMw5_zWeY")
vlm_model = genai.GenerativeModel("gemini-2.5-flash")

# ================== PARAMETERS ==================
MOTION_THRESHOLD = 0.01
COOLDOWN_TIME = 3.0
TEXT_DISPLAY_TIME = 5.0

# ================== GLOBAL STATES ==================
analysis_enabled = False
processing = False
last_feedback = ""
last_feedback_time = 0
last_trigger_time = 0
prev_center = None

# ================== FUNCTIONS ==================
def get_hand_center(hand_landmarks):
    points = np.array([(lm.x, lm.y) for lm in hand_landmarks.landmark])
    cx, cy = np.mean(points[:, 0]), np.mean(points[:, 1])
    return (cx, cy)

def draw_text_with_background(frame, text, pos, font_scale=0.7, thickness=2,
                              text_color=(255, 255, 255), bg_color=(0, 0, 0), alpha=0.6):
    """Draw readable overlay text with translucent background"""
    overlay = frame.copy()
    font = cv2.FONT_HERSHEY_SIMPLEX
    (text_w, text_h), _ = cv2.getTextSize(text, font, font_scale, thickness)
    x, y = pos
    # Background rectangle
    cv2.rectangle(overlay, (x - 10, y - text_h - 10), (x + text_w + 10, y + 10), bg_color, -1)
    # Blend with transparency
    cv2.addWeighted(overlay, alpha, frame, 1 - alpha, 0, frame)
    # Draw text
    cv2.putText(frame, text, (x, y), font, font_scale, text_color, thickness, cv2.LINE_AA)

def analyze_frame_with_vlm(frame):
    """Runs in a background thread to avoid blocking camera"""
    global last_feedback, last_feedback_time, processing
    processing = True

    try:
        image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        img_pil = Image.fromarray(image)

        prompt = (
            "You are a professional ukulele tutor. Analyze this image of a person's hand "
            "playing a ukulele. Respond in one or two short lines only. "
            "Predict which chord it most closely resembles from [F, G, C, Am]. "
            "Give one quick improvement tip if possible."
        )

        response = vlm_model.generate_content([prompt, img_pil])
        feedback = response.text.strip()
        print("\n🎸 VLM FEEDBACK:", feedback, "\n")
        last_feedback = feedback
    except Exception as e:
        print("Error from VLM:", e)
        last_feedback = "Error getting feedback from tutor."
    finally:
        last_feedback_time = time.time()
        processing = False

def is_inside_button(x, y, btn_pos):
    bx, by, bw, bh = btn_pos
    return bx <= x <= bx + bw and by <= y <= by + bh

# ================== MAIN ==================
def main():
    global analysis_enabled, prev_center, last_trigger_time

    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("Error: Could not access webcam.")
        return

    button_pos = (30, 30, 180, 60)  # x, y, w, h

    def click_event(event, x, y, flags, param):
        global analysis_enabled
        if event == cv2.EVENT_LBUTTONDOWN and is_inside_button(x, y, button_pos):
            analysis_enabled = not analysis_enabled
            print(f"Analysis {'enabled' if analysis_enabled else 'disabled'}")

    cv2.namedWindow("Ukulele AI Tutor")
    cv2.setMouseCallback("Ukulele AI Tutor", click_event)

    with mp_hands.Hands(
        static_image_mode=False,
        max_num_hands=1,
        min_detection_confidence=0.5,
        min_tracking_confidence=0.5,
    ) as hands:
        while True:
            ret, frame = cap.read()
            if not ret:
                break

            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            results = hands.process(frame_rgb)
            overlay = frame.copy()
            h, w, _ = overlay.shape

            # Draw start/stop button
            bx, by, bw, bh = button_pos
            color = (0, 255, 0) if not analysis_enabled else (0, 100, 255)
            text = "Start Analysis" if not analysis_enabled else "Stop Analysis"
            cv2.rectangle(overlay, (bx, by), (bx + bw, by + bh), color, -1)
            cv2.putText(overlay, text, (bx + 10, by + 40),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)

            if analysis_enabled and results.multi_hand_landmarks:
                for hand_landmarks in results.multi_hand_landmarks:
                    mp.solutions.drawing_utils.draw_landmarks(
                        overlay, hand_landmarks, mp_hands.HAND_CONNECTIONS
                    )

                    center = get_hand_center(hand_landmarks)
                    if prev_center is not None:
                        dx = abs(center[0] - prev_center[0])
                        dy = abs(center[1] - prev_center[1])
                        motion = np.sqrt(dx**2 + dy**2)

                        if motion > MOTION_THRESHOLD and (time.time() - last_trigger_time) > COOLDOWN_TIME:
                            print("⚡ Position shift detected!")
                            last_trigger_time = time.time()

                            if not processing:
                                thread = threading.Thread(target=analyze_frame_with_vlm, args=(frame.copy(),))
                                thread.start()
                    prev_center = center

            # Processing indicator
            if processing:
                draw_text_with_background(overlay, "Analyzing... 🎶", (w - 270, 50),
                                          font_scale=1.0, thickness=2, bg_color=(0, 128, 255))

            # Show AI feedback (with readable overlay and larger text)
            if last_feedback and (time.time() - last_feedback_time) < TEXT_DISPLAY_TIME:
                draw_text_with_background(overlay, last_feedback, (50, h - 60),
                                          font_scale=1.0, thickness=2, bg_color=(30, 30, 30))

            cv2.imshow("Ukulele AI Tutor", overlay)

            key = cv2.waitKey(1) & 0xFF
            if key == 27 or key == ord('q') or key == ord('Q'):  # ESC or Q or q
                print("Exiting...")
                break
            elif key == ord(' '):  # Spacebar also toggles
                analysis_enabled = not analysis_enabled
                print(f"Analysis {'enabled' if analysis_enabled else 'disabled'}")

    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()