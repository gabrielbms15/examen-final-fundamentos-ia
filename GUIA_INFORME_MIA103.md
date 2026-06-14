# GUÍA DEL INFORME FINAL — MIA-103
## Qué escribir, qué correr y qué variar en cada sección

> **Cómo usar esta guía:**
> Cada sección del informe tiene tres bloques:
> - **QUÉ ESCRIBIR** → contenido narrativo esperado
> - **QUÉ CORRER** → código exacto o función a ejecutar
> - **QUÉ VARIAR** → parámetros y por qué son interesantes para el profesor

---

## ESTRUCTURA GENERAL DEL INFORME

```
1.  Portada
2.  Resumen y Palabras Clave
3.  Introducción
4.  Ontología
5.  Planteamiento del Problema
6.  Metodología
7.  Diseño de los Agentes
8.  Construcción de los Agentes
9.  Análisis de Resultados
10. Conclusiones
11. Recomendaciones
12. Referencias Bibliográficas
```

---

## SECCIÓN 1 — PORTADA

**QUÉ ESCRIBIR:**
- Título: "Diseño y construcción de agentes inteligentes en un entorno 3D discreto multiagente"
- Autores, emails, universidad, curso MIA-103
- Fecha: junio 2026

**QUÉ CORRER:** Nada.

**QUÉ VARIAR:** Nada.

---

## SECCIÓN 2 — RESUMEN Y PALABRAS CLAVE

**QUÉ ESCRIBIR:**
Párrafo de 150-200 palabras que mencione:
- El tipo de entorno (N³ discreto, sin gravedad, 3 tipos de celda)
- Los dos agentes (Robot basado en utilidad con memoria, Monstruo reflejo simple)
- El resultado principal (iridio recolectado, supervivencia, detección de bucles)
- Una métrica concreta del mejor experimento

**Palabras clave:** agente basado en utilidad, agente reflejo simple, entorno 3D discreto, memoria interna, función de utilidad, multiagente, simulación.

**QUÉ CORRER:**
```python
# Correr UNA simulación estándar y anotar los números para el resumen
from simulator import Simulator
import config

config.N = 5
config.N_ROBOT = 2
config.N_MONSTRUOS = 2
config.N_IRIDIO = 5
config.T_FIN = 100
config.SEED = 42

sim = Simulator()
sim.initialize()
sim.run()
summary = sim.metrics.generate_summary()
print(summary)
```

**QUÉ VARIAR:** Nada en esta sección. Los números que salen de la corrida estándar se usan en el resumen.

---

## SECCIÓN 3 — INTRODUCCIÓN

**QUÉ ESCRIBIR:**
Tres subsecciones:

**3.1 Antecedentes:**
Describir brevemente qué es un agente inteligente (citar Russell & Norvig AIMA),
qué es un agente basado en utilidad vs reflejo simple, y por qué el entorno 3D
discreto es un caso de estudio relevante.

**3.2 Descripción del Problema:**
El entorno, las entidades, el objetivo del robot (maximizar iridio) y el objetivo
del monstruo (maximizar robots comidos). Mencionar las restricciones principales
(sin gravedad, 6-adyacencia, velocidades distintas).

**3.3 Resultados Esperados:**
- El robot debe recolectar más iridio con el tiempo (curva de aprendizaje creciente)
- El Infinitómetro debe detectar bucles antes de T=35
- El sistema debe ser reproducible con la misma semilla

**QUÉ CORRER:** Nada nuevo. Usar el summary de la sección 2.

**QUÉ VARIAR:** Nada.

---

## SECCIÓN 4 — ONTOLOGÍA

**QUÉ ESCRIBIR:**

**4.1 Lista de conceptos ontológicos identificados en el enunciado:**

