import sys, pypdfium2 as pdfium
# usage: render.py pdf outprefix scale page1 [page2...]  (pages 1-based)
pdf=pdfium.PdfDocument(sys.argv[1])
out=sys.argv[2]; scale=float(sys.argv[3])
print('pages',len(pdf))
for p in sys.argv[4:]:
    i=int(p)-1
    img=pdf[i].render(scale=scale).to_pil()
    fn=f"{out}-{p}.png"; img.save(fn); print(fn,img.size)
