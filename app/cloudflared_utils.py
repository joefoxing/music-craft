"""
Cloudflare Tunnel utilities for creating and managing tunnels.
Uses cloudflared CLI to expose local Flask server to the internet via Cloudflare.
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

# Global reference to the cloudflared subprocess
_cloudflared_process = None
_cloudflared_url = None

def setup_cloudflared_tunnel(port=5000, token=None, hostname=None, tunnel_id=None,
                             credentials_file=None, legacy_mode=False):
    """
    Set up a Cloudflare Tunnel for the Flask application.
    
    Args:
        port (int): The local port to tunnel
        token (str): Optional Cloudflare Tunnel token (for quick tunnels)
        hostname (str): Optional custom hostname (requires tunnel configuration)
        tunnel_id (str): Optional tunnel ID (for named tunnels)
        credentials_file (str): Path to credentials file for named tunnels
        legacy_mode (bool): If True, use legacy --url mode (no tunnel persistence)
        
    Returns:
        str: Public Cloudflare Tunnel URL
        
    Raises:
        RuntimeError: If tunnel fails to start or URL cannot be retrieved
    """
    global _cloudflared_process, _cloudflared_url
    
    if _cloudflared_process is not None:
        logger.warning("Cloudflared process already exists, stopping it first")
        stop_cloudflared_tunnels()
    
    # Determine cloudflared executable name based on platform
    cloudflared_cmd = 'cloudflared' if sys.platform == 'win32' else 'cloudflared'
    
    # Build command based on mode
    if legacy_mode:
        # Legacy quick tunnel (no persistent tunnel)
        cmd = [cloudflared_cmd, 'tunnel', '--url', f'http://127.0.0.1:{port}']
        if token:
            cmd.extend(['--token', token])
        if hostname:
            cmd.extend(['--hostname', hostname])
    else:
        # Named tunnel mode (recommended)
        if tunnel_id:
            cmd = [cloudflared_cmd, 'tunnel', 'run', '--url', f'http://127.0.0.1:{port}']
            if credentials_file:
                cmd.extend(['--credentials-file', credentials_file])
            cmd.append(tunnel_id)
        else:
            # No tunnel ID: create a quick tunnel (ephemeral)
            cmd = [cloudflared_cmd, 'tunnel', '--url', f'http://127.0.0.1:{port}']
            if token:
                cmd.extend(['--token', token])
    
    logger.info(f"Starting cloudflared with command: {' '.join(cmd)}")
    print(f"[DEBUG] Command: {' '.join(cmd)}")
    sys.stdout.flush()
    
    # Start subprocess, capture stdout and stderr
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
    
    _cloudflared_process = process
    _cloudflared_url = None
    output_lines = []  # collect output for debugging
    
    # Thread to read output and find URL
    def read_output():
        nonlocal process, output_lines
        global _cloudflared_url
        # Pattern to extract any https? URL (more flexible)
        url_pattern = re.compile(r'https?://[^\s]+')
        print("[DEBUG] Reading cloudflared output...")
        sys.stdout.flush()
        for line in iter(process.stdout.readline, ''):
            line = line.strip()
            if line:
                logger.debug(f"cloudflared: {line}")
                output_lines.append(line)
                # Look for URL in line
                # Cloudflared outputs "INF Starting tunnel" with URL or "INF Tunnel established at https://..."
                if ('.trycloudflare.com' in line or
                    '.cfargotunnel.com' in line or
                    'tunnel established at' in line.lower() or
                    'your tunnel is ready at' in line.lower() or
                    'tunnel is now accessible at' in line.lower()):
                    match = url_pattern.search(line)
                    if match:
                        url = match.group(0)
                        logger.info(f"Found Cloudflare Tunnel URL: {url}")
                        _cloudflared_url = url
                # Also check for "https://" in line (common)
                elif 'https://' in line:
                    match = url_pattern.search(line)
                    if match:
                        url = match.group(0)
                        if ('.trycloudflare.com' in url or
                            '.cfargotunnel.com' in url or
                            'tunnel' in line.lower()):
                            logger.info(f"Found Cloudflare Tunnel URL: {url}")
                            _cloudflared_url = url
                # Print to console as well (optional)
                print(f"[cloudflared] {line}")
                sys.stdout.flush()
            if process.poll() is not None:
                break
    
    reader_thread = threading.Thread(target=read_output, daemon=True)
    reader_thread.start()
    
    # Wait for URL to be found (max 60 seconds)
    start_time = time.time()
    while _cloudflared_url is None and time.time() - start_time < 60:
        if process.poll() is not None:
            # process terminated early
            output = process.stdout.read() if process.stdout else ""
            raise RuntimeError(
                f"Cloudflared process exited prematurely with code {process.returncode}. "
                f"Output: {output}\nCollected lines: {output_lines}"
            )
        time.sleep(0.1)
    
    if _cloudflared_url is None:
        # Check if process is still alive
        if process.poll() is not None:
            stop_cloudflared_tunnels()
            raise RuntimeError(
                f"Cloudflared process terminated before URL could be retrieved. "
                f"Collected output lines: {output_lines}"
            )
        # Fallback: construct URL from hostname or tunnel ID
        constructed_url = None
        if hostname:
            constructed_url = f"https://{hostname}"
            logger.info(f"Using constructed tunnel URL from hostname: {constructed_url}")
        elif tunnel_id:
            constructed_url = f"https://{tunnel_id}.cfargotunnel.com"
            logger.info(f"Using constructed tunnel URL from tunnel ID: {constructed_url}")
        else:
            stop_cloudflared_tunnels()
            raise RuntimeError(
                f"Failed to retrieve Cloudflare Tunnel URL within timeout (60 seconds). "
                f"Collected output lines: {output_lines}"
            )
        _cloudflared_url = constructed_url
    
    # Register cleanup
    atexit.register(stop_cloudflared_tunnels)
    
    logger.info(f"Cloudflare Tunnel active: {_cloudflared_url}")
    
    # Print tunnel info
    print(f"\n{'='*50}")
    print("CLOUDFLARE TUNNEL ACTIVE")
    print(f"{'='*50}")
    print(f"Public URL: {_cloudflared_url}")
    print(f"Local URL: http://127.0.0.1:{port}")
    print(f"{'='*50}\n")
    
    return _cloudflared_url

def stop_cloudflared_tunnels():
    """Stop the active cloudflared tunnel."""
    global _cloudflared_process, _cloudflared_url
    if _cloudflared_process is not None:
        logger.info("Stopping cloudflared tunnel")
        # Send SIGTERM (or CTRL_C_EVENT on Windows)
        try:
            if os.name == 'nt':
                # Windows
                _cloudflared_process.terminate()
            else:
                _cloudflared_process.send_signal(signal.SIGTERM)
            # Wait a bit for graceful termination
            _cloudflared_process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            logger.warning("Cloudflared did not terminate gracefully, killing")
            _cloudflared_process.kill()
        except Exception as e:
            logger.error(f"Error stopping cloudflared: {e}")
        finally:
            _cloudflared_process = None
            _cloudflared_url = None
            # Remove atexit registration to avoid duplicate calls
            try:
                atexit.unregister(stop_cloudflared_tunnels)
            except:
                pass

def is_cloudflared_running():
    """
    Check if cloudflared is already running.
    
    Returns:
        bool: True if cloudflared process exists and is alive, False otherwise
    """
    global _cloudflared_process
    if _cloudflared_process is None:
        return False
    return _cloudflared_process.poll() is None

def get_cloudflared_url():
    """
    Get the current active Cloudflare Tunnel URL.
    
    Returns:
        str: Active Cloudflare Tunnel URL or None if no tunnel exists
    """
    global _cloudflared_url
    return _cloudflared_url