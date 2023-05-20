import os.path
import sys
__doc__ = """
Easy interface for controller. 
Valid commands: 
1. LOCK <LASER_NO.>/[ALL] : set wavelength & PID gain and lock for laser <LASER_NO.>; default locks all lasers
2. STOP <LASER_NO.>/[ALL] : pause lock for laser <LASER_NO.>; default stops all laser locks
3. LIST : list laser lock status
4. CALI <LASER_NO.>[0] : calibrate wavelength -- current response for laser <LASER_NO.> at set current; default calibrate the first laser
5. EXIT : exit program
6. HELP : reveal this message
"""

from typing import Dict
from queue import Queue
from controller.pid_controller import PIDController
from util.json_load import load_settings, print_status
import asyncio


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


def get_index(arg):
    if not arg or arg[0] == 'all':
        return list(range(len(lasers)))
    else:
        return [int(_) for _ in arg]


def lock_mode(arg):
    index = get_index(arg)
    ret = []
    for i in index:
        laser = lasers[i]
        if laser['WaveMeterChannel'] == -1:
            print('Warning: No WaveMeterChannel specified, cannot lock laser %s.' % (
                laser['Name']))
        laser['Locked'] = True
        ret.append((laser['WaveMeterChannel'], laser['ArduinoPort'], laser['ArduinoPin'],
                   laser['SetWaveLength'] if laser['SetWaveLength'] != -
                    1 else input_wl(),
                   laser['Kp'], laser['Ki'], laser['Kd']))

    return index, ret


def stop_mode(arg):
    index = get_index(arg)

    for i in index:
        lasers[i]['Locked'] = False
    return index, [()] * len(index)


def cali_mode(arg):
    no = 0 if not arg else int(arg[0])
    laser = lasers[no]
    return [no], [(laser['WaveMeterChannel'], laser['ArduinoPort'], laser['ArduinoPin'])]


async def backend(q):
    async def pid_lock():
        while True:
            for pc in pcs.values():
                pc.loop()
            if not q.empty():
                return
            await asyncio.sleep(0)

    pcs: Dict[int, PIDController] = {}
    while True:
        if not q.empty():
            cmd, args = q.get()
            laser_no = args[0]
            if cmd == 'lock':
                if laser_no in pcs:
                    pcs[laser_no].cleanup()
                pcs[laser_no] = PIDController(*args[1:])
            elif cmd == 'stop':
                if laser_no in pcs:
                    pcs[laser_no].cleanup()
                    del pcs[laser_no]
            elif cmd == 'cali':
                PIDController(*args[1:]).calibrate().cleanup()
            else:
                for pc in pcs.values():
                    pc.cleanup()
                return
        await pid_lock()


def show_help(arg):
    print(__doc__)
    return ()


async def main():
    cmd2func = dict(zip(['lock', 'stop', 'list', 'cali', 'exit', 'help'], [
                    lock_mode, stop_mode, print_status, cali_mode, stop_mode, show_help]))

    cmd_queue = Queue()
    task = asyncio.create_task(backend(cmd_queue))

    while True:
        raw = await asyncio.get_event_loop().run_in_executor(None, input, 'Please input command:')
        cmds = raw.strip().lower().split()
        if not cmds:
            continue

        cmd, arg = cmds[0], cmds[1:]
        if cmd == 'list':
            arg = lasers
        if cmd in cmd2func.keys():
            for i, arg in zip(*cmd2func[cmd](arg)):
                cmd_queue.put((cmd, (i, *arg)))
            if cmd == 'exit':
                break
        else:
            print('Invalid command.')
            print('Valid commands are:%s' %
                  (', '.join(cmd2func.keys())), end='.\n')
    task.cancel()


setting_fname = None
if len(sys.argv) == 2:
    setting_fname = sys.argv[1]
    if not os.path.exists(setting_fname):
        raise FileNotFoundError(
            f"Cannot find settings file at {setting_fname}!")
elif len(sys.argv) > 2:
    raise RuntimeError(
        "Too many input arguments; only one is allowed for settings file name!")
_, lasers = load_settings(fname=setting_fname)
asyncio.run(main())
