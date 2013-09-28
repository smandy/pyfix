


from bsddb3 import db

f = tempfile.mktemp()

d = db.DB()
d.open( f, db.DB_BTREE, db.DB_CREATE, 0666)
seq = db.DBSequence( d )
