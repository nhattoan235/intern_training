

import requests

message = "Hello World!"

try:
    response = requests.post(
        'http://localhost:5000/message',
        json={"message": message},
        timeout=3
    )
    print(f" [x] Sent '{message}' -> Server responded: {response.status_code}")
except requests.exceptions.ConnectionError:
    print(" [!] FAILED: Could not reach server. Message is LOST FOREVER.")
