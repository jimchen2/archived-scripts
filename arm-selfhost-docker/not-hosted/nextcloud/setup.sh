# create the docker-compose.yml and in the same dir

sudo docker-compose up -d 

## Open the TCP Port 7001

sudo systemctl stop nginx ufw
sudo certbot certonly --standalone -d nextcloud.jimchen.me --email jimchen4214@gmail.com --non-interactive --agree-tos 
sudo systemctl restart ufw

### Configure  /etc/nginx/sites-available/nextcloud
sudo ln -s /etc/nginx/sites-available/nextcloud /etc/nginx/sites-enabled/
