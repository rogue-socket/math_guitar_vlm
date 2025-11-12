# # import tkinter as tk
# # from tkinter import messagebox
# # import cv2
# # import numpy as np
# # from PIL import Image, ImageDraw
# # import threading
# # import time
# # import os
# # import json
# # from datetime import datetime
# # import google.generativeai as genai
# # import io
# # import logging
# # import uuid
# #
# # logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
# # logger = logging.getLogger(__name__)
# #
# # API_KEY = "AIzaSyDWkTV9jzPXj0AmKrKhG5hFf9vMw5_zWeY"
# # if not API_KEY:
# #     raise ValueError("GEMINI_API_KEY environment variable not set!")
# #
# # genai.configure(api_key=API_KEY)
# #
# # class SmartWhiteboardVLMDual:
# #     def __init__(self, root):
# #         self.root = root
# #         self.root.title("Smart Whiteboard with Gemini VLM - Dual Canvas")
# #         self.root.geometry("1600x800")
# #
# #         self.virtual_canvas_width = 5000
# #         self.virtual_canvas_height = 5000
# #         self.initial_pil_width = 2000
# #         self.initial_pil_height = 2000
# #
# #         self.question_canvas_width = 700
# #         self.question_canvas_height = 600
# #         self.drawing = False
# #         self.last_x = 0
# #         self.last_y = 0
# #         self.brush_size = 3
# #         self.eraser_size = 15
# #
# #         self.question_strokes = []
# #         self.solution_strokes = []
# #         self.current_stroke = []
# #         self.current_stroke_canvas = None
# #
# #         self.question_pil_image = Image.new("RGB", (self.question_canvas_width, self.question_canvas_height), "white")
# #         self.question_pil_draw = ImageDraw.Draw(self.question_pil_image)
# #
# #         self.solution_pil_image = Image.new("RGB", (self.initial_pil_width, self.initial_pil_height), "white")
# #         self.solution_pil_draw = ImageDraw.Draw(self.solution_pil_image)
# #
# #         self.panning = False
# #         self.pan_start_x = 0
# #         self.pan_start_y = 0
# #
# #         self.prev_frame = None
# #         self.writing_stopped_time = time.time()
# #         self.is_writing = False
# #         self.stop_writing_threshold = 1.5
# #         self.frame_diff_threshold = 1000
# #         self.frame_capture_interval = 0.1
# #
# #         self.vlm_processing = False
# #         self.pending_vlm_response = None
# #         self.last_stroke_bbox = None
# #         self.overlay_canvas_id = None
# #         self.lowest_y = 0
# #
# #         self.question_locked = False
# #         self.question_image_path = None
# #         self.solution_image_path = None
# #         self.solution_image_path = None
# #
# #         self.feedback_log_file = "vlm_feedback.jsonl"
# #
# #         self.monitor_thread = None
# #         self.stop_monitor = False
# #
# #         self.setup_ui()
# #         self.start_monitoring()
# #
# #     def setup_ui(self):
# #         main_container = tk.Frame(self.root)
# #         main_container.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=10, pady=10)
# #
# #         left_section = tk.Frame(main_container)
# #         left_section.pack(side=tk.LEFT, fill=tk.BOTH, expand=False, padx=5)
# #
# #         question_label = tk.Label(left_section, text="Question", font=("Arial", 12, "bold"))
# #         question_label.pack()
# #
# #         question_info = tk.Label(left_section, text="Write the problem here", font=("Arial", 8), fg="#666666")
# #         question_info.pack()
# #
# #         self.question_canvas = tk.Canvas(
# #             left_section,
# #             width=self.question_canvas_width,
# #             height=self.question_canvas_height,
# #             bg="white",
# #             cursor="cross",
# #             highlightthickness=1,
# #             highlightbackground="#cccccc"
# #         )
# #         self.question_canvas.pack(pady=5)
# #
# #         self.question_canvas.bind("<Button-1>", self.start_draw_question)
# #         self.question_canvas.bind("<B1-Motion>", self.draw_question)
# #         self.question_canvas.bind("<ButtonRelease-1>", self.stop_draw_question)
# #         self.question_canvas.bind("<Button-3>", self.start_erase_question)
# #         self.question_canvas.bind("<B3-Motion>", self.erase_question)
# #         self.question_canvas.bind("<ButtonRelease-3>", self.stop_erase_question)
# #
# #         right_section = tk.Frame(main_container)
# #         right_section.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5)
# #
# #         solution_label = tk.Label(right_section, text="Solution", font=("Arial", 12, "bold"))
# #         solution_label.pack()
# #
# #         solution_info = tk.Label(right_section, text="Scroll (Mouse Wheel) • Pan (Middle Click + Drag)", font=("Arial", 8), fg="#666666")
# #         solution_info.pack()
# #
# #         canvas_frame = tk.Frame(right_section)
# #         canvas_frame.pack(fill=tk.BOTH, expand=True, pady=5)
# #
# #         v_scrollbar = tk.Scrollbar(canvas_frame, orient=tk.VERTICAL)
# #         v_scrollbar.grid(row=0, column=1, sticky="ns")
# #
# #         h_scrollbar = tk.Scrollbar(canvas_frame, orient=tk.HORIZONTAL)
# #         h_scrollbar.grid(row=1, column=0, sticky="ew")
# #
# #         self.solution_canvas = tk.Canvas(
# #             canvas_frame,
# #             bg="white",
# #             cursor="cross",
# #             scrollregion=(0, 0, self.virtual_canvas_width, self.virtual_canvas_height),
# #             yscrollcommand=v_scrollbar.set,
# #             xscrollcommand=h_scrollbar.set,
# #             highlightthickness=1,
# #             highlightbackground="#cccccc"
# #         )
# #         self.solution_canvas.grid(row=0, column=0, sticky="nsew")
# #
# #         v_scrollbar.config(command=self.solution_canvas.yview)
# #         h_scrollbar.config(command=self.solution_canvas.xview)
# #
# #         canvas_frame.rowconfigure(0, weight=1)
# #         canvas_frame.columnconfigure(0, weight=1)
# #
# #         self.solution_canvas.bind("<Button-1>", self.start_draw_solution)
# #         self.solution_canvas.bind("<B1-Motion>", self.draw_solution)
# #         self.solution_canvas.bind("<ButtonRelease-1>", self.stop_draw_solution)
# #         self.solution_canvas.bind("<Button-3>", self.start_erase_solution)
# #         self.solution_canvas.bind("<B3-Motion>", self.erase_solution)
# #         self.solution_canvas.bind("<ButtonRelease-3>", self.stop_erase_solution)
# #         self.solution_canvas.bind("<Button-2>", self.start_pan)
# #         self.solution_canvas.bind("<B2-Motion>", self.do_pan)
# #         self.solution_canvas.bind("<MouseWheel>", self.on_mousewheel)
# #         self.solution_canvas.bind("<Button-4>", self.on_mousewheel)
# #         self.solution_canvas.bind("<Button-5>", self.on_mousewheel)
# #
# #         solution_button_frame = tk.Frame(right_section)
# #         solution_button_frame.pack(pady=5)
# #
# #         self.clear_solution_btn = tk.Button(solution_button_frame, text="Clear Solution", command=self.clear_solution, bg="#FFA500", fg="white", width=18)
# #         self.clear_solution_btn.pack(side=tk.TOP, padx=5, pady=3)
# #
# #         button_frame = tk.Frame(left_section)
# #         button_frame.pack(pady=10)
# #
# #         self.start_solution_btn = tk.Button(button_frame, text="Start Solution", command=self.start_solution, bg="#4CAF50", fg="white", width=18)
# #         self.start_solution_btn.pack(side=tk.TOP, padx=5, pady=3)
# #
# #         self.clear_btn = tk.Button(button_frame, text="Reset", command=self.reset_canvases, bg="#FF6B6B", fg="white", width=18)
# #         self.clear_btn.pack(side=tk.TOP, padx=5, pady=3)
# #
# #         self.exit_btn = tk.Button(button_frame, text="Exit", command=self.root.quit, bg="#808080", fg="white", width=18)
# #         self.exit_btn.pack(side=tk.TOP, padx=5, pady=3)
# #
# #         right_panel = tk.Frame(self.root, bg="#f0f0f0", width=300)
# #         right_panel.pack(side=tk.RIGHT, fill=tk.BOTH, padx=10, pady=10)
# #         right_panel.pack_propagate(False)
# #
# #         status_label = tk.Label(right_panel, text="Status", font=("Arial", 12, "bold"), bg="#f0f0f0")
# #         status_label.pack(pady=(10, 5))
# #
# #         self.status_display = tk.Label(
# #             right_panel,
# #             text="⚪ Waiting for user input…",
# #             font=("Arial", 11),
# #             bg="#f0f0f0",
# #             fg="#333333",
# #             wraplength=250,
# #             justify=tk.LEFT
# #         )
# #         self.status_display.pack(pady=5)
# #
# #         feedback_label = tk.Label(right_panel, text="VLM Feedback", font=("Arial", 12, "bold"), bg="#f0f0f0")
# #         feedback_label.pack(pady=(15, 5))
# #
# #         scrollbar = tk.Scrollbar(right_panel)
# #         scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
# #
# #         self.feedback_text = tk.Text(
# #             right_panel,
# #             height=25,
# #             width=35,
# #             font=("Courier", 9),
# #             yscrollcommand=scrollbar.set,
# #             bg="white",
# #             state=tk.DISABLED
# #         )
# #         self.feedback_text.pack(pady=5, fill=tk.BOTH, expand=True)
# #         scrollbar.config(command=self.feedback_text.yview)
# #
# #     def start_draw_question(self, event):
# #         if self.question_locked:
# #             return
# #         self.drawing = True
# #         self.current_stroke_canvas = "question"
# #         self.last_x = event.x
# #         self.last_y = event.y
# #         self.current_stroke = [(int(event.x), int(event.y))]
# #         self.update_status("🟢 Writing question…")
# #
# #     def draw_question(self, event):
# #         if not self.drawing or self.current_stroke_canvas != "question":
# #             return
# #
# #         self.question_canvas.create_line(
# #             self.last_x, self.last_y, event.x, event.y,
# #             fill="black", width=self.brush_size, capstyle=tk.ROUND, smooth=True
# #         )
# #
# #         self.question_pil_draw.line(
# #             [(self.last_x, self.last_y), (event.x, event.y)],
# #             fill="black",
# #             width=self.brush_size
# #         )
# #
# #         self.current_stroke.append((int(event.x), int(event.y)))
# #         self.last_x = event.x
# #         self.last_y = event.y
# #
# #     def stop_draw_question(self, event):
# #         if not self.drawing or self.current_stroke_canvas != "question":
# #             return
# #         self.drawing = False
# #         if self.current_stroke:
# #             self.question_strokes.append(self.current_stroke)
# #             self.current_stroke = []
# #         self.current_stroke_canvas = None
# #
# #     def start_erase_question(self, event):
# #         if self.question_locked:
# #             return
# #         self.drawing = True
# #         self.current_stroke_canvas = "question_erase"
# #         self.last_x = event.x
# #         self.last_y = event.y
# #         self.erase_question(event)
# #
# #     def erase_question(self, event):
# #         if not self.drawing or self.current_stroke_canvas != "question_erase":
# #             return
# #
# #         self.question_canvas.create_oval(
# #             event.x - self.eraser_size, event.y - self.eraser_size,
# #             event.x + self.eraser_size, event.y + self.eraser_size,
# #             fill="white", outline="white"
# #         )
# #         self.question_pil_draw.ellipse(
# #             [(event.x - self.eraser_size, event.y - self.eraser_size),
# #              (event.x + self.eraser_size, event.y + self.eraser_size)],
# #             fill="white"
# #         )
# #         self.last_x = event.x
# #         self.last_y = event.y
# #
# #     def stop_erase_question(self, event):
# #         if self.current_stroke_canvas == "question_erase":
# #             self.drawing = False
# #             self.current_stroke_canvas = None
# #
# #     def start_draw_solution(self, event):
# #         if not self.question_locked:
# #             self.update_status("⚠️  Click 'Start Solution' first!")
# #             return
# #         self.drawing = True
# #         self.current_stroke_canvas = "solution"
# #         x = self.solution_canvas.canvasx(event.x)
# #         y = self.solution_canvas.canvasy(event.y)
# #         self.last_x = x
# #         self.last_y = y
# #         self.current_stroke = [(int(x), int(y))]
# #         self.is_writing = True
# #         self.writing_stopped_time = time.time()
# #         self.update_status("🟢 Writing solution…")
# #         self.fade_out_overlay()
# #
# #     def draw_solution(self, event):
# #         if not self.drawing or self.current_stroke_canvas != "solution":
# #             return
# #
# #         x = self.solution_canvas.canvasx(event.x)
# #         y = self.solution_canvas.canvasy(event.y)
# #
# #         self.solution_canvas.create_line(
# #             self.last_x, self.last_y, x, y,
# #             fill="black", width=self.brush_size, capstyle=tk.ROUND, smooth=True
# #         )
# #
# #         self.solution_pil_draw.line(
# #             [(self.last_x, self.last_y), (x, y)],
# #             fill="black",
# #             width=self.brush_size
# #         )
# #
# #         self.current_stroke.append((int(x), int(y)))
# #         self.last_x = x
# #         self.last_y = y
# #         self.writing_stopped_time = time.time()
# #
# #     def stop_draw_solution(self, event):
# #         if not self.drawing or self.current_stroke_canvas != "solution":
# #             return
# #         self.drawing = False
# #         if self.current_stroke:
# #             self.solution_strokes.append(self.current_stroke)
# #             xs, ys = zip(*self.current_stroke)
# #             min_x, max_x = min(xs), max(xs)
# #             min_y, max_y = min(ys), max(ys)
# #             self.last_stroke_bbox = (min_x, min_y, max_x - min_x + 10, max_y - min_y + 10)
# #
# #             if max_y > self.lowest_y:
# #                 self.lowest_y = max_y
# #
# #             self.current_stroke = []
# #
# #         self.update_scroll_region()
# #         self.current_stroke_canvas = None
# #
# #     def start_erase_solution(self, event):
# #         if not self.question_locked:
# #             self.update_status("⚠️  Click 'Start Solution' first!")
# #             return
# #         self.drawing = True
# #         self.current_stroke_canvas = "solution_erase"
# #         x = self.solution_canvas.canvasx(event.x)
# #         y = self.solution_canvas.canvasy(event.y)
# #         self.last_x = x
# #         self.last_y = y
# #         self.erase_solution(event)
# #
# #     def erase_solution(self, event):
# #         if not self.drawing or self.current_stroke_canvas != "solution_erase":
# #             return
# #
# #         x = self.solution_canvas.canvasx(event.x)
# #         y = self.solution_canvas.canvasy(event.y)
# #
# #         self.solution_canvas.create_oval(
# #             x - self.eraser_size, y - self.eraser_size,
# #             x + self.eraser_size, y + self.eraser_size,
# #             fill="white", outline="white"
# #         )
# #         self.solution_pil_draw.ellipse(
# #             [(x - self.eraser_size, y - self.eraser_size),
# #              (x + self.eraser_size, y + self.eraser_size)],
# #             fill="white"
# #         )
# #         self.last_x = x
# #         self.last_y = y
# #
# #     def stop_erase_solution(self, event):
# #         if self.current_stroke_canvas == "solution_erase":
# #             self.drawing = False
# #             self.current_stroke_canvas = None
# #
# #     def start_solution(self):
# #         if not self.question_strokes:
# #             messagebox.showwarning("Warning", "Please write a question first!")
# #             return
# #
# #         self.question_locked = True
# #         self.snapshot_question()
# #         self.update_status("⚪ Question locked. Start solving…")
# #         self.start_solution_btn.config(state=tk.DISABLED)
# #         self.question_canvas.config(cursor="no")
# #
# #     def snapshot_question(self):
# #         try:
# #             self.question_image_path = f"question_{uuid.uuid4().hex[:8]}.png"
# #             self.question_pil_image.save(self.question_image_path)
# #             logger.info(f"Question snapshot saved: {self.question_image_path}")
# #         except Exception as e:
# #             logger.error(f"Failed to snapshot question: {e}")
# #             messagebox.showerror("Error", f"Failed to snapshot question: {e}")
# #
# #     def reset_canvases(self):
# #         self.solution_canvas.delete("all")
# #         self.question_canvas.delete("all")
# #
# #         self.question_pil_image = Image.new("RGB", (self.question_canvas_width, self.question_canvas_height), "white")
# #         self.question_pil_draw = ImageDraw.Draw(self.question_pil_image)
# #
# #         self.solution_pil_image = Image.new("RGB", (self.initial_pil_width, self.initial_pil_height), "white")
# #         self.solution_pil_draw = ImageDraw.Draw(self.solution_pil_image)
# #
# #         self.question_strokes = []
# #         self.solution_strokes = []
# #         self.current_stroke = []
# #
# #         self.question_locked = False
# #         if self.question_image_path and os.path.exists(self.question_image_path):
# #             os.remove(self.question_image_path)
# #         self.question_image_path = None
# #         self.solution_image_path = None
# #
# #         self.last_stroke_bbox = None
# #         self.lowest_y = 0
# #         self.prev_frame = None
# #         self.is_writing = False
# #
# #         self.start_solution_btn.config(state=tk.NORMAL)
# #         self.question_canvas.config(cursor="cross")
# #
# #         self.solution_canvas.config(scrollregion=(0, 0, self.virtual_canvas_width, self.virtual_canvas_height))
# #         self.update_status("⚪ Waiting for user input…")
# #         self.clear_feedback_display()
# #
# #     def clear_solution(self):
# #         self.solution_canvas.delete("all")
# #
# #         self.solution_pil_image = Image.new("RGB", (self.initial_pil_width, self.initial_pil_height), "white")
# #         self.solution_pil_draw = ImageDraw.Draw(self.solution_pil_image)
# #
# #         self.solution_strokes = []
# #         self.current_stroke = []
# #
# #         self.last_stroke_bbox = None
# #         self.lowest_y = 0
# #         self.prev_frame = None
# #         self.is_writing = False
# #
# #         self.solution_canvas.config(scrollregion=(0, 0, self.virtual_canvas_width, self.virtual_canvas_height))
# #         self.update_status("⚪ Solution cleared…")
# #         self.fade_out_overlay()
# #
# #     def on_mousewheel(self, event):
# #         if event.num == 5 or event.delta < 0:
# #             self.solution_canvas.yview_scroll(3, "units")
# #         elif event.num == 4 or event.delta > 0:
# #             self.solution_canvas.yview_scroll(-3, "units")
# #
# #     def start_pan(self, event):
# #         self.panning = True
# #         self.solution_canvas.scan_mark(event.x, event.y)
# #
# #     def do_pan(self, event):
# #         self.solution_canvas.scan_dragto(event.x, event.y, gain=1)
# #
# #     def update_scroll_region(self):
# #         bbox = self.solution_canvas.bbox("all")
# #         if bbox:
# #             x1, y1, x2, y2 = bbox
# #             x1, y1 = max(0, int(x1) - 100), max(0, int(y1) - 100)
# #             x2, y2 = int(x2) + 100, int(y2) + 100
# #
# #             x2 = max(x2, self.virtual_canvas_width)
# #             y2 = max(y2, self.virtual_canvas_height)
# #
# #             self.solution_canvas.config(scrollregion=(x1, y1, x2, y2))
# #         else:
# #             self.solution_canvas.config(scrollregion=(0, 0, self.virtual_canvas_width, self.virtual_canvas_height))
# #
# #     def update_status(self, status):
# #         self.status_display.config(text=status)
# #         self.root.update_idletasks()
# #
# #     def clear_feedback_display(self):
# #         self.feedback_text.config(state=tk.NORMAL)
# #         self.feedback_text.delete("1.0", tk.END)
# #         self.feedback_text.config(state=tk.DISABLED)
# #
# #     def add_feedback_to_display(self, feedback_text):
# #         self.feedback_text.config(state=tk.NORMAL)
# #         timestamp = datetime.now().strftime("%H:%M:%S")
# #         self.feedback_text.insert(tk.END, f"[{timestamp}]\n{feedback_text}\n\n")
# #         self.feedback_text.see(tk.END)
# #         self.feedback_text.config(state=tk.DISABLED)
# #
# #     def start_monitoring(self):
# #         self.monitor_thread = threading.Thread(target=self.monitor_writing, daemon=True)
# #         self.monitor_thread.start()
# #
# #     def monitor_writing(self):
# #         while not self.stop_monitor:
# #             time.sleep(self.frame_capture_interval)
# #
# #             if not self.is_writing:
# #                 continue
# #
# #             current_frame = self.pil_image_to_cv2(self.solution_pil_image)
# #
# #             if self.prev_frame is not None:
# #                 diff = cv2.absdiff(current_frame, self.prev_frame)
# #                 gray_diff = cv2.cvtColor(diff, cv2.COLOR_BGR2GRAY)
# #                 movement = np.sum(gray_diff > 20)
# #
# #                 if movement < self.frame_diff_threshold:
# #                     elapsed = time.time() - self.writing_stopped_time
# #                     if elapsed >= self.stop_writing_threshold and not self.vlm_processing:
# #                         self.is_writing = False
# #                         self.on_writing_stopped()
# #                 else:
# #                     self.writing_stopped_time = time.time()
# #             else:
# #                 self.writing_stopped_time = time.time()
# #
# #             self.prev_frame = current_frame.copy()
# #
# #     def pil_image_to_cv2(self, pil_img):
# #         return cv2.cvtColor(np.array(pil_img), cv2.COLOR_RGB2BGR)
# #
# #     def on_writing_stopped(self):
# #         logger.info("Writing stopped detected. Triggering VLM analysis...")
# #         self.update_status("🔵 Processing OCR…")
# #         self.vlm_processing = True
# #
# #         vlm_thread = threading.Thread(target=self.process_with_vlm, daemon=True)
# #         vlm_thread.start()
# #
# #     def capture_solution_canvas(self):
# #         logger.info("Using maintained PIL image for VLM processing")
# #         return self.solution_pil_image
# #
# #     def process_with_vlm(self):
# #         try:
# #             if not self.question_image_path:
# #                 logger.error("Question image not available!")
# #                 self.root.after(0, self.add_feedback_to_display, "Error: Question image missing")
# #                 self.vlm_processing = False
# #                 return
# #
# #             logger.info("Capturing solution canvas…")
# #             solution_image = self.capture_solution_canvas()
# #             logger.info(f"Solution captured: {solution_image.size}")
# #
# #             prompt = (
# #                 "You will receive two images. "
# #                 "The FIRST image is the QUESTION/PROBLEM. "
# #                 "The SECOND image is the SOLUTION/ANSWER written by the user. "
# #                 "Analyze whether the SOLUTION correctly solves the QUESTION. "
# #                 "Evaluate each step logically and mathematically — check signs, arithmetic, factorization, substitutions, and final answers. "
# #                 "If the solution appears INCOMPLETE but the steps so far are correct and consistent with the question, "
# #                 "respond that the intermediate steps are correct so far and more work is needed, "
# #                 "and set correctness to true. "
# #                 "Only mark correctness as false if there are genuine mistakes or inconsistencies. "
# #                 "Respond ONLY in strict JSON format as below — no markdown or extra text:\n"
# #                 "{\"feedback\": \"concise feedback under 100 words\", \"correctness\": true/false}"
# #             )
# #
# #             with open(self.question_image_path, "rb") as q_file:
# #                 question_data = q_file.read()
# #
# #             solution_data = io.BytesIO()
# #             solution_image.save(solution_data, format='PNG')
# #             solution_data = solution_data.getvalue()
# #
# #             model = genai.GenerativeModel("gemini-2.5-flash")
# #             response = model.generate_content(
# #                 [
# #                     prompt,
# #                     {"mime_type": "image/png", "data": question_data},
# #                     {"mime_type": "image/png", "data": solution_data}
# #                 ]
# #             )
# #
# #             feedback_text = response.text.strip()
# #
# #             try:
# #                 json_start = feedback_text.find("{")
# #                 json_end = feedback_text.rfind("}") + 1
# #                 if json_start != -1 and json_end > json_start:
# #                     feedback_json = json.loads(feedback_text[json_start:json_end])
# #                 else:
# #                     feedback_json = {"feedback": feedback_text, "correctness": None}
# #             except json.JSONDecodeError:
# #                 feedback_json = {"feedback": feedback_text, "correctness": None}
# #
# #             logger.info(f"VLM Response: {json.dumps(feedback_json, indent=2)}")
# #
# #             self.log_feedback(feedback_json)
# #
# #             self.root.after(0, self.display_vlm_feedback, feedback_json)
# #
# #         except Exception as e:
# #             logger.error(f"VLM processing error: {e}")
# #             error_msg = f"Error: {str(e)}"
# #             self.root.after(0, self.add_feedback_to_display, error_msg)
# #
# #         finally:
# #             self.vlm_processing = False
# #             self.update_status("⚪ Waiting for user input…")
# #
# #     def display_vlm_feedback(self, feedback_json):
# #         feedback = feedback_json.get("feedback", "No feedback")
# #         correctness = feedback_json.get("correctness", None)
# #
# #         color = "#00AA00" if correctness is True else "#FF0000" if correctness is False else "#FFA500"
# #         correctness_str = "✓ Correct" if correctness is True else "✗ Incorrect" if correctness is False else "? Unknown"
# #
# #         display_text = f"{correctness_str}\n\n{feedback}"
# #         self.add_feedback_to_display(display_text)
# #
# #         if self.last_stroke_bbox:
# #             self.render_overlay(feedback, color, correctness)
# #
# #     def render_overlay(self, feedback_text, color, correctness):
# #         if self.overlay_canvas_id:
# #             self.solution_canvas.delete(self.overlay_canvas_id)
# #
# #         overlay_x = 10
# #         overlay_y = self.lowest_y + 30
# #         max_box_width = 600
# #         min_box_width = 200
# #
# #         wrapped_lines = self.wrap_text(feedback_text, max_box_width)
# #
# #         if not wrapped_lines:
# #             wrapped_lines = [feedback_text]
# #
# #         estimated_line_width = max(len(line) * 7 for line in wrapped_lines) if wrapped_lines else 150
# #         box_width = min(max_box_width, max(min_box_width, estimated_line_width + 20))
# #         box_height = len(wrapped_lines) * 20 + 20
# #
# #         self.solution_canvas.create_rectangle(
# #             overlay_x, overlay_y, overlay_x + box_width, overlay_y + box_height,
# #             fill=color, outline="black", width=2,
# #             tags="overlay"
# #         )
# #
# #         text_y = overlay_y + 10
# #         for line in wrapped_lines:
# #             self.solution_canvas.create_text(
# #                 overlay_x + 10, text_y,
# #                 text=line, font=("Arial", 9), fill="white",
# #                 anchor="nw", width=box_width - 20,
# #                 tags="overlay"
# #             )
# #             text_y += 20
# #
# #         self.overlay_canvas_id = "overlay"
# #
# #     def wrap_text(self, text, max_width):
# #         words = text.split()
# #         lines = []
# #         current_line = []
# #
# #         for word in words:
# #             current_line.append(word)
# #             line_text = ' '.join(current_line)
# #
# #             estimated_width = len(line_text) * 7
# #
# #             if estimated_width > max_width - 30:
# #                 if len(current_line) > 1:
# #                     current_line.pop()
# #                     lines.append(' '.join(current_line))
# #                     current_line = [word]
# #                 else:
# #                     lines.append(line_text)
# #                     current_line = []
# #
# #         if current_line:
# #             lines.append(' '.join(current_line))
# #
# #         return lines if lines else [text]
# #
# #     def fade_out_overlay(self):
# #         if self.overlay_canvas_id:
# #             self.solution_canvas.delete(self.overlay_canvas_id)
# #             self.overlay_canvas_id = None
# #
# #     def log_feedback(self, feedback_json):
# #         try:
# #             log_entry = {
# #                 "timestamp": datetime.now().isoformat() + "Z",
# #                 "question_image": os.path.basename(self.question_image_path) if self.question_image_path else None,
# #                 "feedback": feedback_json.get("feedback", ""),
# #                 "correctness": feedback_json.get("correctness", None)
# #             }
# #             with open(self.feedback_log_file, "a") as f:
# #                 f.write(json.dumps(log_entry) + "\n")
# #             logger.info(f"Feedback logged: {log_entry}")
# #         except Exception as e:
# #             logger.error(f"Failed to log feedback: {e}")
# #
# #     def on_closing(self):
# #         self.stop_monitor = True
# #         if self.monitor_thread:
# #             self.monitor_thread.join(timeout=1)
# #
# #         if self.question_image_path and os.path.exists(self.question_image_path):
# #             try:
# #                 os.remove(self.question_image_path)
# #             except:
# #                 pass
# #
# #         self.root.destroy()
# #
# #
# # def launch_whiteboard():
# #     """
# #     Launch Whiteboard Canvas Mode
# #     Called from vlm_studio_launcher.py
# #     Creates a new Toplevel window for the whiteboard
# #     """
# #     root = tk.Toplevel()
# #     root.title("VLM Studio – Whiteboard Canvas Mode")
# #     app = SmartWhiteboardVLMDual(root)
# #     root.protocol("WM_DELETE_WINDOW", app.on_closing)
# #
# #
# # if __name__ == "__main__":
# #     root = tk.Tk()
# #     app = SmartWhiteboardVLMDual(root)
# #     root.protocol("WM_DELETE_WINDOW", app.on_closing)
# #     root.mainloop()
#
# import tkinter as tk
# from tkinter import messagebox
# import cv2
# import numpy as np
# from PIL import Image, ImageDraw
# import threading
# import time
# import os
# import json
# from datetime import datetime
# import google.generativeai as genai
# import io
# import logging
# import uuid
#
# logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
# logger = logging.getLogger(__name__)
#
# API_KEY = "AIzaSyDWkTV9jzPXj0AmKrKhG5hFf9vMw5_zWeY"
# if not API_KEY:
#     raise ValueError("GEMINI_API_KEY environment variable not set!")
#
# genai.configure(api_key=API_KEY)
#
#
# class SmartWhiteboardVLMDual:
#     def __init__(self, root):
#         self.root = root
#         self.root.title("Smart Whiteboard with Gemini VLM - Dual Canvas")
#         self.root.geometry("1600x800")
#         self.root.configure(bg="#1a1a1a")
#
#         self.virtual_canvas_width = 5000
#         self.virtual_canvas_height = 5000
#         self.initial_pil_width = 2000
#         self.initial_pil_height = 2000
#
#         self.question_canvas_width = 700
#         self.question_canvas_height = 600
#         self.drawing = False
#         self.last_x = 0
#         self.last_y = 0
#         self.brush_size = 3
#         self.eraser_size = 15
#
#         self.question_strokes = []
#         self.solution_strokes = []
#         self.current_stroke = []
#         self.current_stroke_canvas = None
#
#         self.question_pil_image = Image.new("RGB", (self.question_canvas_width, self.question_canvas_height), "white")
#         self.question_pil_draw = ImageDraw.Draw(self.question_pil_image)
#
#         self.solution_pil_image = Image.new("RGB", (self.initial_pil_width, self.initial_pil_height), "white")
#         self.solution_pil_draw = ImageDraw.Draw(self.solution_pil_image)
#
#         self.panning = False
#         self.pan_start_x = 0
#         self.pan_start_y = 0
#
#         self.prev_frame = None
#         self.writing_stopped_time = time.time()
#         self.is_writing = False
#         self.stop_writing_threshold = 1.5
#         self.frame_diff_threshold = 1000
#         self.frame_capture_interval = 0.1
#
#         self.vlm_processing = False
#         self.pending_vlm_response = None
#         self.last_stroke_bbox = None
#         self.overlay_canvas_id = None
#         self.lowest_y = 0
#
#         self.question_locked = False
#         self.question_image_path = None
#         self.solution_image_path = None
#
#         self.feedback_log_file = "vlm_feedback.jsonl"
#
#         self.monitor_thread = None
#         self.stop_monitor = False
#
#         self.setup_ui()
#         self.start_monitoring()
#
#     def setup_ui(self):
#         main_container = tk.Frame(self.root, bg="#1a1a1a")
#         main_container.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=10, pady=10)
#
#         left_section = tk.Frame(main_container, bg="#1a1a1a")
#         left_section.pack(side=tk.LEFT, fill=tk.BOTH, expand=False, padx=5)
#
#         question_label = tk.Label(left_section, text="Question", font=("Arial", 14, "bold"),
#                                   bg="#1a1a1a", fg="#ffffff")
#         question_label.pack()
#
#         question_info = tk.Label(left_section, text="Write the problem here", font=("Arial", 9),
#                                  bg="#1a1a1a", fg="#aaaaaa")
#         question_info.pack()
#
#         self.question_canvas = tk.Canvas(
#             left_section,
#             width=self.question_canvas_width,
#             height=self.question_canvas_height,
#             bg="white",
#             cursor="cross",
#             highlightthickness=2,
#             highlightbackground="#555555"
#         )
#         self.question_canvas.pack(pady=5)
#
#         self.question_canvas.bind("<Button-1>", self.start_draw_question)
#         self.question_canvas.bind("<B1-Motion>", self.draw_question)
#         self.question_canvas.bind("<ButtonRelease-1>", self.stop_draw_question)
#         self.question_canvas.bind("<Button-3>", self.start_erase_question)
#         self.question_canvas.bind("<B3-Motion>", self.erase_question)
#         self.question_canvas.bind("<ButtonRelease-3>", self.stop_erase_question)
#
#         right_section = tk.Frame(main_container, bg="#1a1a1a")
#         right_section.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5)
#
#         solution_label = tk.Label(right_section, text="Solution", font=("Arial", 14, "bold"),
#                                   bg="#1a1a1a", fg="#ffffff")
#         solution_label.pack()
#
#         solution_info = tk.Label(right_section, text="Scroll (Mouse Wheel) • Pan (Middle Click + Drag)",
#                                  font=("Arial", 9), bg="#1a1a1a", fg="#aaaaaa")
#         solution_info.pack()
#
#         canvas_frame = tk.Frame(right_section, bg="#1a1a1a")
#         canvas_frame.pack(fill=tk.BOTH, expand=True, pady=5)
#
#         v_scrollbar = tk.Scrollbar(canvas_frame, orient=tk.VERTICAL, bg="#333333", troughcolor="#1a1a1a")
#         v_scrollbar.grid(row=0, column=1, sticky="ns")
#
#         h_scrollbar = tk.Scrollbar(canvas_frame, orient=tk.HORIZONTAL, bg="#333333", troughcolor="#1a1a1a")
#         h_scrollbar.grid(row=1, column=0, sticky="ew")
#
#         self.solution_canvas = tk.Canvas(
#             canvas_frame,
#             bg="white",
#             cursor="cross",
#             scrollregion=(0, 0, self.virtual_canvas_width, self.virtual_canvas_height),
#             yscrollcommand=v_scrollbar.set,
#             xscrollcommand=h_scrollbar.set,
#             highlightthickness=2,
#             highlightbackground="#555555"
#         )
#         self.solution_canvas.grid(row=0, column=0, sticky="nsew")
#
#         v_scrollbar.config(command=self.solution_canvas.yview)
#         h_scrollbar.config(command=self.solution_canvas.xview)
#
#         canvas_frame.rowconfigure(0, weight=1)
#         canvas_frame.columnconfigure(0, weight=1)
#
#         self.solution_canvas.bind("<Button-1>", self.start_draw_solution)
#         self.solution_canvas.bind("<B1-Motion>", self.draw_solution)
#         self.solution_canvas.bind("<ButtonRelease-1>", self.stop_draw_solution)
#         self.solution_canvas.bind("<Button-3>", self.start_erase_solution)
#         self.solution_canvas.bind("<B3-Motion>", self.erase_solution)
#         self.solution_canvas.bind("<ButtonRelease-3>", self.stop_erase_solution)
#         self.solution_canvas.bind("<Button-2>", self.start_pan)
#         self.solution_canvas.bind("<B2-Motion>", self.do_pan)
#         self.solution_canvas.bind("<MouseWheel>", self.on_mousewheel)
#         self.solution_canvas.bind("<Button-4>", self.on_mousewheel)
#         self.solution_canvas.bind("<Button-5>", self.on_mousewheel)
#
#         solution_button_frame = tk.Frame(right_section, bg="#1a1a1a")
#         solution_button_frame.pack(pady=5)
#
#         self.clear_solution_btn = tk.Button(
#             solution_button_frame,
#             text="Clear Solution",
#             command=self.clear_solution,
#             bg="#FFA500",
#             fg="black",
#             width=18,
#             font=("Arial", 12, "bold"),
#             relief=tk.RAISED,
#             borderwidth=3,
#             activebackground="#ff8c00",
#             activeforeground="black",
#             highlightthickness=0
#         )
#         self.clear_solution_btn.pack(side=tk.TOP, padx=5, pady=5)
#
#         button_frame = tk.Frame(left_section, bg="#1a1a1a")
#         button_frame.pack(pady=10)
#
#         self.start_solution_btn = tk.Button(
#             button_frame,
#             text="Start Solution",
#             command=self.start_solution,
#             bg="#4CAF50",
#             fg="black",
#             width=18,
#             font=("Arial", 12, "bold"),
#             relief=tk.RAISED,
#             borderwidth=3,
#             activebackground="#45a049",
#             activeforeground="black",
#             highlightthickness=0
#         )
#         self.start_solution_btn.pack(side=tk.TOP, padx=5, pady=5)
#
#         self.clear_btn = tk.Button(
#             button_frame,
#             text="Reset",
#             command=self.reset_canvases,
#             bg="#FF6B6B",
#             fg="black",
#             width=18,
#             font=("Arial", 12, "bold"),
#             relief=tk.RAISED,
#             borderwidth=3,
#             activebackground="#ff5252",
#             activeforeground="black",
#             highlightthickness=0
#         )
#         self.clear_btn.pack(side=tk.TOP, padx=5, pady=5)
#
#         self.exit_btn = tk.Button(
#             button_frame,
#             text="Exit",
#             command=self.root.quit,
#             bg="#999999",
#             fg="black",
#             width=18,
#             font=("Arial", 12, "bold"),
#             relief=tk.RAISED,
#             borderwidth=3,
#             activebackground="#777777",
#             activeforeground="black",
#             highlightthickness=0
#         )
#         self.exit_btn.pack(side=tk.TOP, padx=5, pady=5)
#
#         right_panel = tk.Frame(self.root, bg="#1a1a1a", width=300)
#         right_panel.pack(side=tk.RIGHT, fill=tk.BOTH, padx=10, pady=10)
#         right_panel.pack_propagate(False)
#
#         status_label = tk.Label(right_panel, text="Status", font=("Arial", 14, "bold"),
#                                 bg="#1a1a1a", fg="#ffffff")
#         status_label.pack(pady=(10, 5))
#
#         self.status_display = tk.Label(
#             right_panel,
#             text="⚪ Waiting for user input…",
#             font=("Arial", 11),
#             bg="#1a1a1a",
#             fg="#ffffff",
#             wraplength=250,
#             justify=tk.LEFT
#         )
#         self.status_display.pack(pady=5)
#
#         feedback_label = tk.Label(right_panel, text="VLM Feedback", font=("Arial", 14, "bold"),
#                                   bg="#1a1a1a", fg="#ffffff")
#         feedback_label.pack(pady=(15, 5))
#
#         scrollbar = tk.Scrollbar(right_panel, bg="#333333", troughcolor="#1a1a1a")
#         scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
#
#         self.feedback_text = tk.Text(
#             right_panel,
#             height=25,
#             width=35,
#             font=("Courier", 10),
#             yscrollcommand=scrollbar.set,
#             bg="#2a2a2a",
#             fg="#ffffff",
#             insertbackground="#ffffff",
#             state=tk.DISABLED,
#             relief=tk.SOLID,
#             borderwidth=1
#         )
#         self.feedback_text.pack(pady=5, fill=tk.BOTH, expand=True)
#         scrollbar.config(command=self.feedback_text.yview)
#
#     def start_draw_question(self, event):
#         if self.question_locked:
#             return
#         self.drawing = True
#         self.current_stroke_canvas = "question"
#         self.last_x = event.x
#         self.last_y = event.y
#         self.current_stroke = [(int(event.x), int(event.y))]
#         self.update_status("🟢 Writing question…")
#
#     def draw_question(self, event):
#         if not self.drawing or self.current_stroke_canvas != "question":
#             return
#
#         self.question_canvas.create_line(
#             self.last_x, self.last_y, event.x, event.y,
#             fill="black", width=self.brush_size, capstyle=tk.ROUND, smooth=True
#         )
#
#         self.question_pil_draw.line(
#             [(self.last_x, self.last_y), (event.x, event.y)],
#             fill="black",
#             width=self.brush_size
#         )
#
#         self.current_stroke.append((int(event.x), int(event.y)))
#         self.last_x = event.x
#         self.last_y = event.y
#
#     def stop_draw_question(self, event):
#         if not self.drawing or self.current_stroke_canvas != "question":
#             return
#         self.drawing = False
#         if self.current_stroke:
#             self.question_strokes.append(self.current_stroke)
#             self.current_stroke = []
#         self.current_stroke_canvas = None
#
#     def start_erase_question(self, event):
#         if self.question_locked:
#             return
#         self.drawing = True
#         self.current_stroke_canvas = "question_erase"
#         self.last_x = event.x
#         self.last_y = event.y
#         self.erase_question(event)
#
#     def erase_question(self, event):
#         if not self.drawing or self.current_stroke_canvas != "question_erase":
#             return
#
#         self.question_canvas.create_oval(
#             event.x - self.eraser_size, event.y - self.eraser_size,
#             event.x + self.eraser_size, event.y + self.eraser_size,
#             fill="white", outline="white"
#         )
#         self.question_pil_draw.ellipse(
#             [(event.x - self.eraser_size, event.y - self.eraser_size),
#              (event.x + self.eraser_size, event.y + self.eraser_size)],
#             fill="white"
#         )
#         self.last_x = event.x
#         self.last_y = event.y
#
#     def stop_erase_question(self, event):
#         if self.current_stroke_canvas == "question_erase":
#             self.drawing = False
#             self.current_stroke_canvas = None
#
#     def start_draw_solution(self, event):
#         if not self.question_locked:
#             self.update_status("⚠️  Click 'Start Solution' first!")
#             return
#         self.drawing = True
#         self.current_stroke_canvas = "solution"
#         x = self.solution_canvas.canvasx(event.x)
#         y = self.solution_canvas.canvasy(event.y)
#         self.last_x = x
#         self.last_y = y
#         self.current_stroke = [(int(x), int(y))]
#         self.is_writing = True
#         self.writing_stopped_time = time.time()
#         self.update_status("🟢 Writing solution…")
#         self.fade_out_overlay()
#
#     def draw_solution(self, event):
#         if not self.drawing or self.current_stroke_canvas != "solution":
#             return
#
#         x = self.solution_canvas.canvasx(event.x)
#         y = self.solution_canvas.canvasy(event.y)
#
#         self.solution_canvas.create_line(
#             self.last_x, self.last_y, x, y,
#             fill="black", width=self.brush_size, capstyle=tk.ROUND, smooth=True
#         )
#
#         self.solution_pil_draw.line(
#             [(self.last_x, self.last_y), (x, y)],
#             fill="black",
#             width=self.brush_size
#         )
#
#         self.current_stroke.append((int(x), int(y)))
#         self.last_x = x
#         self.last_y = y
#         self.writing_stopped_time = time.time()
#
#     def stop_draw_solution(self, event):
#         if not self.drawing or self.current_stroke_canvas != "solution":
#             return
#         self.drawing = False
#         if self.current_stroke:
#             self.solution_strokes.append(self.current_stroke)
#             xs, ys = zip(*self.current_stroke)
#             min_x, max_x = min(xs), max(xs)
#             min_y, max_y = min(ys), max(ys)
#             self.last_stroke_bbox = (min_x, min_y, max_x - min_x + 10, max_y - min_y + 10)
#
#             if max_y > self.lowest_y:
#                 self.lowest_y = max_y
#
#             self.current_stroke = []
#
#         self.update_scroll_region()
#         self.current_stroke_canvas = None
#
#     def start_erase_solution(self, event):
#         if not self.question_locked:
#             self.update_status("⚠️  Click 'Start Solution' first!")
#             return
#         self.drawing = True
#         self.current_stroke_canvas = "solution_erase"
#         x = self.solution_canvas.canvasx(event.x)
#         y = self.solution_canvas.canvasy(event.y)
#         self.last_x = x
#         self.last_y = y
#         self.erase_solution(event)
#
#     def erase_solution(self, event):
#         if not self.drawing or self.current_stroke_canvas != "solution_erase":
#             return
#
#         x = self.solution_canvas.canvasx(event.x)
#         y = self.solution_canvas.canvasy(event.y)
#
#         self.solution_canvas.create_oval(
#             x - self.eraser_size, y - self.eraser_size,
#             x + self.eraser_size, y + self.eraser_size,
#             fill="white", outline="white"
#         )
#         self.solution_pil_draw.ellipse(
#             [(x - self.eraser_size, y - self.eraser_size),
#              (x + self.eraser_size, y + self.eraser_size)],
#             fill="white"
#         )
#         self.last_x = x
#         self.last_y = y
#
#     def stop_erase_solution(self, event):
#         if self.current_stroke_canvas == "solution_erase":
#             self.drawing = False
#             self.current_stroke_canvas = None
#
#     def start_solution(self):
#         if not self.question_strokes:
#             messagebox.showwarning("Warning", "Please write a question first!")
#             return
#
#         self.question_locked = True
#         self.snapshot_question()
#         self.update_status("⚪ Question locked. Start solving…")
#         self.start_solution_btn.config(state=tk.DISABLED)
#         self.question_canvas.config(cursor="no")
#
#     def snapshot_question(self):
#         try:
#             self.question_image_path = f"question_{uuid.uuid4().hex[:8]}.png"
#             self.question_pil_image.save(self.question_image_path)
#             logger.info(f"Question snapshot saved: {self.question_image_path}")
#         except Exception as e:
#             logger.error(f"Failed to snapshot question: {e}")
#             messagebox.showerror("Error", f"Failed to snapshot question: {e}")
#
#     def reset_canvases(self):
#         self.solution_canvas.delete("all")
#         self.question_canvas.delete("all")
#
#         self.question_pil_image = Image.new("RGB", (self.question_canvas_width, self.question_canvas_height), "white")
#         self.question_pil_draw = ImageDraw.Draw(self.question_pil_image)
#
#         self.solution_pil_image = Image.new("RGB", (self.initial_pil_width, self.initial_pil_height), "white")
#         self.solution_pil_draw = ImageDraw.Draw(self.solution_pil_image)
#
#         self.question_strokes = []
#         self.solution_strokes = []
#         self.current_stroke = []
#
#         self.question_locked = False
#         if self.question_image_path and os.path.exists(self.question_image_path):
#             os.remove(self.question_image_path)
#         self.question_image_path = None
#         self.solution_image_path = None
#
#         self.last_stroke_bbox = None
#         self.lowest_y = 0
#         self.prev_frame = None
#         self.is_writing = False
#
#         self.start_solution_btn.config(state=tk.NORMAL)
#         self.question_canvas.config(cursor="cross")
#
#         self.solution_canvas.config(scrollregion=(0, 0, self.virtual_canvas_width, self.virtual_canvas_height))
#         self.update_status("⚪ Waiting for user input…")
#         self.clear_feedback_display()
#
#     def clear_solution(self):
#         self.solution_canvas.delete("all")
#
#         self.solution_pil_image = Image.new("RGB", (self.initial_pil_width, self.initial_pil_height), "white")
#         self.solution_pil_draw = ImageDraw.Draw(self.solution_pil_image)
#
#         self.solution_strokes = []
#         self.current_stroke = []
#
#         self.last_stroke_bbox = None
#         self.lowest_y = 0
#         self.prev_frame = None
#         self.is_writing = False
#
#         self.solution_canvas.config(scrollregion=(0, 0, self.virtual_canvas_width, self.virtual_canvas_height))
#         self.update_status("⚪ Solution cleared…")
#         self.fade_out_overlay()
#
#     def on_mousewheel(self, event):
#         if event.num == 5 or event.delta < 0:
#             self.solution_canvas.yview_scroll(3, "units")
#         elif event.num == 4 or event.delta > 0:
#             self.solution_canvas.yview_scroll(-3, "units")
#
#     def start_pan(self, event):
#         self.panning = True
#         self.solution_canvas.scan_mark(event.x, event.y)
#
#     def do_pan(self, event):
#         self.solution_canvas.scan_dragto(event.x, event.y, gain=1)
#
#     def update_scroll_region(self):
#         bbox = self.solution_canvas.bbox("all")
#         if bbox:
#             x1, y1, x2, y2 = bbox
#             x1, y1 = max(0, int(x1) - 100), max(0, int(y1) - 100)
#             x2, y2 = int(x2) + 100, int(y2) + 100
#
#             x2 = max(x2, self.virtual_canvas_width)
#             y2 = max(y2, self.virtual_canvas_height)
#
#             self.solution_canvas.config(scrollregion=(x1, y1, x2, y2))
#         else:
#             self.solution_canvas.config(scrollregion=(0, 0, self.virtual_canvas_width, self.virtual_canvas_height))
#
#     def update_status(self, status):
#         self.status_display.config(text=status)
#         self.root.update_idletasks()
#
#     def clear_feedback_display(self):
#         self.feedback_text.config(state=tk.NORMAL)
#         self.feedback_text.delete("1.0", tk.END)
#         self.feedback_text.config(state=tk.DISABLED)
#
#     def add_feedback_to_display(self, feedback_text):
#         self.feedback_text.config(state=tk.NORMAL)
#         timestamp = datetime.now().strftime("%H:%M:%S")
#         self.feedback_text.insert(tk.END, f"[{timestamp}]\n{feedback_text}\n\n")
#         self.feedback_text.see(tk.END)
#         self.feedback_text.config(state=tk.DISABLED)
#
#     def start_monitoring(self):
#         self.monitor_thread = threading.Thread(target=self.monitor_writing, daemon=True)
#         self.monitor_thread.start()
#
#     def monitor_writing(self):
#         while not self.stop_monitor:
#             time.sleep(self.frame_capture_interval)
#
#             if not self.is_writing:
#                 continue
#
#             current_frame = self.pil_image_to_cv2(self.solution_pil_image)
#
#             if self.prev_frame is not None:
#                 diff = cv2.absdiff(current_frame, self.prev_frame)
#                 gray_diff = cv2.cvtColor(diff, cv2.COLOR_BGR2GRAY)
#                 movement = np.sum(gray_diff > 20)
#
#                 if movement < self.frame_diff_threshold:
#                     elapsed = time.time() - self.writing_stopped_time
#                     if elapsed >= self.stop_writing_threshold and not self.vlm_processing:
#                         self.is_writing = False
#                         self.on_writing_stopped()
#                 else:
#                     self.writing_stopped_time = time.time()
#             else:
#                 self.writing_stopped_time = time.time()
#
#             self.prev_frame = current_frame.copy()
#
#     def pil_image_to_cv2(self, pil_img):
#         return cv2.cvtColor(np.array(pil_img), cv2.COLOR_RGB2BGR)
#
#     def on_writing_stopped(self):
#         logger.info("Writing stopped detected. Triggering VLM analysis...")
#         self.update_status("🔵 Processing OCR…")
#         self.vlm_processing = True
#
#         vlm_thread = threading.Thread(target=self.process_with_vlm, daemon=True)
#         vlm_thread.start()
#
#     def capture_solution_canvas(self):
#         logger.info("Using maintained PIL image for VLM processing")
#         return self.solution_pil_image
#
#     def process_with_vlm(self):
#         try:
#             if not self.question_image_path:
#                 logger.error("Question image not available!")
#                 self.root.after(0, self.add_feedback_to_display, "Error: Question image missing")
#                 self.vlm_processing = False
#                 return
#
#             logger.info("Capturing solution canvas…")
#             solution_image = self.capture_solution_canvas()
#             logger.info(f"Solution captured: {solution_image.size}")
#
#             prompt = (
#                 "You will receive two images. "
#                 "The FIRST image is the QUESTION/PROBLEM. "
#                 "The SECOND image is the SOLUTION/ANSWER written by the user. "
#                 "Analyze whether the SOLUTION correctly solves the QUESTION. "
#                 "Evaluate each step logically and mathematically — check signs, arithmetic, factorization, substitutions, and final answers. "
#                 "If the solution appears INCOMPLETE but the steps so far are correct and consistent with the question, "
#                 "respond that the intermediate steps are correct so far and more work is needed, "
#                 "and set correctness to true. "
#                 "Only mark correctness as false if there are genuine mistakes or inconsistencies. "
#                 "Respond ONLY in strict JSON format as below — no markdown or extra text:\n"
#                 "{\"feedback\": \"concise feedback under 100 words\", \"correctness\": true/false}"
#             )
#
#             with open(self.question_image_path, "rb") as q_file:
#                 question_data = q_file.read()
#
#             solution_data = io.BytesIO()
#             solution_image.save(solution_data, format='PNG')
#             solution_data = solution_data.getvalue()
#
#             model = genai.GenerativeModel("gemini-2.5-flash")
#             response = model.generate_content(
#                 [
#                     prompt,
#                     {"mime_type": "image/png", "data": question_data},
#                     {"mime_type": "image/png", "data": solution_data}
#                 ]
#             )
#
#             feedback_text = response.text.strip()
#
#             try:
#                 json_start = feedback_text.find("{")
#                 json_end = feedback_text.rfind("}") + 1
#                 if json_start != -1 and json_end > json_start:
#                     feedback_json = json.loads(feedback_text[json_start:json_end])
#                 else:
#                     feedback_json = {"feedback": feedback_text, "correctness": None}
#             except json.JSONDecodeError:
#                 feedback_json = {"feedback": feedback_text, "correctness": None}
#
#             logger.info(f"VLM Response: {json.dumps(feedback_json, indent=2)}")
#
#             self.log_feedback(feedback_json)
#
#             self.root.after(0, self.display_vlm_feedback, feedback_json)
#
#         except Exception as e:
#             logger.error(f"VLM processing error: {e}")
#             error_msg = f"Error: {str(e)}"
#             self.root.after(0, self.add_feedback_to_display, error_msg)
#
#         finally:
#             self.vlm_processing = False
#             self.update_status("⚪ Waiting for user input…")
#
#     def display_vlm_feedback(self, feedback_json):
#         feedback = feedback_json.get("feedback", "No feedback")
#         correctness = feedback_json.get("correctness", None)
#
#         color = "#00AA00" if correctness is True else "#FF0000" if correctness is False else "#FFA500"
#         correctness_str = "✓ Correct" if correctness is True else "✗ Incorrect" if correctness is False else "? Unknown"
#
#         display_text = f"{correctness_str}\n\n{feedback}"
#         self.add_feedback_to_display(display_text)
#
#         if self.last_stroke_bbox:
#             self.render_overlay(feedback, color, correctness)
#
#     def render_overlay(self, feedback_text, color, correctness):
#         if self.overlay_canvas_id:
#             self.solution_canvas.delete(self.overlay_canvas_id)
#
#         overlay_x = 10
#         overlay_y = self.lowest_y + 30
#         max_box_width = 600
#         min_box_width = 200
#
#         wrapped_lines = self.wrap_text(feedback_text, max_box_width)
#
#         if not wrapped_lines:
#             wrapped_lines = [feedback_text]
#
#         estimated_line_width = max(len(line) * 7 for line in wrapped_lines) if wrapped_lines else 150
#         box_width = min(max_box_width, max(min_box_width, estimated_line_width + 20))
#         box_height = len(wrapped_lines) * 20 + 20
#
#         self.solution_canvas.create_rectangle(
#             overlay_x, overlay_y, overlay_x + box_width, overlay_y + box_height,
#             fill=color, outline="black", width=2,
#             tags="overlay"
#         )
#
#         text_y = overlay_y + 10
#         for line in wrapped_lines:
#             self.solution_canvas.create_text(
#                 overlay_x + 10, text_y,
#                 text=line, font=("Arial", 9), fill="white",
#                 anchor="nw", width=box_width - 20,
#                 tags="overlay"
#             )
#             text_y += 20
#
#         self.overlay_canvas_id = "overlay"
#
#     def wrap_text(self, text, max_width):
#         words = text.split()
#         lines = []
#         current_line = []
#
#         for word in words:
#             current_line.append(word)
#             line_text = ' '.join(current_line)
#
#             estimated_width = len(line_text) * 7
#
#             if estimated_width > max_width - 30:
#                 if len(current_line) > 1:
#                     current_line.pop()
#                     lines.append(' '.join(current_line))
#                     current_line = [word]
#                 else:
#                     lines.append(line_text)
#                     current_line = []
#
#         if current_line:
#             lines.append(' '.join(current_line))
#
#         return lines if lines else [text]
#
#     def fade_out_overlay(self):
#         if self.overlay_canvas_id:
#             self.solution_canvas.delete(self.overlay_canvas_id)
#             self.overlay_canvas_id = None
#
#     def log_feedback(self, feedback_json):
#         try:
#             log_entry = {
#                 "timestamp": datetime.now().isoformat() + "Z",
#                 "question_image": os.path.basename(self.question_image_path) if self.question_image_path else None,
#                 "feedback": feedback_json.get("feedback", ""),
#                 "correctness": feedback_json.get("correctness", None)
#             }
#             with open(self.feedback_log_file, "a") as f:
#                 f.write(json.dumps(log_entry) + "\n")
#             logger.info(f"Feedback logged: {log_entry}")
#         except Exception as e:
#             logger.error(f"Failed to log feedback: {e}")
#
#     def on_closing(self):
#         self.stop_monitor = True
#         if self.monitor_thread:
#             self.monitor_thread.join(timeout=1)
#
#         if self.question_image_path and os.path.exists(self.question_image_path):
#             try:
#                 os.remove(self.question_image_path)
#             except:
#                 pass
#
#         self.root.destroy()
#
#
# def launch_whiteboard():
#     """
#     Launch Whiteboard Canvas Mode
#     Called from vlm_studio_launcher.py
#     Creates a new Toplevel window for the whiteboard
#     """
#     root = tk.Toplevel()
#     root.title("VLM Studio – Whiteboard Canvas Mode")
#     app = SmartWhiteboardVLMDual(root)
#     root.protocol("WM_DELETE_WINDOW", app.on_closing)
#
#
# if __name__ == "__main__":
#     root = tk.Tk()
#     app = SmartWhiteboardVLMDual(root)
#     root.protocol("WM_DELETE_WINDOW", app.on_closing)
#     root.mainloop()

