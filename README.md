# Image Steganography Tool
 
An LSB (Least Significant Bit) steganography application built for **IKB21303 – Cryptography and Steganography**, Assignment 2 (UniKL MIIT, July 2026 semester).
 
The tool hides a secret file (text, document, or image) inside a cover image, producing a visually identical **stego image** that secretly contains the hidden file. It can also extract the hidden file back out, and generate analysis (visual comparison, RGB histograms, file size comparison) for the assignment report.
 
---
 
## Features
 
- **Hide files** — embed `.txt`, `.pdf`, `.doc`/`.docx`, `.png`, `.jpg`/`.jpeg` files inside a PNG cover image
- **Extract files** — recover the original hidden file from a stego image, byte-for-byte
- **Capacity check** — calculates available space before embedding and warns if the secret file is too large
- **Header validation** — a magic-byte header (`STEG`) ensures the tool can detect invalid or non-stego images instead of producing garbage output
- **Analysis tools** — visual comparison, RGB histogram comparison, MSE/PSNR image quality metrics, and file size comparison
- **Desktop GUI** — built with PySide6, tabbed interface for Hide / Extract / Analyse workflows
---
 
## Project Structure
 
```
image-steganography/
├── src/
│   ├── __init__.py
│   ├── stego_core.py     # Core LSB embed/extract logic, capacity, header
│   ├── analysis.py       # Histogram, visual comparison, MSE/PSNR
│   └── gui.py             # PySide6 desktop interface
├── tests/
│   └── test_stego.py      # Unit tests (unittest)
├── assets/
│   ├── cover_images/      # Cover images go here
│   ├── secret_files/      # Secret files to hide go here
│   └── output/             # Stego images and analysis output saved here
├── .gitignore
├── requirements.txt
└── README.md
```
 
---
 
## Requirements
 
- Python 3.11+ (PySide6 may fail to import on some older/newer Python builds due to Shiboken DLL issues — see Troubleshooting)
- Dependencies (see `requirements.txt`):
  - Pillow
  - NumPy
  - Matplotlib
  - PySide6
---
 
## Setup
 
```bash
git clone https://github.com/Imanshahhh/image-steganography.git
cd image-steganography
 
python -m venv venv
source venv/Scripts/activate   # Windows Git Bash
# or: venv\Scripts\activate    # Windows CMD
 
pip install -r requirements.txt
```
 
---
 
## Usage
 
### Run the GUI
```bash
python src/gui.py
```
Use the **Hide file** tab to select a cover image and secret file, then embed. Use **Extract file** to recover a hidden file from a stego image. Use **Analyse results** to generate histogram/visual comparison images for the report.
 
### Run Core directly (command line)
```bash
python src/stego_core.py
```
Uses default paths in `assets/` — edit the `COVER`, `SECRET`, `STEGO` constants in the `__main__` block to change them.
 
### Run Analysis directly (command line)
```bash
python src/analysis.py assets/cover_images/cover.png assets/output/stego.png
```
Saves `histogram_comparison.png` and `visual_comparison.png` to `assets/output/`, and prints MSE, PSNR, and file size comparison.
 
### Run Tests
```bash
python -m unittest tests/test_stego.py -v
```
Covers all 5 required file types (byte-for-byte round trip), plus edge cases: secret file too large, invalid/missing cover image, and extraction from a non-stego image.
 
---
 
## How It Works
 
1. The secret file's bytes are prefixed with a small header: a 4-byte magic signature (`STEG`), a 4-byte length field, and an 8-byte file extension field.
2. Header + secret file bytes are converted to a bitstream.
3. The cover image is converted to RGB and flattened; the last bit of each pixel color value is replaced with one bit of the payload, in a fixed row-major order.
4. The result is saved as a lossless PNG (`stego.png`) — required since lossy formats like JPEG would destroy the hidden bits.
5. Extraction reverses the process: it reads the header first to learn the exact payload length and file extension, then reads exactly that many more bits and reconstructs the original file.
---
 
## Limitations
 
- LSB steganography is fragile — image compression (e.g. re-saving as JPEG) or resizing will destroy the hidden data
- Payload capacity is capped by the cover image's pixel count (`width × height × 3 ÷ 8` bytes, minus header overhead)
- The hidden payload is not encrypted
- Designed specifically for lossless cover images (PNG/BMP)
---
 
## Troubleshooting
 
**`DLL load failed while importing Shiboken`**
This is a known PySide6/Windows compatibility issue tied to certain Python versions. Fix by:
1. Installing the [Microsoft Visual C++ Redistributable](https://aka.ms/vs/17/release/vc_redist.x64.exe)
2. If that doesn't resolve it, use a different Python version (3.11/3.12 recommended) and rebuild the venv:
```bash
   py --list                # see installed Python versions
   py -3.11 -m venv venv
   source venv/Scripts/activate
   pip install -r requirements.txt
```
 
---
 
