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

import sip

import aqt.editor
from anki.hooks import addHook
from aqt.browser import Browser
from aqt.qt import *
from aqt.utils import tooltip

from .config import config


def hide_browser_editor(browser: Browser):
    if sip.isdeleted(browser) or not browser.editor:
        return
    browser.form.splitter.widget(1).setVisible(False)
    browser.editor.setNote(None)


def show_browser_editor(browser: Browser):
    if sip.isdeleted(browser) or not browser.editor or not browser.card:
        return
    browser.form.splitter.widget(1).setVisible(True)
    browser.editor.setNote(browser.card.note(reload=True))


def _on_edit_window(browser: Browser) -> bool:
    """Launch BrowserEditCurrent instance"""
    cids = browser.selectedCards()
    if not cids or not browser.card:
        tooltip("No cards selected")
        return False
    elif len(cids) > 1:
        tooltip("Please select just one card")
        return False

    hide_browser_editor(browser)

    browser.external_editor = aqt.dialogs.open(
        "BrowserEditCurrent", browser.mw, browser, browser.card
    )

    return True


def _on_setup_menus(browser):
    """Create menu entry and set attributes up"""
    menu = browser.form.menuEdit
    menu.addSeparator()
    a = menu.addAction("Edit in New Window")
    a.setShortcut(QKeySequence(config["local"]["hotkey"]))
    a.triggered.connect(lambda _, o=browser: _on_edit_window(o))
    browser.external_editor = None


def initialize_browser():
    try:  # >= 2.1.20
        from aqt.gui_hooks import browser_menus_did_init

        browser_menus_did_init.append(_on_setup_menus)
    except (ImportError, ModuleNotFoundError, AttributeError):
        addHook("browser.setupMenus", _on_setup_menus)
