require "yaml"

module Config
  CONFIG_FILE_PATH = "config.yml"
  @@config : YAML::Any?

  def self.load : YAML::Any
    @@config ||= begin
      YAML.parse(File.read(CONFIG_FILE_PATH))
    rescue
      raise "Configuration file not found or invalid."
    end
  end

  def self.database_url : String
    load["database_url"].as_s
  end

  def self.jwt_secret_key : String
    load["jwt_secret_key"].as_s
  end

  def self.port : Int32
    load["port"].as_i
  end

  def self.cloud_name : String
    load["cloud_name"].as_s
  end

  def self.public_url : String
    load["public_url"].as_s
  end

  def self.s3_credentials : Hash(String, String)
    load["s3_credentials"].as_h.to_h { |key, value| {key.to_s, value.as_s} }
  end

  def self.s3_access_key_id : String
    s3_credentials["access_key_id"]
  end

  def self.s3_secret_access_key : String
    s3_credentials["secret_access_key"]
  end

  def self.s3_endpoint : String
    s3_credentials["endpoint"]
  end

  def self.s3_region : String
    s3_credentials["region"]
  end
end
