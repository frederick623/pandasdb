
import csv
import io
from PyQt5 import QtCore, QtGui, QtWidgets

class ViewUtil(QtWidgets.QTableView):
	def __init__(self, *args, **kwargs):
		super().__init__()
		self.installEventFilter(self)
		self.col_types = {}
		return
	
	def handleChanged(self, item):
		item.setData( QtCore.Qt.ForegroundRole, QtGui.QColor(255,0,0))
		return
		
	def eventFilter(self, source, event):
		if (event.type() == QtCore.QEvent.KeyPress and
			event.matches(QtGui.QKeySequence.Copy)):
			self.copySelection()
			return True
		if (event.type() == QtCore.QEvent.KeyPress and
			event.matches(QtGui.QKeySequence.Paste)):
			self.pasteSelection()
			return True
		return super(QtWidgets.QTableView, self).eventFilter(source, event)

	def copySelection(self):
		selection = self.selectedIndexes()
		if selection:
			rows = sorted(index.row() for index in selection)
			columns = sorted(index.column() for index in selection)
			rowcount = rows[-1] - rows[0] + 1
			colcount = columns[-1] - columns[0] + 1
			table = [[''] * colcount for _ in range(rowcount)]
			for index in selection:
				row = index.row() - rows[0]
				column = index.column() - columns[0]
				table[row][column] = index.data()
			stream = io.StringIO()
			csv.writer(stream, delimiter='\t').writerows(table)
			QtWidgets.qApp.clipboard().setText(stream.getvalue())
		return

	def pasteSelection(self):
		selection = self.selectedIndexes()
		if selection:
			model = self.model()

			buffer = QtWidgets.qApp.clipboard().text() 
			rows = sorted(index.row() for index in selection)
			columns = sorted(index.column() for index in selection)
			reader = csv.reader(io.StringIO(buffer), delimiter='\t')
			if len(rows) == 1 and len(columns) == 1:
				for i, line in enumerate(reader):
					for j, cell in enumerate(line):
						model.setData(model.index(rows[0]+i,columns[0]+j), cell)
			else:
				arr = [ [ cell for cell in row ] for row in reader]
				for index in selection:
					row = index.row() - rows[0]
					column = index.column() - columns[0]
					model.setData(model.index(index.row(), index.column()), arr[row][column])
		return
