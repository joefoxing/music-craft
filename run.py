#!/usr/bin/env python3
"""
Music Cover Generator - Main Application Entry Point
Uses Kie API to generate music covers from uploaded audio files.

Version: 1.0.0
Release Date: January 11, 2026
"""

import os
import atexit
from app import create_app
from app.ngrok_utils import setup_ngrok_tunnel, stop_ngrok_tunnels
from app.localtunnel_utils import setup_localtunnel_tunnel, stop_localtunnel_tunnels
from app.cloudflared_utils import setup_cloudflared_tunnel, stop_cloudflared_tunnels
from dotenv import load_dotenv

# Load environment variables
load_dotenv(override=True)

app = create_app()

if __name__ == '__main__':
    # Get configuration from environment
    host = os.environ.get('HOST', '0.0.0.0')
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('FLASK_DEBUG', 'False').lower() == 'true'
    
    ngrok_enabled = os.environ.get('NGROK_ENABLED', 'false').lower() == 'true'
    localtunnel_enabled = os.environ.get('LOCALTUNNEL_ENABLED', 'false').lower() == 'true'
    cloudflared_enabled = os.environ.get('CLOUDFLARED_ENABLED', 'false').lower() == 'true'
    ngrok_url = None
    localtunnel_url = None
    cloudflared_url = None
    tunnel_url = None
    tunnel_type = None
    
    if localtunnel_enabled:
        try:
            print("\n" + "="*50)
            print("INITIALIZING LOCALTUNNEL TUNNEL")
            print("="*50)
            
            subdomain = os.environ.get('LOCALTUNNEL_SUBDOMAIN')
            local_host = os.environ.get('LOCALTUNNEL_LOCAL_HOST')
            print_requests = os.environ.get('LOCALTUNNEL_PRINT_REQUESTS', 'false').lower() == 'true'
            open_browser = os.environ.get('LOCALTUNNEL_OPEN_BROWSER', 'false').lower() == 'true'
            
            # Set up localtunnel tunnel
            localtunnel_url = setup_localtunnel_tunnel(
                port=port,
                subdomain=subdomain,
                local_host=local_host,
                print_requests=print_requests,
                open_browser=open_browser
            )
            
            # Register cleanup function
            atexit.register(stop_localtunnel_tunnels)
            
            # Update app config with tunnel URL
            app.config['LOCALTUNNEL_URL'] = localtunnel_url
            # Also update BASE_URL to ensure callback URLs are correct
            app.config['BASE_URL'] = localtunnel_url
            tunnel_url = localtunnel_url
            tunnel_type = 'Localtunnel'
            
            print(f"Localtunnel tunnel active: {localtunnel_url}")
            print("="*50 + "\n")
            
        except Exception as e:
            print(f"Failed to create Localtunnel tunnel: {e}")
            print("Continuing without Localtunnel...\n")
            localtunnel_enabled = False
    
    elif ngrok_enabled:
        try:
            print("\n" + "="*50)
            print("INITIALIZING NGROK TUNNEL")
            print("="*50)
            
            ngrok_auth_token = os.environ.get('NGROK_AUTH_TOKEN')
            ngrok_region = os.environ.get('NGROK_REGION', 'us')
            existing_ngrok_url = os.environ.get('NGROK_URL')
            
            # Set up Ngrok tunnel
            ngrok_url = setup_ngrok_tunnel(
                port=port,
                auth_token=ngrok_auth_token,
                region=ngrok_region,
                existing_url=existing_ngrok_url
            )
            
            # Register cleanup function
            atexit.register(stop_ngrok_tunnels)
            
            # Update app config with Ngrok URL (use the actual URL from tunnel)
            app.config['NGROK_URL'] = ngrok_url
            # Also update BASE_URL to ensure callback URLs are correct
            app.config['BASE_URL'] = ngrok_url
            tunnel_url = ngrok_url
            tunnel_type = 'Ngrok'
            
            print(f"Ngrok tunnel active: {ngrok_url}")
            print("="*50 + "\n")
            
        except Exception as e:
            print(f"Failed to create Ngrok tunnel: {e}")
            print("Continuing without Ngrok...\n")
            ngrok_enabled = False

    elif cloudflared_enabled:
        try:
            print("\n" + "="*50)
            print("INITIALIZING CLOUDFLARE TUNNEL")
            print("="*50)
            
            token = os.environ.get('CLOUDFLARED_TOKEN')
            hostname = os.environ.get('CLOUDFLARED_HOSTNAME')
            tunnel_id = os.environ.get('CLOUDFLARED_TUNNEL_ID')
            credentials_file = os.environ.get('CLOUDFLARED_CREDENTIALS_FILE')
            legacy_mode = os.environ.get('CLOUDFLARED_LEGACY_MODE', 'false').lower() == 'true'
            
            # Set up Cloudflare Tunnel
            cloudflared_url = setup_cloudflared_tunnel(
                port=port,
                token=token,
                hostname=hostname,
                tunnel_id=tunnel_id,
                credentials_file=credentials_file,
                legacy_mode=legacy_mode
            )
            
            # Register cleanup function
            atexit.register(stop_cloudflared_tunnels)
            
            # Update app config with tunnel URL
            app.config['CLOUDFLARED_URL'] = cloudflared_url
            # Also update BASE_URL to ensure callback URLs are correct
            app.config['BASE_URL'] = cloudflared_url
            tunnel_url = cloudflared_url
            tunnel_type = 'Cloudflare Tunnel'
            
            print(f"Cloudflare Tunnel active: {cloudflared_url}")
            print("="*50 + "\n")
            
        except Exception as e:
            print(f"Failed to create Cloudflare Tunnel: {e}")
            print("Continuing without Cloudflare Tunnel...\n")
            cloudflared_enabled = False

    print(f"""
    ============================================
    Music Cover Generator v1.0.0
    ============================================
    Starting server...
    Host: {host}
    Port: {port}
    Debug: {debug}
    Ngrok: {'Enabled' if ngrok_enabled else 'Disabled'}
    Localtunnel: {'Enabled' if localtunnel_enabled else 'Disabled'}
    Cloudflare Tunnel: {'Enabled' if cloudflared_enabled else 'Disabled'}
    {f'Public URL: {tunnel_url}' if tunnel_url else ''}
    
    Endpoints:
    - Web Interface: http://{host}:{port}/
    - File Upload: http://{host}:{port}/upload
    - Generate Cover: http://{host}:{port}/api/generate-cover
    - Task Status: http://{host}:{port}/api/task-status/<task_id>
    - Callback: http://{host}:{port}/callback
    
    Note: Make sure to set KIE_API_KEY environment variable
    ============================================
    """)
    
    app.run(host=host, port=port, debug=debug)