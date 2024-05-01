# Private API Usage Guide

## Post Videos
```
curl -X POST "http://localhost:8080/api/user-videos/20"      -H "Content-Type: application/json"      -H "Authorization: Bearer 12345"      -d '{"title": "A Video"}'
{"error":"Unauthorized"}
```

### Authorize by login
```
curl -X POST -H "Content-Type: application/json" -d '{"username":"newuser1231", "password":"password123"}' http://localhost:8080/api/auth/login
{"token":"eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJ1c2VyX2lkIjoyMCwiZXhwIjoxNzEwNTc2OTQ5fQ.8JJUnBYxRSb2gXmBTmSZD6UmS3AaK1bDwpka_x41Rak","user_id":20}
```
### Then
```
curl -X POST "http://localhost:8080/api/user-videos/20"      -H "Content-Type: application/json"      -H "Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJ1c2VyX2lkIjoyMCwiZXhwIjoxNzEwNTc2OTQ5fQ.8JJUnBYxRSb2gXmBTmSZD6UmS3AaK1bDwpka_x41Rak"      -d '{"title": "A Video"}'
{"message":"Video created successfully"}
```

## Update Username

```
curl -X PUT "http://localhost:8080/api/user/18"      -H "Content-Type: application/json"      -H "Authorization: Bearer 12345"      -d '{"username": "New User"}'
{"error":"Unauthorized"}
```
### With the bearer
```
curl -X PUT "http://localhost:8080/api/user/20"      -H "Content-Type: application/json"      -H "Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJ1c2VyX2lkIjoyMCwiZXhwIjoxNzEwNTc2OTQ5fQ.8JJUnBYxRSb2gXmBTmSZD6UmS3AaK1bDwpka_x41Rak"      -d '{"username": "New User"}'
{"message":"User updated successfully"}
```
### Listing the username
```
curl -X GET http://localhost:8080/api/user/20
{"id":"20","username":"New User"}
```
## Update Video
```
curl -X PUT "http://localhost:8080/api/video/1" \
     -H "Content-Type: application/json" \
     -H "Authorization: Bearer [Your_Token_Here]" \
     -d '{"title": "Updated Video Title"}'
{"error":"Unauthorized"}
```
### With Bearer
```
curl -X PUT "http://localhost:8080/api/video/1" \
     -H "Content-Type: application/json" \
     -H "Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJ1c2VyX2lkIjoyMCwiZXhwIjoxNzEwNTc2OTQ5fQ.8JJUnBYxRSb2gXmBTmSZD6UmS3AaK1bDwpka_x41Rak" \
     -d '{"title": "Updated Video Title"}'
{"message":"Video updated successfully"}
```
```
[{"id":"2","user_id":"20","title":"My Awesome Video"},{"id":"7","user_id":"20","title":"A Video"},{"id":"8","user_id":"20","title":"A Video"},{"id":"3","user_id":"18","title":"Hello World"},{"id":"1","user_id":"20","title":"Updated Video Title"}]
```
## Delete Video
```
curl -X DELETE "http://localhost:8080/api/video/1" \
     -H "Content-Type: application/json" \
     -H "Authorization: Bearer [Your_Token_Here]" 
{"error":"Unauthorized"}
```
### With Bearer
```
curl -X DELETE "http://localhost:8080/api/video/1" \
     -H "Content-Type: application/json" \
     -H "Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJ1c2VyX2lkIjoyMCwiZXhwIjoxNzEwNTc2OTQ5fQ.8JJUnBYxRSb2gXmBTmSZD6UmS3AaK1bDwpka_x41Rak" \
```

## Delete User
```
curl -X DELETE "http://localhost:8080/api/user/20" -H "Authorization: Bearer [Your_Token_Here]"
{"error":"Unauthorized"}
```
### With Bearer
```
curl -X DELETE "http://localhost:8080/api/user/20" -H "Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJ1c2VyX2lkIjoyMCwiZXhwIjoxNzEwNTc2OTQ5fQ.8JJUnBYxRSb2gXmBTmSZD6UmS3AaK1bDwpka_x41Rak"
```
### Listing the username
```
curl -X GET http://localhost:8080/api/user/20
{"error":"User not found"} 
```