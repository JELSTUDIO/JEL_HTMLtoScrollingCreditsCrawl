import os
import subprocess
import threading
import time
import math
from datetime import datetime
from tkinter import Tk, Label, Button, filedialog, StringVar, OptionMenu, Entry, Checkbutton, BooleanVar
from tkinter.ttk import Progressbar
from pathlib import Path

# IMPORTS FOR AUDIO HANDLING
try:
    from pydub import AudioSegment
    HAS_AUDIO_SUPPORT = True
except ImportError:
    HAS_AUDIO_SUPPORT = False
    print("Warning: pydub not found. Audio timing feature will be disabled.")


from PIL import Image, ImageDraw, ImageFont
from playwright.sync_api import sync_playwright
from concurrent.futures import ThreadPoolExecutor

# -----------------------------
# CONFIG
# -----------------------------
APP_TITLE = "JELSTUDIO HTMLtoScrollingCreditsCrawl v1.4.3"

VIDEO_SIZES = {
    "480p (640x480)": (640, 480),
    "720p (1280x720)": (1280, 720),
    "1080p (1920x1080)": (1920, 1080),
    "1440p (2560x1440)": (2560, 1440),
    "4K (3840x2160)": (3840, 2160),
    "DCI 2K (2048x1080)": (2048, 1080),
    "DCI 4K (4096x2160)": (4096, 2160),
    "21:9 UltraWide (2560x1080)": (2560, 1080),
    "21:9 UltraWide (3440x1440)": (3440, 1440),
    "2.4:1 Cinematic (1920x800)": (1920, 800),
    "2.4:1 Cinematic (3840x1600)": (3840, 1600)
}

FPS_OPTIONS = [16, 24, 30, 48, 50, 60, 120]
CRF_OPTIONS = [15, 18, 20, 23]
PRESETS = ["slow", "medium", "fast"]
CODECS = ["H264", "ProRes"]
GPU_OPTIONS = ["CPU", "NVIDIA (NVENC)"]

# FIXED TIME DEFINITIONS
COUNTDOWN_TIME = 5.0
PADDING_TIME = 5.0

MaxCPUcoresToUseToPreventDiskThrashing = 8

cpu_cores = os.cpu_count()

if cpu_cores >= 18:
    recommendation = "CPU cores >= 18"
elif cpu_cores >= 12:
    recommendation = "CPU cores >= 12"
elif cpu_cores >= 6:
    recommendation = "CPU cores >= 6"
else:
    recommendation = "CPU cores < 6"


# -----------------------------
# playwright and PIL helper
# -----------------------------

def parse_css_color(css_color):
    if css_color.startswith("rgb"):
        nums = css_color.replace("rgb(", "").replace(")", "").split(",")
        return tuple(int(n.strip()) for n in nums[:3])
    elif css_color.startswith("rgba"):
        nums = css_color.replace("rgba(", "").replace(")", "").split(",")
        return tuple(int(n.strip()) for n in nums[:3])
    elif css_color == "transparent":
        return (0, 0, 0) # Default fallback to black
    return (0, 0, 0) # Fallback as tuple for consistency

# -----------------------------
# AUDIO UTILITY
# --------------------------------
def get_audio_duration(audio_path):
    """Reads an audio file and returns its duration in seconds."""
    if not HAS_AUDIO_SUPPORT:
        return None
    
    try:
        # pydub handles MP3, WAV, OGG, etc., provided FFmpeg is installed.
        audio = AudioSegment.from_file(audio_path)
        duration_ms = len(audio)
        return duration_ms / 1000.0  # Convert milliseconds to seconds
    except FileNotFoundError:
        print("Error: FFmpeg not found. Please install it and ensure it is in your system PATH.")
        return None
    except Exception as e:
        print(f"Error loading audio file: {e}")
        return None


# -----------------------------
# HTML RENDER
# -----------------------------

def render_html_fullpage(html_path, output_path, width):
    with sync_playwright() as p:
        browser = p.chromium.launch()
        # Safe path handling for Windows/Playwright
        page_path = Path(html_path).as_uri()
        page = browser.new_page(viewport={"width": width, "height": 1000})
        page.goto(page_path)

        full_height = page.evaluate("document.body.scrollHeight")
        bg_color = page.evaluate("getComputedStyle(document.body).backgroundColor")
        bg_color = parse_css_color(bg_color)

        page.set_viewport_size({"width": width, "height": full_height})
        page.screenshot(path=output_path, full_page=True)
        browser.close()

    return bg_color

# -----------------------------
# SCROLL
# -----------------------------

def ease_in_out(t):
    return 3*t**2 - 2*t**3


