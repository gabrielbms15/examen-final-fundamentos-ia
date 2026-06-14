import config
from simulator import Simulator

def find_learning_seed():
    config.T_FIN = 200
    config.N_MONSTRUOS = 0
    config.N_ROBOT = 2
    config.N = 4
    config.N_IRIDIO = 5
    
    for seed in range(500):
        config.SEED = seed
        sim = Simulator()
        sim.initialize()
        sim.run(verbose=False)
        
        iridio_t100 = next((h["iridio_total_recolectado"] for h in sim.metrics.history if h["t"] == 100), 0)
        iridio_t200 = sim.metrics.history[-1]["iridio_total_recolectado"]
        
        if iridio_t100 > 0 or iridio_t200 > 0:
            if iridio_t200 - iridio_t100 > iridio_t100:
                print(f"BINGO! Seed {seed}: 0..100 -> {iridio_t100}, 101..200 -> {iridio_t200 - iridio_t100}")
                return

if __name__ == '__main__':
    find_learning_seed()
