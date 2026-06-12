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
    y = [scalability_results[k] for k in x]
    
    plt.figure(figsize=(8, 6))
    plt.plot(x, y, marker='o', linestyle='-', color='purple', linewidth=2)
    
    plt.title("Prueba de Escalabilidad")
    plt.xlabel("Tamaño del Mundo (N)")
    plt.ylabel("Tiempo de Simulación (segundos)")
    plt.grid(True, alpha=0.5)
    
    filepath = os.path.join(out_dir, "scalability_time.png")
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
