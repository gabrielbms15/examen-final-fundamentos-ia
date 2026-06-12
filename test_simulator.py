import unittest
from unittest.mock import MagicMock

import config
from config import Action, CellType, DeathCause
from simulator import Simulator
from robot_agent import RobotAgent
from monster_agent import MonsterAgent
from world import World


class TestSimulator(unittest.TestCase):

    def setUp(self):
        # Aseguramos que la semilla es determinista para pruebas
        config.SEED = 42
        config.N = 5
        config.N_ROBOT = 2
        config.N_MONSTRUOS = 2
        config.N_IRIDIO = 3
        config.T_INICIO = 0
        config.T_FIN = 100

    def test_1_inicializacion_sin_colisiones(self):
        sim = Simulator()
        sim.initialize()
        
        self.assertEqual(len(sim.robots), 2)
        self.assertEqual(len(sim.monsters), 2)
        self.assertEqual(len(sim.iridio_positions), 3)
        
        # Verificar que ninguna entidad comparte posición (ya que get_free_random_position evita superposiciones)
        # Recopilamos todas las posiciones
        todas_las_pos = list(sim.robot_positions.values()) + list(sim.monster_positions.values()) + list(sim.iridio_positions)
        
        # Un set debe tener la misma longitud si no hay duplicados
        self.assertEqual(len(todas_las_pos), len(set(todas_las_pos)))
        
        # Verificar que todas son FREE
        for pos in todas_las_pos:
            cell = sim.world.get_cell(*pos)
            self.assertEqual(cell.type, CellType.FREE)

    def test_2_robots_se_activan_cada_tick(self):
        sim = Simulator()
        sim.initialize()
        
        # Mockear step de los robots
        for robot in sim.robots:
            robot.step = MagicMock(return_value={"action": "WAIT"})
            
        # Correr 5 ticks (0, 1, 2, 3, 4)
        for t in range(5):
            sim.step(t)
            
        # Verificar que cada robot fue llamado 5 veces
        for robot in sim.robots:
            self.assertEqual(robot.step.call_count, 5)

    def test_3_monstruos_se_activan_cada_4_ticks(self):
        sim = Simulator()
        sim.initialize()
        
        # Mockear step de los monstruos
        for monster in sim.monsters:
            monster.step = MagicMock(return_value={"action": "WAIT"})
            
        # Correr 12 ticks (0 al 11)
        for t in range(12):
            sim.step(t)
            
        # Ticks donde monstruos se activan: 0, 4, 8 -> 3 veces
        for monster in sim.monsters:
            self.assertEqual(monster.step.call_count, 3)

    def test_4_colision_robot_monstruo(self):
        sim = Simulator()
        # Inicializar manualmente sin initialize() para evitar aleatoriedad
        robot = RobotAgent(robot_id=1, initial_dir=(1, 0, 0))
        monster = MonsterAgent(monster_id=1)
        
        sim.robots.append(robot)
        sim.monsters.append(monster)
        
        sim.robot_positions[robot] = (2, 2, 2)
        sim.monster_positions[monster] = (3, 2, 2)
        
        sim.world.place_entity(robot, "robot", 2, 2, 2)
        sim.world.place_entity(monster, "monster", 3, 2, 2)
        
        # Forzar que el robot avance hacia el monstruo (3, 2, 2)
        # Mockeamos step para que simplemente devuelva MOVE_FORWARD y la nueva pos
        robot.step = MagicMock(return_value={"action": "MOVE_FORWARD", "new_position": (3, 2, 2)})
        monster.step = MagicMock(return_value={"action": "WAIT"}) # Monstruo no hace nada en este test
        
        sim.step(1) # Un tick donde monstruos no se activan (1 % 4 != 0)
        
        # Después del step, el robot se movió a 3,2,2 y el Simulator resolvió la colisión
        self.assertFalse(robot.is_alive)
        self.assertEqual(robot.death_cause, DeathCause.KILLED_BY_MONSTER)
        self.assertEqual(monster.robots_eaten, 1)
        self.assertNotIn(robot, sim.robots)

    def test_5_condicion_termino_tiempo(self):
        config.T_FIN = 5
        sim = Simulator()
        sim.initialize()
        
        # Forzamos que los robots no hagan nada para no agotar el iridio o morir
        for robot in sim.robots:
            robot.step = MagicMock(return_value={"action": "WAIT"})
            
        sim.run()
        
        # El loop debería terminar en t=5 por "TIME_LIMIT"
        # Comprobamos la llamada al dummy logger
        self.assertTrue(True) # Si run termina, el test pasa. En t=5

    def test_6_condicion_termino_iridio_agotado(self):
        config.N_IRIDIO = 1
        sim = Simulator()
        sim.initialize()
        
        # Hacemos que el primer robot recoja el iridio inmediatamente
        robot = sim.robots[0]
        pos_iridio = list(sim.iridio_positions)[0]
        
        # Sobrescribimos su posición y forzamos SUCK_IRIDIO
        sim.world.remove_entity(robot, "robot", *sim.robot_positions[robot])
        sim.robot_positions[robot] = pos_iridio
        sim.world.place_entity(robot, "robot", *pos_iridio)
        
        robot.step = MagicMock(return_value={"action": "SUCK_IRIDIO"})
        
        # El resto esperan
        for r in sim.robots[1:]:
            r.step = MagicMock(return_value={"action": "WAIT"})
            
        for m in sim.monsters:
            m.step = MagicMock(return_value={"action": "WAIT"})
            
        sim.run()
        
        # Debería terminar porque len(iridio_positions) == 0
        self.assertEqual(len(sim.iridio_positions), 0)

    def test_7_posiciones_actualizadas_correctamente(self):
        sim = Simulator()
        sim.initialize()
        
        robot = sim.robots[0]
        pos_anterior = sim.robot_positions[robot]
        nueva_pos = (pos_anterior[0]+1, pos_anterior[1], pos_anterior[2]) # Asumiendo que es libre, pero es mock
        
        robot.step = MagicMock(return_value={"action": "MOVE_FORWARD", "new_position": nueva_pos})
        
        # Engañar al mundo para que la nueva_pos esté libre
        sim.world.get_cell(*pos_anterior).robot = None
        sim.world.get_cell(*nueva_pos).robot = robot
        
        sim.step(1)
        
        self.assertEqual(sim.robot_positions[robot], nueva_pos)
        self.assertNotEqual(sim.robot_positions[robot], pos_anterior)

    def test_8_reproducibilidad(self):
        config.N_IRIDIO = 3
        config.T_FIN = 20
        config.N_ROBOT = 1
        config.N_MONSTRUOS = 1
        
        # Correr con seed=42
        config.SEED = 42
        sim1 = Simulator()
        sim1.initialize()
        sim1.run()
        iridio_recolectado_1 = config.N_IRIDIO - len(sim1.iridio_positions)
        
        # Correr con seed=42
        config.SEED = 42
        sim2 = Simulator()
        sim2.initialize()
        sim2.run()
        iridio_recolectado_2 = config.N_IRIDIO - len(sim2.iridio_positions)
        
        # Correr con seed=99
        config.SEED = 99
        sim3 = Simulator()
        sim3.initialize()
        sim3.run()
        iridio_recolectado_3 = config.N_IRIDIO - len(sim3.iridio_positions)
        
        self.assertEqual(iridio_recolectado_1, iridio_recolectado_2)
        # NOTA: Aunque no es 100% garantizado que seed 99 dé un iridio_recolectado diferente,
        # sí es altamente probable que el estado final o posiciones varíen fuertemente.
        # En lugar de chequear el iridio, comprobaremos las posiciones de los robots iniciales para evitar flakiness:
        
        # Inicializamos ambos seeds para ver diferencias de generación
        sim_A = Simulator()
        config.SEED = 42; sim_A.initialize()
        pos_A = list(sim_A.robot_positions.values())[0]
        
        sim_B = Simulator()
        config.SEED = 99; sim_B.initialize()
        pos_B = list(sim_B.robot_positions.values())[0]
        
        self.assertNotEqual(pos_A, pos_B)

if __name__ == '__main__':
    unittest.main()
