from io import BytesIO
import numpy as np
from PIL import Image, ImageOps

# Ukuran tetap untuk semua citra agar panjang vektor selalu sama.
TARGET_SIZE = (160, 96)  # lebar, tinggi


def load_image(source):
    """Membaca gambar dari path, bytes, atau objek file dan mengembalikan RGB."""
    if isinstance(source, (bytes, bytearray)):
        image = Image.open(BytesIO(source))
    else:
        image = Image.open(source)
    image.load()
    return ImageOps.exif_transpose(image).convert("RGB")


def otsu_threshold(gray_array):
    """Menghitung ambang Otsu tanpa dependensi OpenCV."""
    histogram = np.bincount(gray_array.ravel(), minlength=256).astype(np.float64)
    total = gray_array.size
    sum_total = np.dot(np.arange(256), histogram)
    sum_background = 0.0
    weight_background = 0.0
    best_variance = -1.0
    threshold = 127

    for value in range(256):
        weight_background += histogram[value]
        if weight_background == 0:
            continue
        weight_foreground = total - weight_background
        if weight_foreground == 0:
            break
        sum_background += value * histogram[value]
        mean_background = sum_background / weight_background
        mean_foreground = (sum_total - sum_background) / weight_foreground
        between_variance = (
            weight_background * weight_foreground
            * (mean_background - mean_foreground) ** 2
        )
        if between_variance > best_variance:
            best_variance = between_variance
            threshold = value
    return int(threshold)


def image_to_binary_vector(image, target_size=TARGET_SIZE):
    """
    Preprocessing konsisten:
    EXIF correction -> grayscale -> autocontrast -> contain/padding
    -> Otsu threshold -> vektor biner uint8.
    Bit 1 = piksel gelap, bit 0 = latar terang.
    """
    if not isinstance(image, Image.Image):
        image = load_image(image)

    gray = ImageOps.grayscale(image)
    gray = ImageOps.autocontrast(gray)

    # Menjaga rasio aspek; citra dipasang pada kanvas putih ukuran tetap.
    fitted = ImageOps.contain(gray, target_size, method=Image.Resampling.LANCZOS)
    canvas = Image.new("L", target_size, color=255)
    x = (target_size[0] - fitted.width) // 2
    y = (target_size[1] - fitted.height) // 2
    canvas.paste(fitted, (x, y))

    array = np.asarray(canvas, dtype=np.uint8)
    threshold = otsu_threshold(array)
    binary = (array < threshold).astype(np.uint8)
    return binary.reshape(-1)


def vector_from_path(path):
    """Memuat satu file referensi dan mengubahnya menjadi vektor biner."""
    return image_to_binary_vector(load_image(path))
