<h1 style="font-size: 3em;">Flask-Inventarliste</h1>
<h2 style="font-size: 3em;">Allgemeine Anleitung</h2>
https://www.digitalocean.com/community/tutorials/how-to-serve-flask-applications-with-gunicorn-and-nginx-on-ubuntu-18-04
<h2 style="font-size: 3em;">Commands</h2>
mkdir /vcid
cd /vcid
git clone GITHUB-LINK
cd PA
sudo apt update
sudo apt install python3-full python3-pip python3-dev build-essential libssl-dev libffi-dev python3-setuptools
sudo apt install python3-venv
sudo apt install nginx
sudo apt install mysql-server -> Installanleitung: https://www.digitalocean.com/community/tutorials/how-to-install-mysql-on-ubuntu-20-04-de
python3 -m venv myvenv
source myvenv/bin/activate
sudo myenv/bin/pip install -r requirements.txt
sudo chmod o+w PA/
flask db init
flask db migrate
flask db upgrade

sudo nano /etc/systemd/system/vcid.service
################################################# Inhalt vcid.service
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
#################################################

sudo systemctl daemon-reload
sudo systemctl start vcid.service
sudo systemctl enable vcid.service

sudo nano /etc/nginx/sites-available/vcid
################################################# Inhalt vcid
server {
    listen 80;

    location / {
        include proxy_params;
        proxy_pass http://unix:/vcid/PA/vcid.sock;
    }
}

#################################################

sudo ln -s /etc/nginx/sites-available/vcid /etc/nginx/sites-enabled
sudo nginx -t
sudo rm /etc/nginx/sites-enabled/default
sudo systemctl restart nginx
