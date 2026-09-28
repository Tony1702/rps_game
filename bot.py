from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes,
)
from config import BOT_TOKEN, ADMIN_TELEGRAM_USER_ID
from database.db import (
    init_db,
    get_participant,
    get_all_participants,
    create_participant,
    save_commitment,
    get_vote,
    save_reveal,
    count_verified_votes,
    get_voting_phase,
    set_voting_phase,
    determine_rule_result,
    get_voting_config,
    set_voting_config,
    start_new_round,
    save_round_result,
)
from crypto.commitment import generate_nonce, make_commitment, verify_commitment
from tournament.bracket import Tournament
from tournament.game_manager import GameManager
from tournament.rules import MOVES, get_rule_set
import random

active_rule_set = None
active_tournament = None
game_manager = GameManager()
active_matches = {}
active_byes = []

RULES = {
    1: "Rock, Paper, Scissors, Well",
    2: "Rock, Paper, Scissors, Lizard, Spock",
    3: "Rock, Paper, Scissors, Fire, Water",
}

def is_admin(user_id: int) -> bool:
    return str(user_id) == str(ADMIN_TELEGRAM_USER_ID)

def all_matches_finished():
    if not active_matches:
        return False

    return all(
        game_manager.is_finished(match_id)
        for match_id in active_matches
    )

def get_match_winners():
    winners = []

    for match in active_matches.values():
        winner = match.get("winner")

        if winner is not None:
            winners.append(winner)

    return winners

def start_round(rule_set):
    global active_matches, active_byes

    prepared = active_tournament.prepare_round()
    matches = active_tournament.create_matches()
    byes = active_tournament.get_bye_players()

    active_matches.clear()
    active_byes = list(byes)

    # Los matches de la ronda anterior ya terminaron.
    # Limpiamos su estado antes de crear los nuevos.
    game_manager.matches.clear()

    participant_telegram_ids = {
        participant["voting_credential"]: participant["telegram_user_id"]
        for participant in get_all_participants()
    }

    for index, (player_a, player_b) in enumerate(matches, start=1):
        match_id = f"match-{index}"

        game_manager.create_match(
            match_id,
            player_a,
            player_b,
            rule_set,
        )

        active_matches[match_id] = {
            "player_a": player_a,
            "player_b": player_b,
            "player_a_telegram_id": participant_telegram_ids[player_a],
            "player_b_telegram_id": participant_telegram_ids[player_b],
            "rule_set": rule_set,
        }

    return matches, byes

def rules_keyboard(options):
    labels = {
        1: "🪨 Rock, 🪣 Well",
        2: "🦎 Lizard, 🖖 Spock",
        3: "🔥 Fire, 💧 Water",
    }

    keyboard = []

    for option in options:
        keyboard.append([
            InlineKeyboardButton(
                labels[option],
                callback_data=f"vote:{option}"
            )
        ])

    return InlineKeyboardMarkup(keyboard)

def move_keyboard(match_id):
    match = active_matches[match_id]
    rule_set = match["rule_set"]

    rules = get_rule_set(rule_set)
    moves = rules["moves"]

    emojis = {
        1: "🪨",
        2: "📄",
        3: "✂️",
        4: {
            1: "🪣",  # Well
            2: "🦎",  # Lizard
            3: "🔥",  # Fire
        },
        5: {
            2: "🖖",  # Spock
            3: "💧",  # Water
        },
    }

    keyboard = []
    row = []

    for move_number, move_name in moves.items():
        emoji = emojis[move_number]

        if isinstance(emoji, dict):
            emoji = emoji[rule_set]

        row.append(
            InlineKeyboardButton(
                f"{emoji} {move_name}",
                callback_data=f"move:{match_id}:{move_number}",
            )
        )

        if len(row) == 2:
            keyboard.append(row)
            row = []

    if row:
        keyboard.append(row)

    return InlineKeyboardMarkup(keyboard)

def generate_voting_credential() -> str:
    import secrets
    return "VC-" + secrets.token_hex(16).upper()

