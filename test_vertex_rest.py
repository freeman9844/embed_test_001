import os
import base64
import requests
from google.auth import default
from google.auth.transport.requests import Request

def get_access_token():
    credentials, project = default()
    auth_request = Request()
    credentials.refresh(auth_request)
    return credentials.token, project

try:
    token, project = get_access_token()
    project_id = "jwlee-argolis-202104" # Explicitly use user's project
    location = "us-central1" # Or global, but REST sometimes requires endpoint region
    model_id = "gemini-embedding-2-preview"

    # Let's use a dummy small bytes object for a video if possible, or simple image/text
    # To accurately test, we need actual short bytes if possible, but let's test payload wrapping
    
    url = f"https://{location}-aiplatform.googleapis.com/v1/projects/{project_id}/locations/{location}/publishers/google/models/{model_id}:embedContent"
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }

    # Custom payload following Vertex :embedContent schema for video inlineData
    payload = {
         "content": {
             "parts": [
                 {
                     "inlineData": {
                         "mimeType": "video/mp4",
                         "data": "AAAAIGZ0eXBpc29tAAACAGlzb21pc28yYXZjMW1wNDEAAAAIbW9vdgAAAGxtdmhkAAAAAK7Yg8Ku2IPCAAADFQAAV+QAAQAAAQAAAAAAAAAAAAAAAAEAAAAAAAAAAAAAAAAAAAABAAAAAAAAAAAAAAAAAABAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAgAAAtR0cmFrAAAAXHRraGQAAAADrtiDwq7Yg8IAAAABAAAAA" # Small dummy base64
                     }
                 }
             ]
         }
    }



    print(f"Calling Vertex AI Endpoint: {url}")
    response = requests.post(url, headers=headers, json=payload)
    
    print(f"Status: {response.status_code}")
    print(f"Response: {response.text}")

except Exception as e:
    print(f"REST Call Error: {e}")
