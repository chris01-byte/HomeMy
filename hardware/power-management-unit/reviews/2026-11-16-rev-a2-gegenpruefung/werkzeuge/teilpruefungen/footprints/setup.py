import sys
sys.path.insert(0,'<SITZUNG>/agents/footprints')
import sx, dump
root,fps=dump.board()
def pr(n,ind=0,maxd=6):
    if isinstance(n,list):
        if all(not isinstance(c,list) for c in n):
            print(' '*ind+'('+' '.join(sx.S(c) for c in n)+')')
        else:
            print(' '*ind+'('+str(sx.S(n[0])))
            for c in n[1:]:
                if isinstance(c,list): pr(c,ind+2)
                else: print(' '*(ind+2)+str(sx.S(c)))
            print(' '*ind+')')
print([sx.S(c) for c in sx.find1(root,'general') if not isinstance(c,list)])
pr(sx.find1(root,'general'))
st=sx.find1(root,'setup')
for name in ('stackup','pad_to_mask_clearance','solder_mask_min_width','pad_to_paste_clearance','pad_to_paste_clearance_ratio'):
    n=sx.find1(st,name)
    if n: pr(n)
