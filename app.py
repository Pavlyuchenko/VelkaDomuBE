from flask import Flask, jsonify, request, abort, make_response
from flask_sqlalchemy import SQLAlchemy
from flask_admin import Admin
from flask_admin.contrib.sqla import ModelView
from flask_cors import CORS, cross_origin
from flask_migrate import Migrate

from datetime import datetime, date
import json
from imagekitio import ImageKit

# Password
import hashlib, binascii, os

# Emails
from flask_mail import Message, Mail

# Code
from random import randint


app = Flask(__name__)
app.config["DEBUG"] = False
app.config["TESTING"] = False
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///database.db"
app.config["SECRET_KEY"] = "ioF45sdfFef84egfgew84aSgGDAGge84DGQEWgGd"
app.config["MAIL_SERVER"] = "smtp.zoho.eu"
app.config["MAIL_PORT"] = "465"
app.config["MAIL_USE_TLS"] = False
app.config["MAIL_USE_SSL"] = True
app.config["MAIL_DEBUG"] = False
app.config["MAIL_USERNAME"] = "admin@velkadomu.cz"
app.config["MAIL_PASSWORD"] = "KubaIstVerruckt123*"
app.config["MAIL_DEFAULT_SENDER"] = "admin@velkadomu.cz"
app.config["MAIL_MAX_EMAILS"] = 5
app.config["MAIL_SUPPRESS_SEND"] = False
app.config["MAIL_ASCII_ATTACHMENTS"] = False

cors = CORS(app)
app.config["CORS_HEADERS"] = "Content-Type"

db = SQLAlchemy(app)
migrate = Migrate(app, db)

tags = db.Table(
    "tags",
    db.Column("clanek_id", db.Integer, db.ForeignKey("clanek.id")),
    db.Column("stitek_id", db.Integer, db.ForeignKey("stitek.id")),
)
mail = Mail(app)


