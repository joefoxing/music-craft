# Remove any existing lock file
if (Test-Path .git/index.lock) {
    Remove-Item -Force .git/index.lock
    Write-Host "Removed lock file"
}

# Disable autocrlf temporarily
git config --local core.autocrlf false

# Stage all changes
Write-Host "Staging changes..."
git add .env.example .env.prod.example .github/workflows/deploy.yml .gitignore
git add app/config.py app/models.py app/routes/billing.py app/routes/main.py
git add app/paypal.py
git add app/templates/about.html app/templates/careers.html app/templates/community.html
git add app/templates/help-center.html app/templates/press.html
git add app/templates/privacy.html app/templates/safety.html app/templates/terms.html
git add migrations/versions/c9d3e8f2a5b1_add_paypal_fields.py
git add migrations/versions/e9f1a2b3c4d5_add_paypal_fields_if_missing.py

# Commit
Write-Host "Committing..."
git commit -m "merge local changes with remote updates, resolved conflicts"

# Check result
Write-Host "Checking commit..."
git log --oneline -1

Write-Host "Done!"