| Concepto | Definición Ontológica |
|---|---|
| Entorno | Cubo N×N×N de celdas discretas sin gravedad |
| Celda | Unidad mínima del espacio, tipo exclusivo (FREE/VOID/BLACK_HOLE) |
| ZonaLibre | Celda traversable que puede contener entidades |
| ZonaVacía | Celda impenetrable, bloquea movimiento y propagación |
| AgujerosNegro | Celda donde el tiempo no existe, trampa permanente |
| Robot | Agente con memoria, basado en utilidad, Iridiófilo |
| Monstruo | Agente reflejo simple, Robófago, sin memoria |
| Iridio | Objeto pasivo recolectable, emite brillo a 6 vecinos |
| Tiempo | Contador discreto T que sincroniza agentes |
| Sensor | Mecanismo de percepción del agente |
| Efector | Mecanismo de acción del agente |
| Memoria | Tabla histórica de percepciones-acciones del robot |
| RegladeDecisión | Par condición→acción con peso de utilidad |
| FuncióndeUtilidad | Función que puntúa acciones candidatas dado el contexto |

**4.2 Conceptos NO presentados en el enunciado pero identificados:**

| Concepto Emergente | Justificación |
|---|---|
| PropagacióndeSeñal | El brillo y olor se propagan pero no atraviesan VOID |
| Fenotipo del Robot | Cada instancia tiene memoria y reglas propias aunque comparten genotipo |
| FusióndesMonstruos | Propiedad emergente del RoboJumper cuando dos monstruos coinciden |
| BucleInfinito | Patrón de posiciones repetidas detectado por el Infinitómetro |
| ZonaDeExclusión | Región evitada por el robot tras aprender presencia de monstruo |

**4.3 Diagrama de ontología:**
Presentar el diagrama generado en Protegé o equivalente.

**QUÉ CORRER:**
```python
# Imprimir la jerarquía de clases del sistema para apoyar el diagrama
from ontology import Entity, Agent, Robot, Monster, Iridio, World
import inspect

for cls in [Entity, Agent, Robot, Monster, Iridio, World]:
    print(f"{cls.__name__} → bases: {[b.__name__ for b in cls.__bases__]}")
    print(f"  Atributos: {[a for a in vars(cls) if not a.startswith('_')]}")
```

**QUÉ VARIAR:** Nada. La ontología es fija.

---

## SECCIÓN 5 — PLANTEAMIENTO DEL PROBLEMA

**QUÉ ESCRIBIR:**

> "En un espacio tridimensional discreto compuesto por N³ celdas de tres tipos
> (libres, vacías y agujeros negros), múltiples instancias de un agente Robot
> deben maximizar la recolección de bloques de Iridio mientras evitan ser
> destruidos por instancias de un agente Monstruo y por los peligros del entorno,
> sin incurrir en bucles de comportamiento que comprometan su operación.
> Los agentes operan con información parcial del entorno, percibida exclusivamente
> a través de sensores limitados, y deben tomar decisiones racionales basadas en
> su historial de percepciones y acciones."

**Clasificación del ambiente (tabla AIMA) — OBLIGATORIA:**

| Propiedad | Robot | Monstruo | Justificación |
|---|---|---|---|
| Accesible | No | No | Sensores limitados, sin mapa global |
| Determinista | No | No | Monstruos y otros robots introducen incertidumbre |
| Episódico | No | Sí | Robot acumula memoria; monstruo no recuerda nada |
| Estático | No | No | Monstruos se mueven, iridio desaparece |
| Discreto | Sí | Sí | Grid entero, tiempo discreto |

**QUÉ CORRER:** Nada nuevo.

**QUÉ VARIAR:** Nada.

---

## SECCIÓN 6 — METODOLOGÍA

**QUÉ ESCRIBIR:**
Describir el pipeline de desarrollo en este orden exacto:

```
1. config.py    → parámetros y constantes centralizados
2. world.py     → entorno 3D con generación aleatoria y propagación de señales
3. monster_agent.py → agente reflejo simple (base del sistema multiagente)
4. robot_agent.py   → agente con memoria y utilidad (núcleo del problema)
5. simulator.py     → orquestador del ciclo percepción→decisión→acción
6. metrics.py       → métricas de racionalidad y eficiencia
7. logger.py        → registro cronológico de eventos
8. experiments.py   → experimentos batch parametrizados
9. visualizer.py    → representación gráfica del estado y los resultados
```

Mencionar que cada módulo fue verificado con tests unitarios antes de avanzar al siguiente (desarrollo incremental verificado).

