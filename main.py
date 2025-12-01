import os
import time
import logging
from datetime import datetime, timedelta
from ping3 import ping
from dotenv import load_dotenv
import requests

# Load environment variables
load_dotenv()

# Configuration
GRID_IP = os.getenv('GRID_IP')
GENERATOR_IP = os.getenv('GENERATOR_IP')
LOCATION_NAME = os.getenv('LOCATION_NAME', 'Unknown Location')
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')
CHECK_INTERVAL = int(os.getenv('CHECK_INTERVAL', 5)) # Seconds between checks
TIMEOUT_MINUTES = int(os.getenv('TIMEOUT_MINUTES', 5))

# Setup Logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("neutrino.log"),
        logging.StreamHandler()
    ]
)

def send_telegram_alert(message):
    """Sends a message via Telegram Bot."""
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        logging.error("Credenciales de Telegram no configuradas.")
        return

    full_message = f"[{LOCATION_NAME}] {message}"

    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": full_message
    }
    try:
        response = requests.post(url, json=payload, timeout=10)
        response.raise_for_status()
        logging.info(f"Alerta de Telegram enviada: {full_message}")
    except requests.exceptions.RequestException as e:
        logging.error(f"Error al enviar alerta de Telegram: {e}")

def is_reachable(ip_address):
    """Pings an IP address and returns True if reachable."""
    try:
        # ping returns delay in seconds or None/False on failure
        response = ping(ip_address, timeout=2)
        return response is not None and response is not False
    except Exception as e:
        logging.error(f"Error haciendo ping a {ip_address}: {e}")
        return False

class DeviceMonitor:
    def __init__(self, ip_address, required_consecutive=3):
        self.ip_address = ip_address
        self.required_consecutive = required_consecutive
        self.consecutive_success = 0
        self.consecutive_fail = 0
        self.is_up = None # None indicates unknown initial state

    def update(self):
        """
        Pings the device and updates the internal state based on consecutive results.
        Returns the current confirmed state (True/False) or None if not yet confirmed.
        """
        reachable = is_reachable(self.ip_address)
        
        if reachable:
            self.consecutive_success += 1
            self.consecutive_fail = 0
        else:
            self.consecutive_fail += 1
            self.consecutive_success = 0
        
        # Check if state should change
        if self.consecutive_success >= self.required_consecutive:
            self.is_up = True
        elif self.consecutive_fail >= self.required_consecutive:
            self.is_up = False
            
        return self.is_up

def main():
    logging.info("Monitoreo Neutrino Iniciado")
    logging.info(f"Monitoreando Red: {GRID_IP}, Generador: {GENERATOR_IP}")

    # Initialize Device Monitors
    grid_monitor = DeviceMonitor(GRID_IP)
    generator_monitor = DeviceMonitor(GENERATOR_IP)

    # State tracking
    grid_down_time = None
    
    # Previous states (Initialize as None to detect first status)
    prev_grid_up = None
    prev_generator_up = None

    # Alert repetition tracking
    last_critical_alert_time = None

    while True:
        # Update monitors
        grid_up = grid_monitor.update()
        generator_up = generator_monitor.update()

        # If states are not yet confirmed (initialization phase), wait and retry
        if grid_up is None or generator_up is None:
            logging.info("Calibrando estado de dispositivos...")
            time.sleep(CHECK_INTERVAL)
            continue

        logging.debug(f"Estado - Red: {'ARRIBA' if grid_up else 'ABAJO'}, Generador: {'ARRIBA' if generator_up else 'ABAJO'}")

        # --- Informational Alerts (State Transitions) ---
        
        # Grid Transitions
        if prev_grid_up is not None and grid_up != prev_grid_up:
            if grid_up:
                msg = "ℹ️ INFO: Energía de Red Restaurada."
                logging.info(msg)
                send_telegram_alert(msg)
            else:
                msg = "ℹ️ INFO: Energía de Red Perdida."
                logging.info(msg)
                send_telegram_alert(msg)
        
        # Generator Transitions
        if prev_generator_up is not None and generator_up != prev_generator_up:
            if generator_up:
                msg = "ℹ️ INFO: Generador Iniciado."
                logging.info(msg)
                send_telegram_alert(msg)
            else:
                msg = "ℹ️ INFO: Generador Detenido."
                logging.info(msg)
                send_telegram_alert(msg)

        # Update previous states
        prev_grid_up = grid_up
        prev_generator_up = generator_up

        # --- Critical Alert Logic ---

        if grid_up:
            # Grid is healthy, reset critical tracking
            grid_down_time = None
            last_critical_alert_time = None
        else:
            # Grid is DOWN
            if grid_down_time is None:
                grid_down_time = datetime.now()
            
            if generator_up:
                # Generator is working, we are safe.
                last_critical_alert_time = None
            else:
                # CRITICAL CONDITION: Grid DOWN and Generator DOWN
                now = datetime.now()
                elapsed_since_grid_down = now - grid_down_time
                
                if elapsed_since_grid_down > timedelta(minutes=TIMEOUT_MINUTES):
                    # We are in the danger zone
                    
                    critical_duration = elapsed_since_grid_down - timedelta(minutes=TIMEOUT_MINUTES)
                    should_alert = False
                    
                    if last_critical_alert_time is None:
                        # First alert
                        should_alert = True
                    else:
                        time_since_last_alert = now - last_critical_alert_time
                        
                        # Phase 1: First 10 minutes of alerting
                        if critical_duration <= timedelta(minutes=10):
                            if time_since_last_alert >= timedelta(minutes=1):
                                should_alert = True
                        # Phase 2: After 10 minutes of alerting
                        else:
                            if time_since_last_alert >= timedelta(minutes=10):
                                should_alert = True
                    
                    if should_alert:
                        msg = (f"🚨 ALERTA CRÍTICA: ¡Red CAÍDA y Generador APAGADO!\n"
                               f"Tiempo sin Red: {elapsed_since_grid_down}\n"
                               f"Hora: {now.strftime('%H:%M:%S')}")
                        logging.error(msg)
                        send_telegram_alert(msg)
                        last_critical_alert_time = now
                else:
                    logging.info(f"Esperando generador... ({elapsed_since_grid_down.seconds}s transcurridos)")

        time.sleep(CHECK_INTERVAL)

if __name__ == "__main__":
    main()
