import os
import json
import re
from datetime import datetime
from typing import Dict, List, Optional, Any

PROJECTS_DIR = os.path.abspath(
    os.path.join(os.path.dirname(os.path.dirname(__file__)), "projects")
)


def slugify(text: str) -> str:
    """Mengubah judul/teks menjadi nama folder yang aman (slug)."""
    text = text.lower().strip()
    text = re.sub(r"[^\w\s-]", "", text)
    text = re.sub(r"[\s_-]+", "_", text)
    return text or "novel_project"


def get_project_dir(slug: str) -> str:
    """Mengembalikan path lengkap folder project."""
    return os.path.join(PROJECTS_DIR, slug)


def list_projects() -> List[Dict[str, Any]]:
    """
    Memindai folder projects/ dan mengembalikan daftar semua project yang tersimpan
    beserta statistik glossary dan cache.
    """
    os.makedirs(PROJECTS_DIR, exist_ok=True)
    projects = []

    for entry in os.listdir(PROJECTS_DIR):
        p_dir = os.path.join(PROJECTS_DIR, entry)
        if not os.path.isdir(p_dir):
            continue

        meta_file = os.path.join(p_dir, "project.json")
        if not os.path.exists(meta_file):
            continue

        try:
            with open(meta_file, "r", encoding="utf-8") as f:
                meta = json.load(f)
        except Exception:
            continue

        # Hitung jumlah istilah di glossary
        glossary_file = os.path.join(p_dir, "glossary.json")
        glossary_count = 0
        if os.path.exists(glossary_file):
            try:
                with open(glossary_file, "r", encoding="utf-8") as gf:
                    gdata = json.load(gf)
                    for cat in gdata.values():
                        if isinstance(cat, list):
                            glossary_count += len(cat)
            except Exception:
                pass

        # Hitung jumlah segmen cache
        cache_dir = os.path.join(p_dir, "cache")
        cached_chunks = 0
        if os.path.exists(cache_dir):
            cached_chunks = len([f for f in os.listdir(cache_dir) if f.endswith(".txt")])

        projects.append({
            "slug": entry,
            "title": meta.get("title", entry),
            "author": meta.get("author", "Unknown"),
            "genre": meta.get("genre", "General"),
            "tone": meta.get("tone", "Sastra & Imersif"),
            "source_epub": meta.get("source_epub", ""),
            "target_language": meta.get("target_language", "Indonesian"),
            "created_at": meta.get("created_at", ""),
            "glossary_count": glossary_count,
            "cached_chunks": cached_chunks,
            "dir_path": p_dir
        })

    # Urutkan project berdasarkan waktu terbaru
    projects.sort(key=lambda x: x.get("created_at", ""), reverse=True)
    return projects


def get_project(slug: str) -> Optional[Dict[str, Any]]:
    """Memuat data lengkap dari sebuah project."""
    p_dir = get_project_dir(slug)
    meta_file = os.path.join(p_dir, "project.json")

    if not os.path.exists(meta_file):
        return None

    with open(meta_file, "r", encoding="utf-8") as f:
        meta = json.load(f)

    # Load glossary
    glossary_file = os.path.join(p_dir, "glossary.json")
    glossary = {}
    if os.path.exists(glossary_file):
        with open(glossary_file, "r", encoding="utf-8") as f:
            glossary = json.load(f)

    # Load repair map
    repair_file = os.path.join(p_dir, "repair_map.json")
    repair_map = {}
    if os.path.exists(repair_file):
        with open(repair_file, "r", encoding="utf-8") as f:
            repair_map = json.load(f)

    cache_dir = os.path.join(p_dir, "cache")
    cached_chunks = len([f for f in os.listdir(cache_dir) if f.endswith(".txt")]) if os.path.exists(cache_dir) else 0

    return {
        "slug": slug,
        "metadata": meta,
        "glossary": glossary,
        "repair_map": repair_map,
        "cache_dir": cache_dir,
        "cached_chunks": cached_chunks,
        "dir_path": p_dir
    }


def create_project(
    title: str,
    slug: Optional[str] = None,
    author: str = "Unknown",
    genre: str = "General Fantasy",
    tone: str = "Sastra & Alami",
    source_epub: str = "",
    target_language: str = "Indonesian",
    initial_glossary: Optional[Dict[str, List[str]]] = None,
    initial_repair_map: Optional[Dict[str, str]] = None,
    custom_rules: Optional[List[str]] = None
) -> Dict[str, Any]:
    """
    Membuat project novel baru lengkap dengan strukturnya.
    """
    final_slug = slugify(slug or title)
    p_dir = get_project_dir(final_slug)
    os.makedirs(p_dir, exist_ok=True)

    cache_dir = os.path.join(p_dir, "cache")
    os.makedirs(cache_dir, exist_ok=True)

    metadata = {
        "title": title,
        "slug": final_slug,
        "author": author,
        "genre": genre,
        "tone": tone,
        "source_epub": source_epub,
        "target_language": target_language,
        "custom_rules": custom_rules or [],
        "created_at": datetime.now().isoformat(),
        "updated_at": datetime.now().isoformat()
    }

    glossary = initial_glossary or {
        "characters": [],
        "organizations": [],
        "locations": [],
        "power_system": [],
        "artifacts_items": [],
        "terminology": []
    }

    repair_map = initial_repair_map or {}

    with open(os.path.join(p_dir, "project.json"), "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2, ensure_ascii=False)

    with open(os.path.join(p_dir, "glossary.json"), "w", encoding="utf-8") as f:
        json.dump(glossary, f, indent=2, ensure_ascii=False)

    with open(os.path.join(p_dir, "repair_map.json"), "w", encoding="utf-8") as f:
        json.dump(repair_map, f, indent=2, ensure_ascii=False)

    return get_project(final_slug)


def save_project_glossary(slug: str, glossary: Dict[str, List[str]]):
    """Menyimpan pembaruan glossary project."""
    p_dir = get_project_dir(slug)
    with open(os.path.join(p_dir, "glossary.json"), "w", encoding="utf-8") as f:
        json.dump(glossary, f, indent=2, ensure_ascii=False)
    update_project_timestamp(slug)


def save_project_repair_map(slug: str, repair_map: Dict[str, str]):
    """Menyimpan pembaruan repair map project."""
    p_dir = get_project_dir(slug)
    with open(os.path.join(p_dir, "repair_map.json"), "w", encoding="utf-8") as f:
        json.dump(repair_map, f, indent=2, ensure_ascii=False)
    update_project_timestamp(slug)


def update_project_timestamp(slug: str):
    """Memperbarui waktu update project."""
    p_dir = get_project_dir(slug)
    meta_file = os.path.join(p_dir, "project.json")
    if os.path.exists(meta_file):
        try:
            with open(meta_file, "r", encoding="utf-8") as f:
                meta = json.load(f)
            meta["updated_at"] = datetime.now().isoformat()
            with open(meta_file, "w", encoding="utf-8") as f:
                json.dump(meta, f, indent=2, ensure_ascii=False)
        except Exception:
            pass
