import pytest
import os
import sys
import shutil

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from translator.project_manager import (
    slugify,
    create_project,
    get_project,
    list_projects,
    save_project_glossary,
    save_project_repair_map,
    get_project_dir
)
from translator.prompt_builder import build_dynamic_prompt
from translator.post_processor import process_xhtml_safely, get_sorted_repair_patterns


@pytest.fixture(autouse=True)
def cleanup_test_project():
    test_slug = "test_shadow_slave"
    test_dir = get_project_dir(test_slug)
    if os.path.exists(test_dir):
        shutil.rmtree(test_dir)
    yield
    if os.path.exists(test_dir):
        shutil.rmtree(test_dir)


def test_slugify():
    assert slugify("Lord of the Mysteries (Vol 3)!") == "lord_of_the_mysteries_vol_3"
    assert slugify("Shadow Slave: The First Nightmare") == "shadow_slave_the_first_nightmare"
    assert slugify("Reverend Insanity") == "reverend_insanity"


def test_project_lifecycle():
    # 1. Buat project
    proj = create_project(
        title="Shadow Slave",
        slug="test_shadow_slave",
        author="Guiltythree",
        genre="LitRPG / Dark Fantasy",
        tone="Nuansa misterius, mimpi buruk, dan sistem RPG",
        initial_glossary={
            "characters": ["Sunny", "Nephis", "Cassie"],
            "power_system": ["Shadow Slave", "Ascended", "Transcendent"]
        },
        initial_repair_map={
            "Budak Bayangan": "Shadow Slave"
        }
    )

    assert proj is not None
    assert proj["slug"] == "test_shadow_slave"
    assert proj["metadata"]["title"] == "Shadow Slave"
    assert len(proj["glossary"]["characters"]) == 3

    # 2. Update Glossary
    proj["glossary"]["characters"].append("Effie")
    save_project_glossary("test_shadow_slave", proj["glossary"])

    updated = get_project("test_shadow_slave")
    assert "Effie" in updated["glossary"]["characters"]

    # 3. List projects
    all_projs = list_projects()
    slugs = [p["slug"] for p in all_projs]
    assert "test_shadow_slave" in slugs


def test_dynamic_prompt_builder():
    # Uji adaptasi genre Xianxia
    prompt_xianxia = build_dynamic_prompt(
        title="Reverend Insanity",
        genre="Xianxia / Cultivation",
        tone="Kultivasi gelap dan dunia persilatan",
        glossary={"characters": ["Fang Yuan"], "power_system": ["Spring Autumn Cicada"]}
    )
    assert "XIANXIA" in prompt_xianxia
    assert "Fang Yuan" in prompt_xianxia
    assert "Spring Autumn Cicada" in prompt_xianxia

    # Uji adaptasi genre LitRPG
    prompt_litrpg = build_dynamic_prompt(
        title="Solo Leveling",
        genre="LitRPG / Hunter System",
        tone="Modern Dungeon Hunter",
        glossary={"characters": ["Sung Jin-woo"], "power_system": ["Shadow Monarch"]}
    )
    assert "LITRPG" in prompt_litrpg
    assert "Sung Jin-woo" in prompt_litrpg


def test_xml_ast_post_processing():
    repair_map = {
        "Dunia Roh": "Spirit World",
        "Dunia": "The World",
        "Klan Daun Merah": "Red Leaf Clan"
    }

    patterns = get_sorted_repair_patterns(repair_map)

    xhtml = """<?xml version='1.0' encoding='utf-8'?>
    <html>
      <head>
        <style>.dunia-class { color: red; }</style>
        <title>Bab 1: Dunia Roh</title>
      </head>
      <body>
        <p>Dia melangkah ke Dunia Roh.</p>
        <p>Mereka diserang oleh anggota Klan Daun Merah.</p>
      </body>
    </html>"""

    res = process_xhtml_safely(xhtml, patterns)

    # Pastikan tag <style> tidak tersentuh
    assert ".dunia-class { color: red; }" in res
    # Pastikan 'Dunia Roh' menjadi 'Spirit World' (bukan 'The World Roh')
    assert "Dia melangkah ke Spirit World." in res
    # Pastikan 'Klan Daun Merah' direplace dengan benar
    assert "Red Leaf Clan" in res
