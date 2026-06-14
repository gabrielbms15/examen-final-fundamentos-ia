import csv
import json
from typing import List, Dict, Any, Tuple

import config


class MetricsCollector:
    def __init__(self):
        self.history: List[Dict[str, Any]] = []
        
        # Trackeo persistente de celdas visitadas para EE y pasos_sin_avance_i
        # {robot_id: set of (x,y,z)}
        self._celdas_visitadas_por_robot: Dict[int, set] = {}
        
        # Estado acumulado necesario para ciertas métricas
        self._pasos_sin_avance: Dict[int, int] = {}
        self._agujeros_negros_caidos = 0
        self._bucles_detectados_acumulado = 0
        
        # Guardar robots muertos para los cálculos de métricas al final
        self._all_robots: dict = {} # id -> robot_agent (vivo o muerto)

    def record(self, t: int, world, robots: List[Any], monsters: List[Any]):
        """Toma un snapshot del estado actual de la simulación."""
        
        snapshot = {
            "t": t,
            "robots_vivos": len(robots),
            "monstruos_vivos": len(monsters),
        }
        
        iridio_total_recolectado = 0
        memoria_size_total = 0
        reglas_generadas_total = 0
        
        # Asegurar tracking de todos los robots que han pasado por la simulación
        for r in robots:
            if r.id not in self._all_robots:
                self._all_robots[r.id] = r
                self._celdas_visitadas_por_robot[r.id] = set()
                self._pasos_sin_avance[r.id] = 0
                
        for r in self._all_robots.values():
            iridio_total_recolectado += r.iridio_count
            memoria_size_total += len(r.memory)
            # Solo consideramos como reglas generadas a aquellas que superan las reglas base, 
            # pero dado que el robot inicia con 0 reglas base en nuestra impl, len(rules) es suficiente.
            reglas_generadas_total += len(r.rules)
            
            # Evaluación de avance
            pos = r.memory[-1].posicion if r.memory else None
            if pos:
                es_nueva = pos not in self._celdas_visitadas_por_robot[r.id]
                self._celdas_visitadas_por_robot[r.id].add(pos)
                
                # Si no exploró celda nueva Y no recogió iridio en este step
                # (evaluamos recogió iridio asumiendo que actuó en SUCK_IRIDIO y subió iridio_count)
                # Como lo hacemos de manera retroactiva con el history:
                recogio_ahora = r.memory[-1].accion.value == "SUCK_IRIDIO" if r.memory else False
                if not es_nueva and not recogio_ahora:
                    self._pasos_sin_avance[r.id] += 1
        
        snapshot["iridio_total_recolectado"] = iridio_total_recolectado
        
        # Recuento de iridio en el mapa
        iridio_restante = 0
        for z in range(world.N):
            for y in range(world.N):
                for x in range(world.N):
                    if world.grid[x][y][z].iridio is not None:
                        iridio_restante += 1
        snapshot["iridio_restante"] = iridio_restante
        
        # Muertes y causas (acumuladas globalmente por todos los robots caídos)
        robots_destruidos = sum(1 for r in self._all_robots.values() if not r.is_alive)
        self._bucles_detectados_acumulado = sum(1 for r in self._all_robots.values() if not r.is_alive and r.death_cause and "LOOP" in r.death_cause.name)
        self._agujeros_negros_caidos = sum(1 for r in self._all_robots.values() if not r.is_alive and r.death_cause and "BLACK_HOLE" in r.death_cause.name)

        snapshot["robots_destruidos_acumulado"] = robots_destruidos
        snapshot["bucles_detectados_acumulado"] = self._bucles_detectados_acumulado
        snapshot["agujeros_negros_caidos"] = self._agujeros_negros_caidos
        
        snapshot["memoria_size_promedio"] = memoria_size_total / max(len(robots), 1)
        snapshot["reglas_generadas_promedio"] = reglas_generadas_total / max(len(robots), 1)
        
        # Celdas FREE exploradas (unión de todos los sets)
        celdas_totales_exploradas = set()
        for c_set in self._celdas_visitadas_por_robot.values():
            celdas_totales_exploradas.update(c_set)
            
        total_free_cells = sum(1 for z in range(world.N) for y in range(world.N) for x in range(world.N) if world.grid[x][y][z].is_free())
        snapshot["celdas_exploradas_promedio"] = len(celdas_totales_exploradas) / max(total_free_cells, 1)

        self.history.append(snapshot)

    # =========================================================================
    # COMPUTACIÓN DE SCORES Y EFICIENCIAS
    # =========================================================================

    def compute_robot_score(self, robot) -> float:
        """Calcula R_i (REQ-MET-01)"""
        w1, w2, w3, w4, w5 = config.W1_IRIDIO, config.W2_DEATH, config.W3_LOOP, config.W4_SURVIVE, config.W5_IDLE
        
        deaths_i = 0 if robot.is_alive else 1
        bucles_i = 1 if (not robot.is_alive and robot.death_cause and "LOOP" in robot.death_cause.name) else 0
        tiempo_sobrevivido = robot.step_count
        pasos_sin_avance = self._pasos_sin_avance.get(robot.id, 0)
        
        score = (w1 * robot.iridio_count) \
              - (w2 * deaths_i) \
              - (w3 * bucles_i) \
              + (w4 * tiempo_sobrevivido / config.T_FIN) \
              - (w5 * pasos_sin_avance)
        return score

    def compute_robot_score_breakdown(self, robot) -> Dict[str, float]:
        """Devuelve los componentes de R_i"""
        w1, w2, w3, w4, w5 = config.W1_IRIDIO, config.W2_DEATH, config.W3_LOOP, config.W4_SURVIVE, config.W5_IDLE
        
        deaths_i = 0 if robot.is_alive else 1
        bucles_i = 1 if (not robot.is_alive and robot.death_cause and "LOOP" in robot.death_cause.name) else 0
        tiempo_sobrevivido = robot.step_count
        pasos_sin_avance = self._pasos_sin_avance.get(robot.id, 0)
        
        return {
            "iridio": (w1 * robot.iridio_count),
            "death": -(w2 * deaths_i),
            "bucle": -(w3 * bucles_i),
            "survival": (w4 * tiempo_sobrevivido / config.T_FIN),
            "idle": -(w5 * pasos_sin_avance)
        }

    def compute_global_score(self) -> float:
        """Calcula R_global (REQ-MET-02)"""
        return sum(self.compute_robot_score(r) for r in self._all_robots.values())

    def compute_monster_score(self, monster) -> float:
        """Calcula M_j (REQ-MET-03)"""
        return (monster.robots_eaten * 100) + monster.jumps_count

    def compute_exploration_efficiency(self, total_free_cells: int) -> float:
        """Calcula EE (REQ-MET-06) global"""
        celdas_totales_exploradas = set()
        for c_set in self._celdas_visitadas_por_robot.values():
            celdas_totales_exploradas.update(c_set)
        return len(celdas_totales_exploradas) / max(total_free_cells, 1)

    def compute_survival_rate(self) -> float:
        """Calcula TS (REQ-MET-07)"""
        if not self._all_robots: return 0.0
        vivos = sum(1 for r in self._all_robots.values() if r.is_alive)
        return vivos / len(self._all_robots)

    def compute_collection_efficiency(self) -> float:
        """Calcula ER (REQ-MET-08)"""
        if config.N_IRIDIO == 0: return 0.0
        recolectado = sum(r.iridio_count for r in self._all_robots.values())
        return recolectado / config.N_IRIDIO

    def get_visit_heatmap(self, N: int) -> list:
        """Retorna array N×N con conteo de visitas colapsando eje Z."""
        heatmap = [[0]*N for _ in range(N)]
        for positions in self._celdas_visitadas_por_robot.values():
            for (x, y, z) in positions:
                heatmap[x][y] += 1
        return heatmap

    def generate_summary(self, world=None, monsters=None) -> Dict[str, Any]:
        """Resumen estadístico final (REQ-MET-05)"""
        
        iridio_por_robot = {r.id: r.iridio_count for r in self._all_robots.values()}
        causas_muerte = {}
        reglas_por_robot = {r.id: len(r.rules) for r in self._all_robots.values()}
        
        for r in self._all_robots.values():
            if not r.is_alive and r.death_cause:
                causa = r.death_cause.name
                causas_muerte[causa] = causas_muerte.get(causa, 0) + 1
                
        summary = {
            "global_score": self.compute_global_score(),
            "survival_rate": self.compute_survival_rate(),
            "collection_efficiency": self.compute_collection_efficiency(),
            "robots_scores": {r.id: self.compute_robot_score(r) for r in self._all_robots.values()},
            "robots_scores_breakdown": {r.id: self.compute_robot_score_breakdown(r) for r in self._all_robots.values()},
            "iridio_por_robot": iridio_por_robot,
            "causas_muerte_robots": causas_muerte,
            "reglas_aprendidas_por_robot": reglas_por_robot
        }
        
        if world is not None:
            total_free_cells = sum(1 for z in range(world.N) for y in range(world.N) for x in range(world.N) if world.grid[x][y][z].is_free())
            summary["exploration_efficiency"] = self.compute_exploration_efficiency(total_free_cells)
            summary["visit_heatmap"] = self.get_visit_heatmap(world.N)
            
        if monsters is not None:
            summary["monster_scores"] = {m.id: self.compute_monster_score(m) for m in monsters}

        return summary

    def export_to_csv(self, filepath: str):
        if not self.history:
            return
            
        with open(filepath, 'w', newline='', encoding='utf-8') as f:
            fieldnames = self.history[0].keys()
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            for row in self.history:
                writer.writerow(row)

    def export_to_json(self, filepath: str):
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(self.history, f, indent=2)
