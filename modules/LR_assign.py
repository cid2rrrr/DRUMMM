distances = {('S', 'S'): 0, ('S', 'FT'): 0.3157, ('S', 'MT'): 0.2651, ('S', 'HT'): 0.1962,
            ('S', 'HH'): 0.2345, ('S', 'R'): 0.2345, ('S', 'CC_R'): 0.5184, ('S', 'CC_L'): 0.2912,
            ('FT', 'S'): 0.3157,  ('FT', 'FT'): 0, ('FT', 'MT'): 0.2093, ('FT', 'HT'): 0.3872,
            ('FT', 'HH'): 0.5299, ('FT', 'R'): 0.2101, ('FT', 'CC_R'): 0.2054, ('FT', 'CC_L'): 0.5362,
            ('MT', 'S'): 0.2651, ('MT', 'FT'): 0.2093, ('MT', 'MT'): 0, ('MT', 'HT'): 0.2193,
            ('MT', 'HH'): 0.4027, ('MT', 'R'): 0.1621, ('MT', 'CC_R'): 0.3428, ('MT', 'CC_L'): 0.3691,
            ('HT', 'S'): 0.1962, ('HT', 'FT'): 0.3872, ('HT', 'MT'): 0.2193, ('HT', 'HT'): 0,
            ('HT', 'HH'): 0.195, ('HT', 'R'): 0.3775, ('HT', 'CC_R'): 0.5563, ('HT', 'CC_L'): 0.1517,
            ('HH', 'S'): 0.2345, ('HH', 'FT'): 0.5299, ('HH', 'MT'): 0.4027, ('HH', 'HT'): 0.195,
            ('HH', 'HH'): 0, ('HH', 'R'): 0.5645, ('HH', 'CC_R'): 0.7207, ('HH', 'CC_L'): 0.1235,
            ('R', 'S'): 0.2345, ('R', 'FT'): 0.2101, ('R', 'MT'): 0.1621, ('R', 'HT'): 0.3775,
            ('R', 'HH'): 0.5645, ('R', 'R'): 0, ('R', 'CC_R'): 0.2265, ('R', 'CC_L'): 0.5232,
            ('CC_R', 'S'): 0.5184, ('CC_R', 'FT'): 0.2054, ('CC_R', 'MT'): 0.3428, ('CC_R', 'HT'): 0.5563,
            ('CC_R', 'HH'): 0.7207, ('CC_R', 'R'): 0.2265, ('CC_R', 'CC_R'): 0, ('CC_R', 'CC_L'): 0.708,
            ('CC_L', 'S'): 0.2912, ('CC_L', 'FT'): 0.5362, ('CC_L', 'MT'): 0.3691, ('CC_L', 'HT'): 0.1517,
            ('CC_L', 'HH'): 0.1235, ('CC_L', 'R'): 0.5232, ('CC_L', 'CC_R'): 0.708, ('CC_L', 'CC_L'): 0}

###
data_dict = {}
bpm = 80 # 곡 bpm 정보
R_instrument_array = [] # 오른손악기
L_instrument_array = [] # 왼손악기
measure_array = [] # 마디
time_array = [] # 각 연주의 시간간격
instrument_array = [] # 악기
real_hnd = []  # 오른손, 왼손정보
bass_kick = [] # Bass 유무
instrument_array_exceptB = []
# first_index = 0
###

drum_dict = {0: '',
1: 'S', 
2: 'FT',
3: 'MT',
4: 'HT',
5: 'HH',
6: 'R',
7: 'CC_R',
8: 'CC_L'}
drum_dict = {v: k for k, v in drum_dict.items()}



fixed_time_array = [(time * 100)/bpm for time in time_array]


