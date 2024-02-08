import os

from flask import Flask, session, render_template
from flask_session import Session
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker

app = Flask(__name__)
password = '12345'
owner_name = 'postgres'
# database_name = '"PostgreSQL 16"'
database_name = 'project1'
DATABASE_URL = 'postgresql://'+ owner_name +':'+ password +'@localhost/' + database_name
# DATABASE_URL = 'postgresql://postgres:12345@localhost/PostgreSQL 16'
# DATABASE_URL = 'localhost:5432:PostgreSQL 16:postgres:12345'
print(DATABASE_URL)

# # Check for environment variable
# os.getenv(DATABASE_URL)
# if not os.getenv(DATABASE_URL):
#     raise RuntimeError("DATABASE_URL is not set")

# Configure session to use filesystem
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Set up database
engine = create_engine(os.getenv(DATABASE_URL))
# engine = create_engine(DATABASE_URL)
db = scoped_session(sessionmaker(bind=engine))
print(db)


@app.route("/")
def index():
    return render_template("login.html")


@app.route("/search")
def search():
    return render_template("search.html")

# set DATABASE_URL=postgresql://postgres:12345@localhost/PostgreSQL 16
# pg_isready -d PostgreSQL 16 -h localhost -p 5432 -U postgre



from flask import Flask, request, redirect, url_for, render_template, flash
from flask_session import Session  # Ensure Flask-Session is installed

app = Flask(__name__)
app.secret_key = 'your_secret_key_here'
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Simulated database using a dictionary
users_db = {}

@app.route("/")
def index():
    # Redirect to login if not logged in, otherwise show home page
    if 'username' in session:
        return f'Welcome {session["username"]}! <br> <a href="/logout">Logout</a>'
    else:
        return redirect(url_for('login'))

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form.get('username')
        password = request.form.get('password')  # WARNING: Hash password in real apps

        if username in users_db:
            flash('Username already exists. Choose another one.')
            return redirect(url_for('register'))

        users_db[username] = password  # Save the user
        flash('Registration successful. Please login.')
        return redirect(url_for('login'))
    
    return render_template("registration.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get('username')
        password = request.form.get('password')  # In real apps, compare hash

        if username in users_db and users_db[username] == password:
            session['username'] = username
            return redirect(url_for('index'))
        else:
            flash('Invalid username or password')

    return render_template("login.html")

@app.route("/logout")
def logout():
    session.pop('username', None)
    return redirect(url_for('login'))