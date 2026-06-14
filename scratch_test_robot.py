import json
from world import World
from robot_agent import RobotAgent, Perception
from config import CellType, Action, DeathCause

print("--- DEMO A ---")
world = World(N=5, P_free=1.0, P_soft=0.0, P_negro=0.0, seed=1)
world.get_cell(3,2,2).type = CellType.VOID

robot = RobotAgent(robot_id=1, initial_dir=(1,0,0))
world.place_entity(robot, "robot", 2, 2, 2)

p1 = robot.perceive(world, (2,2,2))
print(f"Antes de mover -> vacuscopio: {p1.vacuscopio}")

result = robot.act(Action.MOVE_FORWARD, world, (2,2,2), 0)
print(f"Resultado del movimiento: {result['action']}, razón: {result.get('reason', '')}")

p2 = robot.perceive(world, (2,2,2))
print(f"Después de BLOCKED -> vacuscopio: {p2.vacuscopio}")

print("\n--- DEMO B ---")
robot = RobotAgent(robot_id=1, initial_dir=(1,0,0))
reglas_antes = len(robot.rules)

p_peligro = Perception(olor=True, brillo=False, iridio_aqui=False,
                       robot_delante=False, posicion=(1,1,1),
                       direccion=(1,0,0), vacuscopio=False, bucle=False)
robot.update_memory(0, p_peligro, Action.MOVE_FORWARD, "MOVE_FORWARD")
robot.update_memory(1, p_peligro, Action.WAIT, "DEAD")
robot.is_alive = False
robot.death_cause = DeathCause.KILLED_BY_MONSTER

robot.generate_new_rules()
print(f"Reglas antes: {reglas_antes}")
print(f"Reglas después: {len(robot.rules)}")
print(f"Nueva regla: '{robot.rules[0].descripcion}'")

print("\n--- DEMO C ---")
with open("results/robot_memories/memory_robot_1.json") as f:
    memory = json.load(f)

from collections import Counter
acciones = Counter(r['accion'] for r in memory)
print(f"Distribución de acciones: {dict(acciones)}")
