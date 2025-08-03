#!/usr/bin/env python3
"""
Script para monitorar preços de hospedagem da StayCharlie
Monitora em background e notifica quando o preço abaixa
"""

import requests
import time
import json
import os
import logging
from datetime import datetime
from bs4 import BeautifulSoup
import re
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import argparse
try:
    from selenium import webdriver
    from selenium.webdriver.chrome.options import Options
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    from selenium.common.exceptions import TimeoutException, WebDriverException
    SELENIUM_AVAILABLE = True
except ImportError:
    SELENIUM_AVAILABLE = False

# Configuração de logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('price_monitor.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

class StayCharliePriceMonitor:
    def __init__(self, config_file='price_monitor_config.json'):
        self.config_file = config_file
        self.price_history_file = 'price_history.json'
        self.config = self.load_config()
        self.price_history = self.load_price_history()
        self.units = self.get_enabled_units()
        
        # Headers para simular um browser real
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'pt-BR,pt;q=0.9,en;q=0.8',
            'Accept-Encoding': 'identity',  # Desabilita compressão para debug
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Cache-Control': 'no-cache',
            'Pragma': 'no-cache',
        }
        
    def get_enabled_units(self):
        """Retorna lista de unidades habilitadas para monitoramento"""
        return [unit for unit in self.config.get('units_to_monitor', []) if unit.get('enabled', True)]
    
    def build_url(self, unit_slug):
        """Constrói URL para uma unidade específica baseado nas configurações"""
        settings = self.config.get('monitoring_settings', {})
        
        base_url = f"https://www.staycharlie.com.br/{unit_slug}"
        params = []
        
        if settings.get('city'):
            params.append(f"city={settings['city']}")
        if settings.get('start_date'):
            params.append(f"start_date={settings['start_date']}")
        if settings.get('end_date'):
            params.append(f"end_date={settings['end_date']}")
        if settings.get('guests'):
            params.append(f"guests={settings['guests']}")
            
        if params:
            return f"{base_url}?{'&'.join(params)}"
        return base_url

    def load_config(self):
        """Carrega configurações do arquivo JSON"""
        default_config = {
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
                    "enabled": True
                }
            ],
            "email_notifications": {
                "enabled": False,
                "smtp_server": "smtp.gmail.com",
                "smtp_port": 587,
                "email": "",
                "password": "",
                "to_email": ""
            },
            "telegram_notifications": {
                "enabled": False,
                "bot_token": "",
                "chat_id": "",
                "phone_number": ""
            },
            "price_change_threshold_percent": 0.0,
            "discount_percent": 25.0
        }
        
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                return {**default_config, **config}
            except Exception as e:
                logger.error(f"Erro ao carregar config: {e}")
                return default_config
        else:
            self.save_config(default_config)
            return default_config

    def save_config(self, config):
        """Salva configurações no arquivo JSON"""
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"Erro ao salvar config: {e}")

    def load_price_history(self):
        """Carrega histórico de preços para múltiplas unidades"""
        if os.path.exists(self.price_history_file):
            try:
                with open(self.price_history_file, 'r', encoding='utf-8') as f:
                    history = json.load(f)
                    # Se for uma lista (formato antigo), converte para o novo formato
                    if isinstance(history, list):
                        # Migra para novo formato se existir histórico antigo
                        if history:
                            return {"charlie-nik-pinheiros": history}
                        else:
                            return {}
                    return history
            except Exception as e:
                logger.error(f"Erro ao carregar histórico: {e}")
        return {}

    def save_price_history(self):
        """Salva histórico de preços para múltiplas unidades"""
        try:
            with open(self.price_history_file, 'w', encoding='utf-8') as f:
                json.dump(self.price_history, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"Erro ao salvar histórico: {e}")
            
    def get_unit_history(self, unit_slug):
        """Retorna histórico de uma unidade específica"""
        return self.price_history.get(unit_slug, [])

    def extract_price(self, html_content):
        """Extrai o preço da página HTML"""
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Debug: salva o HTML para análise
            with open('debug_page.html', 'w', encoding='utf-8') as f:
                f.write(html_content)
            logger.info("HTML salvo em debug_page.html para análise")
            
            # Busca por possíveis seletores de preço específicos para StayCharlie
            price_selectors = [
                # Seletores específicos para StayCharlie
                '[data-testid*="price"]',
                '[data-testid*="total"]',
                '[class*="price"]',
                '[class*="total"]',
                '[class*="amount"]',
                '[class*="value"]',
                '[class*="cost"]',
                '.price',
                '.total-price',
                '.amount',
                '.total',
                '.value'
            ]
            
            for selector in price_selectors:
                elements = soup.select(selector)
                for element in elements:
                    text = element.get_text(strip=True)
                    logger.debug(f"Verificando elemento {selector}: {text}")
                    # Busca por padrões de preço brasileiro (R$ 123,45 ou R$ 1.234,56)
                    price_match = re.search(r'R\$\s*(\d{1,3}(?:\.\d{3})*(?:,\d{2})?)', text)
                    if price_match:
                        price_str = price_match.group(1)
                        # Converte para float (remove pontos e troca vírgula por ponto)
                        price_float = float(price_str.replace('.', '').replace(',', '.'))
                        logger.info(f"Preço encontrado via seletor {selector}: R$ {price_str}")
                        return price_float, price_str
            
            # Busca alternativa por qualquer padrão de preço na página
            full_text = soup.get_text()
            logger.debug(f"Texto completo da página (primeiros 500 chars): {full_text[:500]}")
            
            # Padrões mais flexíveis para preços
            price_patterns = [
                r'R\$\s*(\d{1,3}(?:\.\d{3})*(?:,\d{2})?)',  # R$ 1.234,56
                r'(\d{1,3}(?:\.\d{3})*(?:,\d{2})?)\s*reais?',  # 1234,56 reais
                r'total[:\s]*R?\$?\s*(\d{1,3}(?:\.\d{3})*(?:,\d{2})?)',  # total: R$ 1234,56
                r'pre[çc]o[:\s]*R?\$?\s*(\d{1,3}(?:\.\d{3})*(?:,\d{2})?)',  # preço: R$ 1234,56
            ]
            
            for pattern in price_patterns:
                price_matches = re.findall(pattern, full_text, re.IGNORECASE)
                if price_matches:
                    logger.info(f"Preços encontrados com padrão {pattern}: {price_matches}")
                    # Pega o maior preço encontrado (provavelmente o preço total)
                    prices = []
                    for match in price_matches:
                        try:
                            price_float = float(match.replace('.', '').replace(',', '.'))
                            prices.append((price_float, match))
                        except ValueError:
                            continue
                    
                    if prices:
                        best_price = max(prices, key=lambda x: x[0])
                        logger.info(f"Melhor preço encontrado: R$ {best_price[1]}")
                        return best_price
            
            logger.warning("Nenhum preço encontrado com nenhum padrão")
            return None, None
            
        except Exception as e:
            logger.error(f"Erro ao extrair preço: {e}")
            return None, None

    def fetch_price_with_selenium(self, url=None):
        """Faz requisição usando Selenium para executar JavaScript"""
        if not SELENIUM_AVAILABLE:
            logger.error("Selenium não está instalado")
            return None
            
        # Se não receber URL, usa self.url (compatibilidade com código antigo)
        target_url = url if url is not None else getattr(self, 'url', None)
        
        if not target_url:
            logger.error("Nenhuma URL fornecida para fetch_price_with_selenium")
            return None
            
        driver = None
        try:
            logger.info("Iniciando navegador Selenium...")
            
            # Configura opções do Chrome
            chrome_options = Options()
            chrome_options.add_argument('--headless')  # Executa sem interface gráfica
            chrome_options.add_argument('--no-sandbox')
            chrome_options.add_argument('--disable-dev-shm-usage')
            chrome_options.add_argument('--disable-gpu')
            chrome_options.add_argument('--window-size=1920,1080')
            chrome_options.add_argument('--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
            
            # Cria o driver
            driver = webdriver.Chrome(options=chrome_options)
            driver.set_page_load_timeout(30)
            
            logger.info(f"Acessando URL: {target_url}")
            driver.get(target_url)
            
            # Aguarda um pouco para o JavaScript carregar
            logger.info("Aguardando JavaScript carregar...")
            time.sleep(10)
            
            # Rola a página para garantir que tudo carregue
            logger.info("Rolando página para garantir carregamento...")
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(3)
            driver.execute_script("window.scrollTo(0, 0);")
            time.sleep(3)
            
            # Tenta aguardar por elementos que possam conter preços
            wait = WebDriverWait(driver, 15)
            
            # Lista de possíveis seletores para preços
            price_selectors = [
                '[data-testid*="price"]',
                '[data-testid*="total"]',
                '.price',
                '.total',
                '.amount',
                '[class*="price"]',
                '[class*="total"]',
                '[class*="amount"]',
                '[class*="value"]',
                '[class*="cost"]'
            ]
            
            # Tenta encontrar elementos de preço
            for selector in price_selectors:
                try:
                    elements = driver.find_elements(By.CSS_SELECTOR, selector)
                    for element in elements:
                        text = element.text.strip()
                        if text:
                            logger.debug(f"Elemento encontrado com seletor {selector}: {text}")
                            # Busca por padrões de preço
                            price_match = re.search(r'R\$\s*(\d{1,3}(?:\.\d{3})*(?:,\d{2})?)', text)
                            if price_match:
                                price_str = price_match.group(1)
                                price_float = float(price_str.replace('.', '').replace(',', '.'))
                                logger.info(f"Preço encontrado via Selenium: R$ {price_str}")
                                return price_float
                except Exception as e:
                    logger.debug(f"Erro ao verificar seletor {selector}: {e}")
                    continue
            
            # Se não encontrou com seletores, busca no texto completo da página
            page_text = driver.find_element(By.TAG_NAME, "body").text
            logger.info(f"Tamanho do texto da página: {len(page_text)} caracteres")
            logger.debug(f"Texto da página (primeiros 1000 chars): {page_text[:1000]}")
            
            # Busca especificamente por números que possam ser preços
            numbers_in_page = re.findall(r'\d{1,3}(?:[.,]\d{2,3})*', page_text)
            logger.info(f"Números encontrados na página: {numbers_in_page[:20]}")  # Primeiros 20
            
            # Salva o HTML renderizado para debug
            rendered_html = driver.page_source
            with open('debug_page_rendered.html', 'w', encoding='utf-8') as f:
                f.write(rendered_html)
            logger.info("HTML renderizado salvo em debug_page_rendered.html")
            
            # Busca por padrões de preço no texto completo
            price_patterns = [
                r'R\$\s*(\d{1,3}(?:\.\d{3})*(?:,\d{2})?)',
                r'(\d{1,3}(?:\.\d{3})*(?:,\d{2})?)\s*reais?',
                r'total[:\s]*R?\$?\s*(\d{1,3}(?:\.\d{3})*(?:,\d{2})?)',
                r'pre[çc]o[:\s]*R?\$?\s*(\d{1,3}(?:\.\d{3})*(?:,\d{2})?)',
            ]
            
            for pattern in price_patterns:
                matches = re.findall(pattern, page_text, re.IGNORECASE)
                if matches:
                    logger.info(f"Preços encontrados no texto da página: {matches}")
                    # Converte todos os preços encontrados
                    prices = []
                    for match in matches:
                        try:
                            price_float = float(match.replace('.', '').replace(',', '.'))
                            prices.append(price_float)
                        except ValueError:
                            continue
                    
                    if prices:
                        # Ordena preços do menor para o maior
                        prices.sort()
                        
                        # Detecta preço por noite vs total
                        if len(prices) >= 2:
                            night_price = min(prices)  # Menor preço (por noite)
                            total_price = max(prices)  # Maior preço (total)
                            
                            # Calcula desconto de 25%
                            discount_percent = self.config.get('discount_percent', 25.0)
                            night_price_discounted = night_price * (1 - discount_percent / 100)
                            total_price_discounted = total_price * (1 - discount_percent / 100)
                            
                            price_info = {
                                'night_price': night_price,
                                'total_price': total_price,
                                'night_price_discounted': night_price_discounted,
                                'total_price_discounted': total_price_discounted,
                                'discount_percent': discount_percent
                            }
                            
                            logger.info(f"💰 Preços detectados:")
                            logger.info(f"   📅 Diária: R$ {night_price:.2f} → R$ {night_price_discounted:.2f} (com {discount_percent}% desconto)")
                            logger.info(f"   📊 Total: R$ {total_price:.2f} → R$ {total_price_discounted:.2f} (com {discount_percent}% desconto)")
                            
                            return price_info
                        else:
                            # Se só encontrou um preço, assume que é o total
                            single_price = prices[0]
                            discount_percent = self.config.get('discount_percent', 25.0)
                            discounted_price = single_price * (1 - discount_percent / 100)
                            
                            price_info = {
                                'night_price': None,
                                'total_price': single_price,
                                'night_price_discounted': None,
                                'total_price_discounted': discounted_price,
                                'discount_percent': discount_percent
                            }
                            
                            logger.info(f"💰 Preço total encontrado: R$ {single_price:.2f} → R$ {discounted_price:.2f} (com {discount_percent}% desconto)")
                            return price_info
            
            logger.warning("Nenhum preço encontrado via Selenium")
            return None
            
        except TimeoutException:
            logger.error("Timeout ao carregar a página com Selenium")
            return None
        except WebDriverException as e:
            logger.error(f"Erro do WebDriver: {e}")
            return None
        except Exception as e:
            logger.error(f"Erro inesperado no Selenium: {e}")
            return None
        finally:
            if driver:
                try:
                    driver.quit()
                    logger.debug("Driver do Selenium fechado")
                except:
                    pass

    def fetch_price(self, url=None):
        """Faz requisição para o site e extrai o preço"""
        try:
            # Se não receber URL, usa self.url (compatibilidade com código antigo)
            target_url = url if url is not None else getattr(self, 'url', None)
            
            if not target_url:
                logger.error("Nenhuma URL fornecida para fetch_price")
                return None
                
            logger.info(f"Verificando preço para: {target_url}")
            
            # Cria uma sessão para manter cookies
            session = requests.Session()
            session.headers.update(self.headers)
            
            response = session.get(target_url, timeout=30)
            response.raise_for_status()
            
            logger.info(f"Status da resposta: {response.status_code}")
            logger.info(f"Content-Type: {response.headers.get('content-type', 'N/A')}")
            logger.info(f"Content-Length: {len(response.content)} bytes")
            
            # Verifica se é HTML válido
            content_type = response.headers.get('content-type', '').lower()
            if 'text/html' not in content_type:
                logger.warning(f"Conteúdo não é HTML: {content_type}")
                return None
            
            # Força decodificação correta do conteúdo
            try:
                # Tenta decodificar como UTF-8 primeiro
                if response.encoding is None or 'utf-8' not in response.encoding.lower():
                    response.encoding = 'utf-8'
                
                text_content = response.text
                
                # Se ainda está com caracteres estranhos, tenta outras abordagens
                if any(ord(c) > 127 and c.isprintable() == False for c in text_content[:100]):
                    logger.warning("Conteúdo parece estar mal codificado, tentando decodificação manual")
                    
                    # Tenta diferentes encodings
                    for encoding in ['utf-8', 'latin-1', 'iso-8859-1']:
                        try:
                            text_content = response.content.decode(encoding, errors='ignore')
                            logger.info(f"Decodificação bem-sucedida com: {encoding}")
                            break
                        except:
                            continue
                    else:
                        # Se tudo falhar, usa o conteúdo original mas remove caracteres problemáticos
                        text_content = response.content.decode('utf-8', errors='replace')
                        logger.warning("Usando decodificação com replace para caracteres problemáticos")
                
                logger.info(f"Tamanho do texto: {len(text_content)} caracteres")
                logger.debug(f"Primeiros 200 chars: {text_content[:200]}")
                
                # Verifica se parece ser uma página de erro ou redirecionamento
                if len(text_content) < 500:
                    logger.warning("Página muito pequena, pode ser um erro ou redirecionamento")
                    logger.debug(f"Conteúdo completo: {text_content}")
                
            except Exception as decode_error:
                logger.error(f"Erro na decodificação: {decode_error}")
                text_content = str(response.content)
            
            price_float, price_str = self.extract_price(text_content)
            
            if price_float is not None:
                logger.info(f"Preço encontrado: R$ {price_str}")
                return price_float
            else:
                logger.warning("Preço não encontrado no HTML estático")
                
                # Tenta usar Selenium como fallback
                if SELENIUM_AVAILABLE:
                    logger.info("Tentando buscar preço com Selenium...")
                    selenium_price_info = self.fetch_price_with_selenium(target_url)
                    if selenium_price_info is not None:
                        return selenium_price_info
                else:
                    logger.warning("Selenium não está disponível. Para sites que dependem de JavaScript, instale com: pip install selenium")
                
                logger.warning("Preço não encontrado")
                return None
                
        except requests.RequestException as e:
            logger.error(f"Erro na requisição: {e}")
            return None
        except Exception as e:
            logger.error(f"Erro inesperado: {e}")
            return None

    def send_email_notification(self, subject, message):
        """Envia notificação por email"""
        if not self.config['email_notifications']['enabled']:
            return False
        
        try:
            email_config = self.config['email_notifications']
            
            msg = MIMEMultipart()
            msg['From'] = email_config['email']
            msg['To'] = email_config['to_email']
            msg['Subject'] = subject
            
            msg.attach(MIMEText(message, 'plain', 'utf-8'))
            
            server = smtplib.SMTP(email_config['smtp_server'], email_config['smtp_port'])
            server.starttls()
            server.login(email_config['email'], email_config['password'])
            text = msg.as_string()
            server.sendmail(email_config['email'], email_config['to_email'], text)
            server.quit()
            
            logger.info("Email enviado com sucesso")
            return True
            
        except Exception as e:
            logger.error(f"Erro ao enviar email: {e}")
            return False

    def get_telegram_chat_id(self):
        """Descobre o chat_id do Telegram automaticamente"""
        if not self.config['telegram_notifications']['enabled']:
            return None
            
        try:
            telegram_config = self.config['telegram_notifications']
            bot_token = telegram_config['bot_token']
            
            if not bot_token:
                logger.error("Token do bot Telegram não configurado")
                return None
            
            # Busca atualizações recentes
            url = f"https://api.telegram.org/bot{bot_token}/getUpdates"
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            
            if data['ok'] and data['result']:
                # Pega o chat_id da mensagem mais recente
                latest_update = data['result'][-1]
                if 'message' in latest_update:
                    chat_id = str(latest_update['message']['chat']['id'])
                    logger.info(f"Chat ID encontrado: {chat_id}")
                    return chat_id
                    
            logger.warning("Nenhuma mensagem encontrada. Envie uma mensagem para o bot primeiro.")
            return None
            
        except Exception as e:
            logger.error(f"Erro ao buscar chat_id do Telegram: {e}")
            return None

    def setup_telegram_chat_id(self):
        """Configura o chat_id automaticamente se não estiver definido"""
        telegram_config = self.config['telegram_notifications']
        
        if not telegram_config.get('chat_id'):
            chat_id = self.get_telegram_chat_id()
            if chat_id:
                telegram_config['chat_id'] = chat_id
                self.save_config(self.config)
                logger.info("Chat ID do Telegram configurado automaticamente")
                
                # Envia mensagem de confirmação
                welcome_message = """
✅ *Telegram configurado com sucesso!*

Olá! Seu bot do StayCharlie está funcionando perfeitamente.

Você receberá notificações aqui quando:
🔻 O preço da hospedagem abaixar
📊 Houver mudanças nos valores

*Configuração atual:*
• ⏰ Verificação: a cada 30 minutos
• 📉 Alerta: quedas acima de 5%
• 🎯 Local: Charlie Nik Pinheiros

Para testar, use: `python price_monitor.py --test-telegram`
                """
                
                # Envia a mensagem de boas-vindas (sem usar o método send_telegram_notification para evitar recursão)
                try:
                    bot_token = telegram_config['bot_token']
                    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
                    payload = {
                        'chat_id': chat_id,
                        'text': welcome_message.strip(),
                        'parse_mode': 'Markdown',
                        'disable_web_page_preview': True
                    }
                    response = requests.post(url, json=payload, timeout=10)
                    if response.status_code == 200:
                        logger.info("📱 Mensagem de boas-vindas enviada")
                except Exception as e:
                    logger.debug(f"Erro ao enviar mensagem de boas-vindas: {e}")
                
                return True
            else:
                logger.warning("⚠️  Para receber notificações no Telegram:")
                logger.warning("   1. Abra o Telegram")
                logger.warning("   2. Procure pelo seu bot")
                logger.warning("   3. Envie qualquer mensagem (ex: /start)")
                logger.warning("   4. Execute o monitor novamente")
                return False
        return True

    def send_telegram_notification(self, message):
        """Envia notificação via Telegram"""
        if not self.config['telegram_notifications']['enabled']:
            return False
            
        try:
            telegram_config = self.config['telegram_notifications']
            bot_token = telegram_config['bot_token']
            chat_id = telegram_config['chat_id']
            
            if not bot_token:
                logger.error("Token do bot Telegram não configurado")
                return False
                
            # Tenta configurar chat_id se não estiver definido
            if not chat_id:
                if not self.setup_telegram_chat_id():
                    return False
                chat_id = telegram_config['chat_id']
            
            # Adiciona emojis e formatação para Telegram
            telegram_message = f"🏨 *Monitor StayCharlie*\n\n{message}"
            
            url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
            payload = {
                'chat_id': chat_id,
                'text': telegram_message,
                'parse_mode': 'Markdown',
                'disable_web_page_preview': True
            }
            
            response = requests.post(url, json=payload, timeout=10)
            response.raise_for_status()
            
            result = response.json()
            if result['ok']:
                logger.info("📱 Notificação Telegram enviada com sucesso")
                return True
            else:
                logger.error(f"Erro na API do Telegram: {result}")
                return False
                
        except Exception as e:
            logger.error(f"Erro ao enviar notificação Telegram: {e}")
            return False

    def check_price_change(self, current_price_info, last_price_info):
        """Verifica se houve mudança significativa no preço"""
        if last_price_info is None:
            return False, 0, 'no_change'
        
        # Compara preço total com desconto (que é o que realmente importa)
        current_price = current_price_info['total_price_discounted']
        last_price = last_price_info.get('total_price_discounted', last_price_info.get('price', 0))
        
        if current_price != last_price:
            change_percent = abs(((current_price - last_price) / last_price) * 100)
            threshold = self.config['price_change_threshold_percent']
            
            if change_percent >= threshold:
                if current_price < last_price:
                    return True, change_percent, 'drop'
                else:
                    return True, change_percent, 'rise'
                
        return False, 0, 'no_change'

    def record_price(self, price_info, unit_slug=None):
        """Registra preço no histórico para uma unidade específica"""
        if isinstance(price_info, (int, float)):
            # Compatibilidade com formato antigo
            price_info = {
                'total_price': price_info,
                'total_price_discounted': price_info,
                'night_price': None,
                'night_price_discounted': None,
                'discount_percent': 0
            }
        
        # Se não tiver unit_slug, usa como unidade padrão (compatibilidade)
        if unit_slug is None:
            unit_slug = "charlie-nik-pinheiros"
            
        # Inicializa histórico da unidade se não existir
        if unit_slug not in self.price_history:
            self.price_history[unit_slug] = []
            
        unit_history = self.price_history[unit_slug]
        unit_name = price_info.get('unit_name', unit_slug)
        
        # Constrói URL se não estiver presente
        url = self.build_url(unit_slug) if hasattr(self, 'build_url') else getattr(self, 'url', '')
        
        record = {
            'timestamp': datetime.now().isoformat(),
            'price_info': price_info,
            'url': url,
            'unit_name': unit_name,
            'unit_slug': unit_slug,
            # Mantém compatibilidade com formato antigo
            'price': price_info['total_price_discounted']
        }
        
        # Verifica se houve mudança significativa
        last_record = unit_history[-1] if unit_history else None
        last_price_info = last_record.get('price_info') if last_record else None
        
        current_total_discounted = price_info['total_price_discounted']
        last_total_discounted = 0.0  # Valor padrão para primeira execução
        
        if last_price_info:
            last_total_discounted = last_price_info.get('total_price_discounted', last_record.get('price', 0))
        
        # Só registra se houve mudança no preço ou se é o primeiro registro para esta unidade
        if not unit_history or abs(current_total_discounted - last_total_discounted) > 0.01:
            unit_history.append(record)
            self.save_price_history()
            
            # Verifica se houve mudança significativa no preço
            has_changed, change_percent, change_type = self.check_price_change(price_info, last_price_info)
            
            if has_changed:
                # Formata mensagem detalhada
                discount_pct = price_info['discount_percent']
                
                # Define emoji e título baseado no tipo de mudança
                if change_type == 'drop':
                    emoji = "📉"
                    title = "PREÇO ABAIXOU!"
                    change_desc = f"Queda de: {change_percent:.1f}%"
                    log_msg = f"📉 PREÇO ABAIXOU {change_percent:.1f}%!"
                else:
                    emoji = "📈"
                    title = "PREÇO SUBIU!"
                    change_desc = f"Aumento de: {change_percent:.1f}%"
                    log_msg = f"📈 PREÇO SUBIU {change_percent:.1f}%!"
                
                if price_info['night_price']:
                    price_details = f"""
📅 Diária: R$ {price_info['night_price']:.2f} → R$ {price_info['night_price_discounted']:.2f} (com cupom interno Nubank {discount_pct}%)
📊 Total: R$ {price_info['total_price']:.2f} → R$ {current_total_discounted:.2f} (com cupom interno Nubank {discount_pct}%)
                    """
                else:
                    price_details = f"""
📊 Total: R$ {price_info['total_price']:.2f} → R$ {current_total_discounted:.2f} (com cupom interno Nubank {discount_pct}%)
                    """
                
                message = f"""
{emoji} {title} {emoji}

{unit_name}
Preço anterior (com cupom): R$ {last_total_discounted:.2f}
Preço atual (com cupom): R$ {current_total_discounted:.2f}
{change_desc}

{price_details}

Link: {url}

Monitorado em: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}
                """
                
                logger.info(f"{log_msg} De R$ {last_total_discounted:.2f} para R$ {current_total_discounted:.2f} (com cupom interno Nubank)")
                
                # Envia notificações
                self.send_email_notification(
                    f"{emoji} Mudança de Preço - StayCharlie ({change_percent:.1f}%)",
                    message
                )
                
                self.send_telegram_notification(message)
                
                # Mostra notificação no sistema (macOS)
                try:
                    if change_type == 'drop':
                        os.system(f'''osascript -e 'display notification "Preço abaixou {change_percent:.1f}%! R$ {current_total_discounted:.2f} com cupom Nubank" with title "StayCharlie Monitor"' ''')
                    else:
                        os.system(f'''osascript -e 'display notification "Preço subiu {change_percent:.1f}%! R$ {current_total_discounted:.2f} com cupom Nubank" with title "StayCharlie Monitor"' ''')
                except:
                    pass

    def run_once(self):
        """Executa uma verificação para todas as unidades habilitadas"""
        all_success = True
        
        for unit in self.units:
            unit_name = unit.get('name', 'Unknown')
            unit_slug = unit.get('slug', '')
            
            if not unit_slug:
                logger.warning(f"Unidade {unit_name} não tem slug definido, pulando...")
                continue
                
            logger.info(f"🏠 Verificando preços para: {unit_name}")
            
            url = self.build_url(unit_slug)
            price_info = self.fetch_price(url)
            
            if price_info is not None:
                # Adiciona informações da unidade
                price_info['unit_name'] = unit_name
                price_info['unit_slug'] = unit_slug
                self.record_price(price_info, unit_slug)
            else:
                all_success = False
                logger.error(f"❌ Falha ao verificar preços para {unit_name}")
        
        return all_success

    def run_monitor(self):
        """Executa o monitor em loop contínuo"""
        enabled_units = [unit['name'] for unit in self.units]
        logger.info(f"🚀 Iniciando monitoramento de preços para {len(enabled_units)} unidade(s):")
        for unit in self.units:
            logger.info(f"  🏠 {unit['name']} ({unit['slug']})")
        logger.info(f"⏰ Intervalo de verificação: {self.config['check_interval_minutes']} minutos")
        
        while True:
            try:
                self.run_once()
                
                # Aguarda próxima verificação
                sleep_seconds = self.config['check_interval_minutes'] * 60
                logger.info(f"Próxima verificação em {self.config['check_interval_minutes']} minutos...")
                time.sleep(sleep_seconds)
                
            except KeyboardInterrupt:
                logger.info("Monitoramento interrompido pelo usuário")
                break
            except Exception as e:
                logger.error(f"Erro inesperado: {e}")
                logger.info("Aguardando 5 minutos antes de tentar novamente...")
                time.sleep(300)  # 5 minutos

    def show_history(self):
        """Mostra histórico de preços para todas as unidades"""
        if not self.price_history:
            print("Nenhum preço registrado ainda.")
            return
        
        print("\n📊 Histórico de Preços StayCharlie:")
        print("=" * 70)
        
        # Se for formato antigo (lista), converte e mostra
        if isinstance(self.price_history, list):
            print("\n🏠 Charlie Nik Pinheiros (formato legado):")
            print("-" * 50)
            for record in self.price_history[-10:]:  # Últimos 10 registros
                self._show_record(record)
            return
            
        # Formato novo (múltiplas unidades)
        for unit_slug, unit_history in self.price_history.items():
            if not unit_history:
                continue
                
            # Busca nome da unidade na configuração
            unit_name = None
            for unit in self.units:
                if unit['slug'] == unit_slug:
                    unit_name = unit['name']
                    break
            
            if not unit_name:
                unit_name = unit_history[-1].get('unit_name', unit_slug)
                
            print(f"\n🏠 {unit_name}:")
            print("-" * 50)
            
            for record in unit_history[-10:]:  # Últimos 10 registros
                self._show_record(record)
                
    def _show_record(self, record):
        """Método auxiliar para exibir um registro de preço"""
        timestamp = datetime.fromisoformat(record['timestamp'])
        price_info = record.get('price_info')
        
        if price_info and isinstance(price_info, dict):
            # Formato novo com informações detalhadas
            discount_pct = price_info.get('discount_percent', 0)
            
            if price_info.get('night_price'):
                night_original = price_info['night_price']
                night_discounted = price_info['night_price_discounted']
                total_original = price_info['total_price']
                total_discounted = price_info['total_price_discounted']
                
                print(f"\n🕐 {timestamp.strftime('%d/%m/%Y %H:%M')}")
                print(f"   📅 Diária: R$ {night_original:.2f} → R$ {night_discounted:.2f} (cupom {discount_pct}%)")
                print(f"   📊 Total:  R$ {total_original:.2f} → R$ {total_discounted:.2f} (cupom {discount_pct}%)")
            else:
                total_original = price_info['total_price']
                total_discounted = price_info['total_price_discounted']
                
                print(f"\n🕐 {timestamp.strftime('%d/%m/%Y %H:%M')}")
                print(f"   📊 Total: R$ {total_original:.2f} → R$ {total_discounted:.2f} (cupom {discount_pct}%)")
        else:
            # Formato antigo (compatibilidade)
            price = record.get('price', 0)
            print(f"\n🕐 {timestamp.strftime('%d/%m/%Y %H:%M')}")
            print(f"   💰 Preço: R$ {price:.2f}")
    
    def _get_discounted_price(self, record):
        """Extrai preço com desconto de um registro"""
        price_info = record.get('price_info')
        if price_info and isinstance(price_info, dict):
            return price_info.get('total_price_discounted')
        return record.get('price')

def main():
    parser = argparse.ArgumentParser(description='Monitor de preços StayCharlie')
    parser.add_argument('--once', action='store_true', help='Executa apenas uma verificação')
    parser.add_argument('--history', action='store_true', help='Mostra histórico de preços')
    parser.add_argument('--config', action='store_true', help='Mostra configuração atual')
    parser.add_argument('--test-telegram', action='store_true', help='Testa notificação do Telegram')
    
    args = parser.parse_args()
    
    monitor = StayCharliePriceMonitor()
    
    if args.history:
        monitor.show_history()
    elif args.config:
        print(json.dumps(monitor.config, indent=2, ensure_ascii=False))
    elif args.test_telegram:
        print("🧪 Testando notificação do Telegram...")
        current_time = datetime.now().strftime('%d/%m/%Y %H:%M:%S')
        test_message = f"""
📉 TESTE DE NOTIFICAÇÃO 📉

Hospedagem StayCharlie - Pinheiros
Este é um teste para verificar se as notificações estão funcionando!

📅 Diária: R$ 312,37 → R$ 234,28 (com cupom interno Nubank 25%)
📊 Total: R$ 1.414,50 → R$ 1.060,88 (com cupom interno Nubank 25%)

Link: https://www.staycharlie.com.br/charlie-nik-pinheiros

Testado em: {current_time}
        """
        
        success = monitor.send_telegram_notification(test_message.strip())
        print("✅ Teste do Telegram concluído com sucesso!" if success else "❌ Erro no teste do Telegram")
    elif args.once:
        success = monitor.run_once()
        print("✅ Verificação concluída" if success else "❌ Erro na verificação")
    else:
        monitor.run_monitor()

if __name__ == "__main__":
    main()
