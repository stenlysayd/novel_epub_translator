#!/usr/bin/env python3
"""
Universal Novel EPUB Translator
Interactive Multi-Project Manager & Auto-Glossary AI Translation Platform
"""

import os
import sys
import argparse
from typing import Optional, Dict

from translator.project_manager import (
    list_projects,
    get_project,
    create_project,
    save_project_glossary,
    save_project_repair_map,
    slugify
)
from translator.entity_extractor import (
    read_epub_metadata,
    sample_epub_chapters,
    analyze_novel_context_and_entities
)
from translator.core import translate_project
from translator.post_processor import repair_epub_file


BANNER = """
==============================================================
   📚 UNIVERSAL NOVEL EPUB TRANSLATOR (v2.0)
   Multi-Project AI Translation & Auto-Glossary Detection
==============================================================
"""


def clear_screen():
    os.system("cls" if os.name == "nt" else "clear")


def print_banner():
    print(BANNER)


def interactive_create_project():
    print_banner()
    print("✨ PEMBUATAN PROYEK NOVEL BARU\n" + "-"*50)

    epub_path = input(">> Masukkan path file EPUB novel (.epub): ").strip(' "\'')
    if not os.path.exists(epub_path):
        print(f"\n❌ Error: File '{epub_path}' tidak ditemukan!")
        input("\nTekan Enter untuk kembali...")
        return

    print("\n🔍 Membaca metadata EPUB...")
    meta = read_epub_metadata(epub_path)
    print(f"   Judul Terdeteksi : {meta['title']}")
    print(f"   Penulis          : {meta['author']}")

    default_slug = slugify(meta['title'])
    slug_input = input(f"\n>> Masukkan ID/Slug Project (Tekan Enter untuk '{default_slug}'): ").strip()
    project_slug = slug_input if slug_input else default_slug

    existing = get_project(project_slug)
    if existing:
        print(f"\n⚠️ Project dengan slug '{project_slug}' sudah ada!")
        input("\nTekan Enter untuk kembali...")
        return

    run_auto_extract = input("\n>> Jalankan deteksi otomatis genre & istilah dari EPUB? [Y/n]: ").strip().lower()

    genre = "General Fantasy"
    tone = "Sastra & Alami"
    glossary = {
        "characters": [],
        "organizations": [],
        "locations": [],
        "power_system": [],
        "artifacts_items": [],
        "terminology": []
    }
    repair_map = {}

    if run_auto_extract in ("", "y", "yes"):
        print("\n⏳ Mengambil sampel bab awal dan menganalisis konteks novel...")
        samples = sample_epub_chapters(epub_path, max_samples=4)
        if samples:
            analysis = analyze_novel_context_and_entities(samples)
            genre = analysis.get("genre", genre)
            tone = analysis.get("tone", tone)
            glossary = analysis.get("glossary", glossary)
            repair_map = analysis.get("suggested_repair_map", {})

            term_count = sum(len(v) for v in glossary.values() if isinstance(v, list))
            print(f"\n✨ Analisis Selesai!")
            print(f"   Genre Terdeteksi  : {genre}")
            print(f"   Tone Rekomendasi  : {tone}")
            print(f"   Istilah Ditemukan : {term_count} entitas")
        else:
            print("[WARN] Gagal mengambil sampel teks. Menggunakan profil standar.")

    # Simpan Project Baru
    proj = create_project(
        title=meta["title"],
        slug=project_slug,
        author=meta["author"],
        genre=genre,
        tone=tone,
        source_epub=epub_path,
        initial_glossary=glossary,
        initial_repair_map=repair_map
    )

    print(f"\n🎉 Project '{project_slug}' berhasil dibuat!")
    input("\nTekan Enter untuk masuk ke menu project...")
    interactive_project_dashboard(project_slug)


