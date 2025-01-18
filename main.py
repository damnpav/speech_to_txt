import io
from google.oauth2 import service_account
from google.cloud import speech
from pydub import AudioSegment

def ensure_mono(audio_path):
    audio = AudioSegment.from_wav(audio_path)
    if audio.channels > 1:
        print("Converting stereo to mono...")
        audio = audio.set_channels(1)
        mono_audio_path = audio_path.replace('.wav', '_mono.wav')
        audio.export(mono_audio_path, format='wav')
        return mono_audio_path
    return audio_path

client_file = 'speechdemo-447721-8b16a025ef9c.json'
credentials = service_account.Credentials.from_service_account_file(client_file)
client = speech.SpeechClient(credentials=credentials)

# Load audio file
audio_file = 'audio/output_16_38_48_04_11.wav'
audio_file = ensure_mono(audio_file)
with io.open(audio_file, 'rb') as f:
    content = f.read()
    audio = speech.RecognitionAudio(content=content)

config = speech.RecognitionConfig(
    encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
    sample_rate_hertz=44100,
    language_code='ru-RU',
    alternative_language_codes=['en-US'],
    speech_contexts=[speech.SpeechContext(
            phrases=['neural network', 'gradient descent', 'data frame',
                     'PyTorch', 'TensorFlow', 'feature', 'features', 'boosting',
                     'boostings', 'l1', 'l2'
                     ]
        )]
)

response = client.recognize(config=config, audio=audio)
print(response)
