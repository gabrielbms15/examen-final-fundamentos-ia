from enum import Enum

# =============================================================================
# CONSTANTES GLOBALES DE LA SIMULACIÓN
# =============================================================================
N = 5
P_FREE = 0.7
P_SOFT = 0.2
P_NEGRO = 0.1

N_ROBOT = 2
N_MONSTRUOS = 2
N_IRIDIO = 5

T_INICIO = 0
T_FIN = 1000
SEED = 42

# =============================================================================
# PESOS DE LA FUNCIÓN DE UTILIDAD DEL ROBOT
# =============================================================================
W1_IRIDIO = 10
W2_DEATH = 50
W3_LOOP = 20
W4_SURVIVE = 5
W5_IDLE = 1.2

# =============================================================================
# PARÁMETROS DEL INFINITÓMETRO
# =============================================================================
LOOP_WINDOW = 30
LOOP_MIN_LEN = 4
LOOP_THRESHOLD = 2

# =============================================================================
# PARÁMETROS DE VISUALIZACIÓN
# =============================================================================
CELL_SIZE = 1
FPS = 10
EXPORT_FRAMES = False

# =============================================================================
# ENUMERADORES
# =============================================================================
class CellType(Enum):
    FREE = 0
    VOID = 1
    BLACK_HOLE = 2

class Action(Enum):
    MOVE_FORWARD = "MOVE_FORWARD"
    TURN_0 = "TURN_0"
    TURN_1 = "TURN_1"
    TURN_2 = "TURN_2"
    TURN_3 = "TURN_3"
    SHUTDOWN = "SHUTDOWN"
    COMMUNICATE = "COMMUNICATE"
    SUCK_IRIDIO = "SUCK_IRIDIO"
    WAIT = "WAIT"

class DeathCause(Enum):
    KILLED_BY_MONSTER = "MONSTER"
    KILLED_BY_BLACK_HOLE = "BLACK_HOLE"
    KILLED_BY_LOOP = "LOOP"

# =============================================================================
# ORIENTACIÓN DISCRETA (Reemplaza a orientation.py)
# =============================================================================

# Los 6 vectores de dirección posibles en el grid 3D discreto
DIRECTIONS = [
    (1, 0, 0), (-1, 0, 0),
    (0, 1, 0), (0, -1, 0),
    (0, 0, 1), (0, 0, -1)
]

# TURN_TABLE[direccion_actual][lado 0..3] → nueva dirección tras girar 90°
TURN_TABLE = {
    ( 1, 0, 0): [(0, 1, 0), (0, -1, 0), (0, 0, 1), (0, 0, -1)],
    (-1, 0, 0): [(0, 1, 0), (0, -1, 0), (0, 0, -1), (0, 0, 1)],
    ( 0, 1, 0): [(-1, 0, 0), ( 1, 0, 0), (0, 0, 1), (0, 0, -1)],
    ( 0,-1, 0): [( 1, 0, 0), (-1, 0, 0), (0, 0, -1), (0, 0, 1)],
    ( 0, 0, 1): [( 1, 0, 0), (-1, 0, 0), (0, 1, 0), (0, -1, 0)],
    ( 0, 0,-1): [(-1, 0, 0), ( 1, 0, 0), (0, 1, 0), (0, -1, 0)],
}

def turn(current_direction: tuple, side: int) -> tuple:
    """
    Gira 90° hacia el costado indicado (0–3).
    Sin quaterniones, sin matrices.
    """
    return TURN_TABLE[current_direction][side]
