# Bot de Voto Electrónico para Torneos RPS

Sistema de votación electrónica y gestión de torneos de Rock, Paper, Scissors mediante un bot de Telegram.

El proyecto implementa un mecanismo de votación basado en **commitment/reveal** para seleccionar la variante de reglas que será utilizada durante el torneo, junto con un sistema de emparejamiento y ejecución de partidas.

---

## Estado del proyecto

Actualmente el sistema cuenta con:

- Registro de participantes.
- Credenciales de votación anónimas.
- Separación de las bases de datos de identidad y votación.
- Esquema de votación commitment/reveal.
- Verificación de commitments mediante SHA-256.
- Soporte para múltiples rondas de votación.
- Detección de ganador, empate y ausencia de votos.
- Selección de una de tres variantes de RPS.
- Torneos con 2 o más participantes.
- Emparejamiento automático.
- Manejo de número impar de participantes mediante bye.
- Partidas al mejor de 3 rondas.
- Avance automático de ganadores.
- Determinación y anuncio del campeón.
- 97 pruebas automatizadas pasando.

---

## Requisitos

- Windows
- Python 3.14 o compatible
- Visual Studio Code
- Cuenta/bot de Telegram
- Token de Telegram Bot API

Las dependencias del proyecto se encuentran en `requirements.txt`.

---

## Instalación

### 1. Clonar el repositorio

```bash
git clone <URL_DEL_REPOSITORIO>
cd rps_game
```

### 2. Crear el entorno virtual

```bash
python -m venv .venv
```

### 3. Activar el entorno virtual

```bash
.venv\Scripts\activate
```

### 4. Instalar las dependencias

```bash
pip install -r requirements.txt
```

### 5. Configurar las variables de entorno

Crear el archivo `.env` a partir de `.env.example`:

```bash
copy .env.example .env
```

Editar `.env` y configurar:

```text
TELEGRAM_BOT_TOKEN=TOKEN_DEL_BOT
ADMIN_TELEGRAM_USER_ID=ID_DEL_ADMINISTRADOR
```

El archivo `.env` contiene información sensible y no debe incluirse en el repositorio.

---

## Ejecución

Con el entorno virtual activado:

```bash
python bot.py
```

Si la configuración es correcta, el bot iniciará y quedará disponible en Telegram.

---

# Arquitectura

El proyecto está organizado en varios módulos:

```text
rps_game/
│
├── crypto/
│   └── commitment.py
│
├── database/
│   └── db.py
│
├── tournament/
│   ├── rules.py
│   ├── match.py
│   ├── bracket.py
│   ├── bye.py
│   ├── pairing.py
│   └── game_manager.py
│
├── voting/
│   └── __init__.py
│
├── tests/
│   ├── test_commitment.py
│   ├── test_rpsls.py
│   ├── test_match.py
│   ├── test_bracket.py
│   ├── test_bye.py
│   ├── test_pairing.py
│   ├── test_game_manager.py
│   ├── test_tournament_integration.py
│   └── test_database.py
│
├── data/
│   ├── identity.db
│   └── voting.db
│
├── bot.py
├── config.py
├── requirements.txt
└── pytest.ini
```

---

# Sistema de votación

La selección de las reglas del torneo utiliza un esquema de dos fases:

```text
Participante
    │
    ▼
Credencial anónima
    │
    ▼
Commitment
    │
    ▼
Cierre de commitment
    │
    ▼
Reveal
    │
    ▼
Verificación
    │
    ▼
Conteo de votos
    │
    ▼
Selección de variante
```

## Commitment

El voto no se almacena directamente durante la primera fase.

Se genera un nonce aleatorio y se calcula:

```text
C = SHA256(voto || nonce)
```

El participante conserva el voto y el nonce para poder realizar posteriormente el reveal.

## Reveal

Durante la fase de reveal, el participante proporciona:

```text
voto + nonce
```

El sistema vuelve a calcular el commitment y lo compara con el valor almacenado.

Solamente los votos cuya verificación sea correcta son considerados para el resultado.

## Empates

Si dos o más opciones obtienen la misma cantidad de votos, la ronda se considera empatada y no se selecciona automáticamente una variante.

El sistema permite iniciar una nueva ronda de votación para resolver la selección.

---

# Variantes del juego

El sistema soporta tres conjuntos de reglas.

## Variante 1 — Rock, Paper, Scissors, Well

```text
1. Rock
2. Paper
3. Scissors
4. Well
```

