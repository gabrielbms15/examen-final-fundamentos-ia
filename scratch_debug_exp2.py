import config
from simulator import Simulator

def debug_exp2():
    config.SEED = 42
    config.T_FIN = 200
    config.N_MONSTRUOS = 0
    config.N_IRIDIO = 40
    config.N_ROBOT = 4
    config.N = 5
    
    sim = Simulator()
    sim.initialize()
    for robot in sim.robots:
        robot._sense_infinitometro = lambda *args: False
    sim.run(verbose=True)

if __name__ == '__main__':
    debug_exp2()
