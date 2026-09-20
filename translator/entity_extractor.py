import os
import json
import re
from typing import Dict, List, Tuple, Optional, Any
from bs4 import BeautifulSoup
import ebooklib
from ebooklib import epub
from openai import OpenAI
from json_repair import loads as json_repair_loads


def read_epub_metadata(epub_path: str) -> Dict[str, str]:
    """Mengekstrak judul, penulis, dan metadata dari file EPUB."""
    if not os.path.exists(epub_path):
        raise FileNotFoundError(f"File EPUB tidak ditemukan: {epub_path}")

    try:
        book = epub.read_epub(epub_path)
    except Exception as e:
        filename = os.path.basename(epub_path)
        clean_name = os.path.splitext(filename)[0]
        return {
            "title": clean_name,
            "author": "Unknown",
            "language": "en",
            "description": ""
        }

    # Ambil judul
    title_meta = book.get_metadata("DC", "title")
    title = title_meta[0][0] if title_meta and title_meta[0] else os.path.splitext(os.path.basename(epub_path))[0]

    # Ambil penulis
    creator_meta = book.get_metadata("DC", "creator")
    author = creator_meta[0][0] if creator_meta and creator_meta[0] else "Unknown"

    # Ambil bahasa
    lang_meta = book.get_metadata("DC", "language")
    language = lang_meta[0][0] if lang_meta and lang_meta[0] else "en"

    # Ambil deskripsi
    desc_meta = book.get_metadata("DC", "description")
    description = desc_meta[0][0] if desc_meta and desc_meta[0] else ""

    return {
        "title": str(title).strip(),
        "author": str(author).strip(),
        "language": str(language).strip(),
        "description": str(description).strip()
    }


def sample_epub_chapters(epub_path: str, max_samples: int = 5) -> List[str]:
    """Mengambil sampel teks narasi dari bab-bab awal novel EPUB."""
    book = epub.read_epub(epub_path)
    samples = []

    for item in book.get_items():
        if item.get_type() == ebooklib.ITEM_DOCUMENT:
            soup = BeautifulSoup(item.get_content(), "html.parser")
            text = soup.get_text(separator="\n").strip()
            # Lewati halaman depan / TOC / cover yang terlalu pendek
            if len(text) > 800:
                samples.append(text[:6000])
                if len(samples) >= max_samples:
                    break

    return samples


def analyze_novel_context_and_entities(
    samples: List[str],
    api_key: Optional[str] = None,
    model: str = "gemini-2.5-flash"
) -> Dict[str, Any]:
    """
    Menggunakan LLM untuk mendeteksi genre, gaya bahasa/tone yang cocok,
    dan mengekstrak istilah-istilah entitas penting dari sampel teks novel.
    """
    key = api_key or os.getenv("GEMINI_API_KEY") or os.getenv("OPENAI_API_KEY")
    if not key:
        print("[WARN] Tidak ada API Key untuk ekstraksi otomatis. Menggunakan profil default.")
        return {
            "genre": "General Fantasy",
            "tone": "Sastra & Alami",
            "glossary": {
                "characters": [],
                "organizations": [],
                "locations": [],
                "power_system": [],
                "artifacts_items": [],
                "terminology": []
            },
            "suggested_repair_map": {}
        }

    client = OpenAI(
        api_key=key,
        base_url="https://generativelanguage.googleapis.com/v1beta/openai/"
    )

    combined_text = "\n\n--- SAMPLE CHAPTER BREAK ---\n\n".join(samples[:4])

    prompt = f"""
Anda adalah pakar sastra novel web dan lokalisasi penerjemahan.
Analisis kutipan novel berikut dan berikan analisis lengkap dalam format JSON yang valid.

TUGAS ANDA:
1. "detected_genre": Tentukan genre spesifik novel (contoh: "Xianxia / Cultivation", "LitRPG / System Hunter", "Western Victorian Grimdark", "High Fantasy", "Cyberpunk / Sci-Fi", dll).
2. "tone_recommendation": Rekomendasi nuansa terjemahan Indonesia (contoh: untuk Xianxia gunakan istilah ranah kultivasi yang megah; untuk LitRPG gunakan istilah game/stats yang modern; untuk Victorian gunakan sastra klasik).
3. "glossary": Ekstrak istilah penting DALAM BAHASA INGGRIS ASLINYA (JANGAN DITERJEMAHKAN).
   Kategori:
   - "characters": Nama-nama tokoh / karakter utama.
   - "organizations": Nama sekte, klan, guild, gereja, ordo, atau faksi.
   - "locations": Nama kota, benua, dunia, dungeon, atau tempat penting.
   - "power_system": Nama ranah kultivasi, tingkat sequence, skill, mantra, atau sistem kekuatan.
   - "artifacts_items": Nama senjata, ramuan, artefak, atau pil pusaka.
   - "terminology": Istilah khusus dunia novel ini.
4. "suggested_repair_map": Pasangan istilah yang sering salah diterjemahkan harfiah oleh AI ke bahasa Indonesia beserta bentuk aslinya (contoh: {{"Klan Daun Merah": "Red Leaf Clan"}}).

OUTPUT HARUS BERUPA JSON VALID:
{{
  "detected_genre": "...",
  "tone_recommendation": "...",
  "glossary": {{
    "characters": [],
    "organizations": [],
    "locations": [],
    "power_system": [],
    "artifacts_items": [],
    "terminology": []
  }},
  "suggested_repair_map": {{}}
}}

TEXT SAMPLE:
{combined_text[:18000]}
"""

    try:
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": "You are a novel translation and entity extraction expert. Return only JSON."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.1
        )
        content = response.choices[0].message.content
        data = json_repair_loads(content)
        if isinstance(data, str):
            data = json_repair_loads(data)

        if not isinstance(data, dict):
            raise ValueError("Respon bukan dictionary")

        return {
            "genre": data.get("detected_genre", "General Fantasy"),
            "tone": data.get("tone_recommendation", "Sastra & Alami"),
            "glossary": data.get("glossary", {
                "characters": [],
                "organizations": [],
                "locations": [],
                "power_system": [],
                "artifacts_items": [],
                "terminology": []
            }),
            "suggested_repair_map": data.get("suggested_repair_map", {})
        }
    except Exception as e:
        print(f"[WARN] Ekstraksi otomatis LLM gagal: {e}. Menggunakan profil default.")
        return {
            "genre": "General Fantasy",
            "tone": "Sastra & Alami",
            "glossary": {
                "characters": [],
                "organizations": [],
                "locations": [],
                "power_system": [],
                "artifacts_items": [],
                "terminology": []
            },
            "suggested_repair_map": {}
        }
