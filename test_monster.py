import unittest
from config import CellType, DeathCause
from world import World, Cell
from monster_agent import MonsterAgent


# =============================================================================
# MOCKS
# =============================================================================

class FakeRobot:
    """Mock mínimo de RobotAgent para los tests del monstruo."""
    def __init__(self, robot_id: int = 0):
        self.id = robot_id
        self.is_alive = True
        self.death_cause = None


class FakeIridio:
    """Mock de bloque de iridio (cualquier objeto no-None sirve)."""
    pass


# =============================================================================
# HELPERS
# =============================================================================

def make_all_free_world(n: int, seed: int = 1) -> World:
    """Crea un mundo 100% FREE (útil para tests donde no deben haber barreras)."""
    return World(N=n, P_free=1.0, P_soft=0.0, P_negro=0.0, seed=seed)


# =============================================================================
# TESTS
# =============================================================================

class TestMonsterAgent(unittest.TestCase):

    # -------------------------------------------------------------------------
    # Test 1 — RoboKiller activa cuando hay robot en la misma celda
    # -------------------------------------------------------------------------
    def test_1_robokiller(self):
        w = make_all_free_world(n=5)
        robot = FakeRobot(robot_id=1)
        monster = MonsterAgent(monster_id=1)

        w.place_entity(robot,   "robot",   2, 2, 2)
        w.place_entity(monster, "monster", 2, 2, 2)

        result = monster.step(w, position=(2, 2, 2))

        # El robot debe estar muerto
        self.assertFalse(robot.is_alive)
        self.assertEqual(robot.death_cause, DeathCause.KILLED_BY_MONSTER)
        # El monstruo debe haber incrementado su contador
        self.assertEqual(monster.robots_eaten, 1)
        # El robot ya no debe estar en esa celda
        self.assertIsNone(w.get_cell(2, 2, 2).robot)

    # -------------------------------------------------------------------------
    # Test 2 — RoboJumper no salta a celda con iridio
    # -------------------------------------------------------------------------
    def test_2_robojumper_evita_iridio(self):
        # 3x3x3 FREE. Monstruo en (1,1,1). Los 6 vecinos son:
        #   (0,1,1),(2,1,1),(1,0,1),(1,2,1),(1,1,0),(1,1,2)
        # Colocamos iridio en 5 de ellos; el único libre es (2,1,1).
        w = make_all_free_world(n=3)
        monster = MonsterAgent(monster_id=1)
        start = (1, 1, 1)
        safe_cell = (2, 1, 1)
        
        iridio_cells = [(0, 1, 1), (1, 0, 1), (1, 2, 1), (1, 1, 0), (1, 1, 2)]
        w.place_entity(monster, "monster", *start)
        for pos in iridio_cells:
            w.place_entity(FakeIridio(), "iridio", *pos)

        result = monster.step(w, position=start)

        # El monstruo DEBE haber saltado a la única celda sin iridio
        self.assertEqual(result["new_position"], safe_cell)
        self.assertIsNotNone(w.get_cell(*safe_cell).monster)
        # Ya no debe estar en la celda original
        self.assertIsNone(w.get_cell(*start).monster)

    # -------------------------------------------------------------------------
    # Test 3 — RoboJumper no mueve si no hay celdas válidas
    # -------------------------------------------------------------------------
    def test_3_robojumper_sin_celdas_validas(self):
        # Creamos un mundo FREE y luego convertimos todos los vecinos de (1,1,1)
        # a VOID manualmente para simular el monstruo atrapado.
        w = make_all_free_world(n=3)
        monster = MonsterAgent(monster_id=1)
        start = (1, 1, 1)
        w.place_entity(monster, "monster", *start)

        # Bloquear todos los vecinos cambiando su tipo a VOID
        for nx, ny, nz in w.get_neighbors(*start):
            w.get_cell(nx, ny, nz).type = CellType.VOID

        # No debe lanzar excepción
        try:
            result = monster.step(w, position=start)
        except Exception as e:
            self.fail(f"step() lanzó una excepción inesperada: {e}")

        # El monstruo debe seguir en la misma posición
        self.assertEqual(result["new_position"], start)
        self.assertIsNotNone(w.get_cell(*start).monster)

    # -------------------------------------------------------------------------
    # Test 4 — Fusión de monstruos
    # -------------------------------------------------------------------------
    def test_4_fusion(self):
        # M1 está en (1,1,1), M2 en (2,1,1) — vecinos directos.
        # M1 debe saltar y encontrarse con M2, provocando la fusión.
        # M2 (destino) sobrevive con los contadores sumados.
        w = make_all_free_world(n=5)

        m1 = MonsterAgent(monster_id=1)
        m1.robots_eaten = 3

        m2 = MonsterAgent(monster_id=2)
        m2.robots_eaten = 2

        pos_m1 = (1, 1, 1)
        pos_m2 = (2, 1, 1)

        w.place_entity(m1, "monster", *pos_m1)
        w.place_entity(m2, "monster", *pos_m2)

        # Bloquear todos los vecinos de M1 excepto pos_m2, para forzar el salto hacia M2.
        for nx, ny, nz in w.get_neighbors(*pos_m1):
            if (nx, ny, nz) != pos_m2:
                w.get_cell(nx, ny, nz).type = CellType.VOID

        result = m1.step(w, position=pos_m1)

        # M1 fue absorbido → debe estar muerto
        self.assertFalse(m1.is_alive)

        # M2 sobrevive con los contadores sumados: 2 + 3 = 5
        self.assertEqual(m2.robots_eaten, 5)
        self.assertTrue(m2.is_alive)

        # El sobreviviente reportado en el resultado es M2
        self.assertIs(result["surviving_monster"], m2)

        # M1 ya no debe estar en el grid en pos_m1
        self.assertIsNone(w.get_cell(*pos_m1).monster)

    # -------------------------------------------------------------------------
    # Test 5 — step() no contiene ningún chequeo de tiempo interno
    # -------------------------------------------------------------------------
    def test_5_sin_reloj_interno(self):
        """
        Verifica que step() ejecuta la lógica completa sin depender de
        ningún parámetro de tiempo global. Al llamarlo directamente sin
        ningún 't', debe funcionar igual que si el Simulator lo llamara.
        """
        import inspect
        source = inspect.getsource(MonsterAgent.step)
        
        # Ninguna referencia a "% 4" o "T_" dentro del propio step()
        self.assertNotIn("% 4", source,
            "step() no debe contener lógica de frecuencia 1/4 — eso es del Simulator")
        self.assertNotIn("t_fin", source.lower(),
            "step() no debe referenciar T_FIN")

        # Verificar que step() se puede llamar y retorna un dict con las claves esperadas
        w = make_all_free_world(n=3)
        monster = MonsterAgent(monster_id=99)
        w.place_entity(monster, "monster", 1, 1, 1)

        result = monster.step(w, position=(1, 1, 1))

        self.assertIn("action", result)
        self.assertIn("surviving_monster", result)
        self.assertIn("new_position", result)


if __name__ == "__main__":
    unittest.main()
