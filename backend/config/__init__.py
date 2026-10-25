import pymysql

# Django 6 checks mysqlclient >= 2.2.1; PyMySQL reports an older MySQLdb version.
pymysql.version_info = (2, 2, 1, "final", 0)
pymysql.install_as_MySQLdb()
