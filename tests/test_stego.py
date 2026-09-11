import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from stego_core import embed, extract, calculate_capacity_bytes, load_cover_image

# ============================================================
# Test Configuration
# ============================================================

ASSETS = Path(__file__).resolve().parent.parent / "assets"
COVER_IMAGE = ASSETS / "cover_images" / "cover.png"
SECRET_DIR = ASSETS / "secret_files"
OUTPUT_DIR = ASSETS / "output"

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


# ============================================================
# Test 1–5: All Required File Types
# ============================================================

class TestFileTypeEmbedding(unittest.TestCase):
    """
    Covers Testing Step 5: embed + extract each required file type,
    verify byte-for-byte match.
    """

    def _run_roundtrip(self, secret_filename):
        secret_path = SECRET_DIR / secret_filename
        stego_path = OUTPUT_DIR / f"stego_{secret_path.stem}.png"

        result = embed(
            cover_path=str(COVER_IMAGE),
            secret_path=str(secret_path),
            output_path=str(stego_path),
        )
        self.assertTrue(Path(result["output_path"]).exists())

        extracted = extract(
            stego_path=str(stego_path),
            output_dir=str(OUTPUT_DIR),
        )
        extracted_path = Path(extracted["output_path"])
        self.assertTrue(extracted_path.exists())

        # Byte-for-byte comparison
        original_bytes = secret_path.read_bytes()
        extracted_bytes = extracted_path.read_bytes()
        self.assertEqual(
            original_bytes, extracted_bytes,
            f"Extracted file does not match original for {secret_filename}"
        )

    def test_txt(self):
        self._run_roundtrip("secret.txt")

    def test_pdf(self):
        self._run_roundtrip("secret.pdf")

    def test_doc(self):
        self._run_roundtrip("secret.doc")

    def test_png(self):
        self._run_roundtrip("secret.png")

    def test_jpg(self):
        self._run_roundtrip("secret.jpg")


# ============================================================
# Additional Test: Secret File Too Large
# ============================================================

class TestCapacityLimit(unittest.TestCase):

    def test_secret_too_large_raises_error(self):
        img = load_cover_image(str(COVER_IMAGE))
        capacity = calculate_capacity_bytes(img)

        # Create an oversized dummy secret file bigger than capacity
        oversized_path = SECRET_DIR / "oversized.txt"
        oversized_path.write_bytes(b"A" * (capacity + 1000))

        with self.assertRaises(ValueError):
            embed(
                cover_path=str(COVER_IMAGE),
                secret_path=str(oversized_path),
                output_path=str(OUTPUT_DIR / "should_not_exist.png"),
            )

        oversized_path.unlink()  # cleanup


# ============================================================
# Additional Test: Invalid Cover Image
# ============================================================

class TestInvalidCoverImage(unittest.TestCase):

    def test_nonexistent_cover_raises_error(self):
        with self.assertRaises(FileNotFoundError):
            embed(
                cover_path=str(ASSETS / "cover_images" / "does_not_exist.png"),
                secret_path=str(SECRET_DIR / "secret.txt"),
                output_path=str(OUTPUT_DIR / "should_not_exist.png"),
            )

    def test_corrupt_cover_raises_error(self):
        # A text file renamed as .png is not a valid image
        fake_image = ASSETS / "cover_images" / "fake.png"
        fake_image.write_text("this is not an image")

        with self.assertRaises(ValueError):
            embed(
                cover_path=str(fake_image),
                secret_path=str(SECRET_DIR / "secret.txt"),
                output_path=str(OUTPUT_DIR / "should_not_exist.png"),
            )

        fake_image.unlink()  # cleanup


# ============================================================
# Additional Test: Extraction from Non-Stego Image
# ============================================================

class TestNonStegoExtraction(unittest.TestCase):

    def test_extract_from_plain_image_raises_error(self):
        # A normal image with no embedded header/magic bytes
        with self.assertRaises(ValueError):
            extract(
                stego_path=str(COVER_IMAGE),
                output_dir=str(OUTPUT_DIR),
            )


if __name__ == "__main__":
    unittest.main(verbosity=2)