import subprocess
import threading
import time
import re
import sys
import requests
import os

def run_tunnel_connector():
    tunnel_id = '6c81da6a-af52-4eb4-804f-bee2e0f770e3'
    cred_file = 'C:/Users/Joefoxing/.cloudflared/6c81da6a-af52-4eb4-804f-bee2e0f770e3.json'
    port = 5000
    
    cmd = ['cloudflared', 'tunnel', 'run', '--url', f'http://127.0.0.1:{port}',
           '--credentials-file', cred_file, tunnel_id]
    print(f'Starting tunnel connector: {cmd}')
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1)
    
    output_lines = []
    connector_ready = False
    
    def read_output():
        nonlocal connector_ready
        for line in iter(proc.stdout.readline, ''):
            line = line.strip()
            if line:
                output_lines.append(line)
                print(f'[cloudflared] {line}')
                sys.stdout.flush()
                if 'Registered tunnel connection' in line:
                    connector_ready = True
                    print('Tunnel connector registered with edge')
                elif 'Unable to reach the origin service' in line:
                    print('ERROR: Cannot reach origin')
                elif 'error' in line.lower():
                    print(f'Error line: {line}')
            if proc.poll() is not None:
                break
    
    reader = threading.Thread(target=read_output, daemon=True)
    reader.start()
    
    # Wait for connector ready up to 30 seconds
    start = time.time()
    while not connector_ready and time.time() - start < 30:
        if proc.poll() is not None:
            print('Process exited prematurely')
            break
        time.sleep(0.1)
    
    if not connector_ready:
        print('Failed to establish tunnel connection')
        print('Last 10 lines:', output_lines[-10:])
        proc.terminate()
        proc.wait()
        return False
    
    # Give a moment for routing
    time.sleep(3)
    
    # Test public URL
    public_url = 'https://music.joefoxing.it.com'
    print(f'Testing public URL: {public_url}')
    try:
        resp = requests.get(public_url, timeout=10)
        print(f'Response status: {resp.status_code}')
        if resp.status_code == 200:
            print('SUCCESS: Tunnel is serving requests!')
            success = True
        else:
            print(f'Unexpected status: {resp.status_code}')
            print(f'Headers: {resp.headers}')
            success = False
    except Exception as e:
        print(f'Error testing tunnel: {e}')
        success = False
    
    # Stop connector
    proc.terminate()
    proc.wait()
    return success

if __name__ == '__main__':
    success = run_tunnel_connector()
    sys.exit(0 if success else 1)