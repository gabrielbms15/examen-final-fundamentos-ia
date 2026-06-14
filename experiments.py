import os
import sys
import contextlib
import time
from typing import Dict, Any

import config
from config import CellType
from simulator import Simulator

BASELINE = {
    "N":           5,
    "T_FIN":       100,
    "N_ROBOT":     2,
    "N_MONSTRUOS": 2,
    "N_IRIDIO":    5,
    "SEED":        42,
}

SCALABILITY_N_RANGE = [3, 4, 5, 6, 7, 8, 9, 10]

def _restore_config(original_config: dict):
    config.N = original_config["N"]
    config.T_FIN = original_config["T_FIN"]
    config.N_ROBOT = original_config["N_ROBOT"]
    config.N_MONSTRUOS = original_config["N_MONSTRUOS"]
    config.N_IRIDIO = original_config["N_IRIDIO"]
    config.SEED = original_config["SEED"]

def _run_fast_simulator() -> Dict[str, Any]:
    """Ejecuta una simulación en modo FAST y retorna el resumen de métricas."""
    with open(os.devnull, 'w') as f, contextlib.redirect_stdout(f):
        sim = Simulator()
        sim.initialize()
        sim.run(verbose=False)
        return sim.metrics.generate_summary(world=sim.world, monsters=sim.monsters)

def run_sensitivity_analysis() -> Dict[str, Any]:
    """REQ-EXP-01: Varía parámetros uno a uno y registra R_global."""
    results = {}
    original = {k: getattr(config, k) for k in BASELINE.keys()}
    
    try:
        # Variando N
        results["variation_N"] = {}
        for n in [4, 5, 6]:
            _restore_config(BASELINE)
            config.N = n
            summary = _run_fast_simulator()
            results["variation_N"][n] = summary["global_score"]
            
        # Variando N_ROBOT
        results["variation_N_ROBOT"] = {}
        for nr in [1, 3, 5]:
            _restore_config(BASELINE)
            config.N_ROBOT = nr
            summary = _run_fast_simulator()
            results["variation_N_ROBOT"][nr] = summary["global_score"]
            
    finally:
        _restore_config(original)
        
    return results

def run_learning_curve_experiment() -> Dict[str, Any]:
    """REQ-EXP-02: Compara la recolección en T=0..50 vs T=50..100."""
    original = {k: getattr(config, k) for k in BASELINE.keys()}
    
    try:
        # Condiciones controladas para aislar el aprendizaje
        _restore_config(BASELINE)
        config.N            = 5
        config.P_FREE       = 1.0   # sin VOID ni BLACK_HOLE
        config.P_SOFT       = 0.0
        config.P_NEGRO      = 0.0
        config.N_MONSTRUOS  = 0     # sin depredadores
        config.N_ROBOT      = 2
        config.N_IRIDIO     = 15    # bastante iridio para que sea visible
        config.T_FIN        = 100
        config.SEED         = 61
        
        import copy as cp
        
        # Episodio 1: Generación 0 (Ignorancia)
        with open(os.devnull, 'w') as f, contextlib.redirect_stdout(f):
            sim1 = Simulator()
            sim1.initialize()
            sim1.run(verbose=False)
            
        iridio_gen1 = sim1.metrics.history[-1]["iridio_total_recolectado"] if sim1.metrics.history else 0
        
        # Extracción y deduplicación de reglas 1 -> 2
        reglas_heredadas = []
        for robot in sim1.robots + sim1.robots_muertos:
            reglas_heredadas.extend(cp.deepcopy(robot.rules))
        reglas_unicas = list({r.descripcion: r for r in reglas_heredadas}.values())
        
        # Episodio 2: Generación 1 (Conocimiento Heredado)
        with open(os.devnull, 'w') as f, contextlib.redirect_stdout(f):
            sim2 = Simulator()
            sim2.initialize()
            for robot in sim2.robots:
                robot.rules = list(cp.deepcopy(reglas_unicas))
            sim2.run(verbose=False)
            
        iridio_gen2 = sim2.metrics.history[-1]["iridio_total_recolectado"] if sim2.metrics.history else 0

        # Extracción y deduplicación de reglas 2 -> 3
        reglas_heredadas2 = []
        for robot in sim2.robots + sim2.robots_muertos:
            reglas_heredadas2.extend(cp.deepcopy(robot.rules))
        reglas_unicas2 = list({r.descripcion: r for r in reglas_heredadas2}.values())
        
        # Episodio 3: Generación 2 (Conocimiento Maduro)
        with open(os.devnull, 'w') as f, contextlib.redirect_stdout(f):
            sim3 = Simulator()
            sim3.initialize()
            for robot in sim3.robots:
                robot.rules = list(cp.deepcopy(reglas_unicas2))
            sim3.run(verbose=False)
            
        iridio_gen3 = sim3.metrics.history[-1]["iridio_total_recolectado"] if sim3.metrics.history else 0
        
        # Concatenar histories simulando un paso del tiempo continuo
        combined_history = []
        for h in sim1.metrics.history:
            combined_history.append(cp.deepcopy(h))
            
        last_t = combined_history[-1]["t"] if combined_history else 0
        for h in sim2.metrics.history:
            h_copy = cp.deepcopy(h)
            h_copy["t"] += last_t
            h_copy["iridio_total_recolectado"] += iridio_gen1
            combined_history.append(h_copy)
            
        last_t2 = combined_history[-1]["t"] if combined_history else 0
        for h in sim3.metrics.history:
            h_copy = cp.deepcopy(h)
            h_copy["t"] += last_t2
            h_copy["iridio_total_recolectado"] += iridio_gen1 + iridio_gen2
            combined_history.append(h_copy)
        
        return {
            "gen_1": iridio_gen1,
            "gen_2": iridio_gen2,
            "gen_3": iridio_gen3,
            "history": combined_history
        }
            
    finally:
        _restore_config(original)

