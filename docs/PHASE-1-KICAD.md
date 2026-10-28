# Phase 1 — KiCad design

## What the board does

The XIAO RP2040 samples a 3.3 V analog microphone module and renders a radial audio spectrum on the round GC9A01 display. The encoder changes modes or sensitivity and its push switch selects an option. A buffered data output drives a chain of six rear-facing WS2812B LEDs for ambient light.

The display connector, microphone connector, and encoder are on the front/control side. The addressable LEDs are placed on the rear so the enclosure can use reflected light instead of six bright points facing the user.

## Pin map

| XIAO pin | Net | Function |
| --- | --- | --- |
| D0 / A0 | `MIC_OUT` | Analog microphone sample |
| D1 | `TFT_RST` | Display reset |
| D2 | `TFT_CS` | Display chip select |
| D3 | `TFT_DC` | Display data/command |
| D4 | `ENC_A` | Encoder phase A |
| D5 | `ENC_B` | Encoder phase B |
| D6 | `ENC_SW` | Encoder push switch |
| D7 | `LED_DATA_RAW` | Raw 3.3 V LED data into U2 |
| D8 | `TFT_SCK` | SPI clock |
| D9 | — | Reserved for a later feature |
| D10 | `TFT_MOSI` | SPI data to display |
| 3V3 | `+3V3` | Display logic, microphone, encoder pull-ups |
| 5V | `+5V` | WS2812 chain and level shifter |

The TFT backlight is tied to 3.3 V in Phase 1. If independent backlight dimming is important later, D9 can drive a transistor in a board revision.

## Electrical choices

- The analog microphone keeps the SPI bus and remaining pins simple while still supporting FFT-based visualization.
- The 74AHCT1G125 converts the RP2040's 3.3 V data signal into a 5 V logic signal for reliable WS2812 operation.
- R1 is a 330 ohm series resistor at the LED-chain input.
- C7 is the level-shifter bypass capacitor and C8 is the LED-chain bulk capacitor.
- Six LEDs can theoretically draw much more current at full white than a small USB source should supply. Firmware must cap brightness and avoid unrestricted full-white output.

## Layout

- Board size: 58 mm x 58 mm, rounded corners
- Stackup: two copper layers
- Mounting: four 3.2 mm M3 clearance holes
- Minimum routed track width used: 0.15 mm
- Signal/zone clearance setting: 0.15 mm minimum, with 0.30 mm ground-zone clearance
- Via size: 0.60 mm with 0.30 mm drill
- Ground pours: front and rear

## Checks performed

### ERC

KiCad reports 0 errors and 3 warnings. All three warnings say a placed custom symbol does not match the cached copy in the project-local library (`XIAO_RP2040`, `GC9A01_Round_TFT`, and `Analog_Mic_Module`). They are library-cache provenance warnings, not open pins or conflicting drivers.

### DRC

KiCad reports 0 errors and 5 warnings:

- Four mounting-hole footprints are intentionally embedded/local copies and differ from the installed KiCad library revision.
- The rear `D6` reference text is close to the rounded board edge. The electrical footprint and copper remain inside the board.

Before ordering, re-run ERC/DRC in the installed KiCad version and compare the Gerbers to the chosen board house's minimum trace, clearance, annular-ring, and edge-clearance rules.

## Screenshot log

1. `01-project-created.png` — new Pulse Halo KiCad project
2. `02-controller-module.png` — custom XIAO RP2040 symbol and controller block
3. `03-display-mic-controls.png` — display, microphone, and encoder blocks
4. `04-led-halo-and-level-shifter.png` — buffered LED halo chain
5. `05-complete-connected-schematic.png` — completed connected schematic
6. `06-erc-zero-errors.png` — schematic after ERC corrections, with zero electrical errors
7. `07-pcb-imported-unplaced.png` — footprints imported to PCB before placement
8. `08-functional-placement.png` — functional component placement and board outline
9. `09-routed-front-copper.png` — front-side routing and ground pour
10. `10-routed-rear-led-copper.png` — rear LED routing and ground pour
11. `11-final-3d-board.png` — final 3D PCB render

## Phase boundary

Phase 1 ends with the editable KiCad sources, manufacturing exports, STEP board export, validation reports, and the 11-image work log. The enclosure/display bezel and stand belong to Phase 2 in Fusion; firmware visualization modes and behavior changes belong to Phase 3.

