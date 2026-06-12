import csv
import json
import os
from typing import List, Dict, Any, Tuple
from dataclasses import asdict

class SimLogger:
    def __init__(self):
        self.events: List[Dict[str, Any]] = []
        self._robot_memories: Dict[int, List[Dict[str, Any]]] = {}

    def log_event(self, event_type: str, t: int, **kwargs):
        event = {
            "t": t,
            "event_type": event_type
        }
        event.update(kwargs)
        self.events.append(event)

    def log_robot_move(self, robot_id: int, pos_from: Tuple[int,int,int], pos_to: Tuple[int,int,int], t: int):
        self.log_event("ROBOT_MOVE", t, robot_id=robot_id, pos_from=pos_from, pos_to=pos_to)

    def log_robot_turn(self, robot_id: int, new_dir: Tuple[int,int,int], t: int):
        self.log_event("ROBOT_TURN", t, robot_id=robot_id, new_dir=new_dir)

    def log_iridio_collected(self, pos: Tuple[int,int,int], robot_id: int, t: int):
        self.log_event("IRIDIO_COLLECTED", t, pos=pos, robot_id=robot_id)

    def log_robot_destroyed(self, robot_id: int, cause: str, t: int, robot_agent=None):
        self.log_event("ROBOT_DESTROYED", t, robot_id=robot_id, cause=cause)
        if robot_agent is not None:
            # Capturar memoria antes de que se limpie
            self._robot_memories[robot_id] = [asdict(rec) for rec in robot_agent.memory]

    def log_robot_comm(self, robot1_id: int, robot2_id: int, decision: str, t: int):
        self.log_event("ROBOT_COMM", t, robot1_id=robot1_id, robot2_id=robot2_id, decision=decision)

    def log_monster_jump(self, monster_id: int, pos_from: Tuple[int,int,int], pos_to: Tuple[int,int,int], t: int):
        self.log_event("MONSTER_JUMP", t, monster_id=monster_id, pos_from=pos_from, pos_to=pos_to)

    def log_monster_eat(self, monster_id: int, robot_id: int, t: int):
        self.log_event("MONSTER_EAT", t, monster_id=monster_id, robot_id=robot_id)

    def log_monster_fuse(self, monster1_id: int, monster2_id: int, surviving_id: int, t: int):
        self.log_event("MONSTER_FUSE", t, monster1_id=monster1_id, monster2_id=monster2_id, surviving_id=surviving_id)

    def log_iridio_appeared(self, pos: Tuple[int,int,int], t: int):
        self.log_event("IRIDIO_APPEARED", t, pos=pos)

    def log_new_rule(self, robot_id: int, rule_desc: str, t: int):
        self.log_event("NEW_RULE_GENERATED", t, robot_id=robot_id, rule_description=rule_desc)

    def log_simulation_end(self, reason: str, t: int):
        self.log_event("SIMULATION_END", t, reason=reason)

    def capture_surviving_memories(self, robots: List[Any]):
        """Llamado al final para capturar la memoria de los robots que sobrevivieron."""
        for robot in robots:
            if robot.is_alive and robot.id not in self._robot_memories:
                self._robot_memories[robot.id] = [asdict(rec) for rec in robot.memory]

    def export_to_csv(self, filepath: str):
        if not self.events:
            return
            
        with open(filepath, 'w', newline='', encoding='utf-8') as f:
            # Obtener todas las keys posibles de todos los eventos
            fieldnames = set()
            for event in self.events:
                fieldnames.update(event.keys())
                
            # Ordenar para que t y event_type estén primero
            ordered_fields = ['t', 'event_type'] + sorted([k for k in fieldnames if k not in ['t', 'event_type']])
            
            writer = csv.DictWriter(f, fieldnames=ordered_fields)
            writer.writeheader()
            
            for event in self.events:
                # Convertir tuplas y dicts a strings para el CSV
                clean_event = {k: (str(v) if isinstance(v, (tuple, dict, list)) else v) for k, v in event.items()}
                writer.writerow(clean_event)

    def export_to_json(self, filepath: str):
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(self.events, f, indent=2)

    def export_robot_memories(self, out_dir: str):
        os.makedirs(out_dir, exist_ok=True)
        for robot_id, memory in self._robot_memories.items():
            filepath = os.path.join(out_dir, f"memory_robot_{robot_id}.json")
            # Convertir enums y tuplas a primitivas JSON friendly (dataclass.asdict ya los extrae, pero Enum necesita limpieza)
            clean_memory = []
            for rec in memory:
                c_rec = dict(rec)
                # Parsear accion que es un Enum
                if 'accion' in c_rec and hasattr(c_rec['accion'], 'value'):
                    c_rec['accion'] = c_rec['accion'].value
                clean_memory.append(c_rec)
                
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(clean_memory, f, indent=2)
