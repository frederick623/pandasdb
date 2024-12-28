
import datetime
import numpy as np
import os
import pandas as pd
import pymysql
import re
import sqlalchemy
import traceback

from sqlalchemy import create_engine
from sqlalchemy.ext.automap import automap_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.sql import text
from PyQt5 import QtSql

AUDIT_TBL = "audit_log"
AUDIT_DATA_LENGTH = 255

QTDRIVER_MAPPING = {
	"sqlite": "QSQLITE",
	"mysql": "QMYSQL",
	"postgresql": "QPSQL",
	"oracle": "QOCI",
	"mssql": "QODBC",
}

SADRIVER_MAPPING = {
	"mysql":"pymysql",
	"mssql":"pymssql",
}

class DbObj:
	def __init__(self):
		return

class Dbutil:
	_tablename = None

	def __init__(self, conn_string, tablename):
		self._engine = create_engine(conn_string, pool_recycle=3600, pool_pre_ping=True)
		self._base = automap_base()
		self._base.prepare(self._engine, reflect=True)
		self._session = sessionmaker(bind=self._engine)()
		self._tablename = tablename
		self._tbl = eval("self._base.classes.%s" % self._tablename)
		return 
		
	def to_df(self, where=None):
		query = self._session.query(self._tbl)
		if where is not None:
			query = query.from_statement(text("select * from %s where %s" % (self._tablename, where)))
		df = pd.read_sql(query.statement, query.session.bind)
		return df

	def upsert(self, df):
		tbl_df = df.copy()
		for col in tbl_df.select_dtypes(include=[np.datetime64]):
			tbl_df[col] = tbl_df[col].apply(lambda x: x.isoformat()).replace({'NaT': None})
		if "id" in tbl_df.columns:
			tbl_df["id"] = tbl_df["id"].fillna(0)
		dic_arr = tbl_df.to_dict("records")
		for dic in dic_arr:
			self._session.merge(self._tbl(**dic))
			
		try:
			self._session.commit()
		except:
			self._session.rollback()
			raise
		return

	@staticmethod
	def rename_cols(df, col_map=None):
		col_map = {} if col_map is None else col_map
		df.columns = [ col_map[col] if col in col_map else 
			re.sub('[/\.]', '_', re.sub('[\(\)]', '', col.lower().replace(' ','_'))) for col in df.columns]
		return df

	@staticmethod
	def update_df(a_df, b_df, index, how="outer"):
		a_df = a_df.set_index(index)
		b_df = b_df.set_index(index)
		a_df = a_df.merge(b_df[[]], how=how, left_index=True, right_index=True)
		a_df.update(b_df)
		a_df = a_df.reset_index()
		return a_df

def sqlcol(dfparam):    

	dtypedict = {}
	for i,j in zip(dfparam.columns, dfparam.dtypes):
		if "object" in str(j):
			dtypedict.update({i: sqlalchemy.types.NVARCHAR(length=255)})

		if "datetime" in str(j):
			dtypedict.update({i: sqlalchemy.types.DateTime()})

		if "float" in str(j):
			dtypedict.update({i: sqlalchemy.types.DECIMAL(32,16)})

		if "int" in str(j):
			dtypedict.update({i: sqlalchemy.types.INT()})

		if "bool" in str(j):
			dtypedict.update({i: sqlalchemy.types.BOOLEAN()})

	return dtypedict

def rename_cols(df, col_map=None):
	col_map = {} if col_map is None else col_map
	df.columns = [ col_map[col] if col in col_map else 
		re.sub('[/\.]', '_', re.sub('[\(\)]', '', col.lower().replace(' ','_'))) for col in df.columns]
	return df	

