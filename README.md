# Bot de Voto Electrónico - MVP

Basado en los requisitos del documento Voto Electronico.txt.

## Instalación en WSL2/Ubuntu

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

Edita `.env` y coloca el token de Telegram.

## Pruebas

```bash
pytest -q
```

## Ejecutar

```bash
python3 bot.py
```

## Comandos

- `/start`
- `/vote 1`
- `/vote 2`
- `/vote 3`
- `/reveal VOTO NONCE`
- `/status`
- `/results`

## Criptografía del MVP

`C = SHA256(voto || nonce)`.

El commitment multiplicativo `C(x;r)=x*r` de la pregunta teórica no se utiliza porque no cumple hiding ni binding.

## Limitación de esta primera versión

El backend mantiene una tabla que relaciona Telegram user ID con el identificador anónimo. Por tanto, todavía no proporciona anonimato fuerte frente al propio backend. La siguiente fase debe separar el emisor de identidades del módulo de votación/verificación y definir qué información observa cada actor.
