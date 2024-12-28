
import pandas as pd
from PyQt5 import QtWidgets
from pandasdb.util.viewutil import ViewUtil

class PandasTableWidget(QtWidgets.QTableWidget, ViewUtil):

	def __init__(self, data:list, col_types:dict=None, fix_header:bool=False):
		super().__init__()
		self.installEventFilter(self)
		if col_types is None:
			self.col_types = {}

		self.blockSignals(True)
		
		self.setRowCount(len(data))
		if len(data) > 0:
			self.setColumnCount(len(data[0]))

		for i, row in enumerate(data):
			for j, cell in enumerate(row):
				itm = QtWidgets.QTableWidgetItem(str(cell))
				self.setItem(i, j, itm)

		self.blockSignals(False)

		self.horizontalHeader().setSectionsMovable(not fix_header)

		self.installEventFilter(self)
		self.itemChanged.connect(self.handleChanged)
		return
	
	@classmethod
	def from_df(cls, df:pd.DataFrame, fix_header:bool=False, with_header:bool=True, with_row_num:bool=False):
		col_types = {}
		for i,j in zip(df.columns, df.dtypes):
			col_types[i] = j
		
		obj = cls(df.to_records(index=False).tolist(), col_types, fix_header)

		if with_header:
			for i, x in enumerate(df.columns.astype(str).tolist()):
				obj.setHorizontalHeaderItem(i, QtWidgets.QTableWidgetItem(x))
		for i, x in enumerate(df.index.astype(str).tolist()):
			obj.setVerticalHeaderItem(i, QtWidgets.QTableWidgetItem(x if with_row_num else ""))
		return obj
	
	def get_df(self, convert_datatype:bool=True)->pd.DataFrame:
		rows = self.rowCount()
		columns = self.columnCount()
		tbl = self.getData()

		col = [self.horizontalHeaderItem(x).text() for x in range(columns)]
		ind = [self.verticalHeaderItem(x).text() for x in range(rows)]
		df = pd.DataFrame(tbl, index=ind, columns=col)
		if convert_datatype:
			for key, value in self.col_types.items():
				df[key] = df[key].astype(value)
		return df

	def get_data(self)->list:
		rows = self.rowCount()
		columns = self.columnCount()

		tbl = []
		for i in range(rows):
			row = []
			for j in range(columns):
				cell = self.item(i, j).text()
				row.append(cell)
			tbl.append(row)
		return tbl
