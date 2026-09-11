"""Regular short eFuse output fanouts and a separate inner-layer connector bridge."""
from rebuild import *
import sys
sys.path.insert(0,str(BASE.parent/'rev-a1/scripts'))
from finish_280_routes import Controlled
import pcbnew as pcb
def main():
    guard();b=pcb.LoadBoard(str(BOARD));c=Controlled(b);F,I2=pcb.F_Cu,pcb.In2_Cu
    c.route('PC eFuse output fanouts','PC_BUCK_IN_P',[
      (['U3.17',(36.4,122.75),(36.4,123.25),'U3.18'],.25,F),
      ([(36.4,123.25),(36.4,123.2),(33.6,123.2)],.25,F),
      (['C22.1',(33,124.6)],.5,F),(['R47.1',(29,124.7)],.5,F)])
    c.route('Logic eFuse output fanouts','LOGIC_BUCK_IN_P',[
      (['U4.17',(36.4,150.75),(36.4,151.25),'U4.18'],.25,F),
      (['C27.1',(33,152)],.5,F),(['R57.1',(31,154.0875),'C27.1'],.5,F),(['TP12.1',(26,151.8)],.5,F)])
    c.route('Logic connector bridge on separate inner layer','LOGIC_BUCK_IN_P',[
      (['J10.1',(18,151)],1,I2)], [((18,151),.8,.4)])
    b.BuildConnectivity();f=pcb.ZONE_FILLER(b);f.Fill(b.Zones());pcb.SaveBoard(str(BOARD),b);guard()
    write(OUT/'cycle-05-efuse-recipes.json',{'pcb_sha256':sha(BOARD),'recipes':c.records,'note':'The short J10 positive bridge uses In2; the front/back negative return is not cut by a front-layer signal.'})
    return b,c,f
if __name__=='__main__':owners=main()
