import os
from google import genai

try:
    # Initialize client with Vertex AI and global location
    client = genai.Client(vertexai=True, location='global')
    
    # Vertex AI client usually resolves the project from ADC if not provided
    print("VERTEX AUTH SUCCESS")
    print(f"Project resolved: {getattr(client._client, 'project', 'Unknown')}")
except Exception as e:
    print(f"VERTEX AUTH ERROR: {e}")
