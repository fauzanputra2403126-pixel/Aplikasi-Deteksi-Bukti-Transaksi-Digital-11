from pathlib import Path
import numpy as np

from .converter import vector_from_path


def summarize_dataset(provider_dir):
    provider_dir = Path(provider_dir)
    counts = {}
    for label in ("asli", "palsu"):
        folder = provider_dir / label
        counts[label] = len(
            [p for p in folder.iterdir() if p.suffix.lower() in {".png", ".jpg", ".jpeg", ".webp"}]
        ) if folder.exists() else 0
    return counts


def hamming_metrics(vector_x, vector_y):
    """Menghitung XOR, Hamming Distance, dan Hamming Weight."""
    x = np.asarray(vector_x, dtype=np.uint8).reshape(-1)
    y = np.asarray(vector_y, dtype=np.uint8).reshape(-1)
    if x.shape != y.shape:
        raise ValueError("Panjang kedua vektor biner harus sama.")
    if not np.isin(x, [0, 1]).all() or not np.isin(y, [0, 1]).all():
        raise ValueError("Vektor harus berisi bit 0 dan 1.")

    error_vector = np.bitwise_xor(x, y)
    distance = int(np.count_nonzero(error_vector))
    weight = int(np.sum(error_vector))
    similarity = 1.0 - (distance / len(x)) if len(x) else 0.0

    return {
        "distance": distance,
        "weight": weight,
        "similarity": similarity,
        "total_bits": int(len(x)),
        "is_verified": distance == weight,
    }


def classify_by_hamming(query_vector, provider_dir, min_similarity=0.60, top_k=3):
    """
    Klasifikasi nearest-neighbour sederhana berdasarkan referensi berlabel.
    Ini hanya mengukur kemiripan visual, bukan mengesahkan transaksi.
    """
    provider_dir = Path(provider_dir)
    matches = []

    for label in ("asli", "palsu"):
        folder = provider_dir / label
        if not folder.exists():
            continue
        for path in sorted(folder.iterdir()):
            if path.suffix.lower() not in {".png", ".jpg", ".jpeg", ".webp"}:
                continue
            try:
                reference_vector = vector_from_path(path)
                metrics = hamming_metrics(query_vector, reference_vector)
                matches.append({
                    "label": label,
                    "filename": path.name,
                    **metrics,
                })
            except Exception:
                # Satu file rusak tidak menghentikan pemeriksaan seluruh dataset.
                continue

    if not matches:
        raise ValueError("Tidak ada gambar referensi yang dapat dibaca.")

    matches.sort(key=lambda item: item["distance"])
    nearest = matches[0]
    top_matches = matches[:max(1, top_k)]

    # Tolak keputusan jika kemiripan terdekat terlalu rendah.
    if nearest["similarity"] < min_similarity:
        status = "tidak_yakin"
        label = None
        message = (
            "Gambar terlalu berbeda dari seluruh referensi yang tersedia. "
            "Sistem tidak memberikan label Asli/Palsu."
        )
    else:
        status = "indikasi"
        label = nearest["label"]
        message = (
            f"Gambar paling mirip dengan referensi berlabel {label.upper()}. "
            "Ini bukan konfirmasi transaksi dan harus diperiksa melalui kanal resmi."
        )

    return {
        "status": status,
        "label": label,
        "nearest_label": nearest["label"],
        "similarity": nearest["similarity"],
        "distance": nearest["distance"],
        "weight": nearest["weight"],
        "total_bits": nearest["total_bits"],
        "is_verified": nearest["is_verified"],
        "message": message,
        "top_matches": top_matches,
    }
