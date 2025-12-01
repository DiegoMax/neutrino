# Neutrino - Monitor de Generador

Neutrino es una herramienta simple en Python diseñada para monitorear el estado de la energía de la Red y un Generador de Respaldo. Te alerta vía Telegram si el Generador falla en arrancar dentro de un tiempo específico después de una falla de la Red.

## Lógica

1.  **Monitoreo de Red**: Hace ping a un dispositivo que solo está en línea cuando hay energía de la Red.
2.  **Monitoreo de Generador**: Hace ping a un dispositivo que solo está en línea cuando el Generador está funcionando.
3.  **Validación (Debounce)**: Para evitar falsos positivos por fallos temporales de red, un dispositivo solo se considera "ARRIBA" o "ABAJO" después de **3 pings consecutivos** con el mismo resultado.
4.  **Alertas**:
    - Envía alertas informativas cuando la Red o el Generador cambian de estado (Arriba/Abajo).
    - Si la Red cae y el Generador no arranca dentro de **5 minutos** (configurable), se envía una alerta crítica.
    - La alerta crítica se repite cada **1 minuto** durante los primeros 10 minutos, y luego cada **10 minutos**.
    - Todas las alertas incluyen el nombre de la ubicación configurada.

## Instalación

1.  **Clonar el repositorio** (o copiar los archivos):

    ```bash
    git clone <tu-repo>
    cd neutrino
    ```

2.  **Crear un entorno virtual (opcional pero recomendado)**:

    ```bash
    python3 -m venv .venv
    source .venv/bin/activate
    ```

3.  **Instalar dependencias**:

    ```bash
    pip install -r requirements.txt
    ```

4.  **Configuración**:
    Copia `.env.example` a `.env` y completa tus datos:

    ```bash
    cp .env.example .env
    ```

    Edita el archivo `.env`:

    - `GRID_IP`: Dirección IP del dispositivo alimentado por la Red.
    - `GENERATOR_IP`: Dirección IP del dispositivo alimentado por el Generador.
    - `LOCATION_NAME`: Nombre de la ubicación (ej. "Sitio Central") para identificar las alertas.
    - `TELEGRAM_BOT_TOKEN`: Tu Token del Bot de Telegram.
    - `TELEGRAM_CHAT_ID`: Tu ID de Chat de Telegram.
    - `CHECK_INTERVAL`: Intervalo en segundos entre pings (por defecto: 5).
    - `TIMEOUT_MINUTES`: Tiempo de espera antes de alertar (por defecto: 5).

## Ejecución Manual

```bash
sudo python main.py
```

_Nota: A menudo se requiere `sudo` (o privilegios de administrador) para operaciones de ping ICMP dependiendo de tu sistema operativo._

## Ejecutar como Servicio (Ubuntu Server / Systemd)

Para que Neutrino se ejecute automáticamente al iniciar el sistema y se reinicie si falla, puedes configurarlo como un servicio de systemd.

1.  **Crear el archivo de servicio**:
    Crea un archivo llamado `/etc/systemd/system/neutrino.service`:

    ```bash
    sudo nano /etc/systemd/system/neutrino.service
    ```

2.  **Pegar el siguiente contenido** (Asegúrate de ajustar las rutas y el usuario):

    ```ini
    [Unit]
    Description=Neutrino Generator Monitor
    After=network.target

    [Service]
    Type=simple
    User=root
    WorkingDirectory=/ruta/a/tu/neutrino
    ExecStart=/ruta/a/tu/neutrino/.venv/bin/python main.py
    Restart=always
    RestartSec=10

    [Install]
    WantedBy=multi-user.target
    ```

    - Reemplaza `/ruta/a/tu/neutrino` con la ruta absoluta donde clonaste el proyecto (ej. `/home/usuario/neutrino`).
    - Asegúrate de que `ExecStart` apunte al ejecutable de python dentro de tu entorno virtual (o el del sistema si no usaste venv).
    - Se usa `User=root` porque `ping` suele requerir privilegios. Si has configurado permisos especiales para ping, puedes cambiar el usuario.

3.  **Recargar systemd y habilitar el servicio**:

    ```bash
    sudo systemctl daemon-reload
    sudo systemctl enable neutrino
    sudo systemctl start neutrino
    ```

4.  **Verificar el estado**:

    ```bash
    sudo systemctl status neutrino
    ```

5.  **Ver logs**:

    ```bash
    journalctl -u neutrino -f
    ```

## Requisitos

- Python 3.x
- `ping3`
- `python-dotenv`
- `requests`
