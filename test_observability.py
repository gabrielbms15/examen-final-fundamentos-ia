import unittest
import os
import csv
from unittest.mock import MagicMock

import config
from logger import SimLogger
from metrics import MetricsCollector
from robot_agent import RobotAgent, Perception, MemoryRecord
from config import Action

class TestObservability(unittest.TestCase):

    # =========================================================================
    # TESTS PARA LOGGER
    # =========================================================================

    def test_1_logger_registra_evento(self):
        logger = SimLogger()
        logger.log_robot_destroyed(robot_id=42, cause="BLACK_HOLE", t=10)
        
        self.assertEqual(len(logger.events), 1)
        event = logger.events[0]
        self.assertEqual(event["t"], 10)
        self.assertEqual(event["robot_id"], 42)
        self.assertEqual(event["cause"], "BLACK_HOLE")
        self.assertEqual(event["event_type"], "ROBOT_DESTROYED")

    def test_2_logger_exporta_csv(self):
        logger = SimLogger()
        logger.log_robot_move(1, (0,0,0), (1,0,0), 0)
        logger.log_iridio_collected((1,0,0), 1, 1)
        
        filepath = "test_log.csv"
        logger.export_to_csv(filepath)
        
        self.assertTrue(os.path.exists(filepath))
        with open(filepath, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
            self.assertEqual(len(rows), 2)
            self.assertIn("t", reader.fieldnames)
            self.assertIn("event_type", reader.fieldnames)
            self.assertEqual(rows[0]["event_type"], "ROBOT_MOVE")
            self.assertEqual(rows[1]["event_type"], "IRIDIO_COLLECTED")
            
        os.remove(filepath)

    def test_3_logger_captura_memoria_antes_de_limpiar(self):
        logger = SimLogger()
        robot = RobotAgent(1, (1,0,0))
        
        p_dummy = Perception(False, False, False, False, (0,0,0), (1,0,0), False, False)
        robot.update_memory(0, p_dummy, Action.MOVE_FORWARD, "MOVE_FORWARD")
        
        # El logger debe capturar la memoria de 1 registro
        logger.log_robot_destroyed(1, "MONSTER", 1, robot_agent=robot)
        
        # Luego el simulador limpia la memoria del robot real
        robot.memory.clear()
        
        # La memoria capturada por el logger debe permanecer intacta
        memoria_capturada = logger._robot_memories[1]
        self.assertEqual(len(memoria_capturada), 1)
        self.assertEqual(len(robot.memory), 0)

    # =========================================================================
    # TESTS PARA METRICS
    # =========================================================================

    def test_4_metrics_history(self):
        metrics = MetricsCollector()
        world = MagicMock()
        world.N = 3
        # Dummy world que tiene 0 iridio
        world.grid = [[[MagicMock(iridio=None, is_free=lambda: True) for _ in range(3)] for _ in range(3)] for _ in range(3)]
        
        robot_mock = MagicMock(id=1, iridio_count=0, memory=[], rules=[])
        monster_mock = MagicMock(id=1)
        
        for t in range(3):
            metrics.record(t, world, [robot_mock], [monster_mock])
            
        self.assertEqual(len(metrics.history), 3)
        for i in range(3):
            snap = metrics.history[i]
            self.assertEqual(snap["t"], i)
            self.assertEqual(snap["robots_vivos"], 1)
            self.assertEqual(snap["monstruos_vivos"], 1)
            self.assertEqual(snap["iridio_restante"], 0)

    def test_5_metrics_robot_score(self):
        metrics = MetricsCollector()
        # Modificar pesos temporalmente para el test
        config.W1_IRIDIO = 10
        config.W2_DEATH = 50
        config.W3_LOOP = 20
        config.W4_SURVIVE = 5
        config.W5_IDLE = 1
        config.T_FIN = 100
        
        robot = MagicMock()
        robot.id = 1
        robot.is_alive = True
        robot.iridio_count = 2   # 2 * 10 = 20
        robot.step_count = 50    # 50/100 * 5 = 2.5
        # Muertes: 0 * 50 = 0
        # Bucles: 0 * 20 = 0
        
        metrics._pasos_sin_avance[1] = 3  # 3 * 1 = 3
        
        # Total esperado: 20 - 0 - 0 + 2.5 - 3 = 19.5
        score = metrics.compute_robot_score(robot)
        self.assertAlmostEqual(score, 19.5)

    def test_6_metrics_summary(self):
        metrics = MetricsCollector()
        world = MagicMock()
        world.N = 2
        world.grid = [[[MagicMock(is_free=lambda: True) for _ in range(2)] for _ in range(2)] for _ in range(2)]
        
        robot = MagicMock(id=1, is_alive=True, iridio_count=0, step_count=10, death_cause=None, rules=[])
        monster = MagicMock(id=1, robots_eaten=1, jumps_count=5)
        
        metrics._all_robots[1] = robot
        config.N_IRIDIO = 5
        
        summary = metrics.generate_summary(world=world, monsters=[monster])
        
        self.assertIn("global_score", summary)
        self.assertIn("survival_rate", summary)
        self.assertIn("collection_efficiency", summary)
        self.assertIn("exploration_efficiency", summary)
        self.assertIn("monster_scores", summary)
        
        # Verificar cálculos básicos (ER = 0/5 = 0, Monster score = 1*100 + 5 = 105)
        self.assertEqual(summary["collection_efficiency"], 0.0)
        self.assertEqual(summary["monster_scores"][1], 105.0)

if __name__ == '__main__':
    unittest.main()
