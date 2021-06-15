import os
import time
import multiprocessing


def method1():
    os.system("python main.py start-name-service")


def method2():
    os.system("python main.py create-node --id 0")


if __name__ == "__main__":
    if os.fork():
        method1()
    else:
        time.sleep(1)
        print()
        method2()
