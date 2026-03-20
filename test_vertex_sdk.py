import os
import vertexai
from vertexai.vision_models import MultiModalEmbeddingModel, Video

try:
    project = "jwlee-argolis-202104"
    location = "us-central1" # MultiModalEmbeddingModel usually requires a region
    vertexai.init(project=project, location=location)
    
    # Test 1: Try gemini-embedding-2-preview
    try:
         print("Attempting to load 'gemini-embedding-2-preview'")
         model = MultiModalEmbeddingModel.from_pretrained("gemini-embedding-2-preview")
         print("SUCCESS: gemini-embedding-2-preview loaded!")
    except Exception as e:
         print(f"FAILED gemini-embedding-2-preview: {e}")

    # Test 2: Try multimodalembedding@001
    try:
         print("\nAttempting to load 'multimodalembedding@001'")
         model = MultiModalEmbeddingModel.from_pretrained("multimodalembedding@001")
         print("SUCCESS: multimodalembedding@001 loaded!")
    except Exception as e:
         print(f"FAILED multimodalembedding@001: {e}")

except Exception as e:
    print(f"VERTEX INIT ERROR: {e}")
