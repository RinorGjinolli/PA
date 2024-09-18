<h1 style="font-size: 3em;">Flask-Inventarliste</h1>
<h2 style="font-size: 3em;">Allgemeine Anleitung</h2>
https://www.digitalocean.com/community/tutorials/how-to-serve-flask-applications-with-gunicorn-and-nginx-on-ubuntu-18-04

## Installation

1. Erstelle das Verzeichnis und wechseln hinein:
    ```sh
    mkdir /vcid
    cd /vcid
    ```

2. Klone das Repository:
    ```sh
    git clone GITHUB-LINK
    cd PA
    ```

3. Aktualisiere die Paketliste und installiere die erforderlichen Pakete:
    ```sh
    sudo apt update
    sudo apt install python3-full python3-pip python3-dev build-essential libssl-dev libffi-dev python3-setuptools
    sudo apt install python3-venv
    sudo apt install nginx
    sudo apt install mysql-server
    ```

    Weitere Informationen zur MySQL-Installation:
   https://www.digitalocean.com/community/tutorials/how-to-install-mysql-on-ubuntu-20-04-de

5. Erstelle eine virtuelle Umgebung und aktiviere sie:
    ```sh
    python3 -m venv myvenv
    source myvenv/bin/activate
    ```

6. Installiere die Python-Abhängigkeiten:
    ```sh
    sudo myenv/bin/pip install -r requirements.txt
    ```

7. Ändere die Berechtigungen des `PA`-Verzeichnisses:
    ```sh
    sudo chmod o+w PA/
    ```

8. Initialisieren und migrieren die Datenbank:
    ```sh
    flask db init
    flask db migrate
    flask db upgrade
    ```

## Konfiguration des Systemdienstes

1. Erstelle und bearbeite die Datei `/etc/systemd/system/vcid.service`:
    ```sh
    sudo nano /etc/systemd/system/vcid.service
    ```

    Inhalt der Datei:
    ```ini
    [Unit]
    Description=Gunicorn instance to serve VCID_APP
    After=network.target

    [Service]
    User=root
    Group=www-data
    WorkingDirectory=/vcid/PA
    Environment="PATH=/vcid/PA/myenv/bin"
    ExecStart=/vcid/PA/myenv/bin/gunicorn --workers 3 --bind unix:vcid.sock -m 007 app:app

    [Install]
    WantedBy=multi-user.target
    ```

2. Lade die Systemd-Daemon neu und starte den Dienst:
    ```sh
    sudo systemctl daemon-reload
    sudo systemctl start vcid.service
    sudo systemctl enable vcid.service
    ```

## Konfiguration von Nginx

1. Erstelle und bearbeite die Datei `/etc/nginx/sites-available/vcid`:
    ```sh
    sudo nano /etc/nginx/sites-available/vcid
    ```

    Inhalt der Datei:
    ```nginx
    server {
        listen 80;

        location / {
            include proxy_params;
            proxy_pass http://unix:/vcid/PA/vcid.sock;
        }
    }
    ```

2. Aktiviere die Nginx-Site und testen die Konfiguration:
    ```sh
    sudo ln -s /etc/nginx/sites-available/vcid /etc/nginx/sites-enabled
    sudo nginx -t
    sudo rm /etc/nginx/sites-enabled/default
    sudo systemctl restart nginx
    ```
