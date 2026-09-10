# Rev A-P1 fabrication order notes

Engineering prototype – not production qualified.

Supply the bare 360 x 300 mm four-layer PCB to the Gerbers, separate PTH/NPTH
Excellon files and PCB_STACKUP_PRESSFIT.md. Copper is at least 70/35/35/70 um
finished; thickness is 1.60-1.70 mm between outer copper faces, excluding mask.
ENIG; specified FR-4 Tg125-135 C press-fit baseline. No implicit Tg170 substitute.

PRESSFIT_HOLES.csv identifies all 48 special J1-J6 holes in top-view PCB
coordinates. Excellon carries FINISHED dimensions. Do not replace its 1.475 mm
tool value by the 1.60 mm raw drill value. The fabricator must meet finished
size, raw drill, plating and annular ring jointly. Do not solder or paste these
holes. BC/NT clamp holes are a separate 3.2 mm PTH class, never press-fit holes.

Before accepting the order, the supplier must confirm the special laminate,
thickness, finished copper and bore/plating process. Include representative
press-fit and clamp coupons; their quantity/cost is additional to the one-PCB
BOM and must be stated in the quote. Coupon measurement and insertion-force
acceptance precede pressing the delivered PCB assemblies. No evidence of such
physical acceptance is claimed by this CAD package.

Electrical bare-board testing, outline dimensions, hole measurement, coating
and cleanliness inspection belong to lot acceptance. Do not change nets,
footprints, copper or stackup to meet a supplier's default process. A required
design change creates a new package version and new native checks.
