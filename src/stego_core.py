from pathlib import Path

from PIL import Image
import numpy as np


# ============================================================
# Configuration
# ============================================================

MAGIC = b"STEG"
HEADER_LENGTH_BYTES = 4
HEADER_EXT_BYTES = 8
HEADER_TOTAL_BYTES = len(MAGIC) + HEADER_LENGTH_BYTES + HEADER_EXT_BYTES

SUPPORTED_EXTENSIONS = {
    ".txt", ".pdf", ".doc", ".docx", ".png", ".jpg", ".jpeg",
}


# ============================================================
# Image Functions
# ============================================================

def load_cover_image(path):
    """Load an image and convert it to RGB (exactly 3 channels)."""
    path = Path(path)

    if not path.exists():
        raise FileNotFoundError(f"Image not found: {path}")

    try:
        img = Image.open(path)
        return img.convert("RGB")
    except Exception as e:
        raise ValueError(f"Unable to open image: {e}")


# ============================================================
# Bit / Byte Conversion
# ============================================================

def bytes_to_bits(data: bytes) -> np.ndarray:
    if not data:
        return np.array([], dtype=np.uint8)
    arr = np.frombuffer(data, dtype=np.uint8)
    return np.unpackbits(arr)


def bits_to_bytes(bits: np.ndarray) -> bytes:
    if len(bits) == 0:
        return b""
    if len(bits) % 8 != 0:
        raise ValueError("Invalid bit sequence length.")
    arr = np.packbits(bits)
    return arr.tobytes()


# ============================================================
# Header Functions
# ============================================================

def build_header(secret_bytes: bytes, extension: str) -> bytes:
    """
    Header structure: [4 bytes MAGIC][4 bytes file length][8 bytes extension]
    """
    if not extension:
        extension = ""
    extension = extension.lower()

    if extension and extension not in SUPPORTED_EXTENSIONS:
        raise ValueError(
            f"Unsupported file type: {extension}. "
            f"Supported types: {', '.join(sorted(SUPPORTED_EXTENSIONS))}"
        )

    if len(secret_bytes) > 0xFFFFFFFF:
        raise ValueError("Secret file is too large.")

    length_field = len(secret_bytes).to_bytes(HEADER_LENGTH_BYTES, byteorder="big")

    ext_bytes = extension.encode("utf-8")
    if len(ext_bytes) > HEADER_EXT_BYTES:
        raise ValueError(f"Extension '{extension}' is too long.")
    ext_field = ext_bytes.ljust(HEADER_EXT_BYTES, b"\0")

    return MAGIC + length_field + ext_field


def parse_header(header_bytes: bytes):
    if len(header_bytes) != HEADER_TOTAL_BYTES:
        raise ValueError("Invalid header length.")

    magic = header_bytes[:len(MAGIC)]
    if magic != MAGIC:
        raise ValueError(
            "This does not appear to be a valid stego image created by this tool."
        )

    length_start = len(MAGIC)
    length_end = length_start + HEADER_LENGTH_BYTES
    length_field = header_bytes[length_start:length_end]
    length = int.from_bytes(length_field, byteorder="big")

    ext_start = length_end
    ext_end = ext_start + HEADER_EXT_BYTES
    ext_field = header_bytes[ext_start:ext_end]

    try:
        extension = ext_field.rstrip(b"\0").decode("utf-8")
    except UnicodeDecodeError:
        raise ValueError("Invalid file extension in stego header.")

    if extension and extension not in SUPPORTED_EXTENSIONS:
        raise ValueError(f"Unsupported or invalid extension: {extension}")

    return length, extension


# ============================================================
# Capacity
# ============================================================

def calculate_capacity_bytes(img: Image.Image) -> int:
    """1 LSB per RGB channel: (width × height × 3) / 8 bytes."""
    width, height = img.size
    capacity_bits = width * height * 3
    return capacity_bits // 8


def calculate_available_secret_capacity(img: Image.Image) -> int:
    """Capacity remaining for the secret file after reserving header space."""
    return max(0, calculate_capacity_bytes(img) - HEADER_TOTAL_BYTES)


# ============================================================
# Embedding
# ============================================================

def embed(cover_path: str, secret_path: str, output_path: str = "stego.png"):
    cover_path = Path(cover_path)
    secret_path = Path(secret_path)
    output_path = Path(output_path)

    if not cover_path.exists():
        raise FileNotFoundError(f"Cover image not found: {cover_path}")
    if not secret_path.exists():
        raise FileNotFoundError(f"Secret file not found: {secret_path}")
    if secret_path.stat().st_size == 0:
        raise ValueError("Secret file is empty.")

    extension = secret_path.suffix.lower()
    if extension not in SUPPORTED_EXTENSIONS:
        raise ValueError(
            f"Unsupported secret file type: {extension}\n"
            f"Supported types: {', '.join(sorted(SUPPORTED_EXTENSIONS))}"
        )

    img = load_cover_image(cover_path)

    with open(secret_path, "rb") as f:
        secret_bytes = f.read()

    header_bytes = build_header(secret_bytes, extension)
    payload = header_bytes + secret_bytes

    capacity = calculate_capacity_bytes(img)
    if len(payload) > capacity:
        available = calculate_available_secret_capacity(img)
        raise ValueError(
            f"Secret file is too large.\n"
            f"Secret size: {len(secret_bytes):,} bytes\n"
            f"Available: {available:,} bytes"
        )

    bits = bytes_to_bits(payload)

    pixels = np.array(img, dtype=np.uint8)
    flat = pixels.reshape(-1)
    flat[:len(bits)] = (flat[:len(bits)] & 0xFE) | bits

    stego_pixels = flat.reshape(pixels.shape)
    stego_img = Image.fromarray(stego_pixels, "RGB")

    output_path.parent.mkdir(parents=True, exist_ok=True)
    stego_img.save(output_path, format="PNG")

    return {
        "output_path": str(output_path),
        "secret_size": len(secret_bytes),
        "header_size": HEADER_TOTAL_BYTES,
        "payload_size": len(payload),
        "capacity": capacity,
        "remaining_capacity": capacity - len(payload),
    }