**QUÉ CORRER:** Nada. Esta sección describe el método, no los resultados.

**QUÉ VARIAR:** Nada.

---

## SECCIÓN 7 — DISEÑO DE LOS AGENTES

### 7.1 Entidades operativas en el entorno

**QUÉ ESCRIBIR:**
- Robot (agente), Monstruo (agente), Iridio (objeto pasivo), Celda (estructura del entorno)
- Aclarar: el Entorno NO es una entidad — es el medio donde operan las entidades

### 7.2 Descripción de los agentes (genotipo y fenotipo)

**QUÉ ESCRIBIR:**

**Robot — Genotipo (código compartido):**
- 9 sensores, 4 efectores, función de utilidad, generador de reglas

**Robot — Fenotipo (instancia específica):**
- Posición inicial aleatoria, dirección inicial aleatoria, memoria propia, reglas aprendidas propias

**Monstruo — Genotipo:** 1 sensor, 2 efectores, tabla reflejo fija

**Monstruo — Fenotipo:** Posición inicial aleatoria, robofagímetro propio

### 7.3 Percepciones de cada agente

**QUÉ CORRER:**
```python
# Mostrar ejemplos reales de percepciones capturadas
import json

with open("memory_robot_1.json") as f:
    memory = json.load(f)

print("=== EJEMPLOS DE PERCEPCIONES DEL ROBOT ===")
for record in memory[:3]:
    print(f"T={record['t']}: {record['percepcion']}")
    print(f"  → Acción: {record['accion']}, Resultado: {record['resultado']}")
    print()
```

### 7.4 Tabla percepción-acción

**QUÉ ESCRIBIR:**

**Tabla Robot (referencial — el agente la extiende con la memoria):**

| Percepción | Acción | Prioridad |
|---|---|---|
| bucle=True | SHUTDOWN | 1 (emergencia) |
| iridio_aqui=True | SUCK_IRIDIO | 2 (automático) |
| robot_delante=True | COMMUNICATE | 3 (protocolo) |
| olor=True, memoria sugiere peligro | TURN | 4 (aprendido) |
| brillo=True, olor=False | MOVE_FORWARD | 5 |
| vacuscopio=True | TURN | 6 |
| ninguna señal | MOVE_FORWARD o TURN | 7 (exploración) |

**Tabla Monstruo (completa y fija):**

| Percepción | Acción |
|---|---|
| robot_presente=True | RoboKiller |
| T mod 4 = 0 | RoboJumper (aleatorio) |

### 7.5 Diagrama de prioridad de reglas del Robot

**QUÉ CORRER:**
```python
# Mostrar las reglas base del robot al inicializarse
from robot_agent import RobotAgent
robot = RobotAgent(robot_id=0, initial_dir=(1,0,0))
print(f"Reglas base: {len(robot.rules)}")
for rule in robot.rules:
    print(f"  - {rule.descripcion} | utilidad base: {rule.utilidad}")
```

### 7.6 Mapeo percepción-acción (memoria interna)

**QUÉ ESCRIBIR:**
Explicar la estructura de `MemoryRecord` y cómo el robot la usa para generar nuevas reglas.
Los 3 patrones de aprendizaje (peligro por olor, agujero negro memorizado, iridio confirmado).

**QUÉ CORRER:**
```python
# Mostrar la memoria real del robot exportada por el logger
import json
with open("memory_robot_1.json") as f:
    memory = json.load(f)

print(f"Total de registros en memoria: {len(memory)}")
print(f"Primer registro: T={memory[0]['t']}, acción={memory[0]['accion']}")
print(f"Último registro: T={memory[-1]['t']}, resultado={memory[-1]['resultado']}")

# Contar tipos de acciones tomadas
from collections import Counter
acciones = Counter(r['accion'] for r in memory)
print(f"Distribución de acciones: {dict(acciones)}")
```

### 7.7 Racionalidad del agente

**QUÉ ESCRIBIR:**

**Fórmula R_i (Robot):**
```
R_i = (10 × iridio_count) - (50 × deaths) - (20 × bucles_detectados)
    + (5 × tiempo_sobrevivido / T_fin) - (1 × pasos_sin_avance)
```

