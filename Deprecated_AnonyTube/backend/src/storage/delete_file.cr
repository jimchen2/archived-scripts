# src/storage/delete_file.cr
require "awscr-s3"
require "../config"

module Storage
  @@client = Awscr::S3::Client.new(
    region: Config.s3_region,
    aws_access_key: Config.s3_access_key_id,
    aws_secret_key: Config.s3_secret_access_key,
    endpoint: Config.s3_endpoint
  )

  def self.delete_file(file_name : String) : Nil
    bucket_name = Config.cloud_name
    begin
      response = @@client.delete_object(bucket_name, file_name)
      puts "File '#{file_name}' successfully deleted."
    rescue ex
      puts "An error occurred while trying to delete the file: #{ex.message}"
    end
  end
end
