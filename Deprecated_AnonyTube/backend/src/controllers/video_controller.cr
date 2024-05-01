require "json"
require "db"
require "pg"
require "../config"

class VideoController
  DB_URL = Config.database_url

  # Fetches all videos from the database
  def self.get_all_videos(env)
    videos = [] of Hash(String, String) # Ensure consistent type for JSON serialization
    db = DB.open(DB_URL)
    begin
      db.query("SELECT id, user_id, title, uploaded_at FROM videos") do |rs|
        rs.each do
          # Convert numeric types to String for JSON compatibility and include uploaded_at
          videos << {
            "id"          => rs.read(Int32).to_s,
            "user_id"     => rs.read(Int32).to_s,
            "title"       => rs.read(String),
            "uploaded_at" => rs.read(Time).to_rfc3339, # Format time as RFC3339 string
          }
        end
      end
      env.response.content_type = "application/json"
      env.response.print(videos.to_json)
    ensure
      db.close
    end
  end

  # Fetches videos by a specific user
  def self.get_videos_by_user(env)
    user_id = env.params.url["user_id"].to_i
    query = "SELECT id, title, uploaded_at FROM videos WHERE user_id = $1"
    videos = [] of Hash(String, String)
    db = DB.open(DB_URL)
    begin
      db.query(query, user_id) do |rs|
        rs.each do
          # Convert numeric types to String for JSON compatibility and include uploaded_at
          videos << {
            "id"          => rs.read(Int32).to_s,
            "title"       => rs.read(String),
            "uploaded_at" => rs.read(Time).to_rfc3339, # Format time as RFC3339 string
          }
        end
      end
      env.response.content_type = "application/json"
      env.response.print(videos.to_json)
    rescue e
      puts "Exception: #{e.message}" # Output any exception message
    ensure
      db.close
    end
  end

  # Creates a new video entry
  def self.create_video(env)
    requested_user_id = env.params.url["user_id"].to_i
    # Authorization check
    if env.current_user_id != requested_user_id
      env.response.content_type = "application/json"
      env.response.status_code = 403 # Forbidden
      env.response.print({error: "Unauthorized: You cannot create videos for this user."}.to_json)
      return
    end

    begin
      params = JSON.parse(env.request.body.not_nil!)
      title = params["title"].to_s
      db = DB.open(DB_URL)

      db.exec("INSERT INTO videos (user_id, title) VALUES ($1, $2)", requested_user_id, title)

      env.response.content_type = "application/json"
      env.response.status_code = 201
      env.response.print({message: "Video created successfully"}.to_json)
    rescue e
      puts "Exception: #{e.message}"
      env.response.content_type = "application/json"
      env.response.status_code = 500
      env.response.print({error: e.message}.to_json)
    ensure
      db.close if db
    end
  end

  # Fetches a single video
  def self.get_video(env)
    video_id = env.params.url["video_id"].to_i
    video = {} of String => String
    db = DB.open(DB_URL)
    begin
      db.query("SELECT id, user_id, title, uploaded_at FROM videos WHERE id = ?", video_id) do |rs|
        if rs.move_next
          video["id"] = rs.read(Int32).to_s
          video["user_id"] = rs.read(Int32).to_s
          video["title"] = rs.read(String)
          video["uploaded_at"] = rs.read(Time).to_rfc3339 # Format time as RFC3339 string
        end
      end

      if video.empty?
        env.response.status_code = 404
        env.response.print({error: "Video not found"}.to_json)
      else
        env.response.content_type = "application/json"
        env.response.print(video.to_json)
      end
    ensure
      db.close
    end
  end

  # Updates an existing video
  def self.update_video(env)
    if (current_user_id = env.current_user_id)
      auth_user_id = current_user_id.to_i
      video_id = env.params.url["video_id"].to_i
      begin
        params = JSON.parse(env.request.body.not_nil!)
        title_json = params["title"]?

        if title_json.is_a?(JSON::Any) && (title = title_json.as_s?)
          db = DB.open(DB_URL)

          # Safe parameterized SQL UPDATE statement
          update_sql = "UPDATE videos SET title = $1 WHERE id = $2 AND user_id = $3"
          result = db.exec(update_sql, title, video_id, auth_user_id)

          if result.rows_affected == 0
            env.response.status_code = 403 # Forbidden, or no changes made
            env.response.print({error: "Unauthorized or video not found"}.to_json)
          else
            env.response.content_type = "application/json"
            env.response.print({message: "Video updated successfully"}.to_json)
          end
          db.close
        else
          env.response.status_code = 400
          env.response.print({error: "Invalid or missing title"}.to_json)
        end
      rescue JSON::ParseException
        env.response.status_code = 400
        env.response.print({error: "Invalid JSON format"}.to_json)
      end
    else
      env.response.status_code = 401 # Unauthorized
      env.response.print({error: "You must be logged in to perform this action"}.to_json)
    end
  end

  # Deletes a video
  def self.delete_video(env)
    auth_user_id = env.current_user_id.not_nil!.to_i
    video_id = env.params.url["video_id"].to_i
    db = DB.open(DB_URL)
    begin
      # Safe parameterized SQL DELETE statement
      delete_sql = "DELETE FROM videos WHERE id = $1 AND user_id = $2"

      result = db.exec(delete_sql, video_id, auth_user_id)
      if result.rows_affected == 0
        env.response.status_code = 403 # Forbidden, or no changes made
        env.response.print({error: "Unauthorized or video not found"}.to_json)
      else
        env.response.status_code = 204 # No content
      end
    ensure
      db.close
    end
  end
end
