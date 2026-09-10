# Release metadata coverage

`rev_a_engineering_prototype: true`  
`rev_b_production: false`

The authoritative release scope is [release.json](../release.json). Every authored JSON metadata object now carries both flags. Authored reports may carry the same flags at their top level; the source-manifest array carries them on each authored entry.

Eleven additional calculation, geometry-review, source-index, and footprint-specification records received metadata-only additions. Their complete payloads excluding the two release flags compare identical before and after the edit, including all numerical values. Ten corresponding generators now preserve the flags. The chopper source-manifest work independently covers its source capture/index records and offline manifest generator.

The dependent BOM refresh changes only Q40's newly retrieved primary-source evidence record and source/output hashes in the BOM manifest. Part identities, quantities, numeric calculations, and BOM CSVs remain unchanged. The seven-generator temporary-copy audit was repeated after the final mechanical/BOM/release/export update: all 14 outputs are byte-identical to the current authoritative files. A supplemental footprint-generator run preserves all 48 library definitions semantically and passes 421 pin audits; four annotated custom files differ only in serialization formatting.

Native or consumer-constrained formats keep their original shape and **inherit these two release flags from release.json**:

- Native KiCad ERC/DRC reports, CAD/project files, Gerber/drill files, and autorouter statistics/configuration.
- Ref-keyed placement dictionaries for busbar, chopper, and wake parts; net-keyed connection diagnostics.
- Pad-geometry, filled-polygon, and report-snapshot arrays consumed by review/rendering tools.
- Manufacturer PDF/data and upstream tool provenance. These are evidence sources, not declarations that the project is production-ready.
- CSV, SVG/PNG, assembly drawings, and other non-JSON artifacts share the enclosing release status without altering their file format.

No PCB, library, raw native report, manufacturer PDF, or ref-keyed placement dictionary was edited by this metadata task. Native review generators were updated without rerunning geometry analyses merely to add flags. The metadata-only before/after payload proofs record that edit phase; subsequent authorized final routing/geometry reports are bound by their own current snapshots.

Run `python scripts/audit_release_metadata.py --output evidence/release-metadata-scope.json` from rev-a to check coverage again. It validates every authored metadata object and reports explicit flags, declared schema inheritance, and missing coverage separately. It is read-only except for its requested report. Newly added unknown unflagged JSON fails the audit instead of silently inheriting status.

Evidence: [payload-preservation and generator records](release-metadata-review.json), [file-by-file scope audit](release-metadata-scope.json), and [refreshed reproducibility proof](generator-reproducibility-review.json). These flags identify an engineering prototype; they do not assert completed routing, hardware measurements, or manufacturing approval.
