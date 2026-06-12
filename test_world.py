import unittest
from config import CellType
from world import World

class TestWorld(unittest.TestCase):

    def test_1_dimensiones(self):
        # Crear un World(N=4, ...). Verificar que el grid tiene exactamente 4x4x4 = 64 celdas.
        w = World(N=4, P_free=0.5, P_soft=0.3, P_negro=0.2, seed=1)
        count = 0
        for x in range(4):
            for y in range(4):
                for z in range(4):
                    cell = w.get_cell(x, y, z)
                    self.assertIsNotNone(cell)
                    count += 1
        self.assertEqual(count, 64)

    def test_2_distribucion(self):
        # Crear World con P_free=0.5, P_soft=0.3, P_negro=0.2, N=5.
        w = World(N=5, P_free=0.5, P_soft=0.3, P_negro=0.2, seed=42)
        total = 5**3
        free_count = 0
        soft_count = 0
        negro_count = 0
        for x in range(5):
            for y in range(5):
                for z in range(5):
                    t = w.get_cell(x, y, z).type
                    if t == CellType.FREE:
                        free_count += 1
                    elif t == CellType.VOID:
                        soft_count += 1
                    elif t == CellType.BLACK_HOLE:
                        negro_count += 1
        
        p_free = free_count / total
        p_soft = soft_count / total
        p_negro = negro_count / total

        # Verificar que los porcentajes caen dentro de un margen +/- 5% del esperado
        self.assertTrue(abs(p_free - 0.5) <= 0.05, f"P_free = {p_free}")
        self.assertTrue(abs(p_soft - 0.3) <= 0.05, f"P_soft = {p_soft}")
        self.assertTrue(abs(p_negro - 0.2) <= 0.05, f"P_negro = {p_negro}")

    def test_3_borde_implicito(self):
        # Para un World(N=4), intentar get_neighbors(0,0,0)
        w = World(N=4, P_free=0.5, P_soft=0.3, P_negro=0.2, seed=1)
        neighbors = w.get_neighbors(0, 0, 0)
        # Verificar que ningún vecino retornado tiene coordenada negativa.
        for nx, ny, nz in neighbors:
            self.assertTrue(nx >= 0 and ny >= 0 and nz >= 0)
        
        # Intentar place_entity en (-1,0,0) -> debe lanzar excepción o retornar False.
        with self.assertRaises(ValueError):
            w.place_entity("fake_robot", "robot", -1, 0, 0)

    def test_4_adyacencia(self):
        w = World(N=5, P_free=0.5, P_soft=0.3, P_negro=0.2, seed=1)
        neighbors = w.get_neighbors(2, 2, 2)
        # Debe retornar exactamente 6 vecinos
        self.assertEqual(len(neighbors), 6)
        expected = {(3, 2, 2), (1, 2, 2), (2, 3, 2), (2, 1, 2), (2, 2, 3), (2, 2, 1)}
        self.assertEqual(set(neighbors), expected)

    def test_5_brillo(self):
        # World de puro FREE para asegurar que no hay barreras VOID/BLACK_HOLE para el brillo
        w = World(N=5, P_free=1.0, P_soft=0.0, P_negro=0.0, seed=1)
        w.place_entity("fake_iridio", "iridio", 2, 2, 2)
        w.update_iridio_glow()
        
        # Verificar que las 6 celdas adyacentes tienen brillo=True
        for nx, ny, nz in w.get_neighbors(2, 2, 2):
            self.assertTrue(w.get_cell(nx, ny, nz).brillo)
            
        # Verificar que (2,2,2) misma NO tiene brillo
        self.assertFalse(w.get_cell(2, 2, 2).brillo)
        
        # Verificar que una celda a distancia 2, como (4,2,2), NO tiene brillo
        self.assertFalse(w.get_cell(4, 2, 2).brillo)

    def test_6_olor(self):
        # Igual que Test 5 pero con un monstruo
        w = World(N=5, P_free=1.0, P_soft=0.0, P_negro=0.0, seed=1)
        w.place_entity("fake_monster", "monster", 2, 2, 2)
        w.update_monster_smell()
        
        for nx, ny, nz in w.get_neighbors(2, 2, 2):
            self.assertTrue(w.get_cell(nx, ny, nz).olor)
            
        self.assertFalse(w.get_cell(2, 2, 2).olor)
        self.assertFalse(w.get_cell(4, 2, 2).olor)

    def test_7_brillo_desaparece(self):
        w = World(N=5, P_free=1.0, P_soft=0.0, P_negro=0.0, seed=1)
        w.place_entity("fake_iridio", "iridio", 2, 2, 2)
        w.update_iridio_glow()
        
        w.remove_entity("fake_iridio", "iridio", 2, 2, 2)
        w.update_iridio_glow()
        
        # Verificar que los vecinos ya no tienen brillo=True
        for nx, ny, nz in w.get_neighbors(2, 2, 2):
            self.assertFalse(w.get_cell(nx, ny, nz).brillo)

    def test_8_reproducibilidad(self):
        # Crear World(N=5, seed=42) y guardar distribución
        w1 = World(N=5, P_free=0.5, P_soft=0.3, P_negro=0.2, seed=42)
        types_1 = [w1.get_cell(x, y, z).type for x in range(5) for y in range(5) for z in range(5)]
        
        # Crear otro con seed=42 y verificar identidad
        w2 = World(N=5, P_free=0.5, P_soft=0.3, P_negro=0.2, seed=42)
        types_2 = [w2.get_cell(x, y, z).type for x in range(5) for y in range(5) for z in range(5)]
        self.assertEqual(types_1, types_2)
        
        # Crear con seed=99 y verificar que es diferente
        w3 = World(N=5, P_free=0.5, P_soft=0.3, P_negro=0.2, seed=99)
        types_3 = [w3.get_cell(x, y, z).type for x in range(5) for y in range(5) for z in range(5)]
        self.assertNotEqual(types_1, types_3)

if __name__ == '__main__':
    unittest.main()
