"""
Localtunnel utilities for creating and managing tunnels.
Uses npx localtunnel package to expose local Flask server to the internet.
"""
import os
import re
import sys
import logging
import subprocess
import threading
import time
import atexit
import signal

logger = logging.getLogger(__name__)

# Global reference to the localtunnel subprocess
_localtunnel_process = None
_localtunnel_url = None

def setup_localtunnel_tunnel(port=5000, subdomain=None, local_host=None, 
                             print_requests=False, open_browser=False):
    """
    Set up a localtunnel tunnel for the Flask application.
    
    Args:
        port (int): The local port to tunnel
        subdomain (str): Optional subdomain to request
        local_host (str): Tunnel traffic to this host instead of localhost
        print_requests (bool): Whether to print request info
        open_browser (bool): Whether to open the tunnel URL in browser
        
    Returns:
        str: Public localtunnel URL
        
    Raises:
        RuntimeError: If tunnel fails to start or URL cannot be retrieved
    """
    global _localtunnel_process, _localtunnel_url
    
    if _localtunnel_process is not None:
        logger.warning("Localtunnel process already exists, stopping it first")
        stop_localtunnel_tunnels()
    
    npx_cmd = 'npx.cmd' if sys.platform == 'win32' else 'npx'
    cmd = [npx_cmd, 'localtunnel', '--port', str(port)]
    if subdomain:
        cmd.extend(['--subdomain', subdomain])
    if local_host:
        cmd.extend(['--local-host', local_host])
    if print_requests:
        cmd.append('--print-requests')
    if open_browser:
        cmd.append('--open')
    
    logger.info(f"Starting localtunnel with command: {' '.join(cmd)}")
    print(f"[DEBUG] Command: {' '.join(cmd)}")
    sys.stdout.flush()
    
    # Start subprocess, capture stdout and stderr
    # Use Popen with pipes to read output line by line
    # Debug environment
    import os
    debug_env = {k: v for k, v in os.environ.items() if 'PROXY' in k or 'HTTP' in k or 'NODE' in k}
    print(f"[DEBUG] Environment: {debug_env}")
    sys.stdout.flush()
    process = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        stdin=subprocess.DEVNULL,
        text=True,
        bufsize=1,
        universal_newlines=True
    )
    print(f"[DEBUG] Subprocess PID: {process.pid}")
    sys.stdout.flush()
    
    _localtunnel_process = process
    _localtunnel_url = None
    output_lines = []  # collect output for debugging
    
    # Thread to read output and find URL
    def read_output():
        nonlocal process, output_lines
        global _localtunnel_url
        # Pattern to extract any https? URL (more flexible)
        url_pattern = re.compile(r'https?://[^\s]+')
        print("[DEBUG] Reading localtunnel output...")
        sys.stdout.flush()
        for line in iter(process.stdout.readline, ''):
            line = line.strip()
            if line:
                logger.debug(f"localtunnel: {line}")
                output_lines.append(line)
                # Look for URL in line
                # Check if line contains typical localtunnel domains
                if '.loca.lt' in line or '.localtunnel.me' in line:
                    match = url_pattern.search(line)
                    if match:
                        url = match.group(0)
                        logger.info(f"Found localtunnel URL: {url}")
                        _localtunnel_url = url
                # Also check for "your url is:" pattern
                elif 'your url is:' in line:
                    match = url_pattern.search(line)
                    if match:
                        url = match.group(0)
                        logger.info(f"Found localtunnel URL: {url}")
                        _localtunnel_url = url
                # Print to console as well (optional)
                print(f"[localtunnel] {line}")
                sys.stdout.flush()
            if process.poll() is not None:
                break
    
    reader_thread = threading.Thread(target=read_output, daemon=True)
    reader_thread.start()
    
    # Wait for URL to be found (max 30 seconds)
    start_time = time.time()
    while _localtunnel_url is None and time.time() - start_time < 30:
        if process.poll() is not None:
            # process terminated early
            output = process.stdout.read() if process.stdout else ""
            raise RuntimeError(
                f"Localtunnel process exited prematurely with code {process.returncode}. "
                f"Output: {output}\nCollected lines: {output_lines}"
            )
        time.sleep(0.1)
    
    if _localtunnel_url is None:
        stop_localtunnel_tunnels()
        raise RuntimeError(
            f"Failed to retrieve localtunnel URL within timeout (30 seconds). "
            f"Collected output lines: {output_lines}"
        )
    
    # Register cleanup
    atexit.register(stop_localtunnel_tunnels)
    
    logger.info(f"Localtunnel tunnel active: {_localtunnel_url}")
    
    # Print tunnel info
    print(f"\n{'='*50}")
    print("LOCALTUNNEL TUNNEL ACTIVE")
    print(f"{'='*50}")
    print(f"Public URL: {_localtunnel_url}")
    print(f"Local URL: http://localhost:{port}")
    print(f"{'='*50}\n")
    
    return _localtunnel_url

def stop_localtunnel_tunnels():
    """Stop the active localtunnel tunnel."""
    global _localtunnel_process, _localtunnel_url
    if _localtunnel_process is not None:
        logger.info("Stopping localtunnel tunnel")
        # Send SIGTERM (or CTRL_C_EVENT on Windows)
        try:
            if os.name == 'nt':
                # Windows
                _localtunnel_process.terminate()
            else:
                _localtunnel_process.send_signal(signal.SIGTERM)
            # Wait a bit for graceful termination
            _localtunnel_process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            logger.warning("Localtunnel did not terminate gracefully, killing")
            _localtunnel_process.kill()
        except Exception as e:
            logger.error(f"Error stopping localtunnel: {e}")
        finally:
            _localtunnel_process = None
            _localtunnel_url = None
            # Remove atexit registration to avoid duplicate calls
            try:
                atexit.unregister(stop_localtunnel_tunnels)
            except:
                pass

def is_localtunnel_running():
    """
    Check if localtunnel is already running.
    
    Returns:
        bool: True if localtunnel process exists and is alive, False otherwise
    """
    global _localtunnel_process
    if _localtunnel_process is None:
        return False
    return _localtunnel_process.poll() is None

def get_localtunnel_url():
    """
    Get the current active localtunnel URL.
    
    Returns:
        str: Active localtunnel URL or None if no tunnel exists
    """
    global _localtunnel_url
    return _localtunnel_url