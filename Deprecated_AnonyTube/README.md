users.sql:
```
CREATE TABLE users (
id SERIAL PRIMARY KEY,
username VARCHAR(255) UNIQUE NOT NULL,
password_digest TEXT NOT NULL
);
```
videos.sql:
```
CREATE TABLE videos (
id SERIAL PRIMARY KEY,
user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
title VARCHAR(255) NOT NULL,
uploaded_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);
```


Intialization
```
-- Run these commands in your PostgreSQL client or terminal
CREATE DATABASE video_app_db;

\c video_app_db

CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(255) UNIQUE NOT NULL,
    password_digest TEXT NOT NULL
);

CREATE TABLE videos (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    title VARCHAR(255) NOT NULL,
    uploaded_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);
```


```
# Public routes
get "/api/users", &->UserController.get_all_users(HTTP::Server::Context)
get "/api/user/:id", &->UserController.get_user(HTTP::Server::Context)
post "/api/auth/signup", &->AuthController.sign_up_user(HTTP::Server::Context)
post "/api/auth/login", &->AuthController.login_user(HTTP::Server::Context)
get "/api/videos", &->VideoController.get_all_videos(HTTP::Server::Context)
get "/api/user-videos/:user_id", &->VideoController.get_videos_by_user(HTTP::Server::Context)

# Protected routes with authentication checks
post "/api/user-videos/:user_id" do |env|
  AuthMiddleware.check_authentication(env) do
    VideoController.create_video(env)
  end
end

put "/api/user/:id" do |env|
  AuthMiddleware.check_authentication(env) do
    UserController.update_user(env)
  end
end

delete "/api/user/:id" do |env|
  AuthMiddleware.check_authentication(env) do
    UserController.delete_user(env)
  end
end

put "/api/video/:video_id" do |env|
  AuthMiddleware.check_authentication(env) do
    VideoController.update_video(env)
  end
end

delete "/api/video/:video_id" do |env|
  AuthMiddleware.check_authentication(env) do
    VideoController.delete_video(env)
  end
end

```