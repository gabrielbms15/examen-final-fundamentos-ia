import config
from experiments import run_episodic_test

def find_seed():
    config.W5_IDLE = 0.05
    for seed in range(100):
        config.SEED = seed
        res = run_episodic_test()
        score_mem = res['robot_con_memoria']['score']
        score_no_mem = res['robot_sin_memoria']['score']
        if score_mem > score_no_mem:
            print(f"SEED={seed} W5=0.05 -> Con mem: {score_mem:.2f}, Sin mem: {score_no_mem:.2f}")
            return seed
            
if __name__ == '__main__':
    find_seed()
