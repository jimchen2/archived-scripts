require "./controllers/user_controller"
require "./controllers/video_controller"
require "./controllers/auth_controller"
require "./controllers/storage_controller"
require "./middlewares/auth_middleware"
require "kemal"

# Public routes
get "/api/users", &->UserController.get_all_users(HTTP::Server::Context)
get "/api/user/:id", &->UserController.get_user(HTTP::Server::Context)
post "/api/auth/signup", &->AuthController.sign_up_user(HTTP::Server::Context)
post "/api/auth/login", &->AuthController.login_user(HTTP::Server::Context)
get "/api/auth/validate_token", &->AuthController.validate_token(HTTP::Server::Context)
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

# Storage Routes
get "/api/storage/presigned_url" do |env|
  AuthMiddleware.check_authentication(env) do
    StorageController.generate_presigned_url(env)
  end
end
