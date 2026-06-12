import random
from typing import Optional, Tuple, Any

from config import DeathCause


class MonsterAgent:
    """
    Agente Monstruo — reflejo simple, sin memoria, sin orientación.

    Reglas de diseño críticas (per requerimientos):
    ─────────────────────────────────────────────
    • La posición NO se almacena entre iteraciones: la administra el World/Simulator.
      Se recibe como parámetro en step() y en cada método que la necesita.
    • La frecuencia 1/4 la decide el Simulator. step() asume que ya es su turno.
    • RoboKiller SIEMPRE antes de RoboJumper dentro del mismo turno.
    • La fusión la resuelve robojumper() internamente: el monstruo de la celda
      destino absorbe al que salta. robojumper() retorna el monstruo sobreviviente
      (puede ser self u otro) para que el Simulator actualice su lista.
    """

    def __init__(self, monster_id: int):
        self.id = monster_id
        self.is_alive: bool = True

        # Métricas (REQ-MON-02)
        self.robots_eaten: int = 0   # Robofagímetro
        self.jumps_count: int = 0

    # =========================================================================
    # SENSORES
    # =========================================================================

    def perceive(self, world, position: Tuple[int, int, int]) -> dict:
        """
        Robotscopio (REQ-MON-S01): detecta si hay un robot en la celda actual.
        Retorna {'robot_presente': bool}.
        """
        x, y, z = position
        cell = world.get_cell(x, y, z)
        return {"robot_presente": cell.robot is not None}

    # =========================================================================
    # LÓGICA DE DECISIÓN — tabla reflejo simple (REQ-MON-D01)
    # =========================================================================

    def decide(self, perception: dict) -> str:
        """
        Tabla percepción→acción completamente determinista:
          SI robot_presente → ROBOKILLER
          (siempre) → ROBOJUMPER
        RoboKiller tiene prioridad (REQ-MON-D01 + punto crítico 4).
        """
        if perception["robot_presente"]:
            return "ROBOKILLER"
        return "ROBOJUMPER"

    # =========================================================================
    # EFECTORES
    # =========================================================================

    def robokiller(self, world, position: Tuple[int, int, int]) -> Optional[Any]:
        """
        REQ-MON-E01: destruye el robot en la celda actual.
        Retorna el robot destruido (para que el Simulator actualice logs).
        """
        x, y, z = position
        cell = world.get_cell(x, y, z)
        robot = cell.robot

        if robot is not None:
            # Matar robot: AutoShutdown externo con causa MONSTER
            robot.is_alive = False
            robot.death_cause = DeathCause.KILLED_BY_MONSTER
            world.remove_entity(robot, "robot", x, y, z)
            self.robots_eaten += 1
            return robot

        return None  # No había robot (no debería ocurrir si perceive fue correcto)

    def robojumper(self, world, position: Tuple[int, int, int]) -> Tuple[Optional[Any], Optional[Tuple[int, int, int]]]:
        """
        REQ-MON-E02: salta a una celda adyacente válida.

        Orden de prioridad del filtrado:
        1. Obtener los 6 vecinos.
        2. Filtrar: solo FREE.
        3. Filtrar: sin iridio.
        4. De los restantes, si alguno contiene otro monstruo → fusión:
             el monstruo de la celda destino absorbe a self.
        5. Si no hay ninguna celda válida → no se mueve (retorna sin error).
        6. Si hay opciones sin monstruo → saltar a una aleatoria.

        Retorna (surviving_monster, new_position):
          - surviving_monster: self si no hay fusión, o el monstruo destino si la hay.
          - new_position: coordenada nueva o None si no se movió.
        """
        x, y, z = position
        neighbors = world.get_neighbors(x, y, z)

        # Paso 1 + 2: vecinos FREE
        valid = [(nx, ny, nz) for (nx, ny, nz) in neighbors
                 if world.get_cell(nx, ny, nz).is_free()]

        # Paso 3: filtrar celdas con iridio
        valid = [(nx, ny, nz) for (nx, ny, nz) in valid
                 if world.get_cell(nx, ny, nz).iridio is None]

        if not valid:
            # Paso 5: sin opciones → sin movimiento
            return self, None

        # Paso 4: ¿hay alguna celda con otro monstruo? → fusión preferente
        with_monster = [(nx, ny, nz) for (nx, ny, nz) in valid
                        if world.get_cell(nx, ny, nz).monster is not None]

        if with_monster:
            # Elegir una celda con monstruo aleatoriamente y fusionar
            dest = random.choice(with_monster)
            return self._fuse_into(world, position, dest)

        # Paso 6: saltar a una celda vacía aleatoria
        dest = random.choice(valid)
        world.remove_entity(self, "monster", x, y, z)
        world.place_entity(self, "monster", *dest)
        self.jumps_count += 1
        return self, dest

    def _fuse_into(self, world, current_pos: Tuple[int, int, int], dest_pos: Tuple[int, int, int]) -> Tuple[Any, Tuple[int, int, int]]:
        """
        Fusión: el monstruo que está en dest_pos (surviving) absorbe a self (absorbed).
        surviving.robots_eaten += self.robots_eaten
        surviving.jumps_count  += self.jumps_count
        self.is_alive = False
        Retorna (surviving_monster, dest_pos).
        """
        dx, dy, dz = dest_pos
        surviving = world.get_cell(dx, dy, dz).monster

        # Sumar estadísticas al sobreviviente
        surviving.robots_eaten += self.robots_eaten
        surviving.jumps_count += self.jumps_count

        # Eliminar al absorbido del mundo
        world.remove_entity(self, "monster", *current_pos)
        self.is_alive = False
        self.jumps_count += 1   # El salto que provocó la fusión también cuenta

        return surviving, dest_pos

    def fuse_with(self, other: "MonsterAgent") -> None:
        """
        Interfaz pública para que el Simulator provoque una fusión desde fuera
        si lo necesita. self absorbe a other.
        """
        self.robots_eaten += other.robots_eaten
        self.jumps_count += other.jumps_count
        other.is_alive = False

    # =========================================================================
    # CICLO PRINCIPAL (REQ-MON step)
    # =========================================================================

    def act(self, action: str, world, position: Tuple[int, int, int]):
        """
        Ejecuta la acción decidida.
        Retorna un dict con información útil para el Simulator/Logger:
          {
            "action": str,
            "robot_killed": robot | None,
            "surviving_monster": MonsterAgent,
            "new_position": (x,y,z) | None
          }
        """
        result = {
            "action": action,
            "robot_killed": None,
            "surviving_monster": self,
            "new_position": position,
        }

        if action == "ROBOKILLER":
            result["robot_killed"] = self.robokiller(world, position)
            # Tras matar, siempre intentar saltar (mismo turno)
            surviving, new_pos = self.robojumper(world, position)
            result["surviving_monster"] = surviving
            result["new_position"] = new_pos if new_pos is not None else position
            result["action"] = "ROBOKILLER+ROBOJUMPER"

        elif action == "ROBOJUMPER":
            surviving, new_pos = self.robojumper(world, position)
            result["surviving_monster"] = surviving
            result["new_position"] = new_pos if new_pos is not None else position

        return result

    def step(self, world, position: Tuple[int, int, int]) -> dict:
        """
        Ciclo completo del monstruo para un turno:
          percibir → decidir → actuar.
        El Simulator llama step() solo en los ticks donde corresponde (T mod 4 == 0).
        El monstruo no verifica el reloj global internamente.
        """
        if not self.is_alive:
            return {"action": "DEAD", "surviving_monster": self, "new_position": position}

        perception = self.perceive(world, position)
        action = self.decide(perception)
        return self.act(action, world, position)

    # =========================================================================
    # UTILIDAD
    # =========================================================================

    def performance_score(self) -> int:
        """
        REQ-MET-03: M_j = robots_eaten * 100 + jumps_count
        """
        return self.robots_eaten * 100 + self.jumps_count

    def __repr__(self) -> str:
        return (f"Monster(id={self.id}, alive={self.is_alive}, "
                f"eaten={self.robots_eaten}, jumps={self.jumps_count})")
