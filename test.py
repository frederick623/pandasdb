
import pandasdb

import pandas as pd
from PyQt5 import QtWidgets

def main():
	app = QtWidgets.QApplication([])
	widget = pandasdb.DBWidget("sqlite://mydatabase.db", "users" )
	widget.show()
	app.exec()
	return

if __name__ == '__main__':
	main()
