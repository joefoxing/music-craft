#!/usr/bin/env python3
"""Check lyrics extraction job result"""
import requests
import json

job_id = "a509a9b0-e641-4483-9648-995fd41ec47b"
url = f"http://localhost:8000/v1/lyrics/{job_id}"

print(f"Checking job: {job_id}\n")

response = requests.get(url)
result = response.json()

status = result.get('status', 'unknown')
lyrics = result.get('lyrics', '')
language = result.get('language', 'unknown')

print(f"Status: {status}")
print(f"Language: {language}")
print(f"Lyrics length: {len(lyrics)} characters")
print(f"Newline count: {lyrics.count(chr(10))}")
print(f"\n{'='*70}")
print("LYRICS:")
print(f"{'='*70}\n")
print(lyrics)
print(f"\n{'='*70}")
print("LYRICS WITH LINE NUMBERS:")
print(f"{'='*70}\n")

lines = lyrics.split('\n')
for i, line in enumerate(lines, 1):
    if line.strip():
        print(f"{i:2}. {line}")
    else:
        print(f"{i:2}. [blank line]")