**Fórmula M_j (Monstruo):**
```
M_j = robots_eaten × 100 + jumps_count
```

**¿Es episódico el robot?**
No. La decisión en T depende de la memoria acumulada hasta T-1.
Evidencia: un robot con memoria supera a uno sin memoria (ver Experimento 4).

---

## SECCIÓN 8 — CONSTRUCCIÓN DE LOS AGENTES

Esta es la sección más larga. Cada subsección muestra código + output.

### 8.1 Entorno (world.py)

**QUÉ CORRER:**
```python
# Generar y visualizar un mundo de ejemplo
from world import World
from visualizer import Visualizer

world = World(N=5, P_free=0.7, P_soft=0.2, P_negro=0.1, seed=42)
viz = Visualizer()

# Mostrar 3 capas del cubo
for z in [0, 2, 4]:
    viz.plot_world_slice(world, z_layer=z, t=0,
                         save_path=f"world_slice_z{z}.png")

# Estadísticas del mundo generado
total = 5**3
tipos = {"FREE":0, "VOID":0, "BLACK_HOLE":0}
for x in range(5):
    for y in range(5):
        for z in range(5):
            tipos[world.get_cell(x,y,z).type.name] += 1
print(f"Distribución real: {tipos}")
print(f"Porcentajes: { {k: v/total for k,v in tipos.items()} }")
```

**QUÉ VARIAR Y POR QUÉ ES INTERESANTE:**

| Parámetro | Valores a mostrar | Por qué es interesante |
|---|---|---|
| `P_negro` | 0.05, 0.15, 0.25 | A mayor P_negro, más robots mueren por agujero negro antes de aprender |
| `P_soft` | 0.1, 0.3, 0.5 | A mayor P_soft, el espacio navigable se fragmenta → robots se quedan atrapados |
| `N` | 3, 5, 7 | Muestra cómo el tamaño afecta la densidad del entorno |

### 8.2 Agente Monstruo (monster_agent.py)

**QUÉ CORRER:**
```python
# Demostrar fusión de monstruos
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

# Forzar salto de M1 hacia M2
for nx,ny,nz in world.get_neighbors(1,1,1):
    if (nx,ny,nz) != (2,1,1):
        world.get_cell(nx,ny,nz).type = CellType.VOID

result = m1.step(world, position=(1,1,1))

print(f"M1 vivo: {m1.is_alive}")
print(f"M2 robots_eaten: {m2.robots_eaten}")  # debe ser 5
print(f"Acción: {result['action']}")
print(f"Sobreviviente: Monster {result['surviving_monster'].id}")
```

### 8.3 Agente Robot (robot_agent.py)

**QUÉ CORRER — 3 demostraciones:**

**Demo A: Vacuscopio reactivo**
```python
from world import World
from robot_agent import RobotAgent
from config import CellType, Action

world = World(N=5, P_free=1.0, P_soft=0.0, P_negro=0.0, seed=1)
world.get_cell(3,2,2).type = CellType.VOID

robot = RobotAgent(robot_id=1, initial_dir=(1,0,0))
world.place_entity(robot, "robot", 2, 2, 2)

p1 = robot.perceive(world, (2,2,2))
print(f"Antes de mover → vacuscopio: {p1.vacuscopio}")  # False

result = robot.act(Action.MOVE_FORWARD, world, (2,2,2), 0)
print(f"Resultado del movimiento: {result['action']}, razón: {result['reason']}")

p2 = robot.perceive(world, (2,2,2))
print(f"Después de BLOCKED → vacuscopio: {p2.vacuscopio}")  # True
```

**Demo B: Aprendizaje de regla por olor**
```python
from robot_agent import RobotAgent, Perception
from config import Action, DeathCause

robot = RobotAgent(robot_id=1, initial_dir=(1,0,0))
reglas_antes = len(robot.rules)

# Inyectar patrón: percibí olor, avancé, morí por monstruo
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
```

