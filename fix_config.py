import os
config_path = r'C:/Users/Joefoxing/.cloudflared/config.yml'
config_content = """tunnel: 6c81da6a-af52-4eb4-804f-bee2e0f770e3
credentials-file: C:/Users/Joefoxing/.cloudflared/6c81da6a-af52-4eb4-804f-bee2e0f770e3.json

ingress:
  - hostname: music.joefoxing.it.com
    service: http://localhost:5000
  - service: http_status:404
"""
with open(config_path, 'w', encoding='utf-8') as f:
    f.write(config_content)
print('Config file written')