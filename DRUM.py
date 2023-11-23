import pyaudio, keyboard, wave, argparse
import modules.real_time.init as init
from modules.not_real_time import *
from modules.pyaudio_index_list import *


def record_audio(output_filename, device_idx=2):
    CHUNK = 1024
    FORMAT = pyaudio.paInt16
    CHANNELS = 1
    RATE = 22050

    p = pyaudio.PyAudio()

    stream = p.open(format=FORMAT,
                    channels=CHANNELS,
                    rate=RATE,
                    input=True,
                    frames_per_buffer=CHUNK,
                    input_device_index=device_idx)

    frames = []

    print("Press 'q' to stop recording.")

    while not keyboard.is_pressed('q'):
        data = stream.read(CHUNK)
        frames.append(data)

    print("Saved to " + output_filename + '.')

    stream.stop_stream()
    stream.close()
    p.terminate()

    with wave.open(output_filename, 'wb') as wf:
        wf.setnchannels(CHANNELS)
        wf.setsampwidth(pyaudio.PyAudio().get_sample_size(FORMAT))
        wf.setframerate(RATE)
        wf.writeframes(b''.join(frames))

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Drum Classification with --use_rnn and --real_time options')

    parser.add_argument('--use_rnn', action='store_true', help='Using RNN when predicting')
    parser.add_argument('--real_time', action='store_true', help='Using Real-Time predicting')
    parser.add_argument('--ignore_bpm', action='store_true', help='Set bpm as 100 when making .txt file')
    parser.add_argument('--record_idx', type=int, help='Assign a device index')
    parser.add_argument('--wav', help='Assign a device index')
    parser.add_argument('--idx_list', action='store_true', help='List audio device index list')
    parser.add_argument('--create_midi', action='store_true', help='Create .mid file')


    args = parser.parse_args()

    device_idx = 2 if args.record_idx is None else args.record_idx
    output_filename = "./output.wav" if args.wav is None else args.wav

    init.rm_post_data('./imsi/','wav')
    init.rm_post_data('./imsi/mel/', 'jpg')
    init.rm_post_data('./', 'txt')
    if args.idx_list:
        print_audio_device_list()
    elif args.use_rnn and (args.real_time or args.ignore_bpm):
        print("Error: --use_rnn can be only single used.")
    elif args.create_midi and (args.real_time or args.ignore_bpm):
        print("Midi File needs BPM info. (can't be used w/ ignore_bpm or real_time).")
    elif args.real_time:
        init.main()
    else:
        drum_model = DrumDetection(file_path=output_filename, use_rnn=args.use_rnn, ignore_bpm=args.ignore_bpm, create_midi=args.create_midi)
        if args.wav is None:    
            record_audio(output_filename, device_idx)
        drum_model.run()


