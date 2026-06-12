import random
from typing import Set, Tuple, List, Dict

import config
from config import Action, DeathCause, DIRECTIONS
from world import World
from robot_agent import RobotAgent
from monster_agent import MonsterAgent
from logger import SimLogger
from metrics import MetricsCollector


# Dummy classes removed, now importing real ones.


class Simulator:
    def __init__(self, logger=None, metrics=None):
        self.world = World(
            N=config.N,
            P_free=config.P_FREE,
            P_soft=config.P_SOFT,
            P_negro=config.P_NEGRO,
            seed=config.SEED
        )
        
        self.robots: List[RobotAgent] = []
        self.monsters: List[MonsterAgent] = []
        
        self.robot_positions: Dict[RobotAgent, Tuple[int, int, int]] = {}
        self.monster_positions: Dict[MonsterAgent, Tuple[int, int, int]] = {}
        self.iridio_positions: Set[Tuple[int, int, int]] = set()
        
        self.termination_reason = None
        
        self.logger = logger or SimLogger()
        self.metrics = metrics or MetricsCollector()
        
    def initialize(self):
        """Ubica todas las entidades aleatoriamente en celdas FREE vacías."""
        # Instanciar y ubicar Monstruos
        for i in range(config.N_MONSTRUOS):
            monster = MonsterAgent(monster_id=i+1)
            pos = self.world.get_free_random_position()
            self.world.place_entity(monster, "monster", *pos)
            self.monsters.append(monster)
            self.monster_positions[monster] = pos

        # Instanciar y ubicar Robots
        for i in range(config.N_ROBOT):
            # Asignar una dirección aleatoria inicial
            init_dir = random.choice(DIRECTIONS)
            robot = RobotAgent(robot_id=i+1, initial_dir=init_dir)
            pos = self.world.get_free_random_position()
            self.world.place_entity(robot, "robot", *pos)
            self.robots.append(robot)
            self.robot_positions[robot] = pos

        # Instanciar y ubicar Iridio
        # Usamos una cadena "iridio_N" como objeto dummy para el iridio
        for i in range(config.N_IRIDIO):
            pos = self.world.get_free_random_position()
            iridio_obj = f"iridio_{i+1}"
            self.world.place_entity(iridio_obj, "iridio", *pos)
            self.iridio_positions.add(pos)
            
        # Calcular propagaciones iniciales
        self.world.update_iridio_glow()
        self.world.update_monster_smell()

    def run(self, verbose: bool = True):
        """Bucle principal de simulación."""
        t = config.T_INICIO
        while True:
            self.step(t)
            term_reason = self._check_termination(t)
            if term_reason is not None:
                self.termination_reason = term_reason
                self.logger.log_simulation_end(term_reason, t)
                if verbose:
                    print(f"[Simulator] Simulación terminada en T={t}. Razón: {term_reason}")
                break
            t += 1
            
        return self.metrics.generate_summary()

    def step(self, t: int):
        """
        Orden estricto y no negociable del Tick:
        1. Activar robots
        2. Si T % 4 == 0 → activar monstruos
        3. Resolver colisiones
        4. Actualizar señales
        5. Registrar métricas
        """
        # 1. Activar robots
        for robot in list(self.robots):
            if not robot.is_alive:
                continue
            pos = self.robot_positions[robot]
            result = robot.step(self.world, pos, t)
            self._handle_robot_result(robot, result, t)
            
            # Limpieza inmediata si murió en su step o por la comunicación
            if not robot.is_alive and robot in self.robots:
                self.robots.remove(robot)

        # 2. Activar monstruos (velocidad 1/4)
        if t % 4 == 0:
            for monster in list(self.monsters):
                if not monster.is_alive:
                    continue
                pos = self.monster_positions[monster]
                result = monster.step(self.world, pos)
                self._handle_monster_result(monster, result, t)
                
                # Limpieza de absorbidos por fusión o error
                if not monster.is_alive and monster in self.monsters:
                    self.monsters.remove(monster)

        # 3. Resolver colisiones robot+monstruo
        self._resolve_collisions(t)

        # 4. Actualizar señales
        self.world.update_iridio_glow()
        self.world.update_monster_smell()

        # 5. Registrar métricas
        self.metrics.record(t, self.world, self.robots, self.monsters)

    # =========================================================================
    # MANEJO DE RESULTADOS
    # =========================================================================

    def _handle_robot_result(self, robot: RobotAgent, result: dict, t: int):
        action = result["action"]
        
        if action == "COMMUNICATE":
            # El robot detectó robot_delante=True y decidió iniciar comunicación
            front_pos = robot._get_front_cell(self.robot_positions[robot])
            cell = self.world.get_cell(*front_pos)
            
            if cell.robot is None:
                # El otro robot probablemente ya se movió en este mismo tick
                # En este caso, el robot primario pierde el turno o se le obliga a WAIT
                robot.update_memory(t, result["perception"], Action.WAIT, "MISSED_COMM")
                robot.generate_new_rules()
                return
                
            other_robot = cell.robot
            self._resolve_communication(robot, other_robot, t, result["perception"])
            
        elif action == "MOVE_FORWARD":
            self.robot_positions[robot] = result["new_position"]
            self.logger.log_robot_move(robot.id, self.robot_positions[robot], result["new_position"], t)
            
        elif action.startswith("TURN"):
            self.logger.log_robot_turn(robot.id, result["new_direction"], t)
            
        elif action == "SUCK_IRIDIO":
            pos = self.robot_positions[robot]
            if pos in self.iridio_positions:
                self.iridio_positions.remove(pos)
                self.logger.log_iridio_collected(pos, robot.id, t)
                
        elif action == "SHUTDOWN":
            self.logger.log_robot_destroyed(robot.id, result["reason"], t, robot_agent=robot)
            robot.memory.clear()

    def _handle_monster_result(self, monster: MonsterAgent, result: dict, t: int):
        action = result["action"]
        
        if "ROBOKILLER" in action:
            robot_killed = result.get("robot_killed")
            if robot_killed is not None:
                self.logger.log_robot_destroyed(robot_killed.id, "MONSTER_ROBOKILLER", t, robot_agent=robot_killed)
                robot_killed.memory.clear()
                if robot_killed in self.robots:
                    self.robots.remove(robot_killed)
                    
        # Para RoboJumper, actualizar posición y verificar si hubo fusión
        if "ROBOJUMPER" in action:
            surviving = result["surviving_monster"]
            new_pos = result["new_position"]
            
            # Si el monstruo que saltó sobrevivió (no hubo fusión)
            if surviving == monster:
                self.monster_positions[monster] = new_pos
            else:
                # Fusión: el monstruo que saltó fue absorbido por surviving
                self.logger.log_monster_fuse(monster.id, surviving.id, surviving.id, t)
                # No actualizamos position del monster porque ya is_alive = False

    # =========================================================================
    # COLISIONES Y PROTOCOLOS SÍNCRONOS
    # =========================================================================

    def _resolve_collisions(self, t: int):
        """El robot caminó hacia la celda de un monstruo, el monstruo lo mata por ocupación pasiva."""
        for robot in list(self.robots):
            if not robot.is_alive:
                continue
            
            pos = self.robot_positions[robot]
            cell = self.world.get_cell(*pos)
            
            if cell.monster is not None:
                monster = cell.monster
                # El monstruo mata al robot
                robot.is_alive = False
                robot.death_cause = DeathCause.KILLED_BY_MONSTER
                self.world.remove_entity(robot, "robot", *pos)
                monster.robots_eaten += 1
                self.robots.remove(robot)
                self.logger.log_robot_destroyed(robot.id, "MONSTER_COLLISION", t, robot_agent=robot)
                robot.memory.clear()

    def _resolve_communication(self, robot_a: RobotAgent, robot_b: RobotAgent, t: int, perception_a):
        decision_a = robot_a.communicate(robot_b)
        decision_b = robot_b.communicate(robot_a) # No lo usamos explícitamente según el requerimiento, la decisión rige por decision_a
        
        pos_a = self.robot_positions[robot_a]
        pos_b = self.robot_positions[robot_b]
        
        if decision_a == "yo_sigo":
            # Robot A avanza, Robot B gira
            res_a = robot_a.act(Action.MOVE_FORWARD, self.world, pos_a, t)
            if res_a["action"] == "MOVE_FORWARD":
                self.robot_positions[robot_a] = res_a["new_position"]
            robot_a.update_memory(t, perception_a, Action.MOVE_FORWARD, res_a["action"])
            robot_a.generate_new_rules()
            
            # Forzamos acción en B sin que consuma formalmente su step() normal,
            # pero afectando su estado y registrándolo en memoria.
            # Sin embargo, como B generará su propia percepción en su turno,
            # esto podría corromper el tracking si no le pasamos una percepción actual.
            # El requerimiento simplifica: B gira.
            res_b = robot_b.act(Action.TURN_0, self.world, pos_b, t)
            # Para mantener limpio el flujo sin inyectar percepción falsa, omitimos update_memory de B
            # o requeriríamos leer su percepción aquí. Para simplificar, seguimos el requerimiento literal.
            
        else:
            # Robot A gira, Robot B sigue su curso (actuará en su turno)
            res_a = robot_a.act(Action.TURN_0, self.world, pos_a, t)
            robot_a.update_memory(t, perception_a, Action.TURN_0, res_a["action"])
            robot_a.generate_new_rules()
            
        self.logger.log_robot_comm(robot_a.id, robot_b.id, decision_a, t)

    # =========================================================================
    # TERMINACIÓN
    # =========================================================================

    def _check_termination(self, t: int):
        if t >= config.T_FIN:
            return "TIME_LIMIT"
        if len(self.robots) == 0:
            return "ALL_ROBOTS_DEAD"
        if len(self.iridio_positions) == 0:
            return "ALL_IRIDIO_COLLECTED"
        return None
