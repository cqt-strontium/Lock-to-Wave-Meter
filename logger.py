import time 

class Logger():
    def __init__(self, data=None, fname=None):
        if not fname:
            fname = 'log@%s.txt'%time.strftime("%Y-%m-%d-%H%M%S", time.localtime())
        self.file = open(fname, 'w') 

        for line in data: 
            self.log(line)
    
    def log(self, line):
        self.file.write(', '.join(str(_) for _ in line))
        self.file.write('\n')
        self.file.flush()



