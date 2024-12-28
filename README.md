# Integration of PyQt and Pandas for Data Visualization in Excel Spreadsheet style

A collection of PyQt5 table widget and view with data model which is used to visualize Pandas dataframe or database data

## Widgets

* PandasTableWidget: A subclass of QTableWidget that can be used to display a pandas DataFrame.
* dbwidget: A full-fludged GUI that can be used to display and save data from any QtSQL-compatible database (MySQL/PostgreSQL/Sqlite/MSSQL/Oracle).

## Connection String

The connection string is used to connect to a database. The format of the connection string depends on the type of database being used. For example:
* MySQL: `mysql://username:password@host/dbname`
* PostgreSQL: `postgresql://username:password@host/dbname`
* SQLite: `sqlite:///path/to/database.db`
* MSSQL: `mssql://username:password@host/dbname`
* Oracle: `oracle://username:password@host/dbname`

## Helper functions

* dbtablemodel.py: Defines the a PyQt model capable of interacting with pandas DataFrames or SQLAlchemy ORM objects. This is useful if you wish to deine your own view.
* dbutils.py: Contains helper functions for interacting with databases, such as connecting to a database, executing queries, and fetching results.
* pulldownmenu.py: Overloads existing QComboBox with wheel up/down to select different elements.
* searchbox.py: A textbox which can be used to perform a search on the table widget. To use, one has to initialize the content by init_search() method.
* viewutil.py : Contains helper functions for creating views, such as data changes highlight, copy and paste grid data.

## Installation

To install this package, you can use pip: