# 🚀 Deploy do Monitor StayCharlie na Cloud

Instruções para hospedar o monitor gratuitamente em diferentes plataformas. **Nova versão API** - muito mais rápida e eficiente!

## 📋 Pré-requisitos

1. **Bot do Telegram configurado** com token
2. **Chat ID** do Telegram obtido (usuário ou grupo)
3. **Conta GitHub** para versionamento
4. **Conta na plataforma** escolhida (Railway, Render, etc.)

## 🎯 Variáveis de Ambiente Necessárias

### Obrigatórias
```env
TELEGRAM_BOT_TOKEN=SEU_TOKEN_DO_BOT_AQUI
TELEGRAM_CHAT_ID=SEU_CHAT_ID_AQUI
```

### Opcionais (valores padrão no price_monitor_config.json)
```env
CHECK_INTERVAL_MINUTES=30
PRICE_THRESHOLD_PERCENT=0.0
DISCOUNT_PERCENT=25.0
MONITOR_CITY=SP
MONITOR_START_DATE=2025-09-08
MONITOR_END_DATE=2025-09-12
MONITOR_GUESTS=1
```

---

## 🚄 1. Railway (Recomendado)

### Vantagens:
- ✅ 500 horas/mês grátis
- ✅ Deploy automático via GitHub
- ✅ **Container 80% menor** (versão API)
- ✅ **Performance 10x melhor**
- ✅ Volume persistente

### Passos:

1. **Fork/Upload do projeto:**
   ```bash
   git init
   git add .
   git commit -m "Initial commit"
   git remote add origin https://github.com/SEU_USUARIO/staycharlie-monitor
   git push -u origin main
   ```

