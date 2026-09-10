"""Retrieve public manufacturer evidence and preserve a hash manifest."""
from pathlib import Path
import argparse, concurrent.futures, hashlib, json, urllib.request

ROOT = Path(__file__).parent
PROTOTYPE = {'rev_a_engineering_prototype': True, 'rev_b_production': False}
SOURCES = {
    'kyc.pdf': 'https://www.chemi-con.co.jp/products/relatedfiles/capacitor/catalog/KYCLL-e.PDF',
    'tnpw_e3.pdf': 'https://www.vishay.com/docs/28758/tnpw_e3.pdf',
    'tlv1704.pdf': 'https://www.ti.com/lit/ds/symlink/tlv1704.pdf',
    'ref50.pdf': 'https://www.ti.com/lit/ds/symlink/ref50.pdf',
    'tps7a4001.pdf': 'https://www.ti.com/lit/ds/symlink/tps7a4001.pdf',
    'lm339b.pdf': 'https://www.ti.com/lit/ds/symlink/lm339b.pdf',
    'tps3808.pdf': 'https://www.ti.com/lit/ds/symlink/tps3808.pdf',
    'ucc27511.pdf': 'https://www.ti.com/lit/ds/symlink/ucc27511.pdf',
    'ipt015n10n5.pdf': 'https://www.infineon.com/assets/row/public/documents/24/49/infineon-ipt015n10n5-datasheet-en.pdf',
    'rhnh.pdf': 'https://www.vishay.com/docs/30201/rhnh.pdf',
    'ntcle100.pdf': 'https://www.vishay.com/docs/29049/ntcle100.pdf',
    '7461103.pdf': 'https://www.we-online.com/components/products/datasheet/7461103.pdf',
    'mbr10100.pdf': 'https://www.vishay.com/docs/89193/mbr10100.pdf',
    'vos618a.pdf': 'https://www.vishay.com/docs/83465/vos618a.pdf',
    '2n7002.pdf': 'https://assets.nexperia.com/documents/data-sheet/2N7002.pdf',
    'smcj.pdf': 'https://www.littelfuse.com/~/media/electronics/datasheets/tvs_diodes/littelfuse_tvs_diode_smcj_datasheet.pdf.pdf',
}

def fetch(item):
    name, url = item
    try:
        body = urllib.request.urlopen(url, timeout=45).read()
        if not body.startswith(b'%PDF'):
            raise ValueError('Not a PDF response')
        (ROOT / name).write_bytes(body)
        return {**PROTOTYPE, 'file': name, 'url': url, 'sha256': hashlib.sha256(body).hexdigest(), 'status': 'retrieved', 'retrieved': '2026-09-10'}
    except Exception as exc:
        return {**PROTOTYPE, 'file': name, 'url': url, 'status': 'failed', 'error': str(exc)}

if __name__ == '__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--manifest-only', action='store_true', help='Normalize authored metadata without network retrieval.')
    args=parser.parse_args()
    manifest=ROOT/'source_manifest.json'
    previous=json.loads(manifest.read_text(encoding='utf-8')) if manifest.exists() else []
    if args.manifest_only:
        results=previous
    else:
        with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
            results = list(pool.map(fetch, SOURCES.items()))
        # Preserve independently captured primary-source records that are not
        # PDF downloads in this script's source table.
        results.extend(row for row in previous if row.get('file') not in SOURCES)
    for row in results:
        row.update(PROTOTYPE)
        if row.get('status')=='retrieved_primary_text_capture' and (ROOT/row['file']).exists():
            row['sha256']=hashlib.sha256((ROOT/row['file']).read_bytes()).hexdigest()
    (ROOT / 'source_manifest.json').write_text(json.dumps(results, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(results, indent=2))
