# Reverse-Engineering Notes

## Purpose

This file is the technical memory of the project. It should record confirmed behavior, experiments, failures and open questions.

The repository may be useful before every structure is understood. A binary region can first be manipulated safely as an opaque block and later be decoded property by property.

## Method

1. create controlled save states;
2. export `.psu` files using myMC+;
3. compare binary differences;
4. isolate stable offsets and structures;
5. create the smallest possible modification;
6. import the modified save;
7. validate behavior in PCSX2;
8. record success, crash, loading failure or unexpected behavior.

## Confirmed garage behavior

- garage region starts at `0xC568`;
- each vehicle slot occupies `0x104` bytes;
- the current garage contains 30 physical slots;
- the first byte of slot `0` controls the visible vehicle count;
- the second byte is associated with the selected or active vehicle index;
- complete slot blocks can be exported and imported;
- several slot blocks can be appended when capacity is available;
- copying slot `0` requires special header protection.

## Save-game research

The save-game layer is intentionally less prescriptive than the garage layer.

Current useful operations:

- clone an exported `.psu`;
- inspect file size and hash;
- locate ASCII identifiers;
- perform equal-length replacements;
- maintain multiple career snapshots.

## Experimental findings

Use this section for features that work in limited conditions but are not yet fully mapped.

| Experiment | Input | Modification | Result | Status |
|---|---|---|---|---|
| Example | Base save | Replace vehicle slot | Loaded in game | Verified |

## Failed experiments

Crashes and loading failures are valuable results. Record them rather than deleting them.

| Experiment | Progress | Result |
|---|---:|---|
| H | 6% | Crash after loading |
| I | 0% | Crash after loading |
| D | 6% | Passed initial loading, then remained stuck |
| E | 5% | Crash after loading |
| F | 5% | Crash after loading |
| J | 7% | Crash after loading |
| K | 0% | Crash after loading |

## Open questions

- complete structure of each 260-byte vehicle record;
- exact wheel model and wheel-size fields;
- customization and material properties;
- performance upgrade representation;
- robust vehicle display-name mapping;
- empty-slot variants;
- save directory metadata inside the PSU;
- career progression dependencies and integrity rules.
