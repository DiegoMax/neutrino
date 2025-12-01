# Neutrino - Generator Monitor

Neutrino is a simple Python tool designed to monitor the status of Grid power and a Backup Generator. It alerts you via Telegram if the Generator fails to start within a specified time after a Grid failure.

## Logic

1.  **Grid Monitoring**: Pings a device that is only online when Grid power is available.
2.  **Generator Monitoring**: Pings a device that is only online when the Generator is running.
3.  **Validation (Debounce)**: To avoid false positives due to temporary network glitches, a device is only considered "UP" or "DOWN" after **3 consecutive pings** with the same result.
4.  **Alerts**:
    - Sends informational alerts when the Grid or Generator change state (Up/Down).
    - If the Grid goes DOWN and the Generator does not come UP within **5 minutes** (configurable), a critical alert is sent.
    - The critical alert is repeated every **1 minute** during the first 10 minutes, and then every **10 minutes**.
    - All alerts include the configured location name.

## Installation

1.  **Clone the repository** (or copy the files):

    ```bash
    git clone <your-repo>
    cd neutrino
    ```

2.  **Create a virtual environment (optional but recommended)**:

    ```bash
    python3 -m venv .venv
    source .venv/bin/activate
    ```

3.  **Install dependencies**:

    ```bash
    pip install -r requirements.txt
    ```

4.  **Configuration**:
    Copy `.env.example` to `.env` and fill in your details:

    ```bash
    cp .env.example .env
    ```

    Edit the `.env` file:

    - `GRID_IP`: IP address of the device powered by the Grid.
    - `GENERATOR_IP`: IP address of the device powered by the Generator.
    - `LOCATION_NAME`: Name of the location (e.g., "Central Site") to identify alerts.
    - `TELEGRAM_BOT_TOKEN`: Your Telegram Bot Token.
    - `TELEGRAM_CHAT_ID`: Your Telegram Chat ID.
    - `CHECK_INTERVAL`: Interval in seconds between pings (default: 5).
    - `TIMEOUT_MINUTES`: Time to wait before alerting (default: 5).

## Manual Execution

```bash
sudo python main.py
```

_Note: `sudo` (or Administrator privileges) is often required for ICMP ping operations depending on your OS._

## Run as Service (Ubuntu Server / Systemd)

To have Neutrino run automatically at system startup and restart if it fails, you can configure it as a systemd service.

1.  **Create the service file**:
    Create a file named `/etc/systemd/system/neutrino.service`:

    ```bash
    sudo nano /etc/systemd/system/neutrino.service
    ```

2.  **Paste the following content** (Make sure to adjust paths and user):

    ```ini
    [Unit]
    Description=Neutrino Generator Monitor
    After=network.target

    [Service]
    Type=simple
    User=root
    WorkingDirectory=/path/to/your/neutrino
    ExecStart=/path/to/your/neutrino/.venv/bin/python main.py
    Restart=always
    RestartSec=10

    [Install]
    WantedBy=multi-user.target
    ```

    - Replace `/path/to/your/neutrino` with the absolute path where you cloned the project (e.g., `/home/user/neutrino`).
    - Ensure `ExecStart` points to the python executable within your virtual environment (or the system one if you didn't use venv).
    - `User=root` is used because `ping` usually requires privileges. If you have configured special permissions for ping, you can change the user.

3.  **Reload systemd and enable the service**:

    ```bash
    sudo systemctl daemon-reload
    sudo systemctl enable neutrino
    sudo systemctl start neutrino
    ```

4.  **Check status**:

    ```bash
    sudo systemctl status neutrino
    ```

5.  **View logs**:

    ```bash
    journalctl -u neutrino -f
    ```
