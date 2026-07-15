# Development Guide

## Architecture rule

The command-line interface does not own binary logic.

```text
CLI → service function → binary model → file output
```

Reusable behavior belongs inside `src/mc3_save_editor/`.

Scripts inside `scripts/` are convenience entry points and examples.

## Modules

### `psu`

Generic file-level operations:

- load;
- validate;
- write;
- hash;
- search;
- fixed-length replacement.

### `savegame`

Operations that represent a save workflow:

- inspect;
- clone;
- future identity management;
- future nickname and career metadata.

### `garage`

Garage-specific binary knowledge:

- constants;
- slot addressing;
- header handling;
- scanning;
- import and export;
- identifiers.

## Adding a new garage feature

A new decoded property should normally follow this sequence:

1. document the evidence in `REVERSE_ENGINEERING.md`;
2. add offsets or parsing logic in a focused module;
3. expose a small reusable function;
4. add a CLI command only after the function is stable;
5. add at least one binary fixture test;
6. validate the output in PCSX2.

## Compatibility

Do not silently generalize findings from one game region or save version.

Future compatibility metadata should include:

- game title;
- region;
- executable identifier;
- save size;
- source save hash;
- test result.

## Raw mode

Raw mode bypasses header protection and exists for deliberate experiments. New user-facing operations should default to safe behavior.