# ============================================================
# Extraction
# ============================================================

def extract(stego_path: str, output_dir: str = "."):
    stego_path = Path(stego_path)
    output_dir = Path(output_dir)

    if not stego_path.exists():
        raise FileNotFoundError(f"Stego image not found: {stego_path}")

    img = load_cover_image(stego_path)
    pixels = np.array(img, dtype=np.uint8)
    flat = pixels.reshape(-1)

    header_bits_needed = HEADER_TOTAL_BYTES * 8
    if len(flat) < header_bits_needed:
        raise ValueError("Image is too small to contain a valid stego header.")

    header_bits = flat[:header_bits_needed] & 1
    header_bytes = bits_to_bytes(header_bits)
    length, extension = parse_header(header_bytes)

    payload_bits_needed = length * 8
    start = header_bits_needed
    end = start + payload_bits_needed

    if end > len(flat):
        raise ValueError(
            "Invalid or corrupted stego image. The declared payload exceeds image capacity."
        )

    payload_bits = flat[start:end] & 1
    secret_bytes = bits_to_bytes(payload_bits)

    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / f"extracted_secret{extension}"

    with open(output_path, "wb") as f:
        f.write(secret_bytes)

    return {
        "output_path": str(output_path),
        "file_size": len(secret_bytes),
        "extension": extension,
    }


# ============================================================
# Image Quality Analysis
# ============================================================

def calculate_mse(cover_path: str, stego_path: str) -> float:
    cover = np.array(load_cover_image(cover_path), dtype=np.float64)
    stego = np.array(load_cover_image(stego_path), dtype=np.float64)

    if cover.shape != stego.shape:
        raise ValueError("Cover and stego images must have the same dimensions.")

    return float(np.mean((cover - stego) ** 2))


def calculate_psnr(cover_path: str, stego_path: str) -> float:
    mse = calculate_mse(cover_path, stego_path)
    if mse == 0:
        return float("inf")
    max_pixel = 255.0
    return float(10 * np.log10((max_pixel ** 2) / mse))


# ============================================================
# Histogram Analysis
# ============================================================

def calculate_histogram(image_path: str):
    img = load_cover_image(image_path)
    pixels = np.array(img)

    red_histogram = np.histogram(pixels[:, :, 0], bins=256, range=(0, 256))[0]
    green_histogram = np.histogram(pixels[:, :, 1], bins=256, range=(0, 256))[0]
    blue_histogram = np.histogram(pixels[:, :, 2], bins=256, range=(0, 256))[0]

    return red_histogram, green_histogram, blue_histogram


# ============================================================
# File Size Analysis
# ============================================================

def analyze_file_size(cover_path: str, stego_path: str):
    cover_path = Path(cover_path)
    stego_path = Path(stego_path)

    cover_size = cover_path.stat().st_size
    stego_size = stego_path.stat().st_size
    difference = stego_size - cover_size
    percentage_change = (difference / cover_size) * 100 if cover_size > 0 else 0

    return {
        "cover_size": cover_size,
        "stego_size": stego_size,
        "difference": difference,
        "percentage_change": percentage_change,
    }


# ============================================================
# Quick Manual Test
# ============================================================

if __name__ == "__main__":
    COVER = "assets/cover_images/cover.png"
    SECRET = "assets/secret_files/secret.txt"
    STEGO = "assets/output/stego.png"
    OUTPUT_DIR = "assets/output"

    try:
        result = embed(cover_path=COVER, secret_path=SECRET, output_path=STEGO)
        print("\n=== EMBEDDING ===")
        print(f"Stego image       : {result['output_path']}")
        print(f"Secret size       : {result['secret_size']:,} bytes")
        print(f"Header size       : {result['header_size']:,} bytes")
        print(f"Payload size      : {result['payload_size']:,} bytes")
        print(f"Image capacity    : {result['capacity']:,} bytes")
        print(f"Remaining capacity: {result['remaining_capacity']:,} bytes")

        extracted = extract(stego_path=STEGO, output_dir=OUTPUT_DIR)
        print("\n=== EXTRACTION ===")
        print(f"Extracted file    : {extracted['output_path']}")
        print(f"File size         : {extracted['file_size']:,} bytes")
        print(f"Extension         : {extracted['extension']}")

        mse = calculate_mse(COVER, STEGO)
        psnr = calculate_psnr(COVER, STEGO)
        print("\n=== IMAGE QUALITY ===")
        print(f"MSE               : {mse:.6f}")
        print(f"PSNR              : {psnr:.2f} dB")

        size_info = analyze_file_size(COVER, STEGO)
        print("\n=== FILE SIZE ===")
        print(f"Cover size        : {size_info['cover_size']:,} bytes")
        print(f"Stego size        : {size_info['stego_size']:,} bytes")
        print(f"Difference        : {size_info['difference']:+,} bytes")
        print(f"Percentage change : {size_info['percentage_change']:+.2f}%")

        print("\nAll operations completed successfully.")

    except Exception as e:
        print(f"\nERROR: {e}")