**Demo C: Memoria real del robot**
```python
import json
with open("memory_robot_1.json") as f:
    memory = json.load(f)

print(f"Duración de vida: {len(memory)} ticks")
print(f"Causa de muerte implícita: {memory[-1]['resultado']}")

# Análisis de la memoria
vacuscopio_activaciones = sum(1 for r in memory if r['percepcion']['vacuscopio'])
print(f"Veces que el vacuscopio se activó: {vacuscopio_activaciones}")

posiciones = [tuple(r['posicion']) for r in memory]
celdas_unicas = len(set(posiciones))
print(f"Celdas distintas visitadas: {celdas_unicas}/{len(memory)} pasos")
```

### 8.4 Simulador (simulator.py)

**QUÉ CORRER:**
```python
# Corrida completa con reporte
from simulator import Simulator
import config

config.N = 5
config.N_ROBOT = 2
config.N_MONSTRUOS = 2
config.N_IRIDIO = 5
config.T_FIN = 100
config.SEED = 42

sim = Simulator()
sim.initialize()
sim.run()

summary = sim.metrics.generate_summary()
print("=== RESUMEN DE SIMULACIÓN ===")
print(f"Tiempo total: {summary.get('t_final', 'N/A')} ticks")
print(f"Iridio recolectado: {summary.get('iridio_recolectado_total', 0)}/{config.N_IRIDIO}")
print(f"Robots sobrevivientes: {summary.get('robots_vivos_final', 0)}/{config.N_ROBOT}")
print(f"R_global: {summary.get('R_global', 0):.2f}")
print(f"Tasa de supervivencia: {summary.get('TS', 0):.2%}")
print(f"Eficiencia de recolección: {summary.get('ER', 0):.2%}")
print(f"Eficiencia de exploración: {summary.get('EE', 0):.2%}")

# Exportar log completo
sim.logger.export_to_json("simulation_log.json")
sim.logger.export_to_csv("simulation_log.csv")
```

---

## SECCIÓN 9 — ANÁLISIS DE RESULTADOS

Esta es la sección más importante para el profesor. Cada experimento tiene su propia subsección.

---

### 9.1 Experimento 1 — Análisis de Sensibilidad

**Pregunta:** ¿Cómo afecta cada parámetro al desempeño global del sistema?

**QUÉ CORRER:**
```python
from experiments import run_sensitivity_analysis
from visualizer import Visualizer

results = run_sensitivity_analysis()
viz = Visualizer()
viz.plot_sensitivity(results, save_path="exp1_sensibilidad.png")

# Imprimir tabla de resultados
print(f"{'Parámetro':<15} {'Valor':<8} {'R_global':<12} {'TS':<8} {'ER':<8}")
print("-" * 55)
for r in results:
    print(f"{r['parametro']:<15} {r['valor']:<8} {r['R_global']:<12.2f} {r['TS']:<8.2%} {r['ER']:<8.2%}")
```

**QUÉ VARIAR Y RESULTADO ESPERADO:**

| Parámetro | Valores | Resultado esperado |
|---|---|---|
| `N` | 3, 4, 5, 6, 7 | R_global sube con N (más espacio = menos colisiones fatales) |
| `N_ROBOT` | 1, 2, 3, 5 | Más robots = más iridio recolectado pero más encuentros entre ellos |
| `N_MONSTRUOS` | 1, 2, 4 | Más monstruos = mayor mortalidad de robots |
| `N_IRIDIO` | 3, 5, 10 | Más iridio = mayor ER pero no necesariamente mayor R_global |
| `P_negro` | 0.05, 0.10, 0.20 | Más agujeros = más muertes tempranas por BLACK_HOLE |

---

### 9.2 Experimento 2 — Curva de Aprendizaje

**Pregunta:** ¿El robot recolecta más iridio en la segunda mitad de su vida que en la primera?

**QUÉ CORRER:**
```python
from experiments import run_learning_curve_experiment
from visualizer import Visualizer

results = run_learning_curve_experiment()
viz = Visualizer()
viz.plot_metrics_timeline(results['history'], save_path="exp2_aprendizaje.png")

print("=== CURVA DE APRENDIZAJE ===")
print(f"Iridio en primera mitad (T=0..50):  {results['iridio_primera_mitad']}")
print(f"Iridio en segunda mitad (T=51..100): {results['iridio_segunda_mitad']}")
mejora = results['iridio_segunda_mitad'] - results['iridio_primera_mitad']
print(f"Mejora absoluta: {mejora:+d} bloques")
print(f"Reglas generadas al final: {results['reglas_generadas_promedio']:.1f} por robot")
```

