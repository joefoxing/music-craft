import requests
import time

# Upload audio file
audio_file = r"E:\Developer\lyric_cover_staging\app\static\uploads\test.mp3"

print("Uploading file...")
with open(audio_file, "rb") as f:
    response = requests.post(
        "http://localhost:8000/v1/lyrics",
        files={"file": ("test.mp3", f, "audio/mpeg")},
        data={
            "language_hint": "auto",
            "timestamps": "word"
        }
    )

job_data = response.json()
job_id = job_data["job_id"]
print(f"Job created: {job_id}")
print(f"Status: {job_data['status']}")

# Poll for result
print("\nChecking status...")
for i in range(30):
    time.sleep(2)
    status_resp = requests.get(f"http://localhost:8000/v1/lyrics/{job_id}")
    status_data = status_resp.json()
    
    status = status_data["status"]
    print(f"  [{i+1}/30] Status: {status}")
    
    if status == "done":
        print("\n=== EXTRACTION COMPLETE ===")
        print("\nLYRICS:")
        print(status_data["result"]["lyrics"])
        print("\nMETADATA:")
        print(f"Language: {status_data['meta']['language_detected']}")
        print(f"Duration: {status_data['meta']['duration_sec']}s")
        break
    elif status == "error":
        print(f"\nERROR: {status_data.get('error')}")
        break
