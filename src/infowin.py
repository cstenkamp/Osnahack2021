import tkinter
from multiprocessing import Process, Queue
from threading import Thread
import threading
import time
import random
import string
from functools import wraps
import argparse
import logging



def parse_command_line_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('--log', dest='loglevel',
                        help='log-level for logging-module. one of [DEBUG, INFO, WARNING, ERROR, CRITICAL]',
                        default='WARNING')
    parser.add_argument('--logfile', dest='logfile',
                        help='logfile to log to. If not set, it will be logged to standard stdout/stderr', default='')
    return parser.parse_args()


def setup_logging(loglevel='WARNING', logfile=None):
    numeric_level = getattr(logging, loglevel.upper(), None)
    if not isinstance(numeric_level, int):
        raise ValueError('Invalid log level: %s' % loglevel)
    kwargs = {'level': numeric_level, 'format': '%(asctime)s %(levelname)-8s %(message)s',
              'datefmt': '%Y-%m-%d %H:%M:%S', 'filemode': 'w'}
    if logfile:
        kwargs['filename'] = logfile
    logging.basicConfig(**kwargs)


def random_string(length=8):
    letters = string.ascii_lowercase
    return ''.join(random.choice(letters) for i in range(length))

########################################################################################################################


def main():
    try:
        with InfowinManager() as iwm:
            moneywin = iwm.new_window('moneywin', (500, 100))
            qwin = iwm.quick_display((100, 100), 5, "argh!", fontsize=14)
            qwin2 = iwm.quick_display((100, 300), 2, "arg2h!", fontsize=14)
            qwin3 = iwm.quick_display((300, 300), 99, "I stay until killed!", fontsize=14)
            moneywin.display('helloooo')
            print('All windows created, sleeping for 2.')
            time.sleep(2)
            iwm[qwin].comqueue.put("2 seconds passed! 3 left!")
            moneywin.display('kthxbyeee', 2)
            time.sleep(3)
            moneywin.display('back agaiiin for 2')
            time.sleep(2)
            moneywin.clear()
            time.sleep(2)
            moneywin.display('back agaiiin AGAIN')
            time.sleep(2)
        print("now it should kill them")
        time.sleep(5)
        print("main ends.")
    except KeyboardInterrupt:
        print("interrupted")


def interrupt_ok(fn):
    @wraps(fn)
    def wrapped(*args, **kwargs):
        try:
            return fn(*args, **kwargs)
        except KeyboardInterrupt:
            pass
    return wrapped


########################################################################################################################
########################################################################################################################


class InfowinManager():
    def __init__(self):
        self.active_windows = {}
        self.stopme = False
        self.manager_thread = Thread(target=self.manager_func)
        self.manager_thread.name = 'InfoWinManagerProcess'
        self.manager_thread.setDaemon(True)
        self.manager_thread.start()

    # __getitem__ = lambda self, key: self.active_windows[key]
    def __getitem__(self, key):
        return self.active_windows[key]
    __contains__ = lambda self, key: self.active_windows.__contains__(key)
    def __setitem__(self, key, val):
        self.active_windows[key] = val

    @interrupt_ok
    def manager_func(self):
        while not self.stopme:
            time.sleep(0.05)
            for win in list(self.active_windows.values()):
                if not win.cmdqueue.empty():
                    cmd = win.cmdqueue.get()
                    if cmd in ['delete', 'harddelete']:
                        win.label_active = False
                        if not win.stay_active or cmd == 'harddelete':
                            del self.active_windows[win.name]
                            logging.debug(f"Window {win.name} ended.")
                            continue
                        else:
                            logging.debug(f"Window {win.name} ended for now.")
                    else:
                        win.cmdqueue.put(cmd)
                        time.sleep(random.random() / 5)  # preventing deadlocks...
        for win in list(self.active_windows.keys()):
            logging.debug(f"Window {win} ended.")

    def new_window(self, name, position, **kwargs):
        self[name] = Infowin(self, name, position, **kwargs)
        self[name].stay_active = True
        return self[name]

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        for win in self.active_windows.values():
            logging.debug(f"killing {win.name} bc main ends")
            win.cmdqueue.put('kill')
        self.stopme = True

    def quick_display(self, position, show_for, text, **kwargs):
        while (name := random_string()) in self: pass
        win = Infowin(self, name, position)
        self[name] = win
        win.init_label(show_for, text, **kwargs)
        return name



