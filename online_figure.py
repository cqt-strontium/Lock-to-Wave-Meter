import matplotlib.pyplot as plt
from collections.abc import Iterable


class OnlineFigure():
    def __init__(self, x=None, y=None):
        def construct_lst(arr):
            if isinstance(arr, Iterable):
                ret = [_ for _ in arr]
            elif isinstance(arr, (float, int)):
                ret = [arr]
            elif isinstance(arr, type(None)):
                ret = []
            else:
                raise Exception('Unidentified data type')
            return ret

        self.x = construct_lst(x)
        self.y = construct_lst(y)
        if len(self.x) != len(self.y):
            raise Exception('Unequal length in x and y arrays')

        self.fig, self.ax = plt.subplots()
        self.line,  = self.ax.plot(self.x, self.y, '-')

    def display(self):
        self.line.set_data(self.x, self.y)
        plt.pause(1e-9)

    def append(self, new_x, new_y):
        self.x.append(new_x)
        self.y.append(new_y)

        _, xmax = self.ax.get_xlim()
        if new_x > xmax:
            xmax = 1.1 * new_x
            self.ax.set_xlim(right=xmax)

        ymin, ymax = self.ax.get_ylim()
        if new_y > ymax:
            if new_y > 0:
                ymax = 1.1 * new_y
            else:
                ymax = .9 * new_y
            self.ax.set_ylim(ymin, ymax)
        if new_y < ymin:
            if new_y < 0:
                ymin = 1.1 * new_y
            else:
                ymin = .9 * new_y
            self.ax.set_ylim(ymin, ymax)

        self.display()


if __name__ == '__main__':
    of = OnlineFigure()
    from random import random
    from time import perf_counter, sleep
    for i in range(1000):
        of.append(perf_counter(), random()*2-1)
        sleep(.2)
