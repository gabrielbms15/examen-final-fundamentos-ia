import config
from experiments import run_episodic_test

def check_w5_high():
    for w in [1.0, 2.0, 5.0, 10.0]:
        config.W5_IDLE = w
        res = run_episodic_test()
        score_mem = res['robot_con_memoria']['score']
        score_no_mem = res['robot_sin_memoria']['score']
        print(f"W5_IDLE={w} -> Con mem: {score_mem:.2f}, Sin mem: {score_no_mem:.2f}")

if __name__ == '__main__':
    check_w5_high()
