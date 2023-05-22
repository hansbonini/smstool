import os
import struct
import wave


class PSGSegment:
    def __init__(self, start, end, name):
        self.start = start
        self.end = end
        self.name = name

    def read_psg_data(self, psg_data):
        audio_samples = [0.2, -0.1, 0.5, -0.3, 0.4, -0.2]

        return audio_samples

    def save_wav(self, audio_samples, path):
        sample_width = 2  # 2 bytes (16 bits)
        num_channels = 1  # Mono
        sample_rate = 44100  # 44.1 kHz
        num_frames = len(audio_samples)

        with wave.open(path, "w") as wav_file:
            wav_file.setnchannels(num_channels)
            wav_file.setsampwidth(sample_width)
            wav_file.setframerate(sample_rate)
            wav_file.setnframes(num_frames)

            audio_data = [int(sample * (2 ** (sample_width * 8 - 1) - 1)) for sample in audio_samples]
            wav_file.writeframes(struct.pack("<" + "h" * num_frames, *audio_data))

    def process(self, psg_data):
        audio_samples = self.read_psg_data(psg_data)

        wav_folder = os.path.join("data", "wav")
        os.makedirs(wav_folder, exist_ok=True)

        wav_path = os.path.join(wav_folder, f"{self.name}.wav")
        self.save_wav(audio_samples, wav_path)

        print(f"PSG Segment {self.name}: PSG data saved as WAV.")
