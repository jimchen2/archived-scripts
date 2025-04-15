## Personal Blog

- **_scripts/**: Utility scripts 
  - `dump.py`: Show blog data.
  - `image_upload_to_s3.py`
  - `import_mongo.py`: Updates data to MongoDB.
  - `requirements.txt
- **.github/workflows/**: CI/CD configuration for automatically updating data on push

- **non_english/**: 
  - **de/**: German posts
  - **ru/**: Russian posts
  - **zh/**: Chinese posts
- other folders: 
 - **[type]/[title].md**

## Front-matter format

```markdown
---
date: YYYYMMDD
uuid: #openssl rand -hex 16
---
```

## Schema

```
{
  uuid: {
    type: String,
    default: "",
  },
  title: {
    type: String,
    default: "",
  },
  date: {
    type: Date,  
    default: Date.now,  
  },
  type: {
    type: String,
    default: "",
  },
  body: {
    type: String,
    default: "",
  },
  language: {
    type: String,
    default: "en",
  },
  word_count: {
    type: Number,
  },
},
```