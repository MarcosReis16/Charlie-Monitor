#!/usr/bin/env python3
"""
Script de teste para validar configuração antes do deploy
"""

import os
import sys
import requests
from datetime import datetime

def test_telegram_config():
    """Testa configuração do Telegram"""
    print("🔍 Testando configuração do Telegram...")
    
    bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
    chat_id = os.getenv('TELEGRAM_CHAT_ID')
    
    if not bot_token or not chat_id:
        print("❌ TELEGRAM_BOT_TOKEN ou TELEGRAM_CHAT_ID não definidos")
        return False
    
    try:
        # Testar bot
        url = f"https://api.telegram.org/bot{bot_token}/getMe"
        response = requests.get(url, timeout=10)
        
        if response.status_code == 200:
            bot_info = response.json()
            print(f"✅ Bot '{bot_info['result']['first_name']}' está ativo")
        else:
            print(f"❌ Erro ao verificar bot: {response.status_code}")
            return False
        
        # Testar envio de mensagem
        message = f"""
🧪 *TESTE PRÉ-DEPLOY* 🧪

Configuração do Telegram validada com sucesso!

⏰ Testado em: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}

✅ Bot token válido
✅ Chat ID válido  
✅ Comunicação funcionando

🚀 Pronto para deploy na cloud!
        """
        
        send_url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
        payload = {
            'chat_id': chat_id,
            'text': message.strip(),
            'parse_mode': 'Markdown',
            'disable_web_page_preview': True
        }
        
        response = requests.post(send_url, json=payload, timeout=10)
        
        if response.status_code == 200:
            print("✅ Mensagem de teste enviada com sucesso!")
            return True
        else:
            print(f"❌ Erro ao enviar mensagem: {response.status_code} - {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Erro no teste do Telegram: {e}")
        return False

def test_environment_vars():
    """Testa variáveis de ambiente necessárias"""
    print("\n🔍 Verificando variáveis de ambiente...")
    
    required_vars = {
        'TELEGRAM_BOT_TOKEN': os.getenv('TELEGRAM_BOT_TOKEN'),
        'TELEGRAM_CHAT_ID': os.getenv('TELEGRAM_CHAT_ID'),
        'MONITOR_URL': os.getenv('MONITOR_URL', 'https://www.staycharlie.com.br/charlie-nik-pinheiros?city=SP&start_date=2025-09-08&end_date=2025-09-12&guests=1'),
        'CHECK_INTERVAL_MINUTES': os.getenv('CHECK_INTERVAL_MINUTES', '30'),
        'PRICE_THRESHOLD_PERCENT': os.getenv('PRICE_THRESHOLD_PERCENT', '5.0'),
        'DISCOUNT_PERCENT': os.getenv('DISCOUNT_PERCENT', '25.0')
    }
    
    all_ok = True
    for var_name, var_value in required_vars.items():
        if var_value:
            print(f"✅ {var_name}: {var_value}")
        else:
            print(f"❌ {var_name}: NÃO DEFINIDA")
            all_ok = False
    
    return all_ok

def test_target_url():
    """Testa se a URL do StayCharlie está acessível"""
    print("\n🔍 Testando URL do StayCharlie...")
    
    url = os.getenv('MONITOR_URL', 'https://www.staycharlie.com.br/charlie-nik-pinheiros?city=SP&start_date=2025-09-08&end_date=2025-09-12&guests=1')
    
    try:
        response = requests.get(url, timeout=15, headers={
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        })
        
        if response.status_code == 200:
            print(f"✅ StayCharlie acessível (status: {response.status_code})")
            print(f"✅ Tamanho da resposta: {len(response.content)} bytes")
            return True
        else:
            print(f"⚠️ StayCharlie respondeu com status: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Erro ao acessar StayCharlie: {e}")
        return False

def print_deploy_commands():
    """Mostra comandos para deploy"""
    print("\n" + "="*60)
    print("🚀 COMANDOS PARA DEPLOY")
    print("="*60)
    
    print("\n📋 1. PREPARAR REPOSITÓRIO:")
    print("git init")
    print("git add .")
    print('git commit -m "Deploy monitor StayCharlie"')
    print("git remote add origin https://github.com/SEU_USUARIO/staycharlie-monitor")
    print("git push -u origin main")
    
    print("\n🚄 2. RAILWAY (Recomendado):")
    print("1. Acesse: https://railway.app")
    print("2. New Project → Deploy from GitHub repo")
    print("3. Configure variáveis de ambiente no Settings → Variables")
    print("4. Deploy automático!")
    
    print("\n🎨 3. RENDER:")
    print("1. Acesse: https://render.com")  
    print("2. New → Web Service → Connect Repository")
    print("3. Environment: Docker")
    print("4. Configure variáveis de ambiente")
    
    print("\n🪰 4. FLY.IO:")
    print("fly auth login")
    print("fly launch --no-deploy")
    print("fly secrets set TELEGRAM_BOT_TOKEN=SEU_TOKEN")
    print("fly secrets set TELEGRAM_CHAT_ID=SEU_CHAT_ID")
    print("fly deploy")

def main():
    print("🧪 TESTE PRÉ-DEPLOY - Monitor StayCharlie")
    print("="*50)
    
    # Executar todos os testes
    tests = [
        test_environment_vars(),
        test_target_url(),
        test_telegram_config()
    ]
    
    print("\n" + "="*50)
    print("📊 RESULTADO DOS TESTES")
    print("="*50)
    
    if all(tests):
        print("🎉 TODOS OS TESTES PASSARAM!")
        print("✅ Configuração válida para deploy")
        print("🚀 Você pode prosseguir com o deploy na cloud")
        print_deploy_commands()
        return 0
    else:
        print("❌ ALGUNS TESTES FALHARAM!")
        print("🔧 Corrija os problemas antes do deploy")
        return 1

if __name__ == "__main__":
    sys.exit(main())
