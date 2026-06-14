import os
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.colors import ListedColormap

def _ensure_dir(path: str):
    os.makedirs(path, exist_ok=True)

def plot_world_slice(world, sim, z_layer: int, t: int, out_dir: str = "results"):
    """
    Grilla 2D de una capa Z del cubo.
    Colores: FREE=blanco, VOID=gris, BLACK_HOLE=negro
    Íconos: robot=flecha (o 'R'), monstruo=círculo rojo ('M'), iridio=estrella amarilla ('*')
    Overlay: olor=rojo transparente, brillo=amarillo transparente
    """
    _ensure_dir(out_dir)
    N = world.N
    
    # 0 = FREE (Blanco), 1 = VOID (Gris), 2 = BLACK_HOLE (Negro)
    base_grid = np.zeros((N, N))
    
    for x in range(N):
        for y in range(N):
            cell = world.grid[x][y][z_layer]
            if cell.type.name == "VOID":
                base_grid[y, x] = 1
            elif cell.type.name == "BLACK_HOLE":
                base_grid[y, x] = 2
                
    cmap = ListedColormap(['white', 'gray', 'black'])
    
    fig, ax = plt.subplots(figsize=(8, 8))
    # Dibujar la matriz base
    ax.imshow(base_grid, cmap=cmap, vmin=0, vmax=2, origin='lower')
    
    # Dibujar overlays (olor y brillo)
    for x in range(N):
        for y in range(N):
            cell = world.grid[x][y][z_layer]
            if cell.olor:
                # Cuadrado rojo transparente
                rect = plt.Rectangle((x-0.5, y-0.5), 1, 1, color='red', alpha=0.3)
                ax.add_patch(rect)
            if cell.brillo:
                # Cuadrado amarillo transparente
                rect = plt.Rectangle((x-0.5, y-0.5), 1, 1, color='yellow', alpha=0.3)
                ax.add_patch(rect)

    # Dibujar Iridio
    for (ix, iy, iz) in sim.iridio_positions:
        if iz == z_layer:
            ax.plot(ix, iy, marker='*', color='gold', markersize=20, markeredgecolor='black')
            
    # Dibujar Monstruos
    for monster, (mx, my, mz) in sim.monster_positions.items():
        if mz == z_layer and monster.is_alive:
            ax.plot(mx, my, marker='o', color='red', markersize=15, markeredgecolor='darkred')
            ax.text(mx, my, 'M', color='white', ha='center', va='center', fontweight='bold')
            
    # Dibujar Robots
    for robot, (rx, ry, rz) in sim.robot_positions.items():
        if rz == z_layer and robot.is_alive:
            # Calcular rotación de flecha según direction
            dx, dy, dz = robot.direction
            # Solo dibujamos flecha en X, Y si el robot se mueve en el plano. Si se mueve en Z, un círculo
            if dz != 0:
                ax.plot(rx, ry, marker='o', color='blue', markersize=15)
                ax.text(rx, ry, 'R(Z)', color='white', ha='center', va='center', fontsize=8)
            else:
                # Flecha con quiver
                ax.quiver(rx, ry, dx, dy, color='blue', scale=10, width=0.015, pivot='middle', zorder=5)
                ax.text(rx, ry, 'R', color='white', ha='center', va='center', fontweight='bold', zorder=6)
                
    # Grid lines
    ax.set_xticks(np.arange(-.5, N, 1), minor=True)
    ax.set_yticks(np.arange(-.5, N, 1), minor=True)
    ax.grid(which='minor', color='black', linestyle='-', linewidth=2)
    ax.set_xticks([])
    ax.set_yticks([])
    
    plt.title(f"Simulación T={t} | Capa Z={z_layer}")
    filepath = os.path.join(out_dir, f"world_slice_t{t}_z{z_layer}.png")
    plt.savefig(filepath, bbox_inches='tight')
    plt.close()