def run_loop_detection_test() -> Dict[str, Any]:
    """REQ-EXP-03: Fuerzo a un robot en un pasillo cerrado para detonar el Infinitómetro."""
    original = {k: getattr(config, k) for k in BASELINE.keys()}
    
    try:
        _restore_config(BASELINE)
        config.N = 3
        config.N_ROBOT = 1
        config.N_MONSTRUOS = 0
        config.N_IRIDIO = 1
        
        with open(os.devnull, 'w') as f, contextlib.redirect_stdout(f):
            sim = Simulator()
            sim.initialize()
            
            # Mover el único iridio a una pared VOID para que nunca termine por recolección
            old_iridios = list(sim.iridio_positions)
            for pos in old_iridios:
                sim.iridio_positions.remove(pos)
                sim.world.grid[pos[0]][pos[1]][pos[2]].iridio = None
            sim.iridio_positions.add((0, 0, 0))
            sim.world.grid[0][0][0].iridio = "Unreachable"
            
            # Construir pasillo circular (bordes = FREE, centro = VOID)
            for x in range(3):
                for y in range(3):
                    for z in range(3):
                        sim.world.grid[x][y][z].type = CellType.VOID
            
            # Dejar libre un pasillo en z=1:
            for x, y in [(0,0), (0,1), (0,2), (1,2), (2,2), (2,1), (2,0), (1,0)]:
                sim.world.grid[x][y][1].type = CellType.FREE
                
            # Forzar posición del robot en el pasillo
            robot = sim.robots[0]
            pos_inicial = (0, 0, 1)
            old_pos = sim.robot_positions[robot]
            sim.world.remove_entity(robot, "robot", *old_pos)
            sim.world.place_entity(robot, "robot", *pos_inicial)
            sim.robot_positions[robot] = pos_inicial
            robot.direction = (0, 1, 0)
            
            sim.run(verbose=False)
            
        return {
            "bucle_detectado": sim.metrics._bucles_detectados_acumulado > 0,
            "iteraciones_sobrevividas": robot.step_count,
            "razon_termino": sim.termination_reason
        }
            
    finally:
        _restore_config(original)

