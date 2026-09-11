"""Additional sections tied to actual rebuild current-flow corridors."""
import math
import pcbnew as pcb
def definitions(board):
    F,B,I1,I2=pcb.F_Cu,pcb.B_Cu,pcb.In1_Cu,pcb.In2_Cu
    result=[]
    def add(label,net,a,b,layers=(F,B)):
        for layer in layers:result.append((label,net,layer,a,b))
    add('Input terminal to shunt','BATT_FUSED_P',[20,30],[20,60],(F,))
    add('Battery sensed field','BATT_SENSED_P',[30,35],[60,35])
    add('Main common field','MAIN_COMMON',[58,35],[83,35])
    add('System field','SYS_BUS_P',[80,35],[112,35])
    add('Motion sensed field','MOTION_SENSED_P',[112,37],[148,37])
    add('Motion common field','MOTION_COMMON',[144,37],[170,37])
    add('Motion output field','MOTION_BUS_P',[167,50],[219,50])
    add('Motion right spine','MOTION_BUS_P',[267,90],[280,90])
    add('Motion top bridge','MOTION_BUS_P',[235,5],[235,20])
    add('Battery return across board','BATT_N',[150,98],[150,139])
    add('Battery return right column','BATT_N',[217,160],[238,160])
    pads={f.GetReference()+'.'+p.GetNumber():p for f in board.GetFootprints() for p in f.Pads()}
    def normal(label,net,A,B,half,layers):
        a=pads[A].GetPosition();b=pads[B].GetPosition()
        x,y=pcb.ToMM(a.x+b.x)/2,pcb.ToMM(a.y+b.y)/2
        dx,dy=pcb.ToMM(b.x-a.x),pcb.ToMM(b.y-a.y);d=math.hypot(dx,dy)
        add(label,net,[x-dy*half/d,y+dx*half/d],[x+dy*half/d,y-dx*half/d],layers)
    normal('Left arm approach','ARM_L_N','NT1.1','J4.1',12,(F,B))
    normal('Right arm approach','ARM_R_N','NT2.1','J6.1',12,(F,B))
    add('Left arm pin bank','ARM_L_N',[268,135],[268,156])
    add('Right arm pin bank','ARM_R_N',[268,165],[268,186])
    normal('Drive return original front layer','DRIVE_N','NT3.1','J7.2',8,(F,))
    normal('Lift return original inner layers','LIFT_N','NT4.1','J8.2',8,(I1,I2))
    add('Chopper capacitor return','CHOPPER_N',[228,38],[242,38],(B,))
    add('Chopper return to star','CHOPPER_N',[248,80],[264,80],(B,))
    return result
