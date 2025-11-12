# guitar_video_analyser_prod

import tkinter as tk
from tkinter import filedialog, messagebox
from tkinter import ttk
import threading
import google.generativeai as genai
import json
import re
import cv2
import numpy as np
from pathlib import Path
import os

# ----------------------------
# GOOGLE GEMINI SETUP
# ----------------------------
genai.configure(api_key="AIzaSyDWkTV9jzPXj0AmKrKhG5hFf9vMw5_zWeY")  # <--- replace this
model = genai.GenerativeModel("gemini-2.5-flash")

# ----------------------------
# COMPREHENSIVE PROMPT
# ----------------------------
prompt_input = """
You are a guitar chord recognition system analyzing video frames. Your task is to identify chord changes from a LIMITED SET of common chords by analyzing finger positions.

TARGET CHORDS (these are the ONLY chords you should identify):
- Em (E minor)
- C (C major)
- G (G major)
- D (D major)
- F# (F# major) or F#m (F# minor)
- A (A major)
- Am (A minor)
- F (F major)

RECOGNITION STRATEGY:
1. Carefully observe the finger positions on the fretboard
2. Identify which strings are pressed and at which frets
3. Match the observed pattern to the CLOSEST chord from the target list above
4. If the pattern doesn't closely match ANY of these chords, mark as "Unknown" with low confidence

REFERENCE PATTERNS (standard positions):
- Em: strings [0, 0, 0, 2, 2, 0] (no fingers needed, or 2nd fret on A and D strings)
- C: strings [0, 1, 0, 2, 3, -1] (don't play low E)
- G: strings [3, 0, 0, 0, 2, 3] (or variations like [3, 3, 0, 0, 2, 3])
- D: strings [2, 3, 2, 0, -1, -1] (don't play A and low E strings)
- F#: strings [2, 2, 3, 4, 4, 2] (barre chord, or simpler versions)
- A: strings [0, 2, 2, 2, 0, -1] (don't play low E)
- Am: strings [0, 1, 2, 2, 0, -1] (don't play low E)
- F: strings [1, 1, 2, 3, 3, 1] (barre chord) or [1, 1, 2, 3, -1, -1] (simplified)

VISUAL ANALYSIS INSTRUCTIONS:
1. Examine each string from the nut (headstock) toward the bridge
2. A string is PRESSED only if you clearly see a fingertip pushing it down behind a fret wire
3. Count frets carefully starting from the nut (fret 1 is closest to nut)
4. If unclear, use the overall hand shape to match to the closest common chord
5. Open strings (0) have no fingers touching them in the playing area
6. Muted strings (-1) are either not strummed or deliberately dampened

MATCHING LOGIC:
- Compare your observed finger placement to the reference patterns above
- Find the BEST MATCH from the 8 target chords
- Small variations (1 fret off, one string different) are acceptable - choose the closest match
- If the pattern is drastically different from all 8 chords, mark as "Unknown"

CHORD EVENT DEFINITION:
- NEW event = visible change in finger position creating a different chord shape
- SAME event = fingers remain in same position (even during strumming/arpeggiation)
- Only increment chord_number when you see a clear transition to a DIFFERENT chord shape

OUTPUT SCHEMA:
{
  "chord_number": integer (starts at 1, increments for each new shape),
  "timestamp_start": "hh:mm:ss.sss",
  "timestamp_end": "hh:mm:ss.sss",
  "finger_placement": {
    "string_1": integer (high E: 0=open, -1=muted, 1-5=fret),
    "string_2": integer (B string),
    "string_3": integer (G string),
    "string_4": integer (D string),
    "string_5": integer (A string),
    "string_6": integer (low E)
  },
  "predicted_chord": "chord name" (MUST be one of: Em, C, G, D, F#, A, Am, F, or "Unknown"),
  "confidence": float 0.0-1.0,
  "notes": "string (OPTIONAL: explain matching reasoning if confidence < 0.8)"
}

CONFIDENCE SCORING:
- 0.9-1.0: Pattern clearly matches a target chord, all fingers visible
- 0.7-0.9: Pattern closely matches, minor variations or slight obscuration
- 0.5-0.7: Pattern approximately matches, some uncertainty in finger positions
- <0.5: Poor visibility OR pattern doesn't match any of the 8 target chords well

FORMAT: Return valid JSON array only. No markdown, no text outside JSON.

EXAMPLE:
[
  {
    "chord_number": 1,
    "timestamp_start": "00:00:01.200",
    "timestamp_end": "00:00:04.500",
    "finger_placement": {
      "string_1": 3,
      "string_2": 0,
      "string_3": 0,
      "string_4": 0,
      "string_5": 2,
      "string_6": 3
    },
    "predicted_chord": "G",
    "confidence": 0.95,
    "notes": "Clear G major shape"
  },
  {
    "chord_number": 2,
    "timestamp_start": "00:00:04.500",
    "timestamp_end": "00:00:07.100",
    "finger_placement": {
      "string_1": 0,
      "string_2": 0,
      "string_3": 0,
      "string_4": 2,
      "string_5": 2,
      "string_6": 0
    },
    "predicted_chord": "Em",
    "confidence": 0.92,
    "notes": "Standard Em shape, strings 4 and 5 at fret 2"
  },
  {
    "chord_number": 3,
    "timestamp_start": "00:00:07.100",
    "timestamp_end": "00:00:09.800",
    "finger_placement": {
      "string_1": 0,
      "string_2": 1,
      "string_3": 0,
      "string_4": 2,
      "string_5": 3,
      "string_6": -1
    },
    "predicted_chord": "C",
    "confidence": 0.93,
    "notes": "Standard C major, low E string muted"
  }
]

CRITICAL: Always choose the CLOSEST match from the 8 target chords. Do not identify chords outside this list unless the pattern is completely unrecognizable.
"""


