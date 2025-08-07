# 🏨 Monitor de Preços StayCharlie

Monitor automatizado de preços dos apartamentos StayCharlie com notificações via Telegram. **Versão única com API oficial** - 10x mais rápida e confiável que web scraping!

## ✨ Características

- 🚀 **API Oficial** - Consultas diretas sem web scraping ou Selenium
- ⚡ **Super Rápido** - Verificações em 2-3 segundos (vs 30s+ Selenium)
- 📱 **Notificações Telegram** para grupos ou usuários
- 📊 **Histórico de preços** com comparação automática
- 🎯 **Múltiplas unidades** configuráveis via JSON
- ☁️ **Deploy gratuito** em Railway, Render, Fly.io
- 🔄 **Verificação contínua** com intervalos personalizáveis
- 📦 **Container leve** - Docker otimizado sem Chrome/ChromeDriver
- 🕐 **Timezone correto** - Horários em Brasília

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
CHECK_INTERVAL_MINUTES=120
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

# Execute o monitor
python price_monitor_api.py

# Modo teste (verifica uma vez e para)
python price_monitor_api.py --test

# Verificação única (sem loop contínuo)
python price_monitor_api.py --once
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
  "check_interval_minutes": 120,
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

### Versão Única Consolidada

**`price_monitor_api.py`** - **Única versão de produção**
- ✅ Usa API oficial do StayCharlie (`/api/availability`)
- ✅ Performance otimizada (2-3s por verificação vs 30s+ Selenium)
- ✅ Container Docker leve (sem Chrome/ChromeDriver)
- ✅ Dados precisos e confiáveis direto da API
- ✅ Deploy automático em Railway/Render/Fly.io
- ✅ Timezone Brasília correto (`America/Sao_Paulo`)
- ✅ Tratamento inteligente de unidades indisponíveis
- ✅ Dependências mínimas: apenas `requests` e `pytz`

## 📊 Funcionalidades

### Detecção Inteligente
- **🟢 Preço desceu**: Notifica quedas de preço
- **🔴 Preço subiu**: Alerta aumentos
- **🟡 Preço mantido**: Confirmação de verificação
- **🚫 Indisponível**: Detecta quando `{"data":[]}` na API

### API Integration
- **Endpoint**: `https://www.staycharlie.com.br/api/availability`
- **Method**: `POST` com dados de checkin/checkout
- **Property IDs**: Configurados no `price_monitor_config.json`
- **Detecção de disponibilidade**: Automática via resposta `{"data":[]}`
- **Dados precisos**: Direto da fonte oficial do StayCharlie
- **Rate limiting**: Respeitoso com delays entre requests

## 🔔 Exemplo de Notificação

### Preço Verificado
```
✅ PREÇO VERIFICADO

🏨 Smart Charlie Mobi Pinheiros
🏠 Tipo: Apartamento
🗓️ 08/09/2025 → 12/09/2025 (4 noites)
👥 1 hóspede(s) • 📍 São Paulo

📊 PREÇOS DA API:
📅 Diária: R$ 287.93
💵 Subtotal: R$ 1301.75
💰 Total final: R$ 1301.75

🏢 Disponibilidade:
✅ 4 unidade(s) disponível(is)

⏰ Verificado em: 06/08/2025 às 17:24:32
```

### Unidade Indisponível
```
🚫 UNIDADE INDISPONÍVEL

🏨 Charlie Alves Guimarães Pinheiros
🗓️ 08/09/2025 → 12/09/2025 (4 noites)
👥 1 hóspede(s) • 📍 São Paulo

ℹ️ Nenhuma unidade disponível para as datas selecionadas

⏰ Verificado em: 06/08/2025 às 17:24:40
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
├── price_monitor_api.py      # 🚀 Versão única de produção
├── price_monitor_config.json # Configurações + Property IDs
├── requirements.txt          # Dependências
├── requirements-deploy.txt   # Dependências de deploy
├── Dockerfile               # Container otimizado
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

### Logs e Dados
- `price_monitor_api.log` - Logs detalhados com timestamp Brasília
- `price_history.json` - Histórico de preços por property_id
- `/app/data/` - Diretório de dados no container Docker

## 🚀 Performance Comparison

| Método | Tempo/Verificação | Recursos | Dependências | Confiabilidade |
|--------|------------------|----------|--------------|----------------|
| **API** | 2-3s | Mínimo | requests, pytz | Alta ⭐ |
| Selenium (removido) | 30-60s | Alto | Chrome, ChromeDriver, selenium, beautifulsoup4 | Média |

### Melhorias da Versão API
- 🚀 **10x mais rápida** - De 30s para 3s por verificação
- 📦 **Container 80% menor** - Sem Chrome/ChromeDriver
- 🔧 **Dependências mínimas** - 2 pacotes vs 4+ anteriormente
- 🛡️ **Mais confiável** - Sem problemas de browser/driver
- 💰 **Menor custo de cloud** - Menos CPU e memória

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