def render_single_frame(i, total_frames, img, vid_w, vid_h_scaled, use_ease, scroll_range, bg_color, out_dir, start_index):
    t = i / (total_frames - 1) if total_frames > 1 else 0
    if use_ease:
        t = ease_in_out(t)

    y = int(t * scroll_range)

    frame_big = Image.new("RGB", (vid_w, vid_h_scaled), bg_color)
    frame_big.paste(img, (0, vid_h_scaled - y))

    frame = frame_big.resize((vid_w, vid_h_scaled), Image.LANCZOS)

    global_index = start_index + i
    frame.save(os.path.join(out_dir, f"frame_{global_index:06d}.png"))
    

def create_scroll_frames_parallel(image_path, out_dir, video_size, fps, duration, use_ease, bg_color, start_index, progress_cb=None):
    img = Image.open(image_path).convert("RGB")

    # High-res scaling for scrolling image
    scale = 2
    img = img.resize((img.width, img.height * scale), Image.LANCZOS)

    vid_w, vid_h = video_size
    vid_h_scaled = vid_h * scale

    total_frames = int(duration * fps)
    scroll_range = img.height + vid_h_scaled

    cpu_count = os.cpu_count() or 4

    # Removed: existing_frames check
    # Removed: os.listdir loop for robustness

    with ThreadPoolExecutor(max_workers=min(MaxCPUcoresToUseToPreventDiskThrashing, cpu_count)) as executor:
        futures = []
        for i in range(total_frames):
            global_index = start_index + i
            
            futures.append(executor.submit(
                render_single_frame,
                i, total_frames, img, vid_w, vid_h_scaled,
                use_ease, scroll_range, bg_color, out_dir,
                start_index
            ))

        completed = 0
        total_to_render = len(futures)

        for f in futures:
            f.result()
            completed += 1
            if progress_cb:
                progress_cb(completed, total_to_render)

    return start_index + total_frames


# -----------------------------
# COUNTDOWN + END
# -----------------------------

# Define the name of the font file you placed in the same directory
FONT_FILE_NAME = "Roboto-Medium.ttf" # <-- CHANGE THIS to your file name
DESIRED_FONT_SIZE = 150 # <-- ADJUST THIS for desired size

