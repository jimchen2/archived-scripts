sudo apt update && sudo apt upgrade -y
sudo apt install apt-transport-https ca-certificates curl sudo git build-essential software-properties-common -y
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg
echo "deb [arch=arm64 signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
sudo apt update
sudo apt install docker-ce docker-ce-cli containerd.io certbot -y
sudo adduser --disabled-password --gecos "" builduser
sudo usermod -aG sudo builduser
echo "builduser ALL=(ALL) NOPASSWD:ALL" | sudo tee -a /etc/sudoers

sudo apt install nginx
sudo systemctl enable --now nginx


### Copy nginx.conf to the /etc/nginx/nginx.conf    