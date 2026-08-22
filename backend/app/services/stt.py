import httpx
import os

class SarvamSTTService:
    def __init__(self):
        # We grab the API key from your environment variables so it's not hardcoded
        self.api_key = os.getenv("SARVAM_API_KEY", "sk_5uv9pv0h_y82phMdsHWkBh04e7YSPqEHl/q")
        self.api_url = "https://api.sarvam.ai/speech-to-text" # Verify this exact endpoint in their docs
        
        # We reuse the client to save latency on connection setup
        self.client = httpx.AsyncClient(timeout=5.0)

    async def transcribe(self, audio_data: bytes) -> str:
        """
        Implements the STTServiceProtocol from Person 1.
        Sends the audio bytes to Sarvam AI and returns the transcribed text.
        """
        # Sarvam typically expects a file upload format (multipart/form-data)
        files = {
            'file': ('audio.wav', audio_data, 'audio/wav')
        }
        
        headers = {
            'api-subscription-key': self.api_key
        }
        
        try:
            # Make the async HTTP request to Sarvam
            response = await self.client.post(
                self.api_url,
                files=files,
                headers=headers
            )
            response.raise_for_status() # Raise an error if the API fails (e.g. 401 Unauthorized)
            
            # Parse the JSON response
            result = response.json()
            
            # Extract the text (The exact key depends on Sarvam's response JSON format)
            # You may need to change 'transcript' to whatever their docs specify.
            transcribed_text = result.get("transcript", "")
            
            return transcribed_text
            
        except httpx.HTTPStatusError as e:
            print(f"Sarvam API returned an error: {e}")
            return ""
        except Exception as e:
            print(f"An unexpected error occurred during transcription: {e}")
            return ""
            
    async def close(self):
        # Good practice to close the client when shutting down the app
        await self.client.aclose()