class Clanek(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    titulek = db.Column(db.String(1000), unique=False, nullable=False)
    podnadpis = db.Column(db.Text, unique=True, nullable=False)
    main_popis = db.Column(db.Text, unique=False, nullable=True)
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

    hlavni = db.Column(db.Boolean, default=False)
    sekundarni = db.Column(db.Boolean, default=False)

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
            "stitekColor": self.stitky[0].color,
            "logo": self.author.logo,
        }

    def jsonify_hlavni_clanek(self):
        return {
            "id": self.id,
            "titulek": self.titulek,
            "popisek": self.main_popis,
            "obrazek": self.main_image,
            "datum": self.datum.strftime("%d. %m. %Y"),
            "autor": self.author.jmeno,
            "stitek": self.stitky[0].nazev,
            "stitekColor": self.stitky[0].color,
            "logo": "VelkaDomu",
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

    logo = db.Column(db.String(1000), unique=False, nullable=False, default="VelkaDomu")

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


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    email = db.Column(db.Text, unique=True, nullable=False)
    prezdivka = db.Column(db.Text, unique=True, nullable=False)
    heslo = db.Column(db.Text, unique=True, nullable=False)

    last_logged = db.Column(db.Text, nullable=True)
    last_cookie = db.Column(db.Text, nullable=True)

    email_confirmed = db.Column(db.Boolean, default=False)
    five_digit = db.Column(db.Text)


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
admin.add_view(ModelView(User, db.session))


@app.route("/main-desktop", methods=["GET"])
@cross_origin()
def maindesktop():
    hlavni_clanek = Clanek.query.filter(Clanek.hlavni == True).first()
    sekundarni_clanky = (
        Clanek.query.filter(Clanek.sekundarni == True)
        .order_by(Clanek.datum.desc())
        .all()
    )

    forbidden_ids = []
    if hlavni_clanek:
        forbidden_ids.append(hlavni_clanek.id)
    if sekundarni_clanky:
        for i in sekundarni_clanky:
            forbidden_ids.append(i.id)

    clanky = (
        Clanek.query.filter(Clanek.id.notin_(forbidden_ids))
        .order_by(Clanek.datum.desc())
        .all()
    )

    clanky_res = [x.jsonify_main() for x in clanky]
    if hlavni_clanek:
        hlavni_clanek = hlavni_clanek.jsonify_hlavni_clanek()

    sekundarni_clanky_res = []
    if sekundarni_clanky:
        for i in sekundarni_clanky:
            sekundarni_clanky_res.append(i.jsonify_main())

    sekundarni_clanky_res.insert(0, hlavni_clanek)

    return jsonify(
        clanky=clanky_res,
        sekundarni_clanky=sekundarni_clanky_res,
    )


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
                .replace("/@", "</b>")
                .replace("@", "<b>")
                .replace("/&amp;", "</i>")
                .replace("&amp;", "<i>")
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

    stitek = Stitek.query.filter(Stitek.id == data["stitek"]).first()

    imagekit = ImageKit(
        private_key="private_c84cRvoOXrExXFP/znj6J3pFFrM=",
        public_key="public_gn7dgk7SJbBFinh/vtiiagVDgbM=",
        url_endpoint="https://ik.imagekit.io/velkadomu/",
    )
    upload = imagekit.upload(
        file=data["urlObrazku"], file_name=data["titulek"].replace(" ", "-")
    )

    clanek = Clanek(
        titulek=data["titulek"],
        podnadpis=data["podnadpis"],
        body=res,
        main_image="/" + upload["response"]["name"],
        autor=data["autor"],
        stitky=[stitek],
        dalsi_stitky=data["dalsiStitky"],
    )

    print(data)

    draft = Draft.query.filter(Draft.id == data["id"]).first()
    _save_draft(data["blocks"])
    draft.vydan = True

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

    drafts_id = Draft.query.order_by(Draft.id.desc()).all()

    if drafts_id:
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


@app.route("/auth", methods=["GET"])
def auth():
    imagekit = ImageKit(
        public_key="public_gn7dgk7SJbBFinh/vtiiagVDgbM=",
        url_endpoint="https://ik.imagekit.io/velkadomu/",
        private_key="private_c84cRvoOXrExXFP/znj6J3pFFrM=",
    )
    auth_params = imagekit.get_authentication_parameters()
    return auth_params


@app.route("/titulni-clanek", methods=["GET"])
@cross_origin()
def titulni_clanek():
    clanky = (
        Clanek.query.filter(Clanek.sekundarni == False)
        .order_by(Clanek.datum.desc())
        .limit(12)
        .all()
    )

    clanky_res = [x.jsonify_main() for x in clanky]

    hlavni_clanek = Clanek.query.filter(Clanek.hlavni == True).first().id

    return jsonify(clanky=clanky_res, id=hlavni_clanek)


@app.route("/set-hlavni-clanek", methods=["POST"])
@cross_origin()
def set_hlavni_clanek():
    data = request.json
    _id = data["id"]
    Clanek.query.filter(Clanek.hlavni == True).first().hlavni = False
    Clanek.query.filter(Clanek.id == _id).first().hlavni = True
    db.session.commit()

    return "200"


@app.route("/sekundarni-clanky", methods=["GET"])
@cross_origin()
def sekundarni_clanek():
    clanky = (
        Clanek.query.filter(Clanek.hlavni == False)
        .order_by(Clanek.datum.desc())
        .limit(18)
        .all()
    )

    clanky_res = [x.jsonify_main() for x in clanky]

    sekundarni_clanky = Clanek.query.filter(Clanek.sekundarni == True).all()
    sekundarni_clanky_ids = []

    for i in sekundarni_clanky:
        sekundarni_clanky_ids.append(i.id)

    return jsonify(clanky=clanky_res, ids=sekundarni_clanky_ids)


@app.route("/set-sekundarni-clanek", methods=["POST"])
@cross_origin()
def set_sekundarni_clanek():
    data = request.json
    _ids = data["ids"]
    old = Clanek.query.filter(Clanek.sekundarni == True).all()

    for i in old:
        i.sekundarni = False

    for i in _ids:
        Clanek.query.filter(Clanek.id == i).first().sekundarni = True
    db.session.commit()

    return "200"


# Login


def hash_password(password):
    """Hash a password for storing."""
    salt = hashlib.sha256(os.urandom(60)).hexdigest().encode("ascii")
    pwdhash = hashlib.pbkdf2_hmac("sha512", password.encode("utf-8"), salt, 100000)
    pwdhash = binascii.hexlify(pwdhash)
    return (salt + pwdhash).decode("ascii")


def verify_password(stored_password, provided_password):
    """Verify a stored password against one provided by user"""
    salt = stored_password[:64]
    stored_password = stored_password[64:]
    pwdhash = hashlib.pbkdf2_hmac(
        "sha512", provided_password.encode("utf-8"), salt.encode("ascii"), 100000
    )
    pwdhash = binascii.hexlify(pwdhash).decode("ascii")
    return pwdhash == stored_password


def get_cookie(user):
    today = date.today()
    user_cookie = hash_password(user.prezdivka + str(today))

    user.last_logged = str(today)
    user.last_cookie = user_cookie
    db.session.commit()

    return jsonify(user_cookie=user_cookie, prezdivka=user.prezdivka)


@app.route("/login", methods=["POST", "GET"])
@cross_origin()
def login():
    data = request.json

    name = data["email"]
    heslo = data["heslo"]

    user = User.query.filter(
        (User.email == name) | (User.prezdivka == name)
    ).first_or_404()

    if not verify_password(user.heslo, heslo):
        print("wrong")
        abort(400)

    if user.email_confirmed:
        return get_cookie(user)
    else:
        return jsonify(error="email")


@app.route("/check_cookie", methods=["POST", "GET"])
@cross_origin()
def check_cookie():
    data = request.json

    cookie = data["cookie"]
    prezdivka = data["prezdivka"]
    print(prezdivka)

    user = User.query.filter(User.prezdivka == prezdivka).first_or_404()

    if not verify_password(user.last_cookie, prezdivka + user.last_logged):
        print("wrong")
        abort(400)
        return

    return "200"


def random_with_N_digits(n):
    range_start = 10 ** (n - 1)
    range_end = (10 ** n) - 1
    return randint(range_start, range_end)


@app.route("/send_email", methods=["POST", "GET"])
@cross_origin()
def send_email():
    data = request.json

    email = data["email"]
    prezdivka = data["prezdivka"]
    heslo = data["heslo"]
    rand = random_with_N_digits(5)

    user = User(
        email=email, prezdivka=prezdivka, heslo=hash_password(heslo), five_digit=rand
    )
    db.session.add(user)
    db.session.commit()

    print(rand)

    msg = Message("VelkáDomů.cz", recipients=[email])
    msg.html = (
        """
  <link rel="preconnect" href="https://fonts.gstatic.com">
<link href="https://fonts.googleapis.com/css2?family=Titillium+Web:wght@600&display=swap" rel="stylesheet">
  <title>VelkáDomů.cz</title> 
 </head> 
 <body style="width:100%;font-family:arial, 'helvetica neue', helvetica, sans-serif;-webkit-text-size-adjust:100%;-ms-text-size-adjust:100%;padding:0;Margin:0"> 
   <table class="es-wrapper" width="100%" cellspacing="0" cellpadding="0" style="mso-table-lspace:0pt;mso-table-rspace:0pt;border-collapse:collapse;border-spacing:0px;padding:0;Margin:0;width:100%;height:100%;background-repeat:repeat;background-position:center top"> 
     <tbody><tr style="border-collapse:collapse"> 
      <td valign="top" style="padding:0;Margin:0"> 
       <table class="es-content" cellspacing="0" cellpadding="0" align="center" style="mso-table-lspace:0pt;mso-table-rspace:0pt;border-collapse:collapse;border-spacing:0px;table-layout:fixed !important;width:100%"> 
         <tbody><tr style="border-collapse:collapse"> 
          <td align="center" style="padding:0;Margin:0"> 
           <table class="es-content-body" cellspacing="0" cellpadding="0" bgcolor="#ffffff" align="center" style="mso-table-lspace:0pt;mso-table-rspace:0pt;border-collapse:collapse;border-spacing:0px;background-color:#FFFFFF;width:600px"> 
             <tbody><tr style="border-collapse:collapse"> 
              <td align="left" style="padding:0;Margin:0;padding-top:20px;padding-left:20px;padding-right:20px"> 
               <table cellpadding="0" cellspacing="0" width="100%" style="mso-table-lspace:0pt;mso-table-rspace:0pt;border-collapse:collapse;border-spacing:0px"> 
                 <tbody><tr style="border-collapse:collapse"> 
                  <td align="center" valign="top" style="padding:0;Margin:0;width:560px"> 
                   <table cellpadding="0" cellspacing="0" width="100%" role="presentation" style="mso-table-lspace:0pt;mso-table-rspace:0pt;border-collapse:collapse;border-spacing:0px"> 
                     <tbody><tr style="border-collapse:collapse"> 
                      <td align="center" style="padding:0;Margin:0;font-size:0px"><a target="_blank" href="https://velkadomu.cz/" style="-webkit-text-size-adjust:none;-ms-text-size-adjust:none;mso-line-height-rule:exactly;font-family:arial, 'helvetica neue', helvetica, sans-serif;font-size:14px;text-decoration:underline;color:#2CB543"><img class="adapt-img" src="https://okoxnh.stripocdn.email/content/guids/CABINET_91defe5e82af8afc46d0710ada08f2f7/images/14471609608275059.png" alt="Velká Domů Logo" style="display:block;border:0;outline:none;text-decoration:none;-ms-interpolation-mode:bicubic" title="Velká Domů Logo" width="173"></a></td> 
                     </tr> 
                     <tr style="border-collapse:collapse"> 
                      <td align="center" style="padding:15px;Margin:0"><p style="Margin:0;-webkit-text-size-adjust:none;-ms-text-size-adjust:none;mso-line-height-rule:exactly;font-size:30px;font-family:arial, 'helvetica neue', helvetica, sans-serif;line-height:45px;color:#333333"><strong>Ve<span style="font-size:34px"></span>lkáDomů.cz</strong></p></td> 
                     </tr> 
                     <tr style="border-collapse:collapse"> 
                      <td align="center" style="padding:0;Margin:0;padding-bottom:15px;padding-right:15px;padding-top:25px"><p style="Margin:0;-webkit-text-size-adjust:none;-ms-text-size-adjust:none;mso-line-height-rule:exactly;font-size:14px;font-family:arial, 'helvetica neue', helvetica, sans-serif;line-height:21px;color:#333333"><strong>Tvůj ověřovací kód je:</strong></p></td> 
                     </tr> 
                     <tr style="border-collapse:collapse"> 
                      <td  align="center" style="padding:0;Margin:0"> 
                       <div style="border:3px solid #FF8A00;height:50px;text-align:center;line-height:50px;font-size:35px;letter-spacing:15px;width:45%;font-weight:600">
                         """
        + str(rand)
        + """ 
                       </div></td> 
                     </tr> 
                     <tr style="border-collapse:collapse"> 
                      <td align="center" style="padding:0;Margin:0;padding-top:40px;padding-bottom:40px;padding-right:40px"><p style="Margin:0;-webkit-text-size-adjust:none;-ms-text-size-adjust:none;mso-line-height-rule:exactly;font-size:14px;font-family:arial, 'helvetica neue', helvetica, sans-serif;line-height:21px;color:#333333">Pokud se něco pokazilo, klikni na následující odkaz:<span style="color:#FF8C00"></span><a target="_blank" href="https://fotbalpropal.vercel.app/verify-email/"""
        + str(prezdivka)
        + "/"
        + str(rand)
        + """" style="-webkit-text-size-adjust:none;-ms-text-size-adjust:none;mso-line-height-rule:exactly;font-family:arial, 'helvetica neue', helvetica, sans-serif;font-size:14px;text-decoration:underline;color:#FF8C00">velkadomu.cz</a></p></td> 
                     </tr> 
                     <tr style="border-collapse:collapse"> 
                      <td style="padding:0;Margin:0"> 
                       <div></div></td> 
                     </tr> 
                   </tbody></table></td> 
                 </tr> 
               </tbody></table></td> 
             </tr> 
           </tbody></table></td> 
         </tr> 
       </tbody></table></td> 
     </tr> 
   </tbody></table> 
  </div>  
 
</body></html>"""
    )

    mail.send(msg)

    return "200"


@app.route("/register", methods=["POST", "GET"])
@cross_origin()
def register():
    data = request.json

    five_digit = data["fiveDigit"]
    prezdivka = data["prezdivka"]
    print(prezdivka)

    user = User.query.filter(User.prezdivka == prezdivka).first_or_404()

    if five_digit == user.five_digit:
        user.email_confirmed = True
        db.session.commit()

        return get_cookie(user)
    else:
        return "400"


@app.route("/verify_email", methods=["POST", "GET"])
@cross_origin()
def verify_email():
    data = request.json
    prezdivka = data["prezdivka"]
    code = data["code"]

    user = User.query.filter(User.prezdivka == prezdivka).first_or_404()
    user.email_confirmed = True
    db.session.commit()

    if user.five_digit == code:
        return ""
    else:
        abort(400)


@app.route("/", methods=["POST", "GET"])
@cross_origin()
def test():
    msg = Message("Testovací BOoody", recipients=["michaelg.pavlicek@gmail.com"])
    msg.html = "<h1>Čest Gmaile</h1><br />Takto to fachá?"

    mail.send(msg)

    return "200"


if __name__ == "__main__":
    app.run(port=8000)
