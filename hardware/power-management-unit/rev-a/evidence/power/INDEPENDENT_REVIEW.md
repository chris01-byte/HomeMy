# Power-agent integration review — 2026-09-10

This is a document/circuit review, not physical validation. Reviewed the chopper
connectivity generator and mechanics analysis, root footprint generator, and
controller manufacturer drawings. No CAD files were edited by this reviewer.

## Footprint findings sent to the CAD owner

* TPS48110 DGX0019A land example, datasheet p. 49: row centers ±2.2 mm,
  peripheral pads 1.45 × 0.30 mm, pitch 0.5 mm; omit physical pin 16. Initial
  generator used ±2.15 mm and 1.10 mm length; owner notified to correct it.
* Nexperia SOT8000A p. 10: mounting base is centered on both package axes,
  10.8 × 7.25 mm nominal. Initial generator shifted base pad 13 by −0.55 mm
  in y; owner notified to center it. The nominal body is 12 × 9.4 mm and
  overall lead span 12 mm. Project 1.2 × 1.9 mm lands centered at ±5.65 mm
  extend to ±6.6 mm: 0.6 mm toe beyond nominal leadspan, not the original
  comment's 0.3 mm. That toe/heel shape is a project land, not a manufacturer
  recommended footprint. Assembly-process review still applies.
* LM74930 RGE0024T p. 40: EP 2.1 × 2.1 mm must float. Peripheral reference
  lands are 0.6 × 0.25 mm with centers ±1.9 mm. The maintained KiCad
  RGE0024C non-via footprint matches EP, numbering and 0.5 mm pitch, but uses
  longer 0.875 mm lands at ±1.9375 mm; it is not dimensionally identical.
  Extra heel/toe copper does not contact the isolated EP. The CAD owner may
  retain this reviewed footprint with the difference recorded or reproduce
  the TI land example. Do not silently use the TPS26631 2.7 mm EP footprint.
* TPS26631 U3/U4 use the available Texas_RGE0024H VQFN footprint with
  2.7 mm EP. OUT17 is electrical power-output; internally common OUT18 is
  passive in ERC, preserving detection of different IC output contention.
* PTVS1 DFN body maximum is 8.1 × 6.1 mm. A courtyard computed solely from
  asymmetric pad extents was too small; owner notified to use body maximum
  plus courtyard allowance. Shunt pad geometry matches the distinct force
  and sense lands in the CSS4J drawing.

## Chopper circuit review

LM339B comparator polarities were checked against the generator: low
MOTION_BUS requests off, rising bus crosses the request threshold, separate
OV pulls its healthy node low, hot/shorted NTC pulls the thermal node low,
and open NTC crosses the upper threshold. The thermal comparators share an
open-collector healthy node. Q41/Q44 release the UCC27511 inverting inhibit
only after reference qualification and healthy thermal inputs. An OV event
signals the motion latch while the local resistor chopper continues. Thermal
fault inhibits the driver and signals the same external safety path.

The reference supervisor and Q43 prevent the optocoupler fault LED from
asserting merely because the motion-powered reference is not yet operating.
This avoids a motion-start deadlock. The fault optocoupler remains released
when unpowered. The driver pull-up and pull-down outputs use separate
resistors. The flyback diode cathode is on MOTION_BUS, anode on the switched
drain, so turn-off current recirculates toward the resistor feed. The drain
and motion SMCJ43A clamps operate among 100 V components; they are not the
main/system 56 V-typical TVS.

A shorted chopper MOSFET cannot be cleared by its own gate. Heating must
assert the independent thermal path, causing the motion series switch to
remove its battery feed. Main-path shutdown and fault diagnostics are
separate system behavior; do not call the chopper gate a redundant breaker.
External resistor mounting and pulse qualification remain as specified in
CHOPPER_MECHANICS.md. Energy qualification does not prove unlimited duty.

The chopper agent identified an independent motion native-UV autorecovery
path. It was corrected by U5 TLV3011B, whose open-drain UV output joins
MOTION_FLT_N and the external motion latch. Native EN falling and rising
thresholds are distinct; the former is the relevant no-restart comparison.
Static threshold margins and finite pulse-response limits are recorded in
POWER_STAGE.md and calculated.json.

The two added 470 µF motion capacitors require a new inrush case. Four total
gate charges size BST, but only two input-bank Miller charges are credited
for slew. R34 was increased to 180 kΩ and motion gate bleeds to 10 MΩ. The
estimated ramp/current is useful for prototype setting selection; no table
minimum at 50 V/25 A can prove the full 42 V low-current startup waveform.

## Placement interpretation

placement-power.json includes all power components. KiCad +90 degrees maps
local source pads on the bottom edge toward board right; +270 maps them
left. Q1–3/Q7–8 and Q4–6/Q9–10 therefore face their common sources inward.
Gate-resistor coordinates use the physical transformed gate-pad position.
The main and motion 33 µF film bodies require 24 mm height clearance.
Courtyard collision, routed gate loops, copper width and creepage checks
remain responsibilities of the assembled CAD review, not this placement file.
