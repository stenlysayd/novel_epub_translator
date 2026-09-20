import os
from typing import Optional, Callable
from dotenv import load_dotenv
from tqdm import tqdm
from epub_translator import LLM, translate, SubmitKind

from .project_manager import get_project, update_project_timestamp
from .prompt_builder import build_dynamic_prompt
from .post_processor import repair_epub_file

load_dotenv()


def get_llm_instance(
    api_key: Optional[str] = None,
    model: Optional[str] = None,
    temperature: Optional[float] = None,
    cache_path: str = "./cache"
) -> LLM:
    """Menginisialisasi objek LLM dengan kredensial environment atau parameter."""
    key = api_key or os.getenv("GEMINI_API_KEY")
    if not key:
        raise ValueError(
            "Kunci API Gemini tidak ditemukan!\n"
            "Silakan atur di file .env:\n"
            "GEMINI_API_KEY=AIzaSy...\n"
            "atau berikan melalui parameter."
        )

    model_name = model or os.getenv("DEFAULT_MODEL", "gemini-2.5-flash")
    temp = temperature if temperature is not None else float(os.getenv("DEFAULT_TEMPERATURE", "0.15"))

    os.makedirs(cache_path, exist_ok=True)

    return LLM(
        key=key,
        url="https://generativelanguage.googleapis.com/v1beta/openai/",
        model=model_name,
        token_encoding="cl100k_base",
        temperature=temp,
        cache_path=cache_path
    )


def translate_project(
    slug: str,
    source_epub: str,
    target_epub: str,
    concurrency: int = 3,
    temperature: Optional[float] = None,
    model: Optional[str] = None,
    api_key: Optional[str] = None,
    skip_post_process: bool = False,
    on_progress_callback: Optional[Callable[[float], None]] = None
):
    """
    Menjalankan translasi novel untuk sebuah project:
    1. Membaca data project (metadata, genre, glossary, repair_map)
    2. Merakit prompt dinamis adaptif
    3. Mengeksekusi penerjemahan dengan cache terisolasi
    4. Menjalankan XML AST post-processing secara otomatis
    """
    proj = get_project(slug)
    if not proj:
        raise ValueError(f"Project '{slug}' tidak ditemukan!")

    if not os.path.exists(source_epub):
        raise FileNotFoundError(f"File EPUB sumber tidak ditemukan di: {source_epub}")

    meta = proj["metadata"]
    glossary = proj["glossary"]
    repair_map = proj["repair_map"]
    cache_dir = proj["cache_dir"]

    # 1. Bangun Prompt
    prompt = build_dynamic_prompt(
        title=meta.get("title", slug),
        genre=meta.get("genre", "General Fantasy"),
        tone=meta.get("tone", "Sastra & Alami"),
        target_language=meta.get("target_language", "Indonesian"),
        glossary=glossary,
        custom_rules=meta.get("custom_rules", [])
    )

    # 2. Setup LLM
    llm = get_llm_instance(
        api_key=api_key,
        model=model,
        temperature=temperature,
        cache_path=cache_dir
    )

    # 3. Progress Tracking
    pbar = tqdm(total=100, desc=f"Menerjemahkan: {meta.get('title', slug)}", unit="%")
    last_p = [0.0]

    def _progress_handler(prog: float):
        inc = (prog - last_p[0]) * 100
        if inc > 0:
            pbar.update(inc)
            last_p[0] = prog
        if on_progress_callback:
            on_progress_callback(prog)

    print(f"\n[ENGINE] Memulai translasi: {meta.get('title', slug)}")
    print(f"[CACHE] Folder cache project: {cache_dir}")
    print(f"[TARGET] Output file: {target_epub}")

    try:
        translate(
            source_path=source_epub,
            target_path=target_epub,
            target_language=meta.get("target_language", "Indonesian"),
            submit=SubmitKind.REPLACE,
            llm=llm,
            user_prompt=prompt,
            concurrency=concurrency,
            on_progress=_progress_handler
        )
    finally:
        pbar.close()

    print(f"\n✅ Translasi awal selesai: {target_epub}")

    # 4. Post-processing & Auto-repair
    if not skip_post_process and repair_map:
        print("[INFO] Menjalankan Layer 2 XML AST Post-Processor...")
        audit_path = os.path.join(proj["dir_path"], "audit_report.json")
        stats = repair_epub_file(
            input_path=target_epub,
            repair_map=repair_map,
            output_path=target_epub,
            audit_log_path=audit_path
        )
        print(f"✅ Post-processing selesai! {stats['repairs_made']} istilah berhasil disinkronkan.")
    elif not repair_map:
        print("[INFO] Repair map kosong untuk project ini. Melewati post-processing.")

    update_project_timestamp(slug)
