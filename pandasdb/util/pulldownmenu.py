
from PyQt5 import QtCore, QtGui, QtWidgets

class PulldownMenu(QtWidgets.QComboBox):
	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)
		self.setFocusPolicy(QtCore.Qt.StrongFocus)
		return

	def wheelEvent(self, event):
		if self.hasFocus():
			return QtWidgets.QComboBox.wheelEvent(self, event)
		else:
			return event.ignore()
		