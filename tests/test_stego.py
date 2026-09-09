import sys
import unittest
from pathlib import Path
import cv2
import numpy as np

HEADER_DELIMITER = ":::"

# --- HELPER FUNCTIONS ---

def _bytes_to_bits(data_bytes):
    return ''.join(f'{b:08b}' for b in data_bytes)

def _bits_to_bytes(bits):
    byte_list = [int(bits[i:i+8], 2) for i in range(0, len(bits), 8)]
    return bytes(byte_list)

def load_cover_image(cover_image_path):
    """Loads and validates the cover image file using Path object or string."""
    path_obj = Path(cover_image_path)
    if not path_obj.exists():
        raise FileNotFoundError(f"Cover image not found: {cover_image_path}")
    
    # str(path_obj) ensures cv2 receives a standard string path
    img = cv2.imread(str(path_obj))
    if img is None:
        raise ValueError("Invalid cover image file.")
    return img

def calculate_capacity_bytes(img):
    """Calculates maximum hidden data capacity in bytes."""
    total_pixels_channels = img.shape[0] * img.shape[1] * img.shape[2]
    return total_pixels_channels // 8

# --- MAIN STEGANOGRAPHY API ---

def embed(cover_image_path, secret_file_path, output_stego_path):
    """Hides a secret file inside a cover image using LSB steganography."""
    cover_path = Path(cover_image_path)
    secret_path = Path(secret_file_path)
    stego_path = Path(output_stego_path)

    if not secret_path.exists():
        raise FileNotFoundError(f"Secret file not found: {secret_file_path}")

    img = load_cover_image(cover_path)

    with open(secret_path, 'rb') as f:
        secret_bytes = f.read()

    ext = secret_path.suffix.lower()  # pathlib way to get extension
    header_str = f"{ext}{HEADER_DELIMITER}{len(secret_bytes)}{HEADER_DELIMITER}"
    header_bytes = header_str.encode('utf-8')

    full_payload = header_bytes + secret_bytes
    payload_bits = _bytes_to_bits(full_payload)
    total_bits = len(payload_bits)

    # Capacity Check
    max_capacity_bits = img.shape[0] * img.shape[1] * img.shape[2]
    if total_bits > max_capacity_bits:
        raise ValueError(
            f"Secret file too large ({len(full_payload)} bytes). "
            f"Max capacity is {calculate_capacity_bytes(img)} bytes."
        )

    flat_img = img.flatten()
    for i in range(total_bits):
        flat_img[i] = (flat_img[i] & ~1) | int(payload_bits[i])

    stego_img = flat_img.reshape(img.shape)
    
    # Ensure .png extension using Path
    if stego_path.suffix.lower() != '.png':
        stego_path = stego_path.with_suffix('.png')
        
    cv2.imwrite(str(stego_path), stego_img)
    return str(stego_path)

def extract(stego_image_path, output_dir="extracted"):
    """Extracts a hidden secret file from an LSB stego image."""
    stego_path = Path(stego_image_path)
    out_dir_path = Path(output_dir)

    img = load_cover_image(stego_path)
    flat_img = img.flatten()
    
    header_found = False
    file_size = 0
    file_ext = ""
    data_start_bit = 0

    out_dir_path.mkdir(parents=True, exist_ok=True)  # pathlib way to create dir

    temp_bytes = bytearray()
    for i in range(0, len(flat_img), 8):
        if i + 8 > len(flat_img):
            break
        byte_bits = "".join(str(flat_img[i + j] & 1) for j in range(8))
        byte_val = int(byte_bits, 2)
        temp_bytes.append(byte_val)

        try:
            decoded_text = temp_bytes.decode('utf-8', errors='ignore')
            if HEADER_DELIMITER in decoded_text:
                parts = decoded_text.split(HEADER_DELIMITER)
                if len(parts) >= 3:
                    file_ext = parts[0]
                    file_size = int(parts[1])
                    header_str = f"{file_ext}{HEADER_DELIMITER}{file_size}{HEADER_DELIMITER}"
                    data_start_bit = len(header_str.encode('utf-8')) * 8
                    header_found = True
                    break
        except Exception:
            continue

    if not header_found:
        raise ValueError("No hidden message or valid header found in this image.")

    payload_bits = []
    end_bit = data_start_bit + (file_size * 8)
    if end_bit > len(flat_img):
        raise ValueError("Corrupted data or invalid file header detected.")

    for i in range(data_start_bit, end_bit):
        payload_bits.append(str(flat_img[i] & 1))

    secret_bytes = _bits_to_bytes("".join(payload_bits))
    output_filename = out_dir_path / f"extracted_secret{file_ext}"
    
    with open(output_filename, 'wb') as f:
        f.write(secret_bytes)

    return str(output_filename)

# Backwards compatibility aliases
hide_file_lsb = embed
extract_file_lsb = extract

# --- UNIT TESTS ---

class TestStegoCore(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.test_dir = Path("temp_test_dir")
        cls.test_dir.mkdir(exist_ok=True)
        
        cls.test_cover = cls.test_dir / "temp_cover.png"
        cls.test_secret = cls.test_dir / "temp_secret.txt"
        cls.test_stego = cls.test_dir / "temp_stego.png"
        cls.out_dir = cls.test_dir / "extracted_out"
        cls.secret_data = b"Testing Steganography Core Logic with Pathlib"

        # Create dummy cover image (100x100x3)
        dummy_img = np.random.randint(0, 256, (100, 100, 3), dtype=np.uint8)
        cv2.imwrite(str(cls.test_cover), dummy_img)

        # Create dummy secret file
        with open(cls.test_secret, "wb") as f:
            f.write(cls.secret_data)

    @classmethod
    def tearDownClass(cls):
        # Cleanup using pathlib
        if cls.test_dir.exists():
            for item in cls.test_dir.rglob("*"):
                if item.is_file():
                    item.unlink()
            for subdir in cls.test_dir.iterdir():
                if subdir.is_dir():
                    subdir.rmdir()
            cls.test_dir.rmdir()

    def test_load_and_capacity(self):
        img = load_cover_image(self.test_cover)
        self.assertIsNotNone(img)
        capacity = calculate_capacity_bytes(img)
        self.assertEqual(capacity, (100 * 100 * 3) // 8)

    def test_embed_and_extract(self):
        stego_path = embed(self.test_cover, self.test_secret, self.test_stego)
        self.assertTrue(Path(stego_path).exists())

        extracted_file = extract(self.test_stego, output_dir=self.out_dir)
        self.assertTrue(Path(extracted_file).exists())

        with open(extracted_file, "rb") as f:
            data = f.read()
        self.assertEqual(data, self.secret_data)

if __name__ == "__main__":
    unittest.main(verbosity=2)