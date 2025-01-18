import pyaudio
import queue
import threading
from google.cloud import speech
from google.oauth2 import service_account

client_file = 'speechdemo-447721-8b16a025ef9c.json'
credentials = service_account.Credentials.from_service_account_file(client_file)
client = speech.SpeechClient(credentials=credentials)

FORMAT = pyaudio.paInt16  # Audio format (16-bit PCM)
RATE = 16000              # Sample rate
CHUNK = int(RATE / 10)    # Frames per buffer
input_device = 2
CHANNELS = 1

audio_queue = queue.Queue()


def callback(in_data, frame_count, time_info, status):
    audio_queue.put(in_data)
    return None, pyaudio.paContinue


def create_audio_stream():
    audio_interface = pyaudio.PyAudio()
    stream = audio_interface.open(
        format=FORMAT,
        channels=CHANNELS,
        rate=RATE,
        input=True,
        input_device_index=input_device,
        frames_per_buffer=CHUNK,
        stream_callback=callback,
    )
    return stream, audio_interface


# Streaming transcription
def listen_and_transcribe():
    config = speech.RecognitionConfig(
        encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
        sample_rate_hertz=RATE,
        language_code="ru-RU",
        #alternative_language_codes=["en-US"],  # For mixed Russian-English speech
        enable_automatic_punctuation=True
    )
    streaming_config = speech.StreamingRecognitionConfig(config=config, interim_results=True)

    def generator():
        while True:
            chunk = audio_queue.get()
            if chunk is None:
                break
            yield speech.StreamingRecognizeRequest(audio_content=chunk)

    requests = generator()
    responses = client.streaming_recognize(config=streaming_config, requests=requests)

    # Process responses
    for response in responses:
        for result in response.results:
            if result.is_final:
                print(f"Transcript: {result.alternatives[0].transcript}")


def main():
    stream, audio_interface = create_audio_stream()
    print("Listening and transcribing...")

    threading.Thread(target=listen_and_transcribe, daemon=True).start()

    try:
        stream.start_stream()
        while True:
            pass  # Keep the main thread alive
    except KeyboardInterrupt:
        print("\nStopping...")
        stream.stop_stream()
        stream.close()
        audio_interface.terminate()

main()