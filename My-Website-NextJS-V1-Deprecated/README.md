## Install

```sh
# configure .env
docker run -d --restart always --env-file .env -p 3010:3000 jimchen2/my-website:latest
```

## Build

```sh
# add Dockerfile
docker build --no-cache -t jimchen2/my-website:latest .
```

build then push
```sh
sudo docker build --no-cache -t jimchen2/my-website:latest . && docker push jimchen2/my-website:latest
```
