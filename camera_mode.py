"""
Camera Live Feed Mode
Displays real-time webcam feed for handwriting and problem analysis
"""

import tkinter as tk
from tkinter import messagebox
import cv2
from PIL import Image, ImageTk
import threading
import logging
import os

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

API_KEY = "AIzaSyDWkTV9jzPXj0AmKrKhG5hFf9vMw5_zWeY"
if not API_KEY:
    logger.warning("GEMINI_API_KEY environment variable not set. VLM features will be unavailable.")


class CameraLiveMode:
    def __init__(self, root):
        self.root = root
        self.root.title("VLM Studio – Camera Live Feed Mode")
        self.root.geometry("1000x700")
        
        self.capture = None
        self.camera_thread = None
        self.stop_camera = False
        self.current_frame = None
        
        self.setup_ui()
        self.start_camera()
    
    def setup_ui(self):
        """Build the camera mode UI"""
        # Main container
        main_frame = tk.Frame(self.root, bg="#f9fafb")
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Header
        header_frame = tk.Frame(main_frame, bg="#f9fafb")
        header_frame.pack(fill=tk.X, pady=(0, 15))
        
        title_label = tk.Label(
            header_frame,
            text="📷 Camera Live Feed",
            font=("Segoe UI", 16, "bold"),
            bg="#f9fafb",
            fg="#1a202c"
        )
        title_label.pack(anchor=tk.W)
        
        info_label = tk.Label(
            header_frame,
            text="Real-time webcam analysis for handwriting recognition and math problem solving",
            font=("Segoe UI", 10),
            bg="#f9fafb",
            fg="#718096"
        )
        info_label.pack(anchor=tk.W, pady=(3, 0))
        
        # Content frame
        content_frame = tk.Frame(main_frame, bg="white", relief=tk.RIDGE, bd=1)
        content_frame.pack(fill=tk.BOTH, expand=True, pady=10)
        
        # Video feed frame
        video_frame = tk.Frame(content_frame, bg="black")
        video_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        self.video_label = tk.Label(
            video_frame,
            bg="black",
            fg="white",
            font=("Segoe UI", 12),
            text="Initializing camera..."
        )
        self.video_label.pack(fill=tk.BOTH, expand=True)
        
        # Control panel
        control_frame = tk.Frame(main_frame, bg="#f9fafb")
        control_frame.pack(fill=tk.X, pady=10)
        
        self.capture_btn = tk.Button(
            control_frame,
            text="📸 Capture Frame",
            command=self.capture_frame,
            bg="#4CAF50",
            fg="white",
            font=("Segoe UI", 11, "bold"),
            padx=20,
            pady=10,
            relief=tk.RAISED,
            bd=2
        )
        self.capture_btn.pack(side=tk.LEFT, padx=5)
        
        self.analyze_btn = tk.Button(
            control_frame,
            text="🤖 Analyze Frame (TODO)",
            command=self.analyze_frame,
            bg="#2196F3",
            fg="white",
            font=("Segoe UI", 11, "bold"),
            padx=20,
            pady=10,
            relief=tk.RAISED,
            bd=2,
            state=tk.DISABLED
        )
        self.analyze_btn.pack(side=tk.LEFT, padx=5)
        
        close_btn = tk.Button(
            control_frame,
            text="❌ Close",
            command=self.on_closing,
            bg="#f44336",
            fg="white",
            font=("Segoe UI", 11, "bold"),
            padx=20,
            pady=10,
            relief=tk.RAISED,
            bd=2
        )
        close_btn.pack(side=tk.RIGHT, padx=5)
        
        # Status bar
        status_frame = tk.Frame(main_frame, bg="#eceff1", relief=tk.SUNKEN, bd=1)
        status_frame.pack(fill=tk.X)
        
        self.status_label = tk.Label(
            status_frame,
            text="🟢 Camera ready",
            font=("Segoe UI", 9),
            bg="#eceff1",
            fg="#00897b"
        )
        self.status_label.pack(anchor=tk.W, padx=10, pady=5)
    
    def start_camera(self):
        """Initialize and start camera feed"""
        try:
            self.capture = cv2.VideoCapture(0)
            if not self.capture.isOpened():
                messagebox.showerror("Camera Error", "Unable to open webcam. Please check your camera.")
                self.on_closing()
                return
            
            # Set camera properties
            self.capture.set(cv2.CAP_PROP_FRAME_WIDTH, 800)
            self.capture.set(cv2.CAP_PROP_FRAME_HEIGHT, 600)
            self.capture.set(cv2.CAP_PROP_FPS, 30)
            
            self.update_status("🟢 Camera ready")
            
            # Start camera thread
            self.camera_thread = threading.Thread(target=self.camera_loop, daemon=True)
            self.camera_thread.start()
            logger.info("Camera started successfully")
        except Exception as e:
            logger.error(f"Failed to start camera: {e}")
            messagebox.showerror("Camera Error", f"Error: {e}")
            self.on_closing()
    
    def camera_loop(self):
        """Continuously capture and display frames"""
        while not self.stop_camera:
            try:
                ret, frame = self.capture.read()
                if not ret:
                    logger.warning("Failed to read frame from camera")
                    continue
                
                # Mirror the frame horizontally for better UX
                frame = cv2.flip(frame, 1)
                
                # Store current frame for capture
                self.current_frame = frame.copy()
                
                # Convert to PIL for Tkinter display
                frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                pil_image = Image.fromarray(frame_rgb)
                
                # Resize to fit label if needed
                pil_image.thumbnail((780, 580), Image.Resampling.LANCZOS)
                
                # Convert to PhotoImage
                photo = ImageTk.PhotoImage(pil_image)
                
                # Update label
                self.video_label.config(image=photo)
                self.video_label.image = photo  # Keep a reference
                
            except Exception as e:
                logger.error(f"Error in camera loop: {e}")
                continue
    
    def capture_frame(self):
        """Capture current frame and save it"""
        if self.current_frame is None:
            messagebox.showwarning("Capture Failed", "No frame available to capture")
            return
        
        try:
            import uuid
            filename = f"capture_{uuid.uuid4().hex[:8]}.png"
            cv2.imwrite(filename, self.current_frame)
            self.update_status(f"✓ Frame captured: {filename}")
            messagebox.showinfo("Capture Success", f"Frame saved as:\n{filename}")
            logger.info(f"Frame captured: {filename}")
        except Exception as e:
            logger.error(f"Failed to capture frame: {e}")
            messagebox.showerror("Capture Error", f"Error: {e}")
    
    def analyze_frame(self):
        """Analyze current frame with Gemini VLM (TODO)"""
        if self.current_frame is None:
            messagebox.showwarning("Analysis Failed", "No frame available to analyze")
            return
        
        # TODO: Implement Gemini VLM analysis
        messagebox.showinfo("Analysis", "VLM Analysis Coming Soon!\n\nThis feature will integrate Gemini 2.5 Flash to analyze math problems and handwriting in real-time.")
        logger.info("VLM analysis not yet implemented")
    
    def update_status(self, message):
        """Update status bar"""
        self.status_label.config(text=message)
        self.root.update_idletasks()
    
    def on_closing(self):
        """Clean up and close"""
        self.stop_camera = True
        if self.capture:
            self.capture.release()
        if self.camera_thread:
            self.camera_thread.join(timeout=2)
        self.root.destroy()


def launch_camera():
    """
    Launch Camera Live Feed Mode
    Called from vlm_studio_launcher.py
    """
    root = tk.Toplevel()
    app = CameraLiveMode(root)
    root.protocol("WM_DELETE_WINDOW", app.on_closing)


if __name__ == "__main__":
    root = tk.Tk()
    app = CameraLiveMode(root)
    root.protocol("WM_DELETE_WINDOW", app.on_closing)
    root.mainloop()
