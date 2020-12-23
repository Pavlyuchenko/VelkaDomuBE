from flask import Flask, jsonify, request
from flask_sqlalchemy import SQLAlchemy
from flask_admin import Admin
from flask_admin.contrib.sqla import ModelView
from flask_cors import CORS, cross_origin


from datetime import datetime
import json


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

    datum = db.Column(db.DateTime, default=datetime.now)

    autor = db.Column(db.Integer, db.ForeignKey("autor.id"))
    stitky = db.relationship(
        "Stitek",
        secondary=tags,
        backref=db.backref("stitky", lazy="dynamic"),
    )
    dalsi_stitky = db.Column(db.Text, unique=False, nullable=True)

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


class Draft(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    titulek = db.Column(db.Text)
    podnadpis = db.Column(db.Text)
    url_obrazku = db.Column(db.Text)
    blocks = db.Column(db.Text)
    zadost_o_potvrzeni = db.Column(db.Boolean, default=False)
    vydan = db.Column(db.Boolean, default=False)

    time_saved = db.Column(db.DateTime, default=datetime.now)

    autor = db.Column(db.Integer, db.ForeignKey("autor.id"))

    def jsonify(self):
        return {
            "id": self.id,
            "titulek": self.titulek,
            "podnadpis": self.podnadpis,
            "urlObrazek": self.url_obrazku,
            "blocks": self.blocks,
            "time_saved": self.time_saved.strftime("%d. %m. %Y (%H:%M)"),
            "autor": self.author.__repr__(),
        }


class Rychlovka(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    titulek = db.Column(db.String(200), unique=False, nullable=False)
    body = db.Column(db.Text, unique=True, nullable=False)

    datum = db.Column(db.DateTime, default=datetime.now)


class Autor(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    jmeno = db.Column(db.String(1000), unique=False, nullable=False)

    clanek = db.relationship("Clanek", backref="author")
    draft = db.relationship("Draft", backref="author")

    def __repr__(self):
        return '{"id": ' + str(self.id) + ', "jmeno": "' + self.jmeno + '"}'

    def jsonify(self):
        return {"id": self.id, "jmeno": self.jmeno}


class Stitek(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    nazev = db.Column(db.String(100), unique=True, nullable=False)
    rubrika = db.Column(db.Boolean, default=False)
    color = db.Column(db.String(10), nullable=False)

    clanky = db.Column(db.Integer, db.ForeignKey("clanek.id"))

    def __repr__(self):
        return self.nazev

    def jsonify(self):
        return {"id": self.id, "nazev": self.nazev, "color": self.color}


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
admin.add_view(ModelView(Draft, db.session))


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


def _save_draft(data):
    draft = Draft.query.filter_by(id=data["id"]).first()

    if draft:
        draft.titulek = data["titulek"]
        draft.podnadpis = data["podnadpis"]
        draft.url_obrazku = data["urlObrazku"]
        draft.blocks = json.dumps(data["blocks"])

        autor = Autor.query.filter_by(id=int(data["autor"])).first()
        draft.autor = autor.id
        draft.time_saved = datetime.now()
    else:
        autor = Autor.query.filter_by(id=int(data["autor"])).first()

        draft = Draft(
            titulek=data["titulek"],
            podnadpis=data["podnadpis"],
            url_obrazku=data["urlObrazku"],
            blocks=json.dumps(data["blocks"]),
            autor=autor.id,
        )
        db.session.add(draft)
    db.session.commit()
    return draft


@app.route("/save_draft", methods=["POST"])
@cross_origin()
def save_draft():
    data = request.json

    _save_draft(data)

    return "200"


@app.route("/save_draft_and_potvrdit", methods=["POST"])
@cross_origin()
def save_draft_and_potvrdit():
    data = request.json

    draft = _save_draft(
        data,
    )
    draft.zadost_o_potvrzeni = not draft.zadost_o_potvrzeni
    db.session.commit()

    return "200"


def _create_clanek(blocks):
    res = ""
    for i in blocks:
        if i["type"] == "p":
            res += (
                "<p>"
                + i["content"]
                .replace("@", "<b>")
                .replace("/@", "</b>")
                .replace("&", "<i>")
                .replace("/&", "</i>")
                + "</p>"
            )
        elif i["type"] == "h1":
            res += "<h3>" + i["content"] + "</h3>"
        elif i["type"] == "h2":
            res += "<h4>" + i["content"] + "</h4>"
        elif i["type"] == "h3":
            res += "<h5>" + i["content"] + "</h5>"
        elif i["type"] == "odrazka":
            res += "<div class='odrazka'>" + i["content"] + "</div>"
        elif i["type"] == "citace":
            res += "<div class='citace'>" + i["content"] + "</div>"
        elif i["type"] == "zvyrazneni":
            res += "<div class='zvyrazneni'>" + i["content"] + "</div>"
        elif i["type"] == "obrazek":
            res += "<img href='" + i["url"] + "' alt='whatever' />"

    return res


@app.route("/create_clanek", methods=["POST"])
@cross_origin()
def create_clanek():
    data = request.json

    body = data["blocks"]

    res = _create_clanek(body)

    print(data)

    stitek = Stitek.query.filter(Stitek.id == data["stitek"]).first()

    clanek = Clanek(
        titulek=data["titulek"],
        podnadpis=data["podnadpis"],
        body=res,
        main_image=data["urlObrazku"],
        autor=data["autor"],
        stitky=[stitek],
        dalsi_stitky=data["dalsiStitky"],
    )
    db.session.add(clanek)
    db.session.commit()

    return jsonify(res=res)


@app.route("/drafts", methods=["GET"])
@cross_origin()
def drafts():
    drafts = (
        Draft.query.filter(Draft.zadost_o_potvrzeni == False, Draft.vydan == False)
        .order_by(Draft.time_saved.desc())
        .all()
    )

    if drafts:
        drafts_last_id = Draft.query.all()[-1].id
    else:
        drafts_last_id = 0

    drafts_res = [x.jsonify() for x in drafts]

    return jsonify(drafts=drafts_res, next=drafts_last_id)


@app.route("/drafts_kontrola", methods=["GET"])
@cross_origin()
def drafts_kontrola():
    drafts = (
        Draft.query.filter(Draft.zadost_o_potvrzeni == True, Draft.vydan == False)
        .order_by(Draft.time_saved.desc())
        .all()
    )

    drafts_res = [x.jsonify() for x in drafts]

    return jsonify(drafts_res)


@app.route("/draft/<int:draft_id>", methods=["GET"])
@cross_origin()
def draft(draft_id):
    draft = Draft.query.filter_by(id=draft_id).first()

    autors = [x.jsonify() for x in Autor.query.all()]
    stitky = [x.jsonify() for x in Stitek.query.all()]

    print(stitky)

    if draft:
        return jsonify(draft=draft.jsonify(), autors=autors, stitky=stitky)
    else:
        return jsonify(titulek="None", autors=autors, stitky=stitky)


@app.route("/delete_draft/<int:draft_id>", methods=["GET"])
@cross_origin()
def delete_draft(draft_id):
    draft = Draft.query.filter_by(id=draft_id).delete()
    db.session.commit()
    return "200"


if __name__ == "__main__":
    app.run(port=8000)
    # app.run(threaded=True, port=int(os.environ.get("PORT", 5000))) # Heroku