def plot_metrics_timeline(metrics_history, out_dir: str = "results"):
    """Serie de tiempo: robots_vivos vs iridio_restante vs T"""
    if not metrics_history:
        return
        
    _ensure_dir(out_dir)
    t_vals = [m["t"] for m in metrics_history]
    robots_vivos = [m["robots_vivos"] for m in metrics_history]
    iridio_restante = [m["iridio_restante"] for m in metrics_history]
    
    plt.figure(figsize=(10, 6))
    plt.plot(t_vals, robots_vivos, label='Robots Vivos', color='blue', linewidth=2)
    plt.plot(t_vals, iridio_restante, label='Iridio Restante', color='gold', linewidth=2)
    
    plt.title("Evolución de la Simulación")
    plt.xlabel("Tick (T)")
    plt.ylabel("Cantidad")
    plt.legend()
    plt.grid(True, alpha=0.5)
    
    filepath = os.path.join(out_dir, "metrics_timeline.png")
    plt.savefig(filepath, bbox_inches='tight')
    plt.close()

def plot_p_negro_sensitivity(results_dict, out_dir: str = "results"):
    if "variation_P_NEGRO" not in results_dict:
        return
        
    _ensure_dir(out_dir)
    p_vals = sorted(list(results_dict["variation_P_NEGRO"].keys()))
    r_vals = [results_dict["variation_P_NEGRO"][p]["R_global"] for p in p_vals]
    ts_vals = [results_dict["variation_P_NEGRO"][p]["TS"] for p in p_vals]
    ee_vals = [results_dict["variation_P_NEGRO"][p]["EE"] for p in p_vals]
    er_vals = [results_dict["variation_P_NEGRO"][p]["ER"] for p in p_vals]
    
    fig, ax1 = plt.subplots(figsize=(10, 6))
    ax1.set_xlabel('P_negro')
    ax1.set_ylabel('R_global', color='tab:red')
    ax1.plot(p_vals, r_vals, color='tab:red', marker='o', linewidth=2, label='R_global')
    ax1.tick_params(axis='y', labelcolor='tab:red')
    ax1.grid(True, linestyle='--', alpha=0.7)
    
    ax2 = ax1.twinx()
    ax2.set_ylabel('Métricas de Eficiencia (TS, EE, ER)', color='tab:blue')
    ax2.plot(p_vals, ts_vals, color='tab:blue', marker='s', linewidth=2, linestyle='--', label='Tasa de Supervivencia (TS)')
    ax2.plot(p_vals, ee_vals, color='tab:green', marker='^', linewidth=2, linestyle='-.', label='Eficiencia Exploración (EE)')
    ax2.plot(p_vals, er_vals, color='tab:purple', marker='d', linewidth=2, linestyle=':', label='Eficiencia Recolección (ER)')
    ax2.tick_params(axis='y', labelcolor='tab:blue')
    ax2.set_ylim(-0.05, 1.05)
    
    # Legend for multiple axes
    lines_1, labels_1 = ax1.get_legend_handles_labels()
    lines_2, labels_2 = ax2.get_legend_handles_labels()
    ax2.legend(lines_1 + lines_2, labels_1 + labels_2, loc='upper center', bbox_to_anchor=(0.5, -0.15), ncol=2)
    
    plt.title('Sensibilidad frente a P_negro (Agujeros Negros)')
    fig.tight_layout()
    filepath = os.path.join(out_dir, "sensitivity_P_negro.png")
    plt.savefig(filepath, bbox_inches='tight')
    plt.close()

def plot_heatmap(visit_counts, N, out_dir: str = "results"):
    """Mapa de calor 2D (suma de visitas por celda, colapsando eje Z)"""
    _ensure_dir(out_dir)
    
    heatmap_array = np.array(visit_counts).T  # Transponer para que X e Y coincidan visualmente
    
    plt.figure(figsize=(8, 8))
    plt.imshow(heatmap_array, cmap='hot', origin='lower')
    plt.colorbar(label='Número de visitas (colapsando Z)')
    plt.title("Mapa de Calor de Exploración (Vista Superior)")
    plt.xlabel("Eje X")
    plt.ylabel("Eje Y")
    
    filepath = os.path.join(out_dir, "exploration_heatmap.png")
    plt.savefig(filepath, bbox_inches='tight')
    plt.close()

