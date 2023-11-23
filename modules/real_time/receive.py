import os, time, shutil, librosa, sys
sys.path.append(os.path.dirname(os.path.abspath(os.path.dirname(__file__))))
sys.path.append(os.path.dirname(os.path.abspath(os.path.dirname(os.path.abspath(os.path.dirname(__file__))))))
from modules import LR_assign, model_def
import numpy as np

state = True


MEL_PATH = './imsi/mel/'
DATA_PATH = './data/'
BPM_PATH = './BPM/'
TEXT_PATH = './result.txt'

IMG_HEI = 217
IMG_WID = 334
last_time = 0


def run_cnn(files):
    prd = np.array([])
    arr = []
    prd_cls = []

    test_ds = model_def.tf.keras.preprocessing.image_dataset_from_directory(
        DATA_PATH,
        shuffle=False,
        label_mode=None,
        image_size=(IMG_HEI, IMG_WID),
        batch_size=1)

    norm_test_ds = test_ds.map(lambda x: (model_def.normalization_layer(x)))
    
    try:
        prd = model_def.model.predict(norm_test_ds)
    except:
        pass

    for i in range(prd.shape[0]):
            arr.append(prd[i].argmax())
    for a in arr:
        prd_cls.append(model_def.class_names[a])

    prd_cls = LR_assign.separate_cc(prd_cls)
    hands, feet = LR_assign.foot_hand_separate(prd_cls)
    hands, r_hnd, l_hnd = LR_assign.first_progress(hands)
    _, r_hnd, l_hnd = LR_assign.second_progress(hands, r_hnd, l_hnd)
    r_hnd = LR_assign.class_to_txt(r_hnd)
    l_hnd = LR_assign.class_to_txt(l_hnd)

    save2text(files, feet, r_hnd, l_hnd)


def save2text(files, feet, r_hnd, l_hnd):
    global last_time
    times = [librosa.samples_to_time(int(file[:-4])*model_def.H) for file in files]
    
    time_diff = [times[0] - last_time]
    for i in range(1, len(times)):
        diff = times[i] - times[i-1]
        time_diff.append(diff)
    last_time = times[-1]

    try:
        with open(TEXT_PATH, 'a') as file:
            # 파일 끝에 내용 추가
            for i in range(len(time_diff)):
                file.write(str(0) + '\t ' + str(time_diff[i])[:5] + '\t ' + str(r_hnd[i][0]) + '\t ' + str(l_hnd[i][0]) + '\t ' + str(r_hnd[i][1])\
                     + '\t ' + str(l_hnd[i][1]) + '\t ' + str(feet[i][0]) + '\t ' + str(feet[i][1]) + '\n')

    except FileNotFoundError:
        # 파일이 없다면 새로운 파일 생성 후 내용 추가
        with open(TEXT_PATH, 'w') as file:
            for i in range(len(time_diff)):
                file.write(str(0) +'\t ' + str(time_diff[i])[:5] + '\t ' + str(r_hnd[i][0]) + '\t ' + str(l_hnd[i][0]) + '\t ' + str(r_hnd[i][1])\
                     + '\t ' + str(l_hnd[i][1]) + '\t ' + str(feet[i][0]) + '\t ' + str(feet[i][1]) + '\n')

    except Exception as e:
        print(f'Text File Error: {e}')


def init_model():

    try:
        while state:
            time.sleep(0.5)

            files = os.listdir(MEL_PATH)
            files = [file for file in files if file.endswith('.jpg')]

            if len(files) > 1:
                for file in files:
                    if not os.path.exists(os.path.join(DATA_PATH, file)):
                        shutil.move(os.path.join(MEL_PATH, file), DATA_PATH)

                run_cnn(files)

            rm_files = os.listdir(DATA_PATH)
            for rm_file in rm_files:
                os.remove(os.path.join(DATA_PATH, rm_file))

    except KeyboardInterrupt:
        pass