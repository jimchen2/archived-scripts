# 课程管理系统

- 超级管理员（superadmin）创建课程、教师、项目和论文
  - ID: -1
  - 密码: "password"(为方便起见,I didn't implement changing passwords)
  - 登录主页后可进入管理面板（admin panel）编辑系统信息，如添加教师账号
- 教师创建完毕后可正常登录，但只能管理自己的项目、课程和论文
- 密码使用Argon2算法🔒进行哈希处理
  - 服务器仅存储密码哈希值，不存储明文
- 登录成功后，返回JWT令牌并存储在localStorage中用于身份验证
  - 令牌定期过期以增强安全性
- 前端：[React Bootstrap](https://react-bootstrap.github.io/)
- 后端：Node.js


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


```
Test 1: Superadmin Log in
Test 2: Create a teacher and logging in as the teacher
Test 3: Create a teacher and logging in with false password(assume can't)
Test 4: Delete a teacher and try logging in again(assume can't)
Test 5: Test after Logging in a teacher is authorized(token), and test if an unauthorized teacher can get authenticated(false)
Test 6: Create duplicated teachers with the same ID(should return error)

Projects: (only Superadmin can create projects, teachers only add/remove themselves from projects)
Test 7: Create a teacher, create a project
Test 8: Create 3 projects, find one, list(should return 3)
Test 9: Create 3 projects, delete one, find the deleted(should error)
Test 10: Create 3 projects, change one, search(shall be changed)
Test 11: Create a teacher, create a project, teacher add themself to project
Test 12: Create a teacher, create 2 projects, teacher add themself to both
Test 13: Create 2 teachers, create 2 projects, teacher 1 add themself to project 1
```

# 关于项目

这个项目使用 Express.js 实现了一个后端服务器，用于管理各种实体，如教师、论文、项目、参与者和课程。服务器还集成了身份验证和授权机制，以确保对其端点的安全访问。以下是实现的详细概述：

## 主要组件

### Express 服务器设置

- 使用 Express.js（一个 Node.js 的极简 Web 框架）创建服务器。
- 启用 CORS 以允许前端的跨域请求，并针对来源和凭证进行特定配置。

### 环境配置

- 使用 dotenv 加载环境变量，以管理数据库凭据和 JWT 密钥等配置设置。

### 数据库初始化

- 通过单独的模块初始化数据库，以确保与 MariaDB 数据库的连接。
- 创建连接池以提高数据库操作的效率。

### 中间件

- JSON 解析: 用于解析 JSON 请求的中间件。
- CORS: 配置以允许来自指定前端 URL 的请求。
- 身份验证和授权: 使用基于 JWT 的身份验证，并使用中间件处理授权和超级管理员权限检查。
- 错误处理: 中间件处理身份验证错误并记录身份验证信息。

### 路由

- 定义了单独的路由器来处理各种实体，如教师、论文、项目、参与者和课程。
- 每个路由器处理 CRUD 操作，并在必要时强制执行身份验证和授权。

### 数据库查询

- 使用预处理语句进行安全的数据库查询。
- 辅助函数确保数据完整性和正确处理数据类型（例如，将 BigInt 转换为字符串）。

### 身份验证

- 使用 JWT 进行基于令牌的身份验证。
- 使用 argon2 安全地对密码进行哈希处理，然后将其存储在数据库中。
- 登录端点验证凭据并发放 JWT 令牌。

## 示例路由和功能

### 教师路由 (/routes/teachers.js)

#### 创建教师

```javascript
router.post("/", auth, checkSuperadmin, async (req, res) => {
  // 验证和插入逻辑
});
```
获取所有教师
```javascript
router.get("/", auth, checkSuperadmin, async (req, res) => {
  try {
    const query = "SELECT * FROM teachers";
    const results = await db.query(query);
    res.status(200).send(results);
  } catch (err) {
    console.error(err);
    res.status(500).send("Error fetching teachers");
  }
});
```