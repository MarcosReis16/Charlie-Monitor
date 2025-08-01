# 🏨 StayCharlie Price Monitor

Monitor automático de preços da StayCharlie com notificações via Telegram.

## 🚀 Deploy na Cloud (24/7)

**Teste sua configuração:**
```bash
python test_cloud.py
```

**Plataformas recomendadas:**
- **Railway** - 500h/mês grátis
- **Render** - 750h/mês grátis  
- **Fly.io** - 160GB-hour/mês grátis

📖 **Instruções completas:** [DEPLOY.md](DEPLOY.md)

## ⚙️ Configuração

### Variáveis de Ambiente:
```env
TELEGRAM_BOT_TOKEN=seu_token_aqui
TELEGRAM_CHAT_ID=seu_chat_id_aqui
MONITOR_URL=https://www.staycharlie.com.br/charlie-nik-pinheiros?city=SP&start_date=2025-09-08&end_date=2025-09-12&guests=1
CHECK_INTERVAL_MINUTES=30
PRICE_THRESHOLD_PERCENT=5.0
DISCOUNT_PERCENT=25.0
```

## 🏃‍♂️ Uso Local

```bash
# Instalar dependências
pip install -r requirements-deploy.txt

# Configurar variáveis de ambiente
export TELEGRAM_BOT_TOKEN="seu_token"
export TELEGRAM_CHAT_ID="seu_chat_id"

# Testar
python price_monitor_cloud.py --test

# Executar uma vez
python price_monitor_cloud.py --once

# Monitor contínuo
python price_monitor_cloud.py
```

## 📱 Funcionalidades

✅ **Monitoramento 24/7** de preços da StayCharlie  
✅ **Notificações instantâneas** via Telegram  
✅ **Detecção automática** de quedas de preço  
✅ **Aplicação automática** de cupons de desconto  
✅ **Histórico** de preços  
✅ **Deploy fácil** em plataformas gratuitas  

## 🎯 Como Funciona

1. Acessa a página da StayCharlie a cada 30 minutos
2. Extrai preços usando Selenium (JavaScript renderizado)
3. Aplica desconto do cupom "5ANOS" (25%)
4. Compara com preço anterior
5. Envia alerta no Telegram se preço abaixar ≥ 5%

## 🔧 Estrutura

```
staycharlie-price-monitor/
├── price_monitor_cloud.py    # Versão para cloud
├── price_monitor.py          # Versão local
├── test_cloud.py            # Teste de configuração
├── Dockerfile              # Container para deploy
├── requirements-deploy.txt  # Dependências
├── railway.json            # Config Railway
├── render.yaml             # Config Render
└── DEPLOY.md               # Instruções de deploy
```

## 🎉 Resultado

Após o deploy bem-sucedido, você receberá notificações como esta:

```
🎉 PREÇO ABAIXOU 11.0%!

Hospedagem: StayCharlie Nik Pinheiros
Data: 08-12/09/2025 (4 noites)

💰 Novo preço:
📅 Diária: R$ 360,40 → R$ 270,30
📊 Total: R$ 1.606,60 → R$ 1.204,95

💡 Com cupom 5ANOS (25% desconto)

🔗 Reservar agora

⏰ Verificado em: 01/08/2025 10:08:55
```

---

**Monitor independente e confiável! 🚀**
