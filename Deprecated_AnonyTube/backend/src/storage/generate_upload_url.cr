require "json"
require "../config"

module Storage
  def self.generate_upload_url(file_name : String, expires_in : UInt32 = 3600) : String
    endpoint_url = Config.s3_endpoint
    bucket = Config.cloud_name
    access_key_id = Config.s3_access_key_id
    secret_access_key = Config.s3_secret_access_key
    region = Config.s3_region

    # Directly embedding the Python script within a Bash command
    bash_command = <<-CMD
    python -c "import boto3; from botocore.client import Config; session = boto3.Session(region_name='#{region}'); s3 = session.client('s3', config=Config(signature_version='s3v4'), endpoint_url='#{endpoint_url}', aws_access_key_id='#{access_key_id}', aws_secret_access_key='#{secret_access_key}'); presigned_url = s3.generate_presigned_url('put_object', Params={'Bucket': '#{bucket}', 'Key': '#{file_name}'}, ExpiresIn=#{expires_in}); print(presigned_url)"
    CMD

    # Execute the Bash command and capture the output
    result = `#{bash_command}`

    if $?.success?
      result.strip
    else
      raise "Error generating presigned URL: #{result}"
    end
  end
end
