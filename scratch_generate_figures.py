import os
import json
from experiments import (run_sensitivity_analysis, run_learning_curve_experiment, 
                         run_loop_detection_test, run_episodic_test, 
                         run_communication_experiment, run_scalability_test)
import visualizer

out_dir = "informe"

print("========================================")
print("9.1 Experimento 1 — Análisis de Sensibilidad")
print("========================================")
res_sens = run_sensitivity_analysis()
visualizer.plot_sensitivity(res_sens, out_dir=out_dir)
print(f"{'Parámetro':<15} {'Valor':<8} {'R_global':<12} {'TS':<8} {'ER':<8}")
print("-" * 55)
for k, v in res_sens["variation_N"].items():
    print(f"N={k:<13} {v:<8.2f}")

print("\n========================================")
print("9.2 Experimento 2 — Curva de Aprendizaje")
print("========================================")
res_learn = run_learning_curve_experiment()
# Generar grafico de learning curve manualmente a partir del history
import matplotlib.pyplot as plt
from simulator import Simulator
import config
import contextlib

original = {k: getattr(config, k) for k in ["N", "T_FIN", "N_ROBOT", "N_MONSTRUOS", "N_IRIDIO", "SEED"]}
config.T_FIN = 200
config.N_MONSTRUOS = 0
config.N_IRIDIO = 40
config.N_ROBOT = 4
config.N = 5
with open(os.devnull, 'w') as f, contextlib.redirect_stdout(f):
    sim = Simulator()
    sim.initialize()
    sim.run(verbose=False)
    history = sim.metrics.history
visualizer.plot_metrics_timeline(history, out_dir=out_dir)
for k, v in original.items(): setattr(config, k, v)

print(f"Iridio en primera mitad (T=0..100):  {res_learn['primera_mitad_0_100']}")
print(f"Iridio en segunda mitad (T=101..200): {res_learn['segunda_mitad_101_200']}")

print("\n========================================")
print("9.3 Experimento 3 — Detección de Bucles")
print("========================================")
res_loop = run_loop_detection_test()
print(f"Bucle detectado: {res_loop['bucle_detectado']}")
print(f"Iteraciones sobrevividas: {res_loop['iteraciones_sobrevividas']}")
print(f"Razón de término: {res_loop['razon_termino']}")

print("\n========================================")
print("9.4 Experimento 4 — No-Episodicidad")
print("========================================")
res_ep = run_episodic_test()
print("Robot CON memoria:")
print(f"  Iridio:  {res_ep['robot_con_memoria']['iridio']}")
print(f"  Score:   {res_ep['robot_con_memoria']['score']:.2f}")
print("Robot SIN memoria:")
print(f"  Iridio:  {res_ep['robot_sin_memoria']['iridio']}")
print(f"  Score:   {res_ep['robot_sin_memoria']['score']:.2f}")

print("\n========================================")
print("9.5 Experimento 5 — Impacto de Comunicación")
print("========================================")
res_comm = run_communication_experiment()
visualizer.plot_communication_impact(res_comm, out_dir=out_dir)
for r, scores in res_comm.items():
    print(f"R={r:2} -> CON: {scores['score_con']:7.2f} | SIN: {scores['score_sin']:7.2f}")

print("\n========================================")
print("9.6 Experimento 6 — Escalabilidad")
print("========================================")
res_scale = run_scalability_test()
visualizer.plot_scalability(res_scale, out_dir=out_dir)
for n, t in res_scale.items():
    print(f"N={n} -> {t:.4f} segundos")
