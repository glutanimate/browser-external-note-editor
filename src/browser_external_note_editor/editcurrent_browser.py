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

from typing import List

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QKeySequence
from PyQt5.QtWidgets import QDialog, QDialogButtonBox

import aqt
from anki.cards import Card
from anki.hooks import addHook, remHook
from anki.lang import _
from anki.storage import _Collection
from aqt.browser import Browser
from aqt.main import AnkiQt
from aqt.utils import restoreGeom, saveGeom, tooltip

from .browser import hide_browser_editor, show_browser_editor


class BrowserEditCurrent(QDialog):
    """Based on editcurrent.EditCurrent"""

    def __init__(self, mw: AnkiQt, browser: Browser, card: Card):
        super().__init__(None, Qt.Window)
        mw.setupDialogGC(self)
        self.mw = mw
        self.browser = browser
        self.card = card
        self.form = aqt.forms.editcurrent.Ui_Dialog()
        self.form.setupUi(self)
        self.setWindowTitle(_("Edit Current"))
        self.setMinimumHeight(400)
        self.setMinimumWidth(250)
        self.form.buttonBox.button(QDialogButtonBox.Close).setShortcut(
            QKeySequence("Ctrl+Return")
        )
        self.editor = aqt.editor.Editor(self.mw, self.form.fieldsArea, self)
        self.editor.card = card
        self.editor.setNote(card.note(), focusTo=0)
        restoreGeom(self, "browsereditcurrent")
        self.mw.requireReset()
        self._setupHooks()
        self.show()
        # reset focus after open, taking care not to retain webview
        # pylint: disable=unnecessary-lambda
        self.mw.progress.timer(100, lambda: self.editor.web.setFocus(), False)

    # Qt API

    def reject(self):
        self.saveAndClose()

    # Setup

    ## Hooks

    def _setupHooks(self):
        # TODO: close on browser close?
        try:
            from aqt.gui_hooks import state_did_reset, browser_did_change_row
            from anki.hooks import notes_will_be_deleted

            state_did_reset.append(self._onReset)
            notes_will_be_deleted.append(self._onNotesWillBeDeleted)
            browser_did_change_row.append(self._onBrowserRowChanged)
        except (ImportError, ModuleNotFoundError, AttributeError):
            addHook("reset", self._onReset)
            addHook("remNotes", self._onNotesWillBeDeleted)
            addHook("browser.rowChanged", self._onBrowserRowChanged)  # requires >=2.1.5

    def _teardownHooks(self):
        try:
            from aqt.gui_hooks import state_did_reset, browser_did_change_row
            from anki.hooks import notes_will_be_deleted

            state_did_reset.remove(self._onReset)
            notes_will_be_deleted.remove(self._onNotesWillBeDeleted)
            browser_did_change_row.remove(self._onBrowserRowChanged)
        except (ImportError, ModuleNotFoundError, AttributeError):
            remHook("reset", self._onReset)
            remHook("remNotes", self._onNotesWillBeDeleted)
            remHook("browser.rowChanged", self._onBrowserRowChanged)  # requires >=2.1.5

    ## Hook subscribers

    def _onBrowserRowChanged(self, _: Browser):
        if not self.editor.note:
            return
        selected_nids = self.browser.selectedNotes()
        if selected_nids and selected_nids[0] == self.editor.note.id:
            hide_browser_editor(self.browser)

    def _onNotesWillBeDeleted(self, col: _Collection, nids: List[int]):
        if not self.editor.note:
            return
        current_nid = self.editor.note.id
        if current_nid in nids:
            self.saveAndClose()

    def _onReset(self):
        # lazy approach for now: throw away edits
        try:
            n = self.card.note()
            n.load()
        except Exception as e:  # noqa: E722
            print(e)
            # card's been deleted
            self._teardownHooks()
            # remHook("remNotes", self.onRemoveNotes)
            self.editor.setNote(None)
            self.mw.reset()
            aqt.dialogs.markClosed("BrowserEditCurrent")
            self.close()
            return
        self.editor.setNote(n)

    def saveAndClose(self):
        self.editor.saveNow(self._saveAndClose)

    def _saveAndClose(self) -> None:
        self._teardownHooks()
        if self.browser:
            show_browser_editor(self.browser)
            self.browser.edit_current = None
        saveGeom(self, "browsereditcurrent")
        aqt.dialogs.markClosed("BrowserEditCurrent")
        super().reject()

    # DialogManager API

    def reopen(self, mw: AnkiQt, browser: Browser, card: Card):
        self.editor.saveNow(lambda: self._reopen(mw, browser, card))

    def _reopen(self, mw: AnkiQt, browser: Browser, card: Card):
        self.mw = mw
        self.browser = browser
        self.card = card
        self.editor.card = card
        self.editor.setNote(card.note(), focusTo=0)
        self._onReset()

    def closeWithCallback(self, onsuccess):
        def callback():
            self._saveAndClose()
            onsuccess()

        self.editor.saveNow(callback)


def initialize_editcurrent_browser():
    # Register new dialog in DialogManager:
    try:  # >= 2.1.22
        aqt.dialogs.register_dialog("BrowserEditCurrent", BrowserEditCurrent, None)
    except AttributeError:
        aqt.dialogs._dialogs["BrowserEditCurrent"] = [BrowserEditCurrent, None]
