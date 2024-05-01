# src/controllers/storage_controller.cr
require "../storage/generate_upload_url"
require "json"

class StorageController
  def self.generate_presigned_url(env)
    # Extract file_name from query parameters
    file_name = env.params.query["file_name"]? || "default-filename.txt"
    
    # Call the generate_upload_url method from the Storage module
    presigned_url = Storage.generate_upload_url(file_name)
    
    # Return the presigned_url in a JSON response
    env.response.content_type = "application/json"
    env.response.status_code = 200
    env.response.print({ presigned_url: presigned_url }.to_json)
  rescue ex
    env.response.content_type = "application/json"
    env.response.status_code = 500
    env.response.print({ error: ex.message }.to_json)
  end
end
