# Public API Usage Guide

## List Users

To retrieve a list of all users in the system, you can use the following `GET` request:

```
curl -X GET http://localhost:8080/api/users
```

### Example Response:

```
[
    {"id":"3","username":"testuser1"},
    {"id":"4","username":"newuser"},
    ...
    {"id":"20","username":"newuser1231"}
]
```

This will return an array of JSON objects, each representing a user. The objects include properties such as `id` and `username`.

## List Specific User

To retrieve a list of all users in the system, you can use the following `GET` request:

```
curl -X GET http://localhost:8080/api/user/20
```

### Example Response:

```
{"id":"20","username":"newuser1231"}
```

## Sign Up a New User

If you want to create a new user account, you can do so by making a `POST` request with the desired username and password:

```
curl -X POST -H "Content-Type: application/json" -d '{"username":"newuser12313", "password":"password123"}' http://localhost:8080/api/auth/signup
```

### Example Response:

```
{"message":"User registered successfully","user_id":21}
```

This response indicates that the user has been successfully registered and provides the `user_id` of the new user.

## Log In as a User

To log in with an existing user account and receive an authentication token, issue a `POST` request with the username and password:

### Wrong Login

```
curl -X POST -H "Content-Type: application/json" -d '{"username":"newuser1231", "password":"1241241"}' http://localhost:8080/api/auth/login
{"error":"An error occurred: Error with return code: ARGON2_VERIFY_MISMATCH and value: -35"}
```

```
curl -X POST -H "Content-Type: application/json" -d '{"username":"h4ph5", "password":"1241241"}' http://localhost:8080/api/auth/login
{"error":"User not found"}
```

### Correct Login

```
curl -X POST -H "Content-Type: application/json" -d '{"username":"newuser1231", "password":"password123"}' http://localhost:8080/api/auth/login
```

### Example Response:

```
{
    "token":"eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJ1c2VyX2lkIjoyMCwiZXhwIjoxNzEwNTc0Njg1fQ.MLGO5P-bAsblryjacCohzbQn3wh9UBJIKnJ6zwsZ26Q",
    "user_id":20
}
```

## Get Videos

```
curl -X GET http://localhost:8080/api/videos
[{"id":"1","user_id":"20","title":"My Awesome Video"},{"id":"2","user_id":"20","title":"My Awesome Video"}]
```

## Get User's Videos

```
curl -X GET http://localhost:8080/api/user-videos/20
[{"id":"1","title":"My Awesome Video"},{"id":"2","title":"My Awesome Video"}]
```

## Validate Token

```
curl -X GET   -H "Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJ1c2VyX2lkIjo0MSwiZXhwIjoxNzEwNTk0MDM2fQ.eGCAkw65szFfsKDeasFQG9Abl_vZCCog9vQ6sGon0uc"  http://localhost:8080/api/auth/validate_token
{"user_id":41,"username":"aw343234234343bc"}
```
