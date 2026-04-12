# JEL_VideoCreditsTextCrawl

## HTML to Scrolling Credits Crawl Video Generator

This project provides a Python-based GUI tool for generating scrolling video sequences from static HTML content.

It renders an HTML file as a full-page image and animates the scroll effect across the image, generating both an image-sequence and a video output configurable for various delivery platforms.

Designing a credits-list in an HTML editor (Such as LibreOffice) allows you to define columns, fonts, colors, images, etc, and is relatively easy.
With this script you can then convert the webpage to an image-sequence (And also a video) where it scrolls/crawls smoothly (Timed to match a sound-track if you want. If you load an audio-file it will be included in the exported video)

### Features

*   **HTML Content Rendering:** Imports content from a source HTML file, rendering it as the canvas.
*   **Animated Scroll:** Implements a smooth scrolling effect across the rendered image.
*   **Audio Timing:** Can load an audio file and dynamically set the scrolling duration to match it (So the scroll-time can match a specific sound-track length). The time of the scroll can also be set manually.
*   **Output Video Configuration:** Supports multiple video resolutions (720P, 1080p, 4K) and encoding parameters (FPS, CRF, Codec (H264 and ProRes)).
*   **Output Image Configuration:** Supports multiple image resolutions (720P, 1080p, 4K) and saves images in lossless PNG format named so they can be loaded directly as a video-sequence in a video-editor.
*   **Encoding Flexibility:** Includes options for CPU-based encoding (libx264) and hardware acceleration (NVENC).
*   **Multi Threaded:** To speed up image and video generation.
*   **GUI Workflow:** Provides a complete graphical interface for parameter selection and process control.

### Technical Specifications

*   **Python Compatibility:** The script should be compatible with Python **3.8** through at least **3.11**, but only Python **3.10** is tested.
*   **Dependencies:** Requires `Playwright` (for HTML rendering), `Pillow` (for image manipulation), and `pydub` (for audio analysis).
*   **External Requirement:** Requires `FFmpeg` to be installed on the system and configured in the system PATH for final video encoding.

### Change-list

- v1.3.0 20260412 Added a user-toggle to switch the countdown ON or OFF. It defaults to ON which means there will be a 5-second countdown sequence in the generated output. Untoggle this to have the crawl and music begin immediately in the generated output.
- v1.3.0 20260410 First version of the script.

### Installation

#### System Prerequisites

- **FFmpeg:** Install FFmpeg and ensure the `ffmpeg` executable is available in your system's command line PATH (Only tested with "ffmpeg version 8.1-full_build-www.gyan.dev")
- **Python:** Ensure Python 3.8+ is installed (This script is only tested with "Python 3.10.11")
- **pip** (Python package manager)


#### Installation for Windows (Virtual Environment, tested on Windows 11 Home using an RTX5080 GPU)

It is recommended to use a virtual environment to manage project dependencies.

```bash
# 1. Create the virtual environment
python -m venv venv

# 2. Activate the virtual environment
.\venv\Scripts\activate

# 3. Install Python dependencies
pip install playwright Pillow pydub

# 4. Install Playwright browsers
python -m playwright install
```

#### Installation for Linux/macOS (Not tested)

```bash
# 1. Clone the repository
git clone https://github.com/JELSTUDIO/JEL_HTMLtoScrollingCreditsCrawl.git
cd JEL_HTMLtoScrollingCreditsCrawl

# 2. Install dependencies
pip install playwright Pillow pydub

# 3. Install Playwright browsers
playwright install
```

### Usage Guide

The script uses a GUI to manage the workflow.

1.  **Preparation:** Ensure your source HTML file (containing the full credits design), any images used in the HTML-file, any required font files (e.g., `Roboto-Medium.ttf`), and an optional audio file are ready. If you can see the webpage correctly in a local browser, then it should work fine (Only tested with the Google Chrome-browser though, so beware of potential browser-variations)
2.  **Run the Script:** Execute the Python file by running this command and wait for the GUI to open.
```bash
# Choose the version of the app you want to run, see change-log for differences
python JEL_HTMLtoScrollingCreditsCrawl_v1.3.0.py
```
3.  **Configure Input:**
    *   Select the HTML file using "Browse HTML".
    *   Select the audio file using "Browse Audio" (optional).
