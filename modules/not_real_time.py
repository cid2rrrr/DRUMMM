import librosa, glob, soundfile, librosa.display, os, mido
import numpy as np
import tensorflow as tf
from scipy import signal, ndimage
from matplotlib import pyplot as plt
from audiomentations import AddGaussianNoise
from modules import model_def, onset_novelty, LR_assign

GM_STANDARD = {'B' : 36, # Accoustic Bass Drum
               'S' : 38, # Accoustic Snare
               'FT': 41, # Low Floor Tom
               'MT': 47, # Low-Mid Tom
               'HT': 50, # High Tom
               'CH': 42, # Closed Hi-Hat
               'OH': 46, # Open Hi-Hat
               'R' : 51, # Ride Cymbal 1
               'CC_R': 49, # Crash Cymbal 1
               'CC_L': 57, # Crash Cymbal 2 / substitute candidates : 52-ChineseCymbal, 55-SplashCymbal
               }



class DrumDetection:
    def __init__(self, sr=22050, file_path='./output.wav', use_rnn=False, ignore_bpm=False, create_midi=False):
        self.file_path = file_path
        self.txt_path = file_path[:-4]+'.txt'
        self.mid_path = file_path[:-4]+'.mid'
        self.use_rnn = use_rnn
        self.ignore_bpm = ignore_bpm
        self.y = None
        self.sr = sr
        self.nov_smooth = None
        self.bpm = None
        self.peaks = None
        self.onset_times = None
        self.beats = None
        self.time_diff = []
        self.test_dir = './imsi/mel/'
        self.relative_bpm = 100
        self.img_height = 217
        self.img_width = 334
        self.prd_cls = []
        self.create_midi = create_midi
        self.ticks_per_beat = 600
        self.velocity = 100

        if use_rnn:
            self.rnn = model_def.rnn()
        self.arr = []
        self.gauss = AddGaussianNoise(p=1.0, min_amplitude=0.0005, max_amplitude=0.001)

    def read(self):
        self.y, _ = librosa.load(self.file_path, sr=self.sr, mono=True)
        self.y = librosa.util.normalize(self.y)

    def get_time_info(self):
        nov, _ = onset_novelty.compute_novelty_complex(self.y, Fs=self.sr, N=model_def.N, H=model_def.H, gamma=10)
        nov_smooth = ndimage.gaussian_filter1d(nov, sigma=2)

        self.bpm = round(librosa.beat.tempo(onset_envelope=np.append(np.array([0,0,0,0,0,0,0,0,0]),nov_smooth), \
            sr=self.sr, hop_length=model_def.H, start_bpm=90, max_tempo=150, ac_size=4)[0], 2)

        self.nov_smooth = ndimage.gaussian_filter1d(nov, sigma=8)   ###### 중복됨
        self.peaks = onset_novelty.peak_picking_roeder(np.append(np.array([0,0,0,0,0]),self.nov_smooth), direction=None, abs_thresh=None, 
                                            rel_thresh=None, descent_thresh=None, 
                                            tmin=None, tmax=None)
        self.peaks = self.peaks[::-1] - 5

        if self.ignore_bpm:
            self.onset_times = librosa.samples_to_time(self.peaks * model_def.H)
        else:
            self.onset_times = librosa.samples_to_time(self.peaks * model_def.H) * self.bpm / self.relative_bpm

        self.beats = onset_novelty.quantize_n_sec2beat(self.onset_times, self.bpm)

    def chop_samples(self):
        # existed file removal
        for f in glob.glob('./imsi/*.wav'):
            os.remove(f)
        for f in glob.glob('./imsi/mel/*.jpg'):
            os.remove(f)


        onset_bt = librosa.onset.onset_backtrack(self.peaks, self.nov_smooth)

        for i in range(len(onset_bt)):
            j = 4134
            if i < len(onset_bt)-1:
                if (onset_bt * model_def.H)[i+1] - (onset_bt * model_def.H)[i] < 4134:
                    j = (onset_bt * model_def.H)[i+1] - (onset_bt * model_def.H)[i]
            imsi = self.y[(onset_bt * model_def.H)[i]:(onset_bt * model_def.H)[i]+j]
            if len(imsi) < 4134:
                tmp = np.zeros(2000)
                tmp = self.gauss(tmp, sample_rate=self.sr)
                imsi = np.append(imsi,tmp)
                imsi = imsi[:4134]
            imsi = librosa.util.normalize(imsi)
            f_sample = librosa.feature.melspectrogram(y=imsi, hop_length=128)
            librosa.display.specshow(librosa.power_to_db(f_sample), cmap='jet', y_axis='mel')
            plt.clim(-70,20)
            plt.axis('off')
            plt.savefig(fname='./imsi/mel/'+str(i).zfill(4)+'.jpg', bbox_inches='tight', pad_inches=0)
            plt.close()

            soundfile.write('./imsi/'+str(i).zfill(4)+'.wav', imsi, self.sr, format='WAV')

    def classify(self):
        test_ds = tf.keras.preprocessing.image_dataset_from_directory(
                    self.test_dir,
                    shuffle=False,
                    label_mode=None,
                    image_size=(self.img_height, self.img_width),
                    batch_size=1)

        norm_test_ds = test_ds.map(lambda x: (model_def.normalization_layer(x)))

        prd = model_def.model.predict(norm_test_ds)

        self.arr = []

        for i in range(prd.shape[0]):
            if not self.use_rnn:
                self.arr.append(prd[i].argmax())
            else:
                if prd[i].max() > 0.7:
                    self.arr.append(prd[i].argmax())
                else:
                    beat_pos = self.beats[i]
                    top3_idx = prd[i].argsort()[-3:][::-1]
                    beat_pos_start = max(0, beat_pos-31)

                    starting_point = 0
                    if beat_pos - 31 < 0:
                        starting_point = abs(beat_pos - 31)

                    bar = np.zeros((31,30))

                    if beat_pos_start != beat_pos:
                        for j in range(int(beat_pos_start), int(beat_pos)):
                            if j in self.beats:
                                bar[int(starting_point+j-beat_pos_start)][self.arr[list(self.beats).index(j)]] = 1

                    for j in range(len(bar)):
                        if np.where(bar[j] == 1)[0].size == 0:
                            bar[j][29] = 1

                    rnn_prd = self.rnn.predict(np.expand_dims(bar, axis=0))[0][0]

                    # max_val = -1
                    # for candidate in range(len(rnn_prd)):
                    #     if max_val < rnn_prd[candidate] * prd[i][candidate]:
                    #         max_val = rnn_prd[candidate] * prd[i][candidate]
                    #         chosen = candidate

                    # self.arr.append(chosen)######## imsi

                    self.arr.append((prd[i] * rnn_prd).argmax())


    def prd2text(self):
        for a in self.arr:
            self.prd_cls.append(model_def.class_names[a])
        
        self.prd_cls = LR_assign.separate_cc(self.prd_cls)
        hands, feet = LR_assign.foot_hand_separate(self.prd_cls)
        hands, r_hnd, l_hnd = LR_assign.first_progress(hands)
        _, r_hnd, l_hnd = LR_assign.second_progress(hands, r_hnd, l_hnd)
        r_hnd = LR_assign.class_to_txt(r_hnd)
        l_hnd = LR_assign.class_to_txt(l_hnd)


        self.time_diff = [self.onset_times[0]]
        for i in range(1, len(self.onset_times)):
            diff = self.onset_times[i] - self.onset_times[i-1]
            self.time_diff.append(diff)

        try:
            with open(self.txt_path, 'w') as file:
                if not self.ignore_bpm:
                    file.write('<bpm=' + str(self.bpm) + '>\n')
                for i in range(len(self.time_diff)):
                    file.write(str(0) +'\t ' + str(self.time_diff[i])[:5] + '\t ' + str(r_hnd[i][0]) \
                            + '\t ' + str(l_hnd[i][0]) + '\t ' + str(r_hnd[i][1]) \
                            + '\t ' + str(l_hnd[i][1]) + '\t ' + str(feet[i][0]) + '\t ' + str(feet[i][1]) + '\n')
        except Exception as e:
            print(f'Text File Error: {e}')

    def midi(self):
        mid = mido.MidiFile()
        mid.ticks_per_beat = self.ticks_per_beat
        track = mido.MidiTrack()
        mid.tracks.append(track)

        for i in range(len(self.prd_cls)):
            if i == 0:
                start_time = self.time_diff[i]
                end_time = self.time_diff[i+1] / 2 \
                    if len(self.prd_cls) > 1 else 150
            elif i + 1 == len(self.prd_cls):
                start_time = self.time_diff[i] / 2
                end_time = 0.150
            else:
                start_time = self.time_diff[i] / 2
                end_time = self.time_diff[i+1] / 2

            start_time = int(start_time * 1000)
            end_time = int(end_time * 1000)

            clss = self.prd_cls[i].split('+')

            for j in range(len(clss)):
                if j == 0:
                    track.append(mido.Message('note_on', velocity=self.velocity, \
                                        note=GM_STANDARD[clss[j]], time=start_time))
                else:
                    track.append(mido.Message('note_on', velocity=self.velocity, \
                                        note=GM_STANDARD[clss[j]], time=0))
            
            for k in range(len(clss)):
                if k == 0:
                    track.append(mido.Message('note_off', velocity=0, \
                                              note=GM_STANDARD[clss[k]], time=end_time))
                else:
                    track.append(mido.Message('note_off', velocity=0, \
                                              note=GM_STANDARD[clss[k]], time=0))

        mid.save(self.mid_path)


    def run(self):
        self.read()
        self.get_time_info()
        self.chop_samples()
        self.classify()
        self.prd2text()
        if self.create_midi:
            self.midi()
        for f in glob.glob('./imsi/*.wav'):
            os.remove(f)
        for f in glob.glob('./imsi/mel/*.jpg'):
            os.remove(f)
        print("Done!")

