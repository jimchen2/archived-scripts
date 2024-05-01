require "kemal"
require "./config"
require "./routes" # Routes are defined separately
require "./extensions/context_extension"

# Load configuration settings
Config.load

# Configure Kemal server with settings from Config module
Kemal.config do |config|
  config.port = Config.port
end

before_all do |env|
  env.response.headers.add("Access-Control-Allow-Origin", "*")
  env.response.headers.add("Access-Control-Allow-Methods", "GET, POST, PUT, DELETE, OPTIONS")
  env.response.headers.add("Access-Control-Allow-Headers", "Content-Type, Authorization")
  # Include credentials only if you are using cookies or auth headers
  env.response.headers.add("Access-Control-Allow-Credentials", "true") 
end

# Correct catch-all OPTIONS route for handling preflight requests
options "/*" do |env|
  env.response.content_type = "application/json"
  env.response.status_code = 200
  env.response.print("{}")
end


# Define routes
get "/" do |env|
  "Hello, Kemal!"
end

# Additional routes...

# Start Kemal server
Kemal.run
