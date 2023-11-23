import pyaudio

def print_audio_device_list():
    p = pyaudio.PyAudio()

    print("Available audio devices:")
    for i in range(p.get_device_count()):
        device_info = p.get_device_info_by_index(i)
        print(f"  {i}: {device_info['name']}")

    p.terminate()
