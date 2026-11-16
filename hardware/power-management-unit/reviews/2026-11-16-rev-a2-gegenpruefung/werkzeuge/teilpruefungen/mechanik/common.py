import numpy as np, json
OUT='<SITZUNG>/agents/mech/'
RES=20
_r=None
def R():
    global _r
    if _r is None:
        _r=dict(np.load(OUT+'raster.npz'))
    return _r
nets={int(k):v for k,v in json.load(open(OUT+'nets.json')).items()}
nets[60000]='<NETTIE_FCU_GRAPHIC>'; nets[59999]='<NC_PAD>'
code={v:k for k,v in nets.items()}
board=json.load(open(OUT+'board.json'))
fps={f['ref']:f for f in board['footprints']}
A2J=json.load(open('<SITZUNG>/pmu/hardware/power-management-unit/rev-a2-layout-280x260/manufacturing/busbar-pcb-interface.json'))
def poly_mask(pts,cut=[]):
    from PIL import Image, ImageDraw
    W,H=280*RES,260*RES
    img=Image.new('1',(W,H),0); d=ImageDraw.Draw(img)
    d.polygon([(x*RES,y*RES) for x,y in pts],fill=1)
    for c in cut:
        d.polygon([(x*RES,y*RES) for x,y in c],fill=0)
    return np.array(img,dtype=bool)
PAL={'BATT_FUSED_P':(255,0,0),'BATT_SENSED_P':(255,120,0),'MAIN_COMMON':(255,200,0),'SYS_BUS_P':(200,255,0),'MOTION_SENSED_P':(0,220,0),'MOTION_COMMON':(0,220,180),'MOTION_BUS_P':(0,160,255),
     'BATT_N':(90,90,90),'ARM_L_N':(170,0,255),'ARM_R_N':(255,0,220),'DRIVE_N':(120,60,0),'LIFT_N':(0,90,120),'PC_N':(120,120,0),'LOGIC_BUCK_N':(60,120,60),'CHOPPER_N':(150,80,80),'LOGIC_5V_N':(80,80,160),'LOGIC_GND':(0,0,160),'CHOP_GND':(160,120,200)}
def colorize(arr,default=(200,170,150)):
    h,w=arr.shape
    img=np.full((h,w,3),255,dtype=np.uint8)
    img[arr>0]=default
    for n,c in PAL.items():
        if n in code:
            img[arr==code[n]]=c
    return img
