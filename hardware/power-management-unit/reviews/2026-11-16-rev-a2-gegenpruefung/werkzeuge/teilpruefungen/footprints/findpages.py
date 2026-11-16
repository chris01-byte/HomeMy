import sys, re
from pypdf import PdfReader
r=PdfReader(sys.argv[1])
pats=[re.compile(p,re.I) for p in sys.argv[2:]]
print('pages',len(r.pages))
for i,pg in enumerate(r.pages):
    try: t=pg.extract_text() or ''
    except Exception as e: t=''
    hits=[p.pattern for p in pats if p.search(t)]
    if hits: print(i+1,hits, repr(t[:100]))