########################################################################################################################


class Infowin():
    def __init__(self, managerparent, name, position, **kwargs):
        self.managerparent = managerparent
        self.name = name
        self.position = position
        self.comqueue = Queue()
        self.cmdqueue = Queue()
        self.label_active = False
        self.stay_active = False #für die die mit quick_display angezeigt werden bleibts false, für permanente wirds true. das entshceidet ob der manager es killt.
        self.kwargs = kwargs

    def init_label(self, *args, **kwargs):
        self.label_active = True
        self.process = Process(target=self._init_label, args=args, kwargs=kwargs)
        self.process.name = self.name
        self.process.start()


    @interrupt_ok
    def _init_label(self, show_for, text, fontsize=14, position=None):  # will run in a seperate PROCESS (thread doesnt work!!)
        show_for = show_for or 99**99
        self.master = tkinter.Tk()
        # master.bind("<Escape>", lambda e: e.widget.quit())
        self.label = tkinter.Label(self.master, text=text, font=('Times', str(fontsize)), fg='white', bg='black', justify=tkinter.LEFT)
        self.label.master.overrideredirect(True)  # seems to make it rahmenlos
        if position:
            self.position = position
        self.label.master.geometry(f"+{self.position[0]}+{self.position[1]}")
        self.label.master.wm_attributes("-topmost", True)  # stayontop
        # w.master.wm_attributes("-disabled", True) #not movable etc
        # w.master.wm_attributes("-transparentcolor", "black") #transparent solange rahmenlos
        self.label.pack()
        # self.master.mainloop()
        starttime = time.perf_counter()
        cmd = None
        while time.perf_counter()-starttime < show_for: #https://stackoverflow.com/q/29158220/5122790
            time.sleep(0.05)
            self.master.update_idletasks()
            self.master.update()
            if not self.comqueue.empty():
                self.label.config(text=self.comqueue.get())
                self.label.pack()
            if not self.cmdqueue.empty():
                cmd = self.cmdqueue.get()
                if cmd in ['exit', 'kill']:
                    self.label_active = False
                    break
                elif cmd == 'tick':
                    self.cmdqueue.put('tock')
                elif cmd.startswith('run_for'):
                    starttime = time.perf_counter()
                    show_for = int(cmd[7:])
                elif cmd.startswith('set_pos'):
                    self.position = [int(i) for i in cmd[7:].split(",")]
                    self.label.master.geometry(f"+{self.position[0]}+{self.position[1]}")
                    self.label.pack()
                else:
                    self.cmdqueue.put(cmd)
                    time.sleep(random.random() / 5)  # preventing deadlocks...
        self.label.quit()
        self.label.destroy()
        self.master.destroy()
        # print(f"deleting myself: {self.name}")
        if cmd == 'kill':
            self.cmdqueue.put('harddelete')
        else:
            self.cmdqueue.put('delete')# del self.managerparent[self.name] doesn't work! works on a copy of that instance (separet process!)


    def display(self, text, show_for=0, **kwargs):
        logging.debug(f"display called. ({self.name})")
        self.cmdqueue.put(f'run_for{show_for or 99**99}')
        if not self.label_active:
            self.init_label(show_for, text, **{**self.kwargs, **kwargs})
        else:
            self.comqueue.put(text)
        if 'position' in kwargs:
            self.cmdqueue.put(f'set_pos{",".join([str(i) for i in kwargs["position"]])}')

    def clear(self):
        self.cmdqueue.put('exit')

########################################################################################################################


if __name__ == '__main__':
    args = parse_command_line_args()
    setup_logging(args.loglevel, args.logfile)
    main()
