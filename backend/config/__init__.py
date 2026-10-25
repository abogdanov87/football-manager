import os

import pymysql

# Django 6 checks mysqlclient >= 2.2.1; PyMySQL reports an older MySQLdb version.
pymysql.version_info = (2, 2, 1, "final", 0)
pymysql.install_as_MySQLdb()

if os.environ.get("HOSTING_LEGACY_MYSQL") == "1":
    from django.db.backends.base.base import BaseDatabaseWrapper

    def _skip_db_version_check(self) -> None:
        return None

    BaseDatabaseWrapper.check_database_version_supported = _skip_db_version_check
