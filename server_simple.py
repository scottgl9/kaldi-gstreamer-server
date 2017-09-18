#!/usr/bin/python
import os
import signal
import subprocess
import time

def main():
    p1 = subprocess.Popen('python kaldigstserver/master_server.py --port=8888', shell=True)
    time.sleep(1)
    p2 = subprocess.Popen('python kaldigstserver/worker.py -u ws://localhost:8888/worker/ws/speech -c tedlium_english_nnet2.yaml', shell=True)
    try:
        exit_codes = [p.wait() for p in p1, p2]
    except (KeyboardInterrupt, SystemExit):
        os.kill(p2.pid, signal.SIGINT)
        os.kill(p1.pid, signal.SIGINT)
        time.sleep(2)

if __name__ == "__main__":
    main()
