import pyaudio, wave, sys


FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 22050
CHUNK = 512 * 2

OUTPUT_FILENAME = "./output.wav"


if __name__ == "__main__":
    audio_frames = []
    if len(sys.argv) == 2:
        idx = sys.argv[1]
    else:
        idx = 2

    audio = pyaudio.PyAudio()
    stream = audio.open(format=FORMAT, channels=CHANNELS,
                        rate=RATE, input=True,
                        frames_per_buffer=CHUNK,
                        input_device_index=idx)

    try:
        while True:
            audio_data = stream.read(CHUNK)
            audio_frames.append(audio_data)

            if len(audio_frames) > 0:
                output_wave = wave.open(OUTPUT_FILENAME, 'wb')
                output_wave.setnchannels(CHANNELS)
                output_wave.setsampwidth(2)
                output_wave.setframerate(RATE)
                output_wave.writeframes(b''.join(audio_frames))
                output_wave.close()                

    except KeyboardInterrupt:
        pass

    stream.stop_stream()
    stream.close()
    audio.terminate()