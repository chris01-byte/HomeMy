import sys, re
import pdfplumber
pdf=pdfplumber.open(sys.argv[1])
pat=re.compile(sys.argv[2], re.I)
n=int(sys.argv[3]) if len(sys.argv)>3 else 1
found=0
for i,pg in enumerate(pdf.pages[:12]):
    t=pg.extract_text() or ''
    if pat.search(t) and 'Table of Contents' not in t[:200]:
        print(f'--- page {i+1}')
        print(t[:int(sys.argv[4]) if len(sys.argv)>4 else 2200])
        found+=1
        if found>=n: break
