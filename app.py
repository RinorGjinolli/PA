"""
This script runs the application using a development server.
It contains the definition of routes and views for the application.
"""

from flask import Flask, render_template, redirect, url_for, flash, request
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, SelectField
from wtforms.validators import InputRequired, Length, Email
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate

app = Flask(__name__)
# MySQL Connection String
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql://user:Test@localhost:3306/VCID'
# Secret Key for App
app.config['SECRET_KEY'] = 'SECRETKEY'
 
# SQLAlchemy Initialisierung for DB
db = SQLAlchemy()
db.init_app(app)
 
# Database Models:
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), nullable=False, unique=True)
    email = db.Column(db.String(150), nullable=False, unique=True)
    password = db.Column(db.String(250), nullable=False)

class Device(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    device_type = db.Column(db.String(50), nullable=False)
    brand = db.Column(db.String(50), nullable=False)
    hostname = db.Column(db.String(50), nullable=False)
    owner_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    owner = db.relationship('User', backref='devices')
 
# Migrate Object of DB-Model in App
migrate = Migrate(app, db)

class LoginForm(FlaskForm):
    email = StringField('Email', validators=[InputRequired(), Email()])
    password = PasswordField('Password', validators=[InputRequired()])
    submit = SubmitField('Login')

class RegisterForm(FlaskForm):
    username = StringField('Username', validators=[InputRequired(), Length(min=4, max=20)])
    email = StringField('Email', validators=[InputRequired(), Email()])
    password = PasswordField('Password', validators=[InputRequired()])
    submit = SubmitField('Register')

class AddDeviceForm(FlaskForm):
    device_type = SelectField('Geraetetyp', choices=[('Notebook', 'Notebook'), ('Tower', 'Tower')], validators=[InputRequired()])
    brand = StringField('Marke', validators=[InputRequired(), Length(min=2, max=50)])
    hostname = StringField('Hostname', validators=[InputRequired(), Length(min=2, max=50)])
    submit = SubmitField('Geraet hinzufuegen')

# Make the WSGI interface available at the top level so wfastcgi can get it.
wsgi_app = app.wsgi_app

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.route('/')
@login_required
def index():
    devices = Device.query.all()
    return render_template('index.html', devices=devices)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        user = User.query.filter_by(email=email).first()
        if user and check_password_hash(user.password, password):
            login_user(user)
            return redirect(url_for('index'))
        flash('Login fehlgeschlagen. Ueberpruefe deine Anmeldedaten.')
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        # Generate Password-Hash (default hashing method gets used "pbkdf2:sha256")
        hashed_password = generate_password_hash(password)
        new_user = User(username=username, email=email, password=hashed_password)
        db.session.add(new_user)
        db.session.commit()
        return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route('/add_device', methods=['GET', 'POST'])
@login_required
def add_device():
    form = AddDeviceForm()
    if form.validate_on_submit():
        new_device = Device(
            device_type=form.device_type.data,
            brand=form.brand.data,
            hostname=form.hostname.data,
            owner_id=current_user.id  # Aktueller Benutzer als Eigentuemer
        )
        db.session.add(new_device)
        db.session.commit()
        flash('Geraet erfolgreich hinzugefuegt!', 'success')
        return redirect(url_for('index'))
    return render_template('add_device.html', form=form)

@app.route('/delete_device/<int:device_id>', methods=['POST'])
@login_required
def delete_device(device_id):
    device = Device.query.get_or_404(device_id)
    
    # Ueberpruefe, ob der Benutzer der Eigentuemer des Geraets ist
    if device.owner_id != current_user.id:
        flash('Du bist nicht berechtigt, dieses Geraet zu loeschen.', 'danger')
        return redirect(url_for('index'))
    
    db.session.delete(device)
    db.session.commit()
    flash('Geraet erfolgreich geloescht!', 'success')
    return redirect(url_for('index'))

if __name__ == '__main__':
    import os
    HOST = os.environ.get('SERVER_HOST', 'localhost')
    try:
        PORT = int(os.environ.get('SERVER_PORT', '5555'))
    except ValueError:
        PORT = 5555
    app.run(HOST, PORT)
