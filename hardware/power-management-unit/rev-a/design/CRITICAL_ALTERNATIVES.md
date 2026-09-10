# Critical-part procurement alternatives

Reviewed 2026-09-10. These are procurement and engineering classifications,
not an authorization to substitute a populated power component. Stock and
lead times must be checked again when ordering. No second manufacturer has
been qualified as an interchangeable source for these critical parts.

| Selected part | Exact alternative order code | Compatibility and disposition | Manufacturer evidence |
| --- | --- | --- | --- |
| LM74930QRGERQ1 | LM74930QRGERQ1.A | TI identifies this as an identical alias. Order the canonical LM74930QRGERQ1: the alias is not independently purchasable at TI. Same source and IC; no supply-chain diversification. Full/custom reels or distributor cut tape provide quantity options. | [TI exact part page](https://www.ti.com/product/LM74930-Q1/part-details/LM74930QRGERQ1) |
| TPS48110AQDGXRQ1 | TPS48110AQDGXRQ1.A | TI identifies this as an identical alias and directs ordering through the canonical code. Same source, same DGX19 IC. No independently qualified substitute controller. | [TI exact part page](https://www.ti.com/product/TPS4811-Q1/part-details/TPS48110AQDGXRQ1) |
| TPS26631RGER | TPS26631RGET | Verified same IC/package/electrical function, 250-piece small reel instead of 3000-piece large reel. Approved packaging alternative, same manufacturer. TPS26631RGET.A is its TI identical alias, not another independently purchasable source. | [TI packaging alternatives](https://www.ti.com/product/TPS2663/part-details/TPS26631RGET) |
| PSMN1R0-100ASFJ | PSMN1R0-100ASEJ | Verified same 100 V class and SOT8000A mechanical/pin map. Enhanced-SOA engineering candidate only: requires gate/inrush, SOA, resistance/thermal and startup review before substitution. Current BOM remains ASFJ. | [Nexperia ASE datasheet](https://assets.nexperia.com/documents/data-sheet/PSMN1R0-100ASE.pdf), [manufacturer product page](https://www.nexperia.com/product/PSMN1R0-100ASE) |
| CSS4J-4026R-L500F | CSS4J-4026R-L500FE | Verified same 0.5 mΩ, 1%, four-terminal 10 W part; suffix E changes the standard 13-inch reel to a mini 7-inch reel. Approved packaging alternative, same manufacturer. | [Bourns ordering key](https://www.bourns.com/docs/product-datasheets/css4j-4026.pdf), [manufacturer PCN listing both codes](https://bourns.com/docs/technical-documents/product-change-notifications/N1902_CSS_CSM_EBW_PCN.pdf) |

The LM and TPS48110 aliases provide identification compatibility, not a new
source or an extra stock pool. Do not report them as two independent
suppliers. The TI pages currently mark these controllers and the TPS26631
packaging alternatives active; their public inventory presentation did not
establish stock accessible to this user.

## MOSFET candidate review

PSMN1R0-100ASEJ is Nexperia sales item 934666620118. Nexperia's manufacturer
change notice names that order code and SOT8000A explicitly; the product page
marks the base device Production. The matching pin map is gate 1, sources
2–6, drains 7–12 and mounting base, with identical package outline. Its
maximum RDS(on) at 10 V is 1.04/1.7/2.4 mΩ at 25/100/175 °C. Maximum QG is
509 nC and QGD is 14.5/48.2/111 nC minimum/typical/maximum at the stated
50 V, 25 A, 25 °C test point. Its SOA graph includes a 125 °C mounting-base
curve. Reduced Miller charge can increase startup current even when SOA is
better; preserve neither the ASF slew estimate nor its loss calculation
without recomputing. [Manufacturer datasheet](https://assets.nexperia.com/documents/data-sheet/PSMN1R0-100ASE.pdf),
[Nexperia change notice CN-202508013I](https://mm.digikey.com/Volume0/opasdata/d220001/medias/docus/7517/CN-202508013I.pdf).

No mix of ASF and ASE devices within one parallel bank is approved. Package
names CCPAK1212i / SOT8005A are different from this board's SOT8000A and must
not be accepted because a distributor labels them parametrically similar.

## Supplier and lifecycle observations

| Part / family | Observation on review date | Procurement implication |
| --- | --- | --- |
| LM74930, TPS48110, TPS26631 | TI exact order pages and package addenda mark Active/Production. | Order only the documented package, suffix and carrier; obtain traceable moisture-sensitive packaging for U1/U2. No stock reservation was made. |
| PSMN1R0-100ASF / ASE | Both manufacturer product pages mark Production. [ASF source](https://www.nexperia.com/product/PSMN1R0-100ASF), [ASE source](https://www.nexperia.com/product/PSMN1R0-100ASE). | Current production status does not guarantee small quantities. |
| PSMN1R0-100ASEJ | [DigiKey exact listing](https://www.digikey.com/en/products/detail/nexperia-usa-inc/PSMN1R0-100ASEJ/25724049) offered backorder, with zero immediate stock in the retrieved result. | Engineering alternative is not established as an immediate procurement fallback. Confirm availability before investing in replacement qualification. |
| CSS4J-4026R-L500F / FE | Manufacturer ordering key and PCN support both codes; [DigiKey FE listing](https://www.digikey.com/en/products/detail/bourns-inc/CSS4J-4026R-L500FE/6229296) marks Active. | Manufacturer catalog evidence is present; no separate manufacturer lifecycle flag or reserved stock was established. |

The 5% CSS4J-4026R-L500J/JE options are not approved substitutes for the
specified 1% shunts. Their wider tolerance would alter both protection and
measurement bounds. Different resistance variants also change power ratings;
the series name alone does not establish equivalence.

## Support resistor procurement corrections

R62 uses standard 226 kΩ, not an unverified 224 kΩ order code. The 18.4 kΩ
main ILIM value is assembled from R22 18.2 kΩ plus R64 200 Ω. The seemingly
unusual 39.7 kΩ R31 is a real RT0805BRD0739K7L catalog item, also listed in
[TI's TIDA-00929 BOM](https://www.ti.com/jp/lit/pdf/tidrpf6).
These corrections preserve the current main setting and give U5 a nominal
29.311 V threshold; calculated.json contains its updated bounds.
