import unittest
from typing import Tuple

import config
from config import CellType, Action, DeathCause, TURN_TABLE
from world import World
from robot_agent import RobotAgent, Perception, MemoryRecord, Rule

class FakeIridio:
    pass

class FakeMonster:
    pass

def make_all_free_world(n: int, seed: int = 1) -> World:
    return World(N=n, P_free=1.0, P_soft=0.0, P_negro=0.0, seed=seed)

class TestRobotAgent(unittest.TestCase):

    def test_1_percepcion_senales(self):
        w = make_all_free_world(5)
        # Colocar iridio en (3,2,2)
        w.place_entity(FakeIridio(), "iridio", 3, 2, 2)
        w.update_iridio_glow()
        
        # Robot en (2,2,2) mirando hacia +X (1,0,0)
        robot = RobotAgent(robot_id=1, initial_dir=(1, 0, 0))
        w.place_entity(robot, "robot", 2, 2, 2)
        
        # percibir en (2,2,2)
        p1 = robot.perceive(w, (2, 2, 2))
        self.assertTrue(p1.brillo)
        self.assertFalse(p1.olor)
        self.assertFalse(p1.iridio_aqui)
        
        # mover a (3,2,2)
        w.remove_entity(robot, "robot", 2, 2, 2)
        w.place_entity(robot, "robot", 3, 2, 2)
        
        # percibir en (3,2,2)
        p2 = robot.perceive(w, (3, 2, 2))
        self.assertTrue(p2.iridio_aqui)

    def test_2_vacuscopio_reactivo(self):
        w = make_all_free_world(5)
        w.get_cell(3, 2, 2).type = CellType.VOID
        
        robot = RobotAgent(robot_id=1, initial_dir=(1, 0, 0))
        w.place_entity(robot, "robot", 2, 2, 2)
        
        # Antes de mover, vacuscopio debe ser False
        p1 = robot.perceive(w, (2, 2, 2))
        self.assertFalse(p1.vacuscopio)
        
        # Intentar mover hacia VOID
        result = robot.act(Action.MOVE_FORWARD, w, (2, 2, 2), 0)
        self.assertEqual(result["action"], "BLOCKED")
        self.assertEqual(result["reason"], "VOID")
        
        # Percepción siguiente, vacuscopio debe ser True
        p2 = robot.perceive(w, (2, 2, 2))
        self.assertTrue(p2.vacuscopio)

    def test_3_suck_iridio(self):
        w = make_all_free_world(3)
        iridio = FakeIridio()
        w.place_entity(iridio, "iridio", 1, 1, 1)
        
        robot = RobotAgent(robot_id=1, initial_dir=(1, 0, 0))
        w.place_entity(robot, "robot", 1, 1, 1)
        
        p = robot.perceive(w, (1, 1, 1))
        self.assertTrue(p.iridio_aqui)
        
        action = robot.decide(p)
        self.assertEqual(action, Action.SUCK_IRIDIO)
        
        # act(SUCK_IRIDIO)
        robot.act(Action.SUCK_IRIDIO, w, (1, 1, 1), 0)
        self.assertEqual(robot.iridio_count, 1)
        self.assertIsNone(w.get_cell(1, 1, 1).iridio)

    def test_4_black_hole(self):
        w = make_all_free_world(4)
        w.get_cell(3, 2, 2).type = CellType.BLACK_HOLE
        
        robot = RobotAgent(robot_id=1, initial_dir=(1, 0, 0))
        w.place_entity(robot, "robot", 2, 2, 2)
        
        result = robot.act(Action.MOVE_FORWARD, w, (2, 2, 2), 0)
        self.assertEqual(result["action"], "SHUTDOWN")
        self.assertEqual(result["reason"], "BLACK_HOLE")
        
        self.assertFalse(robot.is_alive)
        self.assertEqual(robot.death_cause, DeathCause.KILLED_BY_BLACK_HOLE)
        # El robot desapareció del mundo
        self.assertIsNone(w.get_cell(2, 2, 2).robot)

    def test_5_infinitometro(self):
        robot = RobotAgent(robot_id=1, initial_dir=(1, 0, 0))
        
        # Inyectar memoria con un patrón repetido.
        # Por defecto LOOP_WINDOW = 30, LOOP_MIN_LEN = 4, LOOP_THRESHOLD = 2
        # Vamos a inyectar una secuencia 8 veces: (1,1,1) -> (2,1,1) -> (2,2,1) -> (1,2,1)
        # Longitud 4 repetida, cumple con que la subcadena de longitud 4 se repite > 2 veces
        
        patron = [(1, 1, 1), (2, 1, 1), (2, 2, 1), (1, 2, 1)]
        
        # Inyectar 32 registros (mayor a LOOP_WINDOW que es 30)
        for i in range(32):
            pos = patron[i % 4]
            # crear un perception dummy
            p_dummy = Perception(False, False, False, False, pos, (1,0,0), False, False)
            robot.update_memory(t=i, perception=p_dummy, action=Action.MOVE_FORWARD, result="MOVE_FORWARD")
            
        # Llamar directamente a _sense_infinitometro()
        self.assertTrue(robot._sense_infinitometro())

    def test_6_roboturner(self):
        robot = RobotAgent(robot_id=1, initial_dir=(1, 0, 0))
        w = make_all_free_world(3)
        w.place_entity(robot, "robot", 1, 1, 1)
        
        result = robot.act(Action.TURN_0, w, (1, 1, 1), 0)
        self.assertEqual(result["action"], "TURN_0")
        
        nueva_dir = robot.direction
        # Verificar que nueva_dir es una de las 4 perpendiculares
        opciones_validas = TURN_TABLE[(1, 0, 0)]
        self.assertIn(nueva_dir, opciones_validas)
        # Verificar que cambió
        self.assertNotEqual(nueva_dir, (1, 0, 0))

    def test_7_memoria_se_actualiza(self):
        w = make_all_free_world(5)
        robot = RobotAgent(robot_id=1, initial_dir=(1, 0, 0))
        w.place_entity(robot, "robot", 1, 1, 1)
        
        # step() 3 veces
        pos = (1, 1, 1)
        for t in range(3):
            robot.step(w, pos, t)
            # asumiendo que avanzó
            if robot.direction == (1, 0, 0):
                pos = (pos[0]+1, pos[1], pos[2])
                
        self.assertEqual(len(robot.memory), 3)
        for i in range(3):
            rec = robot.memory[i]
            self.assertEqual(rec.t, i)
            self.assertIsInstance(rec.percepcion, Perception)
            self.assertIsInstance(rec.accion, Action)
            self.assertIsInstance(rec.posicion, tuple)
            self.assertIsInstance(rec.resultado, str)

    def test_8_generate_new_rules(self):
        robot = RobotAgent(robot_id=1, initial_dir=(1, 0, 0))
        reglas_iniciales = len(robot.rules)
        self.assertEqual(reglas_iniciales, 0)
        
        # Inyectar en memoria el patrón de olor (patrón 1)
        p_t0 = Perception(olor=True, brillo=False, iridio_aqui=False, robot_delante=False,
                          posicion=(1,1,1), direccion=(1,0,0), vacuscopio=False, bucle=False)
        robot.update_memory(0, p_t0, Action.MOVE_FORWARD, "MOVE_FORWARD")
        
        p_t1 = Perception(olor=False, brillo=False, iridio_aqui=False, robot_delante=False,
                          posicion=(2,1,1), direccion=(1,0,0), vacuscopio=False, bucle=False)
        robot.update_memory(1, p_t1, Action.WAIT, "DEAD")
        
        robot.is_alive = False
        robot.death_cause = DeathCause.KILLED_BY_MONSTER
        
        robot.generate_new_rules()
        
        self.assertGreater(len(robot.rules), reglas_iniciales)
        self.assertEqual(robot.rules[0].descripcion, "Penalizar avance tras olor")

    def test_9_memoria_no_compartida(self):
        w = make_all_free_world(5)
        robot_A = RobotAgent(robot_id=1, initial_dir=(1, 0, 0))
        robot_B = RobotAgent(robot_id=2, initial_dir=(0, 1, 0))
        
        w.place_entity(robot_A, "robot", 1, 1, 1)
        w.place_entity(robot_B, "robot", 3, 3, 3)
        
        pos_A = (1, 1, 1)
        for t in range(5):
            # Forzamos que siempre gire para que no se salga de los límites
            robot_A.rules = []
            def cond_always_turn(p, a): return a == Action.TURN_0
            robot_A.rules.append(Rule(cond_always_turn, "Siempre girar", 1000.0))
            
            robot_A.step(w, pos_A, t)
            
        self.assertEqual(len(robot_A.memory), 5)
        self.assertEqual(len(robot_B.memory), 0)

if __name__ == '__main__':
    unittest.main()
