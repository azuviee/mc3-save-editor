#!/usr/bin/env python3
"""
MC3 Garage Tool V0.2
Midnight Club 3: DUB Edition Remix (PS2) .psu garage slot importer/exporter.

V0.2 adds secure import via append:
- export-slot
- export-all
- explicit import-slot, to replace a chosen slot
- append, to add one or more .bin files to the end of the visible garage

Known map:
GARAGE_START = 0xC568
SLOT_SIZE = 0x104 / 260 bytes
SLOT_COUNT = 30

Experimentally discovered observation:
In slot 0, the first bytes function as the global garage header:
+0x00 = number of visible vehicles
+0x01 = index/probable position of the selected/active vehicle

Therefore, when the tool writes to slot 0, it preserves/rewrites this header.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

GARAGE_START = 0xC568
SLOT_SIZE = 0x104
SLOT_COUNT = 30
EXPECTED_PSU_SIZE = 152_064
GLOBAL_HEADER_LEN = 2  # slot 0 +0x00 e +0x01


def read_file(path: Path) -> bytes:
    if not path.exists():
        raise FileNotFoundError(f"File not found: {path}")
    return path.read_bytes()


def write_file(path: Path, data: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data)


def validate_psu(data: bytes) -> None:
    if len(data) != EXPECTED_PSU_SIZE:
        print(f"AVISO: tamanho do PSU = {len(data)} bytes; expected = {EXPECTED_PSU_SIZE} bytes.")


def validate_slot(index: int) -> None:
    if index < 0 or index >= SLOT_COUNT:
        raise ValueError(f"Invalid slot: {index}. Use 0 a {SLOT_COUNT - 1}.")


def slot_offset(index: int) -> int:
    validate_slot(index)
    return GARAGE_START + (index * SLOT_SIZE)


def get_slot(data: bytes, index: int) -> bytes:
    off = slot_offset(index)
    return data[off:off + SLOT_SIZE]


def garage_count(data: bytes) -> int:
    return data[GARAGE_START]


def active_index(data: bytes) -> int:
    return data[GARAGE_START + 1]


def set_garage_header(data: bytes, count: int, selected: int | None = None) -> bytes:
    if count < 0 or count > SLOT_COUNT:
        raise ValueError(f"Invalid number of vehicles: {count}. Use 0 to {SLOT_COUNT}.")
    if selected is None:
        selected = active_index(data)
    selected = max(0, min(selected, max(count - 1, 0)))

    b = bytearray(data)
    b[GARAGE_START] = count
    b[GARAGE_START + 1] = selected
    return bytes(b)


def normalize_slot_for_write(data: bytes, index: int, slot_data: bytes, final_count: int | None = None) -> bytes:
    """Prepares a block for writing.

    When the destination is slot 0, the first 2 bytes cannot blindly come from the .bin file,

    because they control the global garage. They are either preserved or updated.
    """
    if len(slot_data) != SLOT_SIZE:
        raise ValueError(f"Slot importado tem {len(slot_data)} bytes; esperado {SLOT_SIZE}.")

    block = bytearray(slot_data)
    if index == 0:
        count = garage_count(data) if final_count is None else final_count
        selected = active_index(data)
        if count <= 1:
            selected = 0
        else:
            selected = max(0, min(selected, count - 1))
        block[0] = count
        block[1] = selected
    return bytes(block)


def set_slot(data: bytes, index: int, slot_data: bytes, final_count: int | None = None) -> bytes:
    validate_slot(index)
    block = normalize_slot_for_write(data, index, slot_data, final_count=final_count)
    off = slot_offset(index)
    return data[:off] + block + data[off + SLOT_SIZE:]


def is_empty_slot(slot_data: bytes) -> bool:
    return slot_data[:4] == b"\x00\x00\x00\x00"


def ascii_strings(blob: bytes, min_len: int = 4) -> list[str]:
    found = re.findall(rb"[ -~]{" + str(min_len).encode() + rb",}", blob)
    return [x.decode("ascii", errors="ignore") for x in found]


def vehicle_id(slot_data: bytes) -> str | None:
    m = re.search(rb"vp_[A-Za-z0-9_]+", slot_data)
    return m.group(0).decode("ascii", errors="ignore") if m else None


def display_name(slot_data: bytes) -> str | None:
    strings = ascii_strings(slot_data)
    clean = [s.strip() for s in strings if s.strip()]
    if not clean:
        return None
    candidates = [s for s in clean if not s.startswith("vp_")]
    return candidates[-1] if candidates else vehicle_id(slot_data)


def safe_name(text: str) -> str:
    return re.sub(r"[^A-Za-z0-9_.-]+", "_", text).strip("_") or "unknown"


def collect_bin_files(paths: list[Path], include_empty: bool = False) -> list[Path]:
    files: list[Path] = []
    for p in paths:
        if p.is_dir():
            manifest = p / "manifest.json"
            if manifest.exists():
                info = json.loads(manifest.read_text(encoding="utf-8"))
                for entry in info.get("slots", []):
                    if not include_empty and entry.get("empty") is True:
                        continue
                    f = p / entry["filename"]
                    if f.exists():
                        files.append(f)
            else:
                files.extend(sorted(p.glob("*.bin")))
        else:
            files.append(p)

    clean_files: list[Path] = []
    for f in files:
        if f.suffix.lower() != ".bin":
            continue
        data = read_file(f)
        if len(data) != SLOT_SIZE:
            raise ValueError(f"{f} tem {len(data)} bytes; esperado {SLOT_SIZE}.")
        if include_empty or not is_empty_slot(data):
            clean_files.append(f)
    return clean_files


def scan(psu: Path) -> None:
    data = read_file(psu)
    validate_psu(data)
    count = garage_count(data)
    selected = active_index(data)

    print(f"File: {psu}")
    print(f"Size: {len(data)} bytes")
    print(f"Garage start: 0x{GARAGE_START:X}")
    print(f"Slot size:    0x{SLOT_SIZE:X} / {SLOT_SIZE} bytes")
    print(f"Slot count:   {SLOT_COUNT}")
    print(f"Header:       visible vehicles = {count} | likely active index = {selected}")
    print()
    print("SLOT | OFFSET | VISIBLE | STATUS | VEHICLE_ID | NAME")
    print("-" * 90)

    for i in range(SLOT_COUNT):
        block = get_slot(data, i)
        visible = "YES" if i < count else "NO "
        status = "EMPTY" if is_empty_slot(block) else "USED "
        vid = vehicle_id(block) or "-"
        name = display_name(block) or "-"
        print(f"{i:02d}   | 0x{slot_offset(i):05X} | {visible:^7} | {status} | {vid:<24} | {name}")


def export_slot(psu: Path, index: int, out_file: Path) -> None:
    data = read_file(psu)
    validate_psu(data)
    block = get_slot(data, index)
    write_file(out_file, block)
    print(f"Exported slot{index:02d} 0x{slot_offset(index):X} to: {out_file}")


def export_all(psu: Path, out_dir: Path) -> None:
    data = read_file(psu)
    validate_psu(data)

    out_dir.mkdir(parents=True, exist_ok=True)

    for i in range(SLOT_COUNT):
        block = get_slot(data, i)
        vid = vehicle_id(block) or f"slot_{i:02d}"
        filename = f"{safe_name(vid)}.bin"
        write_file(out_dir / filename, block)

    print(f"Exported {SLOT_COUNT} vehicle files to: {out_dir}")


def import_slot(psu: Path, slot_bin: Path, index: int, out_psu: Path, raw: bool = False) -> None:
    data = read_file(psu)
    validate_psu(data)
    block = read_file(slot_bin)
    if len(block) != SLOT_SIZE:
        raise ValueError(f"{slot_bin} tem {len(block)} bytes; expected {SLOT_SIZE}.")

    if raw:
        off = slot_offset(index)
        new_data = data[:off] + block + data[off + SLOT_SIZE:]
        note = "RAW / in preserving header"
    else:
        final_count = max(garage_count(data), index + 1)
        new_data = set_slot(data, index, block, final_count=final_count)
        # Se colocou depois do final visível, aumenta o contador.
        if final_count != garage_count(new_data):
            new_data = set_garage_header(new_data, final_count)
        note = "secure / preserves slot 0 header"

    write_file(out_psu, new_data)
    print(f"Imported {slot_bin} no slot {index:02d} / offset 0x{slot_offset(index):X}")
    print(f"Mode: {note}")
    print(f"Visible vehicles: {garage_count(data)} -> {garage_count(new_data)}")
    print(f"New save: {out_psu}")


def append(psu: Path, inputs: list[Path], out_psu: Path, include_empty: bool = False) -> None:
    data = read_file(psu)
    validate_psu(data)
    files = collect_bin_files(inputs, include_empty=include_empty)
    if not files:
        raise ValueError("No valid .bin file found to add.")

    start_count = garage_count(data)
    if start_count > SLOT_COUNT:
        raise ValueError(f"Invalid counter in save: {start_count}")
    if start_count + len(files) > SLOT_COUNT:
        raise ValueError(
            f"Not enough space: save has {start_count} visible vehicles and you tried to add {len(files)}. "
            f"Limit = {SLOT_COUNT}."
        )

    final_count = start_count + len(files)
    for n, f in enumerate(files):
        target_slot = start_count + n
        block = read_file(f)
        data = set_slot(data, target_slot, block, final_count=final_count)
        vid = vehicle_id(block) or f.name
        print(f"Append: {f.name} -> slot {target_slot:02d} | {vid}")

    data = set_garage_header(data, final_count)
    write_file(out_psu, data)
    print(f"Visible vehicles: {start_count} -> {final_count}")
    print(f"New save: {out_psu}")


def import_all(psu: Path, import_dir: Path, out_psu: Path, raw: bool = False) -> None:
    data = read_file(psu)
    validate_psu(data)

    manifest_path = import_dir / "manifest.json"
    if manifest_path.exists():
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        entries = manifest.get("slots", [])
        visible_count = int(manifest.get("visible_count", SLOT_COUNT))
        for entry in entries:
            i = int(entry["slot"])
            block = read_file(import_dir / entry["filename"])
            if raw:
                off = slot_offset(i)
                data = data[:off] + block + data[off + SLOT_SIZE:]
            else:
                data = set_slot(data, i, block, final_count=visible_count)
        if not raw:
            data = set_garage_header(data, visible_count)
    else:
        for i in range(SLOT_COUNT):
            matches = sorted(import_dir.glob(f"slot_{i:02d}*.bin"))
            if not matches:
                raise FileNotFoundError(f"Could not find file for slot {i:02d} in {import_dir}")
            block = read_file(matches[0])
            data = set_slot(data, i, block, final_count=SLOT_COUNT)
        if not raw:
            data = set_garage_header(data, SLOT_COUNT)

    write_file(out_psu, data)
    print(f"Imported slots from {import_dir}")
    print(f"New save: {out_psu}")


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description="MC3 Garage Tool V0.2")
    sub = parser.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("scan", help="Displays the 30 slots and the garage counter")
    p.add_argument("psu", type=Path)

    p = sub.add_parser("export-slot", help="Exports a specific slot")
    p.add_argument("psu", type=Path)
    p.add_argument("slot", type=int)
    p.add_argument("out_bin", type=Path)

    p = sub.add_parser("export-all", help="Exports all 30 slots")
    p.add_argument("psu", type=Path)
    p.add_argument("out_dir", type=Path)

    p = sub.add_parser("import-slot", help="Replaces/inserts into a specific slot")
    p.add_argument("psu", type=Path)
    p.add_argument("slot_bin", type=Path)
    p.add_argument("slot", type=int)
    p.add_argument("out_psu", type=Path)
    p.add_argument("--raw", action="store_true", help="Raw mode: copies 260 bytes without protecting the slot 0 header")

    p = sub.add_parser("append", help="Adds one or multiple .bin files to the end of the visible garage")
    p.add_argument("psu", type=Path)
    p.add_argument("out_psu", type=Path)
    p.add_argument("bins", nargs="+", type=Path, help=".bin files or exported folder with manifest.json")
    p.add_argument("--include-empty", action="store_true", help="Includes empty slots when adding from a folder")

    p = sub.add_parser("import-all", help="Replaces the entire garage with an exported folder")
    p.add_argument("psu", type=Path)
    p.add_argument("import_dir", type=Path)
    p.add_argument("out_psu", type=Path)
    p.add_argument("--raw", action="store_true", help="Raw mode: copies exactly the exported slots")

    args = parser.parse_args(argv)

    try:
        if args.cmd == "scan":
            scan(args.psu)
        elif args.cmd == "export-slot":
            export_slot(args.psu, args.slot, args.out_bin)
        elif args.cmd == "export-all":
            export_all(args.psu, args.out_dir)
        elif args.cmd == "import-slot":
            import_slot(args.psu, args.slot_bin, args.slot, args.out_psu, raw=args.raw)
        elif args.cmd == "append":
            append(args.psu, args.bins, args.out_psu, include_empty=args.include_empty)
        elif args.cmd == "import-all":
            import_all(args.psu, args.import_dir, args.out_psu, raw=args.raw)
        else:
            parser.error("Invalid command")
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))