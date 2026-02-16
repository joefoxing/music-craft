# Multi-Domain Setup: vnuno.com + joefoxing.com

## Overview

This document outlines the infrastructure configuration for supporting simultaneous access via both `vnuno.com` and `joefoxing.com` domains with proper SEO consolidation through 301 redirects.

## Architecture

```
                    ┌─────────────────────────────────────────────────────┐
                    │                    Caddy Server                       │
                    │              (Reverse Proxy + SSL Termination)        │
                    └─────────────────────────────────────────────────────┘
                                          │
          ┌───────────────────────────────┼───────────────────────────────┐
          │                               │                               │
          ▼                               ▼                               ▼
   ┌─────────────┐                ┌─────────────┐                ┌─────────────┐
   │ www.joefox  │                │ joefoxing   │                │ vnuno.com   │
   │ .com        │───────────────▶│ .com        │◀───────────────│ (301)       │
   │ (redirect)  │                │ (canonical) │                │ (redirect)  │
   └─────────────┘                └─────────────┘                └─────────────┘
          │                               │                               │
          │                               ▼                               │
          │                       ┌─────────────┐                         │
          └──────────────────────▶│ Flask App   │◀────────────────────────┘
                                  │ Port 8000   │
                                  └─────────────┘
```

## DNS Configuration

### Required DNS Records

Configure the following A records at your DNS provider for **both domains**:

| Domain | Type | Value | TTL |
|--------|------|-------|-----|
| `joefoxing.com` | A | `<SERVER_IP>` | 300 |
| `www.joefoxing.com` | A | `<SERVER_IP>` | 300 |
| `vnuno.com` | A | `<SERVER_IP>` | 300 |
| `www.vnuno.com` | A | `<SERVER_IP>` | 300 |
| `staging.joefoxing.com` | A | `<SERVER_IP>` | 300 |

**Replace `<SERVER_IP>` with your actual server IP address.**

### Verification

After DNS propagation (may take 5 minutes to 48 hours), verify with:

```bash
# Check A records
nslookup joefoxing.com
nslookup www.joefoxing.com
nslookup vnuno.com
nslookup www.vnuno.com

# Or using dig
dig +short joefoxing.com A
dig +short www.vnuno.com A
```

## SSL/TLS Certificates

Caddy automatically provisions and renews Let's Encrypt certificates for all configured domains. No manual SSL configuration required.

### Certificate Coverage

- ✅ `joefoxing.com`
- ✅ `www.joefoxing.com`
- ✅ `vnuno.com`
- ✅ `www.vnuno.com`
- ✅ `staging.joefoxing.com`

### Verification

```bash
# Check certificate status
curl -vI https://joefoxing.com 2>&1 | grep -E "(subject|issuer|SSL)"
curl -vI https://vnuno.com 2>&1 | grep -E "(subject|issuer|SSL)"
```

## Virtual Host Configuration

### Redirect Behavior

| Source Domain | Destination | Status Code | Purpose |
|--------------|-------------|-------------|---------|
| `www.joefoxing.com` | `joefoxing.com` | 301 Permanent | Consolidate www traffic |
| `www.vnuno.com` | `vnuno.com` | 301 Permanent | Consolidate www traffic |
| `vnuno.com` | `joefoxing.com` | 301 Permanent | **SEO consolidation** |

### Caddyfile Structure

The canonical domain (`joefoxing.com`) serves the application directly. The alias domain (`vnuno.com`) performs a 301 redirect to consolidate SEO authority.

## Session & Cookie Configuration

### Flask Configuration Updates

Update your Flask application configuration to support both domains:

```python
# config.py or app configuration

class ProductionConfig:
    # Allow both domains for session/cookie integrity
    SESSION_COOKIE_DOMAIN = ".joefoxing.com"  # Leading dot for subdomain support
    SESSION_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"
    
    # If using Flask-Session or similar
    PERMANENT_SESSION_LIFETIME = timedelta(days=7)
    
    # CORS settings if applicable
    CORS_ORIGINS = [
        "https://joefoxing.com",
        "https://www.joefoxing.com",
        "https://vnuno.com",
        "https://www.vnuno.com",
    ]
```

### Important Note on Sessions

Since `vnuno.com` redirects to `joefoxing.com`, sessions will naturally persist once the user lands on `joefoxing.com`. The redirect happens before any session cookies are set.

If you later decide to serve content directly from both domains (without redirect), you'll need to implement:
1. Shared session storage (Redis/Memcached)
2. Cross-domain cookie settings
3. OAuth/SAML for cross-domain authentication

## Deployment Steps

### 1. Update DNS (Allow 5-60 minutes propagation)

```bash
# Verify DNS is pointing correctly before proceeding
dig +short joefoxing.com
dig +short vnuno.com
```

