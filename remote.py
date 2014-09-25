__author__ = 'christian'
from pynetworktables import *
import time
import threading
import json
import copy
from tkinter import *
from tkinter import ttk

NetworkTable.SetIPAddress("10.1.0.2")
NetworkTable.SetClientMode()
NetworkTable.Initialize()

table = NetworkTable.GetTable("SmartDashboard")


root = Tk()
root.title("Framework Remote")
root.resizable(width=0, height=0)
mainframe = ttk.Frame(root, padding="20 20 20 20")
mainframe.grid(column=0, row=0, sticky=(N, W, E, S))
mainframe.columnconfigure(0, weight=1)
mainframe.rowconfigure(0, weight=1)

modlist = list()
currentmod = dict()
commands = dict()
commandindex = 1

modframe = ttk.Frame(mainframe, relief=RAISED, padding="20 20 20 20")
modframe.grid(column=2, row=0, sticky=(N, W, E, S))
modframe.columnconfigure(0, weight=1)
modframe.rowconfigure(0, weight=1)
die = False


class TreeList():

    seltrig = False
    callback = lambda x: True

    def __init__(self, frame, column1key, columns=None):
        if columns is not None:
            self.widget = ttk.Treeview(frame, columns=columns.keys)
        else:
            self.widget = ttk.Treeview(frame)
            columns = dict()

        self.column1key = column1key
        self.srclist = dict()
        self.listedsrclist = dict()
        self.ids = dict()
        self.columns = columns

    def update(self):
        for item in self.listedsrclist:
            if item not in self.srclist:
                self.widget.delete(self.ids[item])
        for item in self.srclist:
            if item not in self.listedsrclist:
                self.ids[item] = self.widget.insert("", END, text=self.srclist[item][self.column1key], tags=(item, "module"))
                self.widget.tag_bind(item, sequence="<1>", callback=self.callback)
            values = list()
            for column in self.columns:
                values.append(self.srclist[item][self.columns[column]])
            self.widget.item(self.ids[item], values=values)
        self.listedsrclist = copy.copy(self.srclist)

    def onSelect(self, callback):
        for item in self.listedsrclist:
            self.widget.tag_bind(item, sequence="<1>", callback=callback)
        self.seltrig = True
        self.callback = callback

    def __getattr__(self, item):
        return getattr(self.widget, item)


def on_select(e):
    threading.Thread(target=mod_selected).start()


modlist_widget = TreeList(mainframe, "filename")
modlist_widget.grid(column=0, row=0, sticky=(N, S))
modlist_widget.heading("#0", text="Modules")
modlist_widget.column("#0", width=300)
modlist_widget.onSelect(on_select)

proclist_widget = TreeList(modframe, "name", columns={"Time Running": "timerunning"})

proclist_widget.grid(column=0, row=0, sticky=W)
proclist_widget.heading("#0", text="Process")
proclist_widget.column("#0", width=75)
proclist_widget.heading("#1", text="Age")
proclist_widget.column("#1", width=50)


def reload_mod():
    global commandindex
    commandindex += 1
    commands[commandindex] = {"command": "reload module", "target": currentmod["name"]}

def unload_mod():
    global commandindex
    commandindex += 1
    commands[commandindex] = {"command": "unload module", "target": currentmod["name"]}

buttongrid = ttk.Frame(modframe, padding="10 10 10 10")
buttongrid.grid(column=1, row=0, sticky=(N, S, E, W))

reload_button = ttk.Button(buttongrid, text="Reload Module", command=reload_mod)
reload_button.grid(column=0, row=0, sticky=N)

unload_button = ttk.Button(buttongrid, text="Unload Module", command=unload_mod)
unload_button.grid(column=0, row=1, sticky=N)

loadgrid = ttk.Frame(mainframe, padding="10 10 10 10")
loadgrid.grid(column=0, row=1, sticky=(N, S, E, W))

modname = StringVar()
modtoload = ttk.Entry(loadgrid, textvariable=modname)
modtoload.grid(column=0, row=0, sticky=(N, S, E, W))


def load_module():
    global commandindex
    commandindex += 1
    commands[commandindex] = {"command": "load module", "target": modname.get()}


loadmod_button = ttk.Button(loadgrid, text="Load Module", command=load_module)
loadmod_button.grid(column=1, row=0, sticky=(N, S, E))

def mod_selected():
    time.sleep(.01)
    global currentmod
    for mod in modsummaries:
        focus = modlist_widget.focus()
        modid = modlist_widget.ids[mod["name"]]
        if modid == focus:
            currentmod = mod
    proclist_widget.srclist = currentmod["runningTasks"]
    proclist_widget.update()


def run():
    global modlist
    while not die:
        try:
            global modsummaries, currentmod
            modsummariesstring = table.GetString('modulesummary')
            modsummaries = json.loads(modsummariesstring)
            modlist = dict()
            for mod in modsummaries:
                modlist[mod["name"]] = mod
                if "name" not in currentmod:
                    currentmod = mod
                if currentmod["name"] == mod["name"]:
                    currentmod = mod

            for mod in modsummaries:
                for proc in mod["runningTasks"]:
                    mod["runningTasks"][proc]["timerunning"] = "{:.2}".format(time.clock() - mod["runningTasks"][proc]["starttime"])

            modlist_widget.srclist = modlist
            modlist_widget.update()
            proclist_widget.srclist = currentmod["runningTasks"]
            proclist_widget.update()
            #Handle commands
            if len(commands) > 4:
                keys = [item for item in commands.keys()]
                for key in keys:
                    if key < commandindex - 4:
                        del(commands[key])

            table.PutString('frameworkcommands', json.dumps(commands))

        except TableKeyNotDefinedException as e:
            print(e)
            time.sleep(2)
        time.sleep(.1)

threading.Thread(target=run).start()
root.mainloop()
die = True
