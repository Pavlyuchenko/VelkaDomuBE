from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_admin import Admin
from flask_admin.contrib.sqla import ModelView

from datetime import datetime


app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///database.db"
app.config["SECRET_KEY"] = "ioF45sdfFef84egfgew84aSgGDAGge84DGQEWgGd"
db = SQLAlchemy(app)

tags = db.Table(
    "tags",
    db.Column("clanek_id", db.Integer, db.ForeignKey("clanek.id")),
    db.Column("stitek_id", db.Integer, db.ForeignKey("stitek.id")),
)


class Clanek(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    titulek = db.Column(db.String(1000), unique=False, nullable=False)
    body = db.Column(db.Text, unique=True, nullable=False)
    main_image = db.Column(db.String(9999), nullable=False)

    datum = db.Column(db.DateTime, default=datetime.utcnow)

    autor = db.Column(db.Integer, db.ForeignKey("autor.id"))
    stitky = db.relationship(
        "Stitek", secondary=tags, backref=db.backref("stitky", lazy="dynamic")
    )

    def __repr__(self):
        return "<Clanek %r>" % self.titulek


class Autor(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    jmeno = db.Column(db.String(1000), unique=False, nullable=False)

    clanek = db.relationship("Clanek", backref="author")

    def __repr__(self):
        return self.jmeno


class Stitek(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    nazev = db.Column(db.String(100), unique=True, nullable=False)
    rubrika = db.Column(db.Boolean, default=False)
    color = db.Column(db.String(10), nullable=False)

    clanky = db.Column(db.Integer, db.ForeignKey("clanek.id"))

    def __repr__(self):
        return self.nazev


class Rychlovka(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    titulek = db.Column(db.String(200), unique=False, nullable=False)
    body = db.Column(db.Text, unique=True, nullable=False)


class NewClanekView(ModelView):
    # edit_template = "test.html"

    column_exclude_list = ["main_image"]
    column_searchable_list = ["titulek"]
    column_filters = ["datum"]
    column_editable_list = ["titulek"]
    can_export = True


admin = Admin(app, name="FotbalPropal.cz", base_template="admin/base.html")

admin.add_view(NewClanekView(Clanek, db.session))
admin.add_view(ModelView(Rychlovka, db.session))
admin.add_view(ModelView(Autor, db.session))
admin.add_view(ModelView(Stitek, db.session))


@app.route('/')
def main():
    return "Hello!"

if __name__ == "__main__":
    app.run(threaded=True, port = int(os.environ.get('PORT', 5000)))