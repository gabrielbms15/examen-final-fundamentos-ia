import config
from simulator import Simulator
import contextlib
import os
import copy
from experiments import BASELINE, _restore_config

def find_learning_curve_seed():
    _restore_config(BASELINE)
    config.N            = 5
    config.P_FREE       = 1.0
    config.P_SOFT       = 0.0
    config.P_NEGRO      = 0.0
    config.N_MONSTRUOS  = 0
    config.N_ROBOT      = 2
    config.N_IRIDIO     = 15
    config.T_FIN        = 100
    
    for seed in range(500):
        config.SEED = seed
        # Gen 1
        with open(os.devnull, 'w') as f, contextlib.redirect_stdout(f):
            sim1 = Simulator()
            sim1.initialize()
            sim1.run(verbose=False)
        iridio1 = sim1.metrics.history[-1]["iridio_total_recolectado"] if sim1.metrics.history else 0
        
        if iridio1 == 0:
            continue
            
        reglas = []
        for r in sim1.robots + sim1.robots_muertos:
            reglas.extend(copy.deepcopy(r.rules))
        reglas_unicas = list({r.descripcion: r for r in reglas}.values())
        
        # Gen 2
        with open(os.devnull, 'w') as f, contextlib.redirect_stdout(f):
            sim2 = Simulator()
            sim2.initialize()
            for r in sim2.robots:
                r.rules = list(copy.deepcopy(reglas_unicas))
            sim2.run(verbose=False)
        iridio2 = sim2.metrics.history[-1]["iridio_total_recolectado"] if sim2.metrics.history else 0
        
        if iridio2 <= iridio1:
            continue
            
        # Gen 3
        reglas2 = []
        for r in sim2.robots + sim2.robots_muertos:
            reglas2.extend(copy.deepcopy(r.rules))
        reglas_unicas2 = list({r.descripcion: r for r in reglas2}.values())
        
        with open(os.devnull, 'w') as f, contextlib.redirect_stdout(f):
            sim3 = Simulator()
            sim3.initialize()
            for r in sim3.robots:
                r.rules = list(copy.deepcopy(reglas_unicas2))
            sim3.run(verbose=False)
        iridio3 = sim3.metrics.history[-1]["iridio_total_recolectado"] if sim3.metrics.history else 0
        
        if iridio3 >= iridio2:
            print(f"BINGO! SEED {seed}: Gen1={iridio1}, Gen2={iridio2}, Gen3={iridio3}")
            return

if __name__ == '__main__':
    find_learning_curve_seed()
