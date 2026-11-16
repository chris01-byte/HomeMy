import sys, pypdfium2 as pdfium
# usage: crop.py pdf page scale x0 y0 x1 y1 out   (fractions of page 0..1)
pdf=pdfium.PdfDocument(sys.argv[1]); i=int(sys.argv[2])-1; scale=float(sys.argv[3])
img=pdf[i].render(scale=scale).to_pil()
W,H=img.size
x0,y0,x1,y1=[float(v) for v in sys.argv[4:8]]
c=img.crop((int(x0*W),int(y0*H),int(x1*W),int(y1*H)))
c.save(sys.argv[8]); print(sys.argv[8],c.size)