# ----------------------------
# HELPER FUNCTIONS
# ----------------------------
def extract_and_save_json(llm_output, output_filename):
    pattern = r'```json\s*(.*?)\s*```'
    match = re.search(pattern, llm_output, re.DOTALL | re.IGNORECASE)
    if not match:
        # Try without code block markers
        try:
            json_data = json.loads(llm_output.strip())
            with open(output_filename, 'w', encoding='utf-8') as f:
                json.dump(json_data, f, indent=2, ensure_ascii=False)
            print(f"JSON successfully extracted and saved to {output_filename}")
            return json_data
        except:
            print("No JSON code block found in the input")
            return None

    json_string = match.group(1).strip()
    try:
        json_data = json.loads(json_string)
        with open(output_filename, 'w', encoding='utf-8') as f:
            json.dump(json_data, f, indent=2, ensure_ascii=False)
        print(f"JSON successfully extracted and saved to {output_filename}")
        return json_data
    except json.JSONDecodeError as e:
        print(f"Error parsing JSON: {e}")
        return None
    except IOError as e:
        print(f"Error saving file: {e}")
        return None


def parse_timestamp(ts_str):
    h, m, s = ts_str.split(':')
    seconds = float(s)
    total_ms = (int(h) * 3600 + int(m) * 60 + seconds) * 1000
    return total_ms


def wrap_text(text, font, font_scale, thickness, max_width):
    words = text.split(' ')
    lines, current_line = [], []
    for word in words:
        test_line = ' '.join(current_line + [word])
        (text_width, _), _ = cv2.getTextSize(test_line, font, font_scale, thickness)
        if text_width <= max_width:
            current_line.append(word)
        else:
            if current_line:
                lines.append(' '.join(current_line))
            current_line = [word]
    if current_line:
        lines.append(' '.join(current_line))
    return lines


def draw_banner(frame, text, y_position, height, padding=20):
    frame_height, frame_width = frame.shape[:2]
    overlay = frame.copy()
    cv2.rectangle(overlay, (0, y_position), (frame_width, y_position + height), (0, 0, 0), -1)
    cv2.addWeighted(overlay, 0.7, frame, 0.3, 0, frame)
    font = cv2.FONT_HERSHEY_SIMPLEX
    font_scale = 0.6
    thickness = 1
    color = (255, 255, 255)
    lines = wrap_text(text, font, font_scale, thickness, frame_width - 2 * padding)
    line_height = 25
    y_offset = y_position + padding + 20
    for line in lines:
        cv2.putText(frame, line, (padding, y_offset), font, font_scale, color, thickness, cv2.LINE_AA)
        y_offset += line_height
    return frame