def interactive_project_dashboard(slug: str):
    while True:
        clear_screen()
        print_banner()

        proj = get_project(slug)
        if not proj:
            print(f"❌ Project '{slug}' tidak ditemukan!")
            input("Tekan Enter...")
            return

        meta = proj["metadata"]
        glossary = proj["glossary"]
        repair_map = proj["repair_map"]
        cache_count = proj["cached_chunks"]

        term_count = sum(len(v) for v in glossary.values() if isinstance(v, list))

        print(f"📖 PROYEK: {meta.get('title')} (ID: {slug})")
        print(f"   Genre       : {meta.get('genre')} | Penulis: {meta.get('author')}")
        print(f"   Tone        : {meta.get('tone')}")
        print(f"   Source EPUB : {meta.get('source_epub') or 'Belum disetel'}")
        print(f"   Glossary    : {term_count} istilah kanonikal")
        print(f"   Repair Map  : {len(repair_map)} aturan koreksi")
        print(f"   Cache       : {cache_count} segmen tersimpan")
        print("-" * 62)
        print("[1] 🚀 Mulai / Lanjutkan Penerjemahan")
        print("[2] 📋 Lihat & Tinjau Glossary Istilah")
        print("[3] ➕ Tambah Istilah Baru ke Glossary")
        print("[4] 🔧 Tinjau & Edit Repair Map")
        print("[5] 🔄 Ekstrak Ulang / Perkaya Glossary dari EPUB")
        print("[6] 🧹 Jalankan Post-Processing / Repair Saja (Offline)")
        print("[b] ⬅️ Kembali ke Menu Utama")
        print("-" * 62)

        choice = input("Pilihan Anda: ").strip().lower()

        if choice == "1":
            default_in = meta.get("source_epub", "")
            in_file = input(f">> File input EPUB [{default_in}]: ").strip(' "\'') or default_in
            if not in_file or not os.path.exists(in_file):
                print(f"❌ File input tidak valid!")
                input("Tekan Enter...")
                continue

            default_out = f"{slug}_Indo.epub"
            out_file = input(f">> File output EPUB [{default_out}]: ").strip(' "\'') or default_out

            concurrency_str = input(">> Concurrency (thread paralel) [3]: ").strip()
            concurrency = int(concurrency_str) if concurrency_str.isdigit() else 3

            try:
                translate_project(
                    slug=slug,
                    source_epub=in_file,
                    target_epub=out_file,
                    concurrency=concurrency
                )
                input("\n✅ Selesai! Tekan Enter untuk kembali ke dashboard...")
            except KeyboardInterrupt:
                print("\n⚠️ Dihentikan manual. Cache tersimpan.")
                input("Tekan Enter...")
            except Exception as e:
                print(f"\n❌ Terjadi kesalahan: {e}")
                input("Tekan Enter...")

        elif choice == "2":
            print("\n📋 DAFTAR GLOSSARY:")
            for cat, items in glossary.items():
                print(f"\n[{cat.upper()}] ({len(items)} item):")
                if items:
                    print(", ".join(items[:40]) + ("..." if len(items) > 40 else ""))
                else:
                    print("- (kosong)")
            input("\nTekan Enter...")

        elif choice == "3":
            print("\n➕ TAMBAH ISTILAH BARU:")
            print("Kategori: [1] characters, [2] organizations, [3] locations, [4] power_system, [5] artifacts_items, [6] terminology")
            cat_map = {
                "1": "characters", "2": "organizations", "3": "locations",
                "4": "power_system", "5": "artifacts_items", "6": "terminology"
            }
            c_sel = input("Pilih nomor kategori: ").strip()
            cat_name = cat_map.get(c_sel, "terminology")
            new_terms = input("Masukkan istilah (pisahkan dengan koma): ").strip()
            if new_terms:
                term_list = [t.strip() for t in new_terms.split(",") if t.strip()]
                current = glossary.get(cat_name, [])
                current.extend(term_list)
                glossary[cat_name] = sorted(list(set(current)))
                save_project_glossary(slug, glossary)
                print(f"✅ {len(term_list)} istilah berhasil ditambahkan ke '{cat_name}'.")
            input("Tekan Enter...")

        elif choice == "4":
            print("\n🔧 REPAIR MAP (Koreksi Otomatis):")
            for w, c in list(repair_map.items())[:25]:
                print(f"  - '{w}' ➡️ '{c}'")
            print(f"Total: {len(repair_map)} aturan.")
            add_more = input("\nTambah aturan baru? (Format: Salah=Benar, kosongkan jika tidak): ").strip()
            if "=" in add_more:
                w, c = add_more.split("=", 1)
                repair_map[w.strip()] = c.strip()
                save_project_repair_map(slug, repair_map)
                print("✅ Aturan berhasil ditambahkan!")
            input("Tekan Enter...")

        elif choice == "5":
            src = meta.get("source_epub")
            if not src or not os.path.exists(src):
                src = input(">> Masukkan path EPUB: ").strip(' "\'')
            if os.path.exists(src):
                print("⏳ Mengekstrak sampel dari buku...")
                samples = sample_epub_chapters(src, max_samples=5)
                analysis = analyze_novel_context_and_entities(samples)
                new_gl = analysis.get("glossary", {})
                # Gabungkan dengan yang sudah ada
                for k, v in new_gl.items():
                    current = glossary.get(k, [])
                    current.extend(v)
                    glossary[k] = sorted(list(set(current)))
                save_project_glossary(slug, glossary)
                print("✅ Glossary berhasil diperkaya dengan sampel baru!")
            input("Tekan Enter...")

        elif choice == "6":
            target_in = input(">> Masukkan path EPUB yang ingin diperbaiki: ").strip(' "\'')
            if os.path.exists(target_in):
                out = input(f">> Output file [{target_in}]: ").strip(' "\'') or target_in
                audit_path = os.path.join(proj["dir_path"], "audit_report.json")
                stats = repair_epub_file(target_in, repair_map, out, audit_path)
                print(f"\n✅ Selesai! {stats['repairs_made']} perbaikan dilakukan pada {stats['documents_scanned']} dokumen.")
            else:
                print("❌ File tidak ditemukan!")
            input("Tekan Enter...")

        elif choice == "b":
            break


