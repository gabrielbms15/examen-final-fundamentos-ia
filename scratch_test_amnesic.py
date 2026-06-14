import os
import contextlib
import config
from simulator import Simulator

def test_amnesic():
    config.W5_IDLE = 1.0 # default
    
    # Run with memory
    with open(os.devnull, 'w') as f, contextlib.redirect_stdout(f):
        sim = Simulator()
        sim.initialize()
        sim.run(verbose=False)
        res_memoria = sim.metrics.generate_summary(world=sim.world, monsters=sim.monsters)
        memoria_score = sum(res_memoria["robots_scores"].values())
        
    # Run without memory (properly amnesic)
    with open(os.devnull, 'w') as f, contextlib.redirect_stdout(f):
        sim_limpio = Simulator()
        sim_limpio.initialize()
        for r in sim_limpio.robots:
            r._sense_infinitometro = lambda *args, **kwargs: False
            r.generate_new_rules = lambda *args, **kwargs: None
        sim_limpio.run(verbose=False)
        res_limpio = sim_limpio.metrics.generate_summary(world=sim_limpio.world, monsters=sim_limpio.monsters)
        limpio_score = sum(res_limpio["robots_scores"].values())
        
    print(f"W5_IDLE=1.0 -> Con mem: {memoria_score:.2f}, Sin mem (fixed): {limpio_score:.2f}")

if __name__ == '__main__':
    test_amnesic()
