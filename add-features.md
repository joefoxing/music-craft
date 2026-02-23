Boost Music Style Boost:
import requests

url = "https://api.kie.ai/api/v1/style/generate"

payload = { "content": "Pop, Mysterious" }
headers = {
    "Authorization": "Bearer <token>",
    "Content-Type": "application/json"
}

response = requests.post(url, json=payload, headers=headers)

print(response.text)
Mashup:
import requests

url = "https://api.kie.ai/api/v1/generate/mashup"

payload = {
    "uploadUrlList": ["https://example.com/audio1.mp3", "https://example.com/audio2.mp3"],
    "customMode": True,
    "model": "V4",
    "callBackUrl": "https://example.com/callback",
    "prompt": "A calm and relaxing piano track with soft melodies",
    "style": "Jazz",
    "title": "Relaxing Piano",
    "instrumental": True,
    "vocalGender": "m",
    "styleWeight": 0.61,
    "weirdnessConstraint": 0.72,
    "audioWeight": 0.65
}
headers = {
    "Authorization": "Bearer <token>",
    "Content-Type": "application/json"
}

response = requests.post(url, json=payload, headers=headers)

print(response.text)

Replace Music Section:

import requests

url = "https://api.kie.ai/api/v1/generate/replace-section"

payload = {
    "taskId": "2fac****9f72",
    "audioId": "e231****-****-****-****-****8cadc7dc",
    "prompt": "A calm and relaxing piano track.",
    "tags": "Jazz",
    "title": "Relaxing Piano",
    "negativeTags": "Rock",
    "infillStartS": 10.5,
    "infillEndS": 20.75,
    "fullLyrics": "[Verse 1]
Original lyrics here
[Chorus]
Modified lyrics for this section
[Verse 2]
More original lyrics",
    "callBackUrl": "https://example.com/callback"
}
headers = {
    "Authorization": "Bearer <token>",
    "Content-Type": "application/json"
}

response = requests.post(url, json=payload, headers=headers)

print(response.text)

Multi-Stem Separation:

import requests

url = "https://api.kie.ai/api/v1/vocal-removal/generate"

payload = {
    "taskId": "5c79****be8e",
    "audioId": "e231****-****-****-****-****8cadc7dc",
    "callBackUrl": "https://api.example.com/callback",
    "type": "import requests

url = "https://api.kie.ai/api/v1/vocal-removal/generate"

payload = {
    "taskId": "5c79****be8e",
    "audioId": "e231****-****-****-****-****8cadc7dc",
    "callBackUrl": "https://api.example.com/callback",
    "type": "separate_vocal"
}
headers = {
    "Authorization": "Bearer <token>",
    "Content-Type": "application/json"
}

response = requests.post(url, json=payload, headers=headers)

print(response.text)"
}
headers = {
    "Authorization": "Bearer <token>",
    "Content-Type": "application/json"
}

response = requests.post(url, json=payload, headers=headers)

print(response.text)

Generate Persona

import requests

url = "https://api.kie.ai/api/v1/generate/generate-persona"

payload = {
    "taskId": "5c79****be8e",
    "audioId": "e231****-****-****-****-****8cadc7dc",
    "name": "Electronic Pop Singer",
    "description": "A modern electronic music style pop singer, skilled in dynamic rhythms and synthesizer tones",
    "vocalStart": 0,
    "vocalEnd": 30,
    "style": "Electronic Pop"
}
headers = {
    "Authorization": "Bearer <token>",
    "Content-Type": "application/json"
}

response = requests.post(url, json=payload, headers=headers)

print(response.text)




