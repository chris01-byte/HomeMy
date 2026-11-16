import sys
sys.path.insert(0,'<SITZUNG>/agents/footprints')
import near
# usage: nearbox.py name x0 y0 x1 y1
name=sys.argv[1]; box=tuple(float(v) for v in sys.argv[2:6])
near.report(name,box,0.0)
