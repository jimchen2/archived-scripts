require "json"
require "db"
require "pg"
require "../config"

class UserController
  DB_URL = Config.database_url

  def self.get_all_users(env)
    users = [] of Hash(String, String) # Updated type to String
    db = DB.open(DB_URL)
    begin
      db.query("SELECT id, username FROM users") do |rs|
        rs.each do
          users << {"id" => rs.read(Int32).to_s, "username" => rs.read(String)}
        end
      end
      env.response.content_type = "application/json"

      env.response.print(users.to_json)
    ensure
      db.close
    end
  end

  def self.get_user(env)
    user_id = env.params.url["id"].to_i
    user = {} of String => DB::Any?
    db = DB.open(DB_URL)
    begin
      db.query("SELECT id, username FROM users WHERE id = $1", user_id) do |rs|
        if rs.move_next
          user["id"] = rs.read(Int32).to_s
          user["username"] = rs.read(String)
        end
      end

      env.response.content_type = "application/json"
      if user.empty?
        env.response.status_code = 404
        env.response.print({error: "User not found"}.to_json)
      else
        JSON.build(env.response) do |json|
          json.object do
            user.each do |key, value|
              json.field key, value.to_s
            end
          end
        end
      end
    ensure
      db.close
    end
  end

  def self.update_user(env)
    requested_user_id = env.params.url["id"].to_i
    if env.current_user_id != requested_user_id
      env.response.status_code = 403 # Forbidden
      env.response.print({error: "Unauthorized: You cannot update this user."}.to_json)
      return
    end

    user_id = env.params.url["id"].to_i
    begin
      body = env.request.body.not_nil! # Ensure the body is not nil.
      params = JSON.parse(body)
      username_json = params["username"]?

      if username_json && !username_json.is_a?(Nil)
        username = username_json.as_s

        db = DB.open(DB_URL)
        db.exec("UPDATE users SET username = $1 WHERE id = $2", username, user_id)
        db.close
        env.response.content_type = "application/json"
        env.response.print({message: "User updated successfully"}.to_json)
      else
        env.response.status_code = 400
        env.response.print({error: "Invalid parameters"}.to_json)
      end
    rescue JSON::ParseException
      env.response.status_code = 400
      env.response.print({error: "Bad request"}.to_json)
    rescue NilAssertionError
      env.response.status_code = 400
      env.response.print({error: "Request body is missing"}.to_json)
    end
  end

  def self.delete_user(env)
    requested_user_id = env.params.url["id"].to_i
    # Authorization check
    if env.current_user_id != requested_user_id
      env.response.status_code = 403 # Forbidden
      env.response.print({error: "Unauthorized: You cannot delete this user."}.to_json)
      return
    end

    db = DB.open(DB_URL)
    begin
      db.exec("DELETE FROM users WHERE id = $1", requested_user_id)
      env.response.status_code = 204
    ensure
      db.close
    end
  end
end
