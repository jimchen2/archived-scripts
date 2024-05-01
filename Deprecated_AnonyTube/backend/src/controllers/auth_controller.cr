require "json"
require "db"
require "pg"
require "jwt"
require "crystal-argon2"
require "../config"

class AuthController
  DB_URL     = Config.database_url
  SECRET_KEY = Config.jwt_secret_key

  def self.process_request_body(env)
    if body = env.request.body
      JSON.parse(body.gets_to_end)
    else
      raise "Request body is empty"
    end
  end

  def self.sign_up_user(env)
    db = DB.open(DB_URL)
    begin
      params = process_request_body(env)
      username = params["username"].to_s
      password = params["password"].to_s
      password_hash = Argon2::Password.create(password)
      user_id : Int32? = nil # Initialize user_id with nil

      db.transaction do
        db.query("INSERT INTO users (username, password_digest) VALUES ($1, $2) RETURNING id", username, password_hash) do |rs|
          if rs.move_next
            user_id = rs.read(Int32)
          end
        end
      end

      if user_id.nil?
        # Handle the error case where user_id wasn't assigned
        env.response.status_code = 500
        env.response.print({error: "Failed to register user"}.to_json)
        return
      else
        # Send a successful response with user ID
        env.response.content_type = "application/json"
        env.response.status_code = 201
        env.response.print({message: "User registered successfully", user_id: user_id}.to_json)
      end
    rescue JSON::ParseException
      env.response.status_code = 400
      env.response.print({error: "Invalid JSON format"}.to_json)
    rescue e
      env.response.status_code = 500
      env.response.print({error: "Unable to create user: #{e.message}"}.to_json)
    ensure
      db.close
    end
  end

  def self.login_user(env)
    db = DB.open(DB_URL)
    begin
      params = process_request_body(env)
      username = params["username"].to_s
      password = params["password"].to_s
      user_password_hash = ""
      user_id : Int32 = 0

      db.query("SELECT id, password_digest FROM users WHERE username = $1 LIMIT 1", username) do |rs|
        if rs.move_next # Use move_next to advance to the next row
          user_id, user_password_hash = rs.read(Int32), rs.read(String)
        else
          env.response.content_type = "application/json"
          env.response.status_code = 404
          env.response.print({error: "User not found"}.to_json)
          return
        end
      end

      if Argon2::Password.verify_password(password, user_password_hash)
        payload = {"user_id" => user_id, "exp" => Time.utc.to_unix + 7200}
        token = JWT.encode(payload, SECRET_KEY, JWT::Algorithm::HS256)
        env.response.content_type = "application/json"
        env.response.status_code = 200
        env.response.print({token: token, user_id: user_id}.to_json)
      else
        env.response.content_type = "application/json"
        env.response.status_code = 401
        env.response.print({error: "Invalid credentials"}.to_json)
      end
    rescue JSON::ParseException
      env.response.status_code = 400
      env.response.print({error: "Invalid JSON format"}.to_json)
    rescue e
      env.response.status_code = 500
      env.response.print({error: "An error occurred: #{e.message}"}.to_json)
    ensure
      db.close
    end
  end

  def self.validate_token(env)
    token = env.request.headers["Authorization"]?.try(&.gsub("Bearer ", ""))
    if token
      begin
        payload = JWT.decode(token, SECRET_KEY, JWT::Algorithm::HS256).first
        user_id = payload["user_id"].as_i

        db = DB.open(DB_URL)
        begin
          user = db.query_one?("SELECT id, username FROM users WHERE id = $1", user_id, as: {Int32, String})
          if user
            env.response.content_type = "application/json"
            env.response.status_code = 200
            env.response.print({user_id: user[0], username: user[1]}.to_json)
          else
            env.response.content_type = "application/json"
            env.response.status_code = 404
            env.response.print({error: "User not found"}.to_json)
          end
        ensure
          db.close
        end
      rescue
        env.response.content_type = "application/json"
        env.response.status_code = 401
        env.response.print({error: "Invalid or expired token"}.to_json)
      end
    else
      env.response.content_type = "application/json"
      env.response.status_code = 401
      env.response.print({error: "Authorization token required"}.to_json)
    end
  end
end
