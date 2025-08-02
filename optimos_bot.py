import os
import logging
from telegram import (
    Update,
    ReplyKeyboardMarkup,
    KeyboardButton,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
    CallbackQueryHandler,
    ConversationHandler,
)
import googlemaps
from geopy.distance import geodesic

# Ative o log para ver erros no Render
logging.basicConfig(level=logging.INFO)

# Tokens (você deve configurar isso como variáveis de ambiente no Render)
TELEGRAM_TOKEN = os.getenv("TOKEN")
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

gmaps = googlemaps.Client(key=GOOGLE_API_KEY)

# Estados da conversa
(
    NOME,
    EMBARQUE,
    DESTINO,
    PASSAGEIROS,
    BAGAGEM,
    CONFIRMACAO,
) = range(6)

# Funções auxiliares
def calcular_distancia(origem, destino):
    resultado = gmaps.distance_matrix(origem, destino, mode="driving")
    metros = resultado["rows"][0]["elements"][0]["distance"]["value"]
    return metros / 1000  # km

def calcular_valor(distancia, passageiros, tem_bagagem):
    valor_km = 2.5
    valor = distancia * valor_km
    if passageiros > 2:
        valor += (passageiros - 2) * 0.5 * distancia
    if tem_bagagem:
        valor += 0.5 * distancia
    return max(valor, 9.0)

# Início
async def iniciar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    botao = [[KeyboardButton("🚗 Solicitar Corrida")]]
    await update.message.reply_text(
        "Olá! Bem-vindo ao Bot de Corridas Optimos.\nClique no botão abaixo para iniciar.",
        reply_markup=ReplyKeyboardMarkup(botao, one_time_keyboard=True, resize_keyboard=True),
    )
    return NOME

async def receber_nome(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()
    context.user_data["nome"] = update.message.text
    await update.message.reply_text("Qual o endereço de embarque?")
    return EMBARQUE

async def receber_embarque(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["embarque"] = update.message.text
    await update.message.reply_text("Qual o destino da sua viagem?")
    return DESTINO

async def receber_destino(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["destino"] = update.message.text
    botoes = [
        [InlineKeyboardButton("1", callback_data="1"),
         InlineKeyboardButton("2", callback_data="2"),
         InlineKeyboardButton("3", callback_data="3"),
         InlineKeyboardButton("4", callback_data="4")]
    ]
    await update.message.reply_text(
        "Quantos passageiros vão na corrida?",
        reply_markup=InlineKeyboardMarkup(botoes),
    )
    return PASSAGEIROS

async def escolher_passageiros(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    context.user_data["passageiros"] = int(query.data)

    botoes = [
        [InlineKeyboardButton("Sim", callback_data="sim"),
         InlineKeyboardButton("Não", callback_data="nao")]
    ]
    await query.edit_message_text(
        "Vai levar bagagem ou compras?",
        reply_markup=InlineKeyboardMarkup(botoes),
    )
    return BAGAGEM

async def escolher_bagagem(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    context.user_data["bagagem"] = query.data == "sim"

    origem = context.user_data["embarque"]
    destino = context.user_data["destino"]
    passageiros = context.user_data["passageiros"]
    tem_bagagem = context.user_data["bagagem"]

    distancia = calcular_distancia(origem, destino)
    valor = calcular_valor(distancia, passageiros, tem_bagagem)

    resumo = (
        f"👤 Cliente: {context.user_data['nome']}\n"
        f"📍 Embarque: {origem}\n"
        f"🏁 Destino: {destino}\n"
        f"👥 Passageiros: {passageiros}\n"
        f"🧳 Bagagem/Compras: {'Sim' if tem_bagagem else 'Não'}\n"
        f"📏 Distância estimada: {distancia:.2f} km\n"
        f"💵 Valor estimado: R$ {valor:.2f}\n\n"
        f"Formas de pagamento: PIX (28999642265), Dinheiro ou Cartão."
    )

    botoes = [
        [InlineKeyboardButton("✅ Aceitar Corrida", callback_data="aceitar")],
        [InlineKeyboardButton("❌ Cancelar", callback_data="cancelar")]
    ]

    await query.edit_message_text(
        resumo,
        reply_markup=InlineKeyboardMarkup(botoes),
    )

    return CONFIRMACAO

async def confirmar_corrida(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == "aceitar":
        await query.edit_message_text("🚗 O motorista está a caminho!\n🌐 Acompanhe a localização em tempo real: https://maps.app.goo.gl/FakeLocationLink")
    else:
        await query.edit_message_text("Corrida cancelada. Obrigado por usar o Bot Optimos! 👋")

    return ConversationHandler.END

async def cancelar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Atendimento cancelado. Envie 🚗 para começar novamente.")
    return ConversationHandler.END

# Main
if __name__ == "__main__":
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()

    conversa = ConversationHandler(
        entry_points=[
            MessageHandler(filters.Regex("🚗"), receber_nome),
            CommandHandler("start", iniciar)
        ],
        states={
            NOME: [MessageHandler(filters.TEXT & ~filters.COMMAND, receber_nome)],
            EMBARQUE: [MessageHandler(filters.TEXT & ~filters.COMMAND, receber_embarque)],
            DESTINO: [MessageHandler(filters.TEXT & ~filters.COMMAND, receber_destino)],
            PASSAGEIROS: [CallbackQueryHandler(escolher_passageiros)],
            BAGAGEM: [CallbackQueryHandler(escolher_bagagem)],
            CONFIRMACAO: [CallbackQueryHandler(confirmar_corrida)],
        },
        fallbacks=[CommandHandler("cancelar", cancelar)],
    )

    app.add_handler(conversa)
    app.run_polling()
