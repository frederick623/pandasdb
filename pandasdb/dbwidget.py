
from PyQt5 import QtCore, QtGui, QtWidgets, QtSql, sip
from pandasdb.util.dbutil import str_to_db
from pandasdb.util.viewutil import ViewUtil

MYSQL_ODBC_CONNSTR = "" 

class DBModel(QtSql.QSqlTableModel):
	
	def __init__(self, connection_string, tbl, is_select=True) -> None:
		
		super().__init__(db=str_to_db(connection_string))
		self.setTable(tbl)
		self.setEditStrategy(self.OnManualSubmit)
		self.primeInsert.connect(self.insertHandling)
		if is_select:
			self.select()

		self.hdr_arr = [ self.headerData(i, QtCore.Qt.Horizontal, QtCore.Qt.DisplayRole) \
			for i in range(self.columnCount())]
		return
	
	def insertHandling(self, row: int, record) -> None:
		for i in range(record.count()):
			if record.field(i).isNull() and \
				(record.field(i).type()==QtCore.QMetaType.Int or \
				record.field(i).type()==QtCore.QMetaType.Float or \
				record.field(i).type()==QtCore.QMetaType.Double):
				record.setValue(i,'')
		return 

	def setData(self, index: QtCore.QModelIndex, value, role: int = ...) -> bool:
		if value == '':
			value = None
		return super().setData(index, value, role=role)

	def data(self, idx: QtCore.QModelIndex, role: int = ...):
		if (role == QtCore.Qt.ForegroundRole and self.isDirty(idx)):
			return QtGui.QColor(255,0,0)
		is_enabled = sip.enableautoconversion(QtCore.QVariant, False)
		value = super().data(idx, role=role)
		sip.enableautoconversion(QtCore.QVariant, is_enabled)
		
		return value.value()

	def get_idx_data(self, idx, header):
		return self.data(self.index(idx.row(), self.hdr_arr.index(header)), QtCore.Qt.EditRole)

class DBDelegate(QtWidgets.QStyledItemDelegate):
	def __init__(self, parent=None) -> None:
		super().__init__(parent=parent)

	def createEditor(self, parent : QtWidgets.QWidget, option, index: QtCore.QModelIndex) :
		val = index.data()
		if isinstance(val, float) or isinstance(val, int):
			widget = QtWidgets.QLineEdit(parent=parent)
			return widget
		return super().createEditor(parent, option, index)
	
class DBView(ViewUtil):
	def __init__(self, parent=None) -> None:
		super().__init__(parent=parent)
		self.setSortingEnabled(True)
		return

	def setModel(self, model: QtCore.QAbstractItemModel) -> None:
		super().setModel(model)
		for col in range(model.columnCount()):
			if model.headerData(col, QtCore.Qt.Horizontal, QtCore.Qt.DisplayRole) == "id":
				self.setColumnHidden(col, True)
				break
		return

class BaseWidget(QtWidgets.QWidget):
	submit_signal = QtCore.pyqtSignal()
	
	def __init__(self, parent=None) -> None:
		super().__init__(parent)
		return

	def submit_action(self):
		self.submit_signal.emit()
		return

	def search_action(self):

		return

	def reload_action(self):

		return

class DBWidget(BaseWidget):
	def __init__(self, connection_string, tbl, parent=None, preload=False, view_only=False) -> None:
		super().__init__(parent)
		self.model = DBModel(connection_string, tbl)
		self.view = DBView()
		self.view.setItemDelegate(DBDelegate())
		self.view.setModel(self.model)
		
		self.searchbox = QtWidgets.QLineEdit("")
		self.searchbox.returnPressed.connect(self.search_action)
		add_btn = QtWidgets.QPushButton("+")
		add_btn.clicked.connect(self.add_action)
		remove_btn = QtWidgets.QPushButton("-")
		remove_btn.clicked.connect(self.remove_action)
		submit_btn = QtWidgets.QPushButton("Submit")
		submit_btn.clicked.connect(self.submit_action)
		revert_btn = QtWidgets.QPushButton("Revert")
		revert_btn.clicked.connect(self.revert_action)
		reload_btn = QtWidgets.QPushButton("Refresh")
		reload_btn.clicked.connect(self.reload_action)
		btn_panel_layout = QtWidgets.QHBoxLayout()
		btn_panel_layout.addWidget(add_btn)
		btn_panel_layout.addWidget(remove_btn)
		btn_panel_layout.addWidget(submit_btn)
		btn_panel_layout.addWidget(revert_btn)
		btn_panel_layout.addWidget(reload_btn)
		self.btn_panel = QtWidgets.QWidget()
		self.btn_panel.setLayout(btn_panel_layout)

		if view_only:
			add_btn.setEnabled(False)
			remove_btn.setEnabled(False)
			submit_btn.setEnabled(False)
			revert_btn.setEnabled(False)

		layout = QtWidgets.QVBoxLayout()
		layout.addWidget(self.searchbox)
		layout.addWidget(self.view)
		layout.addWidget(self.btn_panel)
		self.setLayout(layout)

		if preload:
			self.search_action()
		return

	def add_action(self):
		self.model.insertRow(self.view.currentIndex().row()+1)
		return

	def remove_action(self):
		self.model.removeRow(self.view.currentIndex().row())
		return

	def submit_action(self):
		self.model.submitAll()
		super().submit_action()
		return

	def revert_action(self):
		self.model.revertAll()
		return

	def search_action(self):
		val = self.searchbox.text()
		self.model.setFilter(val)
		self.model.select()
		return

	def reload_action(self):
		self.searchbox.clear()
		self.search_action()
		return

