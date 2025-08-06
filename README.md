# 🏨 Monitor de Preços StayCharlie

Monitor automatizado de preços dos apartamentos StayCharlie com notificações via Telegram. **Nova versão com API oficial** - 10x mais rápida e confiável!

## ✨ Características

- 🚀 **API Oficial** - Consultas diretas sem web scraping
- ⚡ **Super Rápido** - Verificações em 2-3 segundos (vs 30s+)
- 📱 **Notificações Telegram** para grupos ou usuários
- 📊 **Histórico de preços** com comparação automática
- 🎯 **Múltiplas unidades** configuráveis via JSON
- ☁️ **Deploy gratuito** em plataformas cloud
- 🔄 **Verificação contínua** com intervalos personalizáveis
- 📦 **Container leve** - Docker otimizado (80% menor)

## 🚀 Deploy Rápido (Recomendado)

### Railway.app
```bash
# 1. Fork este repositório
# 2. Conecte no Railway.app
# 3. Configure as variáveis de ambiente
# 4. Deploy automático!
```

### Variáveis de Ambiente Necessárias
```env
TELEGRAM_BOT_TOKEN=seu_token_aqui
TELEGRAM_CHAT_ID=seu_chat_id_aqui

# Opcionais (valores padrão no JSON)
CHECK_INTERVAL_MINUTES=30
PRICE_THRESHOLD_PERCENT=0.0
DISCOUNT_PERCENT=25.0
```

## 🔧 Instalação Local

### Pré-requisitos
- Python 3.8+
- Internet (sem necessidade de Chrome/ChromeDriver)

### Passos
```bash
# Clone o repositório
git clone https://github.com/seu-usuario/staycharlie-price-monitor.git
cd staycharlie-price-monitor

# Instale dependências (muito mais leves!)
pip install -r requirements.txt

# Configure as variáveis
cp env.example .env
# Edite o arquivo .env com suas configurações

# Execute versão API (recomendada)
python price_monitor_api.py

# Ou versão local com interface
python price_monitor.py
```

## ⚙️ Configuração

### Bot do Telegram
1. Converse com [@BotFather](https://t.me/botfather)
2. Crie um novo bot: `/newbot`
3. Copie o token gerado
4. Para **grupo**: Adicione o bot ao grupo e torne-o admin
5. Para **usuário**: Envie `/start` para o bot

### Arquivo de Configuração
O arquivo `price_monitor_config.json` permite configurar:

```json
{
  "check_interval_minutes": 30,
  "monitoring_settings": {
    "city": "SP",
    "start_date": "2025-09-08",
    "end_date": "2025-09-12",
    "guests": 1
  },
  "units_to_monitor": [
    {
      "name": "Charlie Nik Pinheiros",
      "slug": "charlie-nik-pinheiros",
      "property_id": "310088",
      "enabled": true
    },
    {
      "name": "Smart Charlie Mobi Pinheiros", 
      "slug": "smart-charlie-mobi-pinheiros",
      "property_id": "256246",
      "enabled": true
    }
  ],
  "price_change_threshold_percent": 0.0,
  "discount_percent": 25.0
}
```

## 🏗️ Arquitetura

### Versão Única

**API** (`price_monitor_api.py`) - **Versão de Produção**
- ✅ Usa API oficial do StayCharlie
- ✅ Performance otimizada (2-3s por verificação)
- ✅ Container Docker leve
- ✅ Dados precisos e confiáveis
- ✅ Deploy automático em Railway/Render
- ✅ Timezone Brasília correto

## 📊 Funcionalidades

### Detecção Inteligente
- **🟢 Preço desceu**: Notifica quedas de preço
- **🔴 Preço subiu**: Alerta aumentos
- **🟡 Preço mantido**: Confirmação de verificação
- **🚫 Indisponível**: Detecta quando `{"data":[]}` na API

### API Integration
- **Endpoint**: `/api/availability`
- **Property IDs**: Configurados no JSON
- **Detecção de disponibilidade**: Automática
- **Dados precisos**: Direto da fonte oficial

## 🔔 Exemplo de Notificação

```
🏨 Monitor StayCharlie API

🟢⬇️ PREÇO DESCEU 0.4%!

🏠 Smart Charlie Mobi Pinheiros
💰 Preço atual: R$ 998.62
📅 Diária: R$ 221.53 (4 noites)
🎯 Desconto: 25%

⏰ Verificado em: 04/01/2025 09:37:52
```

## 📱 Deploy em Plataformas

### Railway (Recomendado)
- ✅ 500 horas gratuitas/mês
- ✅ Deploy automático via GitHub
- ✅ Variáveis de ambiente fáceis
- ✅ Container otimizado

### Render.com
- ✅ 750 horas gratuitas/mês
- ✅ Arquivo `render.yaml` incluído
- ✅ Deploy automático

### Fly.io
- ✅ Sempre ativo
- ✅ 160GB-hour gratuitos
- ✅ Dockerfile otimizado

## 🛠️ Desenvolvimento

### Estrutura do Projeto
```
├── price_monitor_api.py      # 🚀 Versão API (principal)
├── price_monitor.py          # Versão local com GUI
├── price_monitor_cloud.py    # Versão legacy (Selenium)
├── price_monitor_config.json # Configurações + Property IDs
├── requirements.txt          # Dependências locais
├── requirements-deploy.txt   # Dependências otimizadas
├── Dockerfile               # Container leve (sem Chrome)
├── railway.json            # Configuração Railway
├── render.yaml             # Configuração Render
└── env.example             # Exemplo de variáveis
```

### Property IDs das Unidades
```
256246 - smart-charlie-mobi-pinheiros
310088 - charlie-nik-pinheiros  
302911 - charlie-alves-guimaraes-pinheiros
313510 - house-of-charlie-pinheiros
```

### Logs
- `price_monitor_api.log` - Logs da versão API
- `price_history.json` - Histórico de preços por property_id

## 🚀 Performance Comparison

| Método | Tempo/Verificação | Recursos | Confiabilidade |
|--------|------------------|----------|----------------|
| **API** | 2-3s | Mínimo | Alta ⭐ |
| Selenium | 30-60s | Alto | Média |

## 🤝 Contribuição

1. Fork o projeto
2. Crie sua feature branch
3. Commit suas mudanças
4. Push para a branch
5. Abra um Pull Request

## 📄 Licença

Este projeto é licenciado sob a MIT License.

## ⚠️ Disclaimer

Este projeto é apenas para fins educacionais e de monitoramento pessoal. Respeite os termos de uso do StayCharlie.