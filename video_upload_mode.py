"""
Video Upload Mode
Allows users to upload video files for batch analysis and processing
"""

import tkinter as tk
from tkinter import filedialog, messagebox
import cv2
import threading
import logging
import os
from pathlib import Path

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

API_KEY = "AIzaSyDWkTV9jzPXj0AmKrKhG5hFf9vMw5_zWeY"
if not API_KEY:
    logger.warning("GEMINI_API_KEY environment variable not set. VLM features will be unavailable.")


class VideoUploadMode:
    def __init__(self, root):
        self.root = root
        self.root.title("VLM Studio – Video Upload Mode")
        self.root.geometry("900x600")
        
        self.selected_file = None
        self.video_info = None
        self.processing = False
        
        self.setup_ui()
    
    def setup_ui(self):
        """Build the video upload mode UI"""
        # Main container
        main_frame = tk.Frame(self.root, bg="#f9fafb")
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Header
        header_frame = tk.Frame(main_frame, bg="#f9fafb")
        header_frame.pack(fill=tk.X, pady=(0, 15))
        
        title_label = tk.Label(
            header_frame,
            text="🎞️ Video Upload Mode",
            font=("Segoe UI", 16, "bold"),
            bg="#f9fafb",
            fg="#1a202c"
        )
        title_label.pack(anchor=tk.W)
        
        info_label = tk.Label(
            header_frame,
            text="Upload and analyze video recordings for batch processing with Gemini VLM",
            font=("Segoe UI", 10),
            bg="#f9fafb",
            fg="#718096"
        )
        info_label.pack(anchor=tk.W, pady=(3, 0))
        
        # Content frame
        content_frame = tk.Frame(main_frame, bg="white", relief=tk.RIDGE, bd=1)
        content_frame.pack(fill=tk.BOTH, expand=True, pady=10, padx=0)
        
        # File selection section
        file_section = tk.Frame(content_frame, bg="white")
        file_section.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        select_label = tk.Label(
            file_section,
            text="Step 1: Select Video File",
            font=("Segoe UI", 12, "bold"),
            bg="white",
            fg="#1a202c"
        )
        select_label.pack(anchor=tk.W, pady=(0, 10))
        
        file_types_label = tk.Label(
            file_section,
            text="Supported formats: .mp4, .avi, .mov, .mkv, .flv, .wmv",
            font=("Segoe UI", 9),
            bg="white",
            fg="#718096"
        )
        file_types_label.pack(anchor=tk.W, pady=(0, 15))
        
        button_frame = tk.Frame(file_section, bg="white")
        button_frame.pack(fill=tk.X, pady=10)
        
        self.select_btn = tk.Button(
            button_frame,
            text="📁 Choose Video File",
            command=self.select_video_file,
            bg="#FF9800",
            fg="white",
            font=("Segoe UI", 11, "bold"),
            padx=20,
            pady=12,
            relief=tk.RAISED,
            bd=2
        )
        self.select_btn.pack(side=tk.LEFT, padx=5)
        
        # File info section
        self.file_info_frame = tk.Frame(content_frame, bg="white")
        self.file_info_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        self.file_info_label = tk.Label(
            self.file_info_frame,
            text="No file selected",
            font=("Segoe UI", 10),
            bg="white",
            fg="#888888",
            justify=tk.LEFT,
            wraplength=500
        )
        self.file_info_label.pack(anchor=tk.W)
        
        # Analysis section
        analysis_label = tk.Label(
            file_section,
            text="Step 2: Analyze Video",
            font=("Segoe UI", 12, "bold"),
            bg="white",
            fg="#1a202c"
        )
        analysis_label.pack(anchor=tk.W, pady=(20, 10))
        
        self.analyze_btn = tk.Button(
            button_frame,
            text="🤖 Start Analysis",
            command=self.start_analysis,
            bg="#4CAF50",
            fg="white",
            font=("Segoe UI", 11, "bold"),
            padx=20,
            pady=12,
            relief=tk.RAISED,
            bd=2,
            state=tk.DISABLED
        )
        self.analyze_btn.pack(side=tk.LEFT, padx=5)
        
        # Output section
        output_section = tk.Frame(main_frame, bg="#f9fafb")
        output_section.pack(fill=tk.BOTH, expand=True, padx=0, pady=10)
        
        output_label = tk.Label(
            output_section,
            text="Console Output:",
            font=("Segoe UI", 10, "bold"),
            bg="#f9fafb",
            fg="#1a202c"
        )
        output_label.pack(anchor=tk.W, pady=(0, 5))
        
        # Output text widget with scrollbar
        scrollbar = tk.Scrollbar(output_section)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.output_text = tk.Text(
            output_section,
            height=8,
            font=("Courier New", 9),
            bg="#263238",
            fg="#80CBC4",
            yscrollcommand=scrollbar.set
        )
        self.output_text.pack(fill=tk.BOTH, expand=True)
        scrollbar.config(command=self.output_text.yview)
        
        # Status bar
        status_frame = tk.Frame(main_frame, bg="#eceff1", relief=tk.SUNKEN, bd=1)
        status_frame.pack(fill=tk.X)
        
        self.status_label = tk.Label(
            status_frame,
            text="⚪ Ready to select video",
            font=("Segoe UI", 9),
            bg="#eceff1",
            fg="#00897b"
        )
        self.status_label.pack(anchor=tk.W, padx=10, pady=5)
    
    def select_video_file(self):
        """Open file dialog to select a video file"""
        file_types = [
            ("Video Files", "*.mp4 *.avi *.mov *.mkv *.flv *.wmv"),
            ("MP4 Files", "*.mp4"),
            ("AVI Files", "*.avi"),
            ("All Files", "*.*")
        ]
        
        filename = filedialog.askopenfilename(
            title="Select a video file",
            filetypes=file_types
        )
        
        if filename:
            self.selected_file = filename
            self.analyze_selected_file()
    
    def analyze_selected_file(self):
        """Analyze properties of selected video file"""
        if not self.selected_file:
            return
        
        try:
            # Get file info
            file_path = Path(self.selected_file)
            file_size_mb = file_path.stat().st_size / (1024 * 1024)
            
            # Get video info using OpenCV
            cap = cv2.VideoCapture(self.selected_file)
            frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            fps = cap.get(cv2.CAP_PROP_FPS)
            width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            duration_seconds = frame_count / fps if fps > 0 else 0
            cap.release()
            
            # Format duration
            minutes = int(duration_seconds) // 60
            seconds = int(duration_seconds) % 60
            duration_str = f"{minutes}m {seconds}s"
            
            # Update file info display
            info_text = (
                f"📄 File: {file_path.name}\n"
                f"📊 Size: {file_size_mb:.2f} MB\n"
                f"🎬 Resolution: {width}x{height}px\n"
                f"⏱️  Duration: {duration_str} ({frame_count} frames at {fps:.2f} fps)\n"
                f"📍 Path: {self.selected_file}"
            )
            
            self.file_info_label.config(text=info_text, fg="#1a202c")
            self.video_info = {
                "path": self.selected_file,
                "filename": file_path.name,
                "size_mb": file_size_mb,
                "frame_count": frame_count,
                "fps": fps,
                "width": width,
                "height": height,
                "duration_seconds": duration_seconds
            }
            
            # Enable analysis button
            self.analyze_btn.config(state=tk.NORMAL)
            self.update_status("✓ Video loaded successfully")
            
            logger.info(f"Video loaded: {info_text.replace(chr(10), ' | ')}")
        
        except Exception as e:
            logger.error(f"Error analyzing video: {e}")
            self.file_info_label.config(text=f"❌ Error: {e}", fg="#f44336")
            self.update_status(f"❌ Error: {e}")
            messagebox.showerror("Video Error", f"Failed to analyze video:\n{e}")
    
    def start_analysis(self):
        """Start analyzing the video"""
        if not self.selected_file or not self.video_info:
            messagebox.showwarning("No Video", "Please select a video file first")
            return
        
        if self.processing:
            messagebox.showinfo("Processing", "Analysis already in progress")
            return
        
        # Show processing message
        self.processing = True
        self.analyze_btn.config(state=tk.DISABLED)
        self.select_btn.config(state=tk.DISABLED)
        
        self.update_status("🔵 Analyzing video with Gemini VLM...")
        self.add_output_line("=" * 60)
        self.add_output_line(f"Starting analysis of: {self.video_info['filename']}")
        self.add_output_line("=" * 60)
        
        # Simulate processing in a thread
        analysis_thread = threading.Thread(target=self.process_video, daemon=True)
        analysis_thread.start()
    
    def process_video(self):
        """Process video (placeholder for VLM integration)"""
        try:
            # Simulate frame-by-frame processing
            frame_count = self.video_info['frame_count']
            
            self.add_output_line(f"\n📊 Video Analysis Report")
            self.add_output_line(f"File: {self.video_info['filename']}")
            self.add_output_line(f"Size: {self.video_info['size_mb']:.2f} MB")
            self.add_output_line(f"Resolution: {self.video_info['width']}x{self.video_info['height']}")
            self.add_output_line(f"Duration: {int(self.video_info['duration_seconds'])}s")
            self.add_output_line(f"Frame Count: {frame_count}")
            self.add_output_line(f"FPS: {self.video_info['fps']:.2f}")
            
            # TODO: Implement actual VLM analysis
            self.add_output_line("\n🤖 VLM Analysis (TODO):")
            self.add_output_line("- Frame sampling: Would extract key frames from video")
            self.add_output_line("- Problem detection: Would identify math problems")
            self.add_output_line("- Solution validation: Would verify correctness")
            self.add_output_line("- Feedback generation: Would provide Gemini-powered feedback")
            
            self.add_output_line("\n✓ Analysis complete!")
            self.root.after(0, self.finish_analysis)
        
        except Exception as e:
            logger.error(f"Error processing video: {e}")
            self.add_output_line(f"\n❌ Error during processing: {e}")
            self.root.after(0, self.finish_analysis)
    
    def finish_analysis(self):
        """Finish analysis and re-enable buttons"""
        self.processing = False
        self.analyze_btn.config(state=tk.NORMAL)
        self.select_btn.config(state=tk.NORMAL)
        self.update_status("✓ Analysis complete!")
        messagebox.showinfo(
            "Analysis Complete",
            f"Video analysis complete!\n\n"
            f"Gemini VLM integration coming soon.\n"
            f"Check console output above for details."
        )
    
    def add_output_line(self, text):
        """Add a line to console output"""
        def _add():
            self.output_text.config(state=tk.NORMAL)
            self.output_text.insert(tk.END, text + "\n")
            self.output_text.see(tk.END)
            self.output_text.config(state=tk.DISABLED)
        
        self.root.after(0, _add)
    
    def update_status(self, message):
        """Update status bar"""
        self.status_label.config(text=message)
        self.root.update_idletasks()
    
    def on_closing(self):
        """Clean up and close"""
        if self.processing:
            response = messagebox.askyesno(
                "Processing",
                "Analysis is in progress. Close anyway?"
            )
            if not response:
                return
        self.root.destroy()


def launch_video_upload():
    """
    Launch Video Upload Mode
    Called from vlm_studio_launcher.py
    """
    root = tk.Toplevel()
    app = VideoUploadMode(root)
    root.protocol("WM_DELETE_WINDOW", app.on_closing)


if __name__ == "__main__":
    root = tk.Tk()
    app = VideoUploadMode(root)
    root.protocol("WM_DELETE_WINDOW", app.on_closing)
    root.mainloop()
