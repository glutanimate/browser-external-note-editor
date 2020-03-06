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

def on_row_changed(browser, *args, **kwargs):
    """Disable inbuilt editor for externally edited note"""
    # keep *args, **kwargs for < 2.1.20 compat
    nids = browser.selectedNotes()
    if nids and nids[0] == browser.externalNid:
        browser.form.splitter.widget(1).setVisible(False)
        browser.editor.setNote(None)

def on_edit_window(browser):
    """Launch BrowserEditCurrent instance"""
    nids = browser.selectedNotes()
    if len(nids) != 1:
        return
    browser.form.splitter.widget(1).setVisible(False)
    browser.editor.setNote(None)
    browser.externalNid = nids[0]
    browser.editCurrent = aqt.dialogs.open("BrowserEditCurrent", browser.mw, browser)

def on_setup_menus(browser):
    """Create menu entry and set attributes up"""
    menu = browser.form.menuEdit
    menu.addSeparator()
    a = menu.addAction('Edit in New Window')
    a.setShortcut(QKeySequence("Ctrl+Alt+E"))
    a.triggered.connect(lambda _, o=browser: on_edit_window(o))
    browser.externalNid = None
    browser.editCurrent = None


def initialize_browser():
    try:  # >= 2.1.20
        from aqt.gui_hooks import browser_did_change_row, browser_menus_did_init
        browser_did_change_row.append(on_row_changed)
        browser_menus_did_init.append(on_setup_menus)
    
    except (ImportError, ModuleNotFoundError, AttributeError):
        addHook("browser.setupMenus", on_setup_menus)
        Browser.onRowChanged = wrap(Browser.onRowChanged, on_row_changed, "after")
        # Browser.deleteNotes = wrap(Browser.deleteNotes, onDeleteNotes, "before")