### 2. Deploy Caddy Configuration

```bash
# Navigate to deployment directory
cd /path/to/project/deploy/caddy

# Backup existing Caddyfile
cp /etc/caddy/Caddyfile /etc/caddy/Caddyfile.backup.$(date +%Y%m%d)

# Copy new configuration
sudo cp Caddyfile /etc/caddy/Caddyfile

# Validate configuration
sudo caddy validate --config /etc/caddy/Caddyfile

# Reload Caddy (zero-downtime)
sudo systemctl reload caddy

# Or restart if needed
sudo systemctl restart caddy
```

### 3. Verify Deployment

```bash
# Test redirects
curl -I https://www.joefoxing.com/test-path
# Expected: HTTP/2 301 Location: https://joefoxing.com/test-path

curl -I https://vnuno.com/another-path
# Expected: HTTP/2 301 Location: https://joefoxing.com/another-path

curl -I https://www.vnuno.com/
# Expected: HTTP/2 301 Location: https://vnuno.com/ (then to joefoxing.com)

# Verify main site serves content
curl -I https://joefoxing.com/
# Expected: HTTP/2 200
```

### 4. SSL Certificate Verification

```bash
# View certificate details for all domains
echo | openssl s_client -servername joefoxing.com -connect joefoxing.com:443 2>/dev/null | openssl x509 -noout -dates -subject
echo | openssl s_client -servername vnuno.com -connect vnuno.com:443 2>/dev/null | openssl x509 -noout -dates -subject
```

## SEO Considerations

### Why 301 Redirects?

1. **Link Equity Preservation**: 301 redirects pass ~90-99% of link equity (ranking power)
2. **Duplicate Content Prevention**: Search engines won't index both domains for the same content
3. **Canonical URL**: All traffic consolidates to `joefoxing.com` for consistent analytics

### Alternative: Serve Content from Both Domains

If you want both domains to serve content directly (no redirect), update the Caddyfile:

```caddy
# Remove the redirect from vnuno.com block and add reverse proxy
vnuno.com {
    encode gzip
    
    reverse_proxy 127.0.0.1:8000 {
        header_up X-Real-IP {remote_host}
        header_up X-Forwarded-Proto {scheme}
        header_up X-Forwarded-Host {host}
    }
    
    # Add canonical link header to prevent duplicate content
    header Link "<https://joefoxing.com{uri}>; rel=canonical"
    
    # Same headers as joefoxing.com
    header {
        Strict-Transport-Security "max-age=31536000; includeSubDomains; preload"
        X-Content-Type-Options "nosniff"
        X-Frame-Options "DENY"
    }
}
```

**Note**: If serving from both domains, implement canonical URLs in your HTML:

```html
<link rel="canonical" href="https://joefoxing.com/current-page-path">
```

## Monitoring & Maintenance

### Log Locations

```
/var/log/caddy/joefoxing_access.log    # Production traffic
/var/log/caddy/staging_access.log      # Staging traffic
```

### Health Checks

```bash
# Caddy health endpoint
curl https://joefoxing.com/caddy-health
# Expected: OK

# Application health
curl https://joefoxing.com/health
# Expected: Application-specific health response
```

### Certificate Renewal

Caddy handles automatic renewal. Monitor with:

```bash
# Check Caddy status
sudo systemctl status caddy

# View Caddy logs
sudo journalctl -u caddy -f
```

## Troubleshooting

### Issue: DNS Not Propagated

```bash
# Check from multiple locations
dig @8.8.8.8 joefoxing.com
dig @1.1.1.1 vnuno.com
```

### Issue: Certificate Not Issued

```bash
# Check Caddy logs for ACME errors
sudo journalctl -u caddy --since "1 hour ago"

# Verify domain resolves to server
hostname -I  # Get server IP
dig +short joefoxing.com  # Should match
```

### Issue: Redirect Loops

```bash
# Check redirect chain
curl -sLI https://vnuno.com | grep -i location
```

## Rollback Plan

If issues occur, quickly revert to single domain:

```bash
# Restore backup
sudo cp /etc/caddy/Caddyfile.backup.YYYYMMDD /etc/caddy/Caddyfile
sudo systemctl reload caddy

# Or edit Caddyfile to comment out vnuno.com blocks
```

## Summary Checklist

- [ ] DNS A records configured for all 4 hostnames
- [ ] DNS propagation verified
- [ ] Caddyfile deployed to `/etc/caddy/Caddyfile`
- [ ] Configuration validated with `caddy validate`
- [ ] Caddy reloaded/restarted successfully
- [ ] 301 redirects verified with curl
- [ ] SSL certificates issued for all domains
- [ ] Application responds correctly on joefoxing.com
- [ ] Staging site still functional
- [ ] Logs show no errors
