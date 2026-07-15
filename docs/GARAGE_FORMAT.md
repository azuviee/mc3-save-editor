# Garage Binary Format

## Confirmed map

```text
Garage start:      0xC568
Slot size:         0x104 bytes / 260 bytes
Slot count:        30
Garage end:        0xE3E0
```

The offset of slot `n` is:

```text
0xC568 + (n × 0x104)
```

## Global garage header

The first bytes of slot `0` have a special role:

```text
slot 0 + 0x00 = visible vehicle count
slot 0 + 0x01 = active or selected vehicle index
```

Because of this, writing an exported vehicle block directly into slot `0` can corrupt the garage state.

The safe import path rewrites these bytes based on the destination save.

## Slot model

Each garage slot is currently represented as an opaque 260-byte binary record.

Known operations do not need to understand every property inside the block:

- read;
- export;
- replace;
- append;
- restore;
- search for a `vp_` vehicle identifier;
- extract printable ASCII strings.

This allows the garage library to remain useful while deeper reverse engineering continues.

## Visible count and physical slots

A save always contains space for 30 slot records, but only the first `visible_count` records are treated as visible vehicles by the current model.

An exported garage includes all 30 physical slots and a manifest describing:

- slot index;
- offset;
- filename;
- visibility;
- empty status;
- detected vehicle identifier;
- detected display string;
- first 16 bytes.

## Empty slot detection

The current implementation considers a slot empty when its first four bytes are zero.

This rule is useful operationally but should continue to be validated as more garage states are collected.

## Safe import behavior

### Import slot

- validates the destination index;
- validates that the `.bin` file has exactly 260 bytes;
- preserves or rebuilds the slot `0` header;
- increases the visible count when inserting beyond the current end.

### Append

- accepts one or multiple `.bin` files or exported directories;
- skips empty slots by default;
- starts at the current visible count;
- rejects the entire operation when the final count would exceed 30;
- writes a new `.psu`.

### Import all

- restores an exported directory;
- uses `manifest.json` when available;
- restores the visible count;
- preserves safe slot `0` handling unless raw mode is requested.

## Research direction

Future garage modules can be added without rewriting the slot engine:

```text
garage/
├── slots.py
├── scanner.py
├── importer.py
├── exporter.py
├── identifiers.py
├── wheels.py
├── customization.py
├── performance.py
└── comparison.py
```
