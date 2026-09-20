# 🌐 Universal Novel EPUB Translator

Platform penerjemah novel web EPUB berbasis AI (Google Gemini) yang dirancang untuk **semua genre novel** (*Xianxia / Kultivasi*, *LitRPG / Hunter System*, *Western High Fantasy*, *Sci-Fi / Cyberpunk*, dll.) dengan sistem **Manajemen Multi-Project** dan **Deteksi Otomatis Glossary & Konteks**.

---

## 🌟 Fitur Utama

1. **📁 Multi-Project Management**:
   - Setiap novel memiliki wadah terisolasi di folder `projects/<id_novel>/`.
   - Riwayat istilah (`glossary.json`), aturan perbaikan (`repair_map.json`), dan cache terjemahan (`cache/`) disimpan terpisah untuk tiap novel.
   - Menu CLI interaktif untuk memilih melanjutkan novel sebelumnya atau membuat proyek novel baru.

2. **🤖 Auto-Detection Genre & Glossary**:
   - Cukup masukkan file `.epub` apa saja.
   - Sistem secara otomatis membaca metadata (judul, penulis) dan mengambil sampel bab awal.
   - AI mendeteksi **genre cerita** dan menyusun **glossary awal** (nama karakter, sekte/faksi, jurus/skill, artefak) tanpa perlu dibuat manual dari nol.

3. **🎭 Genre & Tone Adaptive Prompting**:
   - Sistem menyesuaikan system prompt sesuai genre:
     - **Xianxia / Wuxia**: Menjaga ranah kultivasi, sebutan persaudaraan sekte (*Senior/Junior Brother*), dan nama jurus.
     - **LitRPG / System Hunter**: Menjaga status bar, format quest/skill, peringkat (*S-Rank, Awakener*), dan dungeon.
     - **Victorian / Grimdark**: Diksi sastra klasik, misterius, dewa-dewi, dan artefak legendaris.
     - **Sci-Fi / Cyberpunk**: Augmentasi, megakorporasi, dan kecerdasan buatan.

4. **🛡️ Zero Style Corruption (XML AST Parser)**:
   - Menggunakan parser DOM `BeautifulSoup` (`lxml-xml`) yang hanya menargetkan node teks (`NavigableString`) dan mem-bypass tag `<style>`, `<script>`, dan `<head>`.
   - Menerapkan prinsip *longest-first* untuk mencegah pemotongan kata majemuk.

5. **⚡ Hemat Biaya & Resume Otomatis**:
   - Dilengkapi sistem caching per-paragraf. Jika proses terputus (Ctrl+C atau koneksi mati), Anda dapat melanjutkannya kapan saja tanpa mengulang dari bab 1.

---

## 📁 Struktur Repositori

```text
universal_epub_translator/
├── .env.example                  # Template kredensial API
├── .gitignore                    # Mengabaikan file cache, epub, dan env
├── requirements.txt              # Pustaka Python yang dibutuhkan
├── README.md                     # Dokumentasi ini
├── main.py                       # CLI Wizard Interaktif + Headless CLI
├── translator/
│   ├── __init__.py
│   ├── project_manager.py        # Logika isolasi & manajemen project
│   ├── entity_extractor.py       # Ekstraksi otomatis metadata, genre & istilah dari EPUB
│   ├── prompt_builder.py         # Generator prompt sastra adaptif berbasis genre
│   ├── core.py                   # Engine orkestrasi translasi LLM dengan caching
│   └── post_processor.py         # Parser XML DOM aman & perbaikan istilah otomatis
├── projects/                     # Folder project novel mandiri
│   ├── lord_of_the_mysteries/   # Contoh project pre-seeded (LOTM)
│   │   ├── project.json
│   │   ├── glossary.json
│   │   └── repair_map.json
│   └── .gitkeep
└── tests/
    └── test_universal_translator.py # Unit test fungsional
```

---

## 🚀 Panduan Memulai

