# PSU Format Notes

## Scope

This document records the functional knowledge currently used by the project when manipulating Midnight Club 3 Remix `.psu` files.

The project does not yet claim a complete implementation of the PlayStation 2 PSU container format. The first release treats the tested `.psu` file as a binary save image and modifies only mapped regions.

## Known file size

Reference save files used during the current research contain:

```text
152,064 bytes
```

The tool reports a warning when a file has another size but does not automatically reject it. This makes comparison and research possible without silently treating every variation as invalid.

## Current workflow

```text
PCSX2 memory card
        ↓
myMC+ export
        ↓
.psu file
        ↓
MC3 Save Editor
        ↓
new .psu file
        ↓
myMC+ import
        ↓
in-game validation
```

## Save identity

The project distinguishes between concepts that may appear related but should not be treated as identical without validation:

- PSU directory name;
- internal save identifier;
- visible save nickname or title;
- save data and career state.

Fixed-length ASCII replacement is available as a controlled research operation. It does not claim to rebuild all PSU directory metadata.

## Research status

| Area | Status |
|---|---|
| File loading and cloning | Working |
| Expected file size | Verified on current reference saves |
| Garage binary region | Working and tested |
| Internal ASCII search | Working |
| Fixed-length ASCII replacement | Working as a controlled binary operation |
| Full PSU directory parser | Not implemented |
| General checksum reconstruction | Not implemented |
| Complete save identity model | Research |

## Safety rule

The project writes modified data to a new path. The original save should remain untouched and backed up.
