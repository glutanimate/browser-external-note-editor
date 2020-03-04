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

from PyQt5.QtWidgets import QDialog, QDialogButtonBox
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QKeySequence

import aqt.editor
from aqt.forms import editcurrent
from aqt.main import AnkiQt
from aqt.utils import saveGeom, restoreGeom
from anki.hooks import addHook, remHook

from anki.utils import isMac

from aqt.browser import Browser
from aqt.editcurrent import EditCurrent
from aqt import dialogs

try:
    from aqt import gui_hooks

    NEW_STYLE_HOOKS = True
except ImportError:
    NEW_STYLE_HOOKS = False


class BrowserEditCurrent(QDialog):
    """Based on editcurrent.EditCurrent"""

    def __init__(self, mw: AnkiQt, browser: Browser):
        super().__init__(None, Qt.Window)
        mw.setupDialogGC(self)
        self.mw = mw
        self.browser = browser
        self.form = aqt.forms.editcurrent.Ui_Dialog()
        self.form.setupUi(self)
        self.setWindowTitle(_("Edit Current"))
        self.setMinimumHeight(400)
        self.setMinimumWidth(250)
        self.form.buttonBox.button(QDialogButtonBox.Close).setShortcut(
            QKeySequence("Ctrl+Return")
        )
        self.editor = aqt.editor.Editor(self.mw, self.form.fieldsArea, self)
        self.editor.card = self.browser.card
        if self.browser.card is not None:
            self.editor.setNote(self.browser.card.note(), focusTo=0)
        restoreGeom(self, "browsereditcurrent")
        if NEW_STYLE_HOOKS:
            gui_hooks.state_did_reset.append(self.onReset)
        else:
            addHook("reset", self.onReset)
        self.mw.requireReset()
        self.show()
        # reset focus after open, taking care not to retain webview
        # pylint: disable=unnecessary-lambda
        self.mw.progress.timer(100, lambda: self.editor.web.setFocus(), False)

    def onReset(self):
        # lazy approach for now: throw away edits
        try:
            n = self.browser.card.note()
            n.load()
        except:
            # card's been deleted
            if NEW_STYLE_HOOKS:
                gui_hooks.state_did_reset.remove(self.onReset)
            else:
                remHook("reset", self.onReset)
            # remHook("remNotes", self.onRemoveNotes)
            self.editor.setNote(None)
            self.mw.reset()
            aqt.dialogs.markClosed("BrowserEditCurrent")
            self.close()
            return
        self.editor.setNote(n)

    def onSave(self):
        remHook("reset", self.onReset)
        self.editor.saveNow()
        self.browser.externalNid = None
        self.browser.form.splitter.widget(1).setVisible(True)
        self.browser.editor.setNote(self.browser.card.note(reload=True))
        saveGeom(self, "browsereditcurrent")
        aqt.dialogs.close("BrowserEditCurrent")

    def onRemoveNotes(self, ids):
        """Close window before shown note is deleted"""
        """Might not be necessary because it's handled by onReset"""
        # called via addHook("remNotes") or new-style hook
        # if my id in ids:
        # self.close

    def canClose(self):
        return True

    def reject(self):
        self.saveAndClose()

    def saveAndClose(self):
        self.editor.saveNow(self._saveAndClose)

    def _saveAndClose(self) -> None:
        if NEW_STYLE_HOOKS:
            gui_hooks.state_did_reset.remove(self.onReset)
        else:
            remHook("reset", self.onReset)

        saveGeom(self, "browsereditcurrent")
        aqt.dialogs.markClosed("BrowserEditCurrent")
        super().reject()

    def closeWithCallback(self, onsuccess):
        def callback():
            self._saveAndClose()
            onsuccess()

        self.editor.saveNow(callback)


def initialize_editor():
    # Register new dialog in DialogManager:
    dialogs._dialogs["BrowserEditCurrent"] = [BrowserEditCurrent, None]
