"""
Ngrok utilities for creating and managing tunnels.
"""
import os
import logging
from pyngrok import ngrok, conf, exception

logger = logging.getLogger(__name__)

def setup_ngrok_tunnel(port=5000, auth_token=None, region=None, existing_url=None):
    """
    Set up an Ngrok tunnel for the Flask application.
    
    Args:
        port (int): The local port to tunnel
        auth_token (str): Optional Ngrok auth token
        region (str): Optional region (us, eu, ap, au, sa, jp, in)
        existing_url (str): Optional existing Ngrok URL to use instead of creating new
    
    Returns:
        str: Public Ngrok URL
    """
    try:
        # Configure ngrok
        if auth_token:
            ngrok.set_auth_token(auth_token)
            logger.info("Ngrok auth token configured")
        
        # Set region if provided
        if region:
            conf.get_default().region = region
            logger.info(f"Ngrok region set to: {region}")
        
        # Check if we should use existing URL or create new tunnel
        if existing_url:
            logger.info(f"Using existing Ngrok URL: {existing_url}")
            public_url = existing_url
        else:
            # Check for existing tunnels first
            try:
                tunnels = ngrok.get_tunnels()
                if tunnels:
                    # Use first available HTTP/HTTPS tunnel
                    for tunnel in tunnels:
                        if tunnel.proto in ['http', 'https'] and f":{port}" in tunnel.config['addr']:
                            logger.info(f"Found existing tunnel to port {port}: {tunnel.public_url}")
                            public_url = tunnel.public_url
                            break
                    else:
                        # No existing tunnel for this port, create new
                        logger.info(f"Creating Ngrok tunnel to localhost:{port}")
                        tunnel = ngrok.connect(port, "http")
                        public_url = tunnel.public_url
                else:
                    # No tunnels exist, create new
                    logger.info(f"Creating Ngrok tunnel to localhost:{port}")
                    tunnel = ngrok.connect(port, "http")
                    public_url = tunnel.public_url
            except exception.PyngrokNgrokError as e:
                if "already online" in str(e):
                    logger.warning(f"Tunnel already exists: {e}")
                    # Try to get existing tunnels
                    tunnels = ngrok.get_tunnels()
                    if tunnels:
                        public_url = tunnels[0].public_url
                        logger.info(f"Using existing tunnel: {public_url}")
                    else:
                        raise
                else:
                    raise
        
        logger.info(f"Ngrok tunnel active: {public_url}")
        
        # Print tunnel info
        print(f"\n{'='*50}")
        print("NGROK TUNNEL ACTIVE")
        print(f"{'='*50}")
        print(f"Public URL: {public_url}")
        print(f"Local URL: http://localhost:{port}")
        print(f"Dashboard: http://localhost:4040")
        print(f"{'='*50}\n")
        
        return public_url
        
    except exception.PyngrokNgrokError as e:
        logger.error(f"Ngrok error: {e}")
        # Provide helpful error message
        if "already online" in str(e):
            logger.error("Another Ngrok process is already running with this configuration.")
            logger.error("Solution: Stop the existing Ngrok process or use a different port.")
        raise
    except Exception as e:
        logger.error(f"Failed to create Ngrok tunnel: {e}")
        raise

def stop_ngrok_tunnels():
    """Stop all active Ngrok tunnels."""
    try:
        ngrok.kill()
        logger.info("All Ngrok tunnels stopped")
    except Exception as e:
        logger.error(f"Error stopping Ngrok tunnels: {e}")

def is_ngrok_running():
    """
    Check if Ngrok is already running.
    
    Returns:
        bool: True if Ngrok is running, False otherwise
    """
    try:
        tunnels = ngrok.get_tunnels()
        return len(tunnels) > 0
    except Exception:
        return False

def get_ngrok_url():
    """
    Get the current active Ngrok URL.
    
    Returns:
        str: Active Ngrok URL or None if no tunnel exists
    """
    try:
        tunnels = ngrok.get_tunnels()
        if tunnels:
            # Return the first HTTP/HTTPS tunnel
            for tunnel in tunnels:
                if tunnel.proto in ['http', 'https']:
                    return tunnel.public_url
        return None
    except Exception as e:
        logger.error(f"Error getting Ngrok URL: {e}")
        return None