"""One explicit restoration of the nine missing Kelvin/main-gate paths."""
from finish_280_routes import *
from bounded_geometry import critical

def main():
    guard(read());before=sha(BOARD);board=pcb.LoadBoard(str(BOARD));c=Controlled(board)
    K,H,D='MAIN_KELVIN_P','MAIN_HGATE','MAIN_DGATE'
    assert not any(t.GetNetname() in [K,H,D] for t in board.GetTracks()), 'This fixed recipe is only for the source missing nets'
    recipes=[
      (K,pcb.F_Cu,[(25.975,41.75),(25.4,40)]),
      (K,pcb.In2_Cu,[(25.4,40),(30.5,40),(30.5,84.5),(34.8,88.8),(34.8,89.6)]),
      (K,pcb.F_Cu,[(35.7,89.5875),(34.8,89.6)]),
      (K,pcb.In1_Cu,[(34.8,89.6),(44.5,89.6),(45.9,91),(45.9,94.1)]),
      (K,pcb.F_Cu,[(45,94.0875),(45.9,94.1)]),
      (K,pcb.In2_Cu,[(25.4,40),(29.3,36.1)]),
      (K,pcb.In1_Cu,[(29.3,36.1),(29.3,17.3),(33.5,17.3),(34.5,18.3)]),
      (K,pcb.F_Cu,[(33,18.5875),(34.5,18.3)]),
      (K,pcb.B_Cu,[(30.5,78.5),(36,78.5)]),
      (K,pcb.F_Cu,[(36,77),(36,78.5)]),
      (H,pcb.F_Cu,[(39.9,96.75),(41.6,96.75),(42.1,97.25)]),
      (H,pcb.In1_Cu,[(42.1,97.25),(43,98.15),(59,98.15),(63,94.15),(63,34.4125)]),
      (D,pcb.F_Cu,[(36.1,94.75),(35.6,94.75),(35.6,94.15)]),
      (D,pcb.B_Cu,[(35.6,94.15),(36.6,95.15),(36.6,100.5),(37.6,101.5),(73,101.5),(78.8,95.7),(78.8,17.4125)])]
    for y in [34.4125,59.4125,84.4125]:recipes.append((H,pcb.F_Cu,[(61.65,y),(63,y)]))
    for y in [17.4125,42.4125,67.4125]:
        recipes.append((D,pcb.F_Cu,[(78.35,y),(79.55,y)]));recipes.append((D,pcb.B_Cu,[(78.8,y),(79.55,y)]))
    vias={K:[(25.4,40),(34.8,89.6),(45.9,94.1),(29.3,36.1),(34.5,18.3),(30.5,78.5),(36,78.5)],
          H:[(42.1,97.25),(63,34.4125),(63,59.4125),(63,84.4125)],
          D:[(35.6,94.15),(79.55,17.4125),(79.55,42.4125),(79.55,67.4125)]}
    for net in [K,H,D]:
        attempt(net,'source has no conductors')
        assert c.route('Restore '+net,net,[(pts,.2,l) for n,l,pts in recipes if n==net],[(p,.6,.3) for p in vias[net]])
    review=critical(board);assert review['passed']==46
    pcb.SaveBoard(str(BOARD),board)
    action('cycle-02-critical',{'input_sha256':before,'output_sha256':sha(BOARD),'recipes':c.records,'explicit_paths':review,
                               'refill_and_native_pending':True,'existing_copper_removed':0})
    write(OUT/'cycle-02-critical-recipes.json',{'input_sha256':before,'output_sha256':sha(BOARD),'recipes':c.records})
    print('Explicit critical graph',review['passed'],'of',review['total'],flush=True)
    return board,c

if __name__=='__main__':owners=main()