4.  **Configure Output:**
    *   Set the desired **Resolution** (You can edit the script at line-28 if you want to add other resolutions to the drop-down menu).
    *   Set the **Image Output Folder** (A time-stamped sub-folder will be created in the selected folder, and inside this sub-folder is where the generated PNG images will be placed). This folder can become quite large, so make sure you select a drive with enough free space for all the images. Beware that the script doesn't throttle itself if your drive is very slow, which in some cases can cause 'disk-thrashing' (That's the awful noise you hear when the disk can't keep up and begins to write multiple files rather than an ordered stream). If that's a general problem you run into then you can edit the script to be slower (Or faster) by editing the variable (MaxCPUcoresToUseToPreventDiskThrashing) at line-44 which currently is set to "8" (Use a lower number to slow down the script, or a higher number to speed it up).
    *   Choose the final **Output Video File** path (The video will be placed directly in the folder you select).
5.  **Set Parameters:** Adjust the Frame Rate (FPS. You can edit the script at line-34 if you want to add other FPS-choices to the drop-down menu), Scroll Duration (If you load an audio-file then this duration is automatically set. If it's a big audio-file then be patient and give the script a little while to load the full audio-file before continuing), and select the desired encoding parameters (Codec, CRF, Preset. These are only relevant if using CPU and not when using GPU. You can edit the script at line-35 and 36 if you want to add other choices to the drop-down menu).
6.  **Execute:** Click the **Run** button and wait for the process to go through its various steps (This can take some time, depending on how long and big your credits-crawl is. A progress-indicator will show how far the process is along).

#### Workflow Logic

The script executes the generation in three stages:

1.  **HTML Capture:** The full HTML content is captured by a headless browser (`Playwright`) into a single image (`full.png`, with a chroma-subsampling of 4:4:4 using full-scale (0-255) 8-bit RGB with no assigned color-space though it should be compatible with sRGB unless your web-page design is non-standard). To match the size of the text, make sure you select the same resolution that was used during webpage design (1920x1080 if you designed the webpage using 1920x1080 resolution), otherwise it will be zoomed in or out.
2.  **Frame Generation:**
    *   A 5-second countdown sequence is rendered (You can adjust the length in the script at line-41). It will print the numbers 5-4-3 and then go blank for the last 2 seconds (Blank meaning the same color as the webpage's background-color)
    *   The scrolling content (The actual web-page content) is generated frame by frame as an image-sequence (Saved as lossless PNG files so you can use it in a video-editor, where you should use "stretch" to scale the images correctly in terms of width vs height as the images are double-height to achieve a more smooth-looking sub-pixel crawl) timed to crawl for the chosen duration in seconds (Either set manually or automatically by loading an audio-file such as a credits-crawl soundtrack)
    *   A 5-second (You can adjust the length in the script at line-42) blank end-frame sequence is rendered (Blank meaning the same color as the webpage's background-color)
3.  **Encoding:** `FFmpeg` compiles all PNG frames, including the audio track, into the final video file. The purpose of this video is mostly to serve as a "daily" preview of the crawl for quick general evaluation of it, with the lossless image-sequence being meant for the final high-quality work. But the exported video can of course be used directly in a video-editor, though you should be aware it may or may not be fully compliant with your desired color-space format. The 2 video-formats (You can edit the script to have others at line-37) are either "H.264/MPEG-4 AVC" or ProRes, with both formats saved in a Quicktime MOV container being 8-bit and leaving the choice of color-space, color-range and chroma-subsampling etc to whatever FFMPEG decides. Generally the videos will look just like the PNG images in terms of color and contrast, which may be a thing to be mindful of if working in some log-format on your final project)

---

### Demonstration and Media

**Video Demo:**
A demo of a credits-crawl exported by the script from an HTML file designed by the LLM "Gemma4" using random names and titles. This video-demo includes the 5-second countdown intro-padding.
[![Video Demo Thumbnail](https://img.youtube.com/vi/4jPLp9_kPmE/maxresdefault.jpg)](https://www.youtube.com/watch?v=4jPLp9_kPmE)


**GUI Preview:**
Images of the GUIs for each version.

v1.0.0
![GUI Preview](https://github.com/JELSTUDIO/JEL_HTMLtoScrollingCreditsCrawl/raw/main/GUIv1.0.0.png)

v1.3.0
![GUI Preview](https://github.com/JELSTUDIO/JEL_HTMLtoScrollingCreditsCrawl/raw/main/GUIv1.3.0.png)

---

## License

This project is licensed under the **AGPL-3.0 license**.

See [LICENSE](LICENSE) for details.
