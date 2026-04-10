# NOTICE and Third-Party Licenses

This project (JEL_HTMLtoScrollingCreditsCrawl) is licensed under the [GNU Affero General Public License v3 (AGPLv3)](https://agpl.org/licenses/AGPL-3.0.html).

While the core application is licensed under AGPLv3, it relies on several external libraries and tools to function. The terms of those dependencies are listed below. When combining code, the terms of all included licenses apply to the resulting work.

## Required Python Libraries (pip dependencies)

The following libraries are required for the script to run. Their licenses must be adhered to.

### 1. Pillow
*   **Purpose:** Image manipulation and rendering.
*   **Version:** `>=10.0.0`
*   **License:** MIT-CMU License
*   **Attribution:** Pillow is licensed under the MIT-CMU License, which grants broad rights for use, copy, modification, and distribution provided the copyright and permission notice is retained. Refer to the official Pillow project for the complete license text.
*   **Link:** [https://github.com/python-pillow/Pillow]

### 2. Playwright
*   **Purpose:** Browser automation and HTML rendering.
*   **Version:** `>=1.30.0`
*   **License:** Apache License 2.0
*   **Attribution:** Playwright is distributed under the Apache License 2.0. This license grants broad rights for use, copy, modification, and distribution, while also addressing patent grants. Refer to the official Playwright repository for the complete license text.
*   **Link:** [https://github.com/microsoft/playwright]

### 3. pydub (Audio Handling Wrapper)
*   **Purpose:** Reading and processing audio files.
*   **Version:** `>=0.25.1`
*   **License:** MIT License
*   **Attribution:** pydub is licensed under the MIT License. Refer to the official pydub project for the complete license text.
*   **Link:** [https://github.com/jiaaro/pydub]
*   **IMPORTANT NOTE:** pydub is a wrapper that requires the external command-line tool **FFmpeg** to function. FFmpeg itself has its own license and must be adhered to.

### 4. External Tool Dependency: FFmpeg
*   **Purpose:** Core media processing required by pydub.
*   **License:** GNU Lesser General Public License v2.1 (LGPL v2.1)
*   **Attribution:** FFmpeg must be installed on the user's system. The LGPL is a compatible copyleft license that allows this program to be combined with an AGPLv3 licensed work.
*   **Link:** [https://www.ffmpeg.org/legal.html]

---

### 📜 Compliance Summary

By using this script, you agree to abide by the terms of the AGPLv3 for the primary application code, and you also agree to abide by the respective licenses of Pillow (MIT-CMU), Playwright (Apache 2.0), pydub (MIT), and FFmpeg (LGPL v2.1).

If you have any questions regarding licensing compliance, please contact the project maintainer.
