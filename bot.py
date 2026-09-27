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

active_tournament = None
game_manager = GameManager()

RULES = {
    1: "Rock, Paper, Scissors, Fire, Well",
    2: "Rock, Paper, Scissors, Lizard, Spock",
    3: "Rock, Paper, Scissors, Fire, Water",
}

def is_admin(user_id: int) -> bool:
    return str(user_id) == str(ADMIN_TELEGRAM_USER_ID)

def rules_keyboard(options):
    labels = {
        1: "🪨 Fire, 🪣 Well",
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

def generate_voting_credential() -> str:
    import secrets
    return "VC-" + secrets.token_hex(16).upper()

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
    global active_tournament

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

    participants = get_all_participants()

    if len(participants) < 2:
        await update.message.reply_text(
            "No hay suficientes participantes para iniciar el torneo.\n"
            f"Participantes registrados: {len(participants)}"
        )
        return

    participant_ids = [
        participant["voting_credential"]
        for participant in participants
    ]

    active_tournament = Tournament(participant_ids)

    prepared = active_tournament.prepare_round()
    matches = active_tournament.create_matches()
    byes = active_tournament.get_bye_players()

    message = (
        "🏆 *Primera ronda preparada*\n\n"
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

    print("Bot iniciado...")
    application.run_polling()

if __name__ == "__main__":
    main()
