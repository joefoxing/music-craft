import requests

# Fetch the completed job
response = requests.get('http://localhost:8000/v1/lyrics/8d487538-a3cf-4885-98f5-48d2cb82cb85')
data = response.json()

lyrics = data['result']['lyrics']

print("=" * 60)
print("LYRICS ANALYSIS")
print("=" * 60)
print(f"Status: {data['status']}")
print(f"Language detected: {data['meta']['language_detected']}")
print(f"Total characters: {len(lyrics)}")
print(f"Newline count: {lyrics.count(chr(10))}")
print()

print("=" * 60)
print("RAW REPRESENTATION (shows \\n characters)")
print("=" * 60)
print(repr(lyrics[:500]))  # First 500 chars
print()

print("=" * 60)
print("FORMATTED LYRICS (as it will display)")
print("=" * 60)
print(lyrics)
print()

print("=" * 60)
print("LINE-BY-LINE BREAKDOWN")
print("=" * 60)
lines = lyrics.split('\n')
print(f"Total lines: {len(lines)}")
print()
for i, line in enumerate(lines, 1):
    if not line.strip():
        print(f"  Line {i}: [BLANK LINE - Stanza Break]")
    else:
        print(f"  Line {i}: {line}")
print()

print("=" * 60)
print("VERDICT")
print("=" * 60)
if lyrics.count('\n') > 0:
    print("✓ SUCCESS: Lyrics contain line breaks!")
    print(f"✓ Found {lyrics.count(chr(10))} line breaks in the text")
    print("✓ Line-by-line formatting is working correctly")
else:
    print("✗ FAILED: No line breaks found - lyrics are a single block")
