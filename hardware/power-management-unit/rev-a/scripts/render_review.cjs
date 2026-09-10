/* Render native CAD SVGs for visual review; no CAD geometry is modified.
 * node scripts/render_review.cjs /path/to/node_modules/sharp
 */
'use strict';
const fs = require('node:fs/promises');
const path = require('node:path');
const crypto = require('node:crypto');
const sharp = require(process.argv[2] || 'sharp');
const root = path.resolve(__dirname, '..');
const sha = bytes => crypto.createHash('sha256').update(bytes).digest('hex');
const packageDir = 'manufacturing/HomeMy_PMU_RevA-P1_2026-09-10';
const inputs = [
  ['assembly/schematic/HomeMy_PMU_RevA-02_main_switch_lm74930.svg', 'assembly/main-schematic-review.png'],
  ...['top', 'inner1', 'inner2', 'bottom'].map(name => [
    `reports/HomeMy_PMU_RevA-${name}-copper.svg`, `reports/${name}-copper-review.png`]),
  ...['front', 'back'].map(name => [
    `${packageDir}/assembly/HomeMy_PMU_RevA-assembly-${name}.svg`,
    `reports/assembly-${name}-review.png`]),
  ...['PTH', 'NPTH'].map(name => [
    `${packageDir}/drill/HomeMy_PMU_RevA-${name}-drl_map.svg`,
    `reports/drill-${name}-review.png`]),
  ['manufacturing/BUSBAR_TOP_VIEW_1to1.svg', 'reports/busbar-mechanical-review.png'],
  ['manufacturing/ASSEMBLY_ORIENTATION.svg', 'reports/assembly-orientation-review.png'],
  [`${packageDir}/assembly/POLARITY.svg`, 'reports/polarity-review.png'],
  [`${packageDir}/mechanical/BB7_1to1.svg`, 'reports/bb7-release-review.png'],
];
async function main() {
  const outputs = await Promise.all(inputs.map(async ([source, target]) => {
    const bytes = await fs.readFile(path.join(root, source));
    const png = await sharp(bytes, {density: 150, limitInputPixels: 100000000})
      .resize({width: 2200}).flatten({background: '#ffffff'}).png().toBuffer();
    await fs.writeFile(path.join(root, target), png);
    return {source, source_sha256: sha(bytes), target, target_sha256: sha(png)};
  }));
  const result = {
    rev_a_engineering_prototype: true, rev_b_production: false,
    state: 'rendered_for_visual_review_not_automatic_geometry_acceptance',
    renderer: {path: 'scripts/render_review.cjs', sha256: sha(await fs.readFile(__filename)),
      sharp: sharp.versions.sharp, vips: sharp.versions.vips},
    board_sha256: sha(await fs.readFile(path.join(root, 'kicad/HomeMy_PMU_RevA.kicad_pcb'))),
    outputs,
  };
  await fs.writeFile(path.join(root, 'reports/rendered-review-manifest.json'), JSON.stringify(result, null, 2) + '\n');
  console.log(`Rendered ${outputs.length} native CAD/mechanical views; CAD files unchanged.`);
}
main().catch(error => {console.error(error); process.exitCode = 1;});
