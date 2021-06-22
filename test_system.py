import os
import time
from concurrent.futures import ThreadPoolExecutor
from threading import Semaphore

mutex = Semaphore()


def start_name_server():
    os.system("python main.py start-name-service")


def create_chord_node(i: int):
    print()
    os.system(f"python main.py create-chord-node {i}")


def create_chord_node(i: int):
    print()
    os.system(f"python main.py create-chord-node {i}")

def create_router_node():
    # print()
    os.system("python main.py create-router-node")

def print_finger_table():
    # print()
    os.system("python main.py finger-table")

def print_hash_table():
    # print()
    os.system("python main.py hash-table")

def scrap(url: str):
    # print()
    os.system(f"python main.py scrap {url}")

if __name__ == "__main__":
    urls = [
        "http://www.cubaeduca.cu",
        "http://www.etecsa.cu",
        "http://www.uci.cu",
        "http://evea.uh.cu",
    ]

    indices = [0, 6, 3, 5]


    try:
        with ThreadPoolExecutor() as executor:
            executor.submit(start_name_server)

            time.sleep(.5)
            executor.submit(create_chord_node, indices[0])

            for i in indices[1:]:
                time.sleep(.5)
                executor.submit(create_chord_node, i)

            time.sleep(.5)

            print()
            for i in range(4, -1, -1):
                time.sleep(1)
                print(f'\rFinger Tables will be impressed in: {i}', end='')
            print('\r' + ' ' * 80, end='')
            print('\r', end='')
            print_finger_table()

            print()
            executor.submit(create_router_node)
            executor.submit(create_router_node)
            executor.submit(create_router_node)

            time.sleep(1)
            for url in urls:
                executor.submit(scrap, url)
            
            print()
            time.sleep(4)
            print_hash_table()
            print()
            print("End")
            exit()
    except KeyboardInterrupt:
        exit()
