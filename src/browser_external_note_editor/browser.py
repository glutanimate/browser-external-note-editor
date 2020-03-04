# -*- coding: utf-8 -*-

# External Note Editor for the Browser Add-on for Anki
#
# Copyright (C) 2017-2020  Aristotelis P. <https://glutanimate.com/>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version, with the additions
# listed at the end of the license file that accompanied this program.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.
#
# NOTE: This program is subject to certain additional terms pursuant to
# Section 7 of the GNU Affero General Public License.  You should have
# received a copy of these additional terms immediately following the
# terms and conditions of the GNU Affero General Public License that
# accompanied this program.
#
# If not, please request a copy through one of the means of contact
# listed here: <https://glutanimate.com/contact/>.
#
# Any modifications to this file must keep this entire header intact.

from aqt.qt import *
import aqt.editor
from aqt.utils import saveGeom, restoreGeom
from anki.hooks import addHook, remHook, wrap
from anki.utils import isMac

from aqt.browser import Browser
from aqt import dialogs

def onRowChanged(self, current, previous):
    """Disable inbuilt editor for externally edited note"""
    nids = self.selectedNotes()
    if nids and nids[0] == self.externalNid:
        self.form.splitter.widget(1).setVisible(False)
        self.editor.setNote(None)

def onEditWindow(self):
    """Launch BrowserEditCurrent instance"""
    nids = self.selectedNotes()
    if len(nids) != 1:
        return
    self.form.splitter.widget(1).setVisible(False)
    self.editor.setNote(None)
    self.externalNid = nids[0]
    self.editCurrent = aqt.dialogs.open("BrowserEditCurrent", self.mw, self)

def onSetupMenus(self):
    """Create menu entry and set attributes up"""
    menu = self.form.menuEdit
    menu.addSeparator()
    a = menu.addAction('Edit in New Window')
    a.setShortcut(QKeySequence("Ctrl+Alt+E"))
    a.triggered.connect(lambda _, o=self: onEditWindow(o))
    self.externalNid = None
    self.editCurrent = None


def initializeBrowser():
    # Hook into menu setup
    addHook("browser.setupMenus", onSetupMenus)
    
    # Modify existing methods
    Browser.onRowChanged = wrap(Browser.onRowChanged, onRowChanged, "after")
    # ↑ use hook here, requires Anki >2.1.5
    #Browser.deleteNotes = wrap(Browser.deleteNotes, onDeleteNotes, "before")