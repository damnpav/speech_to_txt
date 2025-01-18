import pyaudio
import queue
import wave
import threading
from google.cloud import speech
from google.oauth2 import service_account
from datetime import datetime as dt

client_file = 'speechdemo-447721-8b16a025ef9c.json'
credentials = service_account.Credentials.from_service_account_file(client_file)
client = speech.SpeechClient(credentials=credentials)

FORMAT = pyaudio.paInt16  # Audio format (16-bit PCM)
RATE = 44100              # Sample rate
CHUNK = 1024   # Frames per buffer
input_device = 2
CHANNELS = 1
WAVE_OUTPUT_FILENAME = f"audio/stream_trans_{dt.now().strftime(f'%H_%M_%S__%Y%m%d')}.wav"

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


def save_audio_to_file():
    #print(f"Recording audio to {WAVE_OUTPUT_FILENAME}...")
    wf = wave.open(WAVE_OUTPUT_FILENAME, 'wb')
    wf.setnchannels(1)
    wf.setsampwidth(pyaudio.PyAudio().get_sample_size(pyaudio.paInt16))
    wf.setframerate(RATE)

    while True:
        chunk = audio_queue.get()
        if chunk is None:  # End signal
            break
        wf.writeframes(chunk)  # Write audio chunk to WAV file

    wf.close()
    print(f"Audio saved to {WAVE_OUTPUT_FILENAME}")


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

    # Thread for saving audio to a file
    recorder_thread = threading.Thread(target=save_audio_to_file, daemon=True)
    recorder_thread.start()

    # Thread for real-time transcription
    transcription_thread = threading.Thread(target=listen_and_transcribe, daemon=True)
    transcription_thread.start()


    try:
        stream.start_stream()
        while True:
            pass  # Keep the main thread alive
    except KeyboardInterrupt:
        print("\nStopping...")
        stream.stop_stream()
        stream.close()
        audio_interface.terminate()
        audio_queue.put(None)  # Signal the recorder thread to stop
        recorder_thread.join()
        transcription_thread.join()
        print("Finished.")

main()