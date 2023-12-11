from brad.extensions import db

class User(db.Model):
    username = db.Column(db.String, primary_key=True)
    password = db.Column(db.String)
    auth = db.Column(db.String)

class Animation(db.Model):
    id = db.Column(db.String, primary_key=True)
    owner = db.Column(db.String)
    name = db.Column(db.String)