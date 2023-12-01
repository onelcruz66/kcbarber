import os
from flask import Flask
from flask import render_template
from flask import request
from flask import url_for
from flask import redirect
from flask import session
from flask_migrate import Migrate
from flask_login import UserMixin, login_user, LoginManager, login_required, logout_user, current_user
from flask import flash
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import InputRequired, Length, ValidationError
from flask_bcrypt import Bcrypt

from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import desc
from datetime import datetime

import psycopg2
from dotenv import load_dotenv

def configure():
    load_dotenv()

db_user=os.getenv('db_user')
db_password=os.getenv('db_password')
db_url=os.getenv('db_url')
db_name=os.getenv('db_name')

app = Flask(__name__, template_folder='templates', static_folder='static')
app.config['SQLALCHEMY_DATABASE_URI'] = \
    f'postgresql://{db_user}:{db_password}@{db_url}/{db_name}'

app.config['SECRET_KEY'] = os.getenv('secret_key')

bcrypt = Bcrypt(app)
db=SQLAlchemy(app)
migrate = Migrate(app, db)
# db.init_app(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Create the email subscribers model.
class EmailSubscribers(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    subscriber_email_address = db.Column(db.String(200), nullable=False)
    email_date_created = db.Column(db.DateTime, default=datetime.utcnow)

# Create the requested appointments model.
class RequestedAppointments(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    customer_name = db.Column(db.String(100), nullable=False)
    email_address = db.Column(db.String(100), nullable=False)
    phone_number = db.Column(db.String(20), nullable=False)
    service_requested = db.Column(db.String(20), nullable=False)
    date_requested = db.Column(db.Date, nullable=False)
    customer_message = db.Column(db.String(200))

class BackupRequestedAppointments(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    customer_name = db.Column(db.String(100), nullable=False)
    email_address = db.Column(db.String(100), nullable=False)
    phone_number = db.Column(db.String(20), nullable=False)
    service_requested = db.Column(db.String(20), nullable=False)

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20), nullable=False, unique=True)
    password = db.Column(db.String(80), nullable=False)

class LoginForm(FlaskForm):
    username = StringField(validators=[InputRequired(), \
                                       Length(min=4, max=20)], \
                                        render_kw={"placeholder": "Username"})
    
    password = PasswordField(validators=[InputRequired(), \
                                         Length(min=4, max=20)], \
                                            render_kw={"placeholder": "Password"})
    
    submit = SubmitField("Login")

class RegisterForm(FlaskForm):
    username = StringField(validators=[InputRequired(), \
                                       Length(min=4, max=20)], \
                                        render_kw={"placeholder": "Username"})
    
    password = PasswordField(validators=[InputRequired(), \
                                         Length(min=4, max=20)], \
                                            render_kw={"placeholder": "Password"})
    
    submit = SubmitField("Register")

    def validate_username(self, username):
        existing_user_name = User.query.filter_by(username=username.data).first()

        if existing_user_name:
            raise ValidationError("That username already exists. \
                                  Please choose a different one.")


@app.route("/", methods=["GET", "POST"])
@app.route("/home", methods=["GET", "POST"])
def home():
    if request.method == "POST":

        if 'customer_name' in request.form:
            customer_name = request.form['customer_name']
            email_address = request.form['email_address']
            phone_number = request.form['phone_number']
            service_requested = request.form['service_requested']
            date_requested = request.form['date_requested'] 
            customer_message = request.form['customer_message']

            new_appointment = RequestedAppointments(customer_name=customer_name, \
                                                    email_address=email_address, \
                                                    phone_number=phone_number, \
                                                    service_requested=service_requested, \
                                                    date_requested=date_requested, \
                                                    customer_message=customer_message)
            
            store_appointment = BackupRequestedAppointments(customer_name=customer_name, \
                                                            email_address=email_address, \
                                                            phone_number=phone_number, \
                                                            service_requested=service_requested)
            
            # Push to RequestedAppointments database table.
            try:
                db.session.add(new_appointment)
                db.session.commit()

                
                db.session.add(store_appointment)
                db.session.commit()
                return redirect(url_for("appointment"))
            except:
                flash("There was an error with requesting your appointment.", "info")
                return redirect(url_for("home"))
        else:
            subscriber_email_address = request.form['subscriber_email_address']
            new_email = EmailSubscribers(subscriber_email_address=subscriber_email_address)

            # Push to database
            try:
                db.session.add(new_email)
                db.session.commit()
                return redirect(url_for("success"))
            except:
                flash("There was an error with adding your email.", "info")
                return redirect(url_for("home")) 
    
    return render_template("index.html")

@app.route("/gallery")
def gallery():
    return render_template("gallery.html")

@app.route("/contact-us")
def contact():
    return render_template("contact-us.html")


@app.route("/success", methods=["GET", "POST"])
def success():
    emailObject = db.session.query(EmailSubscribers).order_by(desc(EmailSubscribers.id)).first()
    email = emailObject.subscriber_email_address
    return render_template("success.html", email=email)

@app.route("/appointment-requested", methods=["GET", "POST"])
def appointment():
    appointmentObject = db.session.query(RequestedAppointments).order_by(desc(RequestedAppointments.id)).first()
    customer_name = appointmentObject.customer_name
    return render_template("appointment-requested.html", customer_name=customer_name)

@app.route("/register", methods=["GET", "POST"])
@login_required
def register():
    form = RegisterForm()

    if form.validate_on_submit():
        hashed_password = bcrypt.generate_password_hash(form.password.data)
        hashed_password = hashed_password.decode("utf-8", "ignore")
        new_user = User(username=form.username.data, password=hashed_password)
        db.session.add(new_user)
        db.session.commit()
        return redirect(url_for("login"))

    return render_template("register.html", form=form)

@app.route("/login", methods=["GET", "POST"])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user:
            if bcrypt.check_password_hash(user.password, form.password.data):
                login_user(user)
                return redirect(url_for("admin"))
    return render_template("login.html", form=form)

@app.route("/logout", methods=["GET", "POST"])
@login_required
def logout():
    logout_user()
    return redirect(url_for("login"))

@app.route("/admin", methods=["GET", "POST"])
@login_required
def admin():
    try:
        # Fetch all records from RequestedAppointments table
        all_records = RequestedAppointments.query.all()
    except Exception as e:
        return f"Error fetching records: {str(e)}"

    return render_template("admin.html", appointments=all_records)

@app.route("/delete_appointment/<int:appointment_id>", methods=["GET", "POST"])
def delete_appointment(appointment_id):
    try:
        appointment = RequestedAppointments.query.get(appointment_id)
        db.session.delete(appointment)
        db.session.commit()
        flash("Appointment deleted successfully.", "success")
    except Exception as e:
        flash(f'Error deleting appointment: {str(e)}', 'danger')
    return redirect(url_for("admin"))

if __name__ == '__main__':
    configure()
    app.run(host="0.0.0.0", port=5000)