### 1. Kloning & Masuk ke Folder
```bash
git clone https://github.com/stenlysayd/novel_epub_translator.git
cd novel_epub_translator
```

### 2. Pasang Dependensi
Pastikan Anda menggunakan Python 3.10+:
```bash
pip install -r requirements.txt
```

### 2. Atur API Key
Salin file `.env.example` menjadi `.env`:
```bash
cp .env.example .env
```
Buka file `.env` dan masukkan API Key Gemini Anda:
```env
GEMINI_API_KEY=AIzaSy...
```

---

## 🎮 Cara Penggunaan

### Mode Interaktif (Sangat Direkomendasikan)
Cukup jalankan:
```bash
python main.py
```

Anda akan disambut oleh menu terminal interaktif:
```text
==============================================================
   📚 UNIVERSAL NOVEL EPUB TRANSLATOR (v2.0)
   Multi-Project AI Translation & Auto-Glossary Detection
==============================================================
📋 DAFTAR PROYEK NOVEL TERSEDIA:
--------------------------------------------------------------
[1] Lord of the Mysteries
    ID: lord_of_the_mysteries | Genre: Victorian Grimdark | 1,240 Istilah | 0 Segmen Cache
--------------------------------------------------------------
[+] 🆕 Buat Project Baru (Input Novel EPUB Lain)
[q] 🚪 Keluar
--------------------------------------------------------------
Pilihan Anda: 
```

#### Alur Membuat Proyek Novel Baru:
1. Tekan `+` di menu utama.
2. Masukkan path file `.epub` novel Anda (misal: `C:\Books\Shadow_Slave.epub`).
3. Sistem akan otomatis membaca judul dan menanyakan apakah Anda ingin mendeteksi genre & glossary otomatis.
4. Tekan `Y`, dan dalam beberapa detik AI akan menganalisis genre novel dan menyusun glossary awal.
5. Anda langsung masuk ke dashboard novel tersebut dan siap menerjemahkan!

---

### Dashboard Proyek Novel
Saat sebuah proyek dipilih, Anda memiliki kontrol penuh:
- **`[1] Mulai / Lanjutkan Penerjemahan`**: Menerjemahkan EPUB dari awal atau melanjutkan progress cache.
- **`[2] Lihat & Tinjau Glossary Istilah`**: Melihat daftar tokoh, lokasi, sekte/organisasi, dan istilah kekuatan yang diproteksi.
- **`[3] Tambah Istilah Baru ke Glossary`**: Menambahkan nama tokoh baru yang baru muncul di bab pertengahan.
- **`[4] Tinjau & Edit Repair Map`**: Menentukan aturan koreksi khusus (misal: `Budak Bayangan=Shadow Slave`).
- **`[5] Ekstrak Ulang dari EPUB`**: Mengambil sampel bab lain untuk memperkaya glossary secara otomatis.
- **`[6] Jalankan Post-Processing / Repair Saja`**: Memperbaiki istilah novel yang sudah diterjemahkan secara offline tanpa kuota API.

---

### Mode Headless (Untuk Automasi / Skrip)
Anda juga dapat menjalankan perintah langsung melalui argumen CLI:

- **Melihat daftar project**:
  ```bash
  python main.py --list-projects
  ```
- **Menerjemahkan project tertentu**:
  ```bash
  python main.py -p lord_of_the_mysteries -i "input.epub" -o "output_indo.epub"
  ```
- **Hanya menjalankan perbaikan istilah offline**:
  ```bash
  python main.py -p lord_of_the_mysteries -i "draft.epub" --repair-only
  ```

---

## 🧪 Menjalankan Unit Test

Untuk memverifikasi siklus hidup project, adaptasi genre prompt, dan parser XML AST:
```bash
pytest tests/test_universal_translator.py -v
```

---

## ⚖️ Lisensi
Dibuat dengan ❤️ untuk komunitas pembaca dan penerjemah novel web internasional. Bebas dimodifikasi dan dikembangkan lebih lanjut.