def create_countdown(out_dir, video_size, fps, seconds, bg_color, start_index):
    vid_w, vid_h = video_size
    
    # Try to load the font from the local directory
    try:
        font = ImageFont.truetype(FONT_FILE_NAME, DESIRED_FONT_SIZE)
    except IOError:
        font = ImageFont.load_default()

    frame_index = start_index

    for i in range(int(seconds * fps)):
        sec = seconds - (i // fps)

        frame = Image.new("RGB", (vid_w, vid_h), bg_color)
        draw = ImageDraw.Draw(frame)

        if sec > 2:
            text = str(int(sec))
            bbox = draw.textbbox((0,0), text, font=font)
            w, h = bbox[2]-bbox[0], bbox[3]-bbox[1]
            # Draw 4 versions of text for a "shimmer" effect
            draw.text(((vid_w-w)//2 - 100, (vid_h-h)//2 - 100), text, fill="white", font=font)
            draw.text(((vid_w-w)//2 + 100, (vid_h-h)//2 - 100), text, fill="orange", font=font)
            draw.text(((vid_w-w)//2 - 100, (vid_h-h)//2 + 100), text, fill="black", font=font)
            draw.text(((vid_w-w)//2 + 100, (vid_h-h)//2 + 100), text, fill="cyan", font=font)

        global_index = start_index + i
        frame.save(os.path.join(out_dir, f"frame_{global_index:06d}.png"))
        frame_index += 1

    return frame_index


def create_end_padding(out_dir, video_size, fps, seconds, bg_color, start_index):
    vid_w, vid_h = video_size

    frame_index = start_index

    for _ in range(int(seconds * fps)):
        frame = Image.new("RGB", (vid_w, vid_h), bg_color)
        global_index = start_index + (frame_index - start_index)
        frame.save(os.path.join(out_dir, f"frame_{global_index:06d}.png"))
        frame_index += 1

    return frame_index

# -----------------------------
# FFMPEG
# -----------------------------

def encode_video(frames_dir, audio_path, output, fps, crf, preset, codec, gpu, use_countdown):

    cmd = [
        "ffmpeg", "-y",
        "-framerate", str(fps),
        "-i", os.path.join(frames_dir, "frame_%06d.png"),
    ]

    # Add audio input if present
    if audio_path:
        # -----------------------------------------------------------------
        # >>> Apply Input Time Offset here <<<
        # This tells FFmpeg: When you load this audio file, wait for COUNTDOWN_TIME seconds.
        # Only apply offset if countdown is used
        #if use_countdown:
            #cmd.extend(["-itsoffset", str(COUNTDOWN_TIME)])
        cmd.extend(["-i", audio_path])

    # Video codec
    if codec == "H264":
        if gpu == "NVIDIA (NVENC)":
            cmd.extend([
                "-c:v", "h264_nvenc",
                "-preset", "p5",
            ])
        else:
            cmd.extend([
                "-c:v", "libx264",
                "-crf", str(crf),
                "-preset", preset,
            ])

        cmd.extend(["-pix_fmt", "yuv420p"])

    else:  # ProRes
        cmd.extend([
            "-c:v", "prores_ks",
            "-profile:v", "3",
        ])

    # Stream mapping (ONLY add audio mapping if it exists)
    cmd.extend(["-map", "0:v:0"])

    if audio_path:
        if use_countdown:
            delay_ms = int(COUNTDOWN_TIME * 1000)
            cmd.extend([
                "-filter_complex",
                f"[1:a]adelay={delay_ms}|{delay_ms}[a]"
            ])
            cmd.extend([
                "-map", "0:v:0",
                "-map", "[a]",
                "-c:a", "aac"
            ])
        else:
            cmd.extend([
                "-map", "0:v:0",
                "-map", "1:a:0",
                "-c:a", "aac"
            ])
    else:
        cmd.extend(["-map", "0:v:0"])

    cmd.append(output)

    subprocess.run(cmd, check=True)

# -----------------------------
# GUI
# -----------------------------

class App:
    def __init__(self, root):
        self.root = root
        self.root.minsize(460, 800)  # Set minimum width and height
        root.title(APP_TITLE)

        self.html_path = None
        self.output_video = None
        self.image_root = None
        self.audio_path = None # Path for the music file

        self.size = StringVar(value=list(VIDEO_SIZES.keys())[2])
        self.fps = StringVar(value="24")
        # Duration is now dynamic/calculated
        self.duration = StringVar(value="120") 
        self.crf = StringVar(value="15")
        self.preset = StringVar(value="slow")
        self.codec = StringVar(value="H264")
        self.gpu = StringVar(value="NVIDIA (NVENC)")
        
        self.audio_duration_str = StringVar(value="0.0s (Manual Input)")

        self.use_ease = BooleanVar(value=False)
        self.use_countdown = BooleanVar(value=True)  # Option to skip countdown
        self.keep_images = BooleanVar(value=True)
        self.images_only = BooleanVar(value=False)
        # Removed: self.video_only (Logic moved out)

        # --- File Browsers ---
        Label(root, text="Input HTML File").pack()
        Button(root, text="Browse HTML", command=self.load_html).pack()
        
        Label(root, text="Input Audio File (Optional)").pack()
        Button(root, text="Browse Audio", command=self.load_audio).pack()
        Label(root, textvariable=self.audio_duration_str).pack()

        Label(root, text="Output Video File").pack()
        Button(root, text="Choose Output", command=self.choose_output).pack()

        Label(root, text="Image-Sequence Output Folder").pack()
        Button(root, text="Choose Folder", command=self.choose_folder).pack()

        Label(root, text="Resolution").pack()
        OptionMenu(root, self.size, *VIDEO_SIZES.keys()).pack()

        Label(root, text="FPS").pack()
        OptionMenu(root, self.fps, *FPS_OPTIONS).pack()

        Label(root, text="Scroll Duration (sec) [Manual or Audio Set]").pack()
        Entry(root, textvariable=self.duration).pack()

        Checkbutton(root, text="Use Ease In/Out", variable=self.use_ease).pack()
        Checkbutton(root, text="Use Countdown", variable=self.use_countdown).pack()  
        
        # --- Codec Settings ---
        Label(root, text="Codec").pack()
        OptionMenu(root, self.codec, *CODECS).pack()

        Label(root, text="GPU Encoding").pack()
        OptionMenu(root, self.gpu, *GPU_OPTIONS).pack()

        Label(root, text="CRF (CPU only)").pack()
        OptionMenu(root, self.crf, *CRF_OPTIONS).pack()

        Label(root, text="Preset (CPU)").pack()
        OptionMenu(root, self.preset, *PRESETS).pack()
        
        # --- Options ---
        Checkbutton(root, text="Keep Images", variable=self.keep_images).pack()
        Checkbutton(root, text="Images Only", variable=self.images_only).pack()

        Label(root, text=recommendation).pack()

        self.progress = Progressbar(root, length=420, mode='determinate')
        self.progress.pack()

        self.status = Label(root, text="Idle")
        self.status.pack()

        Button(root, text="Run", command=self.start_thread).pack()

    def load_html(self):
        self.html_path = filedialog.askopenfilename(filetypes=[
            ("HTML", "*.html *.htm"),
            ("All Files", "*.*")
        ])

    def load_audio(self):
        """Handles audio file selection and duration calculation."""
        self.audio_path = filedialog.askopenfilename(filetypes=[
            ("Audio", "*.mp3 *.wav *.flac *.ogg *.aac *.ac3 *.m4a *.aiff *.wma *.au"),
            ("All Files", "*.*")
        ])
        if self.audio_path:
            duration = get_audio_duration(self.audio_path)
            if duration is not None:
                self.audio_duration_str.set(f"{duration:.2f} seconds (Audio Set)")
                # Crucial step: Set the scroll duration to the audio duration
                self.duration.set(f"{duration:.2f}") 
            else:
                self.audio_duration_str.set("Error loading audio.")
                self.audio_path = None
        else:
            self.audio_duration_str.set("0.0s (Manual Input)")
            self.audio_path = None


    def choose_output(self):
        self.output_video = filedialog.asksaveasfilename(defaultextension=".mov")

    def choose_folder(self):
        self.image_root = filedialog.askdirectory()

    def update_progress(self, current, total):
        def _update():
            percent = int((current / total) * 100) if total > 0 else 100
            self.progress['value'] = percent
            self.status.config(text=f"Rendering remaining frames: {percent}%")
        self.root.after(0, _update)
    
    def update_status(self, text):
        """Thread-safe status update"""
        self.root.after(0, lambda: self.status.config(text=text))

    def start_thread(self):
        threading.Thread(target=self.run, daemon=True).start()

    def run(self):
        try:
            # --- Validation ---
            if not self.html_path:
                self.update_status("ERROR: Please select an HTML file.")
                return

            if not self.image_root:
                self.update_status("ERROR: Please select an Image-Sequence Output Folder.")
                return

            # --- Timing Calculation ---
            try:
                scroll_duration = float(self.duration.get())
            except ValueError:
                self.update_status("ERROR: Invalid duration value.")
                return
            
            if self.audio_path and float(self.duration.get()) <= 0:
                 self.update_status("ERROR: Invalid duration calculated from audio.")
                 return
           
        
            if self.audio_path:
                self.update_status(f"Audio length detected: {scroll_duration:.2f}s. Scroll time set to match music.")
            else:
                self.update_status(f"Using manual scroll duration: {scroll_duration:.2f} seconds.")


            # --- Setup ---
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            frames_dir = os.path.join(self.image_root, f"credits_{timestamp}")
            os.makedirs(frames_dir, exist_ok=True)

            size = VIDEO_SIZES[self.size.get()]
            fps = int(self.fps.get())

            frame_index = 0

            # 1. Render HTML (Always run now)
            self.update_status("Rendering HTML...")
            img_path = os.path.join(frames_dir, "full.png")
            bg_color = render_html_fullpage(self.html_path, img_path, size[0])

            # 2. Countdown Phase Seconds
            self.update_status("Countdown Phase...")
            if self.use_countdown.get():
                frame_index = create_countdown(frames_dir, size, fps, COUNTDOWN_TIME, bg_color, frame_index)
            else:
                self.update_status("Skipping Countdown...")
                frame = Image.new("RGB", (size[0], size[1]), bg_color)
                frame.save(os.path.join(frames_dir, f"frame_{frame_index:06d}.png"))
                frame_index += 1

            # 3. Scrolling Content Phase (DYNAMIC)
            self.update_status("Rendering scrolling text frames...")
            frame_index = create_scroll_frames_parallel(
                img_path, frames_dir, size, fps, scroll_duration,
                self.use_ease.get(), bg_color,
                frame_index,
                progress_cb=self.update_progress
            )

            # 4. End Padding Phase Seconds
            self.update_status("End padding...")
            frame_index = create_end_padding(frames_dir, size, fps, PADDING_TIME, bg_color, frame_index)

            # --- Video Encoding (Unless Images Only) ---
            if not self.images_only.get():
                if not self.output_video:
                    self.update_status("ERROR: Please choose output video file.")
                    return
                self.update_status("Encoding video...")
                encode_video(frames_dir, self.audio_path, self.output_video, fps,
                             self.crf.get(), self.preset.get(),
                             self.codec.get(), self.gpu.get(), self.use_countdown.get())

            # --- Cleanup ---
            if not self.keep_images.get():
                self.update_status("Cleaning up images...")
                for f in os.listdir(frames_dir):
                    os.remove(os.path.join(frames_dir, f))
                os.rmdir(frames_dir)

            self.update_status("Done!")

        except Exception as e:
            # Safely report error to GUI
            self.root.after(0, lambda: self.status.config(text=f"CRITICAL ERROR: {str(e)}"))
            print(f"Thread Error: {e}")
            import traceback
            traceback.print_exc()


if __name__ == "__main__":
    if not HAS_AUDIO_SUPPORT:
        print("\n!!! WARNING: pydub is not installed. Audio features will not work. Please install it: pip install pydub")
    
    root = Tk()
    App(root)
    root.mainloop()