def plot_sensitivity(sensitivity_results, out_dir: str = "results"):
    """Barras: R_global por cada valor de N probado"""
    _ensure_dir(out_dir)
    
    # sensitivity_results tiene {"variation_N": {4: -10, 5: 20, 6: 50}, ...}
    if "variation_N" not in sensitivity_results:
        return
        
    n_data = sensitivity_results["variation_N"]
    
    x = [str(k) for k in n_data.keys()]
    y = list(n_data.values())
    
    plt.figure(figsize=(8, 6))
    bars = plt.bar(x, y, color='skyblue')
    plt.axhline(0, color='black', linewidth=1)
    
    plt.title("Análisis de Sensibilidad: Tamaño del Mundo (N)")
    plt.xlabel("Dimensión N")
    plt.ylabel("Performance Global (R_global)")
    
    filepath = os.path.join(out_dir, "sensitivity_N.png")
    plt.savefig(filepath, bbox_inches='tight')
    plt.close()

def plot_scalability(scalability_results, out_dir: str = "results"):
    """Línea: tiempo_por_iteracion vs N"""
    _ensure_dir(out_dir)
    
    x = sorted(scalability_results.keys())
    y = [scalability_results[k]["avg_time"] for k in x]
    err = [scalability_results[k]["std_dev"] for k in x]
    
    plt.figure(figsize=(10, 6))
    plt.errorbar(x, y, yerr=err, fmt='-o', color='purple', linewidth=2, capsize=5, label='Promedio ± Desv. Est.')
    
    plt.ylabel("Tiempo Promedio de Ejecución (s)")
    plt.xlabel("Dimensión N")
    plt.title("Escalabilidad del Simulador: Tiempo vs Tamaño del Mundo (N)")
    plt.grid(True, linestyle='--', alpha=0.7)
    plt.legend()
    
    filepath = os.path.join(out_dir, "scalability_time.png")
    plt.savefig(filepath, bbox_inches='tight')
    plt.close()

def plot_communication_impact(results: dict, out_dir: str = "results"):
    """Grafica el impacto de la comunicación vs cantidad de robots."""
    _ensure_dir(out_dir)
    robots = sorted(list(results["communication_impact"].keys()))
    scores_con = [results["communication_impact"][r]["CON"] for r in robots]
    scores_sin = [results["communication_impact"][r]["SIN"] for r in robots]
    
    plt.figure(figsize=(10, 6))
    plt.plot(robots, scores_con, marker='o', label='Con Comunicación', color='blue', linewidth=2)
    plt.plot(robots, scores_sin, marker='s', label='Sin Comunicación', color='red', linewidth=2, linestyle='--')
    
    plt.xlabel("Densidad (Número de Robots)")
    plt.ylabel("Puntaje Global (R_global)")
    plt.title("Impacto del Protocolo de Comunicación según Densidad (N=3)")
    plt.grid(True, linestyle='--', alpha=0.7)
    plt.legend()
    
    filepath = os.path.join(out_dir, "comm_impact.png")
    plt.savefig(filepath, bbox_inches='tight')
    plt.close()

def plot_score_distribution(robots_scores, out_dir: str = "results"):
    """Histograma: distribución de R_i entre todos los robots"""
    _ensure_dir(out_dir)
    
    scores = list(robots_scores.values())
    
    plt.figure(figsize=(8, 6))
    plt.hist(scores, bins=10, color='teal', edgecolor='black')
    
    plt.title("Distribución de Performance de Robots (R_i)")
    plt.xlabel("Score (R_i)")
    plt.ylabel("Frecuencia")
    
    filepath = os.path.join(out_dir, "robot_scores_histogram.png")
    plt.savefig(filepath, bbox_inches='tight')
    plt.close()

def plot_iridium_histogram(iridio_por_robot: dict, out_dir: str = "results"):
    """Histograma: iridio recolectado por cada robot (F3)"""
    _ensure_dir(out_dir)
    robots = [f"R{r}" for r in iridio_por_robot.keys()]
    iridios = list(iridio_por_robot.values())
    
    plt.figure(figsize=(8, 6))
    plt.bar(robots, iridios, color='gold', edgecolor='black')
    
    plt.title("Iridio Recolectado por Robot")
    plt.xlabel("Robot ID")
    plt.ylabel("Cantidad de Iridio")
    plt.grid(axis='y', linestyle='--', alpha=0.7)
    
    filepath = os.path.join(out_dir, "iridium_histogram.png")
    plt.savefig(filepath, bbox_inches='tight')
    plt.close()

