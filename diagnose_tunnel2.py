import subprocess
import threading
import time
import re
import sys
import requests
import os

def run_quick_tunnel():
    """Start a quick tunnel and extract URL"""
    # Kill any existing cloudflared console processes (optional)
    # os.system('taskkill /F /IM cloudflared.exe 2>nul')
    
    cmd = ['cloudflared', 'tunnel', '--url', 'http://127.0.0.1:5000', '--loglevel', 'info']
    print(f'Starting quick tunnel: {cmd}')
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1)
    
    url = None
    output_lines = []
    
    def read_output():
        nonlocal url
        for line in iter(proc.stdout.readline, ''):
            line = line.strip()
            if line:
                output_lines.append(line)
                print(f'[cloudflared] {line}')
                sys.stdout.flush()
                # Look for URL
                if '.trycloudflare.com' in line:
                    match = re.search(r'https?://[^\s]+', line)
                    if match:
                        url = match.group(0)
                        print(f'Found tunnel URL: {url}')
                elif 'tunnel established' in line.lower():
                    if url is None:
                        # try to extract URL from line
                        match = re.search(r'https?://[^\s]+', line)
                        if match:
                            url = match.group(0)
                            print(f'Found tunnel URL from established: {url}')
            if proc.poll() is not None:
                break
    
    reader = threading.Thread(target=read_output, daemon=True)
    reader.start()
    
    # Wait for URL up to 30 seconds
    start = time.time()
    while url is None and time.time() - start < 30:
        if proc.poll() is not None:
            print('Process exited prematurely')
            break
        time.sleep(0.1)
    
    if url is None:
        print('Failed to get tunnel URL')
        print('Last 10 lines:', output_lines[-10:])
        proc.terminate()
        proc.wait()
        return None
    
    # Keep tunnel running for a few seconds while we test
    time.sleep(2)
    
    # Test the URL
    print(f'Testing public URL: {url}')
    try:
        resp = requests.get(url, timeout=10)
        print(f'Response status: {resp.status_code}')
        if resp.status_code == 200:
            print('SUCCESS: Quick tunnel works!')
        else:
            print(f'Unexpected status: {resp.status_code}')
            print(f'Headers: {resp.headers}')
    except Exception as e:
        print(f'Error testing tunnel: {e}')
    
    # Stop tunnel
    proc.terminate()
    proc.wait()
    return url

if __name__ == '__main__':
    run_quick_tunnel()