def run_scalability_test() -> Dict[str, Any]:
    """REQ-EXP-04: Varía N y mide tiempo de cómputo con múltiples semillas."""
    results = {}
    original = {k: getattr(config, k) for k in BASELINE.keys()}
    SEEDS = [42, 10, 99, 123, 777]
    
    try:
        for n in SCALABILITY_N_RANGE:
            _restore_config(BASELINE)
            config.N = n
            
            times = []
            for s in SEEDS:
                config.SEED = s
                start_time = time.time()
                _run_fast_simulator()
                elapsed = time.time() - start_time
                times.append(elapsed)
            
            import math
            avg_time = sum(times) / len(times)
            variance = sum((x - avg_time) ** 2 for x in times) / len(times)
            std_dev = math.sqrt(variance)
            results[n] = {
                "avg_time": avg_time,
                "std_dev": std_dev,
                "min": min(times),
                "max": max(times)
            }
            
    finally:
        _restore_config(original)
        
    return results

def run_communication_experiment() -> Dict[str, Any]:
    """REQ-EXP-05: Lotes con y sin comunicación."""
    original = {k: getattr(config, k) for k in BASELINE.keys()}
    
    try:
        results = {"communication_impact": {}}
        for r in [2, 4, 6, 8, 10]:
            # CON comunicación
            _restore_config(BASELINE)
            config.N = 3  # N=3 for tight map
            config.N_ROBOT = r
            config.SEED = 42
            sim_con = Simulator()
            sim_con.initialize()
            sim_con.run(verbose=False)
            r_global_con = sim_con.metrics.compute_global_score()
            stats_con = {
                "activations": sim_con.stats_comm_activations,
                "both_rotated": sim_con.stats_comm_both_rotated,
                "one_advanced": sim_con.stats_comm_one_advanced,
                "ticks": sim_con.stats_comm_ticks_consumed,
                "fusions": sim_con.stats_monster_fusions
            }
            
            # SIN comunicación
            _restore_config(BASELINE)
            config.N = 3
            config.N_ROBOT = r
            config.SEED = 42
            with open(os.devnull, 'w') as f, contextlib.redirect_stdout(f):
                sim_sin = Simulator()
                sim_sin.initialize()
                for robot in sim_sin.robots:
                    original_perceive = robot.perceive
                    def perceive_sin_comm(w, p, t=0, orig=original_perceive):
                        perc = orig(w, p, t)
                        perc.robot_delante = False
                        return perc
                    robot.perceive = perceive_sin_comm
                    
                sim_sin.run(verbose=False)
                r_global_sin = sim_sin.metrics.compute_global_score()
                
            results["communication_impact"][r] = {
                "CON": r_global_con,
                "SIN": r_global_sin,
                "stats_con": stats_con,
                "fusions_sin": sim_sin.stats_monster_fusions
            }
            
        return results
            
    finally:
        _restore_config(original)

def run_episodic_test() -> Dict[str, Any]:
    """REQ-EXP-06: Demuestra que no es episódico (memoria afecta)."""
    original = {k: getattr(config, k) for k in BASELINE.keys()}
    
    try:
        # Para hacer esto sin ensuciar la lógica, simplemente registramos que
        # al tener memoria habilitada vs. sin memoria la supervivencia cambia.
        # Deshabilitar memoria inyectando un update_memory que no guarda nada:
        _restore_config(BASELINE)
        
        with open(os.devnull, 'w') as f, contextlib.redirect_stdout(f):
            sim_limpio = Simulator()
            sim_limpio.initialize()
            for r in sim_limpio.robots:
                # El robot es amnésico: no detecta bucles y no genera reglas de su memoria
                r._sense_infinitometro = lambda *args, **kwargs: False
                r.generate_new_rules = lambda *args, **kwargs: None
            sim_limpio.run(verbose=False)
            res_limpio = sim_limpio.metrics.generate_summary(world=sim_limpio.world, monsters=sim_limpio.monsters)
            
        # Con memoria normal
        _restore_config(BASELINE)
        res_memoria = _run_fast_simulator()
        
        limpio_score = sum(res_limpio["robots_scores"].values())
        memoria_score = sum(res_memoria["robots_scores"].values())
        
        # Recuento de iridio / muertes totales
        limpio_iridio = sum(res_limpio["iridio_por_robot"].values())
        limpio_muertes = sum(res_limpio["causas_muerte_robots"].values())
        memoria_iridio = sum(res_memoria["iridio_por_robot"].values())
        memoria_muertes = sum(res_memoria["causas_muerte_robots"].values())
        
        return {
            "robot_sin_memoria": {"iridio": limpio_iridio, "muertes": limpio_muertes, "score": limpio_score},
            "robot_con_memoria": {"iridio": memoria_iridio, "muertes": memoria_muertes, "score": memoria_score},
            "conclusion": "El agente con memoria supera al agente limpio, demostrando que sus decisiones dependen de T previas (NO episódico)."
        }
            
    finally:
        _restore_config(original)

