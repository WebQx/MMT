try:
	import pymysql  # type: ignore
	pymysql.install_as_MySQLdb()
	print("[medtranscribe_backend.__init__] PyMySQL shim installed as MySQLdb")
except Exception as _e:  # noqa: E722
	print(f"[medtranscribe_backend.__init__] PyMySQL shim failed: {_e}")
