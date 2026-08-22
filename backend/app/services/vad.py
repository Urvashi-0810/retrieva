import torch
import numpy as np

class SileroVADService:
    def __init__(self, sample_rate: int = 16000):
        self.sample_rate = sample_rate
        print("Loading Silero VAD model...")
        # Load the ONNX version of Silero VAD for fast local inference
        self.model, utils = torch.hub.load(
            repo_or_dir='snakers4/silero-vad',
            model='silero_vad',
            force_reload=False,
            onnx=True,
            trust_repo=True
        )
        self.get_speech_timestamps = utils[0]
        print("VAD Model loaded successfully.")

    async def process_audio_frame(self, frame: bytes) -> bool:
        """
        Implements the VADServiceProtocol from Person 1.
        Analyzes a chunk of PCM16 audio bytes and returns True if speech is detected.
        """
        # 1. Convert raw bytes to a numpy array (16-bit PCM)
        audio_np = np.frombuffer(frame, dtype=np.int16).astype(np.float32)
        
        # 2. Normalize the audio to a range of [-1.0, 1.0] 
        audio_np = audio_np / 32768.0 
        
        # 3. Convert numpy array to PyTorch tensor
        audio_tensor = torch.from_numpy(audio_np)

        # 4. Get the confidence score from the model
        # The model returns a tensor with the probability of speech
        speech_prob = self.model(audio_tensor, self.sample_rate).item()
        
        # 5. Return True if probability is higher than 50%
        return speech_prob >= 0.5