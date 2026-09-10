# Design-input generator reproducibility review

rev_a_engineering_prototype: true  
rev_b_production: false

On 2026-09-10, all **7 tested generators and 14 output artifacts** reproduced the current authoritative files byte for byte in an isolated temporary copy. The final audit was repeated after the annotated PCB was stable and mechanical provenance, BOM, release state and manufacturing exports had been finalized. No stale generator output or dropped corrections remained. The repeated generator execution used isolated copies; no native PCB was regenerated.

| Generator | Outputs | Result |
|---|---:|---|
| `design/build_power_parts.py` | 1 | Exit 0; every output byte-identical |
| `design/build_chopper_parts.py` | 1 | Exit 0; every output byte-identical |
| `design/build_power_placement.py` | 1 | Exit 0; every output byte-identical |
| `design/power_calculations.py` | 1 | Exit 0; every output byte-identical |
| `design/calculate_chopper.py` | 1 | Exit 0; every output byte-identical |
| `manufacturing/build_mechanical.py` | 4 | Exit 0; every output byte-identical |
| `scripts/build_bom.py` | 5 | Exit 0; every output byte-identical |

A supplemental isolated run of `scripts/build_footprints.py` reproduced all **48 vendored library definitions with identical s-expression content**; 44 files are also byte-identical, while the four annotated custom libraries differ only in serialization formatting. All 421 footprint pin audits passed. This run did not write the main libraries or PCB.

The output set covers power/chopper component records, power placement, both calculation records, busbar interface/calculations/SVG/PNG, and the five PCB/external BOM files. JSON comparison also found zero semantic differences. The original files were checked again against their saved hashes after execution.

Each process ran under the bundled portable KiCad Python on Windows. Before each process, the isolated copy was restored to the same authoritative snapshot. The mechanical builder consumed the copied native pad-geometry report; the BOM builder consumed copied source manifests and manufacturer documents. This keeps each result independent of another generator's output.

[Machine-readable results](generator-reproducibility-review.json) record commands, generator/input/output SHA-256 hashes, and result flags. Temporary execution directory: `C:/Users/chrba/AppData/Local/Temp/pmu-generator-audit-fp8e4g0v`.

This review supports the claim that these design/calculation/manufacturing artifacts are reproducible from the recorded inputs. It does **not** establish end-to-end reproduction of the final routed native CAD. Integration, schematic/PCB construction, routing, and repair scripts were outside this bounded run. The final analog placement/Kelvin corrections remain a separate deterministic overlay; the original power placement JSON is not a round-trip export of those final coordinates.

Wake component/placement records include manually authored authoritative inputs. Other evidence utilities are not covered by this generator audit. Identical calculations do not constitute bench measurements, ERC/DRC approval, manufacturing release, or Rev B validation. When the source pad-geometry report changes, regenerate its dependent mechanical/BOM records deliberately rather than expecting the old provenance hash.
