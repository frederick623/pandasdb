
from PyQt5 import QtCore, QtGui, QtWidgets

class InsValidator(QtGui.QValidator):
	def __init__(self, parent, ins_list):
		super().__init__(parent)
		self.ins_list = ins_list
		return
	
	def validate(self, inp, pos):
		return (QtGui.QValidator.Acceptable if inp in self.ins_list else QtGui.QValidator.Intermediate, inp, pos)

class Searchbox(QtWidgets.QLineEdit):
	def __init__(self, *args, **kwargs):
		super(Searchbox, self).__init__(*args, **kwargs)

		self.model = QtCore.QStringListModel()
		completer = QtWidgets.QCompleter()
		completer.setModel(self.model)
		completer.setCaseSensitivity(QtCore.Qt.CaseInsensitive)

		self.setCompleter(completer)
		return
	
	def init_search(self, arr):
		self.model.setStringList(sorted(arr))
		ivalidator = InsValidator(self, arr)
		self.setValidator(ivalidator)
		return