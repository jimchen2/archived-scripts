require "awscr-s3"
require "../config"

# Fetch the S3 credentials from the loaded configuration
access_key_id = Config.s3_access_key_id
secret_access_key = Config.s3_secret_access_key
endpoint = Config.s3_endpoint
region = Config.s3_region

client = Awscr::S3::Client.new(region: region, aws_access_key: access_key_id, aws_secret_key: secret_access_key, endpoint: endpoint)

bucket_name = Config.cloud_name 

# List objects in the bucket
begin
  client.list_objects(bucket_name).each do |resp|
    puts "Contents of the bucket '#{bucket_name}':"
    resp.contents.each do |object|
      puts " - #{object.key}"
    end
  end
rescue ex
  puts "An error occurred while trying to list files: #{ex.message}"
end
