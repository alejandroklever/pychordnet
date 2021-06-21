import os
import time
from concurrent.futures import ThreadPoolExecutor
from threading import Semaphore

mutex = Semaphore()


def start_name_server():
    os.system("python main.py start-name-service")


def create_chord_node(i: int):
    mutex.acquire()
    time.sleep(1)
    mutex.release()
    os.system(f"python main.py create-chord-node {i}")


if __name__ == "__main__":
    urls = [
        "http://www.cubaeduca.cu",
        "http://www.etecsa.cu",
        "http://www.uci.cu",
        "http://evea.uh.cu",
        "http://www.uo.edu.cu",
        "http://www.uclv.edu.cu",
        "http://covid19cubadata.uh.cu",
        "http://www.uh.cu",
    ]

    indices = [0, 6, 3]

    with ThreadPoolExecutor() as executor:
        try:
            executor.submit(start_name_server)
            executor.map(create_chord_node, indices)
            while True:
                pass
        except KeyboardInterrupt:
            executor.shutdown(wait=False)
