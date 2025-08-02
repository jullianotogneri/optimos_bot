import os
from telegram import Update, KeyboardButton, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import (
    ApplicationBuilder, CommandHandler, ContextTypes, MessageHandler, filters, ConversationHandler
)
import googlemaps
from geopy.distance import geodesic

# Carregar variáveis de ambiente
TOKEN = os.getenv("TOKEN")
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
gmaps = googlemaps.Client(key=GOOGLE_API_KEY)

# Etapas da conversa
(
    INICIAR, NOME, EMBARQUE, DESTINO, PASSAGEIROS, BAGAGEM, CONFIRMACAO
) = range(7)

# Início com botão
async def iniciar(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    keyboard = [[KeyboardButton("🚗 Solicitar Corrida")]]
    await update.message.reply_text("Olá! Toque no botão abaixo para começar:", reply_markup=ReplyKeyboardMarkup(keyboard, one_time_keyboard=True))
    return INICIAR

async def nome(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text("Qual o seu nome?", reply_markup=ReplyKeyboardRemove())
    return NOME

async def salvar_nome(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data["nome"] = update.message.text
    await update.message.reply_text("Informe o local de EMBARQUE (nome ou endereço):")
    return EMBARQUE

async def salvar_embarque(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data["embarque"] = update.message.text
    await update.message.reply_text("Informe o local de DESTINO (nome ou endereço):")
    return DESTINO

async def salvar_destino(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data["destino"] = update.message.text

    keyboard = [[KeyboardButton("1"), KeyboardButton("2")],
                [KeyboardButton("3"), KeyboardButton("4")]]
    await update.message.reply_text("Quantos passageiros?", reply_markup=ReplyKeyboardMarkup(keyboard, one_time_keyboard=True))
    return PASSAGEIROS

async def salvar_passageiros(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data["passageiros"] = int(update.message.text)

    keyboard = [[KeyboardButton("✅ Sim"), KeyboardButton("❌ Não")]]
    await update.message.reply_text("Leva bagagem ou compras?", reply_markup=ReplyKeyboardMarkup(keyboard, one_time_keyboard=True))
    return BAGAGEM

async def salvar_bagagem(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data["bagagem"] = update.message.text == "✅ Sim"

    origem = gmaps.geocode(f"{context.user_data['embarque']}, Cachoeiro de Itapemirim - ES")[0]["geometry"]["location"]
    destino = gmaps.geocode(f"{context.user_data['destino']}, Cachoeiro de Itapemirim - ES")[0]["geometry"]["location"]

    origem_coords = (origem["lat"], origem["lng"])
    destino_coords = (destino["lat"], destino["lng"])
    distancia_km = round(geodesic(origem_coords, destino_coords).km, 2)

    passageiros = context.user_data["passageiros"]
    extra_passageiro = max(0, passageiros - 2) * 0.50 * distancia_km
    extra_bagagem = 0.50 * distancia_km if context.user_data["bagagem"] else 0

    valor_corrida = 2.50 * distancia_km + extra_passageiro + extra_bagagem
    valor_corrida = max(valor_corrida, 9.00)

    context.user_data["distancia"] = distancia_km
    context.user_data["valor"] = round(valor_corrida, 2)

    resumo = (
        f"Resumo da corrida:\n"
        f"🧍 Cliente: {context.user_data['nome']}\n"
        f"📍 De: {context.user_data['embarque']}\n"
        f"🏁 Para: {context.user_data['destino']}\n"
        f"👥 Passageiros: {passageiros}\n"
        f"🧳 Bagagem: {'Sim' if context.user_data['bagagem'] else 'Não'}\n"
        f"📏 Distância: {distancia_km:.2f} km\n"
        f"💰 Valor estimado: R$ {valor_corrida:.2f}\n"
        f"Pagamento: PIX (28999642265), Dinheiro ou Cartão."
    )

    keyboard = [[KeyboardButton("✅ Confirmar"), KeyboardButton("❌ Cancelar")]]
    await update.message.reply_text(resumo, reply_markup=ReplyKeyboardMarkup(keyboard, one_time_keyboard=True))
    return CONFIRMACAO

async def confirmar(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if update.message.text == "✅ Confirmar":
        await update.message.reply_location(latitude=-20.8483, longitude=-41.1129)
        await update.message.reply_text("🚗 O motorista está a caminho! Obrigado por escolher a Optimos.")
    else:
        await update.message.reply_text("👍 Corrida cancelada. Estamos à disposição!")
    return ConversationHandler.END

async def cancelar(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text("Atendimento cancelado.")
    return ConversationHandler.END

if __name__ == "__main__":
    app = ApplicationBuilder().token(TOKEN).build()

    conv = ConversationHandler(
        entry_points=[MessageHandler(filters.Regex("🚗 Solicitar Corrida"), nome)],
        states={
            INICIAR: [MessageHandler(filters.Regex("🚗 Solicitar Corrida"), nome)],
            NOME: [MessageHandler(filters.TEXT & ~filters.COMMAND, salvar_nome)],
            EMBARQUE: [MessageHandler(filters.TEXT & ~filters.COMMAND, salvar_embarque)],
            DESTINO: [MessageHandler(filters.TEXT & ~filters.COMMAND, salvar_destino)],
            PASSAGEIROS: [MessageHandler(filters.Regex("^[1-4]$"), salvar_passageiros)],
            BAGAGEM: [MessageHandler(filters.Regex("^(✅ Sim|❌ Não)$"), salvar_bagagem)],
            CONFIRMACAO: [MessageHandler(filters.Regex("^(✅ Confirmar|❌ Cancelar)$"), confirmar)],
        },
        fallbacks=[CommandHandler("cancelar", cancelar)]
    )

    app.add_handler(CommandHandler("start", iniciar))
    app.add_handler(conv)
    app.run_polling()
