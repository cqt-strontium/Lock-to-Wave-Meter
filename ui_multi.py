__doc__ = """
Easy interface for controller. 

Valid commands: 
1. LOCK <LASER_NO.>/[ALL] : set wavelength & PID gain and lock for laser <LASER_NO.>
2. STOP <LASER_NO.>/[ALL] : pause lock for laser <LASER_NO.>
3. LIST : list laser lock status
4. EXIT : exit program
5. HELP : reveal this message
"""

from multiprocessing import Process, Queue, freeze_support
from pid_controller import PIDController
import time
from json_load import load_settings


def input_wl():
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
    return wl


def lock_mode(arg):
    if arg == 'all' or not arg:
        index = list(range(len(lasers)))
    else:
        index = [int(arg)]
    ret = []
    for i in index:
        laser = lasers[i]
        if laser['WaveMeterChannel'] == -1:
            print('Warning: No WaveMeterChannel specified, cannot lock laser %s.' % (laser['Name']))
        laser['Locked'] = True
        ret.append((laser['WaveMeterChannel'], laser['ArduinoPort'], laser['ArduinoPin'],
                   laser['SetWaveLength'] if laser['SetWaveLength'] != -1 else input_wl(),
                   laser['Kp'], laser['Ki'], laser['Kd']))

    return index, ret


def stop_mode(arg):
    if arg == 'all' or not arg:
        index = list(range(len(lasers)))
    else:
        index = [int(arg)]
    for i in index:
        lasers[i]['Locked'] = False
    return index, [()] * len(index)


def list_status():
    pass


def backend(q):
    def pid_lock():
        while True:
            if not len(pcs):
                time.sleep(.05)
            for pc in pcs:
                pc.loop()
            if not q.empty():
                return 

    pcs = {}
    while True:
        if not q.empty():
            cmd, args = q.get()
            print(cmd, args)
            laser_no = args[0]
            if cmd == 'lock':
                if laser_no in pcs:
                    pcs[laser_no].cleanup()
                pcs[laser_no] = PIDController(*args[1:])
            elif cmd == 'stop':
                print('hhelo')
                if laser_no in pcs:
                    pcs[laser_no].cleanup()
                    del pcs[laser_no]
            else:
                for pc in pcs:
                    pc.cleanup()
                return 
        pid_lock()


if __name__ == '__main__':
    freeze_support()

    _, lasers = load_settings()

    cmd_queue = Queue()
    background = Process(target=backend, args=(cmd_queue,))
    background.start()

    cmd2func = dict(zip(['lock', 'stop', 'list', 'exit', 'help'], [
                    lock_mode, stop_mode, list_status, stop_mode, None]))

    while True:
        cmds = input('Please input command:').strip().lower().split()
        if not cmds:
            continue

        cmd, arg = cmds[0], cmds[1:]
        if cmd == 'help':
            print(__doc__)
            continue
        if cmd in cmd2func.keys():
            for i, arg in zip(*cmd2func[cmd](arg)):
                cmd_queue.put((cmd, (i, *arg)))
            if cmd == 'exit':
                break
        elif not cmd:
            continue
        else:
            print('Invalid command.')
            print('Valid commands are:%s' %
                  (', '.join(cmd2func.keys())), end='.\n')

    background.join()  # wait for the clean-up process
