"""
VLM Studio – Mode Selector Launcher
Main entry point for the Digital Whiteboard VLM system
Enables users to choose between operational modes:
1. Mathematics Solving (Whiteboard Canvas + Video Solver)
2. Ukulele/Guitar Tutor (Live Tutor + Upload Video)
"""

import tkinter as tk
from tkinter import ttk
import subprocess
import sys
import os
import logging
from pathlib import Path
import threading

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Get the directory where this script is located
SCRIPT_DIR = Path(__file__).parent.resolve()


class VLMStudioLauncher:
    def __init__(self, root):
        self.root = root
        self.root.title("VLM Studio – Mode Selector")
        self.root.geometry("600x380")
        self.root.resizable(False, False)
        self.root.configure(bg="#f9fafb")

        # Configure style for modern look
        self.setup_styles()

        # Build UI
        self.setup_ui()

    def setup_styles(self):
        """Configure ttk styles for modern appearance"""
        style = ttk.Style()
        style.theme_use('clam')

        # Custom button style
        style.configure(
            'Mode.TButton',
            font=("Segoe UI", 11, "bold"),
            padding=15,
            background="#ffffff"
        )

        # Label styles
        style.configure(
            'Title.TLabel',
            font=("Segoe UI", 18, "bold"),
            background="#f9fafb",
            foreground="#1a202c"
        )

        style.configure(
            'Subtitle.TLabel',
            font=("Segoe UI", 10),
            background="#f9fafb",
            foreground="#718096"
        )

        style.configure(
            'Footer.TLabel',
            font=("Segoe UI", 9),
            background="#f9fafb",
            foreground="#a0aec0"
        )

    def setup_ui(self):
        """Build the launcher UI"""
        # Main container
        main_frame = ttk.Frame(self.root, padding="40")
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Header
        header_frame = ttk.Frame(main_frame)
        header_frame.pack(fill=tk.X, pady=(0, 20))

        title_label = ttk.Label(
            header_frame,
            text="VLM Studio",
            style="Title.TLabel"
        )
        title_label.pack(anchor=tk.W)

        subtitle_label = ttk.Label(
            header_frame,
            text="Select Operation Mode",
            style="Subtitle.TLabel"
        )
        subtitle_label.pack(anchor=tk.W, pady=(5, 0))

        # Scrollable mode buttons container
        canvas = tk.Canvas(main_frame, bg="#f9fafb", highlightthickness=0, height=220)
        scrollbar = ttk.Scrollbar(main_frame, orient="vertical", command=canvas.yview)

        scrollable_frame = ttk.Frame(canvas)
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        # Pack canvas and scrollbar
        canvas.pack(side="left", fill=tk.BOTH, expand=True)
        scrollbar.pack(side="right", fill="y")

        # Enable mouse wheel scrolling
        def on_mousewheel(event):
            canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

        canvas.bind_all("<MouseWheel>", on_mousewheel)

        # Mode buttons container (inside scrollable frame)
        buttons_frame = ttk.Frame(scrollable_frame)
        buttons_frame.pack(fill=tk.BOTH, expand=True, pady=10)

        # Mathematics Solving Mode Button
        self.create_mode_button(
            buttons_frame,
            "🧮  Mathematics Solving",
            "Whiteboard canvas or video solver with real-time Gemini feedback",
            self.start_math_mode,
            0
        )

        # Ukulele/Guitar Tutor Mode Button
        self.create_mode_button(
            buttons_frame,
            "🎸  Ukulele/Guitar Tutor",
            "Live analysis or upload video for annotation",
            self.start_guitar_tutor_mode,
            1
        )

        # Footer (outside main_frame for fixed positioning)
        footer_frame = ttk.Frame(self.root)
        footer_frame.pack(fill=tk.X, side=tk.BOTTOM, pady=10)

        footer_label = ttk.Label(
            footer_frame,
            text="🚀 Gemini 2.5 Flash Powered Learning Assistant",
            style="Footer.TLabel"
        )
        footer_label.pack()

    def create_mode_button(self, parent, title, description, command, row):
        """Create a styled mode selection button"""
        button_frame = ttk.Frame(parent)
        button_frame.pack(fill=tk.X, pady=10)

        button = ttk.Button(
            button_frame,
            text=title,
            command=command,
            style="Mode.TButton",
            width=50
        )
        button.pack(fill=tk.X, ipady=8)

        desc_label = ttk.Label(
            button_frame,
            text=description,
            style="Subtitle.TLabel"
        )
        desc_label.pack(anchor=tk.W, pady=(5, 0))

    def start_math_mode(self):
        """Show sub-options for Mathematics Solving"""
        logger.info("Showing Mathematics Solving options...")
        self.show_math_options()

    def show_math_options(self):
        """Display options dialog for Whiteboard Canvas vs Video Solver"""
        option_window = tk.Toplevel(self.root)
        option_window.title("Mathematics Solving")
        option_window.geometry("550x400")
        option_window.resizable(False, False)
        option_window.configure(bg="#f9fafb")

        # Center on parent
        option_window.transient(self.root)
        option_window.grab_set()

        main_frame = ttk.Frame(option_window, padding="40")
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Title
        title_label = ttk.Label(
            main_frame,
            text="Mathematics Solving",
            style="Title.TLabel"
        )
        title_label.pack(anchor=tk.W, pady=(0, 10))

        subtitle_label = ttk.Label(
            main_frame,
            text="Choose mode of operation",
            style="Subtitle.TLabel"
        )
        subtitle_label.pack(anchor=tk.W, pady=(0, 30))

        # Whiteboard Canvas Button
        canvas_button = ttk.Button(
            main_frame,
            text="✏️  Whiteboard Canvas",
            command=lambda: self.launch_whiteboard_canvas(option_window),
            style="Mode.TButton",
            width=45
        )
        canvas_button.pack(fill=tk.X, ipady=8, pady=(0, 10))

        canvas_desc = ttk.Label(
            main_frame,
            text="Draw problems and solutions with real-time Gemini feedback",
            style="Subtitle.TLabel"
        )
        canvas_desc.pack(anchor=tk.W, pady=(0, 20))

        # Video Solver Button
        video_button = ttk.Button(
            main_frame,
            text="🎞️  Video Solver",
            command=lambda: self.launch_math_video_solver(option_window),
            style="Mode.TButton",
            width=45
        )
        video_button.pack(fill=tk.X, ipady=8, pady=(0, 10))

        video_desc = ttk.Label(
            main_frame,
            text="Upload a video file for mathematical problem analysis",
            style="Subtitle.TLabel"
        )
        video_desc.pack(anchor=tk.W)

    def launch_whiteboard_canvas(self, option_window):
        """Launch Whiteboard Canvas Mode in background thread"""
        option_window.destroy()
        logger.info("Launching Whiteboard Canvas Mode...")
        try:
            # Launch in background thread so launcher stays open
            thread = threading.Thread(target=self._run_whiteboard, daemon=True)
            thread.start()
        except Exception as e:
            logger.error(f"Failed to launch Whiteboard mode: {e}")
            self.show_error_dialog("Whiteboard Mode Error", str(e))

    def _run_whiteboard(self):
        """Run whiteboard in background thread"""
        try:
            import smart_whiteboard_vlm_dual as wb
            wb.launch_whiteboard()
            logger.info("Whiteboard mode closed")
        except Exception as e:
            logger.error(f"Whiteboard mode error: {e}")

    def launch_math_video_solver(self, option_window):
        """Launch math video solver mode"""
        option_window.destroy()
        logger.info("Launching Math Video Solver...")
        try:
            import math_solver as ms
            ms.launch_video_upload_mode()
            logger.info("math video solver done.")
            # logger.warning("Math Video Solver not yet implemented")
            # self.show_error_dialog("Not Implemented", "Math Video Solver functionality will be added here.")
        except Exception as e:
            logger.error(f"Failed to launch Math Video Solver: {e}")
            self.show_error_dialog("Math Video Solver Error", str(e))

    def start_guitar_tutor_mode(self):
        """Show sub-options for Guitar/Ukulele Tutor"""
        logger.info("Showing Guitar/Ukulele Tutor options...")
        self.show_tutor_options()

    def show_tutor_options(self):
        """Display options dialog for Live vs Upload"""
        option_window = tk.Toplevel(self.root)
        option_window.title("Ukulele/Guitar Tutor")
        option_window.geometry("550x400")
        option_window.resizable(False, False)
        option_window.configure(bg="#f9fafb")

        # Center on parent
        option_window.transient(self.root)
        option_window.grab_set()

        main_frame = ttk.Frame(option_window, padding="40")
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Title
        title_label = ttk.Label(
            main_frame,
            text="Ukulele/Guitar Tutor",
            style="Title.TLabel"
        )
        title_label.pack(anchor=tk.W, pady=(0, 10))

        subtitle_label = ttk.Label(
            main_frame,
            text="Choose mode of operation",
            style="Subtitle.TLabel"
        )
        subtitle_label.pack(anchor=tk.W, pady=(0, 30))

        # Live Tutor Button
        live_button = ttk.Button(
            main_frame,
            text="📹  Live Tutor",
            command=lambda: self.launch_live_tutor(option_window),
            style="Mode.TButton",
            width=45
        )
        live_button.pack(fill=tk.X, ipady=8, pady=(0, 10))

        live_desc = ttk.Label(
            main_frame,
            text="Analyze guitar/ukulele chords in real-time via webcam",
            style="Subtitle.TLabel"
        )
        live_desc.pack(anchor=tk.W, pady=(0, 20))

        # Upload Video Button
        upload_button = ttk.Button(
            main_frame,
            text="🎞️  Upload Video",
            command=lambda: self.launch_video_upload(option_window),
            style="Mode.TButton",
            width=45
        )
        upload_button.pack(fill=tk.X, ipady=8, pady=(0, 10))

        upload_desc = ttk.Label(
            main_frame,
            text="Upload a video file for chord annotation and analysis",
            style="Subtitle.TLabel"
        )
        upload_desc.pack(anchor=tk.W)

    def launch_live_tutor(self, option_window):
        """Launch live camera tutor"""
        option_window.destroy()
        logger.info("Launching Live Tutor...")
        try:
            import gc6
            gc6.main()
            logger.info("Live tutor launched successfully")
        except Exception as e:
            logger.error(f"Failed to launch Live Tutor: {e}")
            self.show_error_dialog("Live Tutor Error", str(e))

    def launch_video_upload(self, option_window):
        """Launch video upload mode"""
        option_window.destroy()
        logger.info("Launching Video Upload...")
        try:
            import f1_guitar
            f1_guitar.launch_video_upload_mode()
            logger.info("Video upload launched successfully")
        except Exception as e:
            logger.error(f"Failed to launch Video Upload: {e}")
            self.show_error_dialog("Video Upload Error", str(e))

    def show_error_dialog(self, title, message):
        """Display an error message"""
        from tkinter import messagebox
        messagebox.showerror(title, f"Error: {message}")


def main():
    """Main entry point"""
    root = tk.Tk()
    app = VLMStudioLauncher(root)
    root.mainloop()


if __name__ == "__main__":
    main()