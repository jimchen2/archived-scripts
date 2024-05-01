# /src/middlewares/auth_middleware.cr
require "../config"
require "jwt"

module AuthMiddleware
  SECRET_KEY = Config.jwt_secret_key

  # Checks if the provided JWT token is valid and sets the current user id in context
  def self.valid_token?(context : HTTP::Server::Context) : Bool
    authorization_header = context.request.headers["Authorization"]?
    return false unless authorization_header

    token = authorization_header.try(&.gsub("Bearer ", ""))
    return false unless token

    begin
      decoded_token = JWT.decode(token, SECRET_KEY, JWT::Algorithm::HS256)
      user_id = decoded_token.first["user_id"].as_i
      # Use the setter method provided by the context_extension.cr
      context.current_user_id = user_id
      true
    rescue
      false # Indicate an invalid token or issue with decoding
    end
  end

  # Middleware entry point for checking authentication
  def self.check_authentication(context : HTTP::Server::Context)
    if valid_token?(context)
      yield # Continue processing the request if the token is valid
    else
      # Respond with an error if the token is invalid
      context.response.content_type = "application/json"
      context.response.status_code = 401
      context.response.print({ error: "Unauthorized" }.to_json)
    end
  end
end
