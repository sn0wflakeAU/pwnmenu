from multiprocessing.connection import Listener
from multiprocessing.connection import Client
import pwnagotchi
import pwnagotchi.ui.fonts as fonts
from pwnagotchi.ui.components import *
from pwnagotchi.ui.view import BLACK
from pwnagotchi.ui.view import WHITE
from pwnagotchi.ui import view
import pwnagotchi.plugins as plugins
import os
import logging
import time
import threading

menulabels = []
menucommands = []
menuitemcount = 0

with open('/home/pi/pwnmenu.txt', 'r') as pwnmenutxt:
    lines = pwnmenutxt.readlines()
    for l in lines:
        linelist = l.split(";")
        menulabels.append(linelist[0])
        menucommands.append(linelist[1].replace("\n",""))
        menuitemcount += 1

class PwnMenu(plugins.Plugin):
    __author__ = 'https://gitlab.com/sn0wflake'
    __version__ = '1.0.0'
    __license__ = 'MIT'
    __description__ = 'A simple popup menu to run scripts from'

    def __init__(self):
        self.menuvisible = False
        self.menuitem = 0
        self.menuitemcount = 0
        self.menuitemoffset = 0
        self.ui = False
        self.uihardware = ''
        self.labelcount = 0
        self.updatelabels = False
        self.redrawmenu = False
        self.movecursor = False
        self.running = True
        self.addelements = False
        self.removeelements = False
        self.menuiconvisible = False
        self.timeouthandler = False
        # These defaults are set for the waveshare v2 display
        self.rectfill = [115, 16, 249, 106]
        self.rectline = [114, 15, 250, 107]
        self.pos1 = (118, 18)
        self.pos2 = (118, 30)
        self.pos3 = (118, 42)
        self.pos4 = (118, 54)
        self.pos5 = (118, 66)
        self.pos6 = (118, 78)
        self.pos7 = (118, 90)
        self.posup = (238, 14)
        self.posdown = (238, 94)
        self.poscursor = (118, 17)
        self.posmenuicon = (215, 109)
        self.showuparrow = False
        self.uparrowvisible = False # Use these because remove_element() locks up.
        self.showdownarrow = False
        self.downarrowvisible = False # Use these because remove_elements() locks up.

    def forcedisplayupdate(self):
        self.timeouthandler = False
        if view.ROOT:
            self.redrawmenu = False
            view.ROOT.update(force=True)

    def on_loaded(self):
        logging.info("Pwnmenu Plugin loaded.")
        redrawMenuNow = False
        redrawMenuDelayed = False
        self.timeouthandler = False
        address = ('localhost', 6789)
        listener = Listener(address)
        runcommand = False
        while self.running:
            #time.sleep(10)
            if redrawMenuNow:
                redrawMenuNow = False
                if self.timeouthandler:
                    self.timeouthandler.cancel()
                    self.timeouthandler = False
                self.forcedisplayupdate()
            elif redrawMenuDelayed:
                # This block has been commented out since repeatedly calling .cancel seems to make this lock up.
                #if self.timeouthandler:
                #    self.timeouthandler.cancel()
                #    self.timeouthandler = False
                if not self.timeouthandler:
                    self.timeouthandler = threading.Timer(2.0, self.forcedisplayupdate)
                    self.timeouthandler.start()

            if runcommand:
                logging.info("Pwnmenu running command: %s" % runcommand)
                os.system(runcommand)

            conn = listener.accept()
            msg = conn.recv()
            conn.close()
            movecursor = False
            runcommand = False

            if msg == 'down':
                if self.menuitem == 0:
                    self.menuitem = 1
                    movecursor = True
                    self.addelements = True
                elif self.menuitem == menuitemcount - 1:
                    self.menuitem = 1
                    self.updatelabels = True
                    self.menuitemoffset = 0
                    movecursor = True
                elif self.menuitem < (menuitemcount - 1):
                    self.menuitem += 1
                    movecursor = True

                    if self.menuitem > self.labelcount and (self.menuitem % self.labelcount) == 1:
                        self.menuitemoffset = (self.menuitem // self.labelcount) * 7
                        self.updatelabels = True

            elif msg == 'up':
                if self.menuitem == 0:
                    self.menuitem = 1
                    movecursor = True
                    self.addelements = True
                elif self.menuitem == 1:
                    self.menuitem = menuitemcount - 1
                    self.updatelabels = True
                    movecursor = True
                elif self.menuitem > 1:
                    self.menuitem -= 1
                    movecursor = True

                if self.menuitem == (menuitemcount - 1) or (self.menuitem % self.labelcount) == 0:
                    self.updatelabels = True
                    if self.menuitem <= self.labelcount:
                        self.menuitemoffset = 0
                    elif (self.menuitem % self.labelcount) == 0:
                        self.menuitemoffset = ((self.menuitem // self.labelcount) - 1) * 7
                    else:
                        self.menuitemoffset = (self.menuitem // self.labelcount) * 7

            elif msg == 'ok':
                if self.menuitem == 0:
                    self.menuitem = 1
                    movecursor = True
                    self.addelements = True
                elif self.menuitem:
                    if self.timeouthandler:
                        self.timeouthandler.cancel()
                    runcommand = menucommands[self.menuitem]
                    self.menuitem = 0 # Close menu

            elif msg == 'back':
                if self.menuitem != 0:
                    self.menuitem = 0
                runcommand = menucommands[0]
                self.menuitem = 0 # Close menu

            elif msg == 'close':
                if self.menuitem != 0:
                    self.menuitem = 0

            elif msg == 'stop':
                self.menuitem = 0
                self.running = False

            # Add/remove the up/down arrows
            menumod = menuitemcount % self.labelcount
            self.showuparrow = self.menuitem > self.labelcount
            self.showdownarrow = (menuitemcount - self.menuitem) > (menuitemcount % self.labelcount)

            # Hide menu if set to do so
            if self.menuitem == 0:
                self.removeelements = True
                redrawMenuNow = True

            # Recalculate cursor position
            if movecursor and not self.removeelements:
                menuitem = self.menuitem
                while menuitem > 7:
                    menuitem -= 7 # Wrap around for next page
                y = 5 + (menuitem * 12)
                self.poscursor = (118, y)
                self.movecursor = True
                redrawMenuDelayed = True

            if self.addelements and not self.removeelements:
                self.addelements = False
                self.menuvisible = True
                self.movecursor = False # Moved here anyway, no need to do it again.
                self.updatelabels = True
                if self.uihardware == 'waveshare_v3':
                    if view.ROOT:
                        view.ROOT.add_element('menubg', FilledRect(self.rectfill, color=WHITE))
                        view.ROOT.add_element('menuborder', Rect(self.rectfill, color=BLACK))
                        view.ROOT.add_element('menuitem1', LabeledValue(color=BLACK, label='', value='Menu item 1',
                                    position=self.pos1, label_font=fonts.Medium, text_font=fonts.Medium))
                        view.ROOT.add_element('menuitem2', LabeledValue(color=BLACK, label='', value='Menu item 2',
                                    position=self.pos2, label_font=fonts.Medium, text_font=fonts.Medium))
                        view.ROOT.add_element('menuitem3', LabeledValue(color=BLACK, label='', value='Menu item 3',
                                    position=self.pos3, label_font=fonts.Medium, text_font=fonts.Medium))
                        view.ROOT.add_element('menuitem4', LabeledValue(color=BLACK, label='', value='Menu item 4',
                                    position=self.pos4, label_font=fonts.Medium, text_font=fonts.Medium))
                        view.ROOT.add_element('menuitem5', LabeledValue(color=BLACK, label='', value='Menu item 5',
                                    position=self.pos5, label_font=fonts.Medium, text_font=fonts.Medium))
                        view.ROOT.add_element('menuitem6', LabeledValue(color=BLACK, label='', value='Menu item 6',
                                    position=self.pos6, label_font=fonts.Medium, text_font=fonts.Medium))
                        view.ROOT.add_element('menuitem7', LabeledValue(color=BLACK, label='', value='Menu item 7',
                                    position=self.pos7, label_font=fonts.Medium, text_font=fonts.Medium))
                        view.ROOT.add_element('menucursor', Text(color=BLACK, value='▶',
                                    position=self.poscursor, font=fonts.Medium))

            if self.removeelements and self.menuvisible:
                self.removeelements = False
                self.menuvisible = False
                self.menuitem = 0
                if self.uihardware == 'waveshare_v3':
                    if view.ROOT:
                        view.ROOT.remove_element('menubg')
                        view.ROOT.remove_element('menuborder')
                        view.ROOT.remove_element('menuitem1')
                        view.ROOT.remove_element('menuitem2')
                        view.ROOT.remove_element('menuitem3')
                        view.ROOT.remove_element('menuitem4')
                        view.ROOT.remove_element('menuitem5')
                        view.ROOT.remove_element('menuitem6')
                        view.ROOT.remove_element('menuitem7')
                        view.ROOT.remove_element('menucursor')
                        if self.uparrowvisible:
                            self.uparrowvisible = False
                            view.ROOT.remove_element('menuup')
                        if self.downarrowvisible:
                            self.downarrowvisible = False
                            view.ROOT.remove_element('menudown')
            if self.movecursor and self.menuvisible:
                self.movecursor = False
                if self.uihardware == 'waveshare_v3':
                    if view.ROOT:
                        view.ROOT.remove_element('menucursor')
                        view.ROOT.add_element('menucursor', Text(color=BLACK, value='▶',
                                    position=self.poscursor, font=fonts.Medium))

            if self.showuparrow and self.menuvisible and not self.uparrowvisible:
                self.uparrowvisible = True
                view.ROOT.add_element('menuup', LabeledValue(color=BLACK, label='', value='▲',
                            position=self.posup, label_font=fonts.Medium, text_font=fonts.Medium))
            elif not self.showuparrow and self.uparrowvisible:
                self.uparrowvisible = False
                view.ROOT.remove_element('menuup')

            if self.showdownarrow and self.menuvisible and not self.downarrowvisible:
                self.downarrowvisible = True
                view.ROOT.add_element('menudown', LabeledValue(color=BLACK, label='', value='▼',
                            position=self.posdown, label_font=fonts.Medium, text_font=fonts.Medium))
            elif not self.showdownarrow and self.downarrowvisible:
                self.downarrowvisible = False
                view.ROOT.remove_element('menudown')

        # Exited the main loop. Run cleanup functions here.
        address.close()

    def on_ui_setup(self, ui):
        self.ui = ui
        if ui.is_waveshare_v3():
            self.uihardware = 'waveshare_v3'
            self.labelcount = 7
        ui.add_element('menuicon', Text(color=BLACK, value='=', position=self.posmenuicon, font=fonts.Medium))
        self.menuiconvisible = True
        self.updatelabels = True

    def on_unload(self, ui):
        logging.info("Pwnmenu plugin unloaded.")
        if self.menuiconvisible:
            self.menuiconvisible = False
            ui.remove_element('menuicon')
        if self.running:
            self.running = False
            address = ('localhost', 6789)
            if address:
                conn = Client(address)
                conn.send('stop')
                conn.close()
        if self.uihardware == 'waveshare_v3':
            # Check if element actually added below before removing.
            if self.menuvisible and not self.addelements:
                self.menuvisible = False
                ui.remove_element('menubg')
                ui.remove_element('menuborder')
                ui.remove_element('menuitem1')
                ui.remove_element('menuitem2')
                ui.remove_element('menuitem3')
                ui.remove_element('menuitem4')
                ui.remove_element('menuitem5')
                ui.remove_element('menuitem6')
                ui.remove_element('menuitem7')
                ui.remove_element('menucursor')
                if self.uparrowvisible:
                    ui.remove_element('menuup')
                if self.downarrowvisible:
                    ui.remove_element('menudown')

    def on_ui_update(self, ui):
        if self.menuvisible:
            if self.updatelabels:
                self.updatelabels = False
                if self.uihardware == 'waveshare_v3':
                    menuoffset = self.menuitemoffset
                    menuitem_text1 = menulabels[menuoffset + 1] if menuoffset + 1 < menuitemcount else ' '
                    menuitem_text2 = menulabels[menuoffset + 2] if menuoffset + 2 < menuitemcount else ' '
                    menuitem_text3 = menulabels[menuoffset + 3] if menuoffset + 3 < menuitemcount else ' '
                    menuitem_text4 = menulabels[menuoffset + 4] if menuoffset + 4 < menuitemcount else ' '
                    menuitem_text5 = menulabels[menuoffset + 5] if menuoffset + 5 < menuitemcount else ' '
                    menuitem_text6 = menulabels[menuoffset + 6] if menuoffset + 6 < menuitemcount else ' '
                    menuitem_text7 = menulabels[menuoffset + 7] if menuoffset + 7 < menuitemcount else ' '
                    ui.set('menuitem1', menuitem_text1)
                    ui.set('menuitem2', menuitem_text2)
                    ui.set('menuitem3', menuitem_text3)
                    ui.set('menuitem4', menuitem_text4)
                    ui.set('menuitem5', menuitem_text5)
                    ui.set('menuitem6', menuitem_text6)
                    ui.set('menuitem7', menuitem_text7)

