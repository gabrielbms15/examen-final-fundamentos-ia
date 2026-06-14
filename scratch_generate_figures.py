import os
import json
from experiments import (run_sensitivity_analysis, run_learning_curve_experiment, 
                         run_loop_detection_test, run_episodic_test, 
                         run_communication_experiment, run_scalability_test,
                         run_p_negro_experiment, run_n_robot_experiment,
                         run_n_monstruos_experiment)
import visualizer

out_dir = "informe"

print("========================================")
print("9.1 Experimento 1 — Análisis de Sensibilidad (Baseline para heatmap y F3)")
print("========================================")
res_sens = run_sensitivity_analysis()
visualizer.plot_sensitivity(res_sens, out_dir=out_dir)

# Sacamos de `res_sens` el baseline (N=5 asumiendo que está en summary interno o volvemos a correr uno directo)
# Para el Heatmap y F3 es más fácil hacer un _run_fast_simulator rápido:
from simulator import Simulator
import config
config.N = 5
config.N_ROBOT = 3
sim_baseline = Simulator()
sim_baseline.initialize()
sim_baseline.run(verbose=False)
summary_baseline = sim_baseline.metrics.generate_summary(sim_baseline.world)

# Heatmap (F2)
if "visit_heatmap" in summary_baseline:
    visualizer.plot_heatmap(summary_baseline["visit_heatmap"], config.N, out_dir=out_dir)

# Histogramas y Pie Chart (F3)
visualizer.plot_iridium_histogram(summary_baseline["iridio_por_robot"], out_dir=out_dir)
visualizer.plot_death_causes_piechart(summary_baseline["causas_muerte_robots"], out_dir=out_dir)

print(f"{'Parámetro':<15} {'Valor':<8} {'R_global':<12} {'TS':<8} {'ER':<8}")
print("-" * 55)
for k, v in res_sens["variation_N"].items():
    print(f"N={k:<13} {v:<8.2f}")

print("\n========================================")
print("9.1.2 Experimento 1b — Sensibilidad P_negro")
print("========================================")
res_p_negro = run_p_negro_experiment()
visualizer.plot_p_negro_sensitivity(res_p_negro, out_dir=out_dir)
print(f"{'P_negro':<10} {'R_global':<10} {'TS':<10} {'Iridio':<10}")
print("-" * 45)
for p, v in res_p_negro["variation_P_NEGRO"].items():
    print(f"{p:<10.2f} {v['R_global']:<10.2f} {v['TS']:<10.2f} {v['Iridio']:<10}")

print("\n========================================")
print("9.2 Experimento 2 — Curva de Aprendizaje")
print("========================================")
res_learn = run_learning_curve_experiment()
# Generar grafico de learning curve manualmente a partir del history
import matplotlib.pyplot as plt
from simulator import Simulator
import config
import contextlib

visualizer.plot_metrics_timeline(res_learn["history"], out_dir=out_dir)

print(f"Iridio en Gen 1 (T=0..100):   {res_learn['gen_1']}")
print(f"Iridio en Gen 2 (T=101..200): {res_learn['gen_2']}")
print(f"Iridio en Gen 3 (T=201..300): {res_learn['gen_3']}")

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
for r, scores in res_comm["communication_impact"].items():
    print(f"R={r:2} -> CON: {scores['CON']:7.2f} | SIN: {scores['SIN']:7.2f}")
    print(f"    Activaciones: {scores['stats_con']['activations']} (Ticks perdidos: {scores['stats_con']['ticks']})")
    print(f"    Resoluciones: {scores['stats_con']['both_rotated']} giran ambos, {scores['stats_con']['one_advanced']} avanza uno")
    print(f"    Fusiones Monstruos (CON): {scores['stats_con']['fusions']} | (SIN): {scores['fusions_sin']}")

print("\n========================================")
print("9.6 Experimento 6 — Escalabilidad")
print("========================================")
res_scale = run_scalability_test()
visualizer.plot_scalability(res_scale, out_dir=out_dir)
for n, val in res_scale.items():
    print(f"N={n} -> {val['avg_time']:.4f} segundos (±{val['std_dev']:.4f})")

print("\n========================================")
print("9.7 Experimento 7 — Sensibilidad N_robot (F5)")
print("========================================")
res_n_robot = run_n_robot_experiment()
visualizer.plot_n_robot_sensitivity(res_n_robot, out_dir=out_dir)
for r, v in res_n_robot["variation_N_ROBOT"].items():
    print(f"R={r:<10} R_global: {v['R_global']:<10.2f} TS: {v['TS']:<10.2f} ER: {v['ER']:<10.2f}")

print("\n========================================")
print("9.8 Experimento 8 — Sensibilidad N_monstruos (F5)")
print("========================================")
res_n_monstruos = run_n_monstruos_experiment()
visualizer.plot_n_monstruos_sensitivity(res_n_monstruos, out_dir=out_dir)
for m, v in res_n_monstruos["variation_N_MONSTRUOS"].items():
    print(f"M={m:<10} R_global: {v['R_global']:<10.2f} TS: {v['TS']:<10.2f} ER: {v['ER']:<10.2f}")
