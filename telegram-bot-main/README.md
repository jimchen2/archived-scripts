```
# Clear all proxy variables
set -e ALL_PROXY HTTP_PROXY HTTPS_PROXY all_proxy http_proxy https_proxy

# Set to HTTP on port 7897
set -gx ALL_PROXY http://127.0.0.1:7897
set -gx HTTP_PROXY http://127.0.0.1:7897
set -gx HTTPS_PROXY http://127.0.0.1:7897

# Verify
env | grep -i proxy

# Run your bot
python shit.py
```