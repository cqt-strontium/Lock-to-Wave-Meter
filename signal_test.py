from multiprocessing import Process 
import pynput.keyboard as kb 


def eavesdropper():
    def func(key):
        if not hasattr(key, 'char'):
            return True
        if key.char=='q':
            return False

    with kb.Listener(on_press=func) as listener:
        listener.join()


if __name__ == '__main__':
    th = Process(target=eavesdropper)
    th.start()
    while True:
        for i in range(100):
            pass 

        if not th.is_alive():
            print('I am dead')
            th = Process(target=eavesdropper)
            th.start()
            print(th.is_alive())