2. **Deploy no Railway:**
   - Acesse [railway.app](https://railway.app)
   - Conecte sua conta GitHub
   - Clique em "New Project" → "Deploy from GitHub repo"
   - Selecione seu repositório
   - Railway detectará automaticamente o Dockerfile otimizado

3. **Configurar variáveis (apenas 2 obrigatórias!):**
   - Vá em Settings → Variables
   - Adicione:
     - `TELEGRAM_BOT_TOKEN` = seu_token_aqui
     - `TELEGRAM_CHAT_ID` = seu_chat_id_aqui

4. **Deploy automático:**
   - Railway fará deploy automático
   - **Versão API** - muito mais rápida!
   - Monitor rodando 24/7 com verificações em 2-3s

---

## 🎨 2. Render.com

### Vantagens:
- ✅ 750 horas/mês grátis
- ✅ Deploy via GitHub
- ✅ Dorme quando não usado (mas reinicia automaticamente)

### Passos:

1. **Criar conta no Render:**
   - Acesse [render.com](https://render.com)
   - Conecte sua conta GitHub

2. **Criar Web Service:**
   - Clique em "New" → "Web Service"
   - Conecte seu repositório GitHub
   - Configure:
     - **Name:** `staycharlie-monitor`
     - **Environment:** `Docker`
     - **Plan:** `Free`

3. **Variáveis de ambiente:**
   - Na aba "Environment", adicione todas as variáveis

4. **Deploy:**
   - Render detectará o `render.yaml` automaticamente
   - Clique em "Deploy"

---

## 🪰 3. Fly.io

### Vantagens:
- ✅ 160GB-hour/mês grátis
- ✅ Sempre ativo (não dorme)
- ✅ Containers Docker nativos

### Passos:

1. **Instalar CLI:**
   ```bash
   curl -L https://fly.io/install.sh | sh
   ```

2. **Login e inicializar:**
   ```bash
   fly auth login
   fly launch --no-deploy
   ```

3. **Configurar fly.toml:**
   ```toml
   app = "staycharlie-monitor"
   
   [env]
     MONITOR_URL = "https://www.staycharlie.com.br/charlie-nik-pinheiros?city=SP&start_date=2025-09-08&end_date=2025-09-12&guests=1"
     CHECK_INTERVAL_MINUTES = "30"
     PRICE_THRESHOLD_PERCENT = "5.0"
     DISCOUNT_PERCENT = "25.0"
   
   [processes]
     worker = "python price_monitor_cloud.py"
   
   [[services]]
     internal_port = 8080
     protocol = "tcp"
   ```

4. **Configurar secrets:**
   ```bash
   fly secrets set TELEGRAM_BOT_TOKEN=SEU_TOKEN_DO_BOT_AQUI
   fly secrets set TELEGRAM_CHAT_ID=SEU_CHAT_ID_AQUI
   ```

5. **Deploy:**
   ```bash
   fly deploy
   ```

---

## 🔧 4. Heroku

### Vantagens:
- ✅ Plataforma madura
- ✅ Dynos gratuitos (limitados)

### Passos:

1. **Instalar CLI:**
   ```bash
   # macOS
   brew tap heroku/brew && brew install heroku
   ```

2. **Criar app:**
   ```bash
   heroku create staycharlie-monitor
   heroku stack:set container
   ```

3. **Configurar variáveis:**
   ```bash
   heroku config:set TELEGRAM_BOT_TOKEN=SEU_TOKEN_DO_BOT_AQUI
   heroku config:set TELEGRAM_CHAT_ID=SEU_CHAT_ID_AQUI
   heroku config:set MONITOR_URL="https://www.staycharlie.com.br/charlie-nik-pinheiros?city=SP&start_date=2025-09-08&end_date=2025-09-12&guests=1"
   heroku config:set CHECK_INTERVAL_MINUTES=30
   heroku config:set PRICE_THRESHOLD_PERCENT=0.0
   heroku config:set DISCOUNT_PERCENT=25.0
   ```

4. **Deploy:**
   ```bash
   git push heroku main
   heroku ps:scale worker=1
   ```

---

## 📊 Comparação das Plataformas

| Plataforma | Horas Grátis | Vantagens | Desvantagens |
|------------|---------------|-----------|--------------|
| **Railway** | 500h/mês | Fácil, persistente, Python nativo | Limite de horas |
| **Render** | 750h/mês | Mais horas, fácil deploy | Dorme quando inativo |
| **Fly.io** | 160GB-hour | Sempre ativo, Docker nativo | CLI obrigatório |
| **Heroku** | 1000h/mês | Maduro, confiável | Limitações crescentes |

---

## 🎯 Recomendação

**Para iniciantes:** Railway
**Para sempre ativo:** Fly.io
**Para máximo uptime:** Render

---

## 🔍 Monitoramento

Após o deploy, você pode:

1. **Ver logs:**
   - Railway: Dashboard → Logs
   - Render: Dashboard → Logs
   - Fly.io: `fly logs`
   - Heroku: `heroku logs --tail`

2. **Testar notificação:**
   ```bash
   # Railway/Render (via logs)
   # Fly.io
   fly ssh console -C "python price_monitor_cloud.py --test"
   # Heroku
   heroku run python price_monitor_cloud.py --test
   ```

3. **Verificação única:**
   ```bash
   # Railway/Render (via logs)
   # Fly.io
   fly ssh console -C "python price_monitor_cloud.py --once"
   # Heroku
   heroku run python price_monitor_cloud.py --once
   ```

---

## 🆘 Troubleshooting

### Erro de Chrome/ChromeDriver:
- ✅ Dockerfile já inclui Chrome e ChromeDriver
- ✅ Configurações headless já aplicadas

### Erro de Telegram:
- Verifique se as variáveis estão corretas
- Teste o bot manualmente enviando `/start`

### Erro de memória:
- Plataformas gratuitas têm limite de RAM
- Monitor otimizado para consumo mínimo

### Monitor para de funcionar:
- Railway: Pode ter atingido limite de horas
- Render: App dormiu por inatividade (reinicia automaticamente)
- Fly.io: Problema na aplicação (ver logs)

---

## 🎉 Resultado

Após o deploy bem-sucedido:

✅ **Monitor funcionando 24/7**
✅ **Notificações automáticas no Telegram**
✅ **Funciona mesmo com Mac desligado**
✅ **Verificações regulares a cada 30 minutos**
✅ **Alertas de queda de preço em tempo real**

**Seu monitor agora é independente e confiável!** 🚀
