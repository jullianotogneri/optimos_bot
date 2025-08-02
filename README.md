# 🤖 Bot de Corridas - Optimos

Este é um bot de atendimento para solicitação de corridas urbanas via Telegram. Desenvolvido em Python com a biblioteca `python-telegram-bot` versão 20+.

## 🚀 Funcionalidades

- Início com botão simples 🚗
- Coleta de nome, endereço de embarque e destino
- Seleção de número de passageiros (com botões)
- Seleção de bagagem/compras (sim/não)
- Cálculo automático da distância e valor
- Exibe resumo com valor e distância
- Confirmação da corrida (sim/não)
- Resposta com link fictício de rastreio do motorista

## 💰 Tarifas

- R$2,50/km entre embarque e destino
- Valor mínimo: R$9,00
- Passageiros extras e bagagem aumentam o valor

## 🔧 Como rodar no Render

1. Suba os arquivos no GitHub (incluindo `optimos_bot.py`, `requirements.txt`, `render.yaml`)
2. Crie um novo serviço no [Render](https://render.com)
3. Escolha tipo **Web Service**
4. Defina as variáveis de ambiente:
   - `TOKEN`: token do bot Telegram
   - `GOOGLE_API_KEY`: chave da API Google Maps
5. Render detectará o build automaticamente com base no `render.yaml`

## ✅ Requisitos

- Conta no Telegram com um bot ativo
- Conta gratuita no Render.com
- Conta com acesso à API do Google Maps (Distance Matrix API habilitada)

---

## 📄 Licença

Uso livre para fins educacionais e pessoais. Criação original por [Julliano Riveira Togneri].
