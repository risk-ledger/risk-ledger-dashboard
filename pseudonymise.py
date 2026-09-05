#!/usr/bin/env python3
"""Replace public masked handles with researcher-assigned pseudonyms.

Run from the repository root: ``python3 pseudonymise.py``.
The private mapping file is ignored by Git and must never be committed.
"""

import csv
import base64
import hashlib
import json
import pathlib
import re
import sys
import zlib


ROOT = pathlib.Path(".")
CHAPTER_DATA = ROOT / "chapter4_copytrading_metrics_anonymised.json"
INDEX_HTML = ROOT / "index.html"
NOTEBOOK = ROOT / "chapter4_copytrading_analysis_colab.ipynb"
MAP_PATH = ROOT / "pseudonym_mapping_PRIVATE.csv"

MASK_RE = re.compile(r"\*{2,4}")
LEFTOVER_RE = re.compile(r"\*{3,}")

WORDS = """
Aster Juniper Basalt Cedar Rowan Alder Vega Lyra Orion Cypress
Willow Hazel Linden Maple Sequoia Aspen Birch Elm Fir Laurel
Magnolia Myrtle Olive Pine Poplar Sage Spruce Sycamore Walnut Yew
Quartz Onyx Jasper Flint Slate Granite Marble Obsidian Pumice Shale
Topaz Garnet Beryl Opal Amber Coral Jade Pearl Agate Citrine
Sirius Rigel Altair Deneb Mira Nova Polaris Castor Pollux Antares
Capella Spica Procyon Arcturus Canopus Achird Alcor Mizar Atlas Maia
Fern Moss Ivy Clover Thistle Bramble Heather Gorse Reed Rush
Lotus Tulip Dahlia Zinnia Peony Iris Lily Orchid Poppy Violet
Basil Thyme Rosemary Mint Fennel Chervil Sorrel Tarragon Dill Anise
Cobalt Indigo Ochre Sienna Umber Sepia Cerulean Viridian Crimson Teal
Falcon Heron Kestrel Osprey Plover Swift Tern Wren Finch Lark
Brook Delta Fjord Glacier Harbor Isle Lagoon Mesa Oasis Ridge
Summit Tundra Valley Cove Dune Cliff Grove Meadow Prairie Canyon
Comet Meteor Quasar Pulsar Nebula Zenith Aurora Eclipse Solstice Equinox
Argon Neon Xenon Radon Helium Krypton Lithium Silicon Carbon Boron
Cinnabar Malachite Azurite Pyrite Galena Mica Feldspar Gypsum Halite Calcite
Sandal Ebony Mahogany Teak Bamboo Rattan Cork Balsa Larch Hemlock
Saffron Cumin Clove Nutmeg Cassia Ginger Sumac Sesame Juneberry Quince
Damson Medlar Mulberry Rowanberry Sloe Elder Hawthorn Blackthorn Dogwood Hornbeam
""".split()

PRIVACY_NOTE = (
    "Public handles are replaced with researcher-assigned pseudonyms bearing no "
    "derivation from the originals; platform account IDs are excluded."
)


def pseudonym_for_rank(index: int) -> str:
    if not 1 <= index <= len(WORDS):
        raise ValueError(f"Pseudonym rank must be between 1 and {len(WORDS)}.")
    return f"#{index:03d} {WORDS[index - 1]}"


def replace_text(path: pathlib.Path, mapping: dict[str, str]) -> None:
    text = path.read_text(encoding="utf-8")
    for alias in sorted(mapping, key=len, reverse=True):
        text = text.replace(alias, mapping[alias])
    path.write_text(text, encoding="utf-8")


