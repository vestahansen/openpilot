from openpilot.common.params import Params
from openpilot.selfdrive.ui.qt.api import HttpRequest
from openpilot.selfdrive.ui.qt.widgets.controls import ButtonControl, ToggleControl
from openpilot.selfdrive.ui.qt.widgets.input import InputDialog, ConfirmationDialog


class SshToggle(ToggleControl):
    def __init__(self, parent):
        self.params = Params()
        super().__init__("Enable SSH", "", "", self.params.get_bool("SshEnabled"), parent=parent)
        self.toggleFlipped.connect(self.onToggleFlipped)

    def onToggleFlipped(self, state):
        self.params.put_bool("SshEnabled", state)


class SshControl(ButtonControl):
    def __init__(self, parent):
        super().__init__("SSH Keys", "", ("Warning: This grants SSH access to all public keys in your GitHub settings. "
                                          "Never enter a GitHub username other than your own. A comma employee will NEVER "
                                          "ask you to add their GitHub username."), parent=parent)

        self.params = Params()
        self.clicked.connect(self.onClicked)

        self.refresh()

    def refresh(self):
        param = self.params.get("GithubSshKeys")
        if param:
            username = self.params.get("GithubUsername", encoding='utf-8')
            self.setValue(username)
            self.setText("REMOVE")
        else:
            self.setValue("")
            self.setText("ADD")
        self.setEnabled(True)

    def onClicked(self):
        if self.text() == "ADD":
            username = InputDialog.getText("Enter your GitHub username", self)
            if username:
                self.setText("LOADING")
                self.setEnabled(False)
                self.getUserKeys(username)
        else:
            self.params.remove("GithubUsername")
            self.params.remove("GithubSshKeys")
            self.refresh()

    def getUserKeys(self, username):
        request = HttpRequest(self)
        request.requestDone.connect(lambda resp, success: self.onRequestDone(resp, success, username, request))
        request.sendRequest(f"https://github.com/{username}.keys")

    def onRequestDone(self, resp, success, username, request):
        if success:
            if resp:
                self.params.put("GithubUsername", username)
                self.params.put("GithubSshKeys", resp)
            else:
                ConfirmationDialog.alert(f"Username '{username}' has no keys on GitHub", self)
        else:
            if request.isTimedOut():
                ConfirmationDialog.alert("Request timed out", self)
            else:
                ConfirmationDialog.alert(f"Username '{username}' doesn't exist on GitHub", self)
        self.refresh()
        request.deleteLater()
