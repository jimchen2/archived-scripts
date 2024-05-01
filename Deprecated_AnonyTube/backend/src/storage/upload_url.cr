require "awscr-s3"
require "../config"

access_key_id = Config.s3_access_key_id
secret_access_key = Config.s3_secret_access_key
endpoint = Config.s3_endpoint
region = Config.s3_region
bucket_name = Config.cloud_name

# Initialize the S3 client
client = Awscr::S3::Client.new(region: region, aws_access_key: access_key_id, aws_secret_key: secret_access_key, endpoint: endpoint)

# Method to create a presigned URL for uploading files
def create_presigned_upload_url(client : Awscr::S3::Client, bucket_name : String, file_name : String)
  # Calculate expiry time (e.g., 15 minutes from now)
  expiry_time = Time.now + 15.minutes
  
  presigned_url = client.presigned_put_url(bucket_name, file_name, expires_in: expiry_time.to_unix)
  
  presigned_url
end
begin
  url = create_presigned_upload_url(client, bucket_name, file_name)
  puts "Presigned URL for uploading '#{file_name}' to '#{bucket_name}': #{url}"
rescue ex
  puts "An error occurred while generating the presigned URL: #{ex.message}"
end