def overlay_chord_image(frame, chord_name, chord_img_folder):
    chord_filename = f"{chord_name}.png"
    chord_path = Path(chord_img_folder) / chord_filename
    if not chord_path.exists():
        return frame
    chord_img = cv2.imread(str(chord_path), cv2.IMREAD_UNCHANGED)
    if chord_img is None:
        return frame
    CHORD_IMG_X, CHORD_IMG_Y = 225, 25
    CHORD_IMG_WIDTH, CHORD_IMG_HEIGHT = 200, 250
    chord_img = cv2.resize(chord_img, (CHORD_IMG_WIDTH, CHORD_IMG_HEIGHT))
    h, w = chord_img.shape[:2]

    # Ensure position is within bounds
    if CHORD_IMG_Y + h > frame.shape[0] or CHORD_IMG_X + w > frame.shape[1]:
        return frame

    if chord_img.shape[2] == 4:
        bgr = chord_img[:, :, :3]
        alpha = chord_img[:, :, 3] / 255.0
        roi = frame[CHORD_IMG_Y:CHORD_IMG_Y + h, CHORD_IMG_X:CHORD_IMG_X + w]
        for c in range(3):
            roi[:, :, c] = (alpha * bgr[:, :, c] + (1 - alpha) * roi[:, :, c])
        frame[CHORD_IMG_Y:CHORD_IMG_Y + h, CHORD_IMG_X:CHORD_IMG_X + w] = roi
    else:
        frame[CHORD_IMG_Y:CHORD_IMG_Y + h, CHORD_IMG_X:CHORD_IMG_X + w] = chord_img
    return frame


def draw_chord_overlay(video_path, json_path, output_path, chord_img_folder='./guitar_chord_bank'):
    """Draw chord information on video WITHOUT bounding boxes"""
    with open(json_path, 'r') as f:
        chord_data = json.load(f)

    for chord in chord_data:
        chord['start_ms'] = parse_timestamp(chord['timestamp_start'])
        chord['end_ms'] = parse_timestamp(chord['timestamp_end'])

    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        print(f"Error: Could not open video file: {video_path}")
        return None

    fps = cap.get(cv2.CAP_PROP_FPS)
    width, height = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)), int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

    print(f"Video: {width}x{height} @ {fps} fps, {total_frames} frames")

    out = cv2.VideoWriter(output_path, cv2.VideoWriter_fourcc(*'mp4v'), fps, (width, height))
    frame_count = 0

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        current_time_ms = (frame_count / fps) * 1000
        current_chord = None

        for chord in chord_data:
            if chord['start_ms'] <= current_time_ms < chord['end_ms']:
                current_chord = chord
                break

        if current_chord:
            chord_name = current_chord['predicted_chord']

            # Draw banner with notes at bottom
            notes = current_chord.get('notes', '')
            if notes:
                draw_banner(frame, notes, height - 100, 100)

            # Overlay chord diagram image
            frame = overlay_chord_image(frame, chord_name, chord_img_folder)

        out.write(frame)
        frame_count += 1

        if frame_count % 30 == 0:
            progress = (frame_count / total_frames) * 100
            print(f"Processing: {progress:.1f}% ({frame_count}/{total_frames} frames)")

    cap.release()
    out.release()
    print(f"\nDone! Output saved to: {output_path}")
    return output_path