def separate_cc(prd_cls):
    transformed_prd_cls = []
    for i, cls in enumerate(prd_cls):
        spl = cls.split('+')
        new_element = []

        for s in spl:
            if s == 'C':
                if (i > 0 and any(keyword in prd_cls[i - 1] for keyword in ['R', 'MT', 'FT'])) or (i < len(prd_cls)-1 and any(keyword in prd_cls[i + 1] for keyword in ['R', 'MT', 'FT'])):
                    new_element.append('CC_R')
                else:
                    new_element.append('CC_L')
            else:
                new_element.append(s)
    
        transformed_prd_cls.append('+'.join(new_element))
    
    return transformed_prd_cls


def foot_hand_separate(prd_cls):
    prd_cls_except_b = []
    b_cls = []

    for clss in prd_cls:
        clss = clss.split('+')
        if 'B' in clss:
            clss.remove('B')
            if 'CH' in clss:
                idx = clss.index('CH')
                clss[idx] = 'HH'
                # b_cls.append('B+CH')
                b_cls.append([1,1])
            elif 'OH' in clss:
                idx = clss.index('OH')
                clss[idx] = 'HH'
                # b_cls.append('B+OH')
                b_cls.append([1,0])
            else:
                # b_cls.append('B')
                b_cls.append([1,1])
            prd_cls_except_b.append('+'.join(clss))
        else:
            if 'CH' in clss:
                idx = clss.index('CH')
                clss[idx] = 'HH'
                # b_cls.append('CH')
                b_cls.append([0,1])
            elif 'OH' in clss:
                idx = clss.index('OH')
                clss[idx] = 'HH'
                # b_cls.append('OH')
                b_cls.append([0,0])
            else:
                b_cls.append([0,1])
            prd_cls_except_b.append('+'.join(clss))
        
    return prd_cls_except_b, b_cls


def first_progress(input_data):
    # 첫 연주 분류
    instrument_array_exceptB = input_data[:]
    R_hnd = []
    L_hnd = []

    s_based_pos = ['CC_L', 'HH', 'HT', 'MT', 'FT', 'R', 'CC_R']


    for i in range(len(instrument_array_exceptB)):
        spl = instrument_array_exceptB[i].split('+')
        global first_index
        first_index = 0
        
        if instrument_array_exceptB[i] == '':   # 아무것도 연주하지 않으면 빈칸.
            R_hnd.append('')
            L_hnd.append('')
        
        if (instrument_array_exceptB[i] != '') and ('+' in instrument_array_exceptB[i]):  # 가장 첫 note가 동시연주:
                
            if 'S' in instrument_array_exceptB[i]: # 동시연주에 Snare가 포함되어 있을 경우 Snare를 왼손으로, 나머지를 오른손으로.
                L_hnd.append('S')
                # R_hnd.append(item.replace('S', '').replace('+', ''))
                R_hnd.append(instrument_array_exceptB[i].replace('S','').replace('+',''))
            else:
                if s_based_pos.index(spl[0]) < s_based_pos.index(spl[1]): # Snare 포함되어있지 않은경우 Snare 위치 기준 가까운 쪽에 할당 
                    R_hnd.append(spl[1])
                    L_hnd.append(spl[0])
                else:
                    R_hnd.append(spl[0])
                    L_hnd.append(spl[1])
            first_index = i
                        
        elif (instrument_array_exceptB[i] != ''): # 가장 첫 note가 단일 연주일 경우 무조건 오른손.
            R_hnd.append(instrument_array_exceptB[i])
            L_hnd.append('')
            first_index = i

    return instrument_array_exceptB, R_hnd, L_hnd



