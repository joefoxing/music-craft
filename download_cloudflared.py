import urllib.request
import os
import sys

url = 'https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-windows-amd64.exe'
dest = os.path.expanduser('~/.cloudflared/cloudflared.exe')
os.makedirs(os.path.dirname(dest), exist_ok=True)

print(f'Downloading cloudflared from {url}')
print(f'Destination: {dest}')

try:
    urllib.request.urlretrieve(url, dest)
    print('Download completed.')
    # Verify file size
    size = os.path.getsize(dest)
    print(f'File size: {size} bytes')
except Exception as e:
    print(f'Download failed: {e}')
    sys.exit(1)