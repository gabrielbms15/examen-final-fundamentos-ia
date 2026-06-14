from simulator import Simulator
import config

config.N = 5
config.N_ROBOT = 2
config.N_MONSTRUOS = 2
config.N_IRIDIO = 5
config.T_FIN = 100
config.SEED = 42

sim = Simulator()
sim.initialize()
sim.run()

summary = sim.metrics.generate_summary(sim.world, sim.monsters)
print("=== RESUMEN DE SIMULACIÓN ===")
print(f"Tiempo total: {summary.get('t_final', 100)} ticks")
print(f"Iridio recolectado: {sum(summary.get('iridio_por_robot', {}).values())}/{config.N_IRIDIO}")
# Robots vivos calculation: sum(1 if r > -50 else 0 for r in summary.get('robots_scores', {}).values())
# Wait, I can just use survival_rate * config.N_ROBOT
vivos = int(summary.get('survival_rate', 0) * config.N_ROBOT)
print(f"Robots sobrevivientes: {vivos}/{config.N_ROBOT}")
print(f"R_global: {summary.get('global_score', 0):.2f}")
print(f"Tasa de supervivencia: {summary.get('survival_rate', 0):.2%}")
print(f"Eficiencia de recolección: {summary.get('collection_efficiency', 0):.2%}")
print(f"Eficiencia de exploración: {summary.get('exploration_efficiency', 0):.2%}")
