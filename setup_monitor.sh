#!/bin/bash

echo "🏨 Configurando Monitor de Preços StayCharlie"
echo "============================================="

# Verifica se Python 3 está instalado
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 não encontrado. Por favor, instale Python 3."
    exit 1
fi

# Cria ambiente virtual se não existir
if [ ! -d "venv" ]; then
    echo "📦 Criando ambiente virtual..."
    python3 -m venv venv
fi

# Ativa ambiente virtual
echo "🔧 Ativando ambiente virtual..."
source venv/bin/activate

# Instala dependências
echo "📋 Instalando dependências..."
pip install -r requirements.txt

echo ""
echo "✅ Configuração concluída!"
echo ""
echo "🚀 Para usar o monitor:"
echo "  source venv/bin/activate"
echo "  python price_monitor.py                    # Monitor contínuo"
echo "  python price_monitor.py --once             # Verificação única"
echo "  python price_monitor.py --history          # Ver histórico"
echo ""
echo "⚙️  Edite price_monitor_config.json para configurar notificações por email"