def second_progress(instrument_array_exceptB, R_hnd, L_hnd):
    
    s_based_pos = ['CC_L', 'HH', 'HT', 'MT', 'FT', 'R', 'CC_R']
    global first_index
    t_l_box = [0] * (first_index+1)
    t_r_box = [0] * (first_index+1)

    for i in range(first_index+1, len(instrument_array_exceptB)):  # 처음연주의 다음 연주부터 시작
        spl = instrument_array_exceptB[i].split('+')
        t_q = 60/bpm
        d_m = 0.735  # 

        t_r = 0
        t_l = 0
        
        if instrument_array_exceptB[i] == '':   # 아무것도 연주하지 않으면 빈칸.
            L_hnd.append('')
            R_hnd.append('')

        elif '+' in instrument_array_exceptB[i]:#  동시연주
            
            if spl[0]==spl[1]: # 같은 악기를 연주할 경우 
                R_hnd.append(spl[0])
                L_hnd.append(spl[0])
            
            elif 'S' in instrument_array_exceptB[i]: # 동시연주에 Snare가 포함되어 있을 경우 Snare를 왼손으로, 나머지를 오른손으로.
                L_hnd.append('S')
                R_hnd.append(instrument_array_exceptB[i].replace('S', '').replace('+', ''))
            else:
                if s_based_pos.index(spl[0]) < s_based_pos.index(spl[1]): # Snare 포함되어있지 않은경우 Snare 위치 기준 가까운 쪽에 할당 
                    R_hnd.append(spl[1])
                    L_hnd.append(spl[0])
                else:
                    R_hnd.append(spl[0])
                    L_hnd.append(spl[1])

        else :                                 # 단일연주
            local_time_R = 0
            local_time_L = 0

            d_r = 0
            d_l = 0
            
            for k in range(1,i+1):  
                if not local_time_R and R_hnd[i - k] != '': #i로부터 k번째의 note에 연주가 있을때
                    local_time_R = k
                if not local_time_L and L_hnd[i - k] != '':
                    local_time_L = k   # i번째 note로부터 가장 가까운 R과 L이 i로부터 몇번째 note에 있는지 알아냄
                if local_time_R and local_time_L:
                    break

            for p in range(local_time_L):
                t_l += fixed_time_array[i-p]
            for p in range(local_time_R):
                t_r += fixed_time_array[i-p] # k만큼 fixed_time_array의 요소를 더해서, i번째 note로부터 가장 가까운 R과 L 사이의 시간간격을 반환.

            d_r = distances[(instrument_array_exceptB[i], R_hnd[i-local_time_R])]
            print(instrument_array_exceptB[i])
            print(L_hnd[i-local_time_L] + '-')
            d_l = distances[(instrument_array_exceptB[i], L_hnd[i-local_time_L])]

            # 위 distances.get에 통합
            # if d_r is None:
            #     d_r = 0.0  # 기본값으로 0을 할당
            # if d_l is None:
            #     d_l = 0.0  # 기본값으로 0을 할당
            # min(t_l, t_r)
            if min(t_l, t_r) >= (t_q/2)-0.01: # 바로 직전 note와의 간격이 8분음표보다 길 때
                R_hnd.append(instrument_array_exceptB[i])
                L_hnd.append('')
                
            # 바로 직전 note와의 간격이 32분음표 보다 같거나 짧으면서 같은 악기 연주 : double stroke
            elif min(t_l, t_r) <=(t_q/8)+0.001  and min(t_l, t_r) >=(t_q/8)+0.01 and instrument_array_exceptB[i]==instrument_array_exceptB[i-1]: 
                R_hnd.append(R_hnd[i-1])
                L_hnd.append(L_hnd[i-1])
            elif min(t_l, t_r) <=(t_q/8)+0.001  and min(t_l, t_r) <=(t_q/8)+0.001 and instrument_array_exceptB[i]==instrument_array_exceptB[i-1]: 
                R_hnd.append(L_hnd[i-1])
                L_hnd.append(R_hnd[i-1])

            else:
                R_eval = (t_r/t_q)*(1-(d_r/d_m))
                L_eval = (t_l/t_q)*(1-(d_l/d_m))
                if R_eval > L_eval:
                    R_hnd.append(instrument_array_exceptB[i])
                    L_hnd.append('')
                else:
                    R_hnd.append('')
                    L_hnd.append(instrument_array_exceptB[i])

        t_l_box.append(t_l)
        t_r_box.append(t_r)

    return instrument_array_exceptB, R_hnd, L_hnd


def class_to_txt(prd_cls):
    txt = []
    for prd in prd_cls:
        txt.append([drum_dict[prd], 0 if prd=='' else 1])
    
    return txt