Relaciones:

```text
Rock     → Scissors
Paper    → Rock, Well
Scissors → Paper
Well     → Rock, Scissors
```

## Variante 2 — Rock, Paper, Scissors, Lizard, Spock

```text
1. Rock
2. Paper
3. Scissors
4. Lizard
5. Spock
```

Relaciones:

```text
Rock     → Scissors, Lizard
Paper    → Rock, Spock
Scissors → Paper, Lizard
Lizard   → Paper, Spock
Spock    → Rock, Scissors
```

## Variante 3 — Rock, Paper, Scissors, Fire, Water

```text
1. Rock
2. Paper
3. Scissors
4. Fire
5. Water
```

Relaciones:

```text
Rock     → Scissors, Water
Paper    → Rock, Water
Scissors → Paper, Water
Fire     → Rock, Paper, Scissors
Water    → Fire
```

La variante seleccionada mediante la votación se mantiene durante todo el torneo.

---

# Sistema de torneo

Una vez determinada la variante de juego, se crea el torneo.

## Participantes

El sistema permite seleccionar participantes registrados y generar automáticamente los enfrentamientos.

## Emparejamiento

Los participantes son organizados en partidas de eliminación.

Cuando existe un número impar de participantes, el sistema asigna un **bye**, permitiendo que uno de ellos avance automáticamente a la siguiente etapa.

Ejemplo:

```text
3 participantes

        ┌── Participante A
        │
        ├── Match
        │
        └── Participante B
                 │
                 ▼
              Ganador
                 │
Participante C ──┘
      BYE
```

## Partidas

Cada enfrentamiento utiliza un formato de mejor de 3.

El participante que obtiene dos victorias gana el enfrentamiento.

La variante seleccionada determina las jugadas disponibles y las relaciones de victoria.

## Avance

El ganador de cada enfrentamiento avanza automáticamente a la siguiente etapa del torneo.

El proceso continúa hasta determinar un único campeón.

---

# Comandos del bot

Entre los comandos principales se encuentran:

### Inicio

```text
/start
```

Inicia la interacción con el bot y registra al participante cuando corresponde.

### Votación

```text
/vote 1
/vote 2
/vote 3
```

Realiza un commitment para la variante seleccionada.

### Reveal

```text
/reveal VOTO NONCE
```

Revela el voto y permite verificar el commitment.

### Estado

```text
/status
```

Muestra el estado de la participación en la votación.

### Resultados

```text
/results
```

Muestra los resultados de los votos verificados.

### Resultado de reglas

```text
/rule_results
```

Muestra el resultado de la votación utilizada para seleccionar la variante.

### Torneo

```text
/start_tournament
```

Inicia el torneo utilizando la variante seleccionada.

También permite especificar participantes cuando corresponde al flujo de administración del torneo.

---

# Base de datos

El sistema utiliza SQLite y mantiene separadas las bases de datos de identidad y votación.

## `identity.db`

Almacena información relacionada con la identidad de los participantes y su credencial de votación.

## `voting.db`

Almacena información relacionada con:

- Commitments.
- Reveals.
- Verificación de votos.
- Estado de la votación.
- Configuración de la ronda.
- Historial de rondas.
- Resultados.

La separación permite mantener aislada la información de identidad respecto de la información propia del proceso de votación.

---

# Criptografía

El sistema utiliza SHA-256 para generar commitments:

```text
C = SHA256(voto || nonce)
```

El nonce se genera aleatoriamente utilizando el módulo `secrets` de Python.

El commitment multiplicativo:

```text
C(x;r) = x * r
```

analizado durante la etapa teórica no se utiliza en la implementación debido a que no proporciona las propiedades de hiding y binding requeridas para un esquema de commitment adecuado.

---

# Pruebas

El proyecto utiliza `pytest`.

Para ejecutar todas las pruebas:

```bash
pytest -q
```

Estado actual:

```text
97 passed
```

Las pruebas cubren, entre otros aspectos:

- Commitment y verificación.
- Reglas RPS.
- Partidas.
- Brackets.
- Bye.
- Emparejamiento.
- Game Manager.
- Integración del torneo.
- Persistencia y operaciones de base de datos.

---

# Tecnologías utilizadas

- Python
- python-telegram-bot
- SQLite
- SHA-256
- pytest
- python-dotenv
- Telegram Bot API

---

# Licencia

Este proyecto es de carácter académico y experimental.
