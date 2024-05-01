# src/storage/check_existence.cr
require "awscr-s3"
require "../config"

module Storage
  @@client = Awscr::S3::Client.new(
    region: Config.s3_region,
    aws_access_key: Config.s3_access_key_id,
    aws_secret_key: Config.s3_secret_access_key,
    endpoint: Config.s3_endpoint
  )

  def self.check_existence(file_name : String) : Bool
    bucket_name = Config.cloud_name
    begin
      @@client.head_object(bucket_name, file_name)
      true 
    rescue ex
      return false if ex.message.to_s.includes?("NoSuchKey")
      puts "An error occurred while checking the file: #{ex.message}"
      false
    end
  end
end