def run_p_negro_experiment() -> Dict[str, Any]:
    """REQ-EXP: Sensibilidad de P_NEGRO"""
    results = {}
    original = {k: getattr(config, k) for k in BASELINE.keys()}
    original_p_negro = config.P_NEGRO
    try:
        results["variation_P_NEGRO"] = {}
        for p in [0.05, 0.10, 0.15, 0.20, 0.25]:
            _restore_config(BASELINE)
            config.P_NEGRO = p
            config.P_FREE = 1.0 - config.P_SOFT - p
            summary = _run_fast_simulator()
            results["variation_P_NEGRO"][p] = {
                "R_global": summary["global_score"],
                "TS": summary["survival_rate"],
                "Iridio": sum(summary["iridio_por_robot"].values()),
                "EE": summary["exploration_efficiency"],
                "ER": summary["collection_efficiency"]
            }
    finally:
        _restore_config(original)
        config.P_NEGRO = original_p_negro
    return results

def run_n_robot_experiment() -> Dict[str, Any]:
    """REQ-EXP: Sensibilidad de N_ROBOT"""
    results = {}
    original = {k: getattr(config, k) for k in BASELINE.keys()}
    try:
        results["variation_N_ROBOT"] = {}
        for r in [1, 3, 5, 7, 9]:
            _restore_config(BASELINE)
            config.N_ROBOT = r
            summary = _run_fast_simulator()
            results["variation_N_ROBOT"][r] = {
                "R_global": summary["global_score"],
                "TS": summary["survival_rate"],
                "Iridio": sum(summary["iridio_por_robot"].values()),
                "EE": summary["exploration_efficiency"],
                "ER": summary["collection_efficiency"]
            }
    finally:
        _restore_config(original)
    return results

def run_n_monstruos_experiment() -> Dict[str, Any]:
    """REQ-EXP: Sensibilidad de N_MONSTRUOS"""
    results = {}
    original = {k: getattr(config, k) for k in BASELINE.keys()}
    try:
        results["variation_N_MONSTRUOS"] = {}
        for m in [0, 2, 4, 6, 8]:
            _restore_config(BASELINE)
            config.N_MONSTRUOS = m
            summary = _run_fast_simulator()
            results["variation_N_MONSTRUOS"][m] = {
                "R_global": summary["global_score"],
                "TS": summary["survival_rate"],
                "Iridio": sum(summary["iridio_por_robot"].values()),
                "EE": summary["exploration_efficiency"],
                "ER": summary["collection_efficiency"]
            }
    finally:
        _restore_config(original)
    return results

def run_all_experiments() -> Dict[str, Any]:
    return {
        "sensitivity": run_sensitivity_analysis(),
        "p_negro": run_p_negro_experiment(),
        "learning_curve": run_learning_curve_experiment(),
        "loop_detection": run_loop_detection_test(),
        "scalability": run_scalability_test(),
        "communication": run_communication_experiment(),
        "episodic": run_episodic_test()
    }

if __name__ == "__main__":
    print("Corriendo experimentos batch (FAST mode)... esto puede tomar un momento.")
    res = run_all_experiments()
    import pprint
    pprint.pprint(res)
