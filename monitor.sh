#!/bin/bash

# Script conveniente para o monitor de preços StayCharlie

show_help() {
    echo "🏨 Monitor de Preços StayCharlie"
    echo "================================"
    echo ""
    echo "Uso: ./monitor.sh [comando]"
    echo ""
    echo "Comandos:"
    echo "  start        Inicia monitoramento contínuo em background"
    echo "  check        Executa verificação única"
    echo "  stop         Para o monitoramento em background"
    echo "  status       Mostra status do monitoramento"
    echo "  history      Mostra histórico de preços"
    echo "  config       Mostra configuração atual"
    echo "  setup        Configura o ambiente inicial"
    echo ""
    echo "Exemplos:"
    echo "  ./monitor.sh setup     # Primeira configuração"
    echo "  ./monitor.sh check     # Verificação única"
    echo "  ./monitor.sh start     # Inicia monitoramento"
    echo "  ./monitor.sh history   # Ver histórico"
}

setup() {
    echo "📦 Configurando ambiente..."
    if [ ! -f "venv/bin/activate" ]; then
        ./setup_monitor.sh
    else
        echo "✅ Ambiente já configurado!"
    fi
}

start_monitor() {
    echo "🚀 Iniciando monitoramento em background..."
    
    # Verifica se já está rodando
    if pgrep -f "price_monitor.py" > /dev/null; then
        echo "⚠️  Monitor já está rodando!"
        echo "Use './monitor.sh status' para ver detalhes"
        return 1
    fi
    
    # Ativa ambiente e inicia monitor
    source venv/bin/activate
    nohup python price_monitor.py > monitor.log 2>&1 &
    
    echo "✅ Monitor iniciado em background!"
    echo "📄 Logs em: monitor.log"
    echo "🔍 Use './monitor.sh status' para verificar"
}

stop_monitor() {
    echo "⏹️  Parando monitoramento..."
    
    if pgrep -f "price_monitor.py" > /dev/null; then
        pkill -f "price_monitor.py"
        echo "✅ Monitor parado!"
    else
        echo "ℹ️  Monitor não estava rodando"
    fi
}

show_status() {
    echo "📊 Status do Monitor"
    echo "==================="
    
    if pgrep -f "price_monitor.py" > /dev/null; then
        echo "🟢 Status: RODANDO"
        echo "🔍 PID: $(pgrep -f price_monitor.py)"
        echo ""
        echo "📄 Últimas linhas do log:"
        tail -n 5 monitor.log 2>/dev/null || echo "Log não encontrado"
    else
        echo "🔴 Status: PARADO"
    fi
    
    if [ -f "price_history.json" ]; then
        echo ""
        echo "📈 Última verificação:"
        source venv/bin/activate 2>/dev/null
        python price_monitor.py --history | tail -n 1
    fi
}

check_once() {
    echo "🔍 Executando verificação única..."
    source venv/bin/activate
    python price_monitor.py --once
}

show_history() {
    echo "📊 Histórico de Preços"
    echo "====================="
    source venv/bin/activate
    python price_monitor.py --history
}

show_config() {
    echo "⚙️  Configuração Atual"
    echo "====================="
    source venv/bin/activate
    python price_monitor.py --config
}

# Verifica se está no diretório correto
if [ ! -f "price_monitor.py" ]; then
    echo "❌ Erro: Execute este script no diretório do projeto"
    exit 1
fi

# Processa comando
case "$1" in
    "setup")
        setup
        ;;
    "start")
        setup
        start_monitor
        ;;
    "stop")
        stop_monitor
        ;;
    "status")
        show_status
        ;;
    "check")
        setup
        check_once
        ;;
    "history")
        show_history
        ;;
    "config")
        show_config
        ;;
    "help"|"--help"|"-h")
        show_help
        ;;
    "")
        show_help
        ;;
    *)
        echo "❌ Comando inválido: $1"
        echo ""
        show_help
        exit 1
        ;;
esac