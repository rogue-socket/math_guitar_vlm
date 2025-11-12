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
import time

# ----------------------------
# GOOGLE GEMINI SETUP
# ----------------------------
genai.configure(api_key="AIzaSyDWkTV9jzPXj0AmKrKhG5hFf9vMw5_zWeY")  # <--- replace this
model = genai.GenerativeModel("gemini-2.5-flash")

# ----------------------------
# STEP EXTRACTION PROMPT
# ----------------------------
prompt_step_extraction = """
You are a video-to-structure extractor. For each new mathematical step that appears in the frames, output a JSON object with the following exact schema and formatting rules:

Definition of a step:
- A step is a COMPLETE written mathematical expression or logical transformation (e.g., a full equation, factorization, or substitution).
- If a teacher writes an equation gradually (adding terms piece by piece), group all the terms into ONE step once the equation is complete.
- Only when the teacher starts a NEW logical step (e.g., moving from expansion to factorization, or from an equation to its solution) should you create a new step_number.
- Multiple steps may appear on the same line, but they must still be represented as separate JSON objects.

Output schema:
step_number: integer (starting at 1, incrementing by 1 for each new step)
timestamp_start: string, format hh:mm:ss.sss (e.g., 00:01:23.231) → the exact moment the first character of the step first appears
timestamp_end: string, format hh:mm:ss.sss (e.g., 00:01:24.431) → the exact moment up until the next step appears
bounding_box: array of 4 integers [x1, y1, x2, y2], pixel coordinates of the frame, where (x1,y1) = top-left of the step's text, (x2,y2) = bottom-right of the step's text
written_text: string containing the detected mathematical expression, with all symbols preserved (LaTeX if needed)

Formatting requirements:
- Always output a valid JSON array of objects (no trailing commas, no comments, no text outside JSON).
- All timestamps must include hours, minutes, seconds, and milliseconds (zero-padded).
- All bounding box values must be integers (no floats).
- If multiple steps are written on the same line, they must still be output as SEPARATE JSON objects.

Example output:
[
  {
    "step_number": 1,
    "timestamp_start": "00:00:12.500",
    "timestamp_end": "00:00:15.200",
    "bounding_box": [120, 250, 480, 320],
    "written_text": "x^2 + 3x + x + 3 = 0"
  },
  {
    "step_number": 2,
    "timestamp_start": "00:00:16.000",
    "timestamp_end": "00:00:18.200",
    "bounding_box": [160, 440, 580, 500],
    "written_text": "x(x+3) + 1(x+3) = 0"
  }
]
"""


# ----------------------------
# HELPER FUNCTIONS
# ----------------------------
def extract_and_save_json(llm_output, output_filename):
    """Extract JSON from LLM output (with or without markdown code blocks)"""
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


def create_analysis_prompt(input_steps):
    """Create prompt for analyzing mathematical correctness"""
    step_desc = []
    for s in input_steps:
        step_desc.append(f"Step {s['step_number']} "
                         f"[{s['timestamp_start']} - {s['timestamp_end']}]: "
                         f"{s['written_text']}")

    prompt = f"""
You are a mathematics professor analyzing a student's work specialising in pointing out mathematical mistakes.

Here are the extracted steps from the video:
{chr(10).join(step_desc)}

Task:
- For each step, decide if it is correct or incorrect based on your judgement of the solving procedure.
- Include a short description for comment
- Provide a bottom_comment as commentary on that step.

Return JSON strictly in the following format:
{{
  "analysis": [
    {{
      "step_number": <int>,
      "timestamp_start": "<hh:mm:ss.sss>",
      "timestamp_end": "<hh:mm:ss.sss>",
      "correctness": "right or wrong",
      "comment": "<short inline comment>",
      "bottom_comment": "<general commentary>"
    }}
  ]
}}

sample output:
{{
  "analysis": [
    {{
      "step_number": 3,
      "timestamp_start": "00:08:21.134",
      "timestamp_end": "00:08:25.154",
      "correctness": "right",
      "comment": "factoring is accurately done.",
      "bottom_comment": "The initial quadratic equation is stated correctly, ready for solving."
    }}
  ]
}}
"""
    return prompt


