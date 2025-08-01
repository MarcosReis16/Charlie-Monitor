#!/usr/bin/env python3
"""
Monitor de Preços StayCharlie - Versão Cloud
Adaptado para hospedagem gratuita (Railway, Render, Fly.io)
"""

import os
import json
import time
import logging
import requests
import argparse
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from webdriver_manager.chrome import ChromeDriverManager
import re

# Configuração de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/app/data/price_monitor.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

class StayCharliePriceMonitorCloud:
    def __init__(self):
        # Configurações via variáveis de ambiente
        self.url = os.getenv('MONITOR_URL', 'https://www.staycharlie.com.br/charlie-nik-pinheiros?city=SP&start_date=2025-09-08&end_date=2025-09-12&guests=1')
        self.price_history_file = '/app/data/price_history.json'
        self.telegram_bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
        self.telegram_chat_id = os.getenv('TELEGRAM_CHAT_ID')
        self.check_interval = int(os.getenv('CHECK_INTERVAL_MINUTES', '30'))
        self.price_threshold = float(os.getenv('PRICE_THRESHOLD_PERCENT', '5.0'))
        self.discount_percent = float(os.getenv('DISCOUNT_PERCENT', '25.0'))
        
        logger.info("🚀 StayCharlie Monitor Cloud iniciado")
        logger.info(f"📍 URL: {self.url}")
        logger.info(f"⏰ Intervalo: {self.check_interval} minutos")
        logger.info(f"📉 Limiar: {self.price_threshold}%")
        
        self.price_history = self.load_price_history()
        
        # Headers para simular um browser real
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Linux; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'pt-BR,pt;q=0.9,en;q=0.8',
            'Accept-Encoding': 'identity',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Cache-Control': 'no-cache',
            'Pragma': 'no-cache',
        }

    def load_price_history(self):
        """Carrega histórico de preços"""
        if os.path.exists(self.price_history_file):
            try:
                with open(self.price_history_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Erro ao carregar histórico: {e}")
        return []

    def save_price_history(self):
        """Salva histórico de preços"""
        try:
            os.makedirs(os.path.dirname(self.price_history_file), exist_ok=True)
            with open(self.price_history_file, 'w', encoding='utf-8') as f:
                json.dump(self.price_history, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"Erro ao salvar histórico: {e}")

    def create_driver(self):
        """Cria driver do Selenium otimizado para cloud"""
        chrome_options = Options()
        
        # Configurações essenciais para cloud/headless
        chrome_options.add_argument('--headless=new')  # Novo modo headless
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--disable-extensions')
        chrome_options.add_argument('--disable-logging')
        chrome_options.add_argument('--disable-web-security')
        chrome_options.add_argument('--ignore-certificate-errors')
        chrome_options.add_argument('--ignore-ssl-errors')
        chrome_options.add_argument('--allow-running-insecure-content')
        chrome_options.add_argument('--disable-background-timer-throttling')
        chrome_options.add_argument('--disable-backgrounding-occluded-windows')
        chrome_options.add_argument('--disable-renderer-backgrounding')
        chrome_options.add_argument('--disable-features=TranslateUI')
        chrome_options.add_argument('--disable-default-apps')
        chrome_options.add_argument('--no-first-run')
        chrome_options.add_argument('--disable-background-networking')
        chrome_options.add_argument('--disable-sync')
        
        # Definir user agent
        chrome_options.add_argument(f'--user-agent={self.headers["User-Agent"]}')
        
        # Configurações de performance
        chrome_options.add_argument('--memory-pressure-off')
        chrome_options.add_argument('--max_old_space_size=4096')
        chrome_options.add_argument('--aggressive-cache-discard')
        
        # Configurar tamanho da janela
        chrome_options.add_argument('--window-size=1920,1080')
        
        try:
            # Instalar ChromeDriver automaticamente
            service = Service(ChromeDriverManager().install())
            driver = webdriver.Chrome(service=service, options=chrome_options)
            driver.set_page_load_timeout(30)
            logger.info("✅ Driver do Chrome criado com sucesso")
            return driver
        except Exception as e:
            logger.error(f"❌ Erro ao criar driver: {e}")
            return None

    def fetch_price(self):
        """Busca preços usando Selenium"""
        driver = None
        try:
            driver = self.create_driver()
            if not driver:
                return None
            
            logger.info(f"🌐 Acessando URL: {self.url}")
            driver.get(self.url)
            
            # Aguardar JavaScript carregar
            logger.info("⏳ Aguardando JavaScript carregar...")
            time.sleep(5)
            
            # Aguardar elemento de preço aparecer
            try:
                WebDriverWait(driver, 20).until(
                    EC.presence_of_element_located((By.TAG_NAME, "body"))
                )
            except TimeoutException:
                logger.warning("Timeout aguardando página carregar")
            
            # Aguardar um pouco mais para garantir que os preços são carregados
            time.sleep(3)
            
            # Obter HTML da página renderizada
            html_content = driver.page_source
            
            # Salvar HTML para debug
            with open('/app/data/debug_page_rendered.html', 'w', encoding='utf-8') as f:
                f.write(html_content)
            
            # Buscar preços no HTML renderizado
            price_patterns = [
                r'R\$\s*(\d{1,3}(?:\.\d{3})*,\d{2})',  # R$ 1.234,56
                r'(\d{1,3}(?:\.\d{3})*,\d{2})',        # 1.234,56
                r'(\d{1,3}(?:,\d{3})*\.\d{2})',        # 1,234.56
            ]
            
            all_prices = []
            for pattern in price_patterns:
                matches = re.findall(pattern, html_content)
                all_prices.extend(matches)
            
            # Filtrar preços válidos (acima de R$ 100)
            valid_prices = []
            for price_str in all_prices:
                try:
                    # Normalizar formato brasileiro (vírgula para ponto)
                    if ',' in price_str and '.' in price_str:
                        # Formato: 1.234,56
                        price_clean = price_str.replace('.', '').replace(',', '.')
                    elif ',' in price_str:
                        # Formato: 234,56
                        price_clean = price_str.replace(',', '.')
                    else:
                        # Formato: 234.56
                        price_clean = price_str
                    
                    price_value = float(price_clean)
                    if 100 <= price_value <= 10000:  # Filtro de preços razoáveis
                        valid_prices.append(price_value)
                except ValueError:
                    continue
            
            if valid_prices:
                valid_prices.sort()
                daily_price = min(valid_prices)  # Menor preço (provavelmente diária)
                total_price = max(valid_prices)  # Maior preço (provavelmente total)
                
                logger.info(f"💰 Preços detectados:")
                logger.info(f"   📅 Diária: R$ {daily_price:.2f} → R$ {daily_price * (1 - self.discount_percent/100):.2f} (com {self.discount_percent}% desconto)")
                logger.info(f"   📊 Total: R$ {total_price:.2f} → R$ {total_price * (1 - self.discount_percent/100):.2f} (com {self.discount_percent}% desconto)")
                
                return {
                    'timestamp': datetime.now().isoformat(),
                    'daily_price': daily_price,
                    'total_price': total_price,
                    'daily_price_discounted': daily_price * (1 - self.discount_percent/100),
                    'total_price_discounted': total_price * (1 - self.discount_percent/100),
                    'discount_percent': self.discount_percent
                }
            else:
                logger.warning("❌ Nenhum preço encontrado")
                return None
                
        except Exception as e:
            logger.error(f"❌ Erro ao buscar preços: {e}")
            return None
        finally:
            if driver:
                try:
                    driver.quit()
                    logger.debug("🔒 Driver do Selenium fechado")
                except:
                    pass

    def send_telegram_notification(self, message):
        """Envia notificação para o Telegram"""
        if not self.telegram_bot_token or not self.telegram_chat_id:
            logger.warning("⚠️ Telegram não configurado")
            return False
        
        try:
            url = f"https://api.telegram.org/bot{self.telegram_bot_token}/sendMessage"
            payload = {
                'chat_id': self.telegram_chat_id,
                'text': message,
                'parse_mode': 'Markdown',
                'disable_web_page_preview': True
            }
            
            response = requests.post(url, json=payload, timeout=10)
            
            if response.status_code == 200:
                logger.info("📱 Notificação Telegram enviada com sucesso")
                return True
            else:
                logger.error(f"❌ Erro Telegram: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Erro ao enviar Telegram: {e}")
            return False

    def record_price(self, price_info):
        """Registra preço no histórico e verifica alertas"""
        self.price_history.append(price_info)
        
        # Manter apenas os últimos 100 registros
        if len(self.price_history) > 100:
            self.price_history = self.price_history[-100:]
        
        # Salvar histórico
        self.save_price_history()
        
        # Verificar se deve enviar alerta
        if len(self.price_history) >= 2:
            current = price_info['total_price_discounted']
            previous = self.price_history[-2]['total_price_discounted']
            
            if previous > current:
                drop_percent = ((previous - current) / previous) * 100
                
                if drop_percent >= self.price_threshold:
                    # Enviar alerta
                    current_time = datetime.now().strftime('%d/%m/%Y %H:%M:%S')
                    message = f"""
🎉 *PREÇO ABAIXOU {drop_percent:.1f}%!*

*Hospedagem:* StayCharlie Nik Pinheiros
*Data:* 08-12/09/2025 (4 noites)

💰 *Novo preço:*
📅 Diária: R$ {price_info['daily_price']:.2f} → R$ {price_info['daily_price_discounted']:.2f}
📊 Total: R$ {price_info['total_price']:.2f} → R$ {price_info['total_price_discounted']:.2f}

💡 *Com cupom 5ANOS ({self.discount_percent}% desconto)*

🔗 [Reservar agora]({self.url})

⏰ Verificado em: {current_time}
                    """
                    
                    logger.info(f"🎉 PREÇO ABAIXOU {drop_percent:.1f}%! De R$ {previous:.2f} para R$ {current:.2f} (com cupom)")
                    self.send_telegram_notification(message.strip())

    def run_once(self):
        """Executa uma verificação"""
        price_info = self.fetch_price()
        if price_info is not None:
            self.record_price(price_info)
            return True
        return False

    def run_monitor(self):
        """Executa o monitor em loop contínuo"""
        logger.info(f"🚀 Iniciando monitoramento de preços para: {self.url}")
        logger.info(f"⏰ Intervalo de verificação: {self.check_interval} minutos")
        
        while True:
            try:
                self.run_once()
                
                # Aguarda próxima verificação
                sleep_seconds = self.check_interval * 60
                logger.info(f"😴 Próxima verificação em {self.check_interval} minutos...")
                time.sleep(sleep_seconds)
                
            except KeyboardInterrupt:
                logger.info("🛑 Monitoramento interrompido pelo usuário")
                break
            except Exception as e:
                logger.error(f"❌ Erro inesperado: {e}")
                logger.info("⏳ Aguardando 5 minutos antes de tentar novamente...")
                time.sleep(300)  # 5 minutos

def main():
    parser = argparse.ArgumentParser(description='Monitor de preços StayCharlie - Cloud')
    parser.add_argument('--once', action='store_true', help='Executa apenas uma verificação')
    parser.add_argument('--test', action='store_true', help='Testa notificação do Telegram')
    
    args = parser.parse_args()
    
    monitor = StayCharliePriceMonitorCloud()
    
    if args.test:
        logger.info("🧪 Testando notificação do Telegram...")
        current_time = datetime.now().strftime('%d/%m/%Y %H:%M:%S')
        test_message = f"""
🎉 *TESTE DE NOTIFICAÇÃO* 🎉

Hospedagem StayCharlie - Pinheiros
Este é um teste para verificar se as notificações estão funcionando!

📅 Diária: R$ 312,37 → R$ 234,28 (com 25% cupom)
📊 Total: R$ 1.414,50 → R$ 1.060,88 (com 25% cupom)

🔗 [Link da hospedagem]({monitor.url})

⏰ Testado em: {current_time}
        """
        
        success = monitor.send_telegram_notification(test_message.strip())
        logger.info("✅ Teste concluído com sucesso!" if success else "❌ Erro no teste")
    elif args.once:
        success = monitor.run_once()
        logger.info("✅ Verificação concluída" if success else "❌ Erro na verificação")
    else:
        monitor.run_monitor()

if __name__ == "__main__":
    main()
