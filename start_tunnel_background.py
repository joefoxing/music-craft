#!/usr/bin/env python3
"""
Start Cloudflare Tunnel in background and keep it running.
"""
import subprocess
import os
import sys
import time
import threading

def start_tunnel():
    # Path to cloudflared executable
    cloudflared_path = os.path.expanduser('~/.cloudflared/cloudflared.exe')
    if not os.path.exists(cloudflared_path):
        print(f'ERROR: cloudflared not found at {cloudflared_path}')
        sys.exit(1)
    
    # Tunnel configuration
    tunnel_id = '6c81da6a-af52-4eb4-804f-bee2e0f770e3'
    credentials_file = 'C:/Users/Joefoxing/.cloudflared/6c81da6a-af52-4eb4-804f-bee2e0f770e3.json'
    port = 5000
    
    cmd = [cloudflared_path, 'tunnel', 'run',
           '--url', f'http://127.0.0.1:{port}',
           '--credentials-file', credentials_file,
           tunnel_id]
    
    print(f'Starting tunnel with command: {" ".join(cmd)}')
    # Start detached process
    try:
        # Use DETACHED_PROCESS to detach from console
        # CREATE_NEW_PROCESS_GROUP also helps
        creation_flags = subprocess.CREATE_NEW_PROCESS_GROUP | subprocess.DETACHED_PROCESS
        proc = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
            creationflags=creation_flags,
            # close_fds=True  # not needed on Windows
        )
    except Exception as e:
        # Fallback without creation flags
        print(f'Warning: {e}, trying without flags')
        proc = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1
        )
    
    # Start a thread to read output and log
    def read_output():
        for line in iter(proc.stdout.readline, ''):
            line = line.strip()
            if line:
                print(f'[cloudflared] {line}')
                sys.stdout.flush()
    
    reader = threading.Thread(target=read_output, daemon=True)
    reader.start()
    
    # Wait a few seconds to see if tunnel starts successfully
    time.sleep(5)
    
    # Check if process is still alive
    if proc.poll() is not None:
        print('Tunnel process exited prematurely')
        # Print remaining output
        output = proc.stdout.read()
        if output:
            print(f'Remaining output: {output}')
        sys.exit(1)
    
    print('Tunnel started successfully (PID: {})'.format(proc.pid))
    print('Tunnel is running in background.')
    # Write PID to file for later reference
    with open('cloudflared.pid', 'w') as f:
        f.write(str(proc.pid))
    
    # Keep script alive? Actually we can exit, the subprocess will continue
    # because we used DETACHED_PROCESS (on Windows) and we're not waiting.
    # However, if we exit, the parent process will close the pipe and may cause issues.
    # We'll keep the script alive but sleep indefinitely.
    # Alternatively, we can detach by letting the subprocess inherit and exit.
    # For simplicity, we'll just wait a bit more and then exit.
    # The subprocess will continue because we've redirected stdout/stderr to pipes.
    # On Windows, the subprocess may be terminated when parent exits if not detached.
    # We'll use a loop to keep the script alive for a minute, then exit.
    # In production, you'd want to run as a service.
    print('Monitoring tunnel for 30 seconds...')
    for _ in range(30):
        if proc.poll() is not None:
            print('Tunnel process died')
            break
        time.sleep(1)
    
    print('Exiting start script. Tunnel should continue running.')
    # Do not wait for process
    sys.exit(0)

if __name__ == '__main__':
    start_tunnel()