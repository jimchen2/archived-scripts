# Storage API Usage Guide

## Getting Presigned Urls


```
curl "http://localhost:8080/api/storage/presigned_url?file_name=my_video.mp4"
{"error":"Unauthorized"}
```

With a Bearer

```
curl -X GET   -H "Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJ1c2VyX2lkIjo0NSwiZXhwIjoxNzEwNjUzMTg3fQ.6NyKOrRXyZkANwJai7NVkkSV7IgI0ZLi6aBwVJP0DCw"  http://localhost:8080/api/storage/presigned_url?file_name=my_video.mp4
{"presigned_url":"https://ee64074f404e392345763d53572d3d2e.r2.cloudflarestorage.com/my-cloud/my_video.mp4?AWSAccessKeyId=82e476fd74148c090d0e64ca4ee05f2a&Signature=CJHHe7fGHPGy%2FD2CkqoxzWtz5Ks%3D&Expires=1710649648"}
```

