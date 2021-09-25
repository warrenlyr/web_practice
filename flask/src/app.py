#from click.decorators import confirmation_option
from click.decorators import confirmation_option
from flask import Flask, render_template
from flask import request, url_for, redirect, flash
from flask_login import UserMixin, LoginManager, login_manager, login_user, login_required, current_user, logout_user
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
import click, os, sys


# Config
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:////' + os.path.join(app.root_path, 'data.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'dev'
db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'


# Load user
@login_manager.user_loader
def load_user(user_id):
    user = User.query.get(int(user_id))
    return user


# Init database, option to init after drop
@app.cli.command()
@click.option('--drop', is_flag=True, help='Create a new database after drop.')
def initdb(drop):
    # Initialize the database.
    if drop:
        db.drop_all()
        click.echo('Databse dropped.')
    db.create_all()
    click.echo('Initialized database.')


# Create fake data
@app.cli.command()
def forge():
    db.create_all()
    
    name = 'Jennie Kim'
    movies = [
        {'title': 'test movie 1', 'year': '2012'},
        {'title': 'test movie 2', 'year': '2013'},
        {'title': 'test movie 3', 'year': '2014'},
        {'title': 'test movie 4', 'year': '2015'},
        {'title': 'test movie 5', 'year': '2016'},
        {'title': 'test movie 6', 'year': '2017'},
        {'title': 'test movie 7', 'year': '2018'},
        {'title': 'test movie 8', 'year': '2019'},
        {'title': 'test movie 9', 'year': '2020'},
        {'title': 'test movie 10', 'year': '2021'},
    ]
    
    user = User(name=name)
    db.session.add(user)
    for m in movies:
        movie = Movie(title=m['title'], year=m['year'])
        db.session.add(movie)
    
    db.session.commit()
    click.echo('Done.')


# Create a new table in db, name is user, contains username and hashed password
class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(20))
    username = db.Column(db.String(20))
    password_hash = db.Column(db.String(128))

    # Set password using build-in function hash
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    # Validate the password using the build-in function check hash
    def validate_password(self, password):
        return check_password_hash(self.password_hash, password)


# Create a admin account
@app.cli.command()
@click.option('--username', prompt=True, help='The username used to login.')
@click.option('--password', prompt=True, hide_input=True, confirmation_prompt=True, help='The password used to login.')
def admin(username, password):
    db.create_all()

    # If exist, just update it, create a new one otherwise
    user = User.query.first()
    if user is not None:
        click.echo('Updating user...')
        user.username = username
        user.set_password(password)
    else:
        click.echo('Creating user...')
        user = User(username=username, name='Admin')
        user.set_password(password)
        db.session.add(user)
    
    db.session.commit()
    click.echo('Done')


# Create a new table in db, name is movie, contains movie title and year
class Movie(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(60))
    year = db.Column(db.String(4))


# So we don't have to pass user variable to pages everytime
@app.context_processor
def inject_user():
    user = User.query.first()
    return dict(user=user)


# Login page
@app.route('/login', methods=['GET', 'POST'])
def login():
    # Accept only post request
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        # If any of username and password is blank, push notification,
        # return to login page
        if not username or not password:
            flash('Invalid input.')
            return redirect(url_for('login'))

        user = User.query.first()
        # Entered username and password, validate
        # return to login page if they are not valid
        if username == user.username and user.validate_password(password):
            login_user(user)
            flash('Login success')
            return redirect(url_for('index'))

        flash('Invalid username or password.')
        return redirect(url_for('login'))
    
    return render_template('login.html')


# Logout page, return to index page
@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Loged out.')
    return redirect(url_for('index'))


# Main page
@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        if not current_user.is_authenticated:
            return redirect(url_for('index'))
        # Get datas, pass by 'name'
        title = request.form.get('title')
        year = request.form.get('year')
        # Validate
        if not title or not year or len(year) > 4 or len(title) > 60:
            flash('Invalid input.')
            return redirect(url_for('index'))
        # store into database
        movie = Movie(title=title, year=year)
        db.session.add(movie)
        db.session.commit()
        flash('Item created.')
        return redirect(url_for('index'))
    #user = User.query.first()
    movies = Movie.query.all()
    return render_template('index.html', movies=movies)


# Settings page
@app.route('/settings', methods=['GET', 'POST'])
@login_required
def settings():
    if request.method == 'POST':
        name = request.form['name']
    
        if not name or len(name) > 20:
            flash('Invalid input.')
            return redirect(url_for('settings'))
        
        current_user.name = name
        db.session.commit()
        flash('Setting updated.')
        return redirect(url_for('index'))
    
    return render_template('settings.html')


# 404 page
@app.errorhandler(404)
def page_not_found(e): # Accept error object
    #user = User.query.first()
    return render_template('404.html'), 404


# Movie edit page
@app.route('/movie/edit/<int:movie_id>', methods=['GET', 'POST'])
@login_required
def edit(movie_id):
    movie = Movie.query.get_or_404(movie_id)

    if request.method == 'POST':
        title = request.form['title']
        year = request.form['year']
        
        if not title or not year or len(year) != 4 or len(title) > 60:
            flash('Invalid input.')
            return redirect(url_for('edit', movie_id=movie_id))
        
        # Update
        movie.title = title
        movie.year = year
        db.session.commit()
        flash('Item updated.')
        return redirect(url_for('index'))
    
    return render_template('edit.html', movie=movie)


# delete page, post only
@app.route('/movie/delete/<int:movie_id>', methods=['POST'])
@login_required
def delete(movie_id):
    movie = Movie.query.get_or_404(movie_id)
    db.session.delete(movie)
    db.session.commit()
    flash('Item deleted.')
    return redirect(url_for('index'))    