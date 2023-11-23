import librosa, soundfile, time, os, sys
sys.path.append(os.path.dirname(os.path.abspath(os.path.dirname(__file__))))
import librosa.display
import onset_novelty
import numpy as np
from scipy import ndimage
from audiomentations import AddGaussianNoise

gauss = AddGaussianNoise(p=1.0, min_amplitude=0.0005, max_amplitude=0.001)

OUTPUT_FILENAME = './output.wav'

RATE = 22050
H = 32
N = 512

onset_bt = None
chop_point = 0
y = None


def make_file():
    import matplotlib.pyplot as plt
    global onset_bt
    global chop_point
    global y

    for i in range(len(onset_bt)):
        j = 4134
        if i < len(onset_bt)-1:
            if (onset_bt*H)[i+1] - (onset_bt*H)[i] < 4134:
                j = (onset_bt*H)[i+1] - (onset_bt*H)[i]
        imsi = y[(onset_bt*H)[i]:(onset_bt*H)[i]+j]
        if len(imsi) < 4134:
            tmp = np.zeros(2000)
            tmp = gauss(tmp, sample_rate=RATE)
            imsi = np.append(imsi,tmp)
            imsi = imsi[:4134]
        imsi = librosa.util.normalize(imsi)

        f_sample = librosa.feature.melspectrogram(y=imsi, hop_length=128)


        librosa.display.specshow(librosa.power_to_db(f_sample), cmap='jet', y_axis='mel')

        plt.clim(-70,20)
        plt.axis('off')
        plt.savefig(fname='./imsi/mel/'+str(onset_bt[i]+chop_point).zfill(6)+'.jpg', bbox_inches='tight', pad_inches=0)
        plt.close()

        soundfile.write('./imsi/'+str(onset_bt[i]+chop_point).zfill(6)+'.wav', imsi, RATE, format='WAV')


def read():
    global onset_bt
    global chop_point
    global y

    num_used_peak = 0
    not_changed_cnt = 0
    chop_point = 0
    threshold = 0

    try:
        while True:
            time.sleep(0.5)
            try:
                y, _ = librosa.load(OUTPUT_FILENAME, sr=RATE, mono=True, offset=librosa.samples_to_time(chop_point*H))
            except EOFError:
                continue

            if len(y) == 0:
                continue
            if chop_point == 0:
                y = np.append(np.array([0.7,0.7]),y, axis=0)
            y = librosa.util.normalize(y)
            if chop_point == 0:
                y = y[2:]

            nov, _ = onset_novelty.compute_novelty_complex(y, Fs=RATE, N=N, H=H, gamma=10)
            nov_smooth = ndimage.gaussian_filter1d(nov, sigma=8)
            peaks = onset_novelty.peak_picking_roeder(np.append(np.array([0,0,0,0,0]),nov_smooth), direction=None, abs_thresh=None, 
                                            rel_thresh=None, descent_thresh=None, 
                                            tmin=None, tmax=None)
            
            peaks = peaks[::-1] - 5
            
            if len(peaks) == 0:
                continue

            onset_bt = librosa.onset.onset_backtrack(peaks, nov_smooth)

            onset_bt += chop_point
            onset_bt = onset_bt[onset_bt > threshold] 

            if len(onset_bt) < 5:
                not_changed_cnt += 1

            if len(onset_bt) >= 5:
                not_changed_cnt = 0
                onset_bt = onset_bt[:-2] - chop_point
                make_file()

                num_used_peak += len(onset_bt)
                onset_bt += chop_point
                chop_point = int((onset_bt[-1] + onset_bt[-2])/2) +2
                threshold = onset_bt[-1] + 2
                # print(chop_point)
                # print(threshold)

            if not_changed_cnt > 5 and len(onset_bt) > 0:
                onset_bt = onset_bt - chop_point
                make_file()

                num_used_peak += len(onset_bt)
                onset_bt += chop_point
                chop_point = onset_bt[-1] + 2
                threshold = onset_bt[-1] + 2
                not_changed_cnt = 0

            # print(not_changed_cnt)
            # if not_changed_cnt > 3:
            #     break


    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    read()