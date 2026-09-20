import os
import json
import re
from typing import Dict, List, Optional, Any
from bs4 import BeautifulSoup, NavigableString
import ebooklib
from ebooklib import epub
from tqdm import tqdm


def get_sorted_repair_patterns(repair_map: Dict[str, str]) -> List[tuple]:
    """
    Mengurutkan seluruh entri perbaikan dari string terpanjang ke terpendek
    untuk mencegah tabrakan pemotongan kata majemuk (Longest-First Principle).
    """
    sorted_items = sorted(
        repair_map.items(),
        key=lambda x: len(x[0]),
        reverse=True
    )
    patterns = []
    for wrong, correct in sorted_items:
        if wrong.strip():
            pat = re.compile(rf"\b{re.escape(wrong)}\b", re.IGNORECASE)
            patterns.append((pat, wrong, correct))
    return patterns


def repair_text_content(
    text: str,
    patterns: List[tuple],
    audit_log: Optional[List[Dict]] = None,
    filename: str = ""
) -> str:
    """Menjalankan penggantian pola istilah terurut pada string teks."""
    if not text or not text.strip():
        return text

    for pat, wrong, correct in patterns:
        if pat.search(text):
            if audit_log is not None:
                audit_log.append({
                    "file": filename,
                    "original": wrong,
                    "replaced_with": correct,
                    "snippet": text[:80] + "..." if len(text) > 80 else text
                })
            text = pat.sub(correct, text)

    return text


def process_xhtml_safely(
    xhtml: str,
    patterns: List[tuple],
    audit_log: Optional[List[Dict]] = None,
    filename: str = ""
) -> str:
    """
    Memproses dokumen XHTML secara aman:
    Hanya mengganti isi node NavigableString, melewati tag <style>, <script>, dan <head>.
    Menjamin keutuhan format buku EPUB 100%.
    """
    soup = BeautifulSoup(xhtml, "lxml-xml")

    for node in soup.descendants:
        if isinstance(node, NavigableString):
            content = str(node)
            if not content.strip():
                continue

            # Lewati tag metadata dan stylesheet
            if node.parent and node.parent.name in ("style", "script", "head", "title"):
                continue

            repaired = repair_text_content(content, patterns, audit_log=audit_log, filename=filename)
            if repaired != content:
                node.replace_with(repaired)

    return str(soup)


def repair_epub_file(
    input_path: str,
    repair_map: Dict[str, str],
    output_path: Optional[str] = None,
    audit_log_path: Optional[str] = None
) -> Dict[str, Any]:
    """
    Memindai dan memperbaiki file EPUB secara offline menggunakan repair map project.
    """
    if not os.path.exists(input_path):
        raise FileNotFoundError(f"File EPUB input tidak ditemukan: {input_path}")

    target_output = output_path or input_path
    book = epub.read_epub(input_path)

    patterns = get_sorted_repair_patterns(repair_map)
    audit_log: List[Dict] = []
    scanned_pages = 0

    items = [it for it in book.get_items() if it.get_type() == ebooklib.ITEM_DOCUMENT]

    for item in tqdm(items, desc="Post-processing XHTML"):
        filename = item.get_name()
        try:
            raw_content = item.get_content().decode("utf-8")
            clean_content = process_xhtml_safely(
                raw_content,
                patterns,
                audit_log=audit_log,
                filename=filename
            )
            item.set_content(clean_content.encode("utf-8"))
            scanned_pages += 1
        except Exception as e:
            print(f"\n[WARN] Lewati halaman {filename} karena error: {e}")

    epub.write_epub(target_output, book)

    if audit_log_path:
        with open(audit_log_path, "w", encoding="utf-8") as f:
            json.dump(audit_log, f, indent=2, ensure_ascii=False)

    return {
        "documents_scanned": scanned_pages,
        "repairs_made": len(audit_log),
        "output_file": target_output
    }
