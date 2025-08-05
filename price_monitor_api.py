#!/usr/bin/env python3
"""
Monitor de Preços StayCharlie - Versão API
Usa a API oficial em vez de web scraping para melhor performance e confiabilidade
"""

import os
import json
import time
import logging
import requests
from datetime import datetime
import pytz

# Configuração de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('price_monitor_api.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

def get_brasilia_time():
    brasilia_tz = pytz.timezone('America/Sao_Paulo')
    return datetime.now(brasilia_tz)

class StayCharliePriceMonitorAPI:
    def __init__(self):
        # Configurações via variáveis de ambiente ou arquivo JSON
        self.price_history_file = './app/data/price_history.json'
        self.telegram_bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
        self.telegram_chat_id = os.getenv('TELEGRAM_CHAT_ID')
        self.check_interval = int(os.getenv('CHECK_INTERVAL_MINUTES', '30'))
        self.price_threshold = float(os.getenv('PRICE_THRESHOLD_PERCENT', '0.0'))
        self.discount_percent = float(os.getenv('DISCOUNT_PERCENT', '25.0'))
        
        # Carrega configuração
        self.config = self.load_config()
        self.price_history = self.load_price_history()
        self.units = self.get_enabled_units()
        
        logger.info("🚀 StayCharlie Monitor API iniciado")
        enabled_units = [unit['name'] for unit in self.units]
        logger.info(f"🏠 Monitorando {len(enabled_units)} unidade(s):")
        for unit in self.units:
            logger.info(f"  • {unit['name']} (ID: {unit['property_id']})")
        logger.info(f"⏰ Intervalo: {self.check_interval} minutos")
        logger.info(f"📉 Limiar: {self.price_threshold}%")
        
        # Headers para requisições API
        self.headers = {
            'accept': '*/*',
            'accept-language': 'pt-BR,pt;q=0.9,en;q=0.8',
            'content-type': 'application/json',
            'origin': 'https://www.staycharlie.com.br',
            'referer': 'https://www.staycharlie.com.br/',
            'sec-fetch-dest': 'empty',
            'sec-fetch-mode': 'cors',
            'sec-fetch-site': 'same-origin',
            'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36'
        }
        
    def load_config(self):
        """Carrega configuração do arquivo JSON primeiro, depois aplica ENV vars se disponíveis"""
        default_config = {
            "check_interval_minutes": 30,
            "monitoring_settings": {
                "city": "SP",
                "start_date": "2025-09-08", 
                "end_date": "2025-09-12",
                "guests": 1
            },
            "units_to_monitor": [],
            "telegram_notifications": {
                "enabled": True
            },
            "price_change_threshold_percent": 0.0,
            "discount_percent": 25.0
        }
        
        # Carrega arquivo JSON se existir
        config_file = 'price_monitor_config.json'
        if os.path.exists(config_file):
            try:
                with open(config_file, 'r', encoding='utf-8') as f:
                    json_config = json.load(f)
                config = {**default_config, **json_config}
                logger.info(f"📄 Configuração carregada do arquivo {config_file}")
            except Exception as e:
                logger.error(f"❌ Erro ao carregar config JSON: {e}")
                config = default_config
        else:
            logger.warning(f"⚠️ Arquivo {config_file} não encontrado, usando configuração padrão")
            config = default_config
        
        # Override com ENV vars se disponíveis
        city = os.getenv('MONITOR_CITY')
        start_date = os.getenv('MONITOR_START_DATE') 
        end_date = os.getenv('MONITOR_END_DATE')
        guests = os.getenv('MONITOR_GUESTS')
        
        if city:
            config['monitoring_settings']['city'] = city
            logger.info(f"🌍 Cidade sobrescrita por ENV var: {city}")
        if start_date:
            config['monitoring_settings']['start_date'] = start_date
            logger.info(f"📅 Data início sobrescrita por ENV var: {start_date}")
        if end_date:
            config['monitoring_settings']['end_date'] = end_date
            logger.info(f"📅 Data fim sobrescrita por ENV var: {end_date}")
        if guests:
            config['monitoring_settings']['guests'] = int(guests)
            logger.info(f"👥 Hóspedes sobrescrito por ENV var: {guests}")
            
        return config
        
    def get_enabled_units(self):
        """Retorna lista de unidades habilitadas para monitoramento"""
        return [unit for unit in self.config.get('units_to_monitor', []) if unit.get('enabled', True)]
    
    def fetch_price_api(self, property_id):
        """Busca preços usando a API oficial do StayCharlie"""
        try:
            settings = self.config['monitoring_settings']
            
            payload = {
                "city": settings['city'],
                "start_date": settings['start_date'],
                "end_date": settings['end_date'],
                "guests": str(settings['guests']),
                "property_id": property_id
            }
            
            logger.info(f"🌐 Consultando API para property_id: {property_id}")
            
            response = requests.post(
                'https://www.staycharlie.com.br/api/availability',
                headers=self.headers,
                json=payload,
                timeout=30
            )
            
            response.raise_for_status()
            data = response.json()
            
            if not data.get('data'):
                logger.warning(f"🚫 Unidade {property_id} indisponível (resposta vazia)")
                return None
                
            # Extrai informações detalhadas da API
            availability_data = data['data'][0] if data['data'] else None
            if not availability_data:
                return None
            
            # Dados detalhados da API
            room_type = availability_data.get('room_type_name', 'N/A')
            prices = availability_data.get('prices', {})
            available_units = availability_data.get('available_units', 0)
            
            # Preços da API (já vêm no formato correto como strings)
            daily_rate = float(prices.get('daily_rate', 0))
            total_rate = float(prices.get('total_rate', 0))
            total_without_fees = float(prices.get('total_rate_without_fees', 0))
            
            # Taxas extras
            extra_rates = prices.get('extra_rates', [])
            cleaning_fee = 0
            other_fees = []
            
            for fee in extra_rates:
                fee_name = fee.get('name', '')
                fee_value = float(fee.get('value_float', 0))
                
                if 'limpeza' in fee_name.lower():
                    cleaning_fee = fee_value
                else:
                    other_fees.append({'name': fee_name, 'value': fee_value})
            
            # Calcula noites
            from datetime import datetime
            start = datetime.strptime(settings['start_date'], '%Y-%m-%d')
            end = datetime.strptime(settings['end_date'], '%Y-%m-%d')
            nights = (end - start).days
            
            # Aplica desconto personalizado se configurado
            discount = self.discount_percent / 100
            total_discounted = total_rate * (1 - discount) if discount > 0 else total_rate
            daily_discounted = daily_rate * (1 - discount) if discount > 0 else daily_rate
            
            price_info = {
                'property_id': property_id,
                'room_type': room_type,
                'daily_rate': daily_rate,
                'total_rate': total_rate,
                'total_without_fees': total_without_fees,
                'cleaning_fee': cleaning_fee,
                'other_fees': other_fees,
                'available_units': available_units,
                'nights': nights,
                'total_discounted': total_discounted,
                'daily_discounted': daily_discounted,
                'discount_percent': self.discount_percent,
                'available': True,
                'timestamp': datetime.now().isoformat(),
                'city': settings['city'],
                'guests': settings['guests'],
                'checkin': settings['start_date'],
                'checkout': settings['end_date']
            }
            
            logger.info(f"💰 Preços obtidos para {property_id}: R$ {daily_rate:.2f}/noite → R$ {total_rate:.2f} total ({available_units} unidades)")
            return price_info
            
        except requests.exceptions.RequestException as e:
            logger.error(f"❌ Erro na requisição API para {property_id}: {e}")
            return None
        except Exception as e:
            logger.error(f"❌ Erro ao processar resposta API para {property_id}: {e}")
            return None
    
    def load_price_history(self):
        """Carrega histórico de preços"""
        if os.path.exists(self.price_history_file):
            try:
                with open(self.price_history_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Erro ao carregar histórico: {e}")
                return {}
        return {}
    
    def save_price_history(self):
        """Salva histórico de preços"""
        try:
            os.makedirs(os.path.dirname(self.price_history_file), exist_ok=True)
            with open(self.price_history_file, 'w', encoding='utf-8') as f:
                json.dump(self.price_history, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"Erro ao salvar histórico: {e}")
    
    def send_telegram_notification(self, message):
        """Envia notificação via Telegram"""
        if not self.telegram_bot_token or not self.telegram_chat_id:
            logger.warning("⚠️ Telegram não configurado")
            return False
        
        try:
            url = f"https://api.telegram.org/bot{self.telegram_bot_token}/sendMessage"
            payload = {
                'chat_id': self.telegram_chat_id,
                'text': f"🏨 *Monitor StayCharlie API*\n\n{message}",
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
    
    def check_price_change(self, current_price_info, last_price_info):
        """Verifica se houve mudança significativa no preço"""
        if last_price_info is None:
            return False, 0, 'no_change'
        
        current_price = current_price_info['total_discounted']
        last_price = last_price_info.get('total_discounted', 0)
        
        if current_price != last_price:
            change_percent = abs(((current_price - last_price) / last_price) * 100) if last_price > 0 else 0
            threshold = self.price_threshold
            
            if change_percent >= threshold:
                if current_price < last_price:
                    return True, change_percent, 'drop'
                else:
                    return True, change_percent, 'rise'
                
        return False, 0, 'no_change'
    
    def notify_price_change(self, unit_name, property_id, price_info, change_type, change_percent):
        """Envia notificação detalhada com todos os dados da API"""
        current_total = price_info['total_discounted']
        
        if change_type == 'drop':
            emoji = "🟢⬇️"
            title = f"PREÇO DESCEU {change_percent:.1f}%!"
            status_icon = "📉"
        elif change_type == 'rise':
            emoji = "🔴⬆️"
            title = f"PREÇO SUBIU {change_percent:.1f}%!"
            status_icon = "📈"
        else:
            emoji = "🟡➡️"
            title = "PREÇO VERIFICADO"
            status_icon = "📊"
        
        # Formata datas
        checkin_formatted = datetime.strptime(price_info['checkin'], '%Y-%m-%d').strftime('%d/%m/%Y')
        checkout_formatted = datetime.strptime(price_info['checkout'], '%Y-%m-%d').strftime('%d/%m/%Y')
        
        # Monta detalhes de taxas
        fees_detail = ""
        if price_info['cleaning_fee'] > 0:
            fees_detail += f"\n🧹 Taxa de limpeza: R$ {price_info['cleaning_fee']:.2f}"
        
        for fee in price_info.get('other_fees', []):
            fees_detail += f"\n💳 {fee['name']}: R$ {fee['value']:.2f}"
        
        # Desconto aplicado
        discount_detail = ""
        if price_info['discount_percent'] > 0:
            original_total = price_info['total_rate']
            savings = original_total - current_total
            discount_detail = f"""
🎯 *Desconto Aplicado:*
💰 Preço original: R$ {original_total:.2f}
✂️ Desconto {price_info['discount_percent']:.0f}%: -R$ {savings:.2f}
💸 Você economiza: R$ {savings:.2f}"""
        
        message = f"""
{emoji} *{title}*

🏨 *{unit_name}*
🏠 Tipo: {price_info['room_type']}
🗓️ {checkin_formatted} → {checkout_formatted} ({price_info['nights']} noites)
👥 {price_info['guests']} hóspede(s) • 📍 {price_info['city']}

{status_icon} *PREÇOS DETALHADOS:*
💰 Total final: *R$ {current_total:.2f}*
📅 Diária: R$ {price_info['daily_discounted']:.2f}
💵 Subtotal: R$ {price_info['total_without_fees']:.2f}{fees_detail}
🏷️ Total com taxas: R$ {price_info['total_rate']:.2f}
{discount_detail}

🏢 *Disponibilidade:*
✅ {price_info['available_units']} unidade(s) disponível(is)

⏰ Verificado em: {datetime.now().strftime('%d/%m/%Y às %H:%M:%S')}
        """.strip()
        
        logger.info(f"📱 Enviando notificação detalhada: {title}")
        self.send_telegram_notification(message)
    
    def notify_unavailable(self, unit_name, property_id, settings):
        """Envia notificação quando unidade está indisponível"""
        checkin_formatted = datetime.strptime(settings['start_date'], '%Y-%m-%d').strftime('%d/%m/%Y')
        checkout_formatted = datetime.strptime(settings['end_date'], '%Y-%m-%d').strftime('%d/%m/%Y')
        
        from datetime import datetime
        start = datetime.strptime(settings['start_date'], '%Y-%m-%d')
        end = datetime.strptime(settings['end_date'], '%Y-%m-%d')
        nights = (end - start).days
        
        message = f"""
🚫 *UNIDADE INDISPONÍVEL*

🏨 *{unit_name}*
🗓️ {checkin_formatted} → {checkout_formatted} ({nights} noites)
👥 {settings['guests']} hóspede(s) • 📍 {settings['city']}

❌ *Status:* Não disponível para as datas selecionadas
📊 Nenhuma unidade disponível no momento

💡 *Dica:* Tente outras datas ou verifique novamente mais tarde

⏰ Verificado em: {datetime.now().strftime('%d/%m/%Y às %H:%M:%S')}
        """.strip()
        
        logger.info(f"📱 Enviando notificação de indisponibilidade")
        self.send_telegram_notification(message)

    def monitor_unit(self, unit):
        """Monitora uma unidade específica"""
        unit_name = unit['name']
        property_id = unit['property_id']
        
        logger.info(f"🏠 Verificando preços para: {unit_name} (ID: {property_id})")
        
        # Busca preços atuais via API
        price_info = self.fetch_price_api(property_id)
        
        if price_info is None:
            logger.warning(f"⚠️ {unit_name} indisponível")
            # Envia notificação de indisponibilidade
            settings = self.config['monitoring_settings']
            self.notify_unavailable(unit_name, property_id, settings)
            return
        
        # Compara com histórico
        last_price_info = self.price_history.get(property_id)
        has_change, change_percent, change_type = self.check_price_change(price_info, last_price_info)
        
        # Registra no histórico
        self.price_history[property_id] = price_info
        
        # Envia notificação
        self.notify_price_change(unit_name, property_id, price_info, change_type, change_percent)
        
        # Salva histórico
        self.save_price_history()
    
    def monitor_all_units(self):
        """Monitora todas as unidades habilitadas"""
        logger.info("🚀 Iniciando verificação de todas as unidades")
        
        for unit in self.units:
            try:
                self.monitor_unit(unit)
                time.sleep(2)  # Pequena pausa entre requisições
            except Exception as e:
                logger.error(f"❌ Erro ao monitorar {unit['name']}: {e}")
        
        logger.info("✅ Verificação concluída")
    
    def run_continuous(self):
        """Executa monitoramento contínuo"""
        logger.info(f"🔄 Iniciando monitoramento contínuo (intervalo: {self.check_interval} minutos)")
        
        while True:
            try:
                self.monitor_all_units()
                logger.info(f"😴 Próxima verificação em {self.check_interval} minutos...")
                time.sleep(self.check_interval * 60)
            except KeyboardInterrupt:
                logger.info("⏹️ Monitoramento interrompido pelo usuário")
                break
            except Exception as e:
                logger.error(f"❌ Erro no loop principal: {e}")
                time.sleep(60)  # Pausa de 1 minuto em caso de erro

def main():
    monitor = StayCharliePriceMonitorAPI()
    
    # Teste único ou monitoramento contínuo
    import sys
    if '--once' in sys.argv:
        monitor.monitor_all_units()
    else:
        monitor.run_continuous()

if __name__ == "__main__":
    main()