import tkinter as tk
from tkinter import messagebox
import cv2
import numpy as np
from PIL import Image, ImageDraw
import threading
import time
import os
import json
from datetime import datetime
import google.generativeai as genai
import io
import logging
import uuid

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

API_KEY = "AIzaSyDWkTV9jzPXj0AmKrKhG5hFf9vMw5_zWeY"
if not API_KEY:
    raise ValueError("GEMINI_API_KEY environment variable not set!")

genai.configure(api_key=API_KEY)


class SmartWhiteboardVLMDual:
    def __init__(self, root):
        self.root = root
        self.root.title("Smart Whiteboard with Gemini VLM - Dual Canvas")
        self.root.geometry("1600x800")
        self.root.configure(bg="#1a1a1a")

        self.virtual_canvas_width = 5000
        self.virtual_canvas_height = 5000
        self.initial_pil_width = 2000
        self.initial_pil_height = 2000

        self.question_canvas_width = 450
        self.question_canvas_height = 500
        self.drawing = False
        self.last_x = 0
        self.last_y = 0
        self.brush_size = 3
        self.eraser_size = 15

        self.question_strokes = []
        self.solution_strokes = []
        self.current_stroke = []
        self.current_stroke_canvas = None

        self.question_pil_image = Image.new("RGB", (self.question_canvas_width, self.question_canvas_height), "white")
        self.question_pil_draw = ImageDraw.Draw(self.question_pil_image)

        self.solution_pil_image = Image.new("RGB", (self.initial_pil_width, self.initial_pil_height), "white")
        self.solution_pil_draw = ImageDraw.Draw(self.solution_pil_image)

        self.panning = False
        self.pan_start_x = 0
        self.pan_start_y = 0

        self.prev_frame = None
        self.writing_stopped_time = time.time()
        self.is_writing = False
        self.stop_writing_threshold = 1.5
        self.frame_diff_threshold = 1000
        self.frame_capture_interval = 0.1

        self.vlm_processing = False
        self.pending_vlm_response = None
        self.last_stroke_bbox = None
        self.overlay_canvas_id = None
        self.lowest_y = 0

        self.question_locked = False
        self.question_image_path = None
        self.solution_image_path = None

        self.feedback_log_file = "vlm_feedback.jsonl"

        self.monitor_thread = None
        self.stop_monitor = False

        self.setup_ui()
        self.start_monitoring()

    def setup_ui(self):
        main_container = tk.Frame(self.root, bg="#1a1a1a")
        main_container.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=10, pady=10)

        left_section = tk.Frame(main_container, bg="#1a1a1a")
        left_section.pack(side=tk.LEFT, fill=tk.BOTH, expand=False, padx=5)

        question_label = tk.Label(left_section, text="Question", font=("Arial", 14, "bold"),
                                  bg="#1a1a1a", fg="#ffffff")
        question_label.pack()

        question_info = tk.Label(left_section, text="Write the problem here", font=("Arial", 9),
                                 bg="#1a1a1a", fg="#aaaaaa")
        question_info.pack()

        self.question_canvas = tk.Canvas(
            left_section,
            width=self.question_canvas_width,
            height=self.question_canvas_height,
            bg="white",
            cursor="cross",
            highlightthickness=2,
            highlightbackground="#555555"
        )
        self.question_canvas.pack(pady=5)

        self.question_canvas.bind("<Button-1>", self.start_draw_question)
        self.question_canvas.bind("<B1-Motion>", self.draw_question)
        self.question_canvas.bind("<ButtonRelease-1>", self.stop_draw_question)
        self.question_canvas.bind("<Button-3>", self.start_erase_question)
        self.question_canvas.bind("<B3-Motion>", self.erase_question)
        self.question_canvas.bind("<ButtonRelease-3>", self.stop_erase_question)

        right_section = tk.Frame(main_container, bg="#1a1a1a")
        right_section.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5)

        solution_label = tk.Label(right_section, text="Solution", font=("Arial", 14, "bold"),
                                  bg="#1a1a1a", fg="#ffffff")
        solution_label.pack()

        solution_info = tk.Label(right_section, text="Scroll (Mouse Wheel) • Pan (Middle Click + Drag)",
                                 font=("Arial", 9), bg="#1a1a1a", fg="#aaaaaa")
        solution_info.pack()

        canvas_frame = tk.Frame(right_section, bg="#1a1a1a")
        canvas_frame.pack(fill=tk.BOTH, expand=True, pady=5)

        v_scrollbar = tk.Scrollbar(canvas_frame, orient=tk.VERTICAL, bg="#333333", troughcolor="#1a1a1a")
        v_scrollbar.grid(row=0, column=1, sticky="ns")

        h_scrollbar = tk.Scrollbar(canvas_frame, orient=tk.HORIZONTAL, bg="#333333", troughcolor="#1a1a1a")
        h_scrollbar.grid(row=1, column=0, sticky="ew")

        self.solution_canvas = tk.Canvas(
            canvas_frame,
            bg="white",
            cursor="cross",
            scrollregion=(0, 0, self.virtual_canvas_width, self.virtual_canvas_height),
            yscrollcommand=v_scrollbar.set,
            xscrollcommand=h_scrollbar.set,
            highlightthickness=2,
            highlightbackground="#555555"
        )
        self.solution_canvas.grid(row=0, column=0, sticky="nsew")

        v_scrollbar.config(command=self.solution_canvas.yview)
        h_scrollbar.config(command=self.solution_canvas.xview)

        canvas_frame.rowconfigure(0, weight=1)
        canvas_frame.columnconfigure(0, weight=1)

        self.solution_canvas.bind("<Button-1>", self.start_draw_solution)
        self.solution_canvas.bind("<B1-Motion>", self.draw_solution)
        self.solution_canvas.bind("<ButtonRelease-1>", self.stop_draw_solution)
        self.solution_canvas.bind("<Button-3>", self.start_erase_solution)
        self.solution_canvas.bind("<B3-Motion>", self.erase_solution)
        self.solution_canvas.bind("<ButtonRelease-3>", self.stop_erase_solution)
        self.solution_canvas.bind("<Button-2>", self.start_pan)
        self.solution_canvas.bind("<B2-Motion>", self.do_pan)
        self.solution_canvas.bind("<MouseWheel>", self.on_mousewheel)
        self.solution_canvas.bind("<Button-4>", self.on_mousewheel)
        self.solution_canvas.bind("<Button-5>", self.on_mousewheel)

        solution_button_frame = tk.Frame(right_section, bg="#1a1a1a")
        solution_button_frame.pack(pady=5)

        self.clear_solution_btn = tk.Button(
            solution_button_frame,
            text="Clear Solution",
            command=self.clear_solution,
            bg="#FFA500",
            fg="black",
            width=18,
            font=("Arial", 12, "bold"),
            relief=tk.RAISED,
            borderwidth=3,
            activebackground="#ff8c00",
            activeforeground="black",
            highlightthickness=0
        )
        self.clear_solution_btn.pack(side=tk.TOP, padx=5, pady=5)

        button_frame = tk.Frame(left_section, bg="#1a1a1a")
        button_frame.pack(pady=10)

        self.start_solution_btn = tk.Button(
            button_frame,
            text="Start Solution",
            command=self.start_solution,
            bg="#4CAF50",
            fg="black",
            width=18,
            font=("Arial", 12, "bold"),
            relief=tk.RAISED,
            borderwidth=3,
            activebackground="#45a049",
            activeforeground="black",
            highlightthickness=0
        )
        self.start_solution_btn.pack(side=tk.TOP, padx=5, pady=5)

        self.clear_btn = tk.Button(
            button_frame,
            text="Reset",
            command=self.reset_canvases,
            bg="#FF6B6B",
            fg="black",
            width=18,
            font=("Arial", 12, "bold"),
            relief=tk.RAISED,
            borderwidth=3,
            activebackground="#ff5252",
            activeforeground="black",
            highlightthickness=0
        )
        self.clear_btn.pack(side=tk.TOP, padx=5, pady=5)

        self.exit_btn = tk.Button(
            button_frame,
            text="Exit",
            command=self.root.quit,
            bg="#999999",
            fg="black",
            width=18,
            font=("Arial", 12, "bold"),
            relief=tk.RAISED,
            borderwidth=3,
            activebackground="#777777",
            activeforeground="black",
            highlightthickness=0
        )
        self.exit_btn.pack(side=tk.TOP, padx=5, pady=5)

        right_panel = tk.Frame(self.root, bg="#1a1a1a", width=300)
        right_panel.pack(side=tk.RIGHT, fill=tk.BOTH, padx=10, pady=10)
        right_panel.pack_propagate(False)

        status_label = tk.Label(right_panel, text="Status", font=("Arial", 14, "bold"),
                                bg="#1a1a1a", fg="#ffffff")
        status_label.pack(pady=(10, 5))

        self.status_display = tk.Label(
            right_panel,
            text="⚪ Waiting for user input…",
            font=("Arial", 11),
            bg="#1a1a1a",
            fg="#ffffff",
            wraplength=250,
            justify=tk.LEFT
        )
        self.status_display.pack(pady=5)

        feedback_label = tk.Label(right_panel, text="VLM Feedback", font=("Arial", 14, "bold"),
                                  bg="#1a1a1a", fg="#ffffff")
        feedback_label.pack(pady=(15, 5))

        scrollbar = tk.Scrollbar(right_panel, bg="#333333", troughcolor="#1a1a1a")
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.feedback_text = tk.Text(
            right_panel,
            height=25,
            width=35,
            font=("Courier", 10),
            yscrollcommand=scrollbar.set,
            bg="#2a2a2a",
            fg="#ffffff",
            insertbackground="#ffffff",
            state=tk.DISABLED,
            relief=tk.SOLID,
            borderwidth=1
        )
        self.feedback_text.pack(pady=5, fill=tk.BOTH, expand=True)
        scrollbar.config(command=self.feedback_text.yview)

    def start_draw_question(self, event):
        if self.question_locked:
            return
        self.drawing = True
        self.current_stroke_canvas = "question"
        self.last_x = event.x
        self.last_y = event.y
        self.current_stroke = [(int(event.x), int(event.y))]
        self.update_status("🟢 Writing question…")

    def draw_question(self, event):
        if not self.drawing or self.current_stroke_canvas != "question":
            return

        self.question_canvas.create_line(
            self.last_x, self.last_y, event.x, event.y,
            fill="black", width=self.brush_size, capstyle=tk.ROUND, smooth=True
        )

        self.question_pil_draw.line(
            [(self.last_x, self.last_y), (event.x, event.y)],
            fill="black",
            width=self.brush_size
        )

        self.current_stroke.append((int(event.x), int(event.y)))
        self.last_x = event.x
        self.last_y = event.y

    def stop_draw_question(self, event):
        if not self.drawing or self.current_stroke_canvas != "question":
            return
        self.drawing = False
        if self.current_stroke:
            self.question_strokes.append(self.current_stroke)
            self.current_stroke = []
        self.current_stroke_canvas = None

    def start_erase_question(self, event):
        if self.question_locked:
            return
        self.drawing = True
        self.current_stroke_canvas = "question_erase"
        self.last_x = event.x
        self.last_y = event.y
        self.erase_question(event)

    def erase_question(self, event):
        if not self.drawing or self.current_stroke_canvas != "question_erase":
            return

        self.question_canvas.create_oval(
            event.x - self.eraser_size, event.y - self.eraser_size,
            event.x + self.eraser_size, event.y + self.eraser_size,
            fill="white", outline="white"
        )
        self.question_pil_draw.ellipse(
            [(event.x - self.eraser_size, event.y - self.eraser_size),
             (event.x + self.eraser_size, event.y + self.eraser_size)],
            fill="white"
        )
        self.last_x = event.x
        self.last_y = event.y

    def stop_erase_question(self, event):
        if self.current_stroke_canvas == "question_erase":
            self.drawing = False
            self.current_stroke_canvas = None

    def start_draw_solution(self, event):
        if not self.question_locked:
            self.update_status("⚠️  Click 'Start Solution' first!")
            return
        self.drawing = True
        self.current_stroke_canvas = "solution"
        x = self.solution_canvas.canvasx(event.x)
        y = self.solution_canvas.canvasy(event.y)
        self.last_x = x
        self.last_y = y
        self.current_stroke = [(int(x), int(y))]
        self.is_writing = True
        self.writing_stopped_time = time.time()
        self.update_status("🟢 Writing solution…")
        self.fade_out_overlay()

    def draw_solution(self, event):
        if not self.drawing or self.current_stroke_canvas != "solution":
            return

        x = self.solution_canvas.canvasx(event.x)
        y = self.solution_canvas.canvasy(event.y)

        self.solution_canvas.create_line(
            self.last_x, self.last_y, x, y,
            fill="black", width=self.brush_size, capstyle=tk.ROUND, smooth=True
        )

        self.solution_pil_draw.line(
            [(self.last_x, self.last_y), (x, y)],
            fill="black",
            width=self.brush_size
        )

        self.current_stroke.append((int(x), int(y)))
        self.last_x = x
        self.last_y = y
        self.writing_stopped_time = time.time()

    def stop_draw_solution(self, event):
        if not self.drawing or self.current_stroke_canvas != "solution":
            return
        self.drawing = False
        if self.current_stroke:
            self.solution_strokes.append(self.current_stroke)
            xs, ys = zip(*self.current_stroke)
            min_x, max_x = min(xs), max(xs)
            min_y, max_y = min(ys), max(ys)
            self.last_stroke_bbox = (min_x, min_y, max_x - min_x + 10, max_y - min_y + 10)

            if max_y > self.lowest_y:
                self.lowest_y = max_y

            self.current_stroke = []

        self.update_scroll_region()
        self.current_stroke_canvas = None

    def start_erase_solution(self, event):
        if not self.question_locked:
            self.update_status("⚠️  Click 'Start Solution' first!")
            return
        self.drawing = True
        self.current_stroke_canvas = "solution_erase"
        x = self.solution_canvas.canvasx(event.x)
        y = self.solution_canvas.canvasy(event.y)
        self.last_x = x
        self.last_y = y
        self.erase_solution(event)

    def erase_solution(self, event):
        if not self.drawing or self.current_stroke_canvas != "solution_erase":
            return

        x = self.solution_canvas.canvasx(event.x)
        y = self.solution_canvas.canvasy(event.y)

        self.solution_canvas.create_oval(
            x - self.eraser_size, y - self.eraser_size,
            x + self.eraser_size, y + self.eraser_size,
            fill="white", outline="white"
        )
        self.solution_pil_draw.ellipse(
            [(x - self.eraser_size, y - self.eraser_size),
             (x + self.eraser_size, y + self.eraser_size)],
            fill="white"
        )
        self.last_x = x
        self.last_y = y

    def stop_erase_solution(self, event):
        if self.current_stroke_canvas == "solution_erase":
            self.drawing = False
            self.current_stroke_canvas = None

    def start_solution(self):
        if not self.question_strokes:
            messagebox.showwarning("Warning", "Please write a question first!")
            return

        self.question_locked = True
        self.snapshot_question()
        self.update_status("⚪ Question locked. Start solving…")
        self.start_solution_btn.config(state=tk.DISABLED)
        self.question_canvas.config(cursor="no")

    def snapshot_question(self):
        try:
            self.question_image_path = f"question_{uuid.uuid4().hex[:8]}.png"
            self.question_pil_image.save(self.question_image_path)
            logger.info(f"Question snapshot saved: {self.question_image_path}")
        except Exception as e:
            logger.error(f"Failed to snapshot question: {e}")
            messagebox.showerror("Error", f"Failed to snapshot question: {e}")

    def reset_canvases(self):
        self.solution_canvas.delete("all")
        self.question_canvas.delete("all")

        self.question_pil_image = Image.new("RGB", (self.question_canvas_width, self.question_canvas_height), "white")
        self.question_pil_draw = ImageDraw.Draw(self.question_pil_image)

        self.solution_pil_image = Image.new("RGB", (self.initial_pil_width, self.initial_pil_height), "white")
        self.solution_pil_draw = ImageDraw.Draw(self.solution_pil_image)

        self.question_strokes = []
        self.solution_strokes = []
        self.current_stroke = []

        self.question_locked = False
        if self.question_image_path and os.path.exists(self.question_image_path):
            os.remove(self.question_image_path)
        self.question_image_path = None
        self.solution_image_path = None

        self.last_stroke_bbox = None
        self.lowest_y = 0
        self.prev_frame = None
        self.is_writing = False

        self.start_solution_btn.config(state=tk.NORMAL)
        self.question_canvas.config(cursor="cross")

        self.solution_canvas.config(scrollregion=(0, 0, self.virtual_canvas_width, self.virtual_canvas_height))
        self.update_status("⚪ Waiting for user input…")
        self.clear_feedback_display()

    def clear_solution(self):
        self.solution_canvas.delete("all")

        self.solution_pil_image = Image.new("RGB", (self.initial_pil_width, self.initial_pil_height), "white")
        self.solution_pil_draw = ImageDraw.Draw(self.solution_pil_image)

        self.solution_strokes = []
        self.current_stroke = []

        self.last_stroke_bbox = None
        self.lowest_y = 0
        self.prev_frame = None
        self.is_writing = False

        self.solution_canvas.config(scrollregion=(0, 0, self.virtual_canvas_width, self.virtual_canvas_height))
        self.update_status("⚪ Solution cleared…")
        self.fade_out_overlay()

    def on_mousewheel(self, event):
        if event.num == 5 or event.delta < 0:
            self.solution_canvas.yview_scroll(3, "units")
        elif event.num == 4 or event.delta > 0:
            self.solution_canvas.yview_scroll(-3, "units")

    def start_pan(self, event):
        self.panning = True
        self.solution_canvas.scan_mark(event.x, event.y)

    def do_pan(self, event):
        self.solution_canvas.scan_dragto(event.x, event.y, gain=1)

    def update_scroll_region(self):
        bbox = self.solution_canvas.bbox("all")
        if bbox:
            x1, y1, x2, y2 = bbox
            x1, y1 = max(0, int(x1) - 100), max(0, int(y1) - 100)
            x2, y2 = int(x2) + 100, int(y2) + 100

            x2 = max(x2, self.virtual_canvas_width)
            y2 = max(y2, self.virtual_canvas_height)

            self.solution_canvas.config(scrollregion=(x1, y1, x2, y2))
        else:
            self.solution_canvas.config(scrollregion=(0, 0, self.virtual_canvas_width, self.virtual_canvas_height))

    def update_status(self, status):
        self.status_display.config(text=status)
        self.root.update_idletasks()

    def clear_feedback_display(self):
        self.feedback_text.config(state=tk.NORMAL)
        self.feedback_text.delete("1.0", tk.END)
        self.feedback_text.config(state=tk.DISABLED)

    def add_feedback_to_display(self, feedback_text):
        self.feedback_text.config(state=tk.NORMAL)
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.feedback_text.insert(tk.END, f"[{timestamp}]\n{feedback_text}\n\n")
        self.feedback_text.see(tk.END)
        self.feedback_text.config(state=tk.DISABLED)

    def start_monitoring(self):
        self.monitor_thread = threading.Thread(target=self.monitor_writing, daemon=True)
        self.monitor_thread.start()

    def monitor_writing(self):
        while not self.stop_monitor:
            time.sleep(self.frame_capture_interval)

            if not self.is_writing:
                continue

            current_frame = self.pil_image_to_cv2(self.solution_pil_image)

            if self.prev_frame is not None:
                diff = cv2.absdiff(current_frame, self.prev_frame)
                gray_diff = cv2.cvtColor(diff, cv2.COLOR_BGR2GRAY)
                movement = np.sum(gray_diff > 20)

                if movement < self.frame_diff_threshold:
                    elapsed = time.time() - self.writing_stopped_time
                    if elapsed >= self.stop_writing_threshold and not self.vlm_processing:
                        self.is_writing = False
                        self.on_writing_stopped()
                else:
                    self.writing_stopped_time = time.time()
            else:
                self.writing_stopped_time = time.time()

            self.prev_frame = current_frame.copy()

    def pil_image_to_cv2(self, pil_img):
        return cv2.cvtColor(np.array(pil_img), cv2.COLOR_RGB2BGR)

    def on_writing_stopped(self):
        logger.info("Writing stopped detected. Triggering VLM analysis...")
        self.update_status("🔵 Processing OCR…")
        self.vlm_processing = True

        vlm_thread = threading.Thread(target=self.process_with_vlm, daemon=True)
        vlm_thread.start()

    def capture_solution_canvas(self):
        logger.info("Using maintained PIL image for VLM processing")
        return self.solution_pil_image

    def process_with_vlm(self):
        try:
            if not self.question_image_path:
                logger.error("Question image not available!")
                self.root.after(0, self.add_feedback_to_display, "Error: Question image missing")
                self.vlm_processing = False
                return

            logger.info("Capturing solution canvas…")
            solution_image = self.capture_solution_canvas()
            logger.info(f"Solution captured: {solution_image.size}")

            prompt = (
                "You will receive two images. "
                "The FIRST image is the QUESTION/PROBLEM. "
                "The SECOND image is the SOLUTION/ANSWER written by the user. "
                "Analyze whether the SOLUTION correctly solves the QUESTION. "
                "Evaluate each step logically and mathematically — check signs, arithmetic, factorization, substitutions, and final answers. "
                "If the solution appears INCOMPLETE but the steps so far are correct and consistent with the question, "
                "respond that the intermediate steps are correct so far and more work is needed, "
                "and set correctness to true. "
                "Only mark correctness as false if there are genuine mistakes or inconsistencies. "
                "Respond ONLY in strict JSON format as below — no markdown or extra text:\n"
                "{\"feedback\": \"concise feedback under 100 words\", \"correctness\": true/false}"
            )

            with open(self.question_image_path, "rb") as q_file:
                question_data = q_file.read()

            solution_data = io.BytesIO()
            solution_image.save(solution_data, format='PNG')
            solution_data = solution_data.getvalue()

            model = genai.GenerativeModel("gemini-2.5-flash")
            response = model.generate_content(
                [
                    prompt,
                    {"mime_type": "image/png", "data": question_data},
                    {"mime_type": "image/png", "data": solution_data}
                ]
            )

            feedback_text = response.text.strip()

            try:
                json_start = feedback_text.find("{")
                json_end = feedback_text.rfind("}") + 1
                if json_start != -1 and json_end > json_start:
                    feedback_json = json.loads(feedback_text[json_start:json_end])
                else:
                    feedback_json = {"feedback": feedback_text, "correctness": None}
            except json.JSONDecodeError:
                feedback_json = {"feedback": feedback_text, "correctness": None}

            logger.info(f"VLM Response: {json.dumps(feedback_json, indent=2)}")

            self.log_feedback(feedback_json)

            self.root.after(0, self.display_vlm_feedback, feedback_json)

        except Exception as e:
            logger.error(f"VLM processing error: {e}")
            error_msg = f"Error: {str(e)}"
            self.root.after(0, self.add_feedback_to_display, error_msg)

        finally:
            self.vlm_processing = False
            self.update_status("⚪ Waiting for user input…")

    def display_vlm_feedback(self, feedback_json):
        feedback = feedback_json.get("feedback", "No feedback")
        correctness = feedback_json.get("correctness", None)

        color = "#00AA00" if correctness is True else "#FF0000" if correctness is False else "#FFA500"
        correctness_str = "✓ Correct" if correctness is True else "✗ Incorrect" if correctness is False else "? Unknown"

        display_text = f"{correctness_str}\n\n{feedback}"
        self.add_feedback_to_display(display_text)

        if self.last_stroke_bbox:
            self.render_overlay(feedback, color, correctness)

    def render_overlay(self, feedback_text, color, correctness):
        if self.overlay_canvas_id:
            self.solution_canvas.delete(self.overlay_canvas_id)

        overlay_x = 10
        overlay_y = self.lowest_y + 30
        max_box_width = 600
        min_box_width = 200

        wrapped_lines = self.wrap_text(feedback_text, max_box_width)

        if not wrapped_lines:
            wrapped_lines = [feedback_text]

        estimated_line_width = max(len(line) * 7 for line in wrapped_lines) if wrapped_lines else 150
        box_width = min(max_box_width, max(min_box_width, estimated_line_width + 20))
        box_height = len(wrapped_lines) * 20 + 20

        self.solution_canvas.create_rectangle(
            overlay_x, overlay_y, overlay_x + box_width, overlay_y + box_height,
            fill=color, outline="black", width=2,
            tags="overlay"
        )

        text_y = overlay_y + 10
        for line in wrapped_lines:
            self.solution_canvas.create_text(
                overlay_x + 10, text_y,
                text=line, font=("Arial", 9), fill="white",
                anchor="nw", width=box_width - 20,
                tags="overlay"
            )
            text_y += 20

        self.overlay_canvas_id = "overlay"

    def wrap_text(self, text, max_width):
        words = text.split()
        lines = []
        current_line = []

        for word in words:
            current_line.append(word)
            line_text = ' '.join(current_line)

            estimated_width = len(line_text) * 7

            if estimated_width > max_width - 30:
                if len(current_line) > 1:
                    current_line.pop()
                    lines.append(' '.join(current_line))
                    current_line = [word]
                else:
                    lines.append(line_text)
                    current_line = []

        if current_line:
            lines.append(' '.join(current_line))

        return lines if lines else [text]

    def fade_out_overlay(self):
        if self.overlay_canvas_id:
            self.solution_canvas.delete(self.overlay_canvas_id)
            self.overlay_canvas_id = None

    def log_feedback(self, feedback_json):
        try:
            log_entry = {
                "timestamp": datetime.now().isoformat() + "Z",
                "question_image": os.path.basename(self.question_image_path) if self.question_image_path else None,
                "feedback": feedback_json.get("feedback", ""),
                "correctness": feedback_json.get("correctness", None)
            }
            with open(self.feedback_log_file, "a") as f:
                f.write(json.dumps(log_entry) + "\n")
            logger.info(f"Feedback logged: {log_entry}")
        except Exception as e:
            logger.error(f"Failed to log feedback: {e}")

    def on_closing(self):
        self.stop_monitor = True
        if self.monitor_thread:
            self.monitor_thread.join(timeout=1)

        if self.question_image_path and os.path.exists(self.question_image_path):
            try:
                os.remove(self.question_image_path)
            except:
                pass

        self.root.destroy()


def launch_whiteboard():
    """
    Launch Whiteboard Canvas Mode
    Called from vlm_studio_launcher.py
    Creates a new Toplevel window for the whiteboard
    """
    root = tk.Toplevel()
    root.title("VLM Studio – Whiteboard Canvas Mode")
    app = SmartWhiteboardVLMDual(root)
    root.protocol("WM_DELETE_WINDOW", app.on_closing)


if __name__ == "__main__":
    root = tk.Tk()
    app = SmartWhiteboardVLMDual(root)
    root.protocol("WM_DELETE_WINDOW", app.on_closing)
    root.mainloop()