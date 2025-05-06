## teacher-management-tool

1. Install

```
sudo pacman -Syu
sudo pacman -S nodejs mariadb
sudo mariadb-install-db --user=mysql --ldata=/var/lib/mysql
sudo systemctl start mariadb
```

2. create a database and give privilege

```
sudo mariadb -u root
```

Generate a random password

```
openssl rand -hex 32
```

Then

```
CREATE DATABASE teacher_management;
CREATE USER 'teacher_management_user'@'localhost' IDENTIFIED BY 'c011d1518d1ca1d58ee3ad7e978eb3fe5058c87785daca25314e1cb3b5fd074f';
GRANT ALL PRIVILEGES ON teacher_management.* TO 'teacher_management_user'@'localhost';
FLUSH PRIVILEGES;
exit
```

Drop the user and database

```
DROP USER 'teacher_management_user'@'localhost';
DROP DATABASE teacher_management;
```

3. Upate the `backend/.env` file, example(update it like initialized)

```
DB_HOST=localhost
DB_USER=teacher_management_user
DB_PASSWORD=c011d1518d1ca1d58ee3ad7e978eb3fe5058c87785daca25314e1cb3b5fd074f#openssl rand -hex 32
DB_NAME=teacher_management
PORT=5000
JWT_SECRET=7e4b24f95dbbd7cbf3f7435fc96148f3db1cba4b07aa01aed7748770a3f2e6f2#openssl rand -hex 32

```
4. Start Backend
```
node src/app.js
```

## Code Structure

```
.
├── README.md
├── backend
│   ├── node_modules
│   ├── package-lock.json
│   ├── package.json
│   ├── src
│   └── test
├── db-lab03.pdf
└── frontend
    ├── README.md
    ├── node_modules
    ├── package-lock.json
    ├── package.json
    ├── public
    └── src
```

frontend: react frontendv
backend: nodejs backend 
backend/src: backend code
backend/test: backend tests

Run `npm test` in backend folder 

The test specs are in  [This file](./backend/test/README.md)