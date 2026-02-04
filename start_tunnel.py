import subprocess
import threading
import time
import sys
import os

def read_output(pipe, identifier):
    for line in iter(pipe.readline, ''):
        line = line.strip()
        if line:
            print(f'[{identifier}] {line}')
            sys.stdout.flush()
            # Check for tunnel URL
            if 'https://' in line and ('.trycloudflare.com' in line or '.cfargotunnel.com' in line):
                print(f'Found tunnel URL: {line}')
                # Extract URL
                import re
                match = re.search(r'https?://[^\s]+', line)
                if match:
                    url = match.group(0)
                    print(f'Extracted URL: {url}')
                    # Write to file for later use
                    with open('tunnel_url.txt', 'w') as f:
                        f.write(url)
        else:
            break

# Kill existing cloudflared processes (console) to avoid conflict
# Not needed

# Start cloudflared tunnel run with config
cmd = ['cloudflared', 'tunnel', 'run', '--loglevel', 'info']
print(f'Starting: {cmd}')
proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1)

# Start reader threads
thread = threading.Thread(target=read_output, args=(proc.stdout, 'cloudflared'))
thread.daemon = True
thread.start()

# Wait for a while to see if tunnel starts
time.sleep(15)

# Check if process is still alive
if proc.poll() is None:
    print('Tunnel started successfully')
    # Test public URL
    import requests
    url = 'https://music.joefoxing.it.com/'
    try:
        resp = requests.get(url, timeout=10)
        print(f'Public URL test: {resp.status_code}')
    except Exception as e:
        print(f'Public URL test error: {e}')
    # Keep tunnel running for a bit more
    time.sleep(5)
    proc.terminate()
    proc.wait()
else:
    print('Tunnel process exited early')
    sys.exit(1)