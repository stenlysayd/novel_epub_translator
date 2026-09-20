from typing import Dict, List, Optional


def format_glossary_for_prompt(glossary: Dict[str, List[str]], max_per_category: int = 50) -> str:
    """Mengubah dictionary glossary menjadi format ringkasan untuk prompt LLM."""
    sections = []
    category_labels = {
        "characters": "NAMA KARAKTER / TOKOH",
        "organizations": "SEKTE / KLAN / ORGANISASI / FAKSI",
        "locations": "NAMA KOTA / DUNIA / TEMPAT",
        "power_system": "RANAH KEKUATAN / SEQUENCE / SKILL",
        "artifacts_items": "SENJATA / ARTEFAK / ITEM PENTING",
        "terminology": "ISTILAH KHUSUS DUNIA NOVEL"
    }

    for key, label in category_labels.items():
        items = glossary.get(key, [])
        if items:
            clean_items = [str(x).strip() for x in items if str(x).strip()]
            sampled = clean_items[:max_per_category]
            sections.append(f"[{label} - JANGAN DITERJEMAHKAN]:\n" + ", ".join(sampled))

    return "\n\n".join(sections) if sections else "Tidak ada glossary spesifik."


def get_genre_specific_instructions(genre: str) -> str:
    """Menyediakan instruksi khusus sesuai genre novel."""
    g_lower = genre.lower()

    if "xianxia" in g_lower or "cultivation" in g_lower or "wuxia" in g_lower:
        return """
[PANDUAN GENRE: XIANXIA / KULTIVASI PERSILATAN]
1. RANAH KULTIVASI & DAO: Pertahankan nama ranah (misal: Qi Condensation, Foundation Establishment, Golden Core, Nascent Soul) atau sebutkan dalam istilah baku yang konsisten.
2. SEBUTAN PERSAUDARAAN: Terjemahkan gelar sosial persilatan dengan luwes (Senior Brother -> Kakak Seperguruan Senior, Sect Master -> Ketua Sekte, Elder -> Tetua).
3. HUKUM DAO & JURUS: Nama jurus, teknik pedang, dan pil spiritual dibiarkan dalam bahasa Inggris/Pinyin aslinya.
""".strip()

    elif "litrpg" in g_lower or "system" in g_lower or "hunter" in g_lower or "game" in g_lower:
        return """
[PANDUAN GENRE: LITRPG / SYSTEM / HUNTER NOVEL]
1. JENDELA SISTEM: Format notifikasi sistem `[ ... ]` harus dipertahankan persis.
2. ISTILAH GAME & STATUS: Biarkan istilah teknis RPG dalam Bahasa Inggris (misal: Status Window, Quest, Skill, Buff/Debuff, Cooldown, Dungeon, Raid, Mana, HP).
3. PERINGKAT & KELAS: Format peringkat hunter/item (misal: S-Rank, A-Rank, Mythic, Legendary, Awakener) TETAP INGGRIS.
""".strip()

    elif "victorian" in g_lower or "grimdark" in g_lower or "steampunk" in g_lower or "mystery" in g_lower:
        return """
[PANDUAN GENRE: VICTORIAN / GRIMDARK / MYSTERY FANTASY]
1. NUANSA SASTRA: Gunakan diksi bergaya novel abad ke-19, misterius, elegan, dan dewasa.
2. GELAR & BANGSAWAN: Nama gereja, dewa-dewi, ordo rahasia, serta artefak tersegel DILARANG DITERJEMAHKAN.
3. URUTAN KEKUATAN: Terjemahkan "Sequence X" -> "Urutan X", namun nama job/jalur tetap Inggris.
""".strip()

    elif "sci-fi" in g_lower or "cyberpunk" in g_lower:
        return """
[PANDUAN GENRE: SCI-FI / CYBERPUNK]
1. ISTILAH TEKNOLOGI: Nama augmentasi cybernetic, AI, megakorporasi, dan kapal antariksa tetap dalam Bahasa Inggris.
2. DIKSI: Gunakan gaya bahasa tajam, futuristik, dan berirama cepat.
""".strip()

    else:
        return """
[PANDUAN GENRE: HIGH FANTASY / UMUM]
1. ALUR SASTRA: Terjemahkan narasi secara luwes, jangan harfiah. Utamakan kalimat aktif jika bahasa Indonesia lebih enak dibaca.
2. NAMA & TEMPAT: Semua nama tokoh, kerajaan, kota, ras, dan pusaka legendaris TETAP dalam bahasa Inggris aslinya.
""".strip()


def build_dynamic_prompt(
    title: str,
    genre: str,
    tone: str,
    target_language: str = "Indonesian",
    glossary: Optional[Dict[str, List[str]]] = None,
    custom_rules: Optional[List[str]] = None
) -> str:
    """
    Menyusun System Prompt komprehensif yang dirancang khusus untuk novel ini.
    """
    glossary_text = format_glossary_for_prompt(glossary or {})
    genre_rules = get_genre_specific_instructions(genre)

    custom_rules_block = ""
    if custom_rules:
        custom_rules_block = "\n[ATURAN KHUSUS TAMBAHAN PENGGUNA]:\n" + "\n".join(f"- {r}" for r in custom_rules)

    prompt = f"""
PERAN:
Anda adalah penerjemah sastra profesional untuk novel: "{title}".
Tugas Anda adalah menerjemahkan teks dari Bahasa Inggris ke Bahasa {target_language} dengan standar penerbitan novel resmi.

[PROFIL NOVEL & TONE]
- Judul Novel : {title}
- Genre Utama : {genre}
- Karakter Tone : {tone}

[ATURAN UTAMA PENERJEMAHAN]
1. GAYA BAHASA SASTRA: DILARANG menerjemahkan secara kaku kata demi kata. Gunakan kalimat bahasa Indonesia yang hidup, mengalir alami, dan nyaman dibaca (natural prose).
2. NAMA DAN ISTILAH KHUSUS (PROPER NOUNS): DILARANG KERAS menerjemahkan Nama Tokoh, Nama Tempat, Organisasi, Fraksi, dan Istilah Kunci. Biarkan persis dalam Bahasa Inggris Asli.
3. STRUKTUR KALIMAT: Hindari terjemahan pasif bahasa Inggris yang terdengar canggung dalam bahasa Indonesia. Ubah menjadi kalimat aktif jika terasa lebih luwes.

{genre_rules}
{custom_rules_block}

[DATABASE GLOSSARY NOVEL (ISTILAH WAJIB PERSIS INGGRIS)]
{glossary_text}

PERINTAH:
Terjemahkan teks berikut ke Bahasa {target_language}:
""".strip()

    return prompt
