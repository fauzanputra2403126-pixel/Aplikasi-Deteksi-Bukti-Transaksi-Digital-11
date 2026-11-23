from pathlib import Path
import streamlit as st
from PIL import Image

from modules.template_generator import PROVIDER_CONFIGS
from modules.converter import image_to_binary_vector, load_image
from modules.hamming import classify_by_hamming, summarize_dataset

APP_DIR = Path(__file__).resolve().parent
REFERENCE_DIR = APP_DIR / "data" / "reference"
LABELS = {"Asli": "asli", "Palsu": "palsu"}

st.set_page_config(
    page_title="VerifyID – Analisis Bukti Transaksi",
    page_icon="🛡️",
    layout="wide",
)

st.markdown("""
<style>
.stApp { background: #101827; color: #f3f4f6; }
[data-testid="stMetric"] {
    background: #1c293b; padding: 12px; border-radius: 10px;
}
</style>
""", unsafe_allow_html=True)

st.title("🛡️ VerifyID")
st.caption(
    "Prototipe analisis kemiripan citra menggunakan Hamming Distance "
    "dan Hamming Weight."
)
st.warning(
    "Penting: hasil aplikasi ini hanya menunjukkan kemiripan terhadap dataset "
    "referensi berlabel. Hasilnya bukan bukti mutlak bahwa transaksi benar-benar "
    "terjadi. Verifikasi transaksi tetap perlu melalui kanal resmi penyedia layanan."
)

provider = st.selectbox("Pilih provider", list(PROVIDER_CONFIGS.keys()))
provider_dir = REFERENCE_DIR / PROVIDER_CONFIGS[provider]["folder"]
provider_dir.mkdir(parents=True, exist_ok=True)

tab_check, tab_data, tab_info = st.tabs(
    ["🔎 Periksa bukti", "🗂️ Kelola dataset referensi", "ℹ️ Cara kerja"]
)

with tab_check:
    st.subheader("Unggah bukti transaksi yang akan diperiksa")
    test_file = st.file_uploader(
        "Pilih gambar bukti transaksi",
        type=["png", "jpg", "jpeg", "webp"],
        key="test_upload",
    )
    min_similarity = st.slider(
        "Kemiripan minimum untuk memberikan indikasi",
        min_value=30, max_value=95, value=60, step=1,
        help="Nilai ini adalah ambang kemiripan eksperimen, bukan standar keaslian."
    )

    counts = summarize_dataset(provider_dir)
    c1, c2 = st.columns(2)
    c1.metric("Referensi berlabel asli", counts["asli"])
    c2.metric("Referensi berlabel palsu", counts["palsu"])

    if test_file:
        try:
            test_image = load_image(test_file.getvalue())
            st.image(test_image, caption="Gambar yang akan dianalisis", width=520)
            if st.button("Analisis dengan Hamming", type="primary"):
                if counts["asli"] == 0 or counts["palsu"] == 0:
                    st.error(
                        "Dataset provider ini belum lengkap. Tambahkan minimal satu "
                        "contoh berlabel Asli dan satu contoh berlabel Palsu pada tab "
                        "'Kelola dataset referensi'. Untuk pengujian yang layak, "
                        "gunakan jauh lebih banyak contoh yang bervariasi."
                    )
                else:
                    query_vector = image_to_binary_vector(test_image)
                    result = classify_by_hamming(
                        query_vector, provider_dir, min_similarity=min_similarity / 100
                    )
                    st.markdown("---")
                    st.subheader("Hasil perbandingan")
                    if result["status"] == "indikasi":
                        if result["label"] == "asli":
                            st.success("🟢 PALING MIRIP DENGAN REFERENSI BERLABEL ASLI")
                        else:
                            st.error("🔴 PALING MIRIP DENGAN REFERENSI BERLABEL PALSU")
                    else:
                        st.warning("🟡 BELUM DAPAT DIKLASIFIKASIKAN")

                    st.write(result["message"])
                    m1, m2, m3 = st.columns(3)
                    m1.metric("Label referensi terdekat", result["nearest_label"].upper())
                    m2.metric("Kemiripan terdekat", f'{result["similarity"] * 100:.2f}%')
                    m3.metric("Hamming Distance", f'{result["distance"]:,} bit')
                    st.metric("Hamming Weight wt(x ⊕ y)", f'{result["weight"]:,} bit')
                    st.caption(
                        "Pada vektor biner, Hamming Distance sama dengan Hamming "
                        "Weight dari XOR. Nilai yang sama merupakan pemeriksaan "
                        "konsistensi perhitungan, bukan bukti keaslian."
                    )
                    with st.expander("Lihat beberapa referensi terdekat"):
                        for item in result["top_matches"]:
                            st.write(
                                f'- {item["label"].upper()} — '
                                f'kemiripan {item["similarity"] * 100:.2f}% '
                                f'({item["filename"]})'
                            )
        except Exception as exc:
            st.error(f"Gambar tidak dapat diproses: {exc}")

with tab_data:
    st.subheader(f"Dataset referensi: {provider}")
    st.write(
        "Tambahkan contoh yang labelnya sudah diketahui. Simpan hanya gambar "
        "yang memang boleh digunakan; sebaiknya gunakan data sintetis atau "
        "gambar yang sudah disamarkan."
    )
    label_display = st.radio("Label gambar referensi", ["Asli", "Palsu"], horizontal=True)
    reference_files = st.file_uploader(
        "Unggah satu atau beberapa gambar referensi",
        type=["png", "jpg", "jpeg", "webp"],
        accept_multiple_files=True,
        key="reference_uploads",
    )
    if st.button("Simpan gambar referensi", disabled=not reference_files):
        target = provider_dir / LABELS[label_display]
        target.mkdir(parents=True, exist_ok=True)
        saved = 0
        for uploaded in reference_files:
            try:
                img = load_image(uploaded.getvalue())
                # Simpan sebagai PNG agar format konsisten.
                import uuid
                destination = target / f"{uuid.uuid4().hex}.png"
                img.save(destination, format="PNG")
                saved += 1
            except Exception as exc:
                st.error(f"Gagal menyimpan {uploaded.name}: {exc}")
        st.success(f"{saved} gambar referensi berlabel {label_display} berhasil disimpan.")
        st.rerun()

    counts = summarize_dataset(provider_dir)
    st.write(f"Jumlah referensi **Asli: {counts['asli']}** | **Palsu: {counts['palsu']}**")
    st.caption(
        "Untuk menghapus atau mengganti dataset, kelola folder "
        f"`{provider_dir.relative_to(APP_DIR)}` secara langsung."
    )

with tab_info:
    st.subheader("Alur metode")
    st.markdown("""
    1. Pengguna memilih provider.
    2. Gambar diubah menjadi grayscale, diseragamkan ukurannya, lalu dibinarisasi.
    3. Citra biner diratakan menjadi vektor bit.
    4. Sistem menghitung XOR antara vektor uji dan setiap vektor referensi.
    5. Hamming Distance dihitung sebagai jumlah bit yang berbeda.
    6. Hamming Weight dihitung sebagai jumlah bit bernilai 1 pada hasil XOR.
    7. Sistem menampilkan label dari referensi terdekat jika kemiripannya melewati ambang.

    **Batasan:** metode ini membandingkan pola piksel, bukan memeriksa catatan transaksi
    di server bank/e-wallet. Perubahan ukuran, kompresi, tema aplikasi, jenis ponsel,
    dan tata letak dapat memengaruhi hasil. Dataset harus mewakili variasi tersebut.
    """)
