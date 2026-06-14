import os
import contextlib
import config
from simulator import Simulator

# Configuración base estricta
BASELINE = {
    "N":           6,
    "T_FIN":       100,
    "N_ROBOT":     3,
    "N_MONSTRUOS": 2,
    "N_IRIDIO":    10,
    "SEED":        42,
    "ENABLE_MEMORY_BROADCAST": False,
    "ENABLE_SECTORS":          False,
    "ENABLE_ADAPTIVE_LOOP":    False
}

def _restore_config():
    for k, v in BASELINE.items():
        setattr(config, k, v)

def run_scenario(name: str):
    with open(os.devnull, 'w') as f, contextlib.redirect_stdout(f):
        sim = Simulator()
        sim.initialize()
        sim.run(verbose=False)
        summary = sim.metrics.generate_summary(world=sim.world, monsters=sim.monsters)
    print(f"[{name}]")
    print(f"  R_global: {summary['global_score']:.2f}")
    print(f"  TS:       {summary['survival_rate']:.2f}")
    iridio_total = sum(summary['iridio_por_robot'].values())
    print(f"  Iridio:   {iridio_total}")
    print("-" * 30)

if __name__ == "__main__":
    print("========================================")
    print("Evaluación de Recomendaciones (Baseline)")
    print("========================================")
    
    _restore_config()
    run_scenario("Baseline (Sin Recomendaciones)")
    
    _restore_config()
    config.ENABLE_MEMORY_BROADCAST = True
    run_scenario("Rec 1: Memoria Compartida")
    
    _restore_config()
    config.ENABLE_SECTORS = True
    run_scenario("Rec 2: Sectores de Exploración")
    
    _restore_config()
    config.ENABLE_ADAPTIVE_LOOP = True
    run_scenario("Rec 3: Infinitómetro Adaptativo")
    
    _restore_config()
    config.ENABLE_MEMORY_BROADCAST = True
    config.ENABLE_SECTORS = True
    config.ENABLE_ADAPTIVE_LOOP = True
    run_scenario("Todas las Recomendaciones")
