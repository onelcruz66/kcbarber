import os
from flask import Flask
from flask import render_template
from flask import request
from flask import url_for
from flask import redirect
from flask import session

from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import desc
from datetime import datetime

import psycopg2


app = Flask(__name__, template_folder='templates', static_folder='static')
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://kcbarber_user:KEut1SNGjast5ga8wRFxVLrsKm7mUWiS@dpg-cldqs6ghgaic73bmgs5g-a.oregon-postgres.render.com/kcbarber'

db=SQLAlchemy(app)
# db.init_app(app)

# Create a model
class Customers(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(200), nullable=False)
    date_created = db.Column(db.DateTime, default=datetime.utcnow)


@app.route("/", methods=["GET", "POST"])
@app.route("/home", methods=["GET", "POST"])
def home():
    if request.method == "POST":
        email_address = request.form['email_address']
        new_email = Customers(email=email_address)

        # Push to database
        try:
            db.session.add(new_email)
            db.session.commit()
            return redirect(url_for("success"))
        except:
            return "There was an error with adding your email."
    
    return render_template("index.html")

@app.route("/gallery")
def gallery():
    return render_template("gallery.html")

@app.route("/contact-us")
def contact():
    return render_template("contact-us.html")


@app.route("/success", methods=["GET", "POST"])
def success():
    emailObject = db.session.query(Customers).order_by(desc(Customers.id)).first()
    email = emailObject.email
    return render_template("success.html", email=email)


if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5000)

