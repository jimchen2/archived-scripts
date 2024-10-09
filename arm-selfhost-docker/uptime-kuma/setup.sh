docker volume create uptime-kuma
docker run -d --restart=always -p 7004:3001 -v uptime-kuma:/app/data --name uptime-kuma louislam/uptime-kuma:1

### Lets encrypt 
sudo systemctl stop nginx ufw
sudo certbot certonly --standalone -d status.jimchen.me --email jimchen4214@gmail.com --non-interactive --agree-tos 
sudo systemctl restart ufw


### Configure  /etc/nginx/sites-available/uptime-kuma
sudo ln -s /etc/nginx/sites-available/uptime-kuma /etc/nginx/sites-enabled/
