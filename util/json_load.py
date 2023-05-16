import json 

def fill_missing_attr(laser_arr):
    attrs = ['ArduinoPin', 'WaveMeterChannel', 'SetWaveLength', 'Kp', 'Ki', 'Kd']
    default_value = dict(zip(attrs, [-1, -1, -1, 0, 0, 0]))
    for laser in laser_arr:
        for attr in attrs:
            if attr not in laser:
                laser[attr] = default_value[attr]


def print_status(lasers):
    print('%-5s %-4s %-15s %-8s %-9s %-8s %-8s %-8s' % ('Lck?', 'No.', 'Name', 'SS Pin', 'WLM Chan.', 'Kp', 'Ki', 'Kd'))

    for i, laser in enumerate(lasers): 
        print('%-5s %-4i %-15s %-8d %-9d %-8.1e %-8.1e %-8.1e' % ('' if 'Locked' not in laser or not laser['Locked'] else '*', i, laser['Name'][:15], laser['ArduinoPin'], laser['WaveMeterChannel'], laser['Kp'], laser['Ki'], laser['Kd']))
    return ()

def load_settings(suppress_output=False):
    settings = json.load(open('wlm.json'))
    if not suppress_output:
        print('Arduino is at port %s.' % settings['ArduinoPort'])
    lasers = settings['Lasers']
    fill_missing_attr(lasers)
    if not suppress_output:
        print('There are %d laser(s) to control:' % len(lasers))
        print_status(lasers)

    for laser in lasers: 
        if not 'ArduinoPort' in laser:
            laser['ArduinoPort'] = settings['ArduinoPort']
    return settings, lasers