def plot_death_causes_piechart(causas_muerte: dict, out_dir: str = "results"):
    """Gráfico de Torta: Distribución de causas de muerte (F3)"""
    _ensure_dir(out_dir)
    if not causas_muerte:
        return
        
    labels = list(causas_muerte.keys())
    sizes = list(causas_muerte.values())
    
    plt.figure(figsize=(8, 8))
    plt.pie(sizes, labels=labels, autopct='%1.1f%%', startangle=140, colors=['#ff9999','#66b3ff','#99ff99','#ffcc99'])
    plt.title("Distribución de Causas de Muerte")
    
    filepath = os.path.join(out_dir, "death_causes_pie.png")
    plt.savefig(filepath, bbox_inches='tight')
    plt.close()

def plot_n_robot_sensitivity(results_dict, out_dir: str = "results"):
    """Línea: Impacto de N_robot (F5)"""
    if "variation_N_ROBOT" not in results_dict:
        return
        
    _ensure_dir(out_dir)
    r_vals = sorted(list(results_dict["variation_N_ROBOT"].keys()))
    rg_vals = [results_dict["variation_N_ROBOT"][r]["R_global"] for r in r_vals]
    ts_vals = [results_dict["variation_N_ROBOT"][r]["TS"] for r in r_vals]
    
    fig, ax1 = plt.subplots(figsize=(8, 5))
    ax1.set_xlabel('N_robot (Cantidad de Robots)')
    ax1.set_ylabel('R_global', color='tab:red')
    ax1.plot(r_vals, rg_vals, color='tab:red', marker='o', linewidth=2, label='R_global')
    ax1.tick_params(axis='y', labelcolor='tab:red')
    ax1.grid(True, linestyle='--', alpha=0.7)
    
    ax2 = ax1.twinx()
    ax2.set_ylabel('Tasa de Supervivencia (TS)', color='tab:blue')
    ax2.plot(r_vals, ts_vals, color='tab:blue', marker='s', linewidth=2, linestyle='--', label='TS')
    ax2.tick_params(axis='y', labelcolor='tab:blue')
    ax2.set_ylim(-0.05, 1.05)
    
    plt.title('Sensibilidad frente a la Densidad de Presas (N_robot)')
    fig.tight_layout()
    filepath = os.path.join(out_dir, "sensitivity_n_robot.png")
    plt.savefig(filepath, bbox_inches='tight')
    plt.close()

def plot_n_monstruos_sensitivity(results_dict, out_dir: str = "results"):
    """Línea: Impacto de N_monstruos (F5)"""
    if "variation_N_MONSTRUOS" not in results_dict:
        return
        
    _ensure_dir(out_dir)
    m_vals = sorted(list(results_dict["variation_N_MONSTRUOS"].keys()))
    rg_vals = [results_dict["variation_N_MONSTRUOS"][m]["R_global"] for m in m_vals]
    ts_vals = [results_dict["variation_N_MONSTRUOS"][m]["TS"] for m in m_vals]
    
    fig, ax1 = plt.subplots(figsize=(8, 5))
    ax1.set_xlabel('N_monstruos (Cantidad de Depredadores)')
    ax1.set_ylabel('R_global', color='tab:red')
    ax1.plot(m_vals, rg_vals, color='tab:red', marker='v', linewidth=2, label='R_global')
    ax1.tick_params(axis='y', labelcolor='tab:red')
    ax1.grid(True, linestyle='--', alpha=0.7)
    
    ax2 = ax1.twinx()
    ax2.set_ylabel('Tasa de Supervivencia (TS)', color='tab:blue')
    ax2.plot(m_vals, ts_vals, color='tab:blue', marker='s', linewidth=2, linestyle='--', label='TS')
    ax2.tick_params(axis='y', labelcolor='tab:blue')
    ax2.set_ylim(-0.05, 1.05)
    
    plt.title('Sensibilidad frente a la Densidad de Depredadores (N_monstruos)')
    fig.tight_layout()
    filepath = os.path.join(out_dir, "sensitivity_n_monstruos.png")
    plt.savefig(filepath, bbox_inches='tight')
    plt.close()
