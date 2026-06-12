# REQUERIMIENTOS DE SOFTWARE — EXAMEN FINAL MIA-103
## Fundamentos de Inteligencia Artificial

> **Fecha de análisis:** 10 de junio de 2026  
> **Propósito:** Traducción exhaustiva del enunciado en requerimientos de software implementables, con criterio propio sobre métricas, racionalidad y estructura de códigos.

---

## ÍNDICE

1. [Visión General del Sistema](#1-visión-general-del-sistema)
2. [Requerimientos del Entorno (World Engine)](#2-requerimientos-del-entorno-world-engine)
3. [Requerimientos del Agente Robot](#3-requerimientos-del-agente-robot)
4. [Requerimientos del Agente Monstruo](#4-requerimientos-del-agente-monstruo)
5. [Requerimientos del Gestor de Tiempo](#5-requerimientos-del-gestor-de-tiempo)
6. [Requerimientos de Métricas y Racionalidad](#6-requerimientos-de-métricas-y-racionalidad)
7. [Requerimientos de Logging y Memoria](#7-requerimientos-de-logging-y-memoria)
8. [Requerimientos de Visualización](#8-requerimientos-de-visualización)
9. [Requerimientos del Orquestador / Simulación](#9-requerimientos-del-orquestador--simulación)
10. [Requerimientos de Análisis y Experimentos](#10-requerimientos-de-análisis-y-experimentos)
11. [Estructura de Códigos a Implementar](#11-estructura-de-códigos-a-implementar)
12. [Criterio Propio: Métricas y Racionalidad](#12-criterio-propio-métricas-y-racionalidad)
13. [Checklist de Cobertura vs. Documento](#13-checklist-de-cobertura-vs-documento)

---

## 1. VISIÓN GENERAL DEL SISTEMA

El sistema es una **simulación multiagente en un espacio 3D cúbico discreto**. Los componentes principales son:

| Componente | Descripción |
|---|---|
| `World` | Cubo N×N×N de celdas tipificadas (libre, vacía, agujero negro) |
| `Robot` | Agente con memoria interna, basado en utilidad, velocidad 1/1 |
| `Monster` | Agente reflejo simple, sin memoria, velocidad 1/4 |
| `Iridio` | Objeto pasivo recolectable con propiedades de brillo |
| `TimeManager` | Contador global T que sincroniza todos los agentes |
| `Simulator` | Orquestador que ejecuta el ciclo percepción→decisión→acción |
| `MetricsCollector` | Registra todas las métricas en cada iteración |
| `Visualizer` | Representación gráfica 2D/3D del estado del mundo (opcional pero recomendado) |

> **Nota sobre orientación:** No existe un módulo `orientation.py` separado. La lógica de giro del robot (Roboturner) se resuelve completamente con la constante `TURN_TABLE` en `config.py` — una tabla de lookup de 6×4 entradas. Esto cubre el 100% de lo que el enunciado exige sin necesidad de quaterniones ni matrices de rotación.

**Parámetros de entrada del sistema (todos configurables):**

```
N            → Tamaño del lado del cubo (el mundo tiene N³ celdas)
P_free       → Porcentaje de zonas libres
P_soft       → Porcentaje de zonas vacías
P_negro      → Porcentaje de agujeros negros
N_robot      → Número de robots (instancias del agente Robot)
N_monstruos  → Número de monstruos (instancias del agente Monstruo)
N_iridio     → Número de bloques de iridio
T_inicio     → Valor inicial del contador de tiempo
T_fin        → Valor final del contador de tiempo (condición de término)
SEED         → Semilla aleatoria para reproducibilidad de experimentos
```

> **Restricción de validación:** `P_free + P_soft + P_negro = 1.0`. El sistema debe validar esto al iniciar.

---

## 2. REQUERIMIENTOS DEL ENTORNO (WORLD ENGINE)

### 2.1 Estructura de Datos del Mundo

**REQ-ENV-01:** El mundo debe representarse como un arreglo tridimensional de `N×N×N` celdas indexadas por `(x, y, z)` donde `x, y, z ∈ [0, N-1]`.

**REQ-ENV-02:** Cada celda debe tener un tipo exclusivo:
- `FREE` (libre): puede contener entidades
- `VOID` (vacía): impenetrable, ninguna entidad puede entrar ni cruzar
- `BLACK_HOLE` (agujero negro): el tiempo no existe aquí; quien entra no sale

**REQ-ENV-03:** El mundo debe estar rodeado de una capa de celdas `VOID` implícita (el borde), por lo que las coordenadas válidas son `[0, N-1]` y cualquier intento de salir es bloqueado como `VOID`.

**REQ-ENV-04:** El mundo debe generarse aleatoriamente al iniciar la simulación con la distribución porcentual configurada (`P_free`, `P_soft`, `P_negro`).

**REQ-ENV-05:** La generación debe garantizar que **al menos** `N_robot + N_monstruos + N_iridio` celdas sean de tipo `FREE` para colocar todas las entidades iniciales.

**REQ-ENV-06:** El sistema debe validar que el mundo generado sea **conexo** para las celdas `FREE` (o al menos que todos los robots y el iridio sean alcanzables entre sí mediante BFS/DFS). Si no es conexo, regenerar.

### 2.2 Adyacencia

**REQ-ENV-07:** La adyacencia en un espacio 3D discreto es de **6 caras** (no diagonal). Los 6 vecinos de `(x,y,z)` son:
```
(x+1,y,z), (x-1,y,z)   → eje X
(x,y+1,z), (x,y-1,z)   → eje Y
(x,y,z+1), (x,y,z-1)   → eje Z
```

**REQ-ENV-08:** El sistema debe exponer una función `get_neighbors(x, y, z) → list[Cell]` que retorne los vecinos válidos (dentro de límites del cubo).

### 2.3 Propagación de Señales

**REQ-ENV-09 — Brillo del Iridio:** Cuando un bloque de iridio existe en `(x,y,z)`, sus 6 celdas adyacentes deben tener el atributo `IRIDIO_BRILLO = True`. Esta propagación debe recalcularse cada vez que un bloque de iridio desaparece.

**REQ-ENV-10 — Olor del Monstruo:** Cuando un monstruo está en `(x,y,z)`, sus 6 celdas adyacentes deben tener el atributo `OLOR_MONSTRUO = True`. Esta propagación debe recalcularse cada vez que un monstruo se mueve.

**REQ-ENV-11:** Las propagaciones de brillo y olor **se superponen**: una celda puede tener ambas señales simultáneamente. Cada señal es independiente.

**REQ-ENV-12:** La propagación **no atraviesa celdas VOID ni BLACK_HOLE** (el olor/brillo no se filtra a través de paredes). *(Criterio propio — el enunciado no lo especifica, pero es físicamente consistente y añade complejidad estratégica al agente).*

### 2.4 Estado de Contenido de Celdas

**REQ-ENV-13:** Cada celda `FREE` puede contener como máximo:
- 1 bloque de Iridio **ó** 1 Robot **ó** 1 Monstruo (o combinaciones Robot+Monstruo para disparar el RoboKiller, pero no 2 bloques de Iridio)
- **Nota:** Un robot puede estar en la misma celda que iridio (la absorbe inmediatamente) o que un monstruo (es destruido inmediatamente)

**REQ-ENV-14:** El mundo debe exponer métodos:
- `place_entity(entity, x, y, z)` → coloca entidad
- `remove_entity(entity)` → remueve entidad
- `get_cell_content(x, y, z)` → retorna qué hay en la celda
- `get_cell_type(x, y, z)` → retorna FREE / VOID / BLACK_HOLE
- `get_cell_signals(x, y, z)` → retorna `{brillo: bool, olor: bool}`

---

## 3. REQUERIMIENTOS DEL AGENTE ROBOT

### 3.1 Estructura del Robot

**REQ-ROB-01:** Cada robot es una **instancia independiente** de la clase `RobotAgent`. Todas las instancias comparten el mismo código (genotipo) pero tienen su propia memoria (fenotipo distinto).

**REQ-ROB-02:** El robot tiene los siguientes atributos de estado:
```
position     (x, y, z)         → posición actual en el mundo
direction    (dx, dy, dz)      → vector unitario de dirección de avance;
                                  exactamente uno de los 6 valores posibles:
                                  (1,0,0),(-1,0,0),(0,1,0),(0,-1,0),(0,0,1),(0,0,-1)
is_alive     bool              → si el robot sigue activo
iridio_count int               → cantidad de iridio recolectado
step_count   int               → número de iteraciones ejecutadas
id           int               → identificador único
```

**REQ-ROB-03:** El robot **siempre tiene dirección**. La dirección es uno de los 6 vectores unitarios del grid 3D discreto. Los 4 costados son los 4 vectores perpendiculares al vector de avance actual, obtenidos mediante una tabla de lookup `TURN_TABLE` definida en `config.py`. No se requiere matriz de rotación ni quaternión — el enunciado solo pide girar 90° entre los 4 costados numerados, lo cual se resuelve completamente con esa tabla.

### 3.2 Sensores del Robot

**REQ-ROB-S01 — Vacuscopio:** Se activa **reactivamente**: solo cuando el robot intenta moverse a una celda VOID y falla. Retorna `True` si el movimiento fue bloqueado por zona vacía. No percibe la zona vacía a distancia.

**REQ-ROB-S02 — Apestómetro:** Se activa en cada iteración. Consulta `get_cell_signals(x,y,z)` y retorna `{olor: bool}`. No indica en qué dirección está el monstruo.

**REQ-ROB-S03 — Black Hole Detector:** Se activa cuando el robot **ya entró** a una celda `BLACK_HOLE`. Activa inmediatamente `AutoShutdownUnit`. El robot no puede evitarlo una vez dentro (por eso la memoria y el aprendizaje son críticos).

**REQ-ROB-S04 — IridioScan:** Se activa en cada iteración. Consulta si alguno de los 6 vecinos tiene `brillo = True`. Retorna `{brillo: bool}`. No indica la dirección exacta.

**REQ-ROB-S05 — Energómetro Espectral:** Se activa cuando el robot está en la misma celda que un bloque de iridio. Retorna `{iridio_presente: bool}` y dispara automáticamente el efector `IridioSuctor`.

**REQ-ROB-S06 — RoboLocator:** Retorna la posición actual `(x, y, z)` del robot. Solo se activa cuando el robot ocupa una celda (es decir, en cada iteración normal).

**REQ-ROB-S07 — Giroscopio:** Retorna la dirección actual del robot `(dx, dy, dz)` y su orientación. No retorna la posición.

**REQ-ROB-S08 — Roboscanner:** Detecta si la celda **delante** del robot (en la dirección actual) contiene otro robot. Si `True`, dispara protocolo de comunicación entre robots.

**REQ-ROB-S09 — Infinitómetro:** Sensor de bucle infinito. Debe implementarse como lógica interna que analiza la memoria del robot. Ver criterio en sección 12.

**Percepción completa por iteración** (tupla que recibe el agente):
```python
Perception = {
    "olor":           bool,   # Apestómetro
    "brillo":         bool,   # IridioScan
    "iridio_aqui":    bool,   # Energómetro Espectral
    "robot_delante":  bool,   # Roboscanner
    "posicion":       (x,y,z),# RoboLocator
    "direccion":      (dx,dy,dz), # Giroscopio
    "vacuscopio":     bool,   # Solo True si el paso anterior fue bloqueado
    "bucle":          bool,   # Infinitómetro
}
```

### 3.3 Efectores del Robot

**REQ-ROB-E01 — Propulsor Direccional:** Mueve el robot hacia adelante (celda en la dirección actual). Antes de moverse, verifica tipo de celda destino:
- Si `VOID` → activa Vacuscopio, no se mueve
- Si `BLACK_HOLE` → entra, activa Black Hole Detector → AutoShutdown
- Si `FREE` → entra, activa sensores de la nueva celda

**REQ-ROB-E02 — Roboturner:** Rota la dirección del robot 90° hacia uno de sus 4 costados. Los 4 costados se numeran (0, 1, 2, 3) y la rotación se resuelve con una tabla de lookup `TURN_TABLE` definida en `config.py`. La acción es `TURN(lado: int ∈ {0,1,2,3})`. No se necesita archivo `orientation.py` separado ni representación matricial/cuaternionica — la tabla cubre los 6×4 = 24 casos posibles en ~10 líneas de código.

**REQ-ROB-E03 — IridioSuctor:** Se activa automáticamente cuando `Energómetro Espectral = True`. Elimina el bloque de iridio de la celda, incrementa `iridio_count`, recalcula el brillo en el entorno.

**REQ-ROB-E04 — AutoShutdownUnit:** Termina la instancia del robot. Se activa por:
- Black Hole Detector
- Infinitómetro (bucle detectado)
- RoboKiller del monstruo (pero esto es externo)

**Acciones posibles del robot por iteración:**
```
MOVE_FORWARD          → Propulsor
TURN(0), TURN(1), TURN(2), TURN(3)  → Roboturner (4 acciones)
SUCK_IRIDIO           → IridioSuctor (automático, no cuenta como acción de decisión)
SHUTDOWN              → AutoShutdownUnit
COMMUNICATE(robot_id) → Protocolo entre robots (solo si Roboscanner = True)
WAIT                  → No hacer nada (no recomendado, pero posible)
```
> Total de acciones posibles: 7 (MOVE, TURN×4, SHUTDOWN, COMMUNICATE)

### 3.4 Memoria Interna del Robot

**REQ-ROB-M01:** Cada robot mantiene una **tabla de mapeo** (lista cronológica de registros):
```python
MemoryRecord = {
    "t":          int,        # tiempo en que ocurrió
    "percepcion": dict,       # percepción completa en ese instante
    "accion":     str,        # acción tomada
    "posicion":   (x,y,z),    # posición en ese instante
    "resultado":  str,        # qué pasó tras la acción (blocked, moved, iridio, etc.)
}
```

**REQ-ROB-M02:** La memoria es privada por instancia. Al destruirse el robot, la memoria se elimina con él.

**REQ-ROB-M03:** La memoria puede contener información **desactualizada** (un monstruo que se movió, iridio ya recogido). El agente debe tratar su memoria como **creencia**, no como hecho.

**REQ-ROB-M04:** El agente puede inferir **nuevas reglas** a partir de su memoria. Por ejemplo: "si en el tiempo T-5 percibí olor y moví hacia adelante, y en T-4 fui destruido por monstruo → regla: si hay olor, no avanzar en esa dirección". Esto se implementa como análisis de patrones en la tabla de memoria.

### 3.5 Lógica de Decisión del Robot (Agente Basado en Utilidad)

**REQ-ROB-D01:** El robot tiene un conjunto inicial de **reglas base** (hardcoded al inicio) y puede agregar nuevas reglas derivadas de su memoria.

**REQ-ROB-D02:** Para cada percepción puede activarse más de una regla. El agente debe tener una **función de utilidad** que puntúe cada acción candidata y elija la de mayor utilidad.

**REQ-ROB-D03:** La **única acción aleatoria permitida** para el robot es cuando el Roboscanner detecta otro robot enfrente (protocolo de encuentro). En todos los demás casos, la decisión es determinista basada en reglas + utilidad.

**REQ-ROB-D04 — Diagrama de Prioridad de Reglas (requerido en el informe):**
```
PRIORIDAD (de mayor a menor):
1. Si Black Hole Detector activo → SHUTDOWN (máxima prioridad, irreversible)
2. Si Infinitómetro activo (bucle) → SHUTDOWN
3. Si Energómetro activo → SUCK_IRIDIO (automático)
4. Si Robot delante → COMMUNICATE → decidir TURN o MOVE según protocolo
5. Si memoria sugiere peligro en dirección actual → TURN (regla aprendida)
6. Si Apestómetro activo → evaluar utilidades de TURN vs MOVE según memoria
7. Si IridioScan activo → MOVE_FORWARD hacia posible iridio (si no hay olor)
8. Si ninguna señal → exploración sistemática (MOVE o TURN según exploración)
```

**REQ-ROB-D05:** Las reglas nuevas generadas por la memoria **no sobreescriben** las reglas base. Solo añaden contexto.

---

## 4. REQUERIMIENTOS DEL AGENTE MONSTRUO

### 4.1 Estructura del Monstruo

**REQ-MON-01:** Cada monstruo es una instancia de la clase `MonsterAgent`. No tiene memoria, no tiene orientación, no sabe dónde está.

**REQ-MON-02:** Atributos de estado:
```
position        (x, y, z)   → posición actual (solo el mundo la conoce)
is_alive        bool
robots_eaten    int          → robofagímetro
jumps_count     int          → número de saltos realizados
id              int
```

**REQ-MON-03:** El monstruo opera a velocidad `1/4`: solo percibe y actúa cada 4 iteraciones del contador T.

### 4.2 Sensores del Monstruo

**REQ-MON-S01 — Robotscopio:** Detecta si en la celda actual del monstruo existe un robot. Retorna `{robot_presente: bool}`.

### 4.3 Efectores del Monstruo

**REQ-MON-E01 — RoboKiller:** Si `Robotscopio = True`, termina la vida del robot. Incrementa `robots_eaten`. El robot destruido pierde toda su memoria.

**REQ-MON-E02 — RoboJumper:** Se activa autónomamente cada 4 iteraciones (con o sin robot):
- Selecciona aleatoriamente una de las 6 celdas adyacentes
- Condiciones para saltar:
  - La celda debe ser `FREE`
  - La celda no debe contener Iridio
  - Si la celda contiene otro monstruo → **fusión**: ambos se vuelven uno, se suman `robots_eaten` y `jumps_count`
- Si ninguna celda adyacente es válida → el monstruo no se mueve en esa iteración

### 4.4 Lógica de Decisión del Monstruo (Agente Reflejo Simple)

**REQ-MON-D01:** La tabla percepción-acción del monstruo es completamente determinista:
```
SI Robotscopio = True → RoboKiller
SI T mod 4 = 0       → RoboJumper (aleatorio)
```
No hay más reglas. No hay memoria. No hay utilidad.

---

## 5. REQUERIMIENTOS DEL GESTOR DE TIEMPO

**REQ-TIME-01:** El `TimeManager` mantiene un contador entero `T ≥ 0`.

**REQ-TIME-02:** En cada iteración, `T` se incrementa en 1.

**REQ-TIME-03:** La simulación termina si:
- `T == T_fin`
- Todos los robots están muertos (no quedan instancias activas)
- Todo el iridio fue recolectado

**REQ-TIME-04:** En cada iteración, el orden de activación debe ser:
```
1. Activar todos los Robots (velocidad 1/1) → percibir → decidir → actuar
2. Si T mod 4 == 0 → Activar todos los Monstruos → percibir → actuar
3. Resolver colisiones (robot entra a celda de monstruo → RoboKiller)
4. Actualizar propagaciones (brillo, olor)
5. Registrar métricas del instante T
6. T += 1
```

**REQ-TIME-05:** El orden de activación de robots en el mismo instante es arbitrario pero reproducible (usar la semilla `SEED`).

---

## 6. REQUERIMIENTOS DE MÉTRICAS Y RACIONALIDAD

*(Esta sección mezcla lo que exige el documento con criterio propio para que tengan qué analizar y concluir.)*

### 6.1 Medida de Racionalidad del Robot

El documento exige definir una medida de racionalidad. Se propone la siguiente función:

**REQ-MET-01 — Performance Score del Robot (instancia i):**
```
R_i = (w1 × iridio_count_i) 
    - (w2 × deaths_i)               ← 0 si sobrevivió, 1 si fue destruido
    - (w3 × bucles_detectados_i) 
    + (w4 × tiempo_sobrevivido_i / T_fin)
    - (w5 × pasos_sin_avance_i)     ← iteraciones donde no recolectó ni exploró nuevo territorio
```
Donde `w1=10, w2=50, w3=20, w4=5, w5=1` son pesos configurables.

**REQ-MET-02 — Performance Global del Sistema:**
```
R_global = Σ R_i  para todos los robots (vivos y muertos)
```

**REQ-MET-03 — Medida de Racionalidad del Monstruo:**
```
M_j = robots_eaten_j × 100 + jumps_count_j
```
El monstruo es racional en la medida en que maximiza `robots_eaten`.

### 6.2 Métricas a Registrar por Iteración

**REQ-MET-04:** El `MetricsCollector` debe registrar en cada iteración `T`:

| Métrica | Descripción |
|---|---|
| `t` | Instante de tiempo |
| `robots_vivos` | Cuántos robots siguen activos |
| `iridio_total_recolectado` | Suma acumulada de todos los robots |
| `iridio_restante` | Bloques de iridio que quedan en el mundo |
| `monstruos_vivos` | Cuántos monstruos siguen activos (puede haber fusiones) |
| `robots_destruidos_acumulado` | Total de robots eliminados hasta T |
| `bucles_detectados_acumulado` | Total de AutoShutdowns por bucle |
| `agujeros_negros_caidos` | Total de caídas a agujeros negros |
| `memoria_size_promedio` | Tamaño promedio de la memoria de cada robot vivo |
| `reglas_generadas_promedio` | Nuevas reglas generadas por los robots en promedio |
| `celdas_exploradas_promedio` | Porcentaje de celdas FREE visitadas por los robots |

**REQ-MET-05:** Al final de la simulación generar un **resumen estadístico**:
- Iridio recolectado por robot (histograma)
- Distribución de causas de muerte de robots (agujero negro, monstruo, bucle)
- Evolución temporal de robots vivos vs. iridio restante (serie de tiempo)
- Mapa de calor de celdas visitadas en el mundo
- Número de reglas aprendidas por cada robot antes de morir

### 6.3 Métricas de Calidad del Agente (para el análisis)

**REQ-MET-06 — Eficiencia de exploración:**
```
EE = celdas_FREE_visitadas / total_celdas_FREE
```

**REQ-MET-07 — Tasa de supervivencia:**
```
TS = robots_vivos_al_final / N_robot
```

**REQ-MET-08 — Eficiencia de recolección:**
```
ER = iridio_recolectado / N_iridio
```

**REQ-MET-09 — Detección de bucles (propiedad emergente a analizar):**
El Infinitómetro debe implementarse como: si en los últimos K iteraciones el robot ha pasado por la misma secuencia de posiciones más de M veces → bucle. Se sugiere `K=20, M=2` como parámetros configurables.

---

## 7. REQUERIMIENTOS DE LOGGING Y MEMORIA

**REQ-LOG-01:** El sistema debe generar un log estructurado en formato **CSV o JSON** con todos los eventos de la simulación, indexados por tiempo T.

**REQ-LOG-02:** Eventos a registrar:
```
ROBOT_MOVE(id, from, to, t)
ROBOT_TURN(id, new_dir, t)
ROBOT_IRIDIO_SUCKED(id, pos, t)
ROBOT_DESTROYED(id, cause: {BLACK_HOLE|MONSTER|LOOP}, t)
ROBOT_COMM(id1, id2, decision, t)
MONSTER_JUMP(id, from, to, t)
MONSTER_EAT(monster_id, robot_id, t)
MONSTER_FUSE(id1, id2, surviving_id, t)
IRIDIO_APPEARED(pos, t)         ← al inicio
IRIDIO_COLLECTED(pos, robot_id, t)
NEW_RULE_GENERATED(robot_id, rule_description, t)
SIMULATION_END(reason, t)
```

**REQ-LOG-03:** La memoria de cada robot debe poder exportarse al final de la simulación para análisis externo.

---

## 8. REQUERIMIENTOS DE VISUALIZACIÓN

*(No obligatoria según el enunciado, pero altamente recomendada para el análisis de resultados)*

**REQ-VIS-01 — Visualización 2D (slices):** Mostrar capas 2D del cubo (planos X-Y para cada Z fijo). En cada celda mostrar:
- Color según tipo: FREE=blanco, VOID=gris oscuro, BLACK_HOLE=negro
- Ícono de robot (flecha indicando dirección)
- Ícono de monstruo
- Ícono de iridio (brillo amarillo)
- Overlay de señales (olor=rojo semitransparente, brillo=amarillo semitransparente)

**REQ-VIS-02 — Visualización 3D (matplotlib/plotly):** Scatter plot 3D con los elementos dinámicos sobre el grid estático.

**REQ-VIS-03 — Panel de métricas en tiempo real:** Gráfico de líneas mostrando evolución de robots vivos, iridio restante, score total.

**REQ-VIS-04 — Exportación de frames:** Capacidad de guardar frames de la simulación como imágenes PNG para generar GIF animado.

---

## 9. REQUERIMIENTOS DEL ORQUESTADOR / SIMULACIÓN

**REQ-SIM-01:** La clase `Simulator` debe:
- Inicializar el mundo con los parámetros dados
- Colocar robots, monstruos e iridio en posiciones aleatorias FREE (sin colisión entre sí al inicio)
- Ejecutar el bucle principal de tiempo
- Resolver el orden de activación (ver REQ-TIME-04)
- Detectar condición de término
- Exportar métricas y logs al finalizar

**REQ-SIM-02:** Debe ser posible ejecutar múltiples simulaciones con distintos parámetros (experimentos batch) y comparar resultados.

**REQ-SIM-03:** El sistema debe ser **reproducible**: con la misma `SEED` y los mismos parámetros debe producir exactamente la misma simulación.

**REQ-SIM-04 — Modos de ejecución:**
- `FAST`: sin visualización, máxima velocidad
- `VISUAL`: con visualización paso a paso (puede pausar)
- `BATCH`: N ejecuciones con variación de parámetros

---

## 10. REQUERIMIENTOS DE ANÁLISIS Y EXPERIMENTOS

*(Para generar todos los resultados exigidos en el informe)*

**REQ-EXP-01 — Experimento de Sensibilidad:** Variar N, P_free, N_robot, N_monstruos, N_iridio individualmente y medir el impacto en `R_global`. Resultado: tabla comparativa y gráficas.

**REQ-EXP-02 — Experimento de Aprendizaje:** Comparar la cantidad de iridio recolectado en las primeras 50 iteraciones vs. las últimas 50 iteraciones de cada robot. Si el robot aprende, debe mejorar con el tiempo. Resultado: curva de aprendizaje.

**REQ-EXP-03 — Experimento de Bucles:** Verificar que el Infinitómetro funciona correctamente. Crear un escenario donde el robot inevitablemente entre en bucle (sin iridio, con paredes VOID por todos lados excepto un pasillo circular) y medir en cuántas iteraciones lo detecta.

**REQ-EXP-04 — Experimento de Escalabilidad:** Variar N de 3 a 10 y medir el tiempo de cómputo por iteración. Resultado: gráfica de escalabilidad.

**REQ-EXP-05 — Experimento de Cooperación/Comunicación:** Medir cuántas veces se activa el Roboscanner y el impacto de la decisión tomada (continuar vs. girar) sobre el score final.

**REQ-EXP-06 — Verificar Ambiente Episódico:** Demostrar con logs que el agente robot NO es episódico (el resultado de una acción en T afecta las decisiones en T+1 y más allá).

---

## 11. ESTRUCTURA DE CÓDIGOS A IMPLEMENTAR

A continuación se listan los archivos Python a implementar, su propósito y qué debe contener cada uno.

---

### `config.py`
**Propósito:** Centralizar todos los parámetros de configuración de la simulación.

**Debe contener:**
- Constantes globales: `N`, `P_FREE`, `P_SOFT`, `P_NEGRO`, `N_ROBOT`, `N_MONSTRUOS`, `N_IRIDIO`, `T_INICIO`, `T_FIN`, `SEED`
- Pesos de la función de utilidad del robot: `W1_IRIDIO`, `W2_DEATH`, `W3_LOOP`, `W4_SURVIVE`, `W5_IDLE`
- Parámetros del Infinitómetro: `LOOP_WINDOW`, `LOOP_THRESHOLD`
- Parámetros de visualización: `CELL_SIZE`, `FPS`, `EXPORT_FRAMES`
- Enums o constantes para tipos de celda: `FREE=0, VOID=1, BLACK_HOLE=2`
- Enums para acciones del robot: `MOVE, TURN_0, TURN_1, TURN_2, TURN_3, SHUTDOWN, COMMUNICATE, WAIT`
- Enums para causas de muerte: `KILLED_BY_MONSTER, KILLED_BY_BLACK_HOLE, KILLED_BY_LOOP`
- **Tabla de orientación discreta del robot** — reemplaza completamente a `orientation.py`:

```python
# Los 6 vectores de dirección posibles en el grid 3D discreto
DIRECTIONS = [(1,0,0),(-1,0,0),(0,1,0),(0,-1,0),(0,0,1),(0,0,-1)]

# TURN_TABLE[direccion_actual][lado 0..3] → nueva dirección tras girar 90°
TURN_TABLE = {
    ( 1, 0, 0): [(0, 1,0),(0,-1,0),(0,0, 1),(0,0,-1)],
    (-1, 0, 0): [(0, 1,0),(0,-1,0),(0,0,-1),(0,0, 1)],
    ( 0, 1, 0): [(-1,0,0),(1,0,0),(0,0, 1),(0,0,-1)],
    ( 0,-1, 0): [( 1,0,0),(-1,0,0),(0,0,-1),(0,0, 1)],
    ( 0, 0, 1): [( 1,0,0),(-1,0,0),(0, 1,0),(0,-1,0)],
    ( 0, 0,-1): [(-1,0,0),( 1,0,0),(0, 1,0),(0,-1,0)],
}

def turn(current_direction: tuple, side: int) -> tuple:
    """Gira 90° hacia el costado indicado (0–3). Sin quaterniones, sin matrices."""
    return TURN_TABLE[current_direction][side]
```

> **Nota de diseño:** Esta tabla cubre los 24 casos posibles (6 direcciones × 4 costados) y es todo lo que el Roboturner necesita. El archivo `orientation.py` queda **eliminado** del proyecto.

---

### `world.py`
**Propósito:** Modelar el entorno 3D y todas sus propiedades.

**Debe contener:**
- Clase `Cell`: tipo (FREE/VOID/BLACK_HOLE), contenido (robot, monstruo, iridio o None), señales (brillo, olor)
- Clase `World`:
  - Método `__init__(N, P_free, P_soft, P_negro, seed)`: genera el grid aleatorio
  - Método `generate_world()`: distribución aleatoria de tipos de celda
  - Método `validate_world()`: verifica conectividad y suficiencia de celdas libres
  - Método `get_neighbors(x,y,z)`: retorna lista de celdas adyacentes válidas
  - Método `get_cell(x,y,z)`: retorna la celda
  - Método `place_entity(entity, x,y,z)`: ubica una entidad
  - Método `remove_entity(entity)`: remueve una entidad
  - Método `update_iridio_glow()`: recalcula brillo en todo el mapa
  - Método `update_monster_smell()`: recalcula olor en todo el mapa
  - Método `is_valid_position(x,y,z)`: verifica que esté dentro de límites
  - Método `get_free_random_position()`: retorna una posición FREE aleatoria sin entidades
  - Método `to_array()`: exporta el estado del mundo como numpy array (para visualización)

---

### `robot_agent.py`
**Propósito:** Implementar completamente el agente Robot con todos sus sensores, efectores, memoria y lógica de decisión.

**Debe contener:**
- Clase `Perception`: dataclass con todos los campos del sensor (olor, brillo, iridio_aqui, robot_delante, posicion, direccion, vacuscopio, bucle)
- Clase `MemoryRecord`: dataclass con (t, percepcion, accion, posicion, resultado)
- Clase `Rule`: representa una regla de decisión con (condicion: callable, accion: str, utilidad: float, descripcion: str)
- Clase `RobotAgent`:
  - Método `__init__(id, world, initial_pos, initial_dir)`: inicialización
  - Método `perceive()`: ejecuta todos los sensores y retorna un objeto `Perception`
  - Método `sense_apestometro()`: consulta olor en celda actual
  - Método `sense_iridioscan()`: consulta brillo en celdas adyacentes
  - Método `sense_energometro()`: detecta iridio en celda actual
  - Método `sense_roboscanner(world)`: detecta robot en celda delantera
  - Método `sense_infinitometro()`: analiza memoria para detectar bucle
  - Método `decide(perception)`: función de decisión → activa reglas, calcula utilidades, retorna acción
  - Método `evaluate_utility(action, perception)`: calcula utilidad de una acción dado el contexto
  - Método `act(action, world)`: ejecuta la acción decidida, retorna resultado
  - Método `move_forward(world)`: mueve al cubo delantero
  - Método `turn(side)`: rota la dirección 90°
  - Método `suck_iridio(world)`: absorbe el iridio
  - Método `shutdown()`: apaga el robot
  - Método `communicate(other_robot)`: protocolo de encuentro, retorna decisión conjunta
  - Método `update_memory(t, perception, action, result)`: agrega registro a la tabla de memoria
  - Método `generate_new_rules()`: analiza la memoria y genera nuevas reglas
  - Método `step(world, t)`: método principal — percibir → decidir → actuar → registrar
  - Atributo `memory`: lista de `MemoryRecord`
  - Atributo `rules`: lista de `Rule` (base + aprendidas)
  - Atributo `iridio_count`, `is_alive`, `death_cause`, `step_count`

---

### `monster_agent.py`
**Propósito:** Implementar el agente Monstruo como reflejo simple sin memoria.

**Debe contener:**
- Clase `MonsterAgent`:
  - Método `__init__(id, world, initial_pos)`: inicialización
  - Método `perceive(world)`: solo ejecuta Robotscopio, retorna `{robot_presente: bool}`
  - Método `decide(perception)`: tabla reflejo simple → si robot, matar; si T mod 4, saltar
  - Método `act(action, world)`: ejecuta RoboKiller o RoboJumper
  - Método `robokiller(world)`: destruye el robot en la celda actual
  - Método `robojumper(world)`: salta a celda adyacente aleatoria válida
  - Método `fuse_with(other_monster)`: fusión al caer en celda de otro monstruo
  - Método `step(world, t)`: ciclo completo para el monstruo
  - Atributo `robots_eaten`, `jumps_count`, `is_alive`

---

### `simulator.py`
**Propósito:** Orquestador principal de la simulación.

**Debe contener:**
- Clase `Simulator`:
  - Método `__init__(config)`: lee configuración, instancia mundo, robots, monstruos, iridio
  - Método `initialize()`: coloca todas las entidades en posiciones iniciales válidas
  - Método `run()`: bucle principal de tiempo, llama step en orden correcto
  - Método `step(t)`: un tick del reloj — activa robots, monstruos, resuelve colisiones, actualiza señales, registra métricas
  - Método `resolve_collisions()`: detecta co-ubicación robot+monstruo o robot+agujero negro
  - Método `check_termination()`: verifica condiciones de fin
  - Método `export_results()`: exporta logs, métricas y memorias de robots
  - Atributo `world`, `robots`, `monsters`, `iridio_positions`, `time_manager`, `metrics_collector`, `logger`

---

### `metrics.py`
**Propósito:** Registrar y calcular todas las métricas de la simulación.

**Debe contener:**
- Clase `MetricsCollector`:
  - Método `record(t, world, robots, monsters)`: captura el estado en el instante T
  - Método `compute_robot_score(robot)`: calcula `R_i` para un robot
  - Método `compute_global_score()`: calcula `R_global`
  - Método `compute_monster_score(monster)`: calcula `M_j`
  - Método `compute_exploration_efficiency(robot)`: calcula `EE`
  - Método `compute_survival_rate()`: calcula `TS`
  - Método `compute_collection_efficiency()`: calcula `ER`
  - Método `generate_summary()`: retorna diccionario con todas las métricas finales
  - Método `export_to_csv(filepath)`: exporta series de tiempo
  - Método `export_to_json(filepath)`: exporta métricas finales
  - Atributo `history`: lista de snapshots por instante T

---

### `logger.py`
**Propósito:** Registrar todos los eventos de la simulación en orden cronológico.

**Debe contener:**
- Clase `SimLogger`:
  - Método `log_event(event_type, **kwargs)`: registra un evento
  - Métodos específicos: `log_robot_move()`, `log_robot_turn()`, `log_iridio_collected()`, `log_robot_destroyed()`, `log_monster_jump()`, `log_monster_eat()`, `log_monster_fuse()`, `log_new_rule()`, `log_simulation_end()`
  - Método `export(filepath, format='csv')`: exporta el log completo
  - Atributo `events`: lista de dicts con todos los eventos

---

### `visualizer.py`
**Propósito:** Visualización del estado del mundo y las métricas.

**Debe contener:**
- Clase `Visualizer`:
  - Método `render_slice_2d(world, z_layer, t)`: renderiza un plano Z del cubo
  - Método `render_3d_scatter(world, t)`: renderiza el mundo en 3D con matplotlib/plotly
  - Método `render_metrics_panel(metrics_history)`: gráfico de líneas de métricas
  - Método `render_heatmap(visit_counts)`: mapa de calor de visitas
  - Método `export_frame(t, filepath)`: guarda el estado actual como imagen PNG
  - Método `animate(simulation_log)`: genera GIF de la simulación
  - Método `show()`: muestra la visualización interactiva

---

### `experiments.py`
**Propósito:** Orquestador de experimentos batch para el análisis de resultados.

**Debe contener:**
- Función `run_sensitivity_analysis()`: varía parámetros uno a uno y registra R_global
- Función `run_learning_curve_experiment()`: mide mejora del agente con el tiempo
- Función `run_loop_detection_test()`: escenario de bucle forzado
- Función `run_scalability_test()`: varía N y mide tiempo de cómputo
- Función `run_communication_experiment()`: mide impacto del protocolo de comunicación
- Función `run_episodic_test()`: demuestra que el agente no es episódico
- Función `run_all_experiments()`: ejecuta todos los experimentos y genera reporte
- Función `plot_results(results_dict)`: genera todas las gráficas del análisis

---

### `ontology.py` *(opcional, para representación formal)*
**Propósito:** Representar formalmente los conceptos ontológicos del problema.

**Debe contener:**
- Clases Python que mapean directamente a los conceptos de la ontología:
  - `Entity` (base abstracta), `Agent(Entity)`, `Object(Entity)`
  - `World`, `Cell`, `Zone`
  - `Robot(Agent)`, `Monster(Agent)`
  - `Iridio(Object)`, `BlackHole(Zone)`, `VoidZone(Zone)`, `FreeZone(Zone)`
  - `Sensor`, `Effector`, `Memory`, `Rule`, `UtilityFunction`
- Diccionario de definiciones ontológicas como docstrings o constantes

---

### `main.py`
**Propósito:** Punto de entrada principal de la simulación.

**Debe contener:**
- Parseo de argumentos por línea de comandos (N, seed, modo de ejecución, etc.)
- Instanciación del `Simulator` con la configuración elegida
- Llamada a `simulator.run()`
- Llamada a `experiments.run_all_experiments()` si el modo es `batch`
- Generación del reporte final

---

## 12. CRITERIO PROPIO: MÉTRICAS Y RACIONALIDAD

### 12.1 Sobre el Infinitómetro (sección 4.1.1, sensor 9)

El enunciado dice "que usted debe construir". Se propone el siguiente algoritmo:

```
ALGORITMO INFINITÓMETRO:
1. Mantener una ventana deslizante de las últimas LOOP_WINDOW posiciones visitadas.
2. Convertir la secuencia de posiciones en una cadena de texto.
3. Buscar si alguna sub-secuencia de longitud mínima LOOP_MIN_LEN se repite 
   al menos LOOP_THRESHOLD veces consecutivas dentro de la ventana.
4. Si se detecta repetición → retornar True → activar AutoShutdownUnit.

Parámetros sugeridos: LOOP_WINDOW=30, LOOP_MIN_LEN=4, LOOP_THRESHOLD=2
```

### 12.2 Sobre la Función de Utilidad

Para cada par (percepción, acción), la utilidad puede calcularse como:
```
U(accion | percepcion) = 
    + GAIN_IRIDIO     si accion lleva hacia celda con brillo y no hay olor
    - RISK_MONSTER    si hay olor y la acción avanza hacia zona posiblemente peligrosa
    - RISK_BLACK_HOLE si la memoria registra agujero negro en la dirección actual
    + GAIN_EXPLORE    si la acción lleva a una celda no visitada
    - PENALTY_REVISIT si la celda destino ya fue visitada muchas veces
```

### 12.3 Sobre el Ambiente (clasificación AIMA)

Para el informe, la clasificación recomendada es:

| Propiedad | Robot | Monstruo | Justificación |
|---|---|---|---|
| Accesible | No | No | Sensores limitados, no percibe el mapa completo |
| Determinista | No | No | Monstruos y otros robots introducen no determinismo |
| Episódico | No | Sí | Robot tiene memoria; monstruo no |
| Estático | No | No | Monstruos se mueven, iridio desaparece |
| Discreto | Sí | Sí | Grid de celdas enteras, tiempo discreto |

### 12.4 Propiedades Emergentes a Identificar

El enunciado pide identificar propiedades emergentes en las conclusiones:
1. **Clustering de monstruos**: los RoboJumper aleatorios pueden llevar a fusiones en cascada
2. **Zonas de exclusión aprendidas**: los robots aprenden a evitar regiones con olor → áreas que nunca exploran
3. **Competencia por iridio**: múltiples robots aceleran la recolección pero también pueden bloquearse entre sí
4. **Extinción prematura**: si N_monstruos es alto y N suficientemente pequeño, los robots pueden ser eliminados antes de recolectar nada (tipping point)
5. **Inmortalidad accidental de monstruos**: si todos los monstruos se fusionan en uno, ese super-monstruo tiene un `robots_eaten` muy alto pero solo opera en una zona

---

## 13. CHECKLIST DE COBERTURA VS. DOCUMENTO

| Requerimiento del Enunciado | Cubierto en | Notas |
|---|---|---|
| Mundo N³ con 3 tipos de celdas | `world.py` REQ-ENV-01..04 | ✅ |
| Parámetros N, P_free, P_soft, P_negro | `config.py` | ✅ |
| Borde VOID implícito | `world.py` REQ-ENV-03 | ✅ |
| 6-adyacencia (no diagonal) | `world.py` REQ-ENV-07 | ✅ |
| Brillo del iridio a 6 vecinos | `world.py` REQ-ENV-09 | ✅ |
| Olor del monstruo a 6 vecinos | `world.py` REQ-ENV-10 | ✅ |
| 1 iridio por celda máximo | `world.py` REQ-ENV-13 | ✅ |
| Robot velocidad 1/1 | `simulator.py` REQ-TIME-04 | ✅ |
| Monstruo velocidad 1/4 | `simulator.py` REQ-TIME-04 | ✅ |
| Vacuscopio (reactivo, no predictivo) | `robot_agent.py` REQ-ROB-S01 | ✅ |
| Apestómetro (6 caras, sin dirección) | `robot_agent.py` REQ-ROB-S02 | ✅ |
| Black Hole Detector → AutoShutdown | `robot_agent.py` REQ-ROB-S03 | ✅ |
| IridioScan (6 caras, sin dirección) | `robot_agent.py` REQ-ROB-S04 | ✅ |
| Energómetro → IridioSuctor automático | `robot_agent.py` REQ-ROB-S05 | ✅ |
| RoboLocator (posición actual) | `robot_agent.py` REQ-ROB-S06 | ✅ |
| Giroscopio (dirección, no posición) | `robot_agent.py` REQ-ROB-S07 | ✅ |
| Roboscanner → protocolo comunicación | `robot_agent.py` REQ-ROB-S08 | ✅ |
| Infinitómetro → AutoShutdown | `robot_agent.py` REQ-ROB-S09 + sección 12.1 | ✅ |
| Propulsor direccional (mueve hacia adelante) | `robot_agent.py` REQ-ROB-E01 | ✅ |
| Roboturner (4 lados, 90°) | `robot_agent.py` REQ-ROB-E02 + `TURN_TABLE` en `config.py` | ✅ |
| IridioSuctor (absorbe iridio) | `robot_agent.py` REQ-ROB-E03 | ✅ |
| AutoShutdownUnit | `robot_agent.py` REQ-ROB-E04 | ✅ |
| Memoria interna del robot | `robot_agent.py` REQ-ROB-M01..04 | ✅ |
| Reglas actualizables por experiencia | `robot_agent.py` REQ-ROB-M04, REQ-ROB-D05 | ✅ |
| Solo aleatorio en encuentro con robot | `robot_agent.py` REQ-ROB-D03 | ✅ |
| Agente basado en utilidad | `robot_agent.py` REQ-ROB-D01..D04 + `metrics.py` | ✅ |
| Sin cooperación entre robots (excepto encuentro) | `robot_agent.py` REQ-ROB-D03 | ✅ |
| Monstruo: Robotscopio | `monster_agent.py` REQ-MON-S01 | ✅ |
| Monstruo: RoboKiller | `monster_agent.py` REQ-MON-E01 | ✅ |
| Monstruo: RoboJumper (cada 4 iter, no a iridio) | `monster_agent.py` REQ-MON-E02 | ✅ |
| Monstruo: fusión al encontrarse | `monster_agent.py` REQ-MON-E02 | ✅ |
| Monstruo: sin memoria | `monster_agent.py` REQ-MON-D01 | ✅ |
| Monstruo: sin orientación/dirección | `monster_agent.py` | ✅ |
| Contador T con T_inicio y T_fin | `simulator.py` REQ-TIME-01..03 | ✅ |
| Condiciones de término | `simulator.py` REQ-TIME-03 | ✅ |
| Robofagímetro del monstruo | `monster_agent.py` REQ-MON-02 | ✅ |
| Ontología + diagrama | `ontology.py` + sección 6.1 del informe | ✅ |
| Tabla percepción-acción Robot | `robot_agent.py` + informe sección 6.3.6 | ✅ |
| Tabla percepción-acción Monstruo | `monster_agent.py` + informe sección 6.3.6 | ✅ |
| Clasificación ambiente AIMA | Informe sección 6.3.5 + sección 12.3 de este doc | ✅ |
| Medida de racionalidad | `metrics.py` + sección 6 de este doc | ✅ |
| ¿Es episódico? Justificar | `experiments.py` REQ-EXP-06 + sección 12.3 | ✅ |
| ¿Entra a bucle infinito? | `robot_agent.py` Infinitómetro + REQ-EXP-03 | ✅ |
| Pruebas y corridas verificables | `experiments.py` + `main.py` | ✅ |
| Código fuente legible | Convención: PEP-8, docstrings, comentarios | ✅ |
| Google Drive con todos los archivos | Entrega manual por el grupo | ⚠️ |
| Bibliografía | Informe sección 12 | ⚠️ |

---

## DEPENDENCIAS PYTHON RECOMENDADAS

```
numpy          → operaciones matriciales, arrays 3D
matplotlib     → visualización 2D/3D y gráficas de métricas
plotly         → visualización 3D interactiva (alternativa a matplotlib)
pandas         → manejo de tablas de métricas y logs
networkx       → verificación de conectividad del mundo (BFS/DFS)
imageio        → exportación de GIFs animados
dataclasses    → definición de Perception, MemoryRecord, etc. (stdlib)
enum           → definición de tipos de celda, acciones, causas de muerte (stdlib)
json, csv      → exportación de logs y métricas (stdlib)
random         → generación aleatoria con semilla reproducible (stdlib)
copy           → deep copy de estados del mundo para snapshots
tqdm           → barras de progreso en experimentos batch
```

---

*Fin del documento de requerimientos.*
