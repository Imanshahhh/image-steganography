from PIL import Image
import numpy as np

HEADER_LENGTH_BYTES = 4      # stores payload length
HEADER_EXT_BYTES = 8         # stores file extension, e.g. b'.txt\0\0\0\0'
HEADER_TOTAL_BYTES = HEADER_LENGTH_BYTES + HEADER_EXT_BYTES

