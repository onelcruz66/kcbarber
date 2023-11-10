from flask import Flask
from flask import render_template
from flask import request
from flask import url_for

app = Flask(__name__, template_folder='templates', static_folder='static')

@app.route("/")
@app.route("/home")
def home():
    return render_template("index.html")

@app.route("/gallery")
def gallery():
    return render_template("gallery.html")

@app.route("/contact-us")
def contact():
    return render_template("contact-us.html")


if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5000)