**QUÉ VARIAR:**

| Parámetro | Por qué variarlo |
|---|---|
| `T_FIN` = 50, 100, 200 | Con más tiempo el robot aprende más reglas → la brecha primera/segunda mitad crece |
| `N_MONSTRUOS` = 0, 1, 2 | Sin monstruos el robot vive más y la curva de aprendizaje es más clara |
| `SEED` = 42, 7, 99 | Verificar que la mejora no es artefacto de una semilla particular |

---

### 9.3 Experimento 3 — Detección de Bucles

**Pregunta:** ¿En cuántas iteraciones el Infinitómetro detecta un bucle inevitable?

**QUÉ CORRER:**
```python
from experiments import run_loop_detection_test
from visualizer import Visualizer

results = run_loop_detection_test()

print("=== DETECCIÓN DE BUCLES ===")
print(f"Bucle detectado en iteración: {results['t_deteccion']}")
print(f"Longitud del patrón repetido: {results['patron_longitud']} posiciones")
print(f"Veces que se repitió antes de detectar: {results['repeticiones']}")
print(f"Causa de término: {results['causa_termino']}")

# Graficar las posiciones visitadas (pasillo circular)
viz = Visualizer()
viz.plot_heatmap(results['visit_counts'], N=results['N'],
                 save_path="exp3_bucle_heatmap.png")
```

**QUÉ VARIAR:**

| Parámetro | Valores | Por qué es interesante |
|---|---|---|
| `LOOP_WINDOW` | 20, 30, 40 | Ventana más pequeña = detección más rápida pero más falsos positivos |
| `LOOP_THRESHOLD` | 2, 3 | Umbral más alto = más tolerante a repeticiones naturales de exploración |
| Largo del pasillo | 3, 5, 8 celdas | Pasillo más largo = patrón más largo = tarda más en detectarse |

---

### 9.4 Experimento 4 — No-Episodicidad

**Pregunta:** ¿El robot con memoria supera al robot sin memoria?

**QUÉ CORRER:**
```python
from experiments import run_episodic_test
from visualizer import Visualizer

results = run_episodic_test()

print("=== TEST DE NO-EPISODICIDAD ===")
print(f"Robot CON memoria:")
print(f"  Iridio recolectado: {results['robot_con_memoria']['iridio']}")
print(f"  Score R_i:          {results['robot_con_memoria']['score']:.2f}")
print(f"  Muertes:            {results['robot_con_memoria']['muertes']}")
print()
print(f"Robot SIN memoria (limpio cada tick):")
print(f"  Iridio recolectado: {results['robot_sin_memoria']['iridio']}")
print(f"  Score R_i:          {results['robot_sin_memoria']['score']:.2f}")
print(f"  Muertes:            {results['robot_sin_memoria']['muertes']}")
print()
print(f"Conclusión: {results['conclusion']}")
```

**QUÉ VARIAR:**

| Parámetro | Por qué variarlo |
|---|---|
| `T_FIN` = 50, 100, 200 | Con más tiempo la brecha entre con/sin memoria se agranda |
| `N_MONSTRUOS` = 0, 2, 4 | Más monstruos = más oportunidad de aprender la regla de olor |
| `SEED` multiple | Verificar que el resultado no es específico de una semilla |

---

### 9.5 Experimento 5 — Impacto de la Comunicación

**Pregunta:** ¿Los robots que negocian al encontrarse tienen mejor desempeño?

**QUÉ CORRER:**
```python
from experiments import run_communication_experiment

results = run_communication_experiment()

print("=== IMPACTO DEL PROTOCOLO DE COMUNICACIÓN ===")
print(f"CON comunicación (aleatorio):")
print(f"  R_global: {results['con_comunicacion']['R_global']:.2f}")
print(f"  Activaciones Roboscanner: {results['con_comunicacion']['roboscanner_activaciones']}")
print()
print(f"SIN comunicación (siempre avanza):")
print(f"  R_global: {results['sin_comunicacion']['R_global']:.2f}")
print(f"  Colisiones entre robots: {results['sin_comunicacion']['colisiones_robots']}")
```

