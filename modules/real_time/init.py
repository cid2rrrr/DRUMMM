import subprocess, threading, signal, os
from modules.real_time import receive

rec_sub = None
chop_sup = None
exit_flag = threading.Event()

def rm_post_data(path, ext):
    for filename in os.listdir(path):
        if filename.endswith('.'+ext):
            file_path = os.path.join(path, filename)
            os.remove(file_path)

def main():
    rm_post_data('./imsi/','wav')
    rm_post_data('./imsi/mel/', 'jpg')
    rm_post_data('./data/', 'jpg')
    rm_post_data('./', 'txt')

    rec_sub = subprocess.Popen(["python", "./modules/real_time/record.py"])
    chop_sub = subprocess.Popen(["python", "./modules/real_time/chop.py"])

    t = threading.Thread(target=receive.init_model)
    t.daemon = True
    t.start()
    try:
        while True:
            user_input = input("**************** \n**************** \n* Recording Started. *\n* Type 'q' to Terminate. *\n**************** \n**************** \n")
            if user_input.lower() == 'q':
                break

        exit_flag.set()
        rec_sub.send_signal(signal.SIGTERM)
        chop_sub.send_signal(signal.SIGTERM)

    except KeyboardInterrupt:
        exit_flag.set()
        rec_sub.send_signal(signal.SIGTERM)
        chop_sub.send_signal(signal.SIGTERM)

    print("Program exit.")

    rm_post_data('./imsi/','wav')
    rm_post_data('./imsi/mel/', 'jpg')

    exit()