def interactive_main_menu():
    while True:
        clear_screen()
        print_banner()

        projects = list_projects()

        print("📋 DAFTAR PROYEK NOVEL TERSEDIA:\n" + "-"*62)
        if not projects:
            print("   (Belum ada project novel. Silakan buat project baru.)")
        else:
            for idx, p in enumerate(projects, 1):
                title = p["title"]
                genre = p["genre"]
                terms = p["glossary_count"]
                cache = p["cached_chunks"]
                print(f"[{idx}] {title}")
                print(f"    ID: {p['slug']} | Genre: {genre} | {terms} Istilah | {cache} Segmen Cache")

        print("-" * 62)
        print("[+] 🆕 Buat Project Baru (Input Novel EPUB Lain)")
        print("[q] 🚪 Keluar")
        print("-" * 62)

        choice = input("Pilihan Anda: ").strip()

        if choice.lower() == "q":
            print("\nSampai jumpa lagi!")
            sys.exit(0)

        elif choice == "+":
            interactive_create_project()

        elif choice.isdigit():
            idx = int(choice) - 1
            if 0 <= idx < len(projects):
                interactive_project_dashboard(projects[idx]["slug"])
            else:
                print("Pilihan nomor tidak valid.")
                input("Tekan Enter...")


def headless_cli():
    parser = argparse.ArgumentParser(description="Universal Novel EPUB Translator CLI")
    parser.add_argument("--list-projects", action="store_true", help="Tampilkan semua project yang ada.")
    parser.add_argument("-p", "--project", help="ID/Slug project yang ingin digunakan.")
    parser.add_argument("-i", "--input", help="Path file EPUB input.")
    parser.add_argument("-o", "--output", help="Path file EPUB output.")
    parser.add_argument("-c", "--concurrency", type=int, default=3, help="Jumlah concurrent workers.")
    parser.add_argument("--repair-only", action="store_true", help="Hanya jalankan perbaikan offline XML AST.")
    parser.add_argument("--create-project", action="store_true", help="Buat project baru dari CLI.")
    parser.add_argument("--title", help="Judul novel untuk project baru.")
    parser.add_argument("--genre", default="General Fantasy", help="Genre novel.")

    args = parser.parse_args()

    if args.list_projects:
        for p in list_projects():
            print(f"- {p['title']} [{p['slug']}] ({p['genre']})")
        return

    if args.create_project:
        if not args.input or not args.title:
            print("Error: --input dan --title diperlukan untuk membuat project.")
            sys.exit(1)
        create_project(title=args.title, slug=args.project, source_epub=args.input, genre=args.genre)
        print(f"Project '{args.title}' berhasil dibuat.")
        return

    if args.project:
        proj = get_project(args.project)
        if not proj:
            print(f"Error: Project '{args.project}' tidak ditemukan.")
            sys.exit(1)

        in_file = args.input or proj["metadata"].get("source_epub")
        out_file = args.output or f"{args.project}_Indo.epub"

        if args.repair_only:
            stats = repair_epub_file(in_file, proj["repair_map"], out_file)
            print(f"Repair selesai: {stats['repairs_made']} istilah diperbaiki.")
            return

        translate_project(slug=args.project, source_epub=in_file, target_epub=out_file, concurrency=args.concurrency)
        return

    # Jika tidak ada argumen CLI yang diberikan, buka mode interaktif
    interactive_main_menu()


if __name__ == "__main__":
    if len(sys.argv) > 1:
        headless_cli()
    else:
        interactive_main_menu()
