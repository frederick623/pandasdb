
import pandasdb.util.dbutil as dbutil
import pandas as pd

from pandas.api.types import is_datetime64_any_dtype 
from PyQt5 import QtCore, QtGui, QtWidgets
from typing import NamedTuple

TBL_ID_COL = "id"

class Linkage(NamedTuple):
	tbl_name: str
	tbl_id_col: str
	tbl_foreign_key: str
	tbl_name_col: str
	is_editable: bool


class DBTableModel(QtCore.QAbstractTableModel):
	def __init__(self, conn_string, tbl, link_tbls=None):
		super().__init__()
		self.header = []
		self.rows = []

		self.conn_string = conn_string
		self.link_tbls = [] if link_tbls is None else link_tbls
		self.tbl = tbl
		self.map_dfs = {}
		self.col_types = None
		return

	def loadDb(self):
		df = dbutil.get_tbl(self.conn_string, self.tbl, False)
		self.col_types = { i:j for i, j in zip(df.columns, df.dtypes)}
		
		for map_tuple in self.link_tbls:
			map_df = dbutil.get_tbl(map_tuple.tbl_name, False)
			map_df = map_df.rename(columns={map_tuple.tbl_id_col: map_tuple.tbl_foreign_key})
			for k, v in zip(map_df.columns, map_df.dtypes):
				if is_datetime64_any_dtype(v):
					map_df[k] = pd.to_datetime(map_df[k], utc=True)
				elif "object" in str(v).lower():
					map_df[k] = map_df[k].fillna("")
				elif "int" in str(v).lower() or "decimal" in str(v).lower():
					map_df[k] = map_df[k].fillna(0)
			if TBL_ID_COL in map_df.columns:
				map_df = map_df.drop(columns=[TBL_ID_COL])
			df = df.merge(map_df, on=map_tuple.tbl_foreign_key, how="left")
			self.map_dfs[map_tuple] = map_df

		df = df[np.setdiff1d(df.columns, self.display_cols).tolist()+self.display_cols]
		if len(self.display_cols) > 0:
			df = df.sort_values(self.display_cols)
		
		for k, v  in self.col_types.items():
			if is_datetime64_any_dtype(v):
				df[k] = pd.to_datetime(df[k], utc=True)
			elif "object" in str(v).lower():
				df[k] = df[k].fillna("")
			elif "int" in str(v).lower() or "decimal" in str(v).lower():
				df[k] = df[k].fillna(0)
		
		self.id_col = df.columns.tolist().index(TBL_ID_COL)
		self.table_widget.setDf(df)
		self.table_widget.setHorizontalHeaderLabels(
			[ '_'.join([ ele[0].upper() + ele[1:] for ele in col.split('_')]) 
				for col in df.columns ])
		self.db_df = df

		self.table_widget.blockSignals(True)

		if self.table_widget.rowCount() > 0:
			for row in range(self.table_widget.rowCount()):
				itm = self.table_widget.item(row, self.id_col)
				itm.setFlags(QtCore.Qt.ItemIsSelectable | QtCore.Qt.ItemIsEnabled)
			self.cur_id = int(itm.text()) + 1
		else:
			self.cur_id = 1
		self.convert_dropdown()

		for map_tuple in self.link_tbls:
			col = map_tuple.tbl_foreign_key
			self.table_widget.setColumnHidden(df.columns.tolist().index(col), True)
		for idx, col in enumerate(df.columns):
			if col not in self.display_cols:
				self.table_widget.setColumnHidden(idx, True)
			if "_name" in col:
				self.table_widget.resizeColumnToContents(idx)
		if TBL_ID_COL in df.columns:
			self.table_widget.setColumnHidden(self.id_col, True)

		self.table_widget.blockSignals(False)
		return

	def setDf(self, df):
		self.header = df.columns
		self.rows = df.to_records(index=False).tolist()
		return

	def rowCount(self, parent):
		return len(self.rows)

	def columnCount(self, parent):
		return len(self.header)

	def data(self, index, role):
		if role != QtCore.Qt.DisplayRole:
			return QtCore.QVariant()
		return self.rows[index.row()][index.column()]

	def headerData(self, section, orientation, role):
		if role != QtCore.Qt.DisplayRole or orientation != QtCore.Qt.Horizontal:
			return QtCore.QVariant()
		return self.header[section]
		
	def load_action(self):
		df = dbutil.get_tbl(self.tbl, False)
		self.col_types = { i:j for i, j in zip(df.columns, df.dtypes)}
		
		for map_tuple in self.link_tbls:
			map_df = dbutil.get_tbl(map_tuple.tbl_name, False)
			map_df = map_df.rename(columns={map_tuple.tbl_id_col: map_tuple.tbl_foreign_key})
			for k, v in zip(map_df.columns, map_df.dtypes):
				if is_datetime64_any_dtype(v):
					map_df[k] = pd.to_datetime(map_df[k], utc=True)
				elif "object" in str(v).lower():
					map_df[k] = map_df[k].fillna("")
				elif "int" in str(v).lower() or "decimal" in str(v).lower():
					map_df[k] = map_df[k].fillna(0)
			if TBL_ID_COL in map_df.columns:
				map_df = map_df.drop(columns=[TBL_ID_COL])
			df = df.merge(map_df, on=map_tuple.tbl_foreign_key, how="left")
			self.map_dfs[map_tuple] = map_df

		df = df[np.setdiff1d(df.columns, self.display_cols).tolist()+self.display_cols]
		if len(self.display_cols) > 0:
			df = df.sort_values(self.display_cols)
		
		for k, v  in self.col_types.items():
			if is_datetime64_any_dtype(v):
				df[k] = pd.to_datetime(df[k], utc=True)
			elif "object" in str(v).lower():
				df[k] = df[k].fillna("")
			elif "int" in str(v).lower() or "decimal" in str(v).lower():
				df[k] = df[k].fillna(0)
		
		self.id_col = df.columns.tolist().index(TBL_ID_COL)
		self.table_widget.setDf(df)
		self.table_widget.setHorizontalHeaderLabels(
			[ '_'.join([ ele[0].upper() + ele[1:] for ele in col.split('_')]) 
				for col in df.columns ])
		self.db_df = df

		self.table_widget.blockSignals(True)

		if self.table_widget.rowCount() > 0:
			for row in range(self.table_widget.rowCount()):
				itm = self.table_widget.item(row, self.id_col)
				itm.setFlags(QtCore.Qt.ItemIsSelectable | QtCore.Qt.ItemIsEnabled)
			self.cur_id = int(itm.text()) + 1
		else:
			self.cur_id = 1
		self.convert_dropdown()

		for map_tuple in self.link_tbls:
			col = map_tuple.tbl_foreign_key
			self.table_widget.setColumnHidden(df.columns.tolist().index(col), True)
		for idx, col in enumerate(df.columns):
			if col not in self.display_cols:
				self.table_widget.setColumnHidden(idx, True)
			if "_name" in col:
				self.table_widget.resizeColumnToContents(idx)
		if TBL_ID_COL in df.columns:
			self.table_widget.setColumnHidden(self.id_col, True)

		self.table_widget.blockSignals(False)
		return