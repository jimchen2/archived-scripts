# Extend the HTTP::Server::Context with additional functionality
class HTTP::Server::Context
  # Define a property `current_user_id` which is nil by default
  property current_user_id : Int32?
end
