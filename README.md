# Pulse Halo

Pulse Halo is a small desktop audio visualizer built around a 1.28-inch round GC9A01 TFT. A microphone module feeds a XIAO RP2040, which will draw the circular spectrum spikes seen in music-visualizer videos. A rotary encoder controls the display, and six rear-facing WS2812B LEDs add a soft wall/desk glow.

The design target is a complete project under the Hack Club $50 cap, including shipping and tax. Phase 1 deliberately uses inexpensive modules and commonly stocked parts; purchasing and landed-price verification will happen before ordering.

## Project status

- **Phase 1 — KiCad:** complete design package in this repository
- **Phase 2 — Fusion:** not started
- **Phase 3 — firmware, features, and revisions:** not started

This is a design-checked PCB, not a fabricated or hardware-tested board yet.

## Phase 1 hardware

- Seeed Studio XIAO RP2040 controller module
- 1.28-inch 240x240 GC9A01 SPI round TFT module
- 3.3 V analog microphone module
- EC11 rotary encoder with push switch
- Six rear-mounted WS2812B LEDs
- 74AHCT1G125 3.3 V-to-5 V LED data buffer
- 330 ohm WS2812 data resistor
- 100 nF local bypass capacitor and 100 uF LED bulk capacitor
- 58 mm x 58 mm rounded two-layer PCB with four M3 mounting holes

USB powers the XIAO and the board. Firmware must impose a conservative global LED brightness limit so the six LEDs and display stay within the available USB current.

## Repository map

- `hardware/kicad/` — editable KiCad project, local symbol library, and XIAO footprint
- `docs/PHASE-1-KICAD.md` — architecture, pin map, checks, and screenshot index
- `docs/screenshots/phase-1/` — 11 unique progress screenshots
- `docs/exports/Pulse-Halo-schematic.pdf` — readable schematic export
- `manufacturing/gerbers/` — copper, mask, silkscreen, outline, and job files
- `manufacturing/drill/` — PTH/NPTH Excellon files and drill maps
- `manufacturing/assembly/Pulse-Halo-BOM.csv` — generated PCB BOM
- `manufacturing/Pulse-Halo-board.step` — board export for Phase 2 enclosure work

## Validation snapshot

- ERC: 0 errors, 3 warnings. The warnings are cache/library comparison notices for the three project-local symbols.
- DRC: 0 errors, 5 warnings. Four warnings are local mounting-hole footprint/library comparison notices; one is the back-silkscreen D6 reference near the rounded board edge.
- Routing: 0 unrouted nets after routing, with front and rear ground pours.

The warnings and generated fabrication package should be reviewed once more against the exact PCB manufacturer's rules before ordering.

