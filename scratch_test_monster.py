from world import World
from monster_agent import MonsterAgent
from config import CellType

world = World(N=5, P_free=1.0, P_soft=0.0, P_negro=0.0, seed=1)

m1 = MonsterAgent(monster_id=1)
m1.robots_eaten = 3
m2 = MonsterAgent(monster_id=2)
m2.robots_eaten = 2

world.place_entity(m1, "monster", 1, 1, 1)
world.place_entity(m2, "monster", 2, 1, 1)

for nx,ny,nz in world.get_neighbors(1,1,1):
    if (nx,ny,nz) != (2,1,1):
        world.get_cell(nx,ny,nz).type = CellType.VOID

result = m1.step(world, position=(1,1,1))

print(f"M1 vivo: {m1.is_alive}")
print(f"M2 robots_eaten: {m2.robots_eaten}")
print(f"Acción: {result['action']}")
if 'surviving_monster' in result:
    print(f"Sobreviviente: Monster {result['surviving_monster'].id}")
else:
    print("No hubo fusión")