def tbl_import(conn_string, tbl, df, is_replace=True, mapping=None, with_id=True):
	
	if df.shape[0] == 0:
		if is_replace:
			raise("Empty dataframe with replace, possibly error.")
		else:
			return

	engine = sqlalchemy.create_engine(conn_string)
	conn = engine.connect()

	audit_df = pd.DataFrame({
		"update_datetime": [datetime.datetime.now()],
		"table": [tbl],
		"query": ["replace" if is_replace else "append"] ,
		"data": ["" if df.shape[0] == 0 else df.iloc[-1].to_json(orient="records")[:AUDIT_DATA_LENGTH]],
		"update_by":os.getlogin(),
		"process":str(traceback.extract_stack())[:AUDIT_DATA_LENGTH],
	})

	audit_df.to_sql(AUDIT_TBL, con=engine, if_exists="append", index=False)

	df = rename_cols(df, mapping)
	db_col_type = sqlcol(df)
	if is_replace:
		conn.execute(text("drop table if exists %s" % tbl))
	conn.execute(text(df_to_sql(df, tbl, with_id)))
	df.to_sql(tbl, con=engine, if_exists="append", index=False, dtype=db_col_type)

	conn.close()
	return

def df_to_sql(df:pd.DataFrame, table_name:str, with_id=True)->str:
	columns = []

	for col in df.columns:
		dtype = df[col].dtype.name
		
		if dtype == 'int64':
			sql_type = 'INTEGER'
		elif dtype == 'float64':
			sql_type = 'FLOAT'
		elif dtype == 'object':
			sql_type = f"VARCHAR(255)"
		elif dtype == 'bool':
			sql_type = 'BOOLEAN'
		elif dtype in ['datetime64', 'timedelta[ns]']:
			sql_type = 'DATETIME'
		else:
			sql_type = 'TEXT'
		
		# Add NOT NULL if no null values are present
		is_nullable = df[col].isnull().any()
		columns.append(f"{col} {sql_type}" + (" NULL" if is_nullable else " NOT NULL"))
	
	if with_id:
		column_definitions = " id INTEGER PRIMARY KEY AUTOINCREMENT, "
	else:
		column_definitions = ""
		
	column_definitions += ", ".join(columns)
		
	create_table_script = f"CREATE TABLE IF NOT EXISTS {table_name} ({column_definitions});"
	
	return create_table_script

def get_tbl(conn_string:str, tbl:str, cond=None, set_index_id=None):
	engine = sqlalchemy.create_engine(conn_string)

	query = "select * from %s where " % tbl
	if cond is None:
		query += "1"
	elif isinstance(cond, str):
		query += cond
	else:
		query += " and ".join([ ( " %s in (%s) " % (k, ",".join([ "'%s'"%x for x in v ])) \
			if isinstance(v, list) else ( " %s is null " % k if v is None else \
				" %s = '%s' " % (k,v)) ) for k,v in cond.items() ])
	df = pd.read_sql_query(query, con=engine)
	if set_index_id is None and "id" in df.columns:
		df = df.drop(columns=["id"])
	if set_index_id and "id" in df.columns:
		df = df.set_index("id")
	return df

def str_to_db(conn_str:str)->QtSql.QSqlDatabase:
	# Split the conn_str by '://' to get database type and rest of the URL
	driver, url = conn_str.split("://")
	db = QtSql.QSqlDatabase.addDatabase(QTDRIVER_MAPPING[driver])

	if os.path.exists(url.strip('/')):
		db.setDatabaseName(url.strip('/'))
		
	else:
		# Further split the URL by '@' to separate authentication details from host information
		auth_details, host_info = url.split("@")

		# Parse username and password from auth_details using ':' as a delimiter
		username, password = auth_details.split(":")

		# Split host_info by '/' to get host:port and dbname separately
		host_and_port, dbname = host_info.rsplit("/", 1)

		# Finally split host_and_port by ':' to get host and port
		host, port = host_and_port.split(":", 1)
			
		db.setDatabaseName(dbname)
		if host != "":
			db.setHostName(host)
		if port != 0:
			db.setPort(int(port))
		if username != "":
			db.setUserName(username)
		if password != "":
			db.setPassword(password)

	if db.open():
		print("Connected to the database successfully")
	else:
		print("Failed to connect to the database:", db.lastError().text())

	return db 

if __name__ == "__main__":
	conn_string = "sqlite:///mydatabase.db"
	tbl = "users"
	set_index_id = True
	result_df = pd.read_csv("users.csv")
	tbl_import(conn_string, tbl, result_df)
	
	pass
