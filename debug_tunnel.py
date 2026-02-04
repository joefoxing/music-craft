import requests
import socket
import time

url = "https://music.joefoxing.it.com/"
print(f"Testing {url}")
try:
    # Set a longer timeout
    response = requests.get(url, timeout=30)
    print(f"Status: {response.status_code}")
    print(f"Headers: {response.headers}")
    print(f"Body length: {len(response.text)}")
except requests.exceptions.ConnectTimeout as e:
    print(f"Connect timeout: {e}")
except requests.exceptions.ReadTimeout as e:
    print(f"Read timeout: {e}")
except requests.exceptions.ConnectionError as e:
    print(f"Connection error: {e}")
except Exception as e:
    print(f"Other error: {e}")

# Also test via IP address with Host header
print("\nTesting with IP and Host header...")
try:
    # Use the IP address from DNS
    ip = "172.64.80.1"
    headers = {"Host": "music.joefoxing.it.com"}
    response = requests.get(f"https://{ip}/", headers=headers, timeout=10, verify=False)
    print(f"Status via IP: {response.status_code}")
except Exception as e:
    print(f"IP test error: {e}")

# Test localhost
print("\nTesting localhost:5000...")
try:
    response = requests.get("http://localhost:5000/", timeout=5)
    print(f"Localhost status: {response.status_code}")
except Exception as e:
    print(f"Localhost error: {e}")