**QUÉ VARIAR:**

| Parámetro | Por qué variarlo |
|---|---|
| `N_ROBOT` = 2, 4, 6 | Más robots = más encuentros = comunicación más relevante |
| `N` = 3, 5 | Mundo pequeño = más encuentros forzados |

---

### 9.6 Experimento 6 — Escalabilidad

**Pregunta:** ¿Cómo crece el tiempo de cómputo con N?

**QUÉ CORRER:**
```python
from experiments import run_scalability_test
from visualizer import Visualizer

results = run_scalability_test()
viz = Visualizer()
viz.plot_scalability(results, save_path="exp6_escalabilidad.png")

print("=== ESCALABILIDAD ===")
print(f"{'N':<6} {'Celdas':<10} {'ms/tick':<12} {'Total ticks':<15}")
print("-" * 45)
for r in results:
    print(f"{r['N']:<6} {r['N']**3:<10} {r['ms_per_tick']:<12.3f} {r['t_final']:<15}")
```

**QUÉ VARIAR:**

| Valores de N | Resultado esperado |
|---|---|
| 3, 4, 5, 6, 7 | Crecimiento aproximadamente cúbico O(N³) en tiempo de cómputo |

---

### 9.7 Visualización del Estado del Mundo

**QUÉ CORRER:**
```python
# Corrida con capturas de estado en T=0, T=25, T=50, T=75, T=100
from simulator import Simulator
from visualizer import Visualizer
import config

config.N = 5; config.N_ROBOT = 2; config.N_MONSTRUOS = 2
config.N_IRIDIO = 5; config.T_FIN = 100; config.SEED = 42

sim = Simulator()
sim.initialize()
viz = Visualizer()

# Capturar frames en momentos clave
snapshots_t = [0, 25, 50, 75, 99]
for t_objetivo in snapshots_t:
    while sim.current_t < t_objetivo and not sim.finished:
        sim.step(sim.current_t)
        sim.current_t += 1
    viz.plot_world_slice(sim.world, z_layer=2, t=sim.current_t,
                         save_path=f"snapshot_t{t_objetivo}.png")

# Mapa de calor de toda la simulación
heatmap = sim.metrics.get_visit_heatmap(config.N)
viz.plot_heatmap(heatmap, N=config.N, save_path="heatmap_exploracion.png")

# Timeline de métricas
viz.plot_metrics_timeline(sim.metrics.history,
                          save_path="timeline_metricas.png")

# Distribución de scores
scores = [sim.metrics.compute_robot_score(r) for r in sim.robots]
viz.plot_score_distribution(scores, save_path="distribucion_scores.png")
```

---

## SECCIÓN 10 — CONCLUSIONES

**QUÉ ESCRIBIR:**
Cada conclusión debe ser una métrica, no una opinión. Estructura sugerida:

```
C1. El Infinitómetro detectó bucles en un promedio de X iteraciones
    (rango: Y-Z) para pasillos de longitud L, con LOOP_WINDOW=30.

C2. El agente Robot con memoria superó al agente sin memoria en un
    X% en score R_i promedio, validando que el entorno NO es episódico.

C3. A mayor P_negro (agujeros negros), la tasa de supervivencia TS
    decreció de X% (P_negro=0.05) a Y% (P_negro=0.25).

C4. La fusión de monstruos ocurrió en el X% de las simulaciones con
    N_MONSTRUOS >= 2, resultando en un super-monstruo con robots_eaten
    promedio de Z.

C5. La escalabilidad del sistema es aproximadamente O(N^2.X) en tiempo
    de cómputo por iteración para N entre 3 y 7.
```

**Propiedades emergentes identificadas:**
1. Clustering de monstruos → fusiones en cascada
2. Zonas de exclusión aprendidas por robots tras detectar olor
3. Comportamiento de seguimiento de paredes (evidenciado en memory_robot_1.json)
4. Extinción prematura con P_negro alto + N pequeño

