# VerifyID – Prototipe Hamming

Aplikasi Streamlit untuk membandingkan gambar bukti transaksi dengan dataset
referensi berlabel menggunakan Hamming Distance dan Hamming Weight.

## 1. Instalasi

Disarankan menggunakan Python 3.10 atau lebih baru.

```bash
python -m venv .venv
```

Aktifkan lingkungan virtual:

Windows:
```bash
.venv\Scripts\activate
```

macOS/Linux:
```bash
source .venv/bin/activate
```

Pasang dependensi dan jalankan aplikasi:

```bash
pip install -r requirements.txt
streamlit run app.py
```

## 2. Cara menggunakan

1. Buka aplikasi di browser.
2. Pilih provider.
3. Buka tab **Kelola dataset referensi**.
4. Masukkan beberapa contoh gambar yang labelnya telah diketahui sebagai Asli.
5. Ulangi untuk contoh yang labelnya telah diketahui sebagai Palsu.
6. Buka tab **Periksa bukti**, unggah gambar uji, lalu klik Analisis.

Dataset disimpan lokal di:
`data/reference/<nama_provider>/asli/` dan
`data/reference/<nama_provider>/palsu/`.

Setiap provider mempunyai dataset sendiri. Jangan mencampur referensi antar-provider.

## 3. Makna perhitungan

Untuk dua vektor biner x dan y:

- Error vector: `e = x XOR y`
- Hamming Distance: `d(x,y) = jumlah bit yang berbeda`
- Hamming Weight: `wt(e) = jumlah bit 1 pada e`
- Untuk vektor biner, `d(x,y) = wt(x XOR y)`

Kemiripan yang ditampilkan:
`(1 - d(x,y)/n) × 100%`

## 4. Batasan ilmiah dan keamanan

- Ini prototipe pembelajaran/penelitian, bukan layanan verifikasi transaksi resmi.
- Label hasil berarti "paling mirip dengan contoh berlabel ...", bukan kepastian asli/palsu.
- Hamming berbasis piksel dapat berubah karena kompresi, resolusi, crop, tema,
  font, dan tata letak.
- Kualitas hasil bergantung pada dataset. Kumpulkan contoh yang beragam dan
  pisahkan data pelatihan/referensi dari data pengujian.
- Evaluasi dengan confusion matrix, accuracy, precision, recall, dan F1-score.
- Bukti transaksi dapat memuat data pribadi. Gunakan data sintetis atau samarkan
  nama, nomor rekening, nomor telepon, dan informasi sensitif. Jangan unggah
  data orang lain tanpa izin.
- Jangan gunakan keluaran aplikasi sebagai satu-satunya dasar menerima pembayaran.
  Periksa mutasi atau status transaksi melalui aplikasi/kanal resmi provider.

## 5. Struktur proyek

```text
VerifyID_Hamming/
├── app.py
├── requirements.txt
├── README.md
├── modules/
│   ├── __init__.py
│   ├── converter.py
│   ├── hamming.py
│   └── template_generator.py
└── data/
    └── reference/
```