def main() -> None:
    required = (CHAPTER_DATA, INDEX_HTML, NOTEBOOK)
    missing = [str(path) for path in required if not path.exists()]
    if missing:
        sys.exit("Run from the repository root; missing: " + ", ".join(missing))

    chapter = json.loads(CHAPTER_DATA.read_text(encoding="utf-8"))
    html = INDEX_HTML.read_text(encoding="utf-8")
    embedded = re.search(
        r"const DATA = (\{.*?\});\s*const FEE_DEFAULTS", html, flags=re.DOTALL
    )
    if embedded is None:
        sys.exit("Could not locate the embedded dashboard dataset in index.html.")
    dashboard = json.loads(embedded.group(1))
    records = chapter["records"]
    traders = dashboard["traders"]
    if len(records) != 200 or len(traders) != 200 or len(WORDS) != 200:
        sys.exit("Expected exactly 200 chapter records, dashboard traders, and pseudonym words.")

    mapping: dict[str, str] = {}
    for index, (record, trader) in enumerate(zip(records, traders), start=1):
        pseudonym = pseudonym_for_rank(index)
        chapter_alias = record.get("trader_alias")
        dashboard_alias = trader.get("name")
        if not isinstance(chapter_alias, str) or not MASK_RE.search(chapter_alias):
            sys.exit(f"Unexpected chapter alias format at rank {index}.")
        if not isinstance(dashboard_alias, str) or not MASK_RE.search(dashboard_alias):
            sys.exit(f"Unexpected dashboard alias format at rank {index}.")
        mapping[chapter_alias] = pseudonym
        mapping[dashboard_alias] = pseudonym

    for path in (CHAPTER_DATA, INDEX_HTML):
        if path.exists():
            replace_text(path, mapping)

    chapter = json.loads(CHAPTER_DATA.read_text(encoding="utf-8"))
    chapter.setdefault("metadata", {})["privacy"] = PRIVACY_NOTE
    CHAPTER_DATA.write_text(
        json.dumps(chapter, ensure_ascii=False, indent=1) + "\n", encoding="utf-8"
    )

    # Keep the Colab fallback payload, checksum and privacy assertions aligned
    # with the newly pseudonymised frozen dataset.
    raw = CHAPTER_DATA.read_bytes()
    digest = hashlib.sha256(raw).hexdigest()
    embedded = base64.b64encode(zlib.compress(raw, level=9)).decode("ascii")
    notebook = json.loads(NOTEBOOK.read_text(encoding="utf-8"))
    for cell in notebook.get("cells", []):
        source = cell.get("source", [])
        for i, line in enumerate(source):
            line = line.replace(
                "partially " + "masked trader aliases",
                "researcher-assigned pseudonyms",
            )
            if line.lstrip().startswith("(for example,"):
                line = line.replace(line[line.index("`") : line.rindex("`") + 1], "`#017 Aster`")
            line = line.replace(
                "contain only " + "masked",
                "contain only researcher-assigned pseudonyms and",
            )
            line = line.replace("aliases and aggregate/derived measures", "aggregate/derived measures")
            if line.startswith("EXPECTED_SHA256 = "):
                line = f'EXPECTED_SHA256 = "{digest}"\n'
            elif line.startswith("EMBEDDED_DATA_B64 = "):
                line = f'EMBEDDED_DATA_B64 = "{embedded}"\n'
            elif 'str.contains(r"\\*\\*\\*"' in line:
                line = 'assert df["trader_alias"].str.fullmatch(r"#\\d{3} [A-Za-z]+").all()\n'
            source[i] = line
    NOTEBOOK.write_text(
        json.dumps(notebook, ensure_ascii=False, indent=1) + "\n", encoding="utf-8"
    )

    with MAP_PATH.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(("original_alias", "pseudonym"))
        for alias, pseudonym in mapping.items():
            writer.writerow((alias, pseudonym))

    checked = (CHAPTER_DATA, INDEX_HTML, NOTEBOOK)
    leftovers = {
        str(path): len(LEFTOVER_RE.findall(path.read_text(encoding="utf-8")))
        for path in checked
        if path.exists()
    }
    total_left = sum(leftovers.values())
    print(f"Assigned 200 pseudonyms across {len(mapping)} source-handle variants.")
    print(f"Leftover mask-pattern strings across public artefacts: {total_left}")
    print(f"Private mapping written to {MAP_PATH}; this path is excluded by .gitignore.")
    if total_left:
        for path, count in leftovers.items():
            if count:
                print(f"  {path}: {count}")
        raise SystemExit(1)


if __name__ == "__main__":
    main()