**QUÉ CORRER:**
```python
# Tabla resumen de todas las conclusiones métricas
from experiments import run_all_experiments
all_results = run_all_experiments()

# Exportar todo a JSON para el informe
import json
with open("resultados_completos.json", "w") as f:
    json.dump(all_results, f, indent=2)
print("Resultados exportados a resultados_completos.json")
```

---

## SECCIÓN 11 — RECOMENDACIONES

El enunciado exige al menos 3 recomendaciones implementadas y evaluadas.

**Recomendación 1 — Memoria compartida selectiva entre robots (anti-bucle colectivo)**

```python
# Implementar: cuando un robot muere por BLACK_HOLE,
# antes de borrar su memoria, broadcast la posición del agujero
# a los robots vivos dentro de distancia Manhattan <= 3.

# Para probar: comparar muertes_por_black_hole con/sin esta feature
config.ENABLE_MEMORY_BROADCAST = True  # agregar a config.py
```

**Recomendación 2 — Exploración sistemática por sectores**

```python
# En lugar de exploración puramente por utilidad, dividir el cubo
# en octantes y asignar un octante prioritario a cada robot.
# Reducir PENALTY_REVISIT para celdas fuera del octante asignado.

# Para probar: comparar EE (eficiencia de exploración) con/sin sectores
```

**Recomendación 3 — Umbral adaptativo del Infinitómetro**

```python
# En lugar de LOOP_WINDOW fijo, hacer que crezca con el tiempo:
# LOOP_WINDOW_efectivo = LOOP_WINDOW * (1 + t / T_FIN)
# Así el robot es más tolerante a repeticiones al inicio
# (exploración normal) y más estricto al final.

# Para probar: comparar t_deteccion y false_positives con/sin adaptativo
```

**QUÉ CORRER para cada recomendación:**
```python
# Comparar R_global con y sin cada recomendación
from experiments import run_sensitivity_analysis

# Baseline
config.ENABLE_MEMORY_BROADCAST = False
baseline = run_sensitivity_analysis()

# Con recomendación 1
config.ENABLE_MEMORY_BROADCAST = True
con_rec1 = run_sensitivity_analysis()

print(f"R_global baseline: {baseline[0]['R_global']:.2f}")
print(f"R_global con rec1: {con_rec1[0]['R_global']:.2f}")
print(f"¿Es viable? {'Sí' if con_rec1[0]['R_global'] > baseline[0]['R_global'] else 'No'}")
```

---

## SECCIÓN 12 — REFERENCIAS BIBLIOGRÁFICAS

**Bibliografía mínima recomendada:**

1. Russell, S. & Norvig, P. (2020). *Artificial Intelligence: A Modern Approach* (4th ed.). Pearson. — Fuente principal para tipos de agentes, clasificación AIMA del ambiente, agentes basados en utilidad.

2. Wooldridge, M. (2009). *An Introduction to MultiAgent Systems* (2nd ed.). Wiley. — Para el diseño multiagente y la interacción entre instancias.

3. Sutton, R. & Barto, A. (2018). *Reinforcement Learning: An Introduction* (2nd ed.). MIT Press. — Para contextualizar el aprendizaje por experiencia del robot.

4. Weiss, G. (Ed.). (2013). *Multiagent Systems*. MIT Press. — Para el protocolo de comunicación entre agentes.

---

## CHECKLIST FINAL ANTES DE ENTREGAR

```
☐ Todas las figuras están numeradas (Figura 1, Figura 2, ...)
☐ Todas las tablas están numeradas (Tabla 1, Tabla 2, ...)
☐ Documento a doble columna, fuente 10 u 11
☐ Código fuente legible (no capturas de pantalla de código)
☐ Imágenes legibles (resolución suficiente)
☐ memory_robot_1.json analizado y comentado en sección 8.3
☐ Los 6 experimentos tienen output real (no simulado)
☐ Las 3 recomendaciones fueron implementadas y evaluadas
☐ Cada conclusión tiene una métrica concreta
☐ Google Drive con todos los archivos accesible
☐ Este documento incluido como primera parte del entregable
```

---

*Fin de la guía del informe.*
