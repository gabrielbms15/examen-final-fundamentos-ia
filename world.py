import random
import copy
from typing import List, Tuple, Dict, Any, Optional
import config
from config import CellType

class Cell:
    """
    Representa una celda del mundo 3D discreto.
    """
    def __init__(self, cell_type: CellType):
        self.type = cell_type
        
        # Entidades (separadas para facilitar colisiones y concurrencia)
        self.robot = None
        self.monster = None
        self.iridio = None
        
        # Señales
        self.brillo = False
        self.olor = False

    def is_free(self) -> bool:
        return self.type == CellType.FREE

    def has_entity(self) -> bool:
        return self.robot is not None or self.monster is not None or self.iridio is not None

class World:
    def __init__(self, N: int, P_free: float, P_soft: float, P_negro: float, seed: int):
        # Validar restricción de probabilidades con margen de tolerancia para floats
        if abs(P_free + P_soft + P_negro - 1.0) > 1e-6:
            raise ValueError(f"Las probabilidades deben sumar 1.0 (suma actual: {P_free + P_soft + P_negro})")
            
        self.N = N
        self.P_free = P_free
        self.P_soft = P_soft
        self.P_negro = P_negro
        self.seed = seed
        self.grid: List[List[List[Cell]]] = []
        
        random.seed(self.seed)
        
        # Total de entidades mínimas que necesitan espacio
        self.min_free_cells = config.N_ROBOT + config.N_MONSTRUOS + config.N_IRIDIO
        
        # Generar mundo hasta que sea válido
        max_attempts = 100
        for attempt in range(1, max_attempts + 1):
            self.generate_world()
            if self.validate_world():
                print(f"[World] Mundo generado exitosamente en el intento {attempt}.")
                break
        else:
            raise RuntimeError(f"No se pudo generar un mundo válido tras {max_attempts} intentos.")

    def generate_world(self):
        """Genera el grid NxNxN con la distribución probabilística dada."""
        self.grid = []
        choices = [CellType.FREE, CellType.VOID, CellType.BLACK_HOLE]
        weights = [self.P_free, self.P_soft, self.P_negro]
        
        for x in range(self.N):
            plane_x = []
            for y in range(self.N):
                row_y = []
                for z in range(self.N):
                    # Seleccionar tipo de celda según las probabilidades
                    cell_type = random.choices(choices, weights=weights, k=1)[0]
                    row_y.append(Cell(cell_type))
                plane_x.append(row_y)
            self.grid.append(plane_x)

    def validate_world(self) -> bool:
        """
        Verifica que el componente conexo más grande de celdas FREE 
        tenga al menos el tamaño mínimo para albergar a las entidades.
        """
        visited = set()
        max_component_size = 0
        
        for x in range(self.N):
            for y in range(self.N):
                for z in range(self.N):
                    if self.grid[x][y][z].is_free() and (x, y, z) not in visited:
                        # Iniciar BFS para encontrar el tamaño del componente conexo
                        component_size = self._bfs_component_size(x, y, z, visited)
                        if component_size > max_component_size:
                            max_component_size = component_size
                            
        return max_component_size >= self.min_free_cells

    def _bfs_component_size(self, start_x: int, start_y: int, start_z: int, visited: set) -> int:
        """Algoritmo BFS para encontrar el tamaño de un componente conexo."""
        queue = [(start_x, start_y, start_z)]
        visited.add((start_x, start_y, start_z))
        size = 0
        
        while queue:
            cx, cy, cz = queue.pop(0)
            size += 1
            
            for nx, ny, nz in self.get_neighbors(cx, cy, cz):
                if self.grid[nx][ny][nz].is_free() and (nx, ny, nz) not in visited:
                    visited.add((nx, ny, nz))
                    queue.append((nx, ny, nz))
        return size

    def get_neighbors(self, x: int, y: int, z: int) -> List[Tuple[int, int, int]]:
        """Retorna las coordenadas de los vecinos adyacentes (6 caras) dentro de los límites."""
        neighbors = []
        directions = [
            (1, 0, 0), (-1, 0, 0),
            (0, 1, 0), (0, -1, 0),
            (0, 0, 1), (0, 0, -1)
        ]
        
        for dx, dy, dz in directions:
            nx, ny, nz = x + dx, y + dy, z + dz
            if self.is_valid_position(nx, ny, nz):
                neighbors.append((nx, ny, nz))
                
        return neighbors

    def is_valid_position(self, x: int, y: int, z: int) -> bool:
        """Verifica si las coordenadas están dentro de los límites del cubo."""
        return 0 <= x < self.N and 0 <= y < self.N and 0 <= z < self.N

    def get_cell(self, x: int, y: int, z: int) -> Cell:
        """Retorna la celda en la posición dada."""
        if not self.is_valid_position(x, y, z):
            raise ValueError(f"Posición ({x}, {y}, {z}) fuera de los límites del mundo.")
        return self.grid[x][y][z]

    def get_free_random_position(self) -> Tuple[int, int, int]:
        """
        Retorna una posición aleatoria que sea FREE y que no tenga ninguna entidad.
        Nota: Idealmente esta posición debería pertenecer al componente conexo más grande,
        pero para simplificar, buscaremos una celda FREE vacía.
        """
        free_cells = []
        for x in range(self.N):
            for y in range(self.N):
                for z in range(self.N):
                    cell = self.grid[x][y][z]
                    if cell.is_free() and not cell.has_entity():
                        free_cells.append((x, y, z))
        
        if not free_cells:
            raise RuntimeError("No hay suficientes celdas FREE disponibles para ubicar las entidades.")
            
        return random.choice(free_cells)

    def place_entity(self, entity: Any, entity_type: str, x: int, y: int, z: int):
        """Ubica una entidad (robot, monster o iridio) en el mundo."""
        if not self.is_valid_position(x, y, z):
            raise ValueError(f"Posición ({x}, {y}, {z}) fuera de los límites.")
        cell = self.grid[x][y][z]
        if entity_type == 'robot':
            cell.robot = entity
        elif entity_type == 'monster':
            cell.monster = entity
        elif entity_type == 'iridio':
            cell.iridio = entity

    def remove_entity(self, entity: Any, entity_type: str, x: int, y: int, z: int):
        """Remueve una entidad del mundo."""
        if not self.is_valid_position(x, y, z):
            raise ValueError(f"Posición ({x}, {y}, {z}) fuera de los límites.")
        cell = self.grid[x][y][z]
        if entity_type == 'robot' and cell.robot == entity:
            cell.robot = None
        elif entity_type == 'monster' and cell.monster == entity:
            cell.monster = None
        elif entity_type == 'iridio' and cell.iridio == entity:
            cell.iridio = None

    def update_iridio_glow(self):
        """Recalcula la señal de brillo en todo el mapa basada en la posición de los bloques de iridio."""
        # Limpiar brillo existente
        for x in range(self.N):
            for y in range(self.N):
                for z in range(self.N):
                    self.grid[x][y][z].brillo = False
                    
        # Propagar nuevo brillo
        for x in range(self.N):
            for y in range(self.N):
                for z in range(self.N):
                    if self.grid[x][y][z].iridio is not None:
                        # Propagar a las 6 caras adyacentes
                        for nx, ny, nz in self.get_neighbors(x, y, z):
                            neighbor_cell = self.grid[nx][ny][nz]
                            # REQ-ENV-12: No atraviesa VOID ni BLACK_HOLE
                            if neighbor_cell.is_free():
                                neighbor_cell.brillo = True

    def update_monster_smell(self):
        """Recalcula la señal de olor en todo el mapa basada en la posición de los monstruos."""
        # Limpiar olor existente
        for x in range(self.N):
            for y in range(self.N):
                for z in range(self.N):
                    self.grid[x][y][z].olor = False
                    
        # Propagar nuevo olor
        for x in range(self.N):
            for y in range(self.N):
                for z in range(self.N):
                    if self.grid[x][y][z].monster is not None:
                        # Propagar a las 6 caras adyacentes
                        for nx, ny, nz in self.get_neighbors(x, y, z):
                            neighbor_cell = self.grid[nx][ny][nz]
                            # REQ-ENV-12: No atraviesa VOID ni BLACK_HOLE
                            if neighbor_cell.is_free():
                                neighbor_cell.olor = True

    def to_array(self) -> List[List[List[Dict[str, Any]]]]:
        """
        Exporta el estado del mundo para visualización (opcional).
        """
        # Se puede mejorar la serialización para exportar tipos más simples
        state = []
        for x in range(self.N):
            plane = []
            for y in range(self.N):
                row = []
                for z in range(self.N):
                    cell = self.grid[x][y][z]
                    row.append({
                        "type": cell.type.name,
                        "has_robot": cell.robot is not None,
                        "has_monster": cell.monster is not None,
                        "has_iridio": cell.iridio is not None,
                        "brillo": cell.brillo,
                        "olor": cell.olor
                    })
                plane.append(row)
            state.append(plane)
        return state
