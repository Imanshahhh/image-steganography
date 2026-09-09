import os
import cv2
import numpy as np

HEADER_DELIMITER = ":::"

def _bytes_to_bits(data_bytes):
    return ''.join(f'{b:08b}' for b in data_bytes)

def _bits_to_bytes(bits):
    byte_list = [int(bits[i:i+8], 2) for i in range(0, len(bits), 8)]
    return bytes(byte_list)

def hide_file_lsb(cover_image_path, secret_file_path, output_stego_path):
    if not os.path.exists(cover_image_path):
        raise FileNotFoundError(f"Cover image not found: {cover_image_path}")
    if not os.path.exists(secret_file_path):
        raise FileNotFoundError(f"Secret file not found: {secret_file_path}")

    img = cv2.imread(cover_image_path)
    if img is None:
        raise ValueError("Invalid cover image file.")

    with open(secret_file_path, 'rb') as f:
        secret_bytes = f.read()

    ext = os.path.splitext(secret_file_path)[1].lower()
    header_str = f"{ext}{HEADER_DELIMITER}{len(secret_bytes)}{HEADER_DELIMITER}"
    header_bytes = header_str.encode('utf-8')

    full_payload = header_bytes + secret_bytes
    payload_bits = _bytes_to_bits(full_payload)
    total_bits = len(payload_bits)

    # Capacity check
    max_capacity = img.shape[0] * img.shape[1] * img.shape[2]
    if total_bits > max_capacity:
        raise ValueError(f"Secret file too large ({total_bits} bits). Max capacity is {max_capacity} bits.")

    flat_img = img.flatten()
    for i in range(total_bits):
        flat_img[i] = (flat_img[i] & ~1) | int(payload_bits[i])

    stego_img = flat_img.reshape(img.shape)
    if not output_stego_path.lower().endswith('.png'):
        output_stego_path += '.png'
        
    cv2.imwrite(output_stego_path, stego_img)
    return output_stego_path

def extract_file_lsb(stego_image_path, output_dir="extracted"):
    if not os.path.exists(stego_image_path):
        raise FileNotFoundError(f"Stego image not found: {stego_image_path}")

    img = cv2.imread(stego_image_path)
    if img is None:
        raise ValueError("Invalid stego image file.")

    flat_img = img.flatten()
    header_found = False
    file_size = 0
    file_ext = ""
    data_start_bit = 0

    os.makedirs(output_dir, exist_ok=True)

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
    output_filename = os.path.join(output_dir, f"extracted_secret{file_ext}")
    
    with open(output_filename, 'wb') as f:
        f.write(secret_bytes)

    return output_filename