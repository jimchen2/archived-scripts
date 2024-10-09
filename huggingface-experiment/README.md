
## Install
```
pip install diffusers accelerate transformers protobuf sentencepiece Pillow
apt install -y vim jq
huggingface-cli login
```

## Note

1. Please don't "bloat' the notebooks. 

Please don't carry the images in stable diffusion models, they are hugely bloated and the Notebook size can be over 300 MB, instead, upload to S3 and deliver via Cloudfront

2. Please choose a higher-end GPU, like H100, or else it takes very long for inference to run

3. Please choose a GPU with high network downloading speed, or else it takes forever for models to download

4. Please allocate a lot of Disk space for the models to download