def parse_timestamp(timestamp):
    """Convert timestamp (e.g., "00:00:07.700") to seconds"""
    parts = timestamp.split(':')
    hours = int(parts[0])
    minutes = int(parts[1])
    seconds = float(parts[2])
    return hours * 3600 + minutes * 60 + seconds


def timestamp_to_frame(timestamp, fps):
    """Convert timestamp to frame number"""
    seconds = parse_timestamp(timestamp)
    return int(seconds * fps)


def wrap_text(text, font, scale, thickness, max_width):
    """Wrap text to fit within max_width pixels"""
    words = text.split()
    lines = []
    current_line = []

    for word in words:
        test_line = ' '.join(current_line + [word])
        text_size = cv2.getTextSize(test_line, font, scale, thickness)[0]

        if text_size[0] <= max_width:
            current_line.append(word)
        else:
            if current_line:
                lines.append(' '.join(current_line))
            current_line = [word]

    if current_line:
        lines.append(' '.join(current_line))

    return lines


def draw_overlay_box(frame, position, text, frame_width, frame_height):
    """Draw overlay text near the specified step position"""
    x1, y1, x2, y2 = position
    x1 = int(x1 * 1.7)
    y1 = int(y1 * 1.7)
    x2 = int(x2 * 1.7)
    y2 = int(y2 * 1.7)

    # Calculate the center point of the step
    step_center_x = (x1 + x2) // 2
    step_center_y = (y1 + y2) // 2

    # Determine if this is a "right" or "wrong" comment
    is_correct = text.strip().lower().startswith('right')

    # Set colors based on correctness
    if is_correct:
        bg_color = (0, 200, 0)  # Green background
        text_color = (255, 255, 255)  # White text
        border_color = (0, 150, 0)  # Darker green border
    else:
        bg_color = (0, 0, 200)  # Red background
        text_color = (255, 255, 255)  # White text
        border_color = (0, 0, 150)  # Darker red border

    # Prepare text (remove "right" or "wrong" prefix)
    display_text = text.strip()
    if display_text.lower().startswith('right '):
        display_text = display_text[6:]
    elif display_text.lower().startswith('wrong '):
        display_text = display_text[6:]

    # Text properties
    font = cv2.FONT_HERSHEY_SIMPLEX
    scale = 0.6
    thickness = 2

    # Calculate overlay box dimensions
    max_text_width = min(300, frame_width // 3)
    wrapped_lines = wrap_text(display_text, font, scale, thickness, max_text_width - 20)

    line_height = 25
    padding = 15
    if wrapped_lines:
        max_line_width = max([cv2.getTextSize(line, font, scale, thickness)[0][0] for line in wrapped_lines])
        box_width = min(max_text_width, max_line_width + 2 * padding)
    else:
        box_width = max_text_width
    box_height = len(wrapped_lines) * line_height + 2 * padding

    # Determine overlay position
    overlay_x = x2 + 20
    overlay_y = step_center_y - box_height // 2

    if overlay_x + box_width > frame_width:
        overlay_x = max(0, x1 - box_width - 20)
    if overlay_x < 0:
        overlay_x = max(0, min(step_center_x - box_width // 2, frame_width - box_width))
        if step_center_y > frame_height // 2:
            overlay_y = max(0, y1 - box_height - 20)
        else:
            overlay_y = min(frame_height - box_height, y2 + 20)

    overlay_x = max(0, min(overlay_x, frame_width - box_width))
    overlay_y = max(0, min(overlay_y, frame_height - box_height))

    # Draw semi-transparent background
    overlay_img = frame.copy()
    cv2.rectangle(overlay_img, (overlay_x, overlay_y),
                  (overlay_x + box_width, overlay_y + box_height),
                  bg_color, -1)
    cv2.addWeighted(overlay_img, 0.85, frame, 0.15, 0, frame)

    # Draw border
    cv2.rectangle(frame, (overlay_x, overlay_y),
                  (overlay_x + box_width, overlay_y + box_height),
                  border_color, 2)

    # Pointer line
    overlay_center_x = overlay_x + box_width // 2
    overlay_center_y = overlay_y + box_height // 2
    if step_center_x < overlay_x:
        line_start = (overlay_x, overlay_center_y)
    elif step_center_x > overlay_x + box_width:
        line_start = (overlay_x + box_width, overlay_center_y)
    elif step_center_y < overlay_y:
        line_start = (overlay_center_x, overlay_y)
    else:
        line_start = (overlay_center_x, overlay_y + box_height)
    cv2.line(frame, line_start, (step_center_x, step_center_y), border_color, 2)

    # Step marker
    cv2.circle(frame, (step_center_x, step_center_y), 5, border_color, -1)
    cv2.circle(frame, (step_center_x, step_center_y), 5, (255, 255, 255), 1)

    # Draw text
    for i, line in enumerate(wrapped_lines):
        text_x = overlay_x + padding
        text_y = overlay_y + padding + (i + 1) * line_height
        cv2.putText(frame, line, (text_x, text_y), font, scale, text_color, thickness, cv2.LINE_AA)


def draw_bottom_comment(frame, text, frame_width, frame_height):
    """Draw bottom comment at the bottom of the video"""
    font = cv2.FONT_HERSHEY_SIMPLEX
    scale = 0.8
    thickness = 2
    text_color = (255, 255, 255)
    bg_color = (0, 0, 0)

    comment_height = 120
    comment_y_start = frame_height - comment_height

    # Draw semi-transparent background
    overlay = frame.copy()
    cv2.rectangle(overlay, (0, comment_y_start), (frame_width, frame_height), bg_color, -1)
    cv2.addWeighted(overlay, 0.8, frame, 0.2, 0, frame)

    # Draw border line
    cv2.line(frame, (0, comment_y_start), (frame_width, comment_y_start), (100, 100, 100), 2)

    # Wrap and draw text
    max_width = int(frame_width * 0.9)
    wrapped_lines = wrap_text(text, font, scale, thickness, max_width)

    line_height = 30
    total_text_height = len(wrapped_lines) * line_height
    start_y = comment_y_start + (comment_height - total_text_height) // 2 + 25

    for i, line in enumerate(wrapped_lines):
        text_size = cv2.getTextSize(line, font, scale, thickness)[0]
        text_x = (frame_width - text_size[0]) // 2
        text_y = start_y + (i * line_height)

        cv2.putText(frame, line, (text_x, text_y), font, scale, (0, 0, 0), thickness + 2, cv2.LINE_AA)
        cv2.putText(frame, line, (text_x, text_y), font, scale, text_color, thickness, cv2.LINE_AA)


def process_video_with_overlays(video_path, overlay_json_path, output_path):
    """Process video and add overlays"""
    with open(overlay_json_path, 'r') as f:
        overlay_data = json.load(f)

    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        print(f"Error: Could not open video file: {video_path}")
        return None

    fps = int(cap.get(cv2.CAP_PROP_FPS))
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

    print(f"Video: {width}x{height} @ {fps} fps, {total_frames} frames")

    out = cv2.VideoWriter(output_path, cv2.VideoWriter_fourcc(*'mp4v'), fps, (width, height))

    # Convert timestamps to frame numbers
    overlays_with_frames = []
    for overlay in overlay_data['overlays']:
        start_frame = timestamp_to_frame(overlay['timestamp_start'], fps)
        end_frame = timestamp_to_frame(overlay['timestamp_end'], fps)
        overlays_with_frames.append({
            'start_frame': start_frame,
            'end_frame': end_frame,
            'position': overlay['position'],
            'text': overlay['overlay_text']
        })

    bottom_comments_with_frames = []
    for comment in overlay_data['bottom_comments']:
        start_frame = timestamp_to_frame(comment['timestamp_start'], fps)
        end_frame = timestamp_to_frame(comment['timestamp_end'], fps)
        bottom_comments_with_frames.append({
            'start_frame': start_frame,
            'end_frame': end_frame,
            'text': comment['overlay_text']
        })

    frame_count = 0

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        frame_count += 1

        # Add overlays
        for overlay in overlays_with_frames:
            if overlay['start_frame'] <= frame_count <= overlay['end_frame']:
                draw_overlay_box(frame, overlay['position'], overlay['text'], width, height)

        # Add bottom comments
        for comment in bottom_comments_with_frames:
            if comment['start_frame'] <= frame_count <= comment['end_frame']:
                draw_bottom_comment(frame, comment['text'], width, height)

        out.write(frame)

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
class MathAnalyzerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("📐 Math Equation Analyzer")
        self.root.geometry("520x300")
        self.root.resizable(False, False)

        ttk.Label(root, text="📝 Math Video Processor", font=("Arial", 16, "bold")).pack(pady=15)

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
            self.progress["value"] = 5
            self.status_label.config(text="Uploading video to Gemini...")
            self.root.update_idletasks()

            # Step 1: Upload video
            try:
                video_file = genai.upload_file(self.video_path)
            except Exception as e:
                raise RuntimeError(f"Upload failed: {e}")

            self.progress["value"] = 15
            self.status_label.config(text="Waiting for video processing...")
            self.root.update_idletasks()

            # Step 2: Wait for ACTIVE state
            max_wait = 300
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

            self.progress["value"] = 30
            self.status_label.config(text="Extracting mathematical steps...")
            self.root.update_idletasks()

            # Step 3: Extract steps
            try:
                response = model.generate_content([video_file, prompt_step_extraction])
            except Exception as e:
                raise RuntimeError(f"Step extraction failed: {e}")

            Path("math_temp").mkdir(exist_ok=True)
            input_json_path = "./math_temp/input.json"
            extract_and_save_json(response.text, input_json_path)

            self.progress["value"] = 50
            self.status_label.config(text="Analyzing mathematical correctness...")
            self.root.update_idletasks()

            # Step 4: Analyze correctness
            with open(input_json_path, "r") as f:
                input_steps = json.load(f)

            analysis_prompt = create_analysis_prompt(input_steps)

            try:
                response = model.generate_content([video_file, analysis_prompt])
            except Exception as e:
                raise RuntimeError(f"Analysis failed: {e}")

            analysis_json_path = "./math_temp/analysis.json"
            extract_and_save_json(response.text, analysis_json_path)

            self.progress["value"] = 65
            self.status_label.config(text="Creating overlay data...")
            self.root.update_idletasks()

            # Step 5: Create overlay JSON
            with open(analysis_json_path, "r", encoding="utf-8") as f:
                analysis_data = json.load(f)["analysis"]

            analysis_map = {a["step_number"]: a for a in analysis_data}

            overlays = []
            bottom_comments = []

            for step in input_steps:
                step_number = step["step_number"]
                if step_number not in analysis_map:
                    continue

                analysis = analysis_map[step_number]

                overlays.append({
                    "timestamp_start": step["timestamp_start"],
                    "timestamp_end": step["timestamp_end"],
                    "position": step["bounding_box"],
                    "overlay_text": f"{analysis['correctness']} {analysis['comment']}"
                })

                bottom_comments.append({
                    "timestamp_start": step["timestamp_start"],
                    "timestamp_end": step["timestamp_end"],
                    "overlay_text": analysis["bottom_comment"]
                })

            overlay_json = {
                "overlays": overlays,
                "bottom_comments": bottom_comments
            }

            overlay_json_path = "./math_temp/overlay.json"
            with open(overlay_json_path, "w", encoding="utf-8") as f:
                json.dump(overlay_json, f, indent=2, ensure_ascii=False)

            self.progress["value"] = 75
            self.status_label.config(text="Generating overlay video...")
            self.root.update_idletasks()

            # Step 6: Process video with overlays
            Path("math_output").mkdir(exist_ok=True)
            output_path = "./math_output/output_with_overlays.mp4"
            self.output_path = process_video_with_overlays(
                self.video_path, overlay_json_path, output_path
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
    app = MathAnalyzerApp(root)
    root.mainloop()


if __name__ == "__main__":
    launch_video_upload_mode()