def get_participant_credential(telegram_user_id):
    participant = get_participant(telegram_user_id)

    if not participant:
        return None

    return participant["voting_credential"]

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    participant = get_participant(user_id)
    if participant:
        await update.message.reply_text(
            "Ya estás registrado.\n\n"
            f"Tu credencial de votación es: "
            f"{participant['voting_credential']}\n"
            "Conserva esta credencial."
        )
        return
    voting_credential = generate_voting_credential()
    create_participant(user_id, voting_credential)
    await update.message.reply_text(
        "Registro completado.\n\n"
        f"Tu credencial de votación es: {voting_credential}\n\n"
        "Esta credencial se utiliza para interactuar con el módulo "
        "de votación sin utilizar directamente tu identidad de Telegram."
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("/start - Registro\n/vote 1|2|3 - Crear commitment\n/reveal VOTO NONCE - Revelar y verificar\n/status - Estado\n/results - Resultados verificados")

async def vote(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    participant = get_participant(user_id)

    if not participant:
        await update.message.reply_text(
            "Primero debes ejecutar /start."
        )
        return

    if get_voting_phase() != "commitment":
        await update.message.reply_text(
            "⚠️ La fase de votación por commitment no está activa."
        )
        return

    config = get_voting_config()

    await update.message.reply_text(
        "🎮 ELECCIÓN DE REGLAS\n\n"
        "Seleccione la variante que desea utilizar:",
        reply_markup=rules_keyboard(
            config["allowed_options"]
        )
    )

async def vote_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if get_voting_phase() != "commitment":
        await query.edit_message_text(
            "⚠️ La fase de commitment ya no está activa."
        )
        return

    user_id = query.from_user.id
    participant = get_participant(user_id)

    if not participant:
        await query.edit_message_text(
            "Primero debes registrarte utilizando /start."
        )
        return

    try:
        selected = int(query.data.split(":")[1])
    except (ValueError, IndexError):
        await query.edit_message_text(
            "La opción de voto no es válida."
        )
        return

    if selected not in RULES:
        await query.edit_message_text(
            "La opción seleccionada no es válida."
        )
        return

    config = get_voting_config()

    round_number = config["round_number"]

    if selected not in config["allowed_options"]:
        await query.edit_message_text(
            "⚠️ La opción seleccionada no está disponible "
            "en esta ronda de votación."
        )
        return

    nonce = generate_nonce()
    commitment = make_commitment(selected, nonce)

    saved = save_commitment(
        participant["voting_credential"],
        commitment,
        round_number
    )

    if not saved:
        await query.edit_message_text(
            "⚠️ Ya existe un commitment registrado para "
            f"tu credencial en la ronda {round_number}.\n\n"
            "El voto de esta ronda no puede ser modificado."
        )
        return

    await query.edit_message_text(
        "✓ Commitment generado correctamente.\n\n"
        f"Variante seleccionada: {RULES[selected]}\n\n"
        f"Commitment:\n{commitment}\n\n"
        "GUARDA estos datos para la fase de reveal:\n\n"
        f"Voto: {selected}\n"
        f"Nonce: {nonce}\n\n"
        "El commitment es el valor que queda registrado "
        "para verificar posteriormente tu voto."
    )

async def reveal(update: Update, context: ContextTypes.DEFAULT_TYPE):
    participant = get_participant(update.effective_user.id)

    config = get_voting_config()
    round_number = config["round_number"]

    if not participant:
        await update.message.reply_text("Primero ejecuta /start.")
        return
    if get_voting_phase() != "reveal":
        await update.message.reply_text(
            "⚠️ La fase de reveal no está activa."
        )
        return
    if len(context.args) != 2:
        await update.message.reply_text("Uso: /reveal VOTO NONCE")
        return
    try:
        selected = int(context.args[0])
    except ValueError:
        await update.message.reply_text("El voto debe ser 1, 2 o 3.")
        return
    nonce = context.args[1]
    record = get_vote(participant["voting_credential"], round_number)
    
    if not record:
        await update.message.reply_text(
            "No existe un commitment asociado a tu identificador."
        )
        return

    if record["verified"]:
        await update.message.reply_text(
            "⚠️ Este voto ya fue verificado y no puede volver a revelarse."
        )
        return

    valid = verify_commitment(record["commitment"], selected, nonce)
    save_reveal(
        participant["voting_credential"],
        round_number,
        selected,
        nonce,
        valid
    )
    await update.message.reply_text("✓ Reveal válido." if valid else "✗ Reveal inválido: no coincide con el commitment.")

async def status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    participant = get_participant(update.effective_user.id)

    config = get_voting_config()
    round_number = config["round_number"]

    if not participant:
        await update.message.reply_text("No estás registrado. Usa /start.")
        return
    record = get_vote(participant["voting_credential"], round_number)
    if not record:
        await update.message.reply_text(f"Credencial de votación: {participant['voting_credential']}\nEstado: sin commitment")
        return
    state = "verificado" if record["verified"] else ("revelado pero inválido" if record["revealed_vote"] is not None else "pendiente de reveal")
    await update.message.reply_text(f"Credencial de votación: {participant['voting_credential']}\nEstado: {state}\nCommitment: {record['commitment']}")

async def results(update: Update, context: ContextTypes.DEFAULT_TYPE):
    config = get_voting_config()
    round_number = config["round_number"]

    counts = count_verified_votes(round_number)

    if not counts:
        await update.message.reply_text(
            f"Todavía no existen votos verificados en la ronda {round_number}."
        )
        return

    lines = [
        f"Resultados de votos verificados — Ronda {round_number}:"
    ]

    for option, total in counts:
        lines.append(
            f"{option}: {RULES.get(option, 'Desconocida')} -> {total} voto(s)"
        )

    await update.message.reply_text("\n".join(lines))

async def phase_commitment(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        await update.message.reply_text(
            "⛔ No tienes permisos para realizar esta operación."
        )
        return

    set_voting_phase("commitment")

    await update.message.reply_text(
        "🟢 Fase de COMMITMENT activada.\n\n"
        "Los participantes pueden registrar sus commitments."
    )

async def phase_reveal(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        await update.message.reply_text(
            "⛔ No tienes permisos para realizar esta operación."
        )
        return

    set_voting_phase("reveal")

    await update.message.reply_text(
        "🟡 Fase de REVEAL activada.\n\n"
        "Los participantes pueden revelar sus votos."
    )

async def phase_closed(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        await update.message.reply_text(
            "⛔ No tienes permisos para realizar esta operación."
        )
        return

    set_voting_phase("closed")

    await update.message.reply_text(
        "🔴 Votación CERRADA.\n\n"
        "No se aceptan nuevos commitments ni reveals."
    )

async def phase(update: Update, context: ContextTypes.DEFAULT_TYPE):
    current_phase = get_voting_phase()

    labels = {
        "commitment": "🟢 COMMITMENT",
        "reveal": "🟡 REVEAL",
        "closed": "🔴 CERRADA",
    }

    await update.message.reply_text(
        f"Estado actual de la votación:\n\n"
        f"{labels[current_phase]}"
    )

async def rule_results(update: Update, context: ContextTypes.DEFAULT_TYPE):
    config = get_voting_config()
    round_number = config["round_number"]

    result = determine_rule_result(round_number)

    if result["status"] == "tie":
        save_round_result(
            round_number,
            "tie",
            tied_options=result["tied_options"]
        )

    elif result["status"] == "winner":
        save_round_result(
            round_number,
            "winner",
            winner=result["winner"]
        )

    lines = [
        f"📊 RESULTADO DE LA VOTACIÓN DE REGLAS — RONDA {round_number}\n"
    ]

    counts = result["counts"]

    for option, description in RULES.items():
        total = counts.get(option, 0)
        lines.append(
            f"{option}. {description} → {total} voto(s)"
        )

    if result["status"] == "no_votes":
        lines.append(
            "\n⚠️ No existen votos verificados."
        )

    elif result["status"] == "tie":
        tied = ", ".join(
            str(option)
            for option in result["tied_options"]
        )

        lines.append(
            f"\n⚠️ EMPATE\n"
            f"Opciones empatadas: {tied}"
        )

    elif result["status"] == "winner":
        winner = result["winner"]

        lines.append(
            f"\n✓ Resultado: opción {winner}\n"
            f"Reglas seleccionadas: {RULES[winner]}"
        )

    await update.message.reply_text(
        "\n".join(lines)
    )

async def start_tiebreak(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        await update.message.reply_text(
            "⛔ No tienes permisos para realizar esta operación."
        )
        return

    config = get_voting_config()
    current_round = config["round_number"]

    result = determine_rule_result(current_round)

    if result["status"] == "tie":
        save_round_result(
            current_round,
            "tie",
            tied_options=result["tied_options"]
        )

    if result["status"] == "no_votes":
        await update.message.reply_text(
            "⚠️ No existen votos verificados en la ronda actual."
        )
        return

    if result["status"] == "winner":
        winner = result["winner"]

        await update.message.reply_text(
            "✓ No es necesario realizar un desempate.\n\n"
            f"Ganador actual: opción {winner}\n"
            f"Reglas: {RULES[winner]}"
        )
        return

    tied_options = result["tied_options"]

    if len(tied_options) < 2:
        await update.message.reply_text(
            "⚠️ No existen suficientes opciones empatadas "
            "para iniciar un desempate."
        )
        return

    new_round = current_round + 1

    start_new_round(
        new_round,
        tied_options
    )

    options_text = "\n".join(
        f"{option}. {RULES[option]}"
        for option in tied_options
    )

    await update.message.reply_text(
        "🔄 NUEVA RONDA DE DESEMPATE\n\n"
        f"Ronda anterior: {current_round}\n"
        f"Nueva ronda: {new_round}\n\n"
        "Opciones que continúan:\n"
        f"{options_text}\n\n"
        "🟢 La fase de COMMITMENT está activa."
    )

async def start_tournament(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global active_tournament, active_rule_set

    user_id = update.effective_user.id

    if not is_admin(user_id):
        await update.message.reply_text(
            "No tienes permisos para iniciar el torneo."
        )
        return

    if active_tournament is not None:
        await update.message.reply_text(
            "Ya existe un torneo activo."
        )
        return

    if len(context.args) > 2:
        await update.message.reply_text(
            "Uso:\n"
            "/start_tournament\n"
            "/start_tournament NUMERO\n"
            "/start_tournament CREDENCIAL_A CREDENCIAL_B"
        )
        return

    participants = get_all_participants()

    if len(participants) < 2:
        await update.message.reply_text(
            "Se necesitan al menos 2 participantes para iniciar el torneo."
        )
        return

    # ---------------------------------------------------------
    # Selección de participantes
    # ---------------------------------------------------------

    if len(context.args) == 2:
        # Selección explícita mediante credenciales
        requested_credentials = context.args

        if requested_credentials[0] == requested_credentials[1]:
            await update.message.reply_text(
                "Las dos credenciales deben ser diferentes."
            )
            return

        participants_by_credential = {
            participant["voting_credential"]: participant
            for participant in participants
        }

        missing_credentials = [
            credential
            for credential in requested_credentials
            if credential not in participants_by_credential
        ]

        if missing_credentials:
            await update.message.reply_text(
                "No se encontraron las siguientes credenciales:\n\n"
                + "\n".join(
                    f"• `{credential}`"
                    for credential in missing_credentials
                ),
                parse_mode="Markdown"
            )
            return

        participants = [
            participants_by_credential[credential]
            for credential in requested_credentials
        ]

    elif len(context.args) == 1:
        # Selección aleatoria mediante cantidad
        try:
            requested_count = int(context.args[0])
        except ValueError:
            await update.message.reply_text(
                "El argumento debe ser un número entero "
                "o dos credenciales de participantes."
            )
            return

        if requested_count < 2:
            await update.message.reply_text(
                "El torneo debe tener al menos 2 participantes."
            )
            return

        if requested_count > len(participants):
            await update.message.reply_text(
                f"No hay suficientes participantes registrados.\n\n"
                f"Participantes disponibles: {len(participants)}\n"
                f"Solicitados: {requested_count}"
            )
            return

        participants = random.sample(
            participants,
            requested_count
        )

    # Si no se proporcionaron argumentos, se utilizan todos.
    participant_ids = [
        participant["voting_credential"]
        for participant in participants
    ]

    # ---------------------------------------------------------
    # Obtener la variante ganadora de la votación
    # ---------------------------------------------------------

    config = get_voting_config()
    round_number = config["round_number"]

    rule_result = determine_rule_result(round_number)

    if rule_result["status"] == "no_votes":
        await update.message.reply_text(
            "⚠️ No existen votos verificados para seleccionar "
            "las reglas del torneo."
        )
        return

    if rule_result["status"] == "tie":
        tied = ", ".join(
            str(option)
            for option in rule_result["tied_options"]
        )

        await update.message.reply_text(
            "⚠️ No se puede iniciar el torneo porque existe "
            "un empate en la votación de reglas.\n\n"
            f"Opciones empatadas: {tied}\n\n"
            "Realiza el desempate antes de iniciar el torneo."
        )
        return

    rule_set = rule_result["winner"]

    active_rule_set = rule_set

    active_tournament = Tournament(participant_ids)

    matches, byes = start_round(active_rule_set)

    message = (
        "🏆 *Primera ronda preparada*\n\n"
        f"Reglas seleccionadas: {RULES[rule_set]}\n"
        f"Participantes: {len(participant_ids)}\n"
        f"Matches: {len(matches)}\n"
    )

    if byes:
        message += "\n🎫 *Bye:*\n"
        for player in byes:
            message += f"• `{player}` avanza automáticamente\n"

    message += "\n⚔️ *Enfrentamientos:*\n"

    for index, (player_a, player_b) in enumerate(matches, start=1):
        message += (
            f"{index}. `{player_a}` vs `{player_b}`\n"
        )

    message += "\nLos matches serán al mejor de 3."

    await update.message.reply_text(
        message,
        parse_mode="Markdown"
    )

async def play_match_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):
    user_id = update.effective_user.id

    credential = get_participant_credential(user_id)

    if not credential:
        await update.message.reply_text(
            "No estás registrado como participante."
        )
        return

    if not active_matches:
        await update.message.reply_text(
            "No hay matches activos."
        )
        return

    for match_id, match in active_matches.items():
        match_number = match_id.split("-")[1]

        if game_manager.is_finished(match_id):
            if credential in (match["player_a"], match["player_b"]):
                await update.message.reply_text(
                    f"🏁 Match {match_number} ya terminó.\n\n"
                    "No puedes realizar más jugadas en este match."
                )
                return

        if credential == match["player_a"]:
            await update.message.reply_text(
                f"🎮 Match {match_number}\n\n"
                "Eres el jugador A.\n\n"
                "Selecciona tu jugada:",
                reply_markup=move_keyboard(match_id)
            )
            return

        if credential == match["player_b"]:
            await update.message.reply_text(
                f"🎮 Match {match_number}\n\n"
                "Eres el jugador B.\n\n"
                "Selecciona tu jugada:",
                reply_markup=move_keyboard(match_id)
            )
            return

    await update.message.reply_text(
        "No tienes un match activo en esta ronda."
    )

async def move_callback(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):
    query = update.callback_query
    await query.answer()

    data = query.data

    _, match_id, move_text = data.split(":")

    move = int(move_text)

    user_id = query.from_user.id

    credential = get_participant_credential(user_id)

    if not credential:
        await query.edit_message_text(
            "No estás registrado como participante."
        )
        return

    if match_id not in active_matches:
        await query.edit_message_text(
            "El match ya no está activo."
        )
        return

    match = active_matches[match_id]

    if credential not in (
        match["player_a"],
        match["player_b"],
    ):
        await query.edit_message_text(
            "No perteneces a este match."
        )
        return

    try:
        result = game_manager.submit_move(
            match_id,
            credential,
            move,
        )
    except ValueError as error:
        await query.answer(
            str(error),
            show_alert=True,
        )
        return

    if result is None:
        await query.edit_message_text(
            "✅ Tu jugada fue registrada.\n\n"
            "Esperando la jugada del otro participante."
        )
        return

    state = game_manager.get_match(match_id)

    move_a, move_b = state["results"][-1]

    round_number = len(state["results"])

    if result == "A":
        round_result = "🏆 Ganó el Jugador A"
    elif result == "B":
        round_result = "🏆 Ganó el Jugador B"
    else:
        round_result = "🤝 Empate"

    score_text = (
        f"Jugador A: {state['wins_a']}\n"
        f"Jugador B: {state['wins_b']}"
    )

    if state["finished"]:
        if state["winner"] == match["player_a"]:
            match_winner = "Jugador A"
        else:
            match_winner = "Jugador B"

        active_matches[match_id]["winner"] = state["winner"]

        if all_matches_finished():
            winners = get_match_winners()

            winners.extend(active_byes)

            active_tournament.advance(winners)

            if active_tournament.is_finished():
                tournament_winner = active_tournament.get_winner()

                participant_telegram_ids = {
                    participant["voting_credential"]: participant["telegram_user_id"]
                    for participant in get_all_participants()
                }

                winner_telegram_id = participant_telegram_ids[tournament_winner]

                await context.bot.send_message(
                    chat_id=winner_telegram_id,
                    text=(
                        "🏆 ¡Has ganado el torneo!\n\n"
                        "Eres el campeón del torneo."
                    )
                )

            else:
                start_round(match["rule_set"])

                for next_match_id, next_match in active_matches.items():
                    match_number = next_match_id.split("-")[1]

                    await context.bot.send_message(
                        chat_id=next_match["player_a_telegram_id"],
                        text=(
                            f"🎮 Nueva ronda\n\n"
                            f"Match {match_number}\n"
                            "Eres el jugador A.\n\n"
                            "Usa /play_match para realizar tu jugada."
                        )
                    )

                    await context.bot.send_message(
                        chat_id=next_match["player_b_telegram_id"],
                        text=(
                            f"🎮 Nueva ronda\n\n"
                            f"Match {match_number}\n"
                            "Eres el jugador B.\n\n"
                            "Usa /play_match para realizar tu jugada."
                        )
                    )

        final_message = (
            f"🏆 Match terminado\n\n"
            f"Ganador: {match_winner}\n\n"
            f"📊 Marcador final:\n"
            f"Jugador A: {state['wins_a']}\n"
            f"Jugador B: {state['wins_b']}"
        )

        await context.bot.send_message(
            chat_id=match["player_a_telegram_id"],
            text=final_message
        )

        await context.bot.send_message(
            chat_id=match["player_b_telegram_id"],
            text=final_message
        )

        await query.edit_message_text(
            "✅ Tu jugada fue registrada.\n\n"
            "El match ha terminado."
        )

        return

    rules = get_rule_set(state["rule_set"])

    result_message = (
        f"🎮 Resultado de la ronda {round_number}\n\n"
        f"Jugador A: {rules['moves'][move_a]}\n"
        f"Jugador B: {rules['moves'][move_b]}\n\n"
        f"{round_result}\n\n"
        f"📊 Marcador:\n"
        f"{score_text}"
    )

    await context.bot.send_message(
        chat_id=match["player_a_telegram_id"],
        text=result_message
    )

    await context.bot.send_message(
        chat_id=match["player_b_telegram_id"],
        text=result_message
    )

    await query.edit_message_text(
        "✅ Tu jugada fue registrada.\n\n"
        "La ronda ha terminado. Revisa el resultado y el marcador."
    )

def main():
    init_db()
    application = Application.builder().token(BOT_TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("vote", vote))

    application.add_handler(
        CallbackQueryHandler(
            vote_callback,
            pattern=r"^vote:[123]$"
        )
    )

    application.add_handler(
        CallbackQueryHandler(
            move_callback,
            pattern=r"^move:match-\d+:[1-5]$"
        )
    )

    application.add_handler(CommandHandler("reveal", reveal))
    application.add_handler(CommandHandler("status", status))
    application.add_handler(CommandHandler("results", results))

    application.add_handler(
        CommandHandler("start_tournament", start_tournament)
    )

    application.add_handler(
        CommandHandler("phase_commitment", phase_commitment)
    )

    application.add_handler(
        CommandHandler("phase_reveal", phase_reveal)
    )

    application.add_handler(
        CommandHandler("phase_closed", phase_closed)
    )

    application.add_handler(
        CommandHandler("phase", phase)
    )

    application.add_handler(
        CommandHandler("rule_results", rule_results)
    )

    application.add_handler(
        CommandHandler("start_tiebreak", start_tiebreak)
    )

    application.add_handler(
        CommandHandler("play_match", play_match_command)
    )

    print("Bot iniciado...")
    application.run_polling()

if __name__ == "__main__":
    main()
