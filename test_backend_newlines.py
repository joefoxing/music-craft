#!/usr/bin/env python3
"""Test if backend returns newlines in lyrics"""
import requests
import time
import json

# Configuration
API_URL = "http://localhost:8000/v1/lyrics"
AUDIO_FILE = r"E:\Developer\lyric_cover_staging\app\static\uploads\00daf4d19d2c4eb790e2244e67d1c954.mp3"

print("\n" + "="*60)
print("Testing Lyrics Extraction Backend")
print("="*60)

# Step 1: Submit extraction job
print("\n1. Submitting extraction job...")
print(f"   Audio file: {AUDIO_FILE}")

with open(AUDIO_FILE, 'rb') as f:
    files = {'file': f}
    data = {'language_hint': 'auto', 'timestamps': 'word'}
    response = requests.post(API_URL, files=files, data=data)

if response.status_code not in [200, 202]:
    print(f"   ERROR: Failed to submit job (status {response.status_code})")
    print(f"   Response: {response.text}")
    exit(1)

result = response.json()
job_id = result.get('job_id')
print(f"   ✓ Job ID: {job_id}")

# Step 2: Wait for completion
print("\n2. Waiting for job completion...")
max_attempts = 30
status_url = f"{API_URL}/{job_id}"

for attempt in range(1, max_attempts + 1):
    time.sleep(2)
    response = requests.get(status_url)
    result = response.json()
    status = result.get('status', 'unknown')
    
    print(f"   Attempt {attempt}: Status = {status}")
    
    if status in ['completed', 'failed']:
        break

# Step 3: Get final result
print("\n3. Final Result:")
response = requests.get(status_url)
result = response.json()

status = result.get('status')
lyrics = result.get('lyrics', '')
language = result.get('language', 'unknown')

print(f"   Status: {status}")
print(f"   Language: {language}")
print(f"   Lyrics length: {len(lyrics)} characters")

# Count newlines
newline_count = lyrics.count('\n')
print(f"   Newline count: {newline_count}", end='')
if newline_count > 0:
    print(" ✓")
else:
    print(" ✗")

# Step 4: Show lyrics with line numbers
print("\n4. Lyrics with line breaks:")
lines = lyrics.split('\n')
for i, line in enumerate(lines, 1):
    if line.strip() == '':
        print(f"   Line {i}: [BLANK LINE]")
    else:
        print(f"   Line {i}: {line[:80]}")  # Truncate long lines for readability

# Summary
print("\n" + "="*60)
if newline_count > 0:
    print("✓ SUCCESS: Backend is returning newlines correctly!")
    print(f"  Found {newline_count} newlines across {len(lines)} lines")
else:
    print("✗ FAILURE: Backend is NOT returning newlines!")
    print("  Lyrics are returned as a single block of text")
print("="*60 + "\n")

# Save full lyrics to file for inspection
with open('last_extracted_lyrics.txt', 'w', encoding='utf-8') as f:
    f.write(lyrics)
print("Full lyrics saved to: last_extracted_lyrics.txt")
