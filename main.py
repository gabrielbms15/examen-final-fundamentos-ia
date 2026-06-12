import argparse
import os

import config
from simulator import Simulator
import experiments
import visualizer

def parse_args():
    parser = argparse.ArgumentParser(description="Simulador Multiagente - Examen Final MIA-103")
    parser.add_argument("--mode", choices=["fast", "visual", "batch"], default="fast", 
                        help="Modo de ejecución: fast (silencioso), visual (prints + slices gráficos), batch (correr suite de experimentos)")
    parser.add_argument("--N", type=int, default=config.N, help="Tamaño del cubo (NxNxN)")
    parser.add_argument("--seed", type=int, default=config.SEED, help="Semilla aleatoria")
    parser.add_argument("--n_robot", type=int, default=config.N_ROBOT, help="Número de robots inicial")
    parser.add_argument("--n_monstruos", type=int, default=config.N_MONSTRUOS, help="Número de monstruos inicial")
    parser.add_argument("--n_iridio", type=int, default=config.N_IRIDIO, help="Bloques de iridio")
    parser.add_argument("--t_fin", type=int, default=config.T_FIN, help="Límite de ticks de reloj")
    return parser.parse_args()

def main():
    args = parse_args()
    
    # Aplicamos parámetros al config global (para fast/visual; el batch los sobreescribirá internamente)
    config.N = args.N
    config.SEED = args.seed
    config.N_ROBOT = args.n_robot
    config.N_MONSTRUOS = args.n_monstruos
    config.N_IRIDIO = args.n_iridio
    config.T_FIN = args.t_fin
    
    os.makedirs("results", exist_ok=True)
    
    if args.mode == "batch":
        print("Iniciando orquestación de experimentos BATCH. Esto tomará varios segundos...")
        results = experiments.run_all_experiments()
        
        print("Experimentos finalizados. Generando gráficas comparativas en la carpeta 'results/'.")
        visualizer.plot_sensitivity(results["sensitivity"])
        visualizer.plot_scalability(results["scalability"])
        
        print("\n--- RESUMEN DE EXPERIMENTOS NO GRÁFICOS ---")
        print("Aprendizaje (Iridio recogido 0-50 vs 50-100):", results["learning_curve"])
        print("Bucle Detectado:", results["loop_detection"]["bucle_detectado"], 
              f"(Razon de término: {results['loop_detection']['razon_termino']})")
        print("Comunicación:", results["communication"])
        print("Episódico:", results["episodic"]["conclusion"])
        print("-------------------------------------------\n")
        
    elif args.mode in ["fast", "visual"]:
        verbose = (args.mode == "visual")
        print(f"Inicializando simulador en modo {args.mode.upper()}...")
        
        sim = Simulator()
        sim.initialize()
        
        # En modo visual, graficamos el slice 2D del mundo (en Z=0 por defecto) al iniciar
        if args.mode == "visual":
            visualizer.plot_world_slice(sim.world, sim, z_layer=0, t=0)
            
        print("Ejecutando simulación...")
        sim.run(verbose=verbose)
        
        # Asegurar exportación de memorias de sobrevivientes
        sim.logger.capture_surviving_memories(sim.robots)
        
        print("Simulación terminada. Exportando logs y JSON de eventos...")
        sim.logger.export_to_csv("results/simulation_events.csv")
        sim.logger.export_robot_memories("results/robot_memories")
        sim.metrics.export_to_json("results/metrics_history.json")
        
        print("Renderizando gráficas (Timeline, Heatmap, Histograma)...")
        summary = sim.metrics.generate_summary(world=sim.world, monsters=sim.monsters)
        visualizer.plot_metrics_timeline(sim.metrics.history)
        
        heatmap_data = sim.metrics.get_visit_heatmap(config.N)
        visualizer.plot_heatmap(heatmap_data, config.N)
        
        visualizer.plot_score_distribution(summary["robots_scores"])
        
        if args.mode == "visual":
            # Extra slice gráfico al final
            visualizer.plot_world_slice(sim.world, sim, z_layer=0, t=config.T_FIN)
            
        print("¡Todos los artefactos generados en la carpeta 'results/'!")

if __name__ == "__main__":
    main()
