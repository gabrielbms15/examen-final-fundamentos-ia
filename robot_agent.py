import random
from dataclasses import dataclass
from typing import Dict, Any, List, Tuple, Callable

import config
from config import Action, CellType, DeathCause, turn


@dataclass
class Perception:
    olor: bool
    brillo: bool
    iridio_aqui: bool
    robot_delante: bool
    posicion: Tuple[int, int, int]
    direccion: Tuple[int, int, int]
    vacuscopio: bool
    bucle: bool

@dataclass
class MemoryRecord:
    t: int
    percepcion: Perception
    accion: Action
    posicion: Tuple[int, int, int]
    resultado: str

@dataclass
class Rule:
    condicion: Callable[[Perception, Action], bool]
    descripcion: str
    weight_modifier: float


class RobotAgent:
    def __init__(self, robot_id: int, initial_dir: Tuple[int, int, int]):
        self.id = robot_id
        self.is_alive = True
        self.direction = initial_dir
        
        self.iridio_count = 0
        self.step_count = 0
        self.death_cause = None
        
        self.memory: List[MemoryRecord] = []
        self.rules: List[Rule] = []
        
        self._last_vacuscopio = False

    def step(self, world, position: Tuple[int, int, int], t: int) -> dict:
        """Ciclo completo del robot: perceive -> decide -> act"""
        if not self.is_alive:
            return {"action": Action.WAIT.value, "reason": "DEAD"}

        perception = self.perceive(world, position)
        action = self.decide(perception)
        
        # Protocolo de comunicación (Simulator se encarga de ejecutar y actualizar memoria)
        if action == Action.COMMUNICATE:
            return {"action": Action.COMMUNICATE.value, "perception": perception}
            
        result = self.act(action, world, position, t)
        
        self.update_memory(t, perception, action, result["action"])
        self.generate_new_rules()
        
        return result

    # =========================================================================
    # CAPA 1: PERCEPCIÓN
    # =========================================================================

    def perceive(self, world, position: Tuple[int, int, int]) -> Perception:
        x, y, z = position
        cell = world.get_cell(x, y, z)
        
        # Apestómetro
        olor = cell.olor
        
        # IridioScan (brillo en la celda actual)
        brillo = cell.brillo
                
        # Energómetro Espectral
        iridio_aqui = (cell.iridio is not None)
        
        # Roboscanner
        robot_delante = False
        front_pos = self._get_front_cell(position)
        if world.is_valid_position(*front_pos):
            front_cell = world.get_cell(*front_pos)
            if front_cell.robot is not None:
                robot_delante = True
                
        # Infinitómetro (Bucle)
        bucle = self._sense_infinitometro()

        return Perception(
            olor=olor,
            brillo=brillo,
            iridio_aqui=iridio_aqui,
            robot_delante=robot_delante,
            posicion=position,
            direccion=self.direction,
            vacuscopio=self._last_vacuscopio,
            bucle=bucle
        )

    def _sense_infinitometro(self) -> bool:
        """Analiza la memoria y detecta bucles (patrones repetidos)."""
        if len(self.memory) < config.LOOP_WINDOW:
            return False
            
        recent = self.memory[-config.LOOP_WINDOW:]
        pos_str = "".join([f"{r.posicion}" for r in recent])
        
        for length in range(config.LOOP_MIN_LEN, config.LOOP_WINDOW // config.LOOP_THRESHOLD + 1):
            for start in range(len(recent) - length * config.LOOP_THRESHOLD + 1):
                subseq = "".join([f"{r.posicion}" for r in recent[start:start+length]])
                if pos_str.count(subseq) >= config.LOOP_THRESHOLD:
                    return True
        return False

    def _get_front_cell(self, position: Tuple[int, int, int]) -> Tuple[int, int, int]:
        x, y, z = position
        dx, dy, dz = self.direction
        return (x + dx, y + dy, z + dz)

    # =========================================================================
    # CAPA 2: DECISIÓN
    # =========================================================================

    def decide(self, perception: Perception) -> Action:
        # Reglas Absolutas (Prioridad: Bypassan Utilidad)
        if perception.bucle:
            return Action.SHUTDOWN
        
        if perception.iridio_aqui:
            return Action.SUCK_IRIDIO
            
        if perception.robot_delante:
            return Action.COMMUNICATE

        # Utilidad
        candidates = [Action.MOVE_FORWARD, Action.TURN_0, Action.TURN_1, Action.TURN_2, Action.TURN_3]
        scores = {action: self.evaluate_utility(action, perception) for action in candidates}
        
        # Resolver empates determinísticamente garantizando la mejor acción
        best_score = max(scores.values())
        best_actions = [a for a, s in scores.items() if s == best_score]
        return best_actions[0]

    def evaluate_utility(self, action: Action, perception: Perception) -> float:
        score = 0.0
        
        if action == Action.MOVE_FORWARD:
            # Incentivos básicos basados en sensores (heurística inicial)
            if perception.brillo and not perception.olor:
                score += config.W1_IRIDIO  # Ir hacia el brillo
            if perception.olor:
                score -= config.W2_DEATH  # Huir del peligro
            if perception.vacuscopio:
                score -= 20.0  # Si acaba de chocar contra el vacío, desincentivar avanzar
                
            # Preferencia a explorar (frente a quedarse rotando en el mismo lugar)
            score += 1.0
            
        # Modificadores de peso basados en reglas aprendidas
        for rule in self.rules:
            if rule.condicion(perception, action):
                score += rule.weight_modifier
                
        return score

    # =========================================================================
    # CAPA 3: ACTUACIÓN
    # =========================================================================

    def act(self, action: Action, world, position: Tuple[int, int, int], t: int) -> dict:
        """Modifica el estado del robot y/o del mundo."""
        self.step_count += 1
        x, y, z = position
        
        if action == Action.SHUTDOWN:
            self.is_alive = False
            self.death_cause = DeathCause.KILLED_BY_LOOP
            world.remove_entity(self, "robot", *position)
            return {"action": "SHUTDOWN", "reason": "LOOP"}

        if action == Action.SUCK_IRIDIO:
            cell = world.get_cell(x, y, z)
            if cell.iridio:
                world.remove_entity(cell.iridio, "iridio", x, y, z)
                self.iridio_count += 1
            return {"action": "SUCK_IRIDIO"}

        if action == Action.MOVE_FORWARD:
            dest = self._get_front_cell(position)
            
            if not world.is_valid_position(*dest):
                self._last_vacuscopio = True
                return {"action": "BLOCKED", "reason": "OUT_OF_BOUNDS"}
                
            cell = world.get_cell(*dest)
            
            if cell.type == CellType.VOID:
                # El vacuscopio se activa AQUÍ como consecuencia de un intento fallido
                self._last_vacuscopio = True
                return {"action": "BLOCKED", "reason": "VOID"}
                
            elif cell.type == CellType.BLACK_HOLE:
                self._last_vacuscopio = False
                self.is_alive = False
                self.death_cause = DeathCause.KILLED_BY_BLACK_HOLE
                world.remove_entity(self, "robot", *position)
                # Entró al agujero, no existe más en el mapa
                return {"action": "SHUTDOWN", "reason": "BLACK_HOLE"}
                
            else:
                self._last_vacuscopio = False
                # Movimiento exitoso
                world.remove_entity(self, "robot", *position)
                world.place_entity(self, "robot", *dest)
                return {"action": "MOVE_FORWARD", "new_position": dest}

        # Manejo de giros a los 4 costados
        if action in [Action.TURN_0, Action.TURN_1, Action.TURN_2, Action.TURN_3]:
            # Extraer el índice 0, 1, 2 o 3 de la cadena de la acción
            side_index = int(action.value[-1])
            self.direction = turn(self.direction, side_index)
            self._last_vacuscopio = False
            return {"action": action.value, "new_direction": self.direction}

        return {"action": "WAIT"}

    def communicate(self, other_robot) -> str:
        """
        Única decisión aleatoria del robot. El Simulator será quien resuelva 
        las intenciones de ambos robots de forma síncrona.
        """
        decision = random.choice(["yo_sigo", "tu_sigues"])
        return decision

    # =========================================================================
    # APRENDIZAJE Y MEMORIA
    # =========================================================================

    def update_memory(self, t: int, perception: Perception, action: Action, result: str):
        """Almacena el registro histórico del ciclo."""
        record = MemoryRecord(
            t=t,
            percepcion=perception,
            accion=action,
            posicion=perception.posicion,
            resultado=result
        )
        self.memory.append(record)

    def generate_new_rules(self):
        """Busca patrones en la memoria para ajustar pesos de utilidad."""
        if len(self.memory) < 2:
            return
            
        last = self.memory[-1]
        prev = self.memory[-2]

        # PATRÓN 1: Peligro por olor
        if not self.is_alive and self.death_cause == DeathCause.KILLED_BY_MONSTER:
            if prev.percepcion.olor and prev.accion == Action.MOVE_FORWARD:
                bad_dir = prev.percepcion.direccion
                def cond_olor(p: Perception, a: Action, d=bad_dir) -> bool:
                    return p.olor and a == Action.MOVE_FORWARD and p.direccion == d
                    
                rule = Rule(condicion=cond_olor, descripcion="Penalizar avance tras olor", weight_modifier=-100.0)
                if not any(r.descripcion == rule.descripcion for r in self.rules):
                    self.rules.append(rule)

        # PATRÓN 2: Agujero negro memorizado
        if prev.accion == Action.MOVE_FORWARD and last.resultado == "SHUTDOWN" and self.death_cause == DeathCause.KILLED_BY_BLACK_HOLE:
            bad_pos = self._get_front_cell(prev.posicion)
            def cond_bh(p: Perception, a: Action, bp=bad_pos) -> bool:
                return a == Action.MOVE_FORWARD and self._get_front_cell(p.posicion) == bp
                
            rule = Rule(condicion=cond_bh, descripcion=f"Evitar BLACK_HOLE en {bad_pos}", weight_modifier=-1000.0)
            if not any(r.descripcion == rule.descripcion for r in self.rules):
                self.rules.append(rule)
                
        # PATRÓN 3: Iridio confirmado
        if prev.percepcion.brillo and prev.accion == Action.MOVE_FORWARD and last.percepcion.iridio_aqui:
            good_dir = prev.percepcion.direccion
            def cond_iridio(p: Perception, a: Action, d=good_dir) -> bool:
                return p.brillo and a == Action.MOVE_FORWARD and p.direccion == d
                
            rule = Rule(condicion=cond_iridio, descripcion="Reforzar avance por brillo confirmado", weight_modifier=50.0)
            if not any(r.descripcion == rule.descripcion for r in self.rules):
                self.rules.append(rule)
