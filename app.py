"""
Dieses Skript fuehrt die Anwendung mit einem Entwicklungsserver aus.
Es enthaelt die Definition der Routen und Ansichten fuer die Anwendung.
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

# MySQL-Verbindungsstring zur Datenbank
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql://user:Test@localhost:3306/VCID'

# Geheimschluessel fuer die App (wird fuer Sessions und Formulare verwendet)
app.config['SECRET_KEY'] = 'SECRETKEY'
 
# Initialisierung von SQLAlchemy fuer die Datenbankverbindung
db = SQLAlchemy()
db.init_app(app)
 
# Datenbankmodelle:
class User(UserMixin, db.Model):
     # Tabelle fuer Benutzer
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), nullable=False, unique=True)
    email = db.Column(db.String(150), nullable=False, unique=True)
    password = db.Column(db.String(250), nullable=False)

class Device(db.Model):
    # Tabelle fuer Geräte
    id = db.Column(db.Integer, primary_key=True)
    device_type = db.Column(db.String(50), nullable=False)
    brand = db.Column(db.String(50), nullable=False)
    hostname = db.Column(db.String(50), nullable=False)
    owner_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    owner = db.relationship('User', backref='devices')
 
# Flask-Migrate-Objekt, um Datenbankmigrationen zu verwalten
migrate = Migrate(app, db)

# Formular fuer die Benutzeranmeldung
class LoginForm(FlaskForm):
    email = StringField('Email', validators=[InputRequired(), Email()])
    password = PasswordField('Password', validators=[InputRequired()])
    submit = SubmitField('Login')

# Formular fuer die Benutzerregistrierung
class RegisterForm(FlaskForm):
    username = StringField('Username', validators=[InputRequired(), Length(min=4, max=20)])
    email = StringField('Email', validators=[InputRequired(), Email()])
    password = PasswordField('Password', validators=[InputRequired()])
    submit = SubmitField('Register')

# Formular zum Hinzufuegen eines neuen Geraets
class AddDeviceForm(FlaskForm):
    device_type = SelectField('Geraetetyp', choices=[('Notebook', 'Notebook'), ('Tower', 'Tower')], validators=[InputRequired()])
    brand = StringField('Marke', validators=[InputRequired(), Length(min=2, max=50)])
    hostname = StringField('Hostname', validators=[InputRequired(), Length(min=2, max=50)])
    submit = SubmitField('Geraet hinzufuegen')

# Macht die WSGI-Schnittstelle auf oberster Ebene verfuegbar
wsgi_app = app.wsgi_app

# Initialisierung des Login-Managers fuer Benutzer-Authentifizierung
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# Laedt den Benutzer basierend auf der Benutzer-ID (wird fuer die Sitzung verwendet)
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Route fuer die Startseite, die eine Uebersicht der Geraete anzeigt (nur fuer angemeldete Benutzer)
@app.route('/')
@login_required
def index():
    devices = Device.query.all()
    return render_template('index.html', devices=devices)

# Route fuer die Benutzerregistrierung
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        # Generiert Password-Hash default hashing Methode "pbkdf2:sha256"
        hashed_password = generate_password_hash(password)
        new_user = User(username=username, email=email, password=hashed_password)
        db.session.add(new_user)
        db.session.commit()
        return redirect(url_for('login'))
    return render_template('register.html')

# Route fuer das Benutzer-Login
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

# Route fuer das Benutzer-Logout
@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

# Route zum Hinzufuegen eines neuen Geraets (nur fuer angemeldete Benutzer)
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

# Route zum Loeschen eines Geraets (nur fuer angemeldete Benutzer)
@app.route('/delete_device/<int:device_id>', methods=['POST'])
@login_required
def delete_device(device_id):
    device = Device.query.get_or_404(device_id)
    
    # Ueberpruefen, ob der angemeldete Benutzer der Eigentuemer des Geraets ist
    if device.owner_id != current_user.id:
        flash('Du bist nicht berechtigt, dieses Geraet zu loeschen.', 'danger')
        return redirect(url_for('index'))
    
    db.session.delete(device)
    db.session.commit()
    flash('Geraet erfolgreich geloescht!', 'success')
    return redirect(url_for('index'))

# Startet die Flask-App, wenn das Skript direkt ausgefuehrt wird
if __name__ == '__main__':
    import os
    HOST = os.environ.get('SERVER_HOST', 'localhost')
    try:
        PORT = int(os.environ.get('SERVER_PORT', '5555'))
    except ValueError:
        PORT = 5555
    app.run(HOST, PORT)
