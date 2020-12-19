from flask import Flask, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_admin import Admin
from flask_admin.contrib.sqla import ModelView
from flask_cors import CORS, cross_origin


from datetime import datetime


app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///database.db"
app.config["SECRET_KEY"] = "ioF45sdfFef84egfgew84aSgGDAGge84DGQEWgGd"

cors = CORS(app)
app.config["CORS_HEADERS"] = "Content-Type"

db = SQLAlchemy(app)

tags = db.Table(
    "tags",
    db.Column("clanek_id", db.Integer, db.ForeignKey("clanek.id")),
    db.Column("stitek_id", db.Integer, db.ForeignKey("stitek.id")),
)


class Clanek(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    titulek = db.Column(db.String(1000), unique=False, nullable=False)
    podnadpis = db.Column(db.Text, unique=True, nullable=False)
    body = db.Column(db.Text, unique=True, nullable=False)
    main_image = db.Column(db.String(9999), nullable=False)

    datum = db.Column(db.DateTime, default=datetime.utcnow)

    autor = db.Column(db.Integer, db.ForeignKey("autor.id"))
    stitky = db.relationship(
        "Stitek",
        secondary=tags,
        backref=db.backref("stitky", lazy="dynamic"),
    )

    def __repr__(self):
        return "<Clanek %r>" % self.titulek

    def jsonify(self):
        stitky = [x.nazev for x in list(self.stitky)]
        return {
            "titulek": self.titulek,
            "podnadpis": self.podnadpis,
            "body": self.body,
            "obrazek": self.main_image,
            "datum": self.datum.strftime("%d. %m. %Y"),
            "autor": self.author.jmeno,
            "stitky": stitky,
        }

    def jsonify_main(self):
        return {
            "id": self.id,
            "titulek": self.titulek,
            "obrazek": self.main_image,
            "datum": self.datum.strftime("%d. %m. %Y"),
            "autor": self.author.jmeno,
            "stitek": self.stitky[0].nazev,
        }


class Rychlovka(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    titulek = db.Column(db.String(200), unique=False, nullable=False)
    body = db.Column(db.Text, unique=True, nullable=False)

    datum = db.Column(db.DateTime, default=datetime.utcnow)


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


# Admin views


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


@app.route("/main", methods=["GET"])
@cross_origin()
def main():
    clanky = Clanek.query.order_by(Clanek.datum.desc()).all()

    clanky_res = [x.jsonify_main() for x in clanky]

    return jsonify(clanky_res)


@app.route("/clanek/<int:clanek_id>", methods=["GET"])
@cross_origin()
def clanek(clanek_id):
    clanek = Clanek.query.filter_by(id=clanek_id).first()

    return jsonify(clanek.jsonify())


if __name__ == "__main__":
    app.run(port=8000)
    # app.run(threaded=True, port=int(os.environ.get("PORT", 5000))) # Heroku