# ----------------------------
# TKINTER GUI
# ----------------------------
class GuitarApp:
    def __init__(self, root):
        self.root = root
        self.root.title("🎸 Guitar Chord Analyzer")
        self.root.geometry("520x300")
        self.root.resizable(False, False)

        ttk.Label(root, text="🎶 Guitar Chord Video Processor", font=("Arial", 16, "bold")).pack(pady=15)

        self.upload_btn = ttk.Button(root, text="Upload Video", command=self.upload_video)
        self.upload_btn.pack(pady=10)

        self.progress = ttk.Progressbar(root, orient="horizontal", length=400, mode="determinate")
        self.progress.pack(pady=10)

        self.status_label = ttk.Label(root, text="No video selected", font=("Arial", 10))
        self.status_label.pack(pady=10)

        self.download_btn = ttk.Button(root, text="Download Processed Video", command=self.download_video,
                                       state="disabled")
        self.download_btn.pack(pady=10)

        self.video_path = None
        self.output_path = None

    def upload_video(self):
        file_path = filedialog.askopenfilename(filetypes=[("Video files", "*.mp4 *.mov *.avi")])
        if not file_path:
            return
        self.video_path = file_path
        self.status_label.config(text=f"Selected: {os.path.basename(file_path)}")
        threading.Thread(target=self.process_video, daemon=True).start()

    def process_video(self):
        try:
            self.progress["value"] = 10
            self.status_label.config(text="Uploading video to Gemini...")
            self.root.update_idletasks()

            # Step 1: Upload video to Gemini
            try:
                video_file = genai.upload_file(self.video_path)
            except Exception as e:
                raise RuntimeError(f"Upload failed: {e}")

            self.progress["value"] = 20
            self.status_label.config(text="Waiting for video to be processed by Gemini...")
            self.root.update_idletasks()

            # Step 2: Wait for file to be ACTIVE
            import time
            max_wait = 300  # 5 minutes max
            wait_time = 0
            while video_file.state.name == "PROCESSING":
                time.sleep(2)
                wait_time += 2
                video_file = genai.get_file(video_file.name)
                self.status_label.config(text=f"Processing video... ({wait_time}s)")
                self.root.update_idletasks()

                if wait_time >= max_wait:
                    raise RuntimeError("Video processing timeout")

            if video_file.state.name != "ACTIVE":
                raise RuntimeError(f"Video file is in {video_file.state.name} state")

            self.progress["value"] = 40
            self.status_label.config(text="Analyzing video with Gemini (this may take a few minutes)...")
            self.root.update_idletasks()

            # Step 3: Use synchronous generation with detailed prompt
            try:
                response = model.generate_content([video_file, prompt_input])
            except Exception as e:
                raise RuntimeError(f"Gemini analysis failed: {e}")

            Path("guitar_temp").mkdir(exist_ok=True)
            json_path = "./guitar_temp/first.json"

            extract_and_save_json(response.text, json_path)
            self.progress["value"] = 60
            self.status_label.config(text="Generating overlay video...")
            self.root.update_idletasks()

            # Step 3: Render with OpenCV (NO BOUNDING BOXES)
            Path("guitar_output").mkdir(exist_ok=True)
            output_path = "./guitar_output/output_with_overlay.mp4"
            self.output_path = draw_chord_overlay(
                self.video_path, json_path, output_path, chord_img_folder="./guitar_chord_bank"
            )

            self.progress["value"] = 100
            self.status_label.config(text="✅ Processing complete!")
            self.download_btn["state"] = "normal"

        except Exception as e:
            messagebox.showerror("Error", f"An error occurred:\n{str(e)}")
            self.status_label.config(text="❌ Failed")
            self.progress["value"] = 0

    def download_video(self):
        if not self.output_path:
            return
        dest = filedialog.asksaveasfilename(defaultextension=".mp4", filetypes=[("MP4 files", "*.mp4")])
        if not dest:
            return
        try:
            import shutil
            shutil.copy(self.output_path, dest)
            messagebox.showinfo("Download", f"Saved processed video to:\n{dest}")
        except Exception as e:
            messagebox.showerror("Error", f"Could not save file:\n{str(e)}")


# ----------------------------
# ENTRY POINT
# ----------------------------
def launch_video_upload_mode():
    root = tk.Tk()
    app = GuitarApp(root)
    root.mainloop()


if __name__ == "__main__":
    launch_video_upload_mode()