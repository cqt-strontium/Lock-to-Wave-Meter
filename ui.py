__doc__ = """
Easy interface for controller. 

Valid commands: 
1. LOCK: set wavelength & PID gain and lock
2. STOP: pause lock
3. TUNE: set PID gain and let set wavelength vary as step function 
4. EXIT: exit program
5. HELP: reveal this message
"""

from multiprocessing import Process, Queue, freeze_support 
from pid_controller import PIDController
import time 


def tune_mode():
    while True:
        try: 
            kp, ki, kd = (float(_) for _ in input('Please input PID gains:\n').split())
        except:
            continue
        else:
            return kp, ki, kd 


def lock_mode():
    while True:
        wl = input('Please input wavelength set point:\n')
        if len(wl):
            try:
                wl = float(wl)
            except:
                continue
            else:
                break
        else:
            break
    return wl, *tune_mode()


def stop_mode():
    return ()


def pid_lock(q, args):
    pc = PIDController(1, "COM56", 9, *args)
    while True:
        pc.loop()
        if not q.empty():
            pc.cleanup()
            return 


def pid_tune(q, args):
    pc = PIDController(1, "COM56", 9, None, *args)
    wl = pc.set_wavelength
    hp, offset = 100, 1e-4
    while True:        
        pc.set_wavelength = wl - offset
        for _ in range(hp):
            pc.loop()
            time.sleep(.05)
            if not q.empty():
                pc.cleanup()
                return 

        pc.set_wavelength = wl + offset
        for _ in range(hp):
            pc.loop()
            time.sleep(.05)
            if not q.empty():
                pc.cleanup()
                return 
                

def pid_pause(q, args):
    while q.empty(): 
        time.sleep(.05)


def backend(q):
    cmd2func = dict(zip(['lock', 'tune', 'stop'],[pid_lock,pid_tune, pid_pause]))
    while True:
        if not q.empty():
            cmd, args = q.get()
            if cmd == 'exit':
                return 
            cmd2func[cmd](q, args)


if __name__ == '__main__':
    freeze_support()
    
    cmd_queue = Queue()
    background = Process(target=backend, args=(cmd_queue,))
    background.start()

    cmd2func = dict(zip(['lock', 'tune', 'stop', 'exit', 'help'],[lock_mode,tune_mode, stop_mode, stop_mode, None]))

    while True: 
        cmd = input('Please input command:').strip().lower()
        if cmd == 'help':
            print(__doc__)
            continue
        if cmd in cmd2func.keys():
            args = cmd2func[cmd]() 

            cmd_queue.put((cmd, args))
            if cmd == 'exit': 
                break
        elif not cmd:
            continue
        else:
            print('Invalid command.')
            print('Valid commands are:%s'%(', '.join(cmd2func.keys())), end='.\n')
    
    background.join()  # wait for the clean-up process
    