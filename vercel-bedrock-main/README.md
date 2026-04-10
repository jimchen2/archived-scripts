## Build and Install

```
docker build --no-cache -t jimchen2/vercel-bedrock .
docker run -d --restart always --env-file .env -p 3210:3000 jimchen2/vercel-bedrock:latest
docker push jimchen2/vercel-bedrock
docker system prune -af
```
