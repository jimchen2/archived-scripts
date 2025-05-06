```
sudo fallocate -l "2G" /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile
echo "/swapfile swap swap defaults 0 0" | sudo tee -a /etc/fstab

sudo apt update && sudo apt upgrade -y
sudo apt install git build-essential npm nginx certbot gnupg curl screen mariadb-server -y

curl -fsSL https://deb.nodesource.com/setup_22.x | sudo bash -
sudo apt install nodejs -y

sudo useradd -m builduser
sudo passwd -d builduser
echo 'builduser ALL=(ALL) NOPASSWD: ALL' | sudo tee /etc/sudoers.d/builduser

sudo systemctl enable --now mariadb
```
##################################################################
```
sudo mkdir -p /var/www; sudo git clone https://github.com/jimchen2/ustc-db-course-new-nextjs /var/www/Website; sudo chown -R builduser:builduser /var/www/Website

# Configure password for database

# mysql -u root -p -e "GRANT ALL PRIVILEGES ON *.* TO 'root'@'localhost' IDENTIFIED BY 'your_root_password'; FLUSH PRIVILEGES;"

sudo -u builduser bash -c 'cd /var/www/Website; npm install;npx prisma migrate dev --name init;npm run build;'

sudo systemctl stop nginx
sudo systemctl stop ufw
sudo certbot certonly --standalone -d jimchen.uk --email jimchen4214@gmail.com --non-interactive --agree-tos
sudo systemctl start ufw

mkdir -p /etc/nginx/{sites-available,sites-enabled} && sudo ln -sf /etc/nginx/sites-available/website.conf /etc/nginx/sites-enabled/
sudo cp /var/www/Website/website.conf /etc/nginx/sites-available/website.conf
sudo cp /var/www/Website/nginx.conf /etc/nginx/nginx.conf
sudo systemctl enable --now nginx

sudo cp /var/www/Website/website.service /etc/systemd/system/website.service
sudo cp /var/www/Website/update-website.service /etc/systemd/system/
sudo systemctl daemon-reload && sudo systemctl enable --now website.service
```
