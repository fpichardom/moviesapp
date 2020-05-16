import os
import numpy as np
from datetime import datetime
from flask import Flask, render_template, request, redirect, flash
from flask_sqlalchemy import SQLAlchemy
from flask_bootstrap import Bootstrap
from flask_wtf import FlaskForm
from wtforms import RadioField, SubmitField, SelectField, StringField
from wtforms.validators import DataRequired
from imdb import IMDb
#from tinydb import TinyDB, Query
#from tinydb.operations import add


app = Flask(__name__)
Bootstrap(app)

############# Database Settings #############

basedir = os.path.abspath(os.path.dirname(__file__))

app.config['SECRET_KEY'] = 'merenero456perenzejo'
#app.config['SQLALCHEMY_DATABASE_URI'] =\
#    'mysql://fpichardom:theMoviesSupreme@fpichardom.mysql.pythonanywhere-services.com/fpichardom$movies'
app.config['SQLALCHEMY_DATABASE_URI'] =\
    'sqlite:///' + os.path.join(basedir, 'movies.sqlite')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)
####################################

movie_genre = db.Table('movie_genre',
    db.Column('movie_id', db.Integer, db.ForeignKey('movies.id')),
    db.Column('genre_id', db.String(20), db.ForeignKey('genres.genre'))
)

movie_user = db.Table('movie_user',
    db.Column('movie_id', db.Integer, db.ForeignKey('movies.id')),
    db.Column('user_id', db.String(50), db.ForeignKey('users.username'))
)


class Movie(db.Model):

    __tablename__ = 'movies'

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), index=True)
    year = db.Column(db.Integer)
    cover_url = db.Column(db.String(150))
    plot = db.Column(db.Text)
    movie_id = db.Column(db.String(10), unique=True, index=True)
    imdb_id = db.Column(db.String(10), unique=True)
    entry_date = db.Column(db.DateTime)
    is_current = db.Column(db.Boolean, default=False)
    seen= db.Column(db.Boolean, default=False)
    genres = db.relationship('Genre',
                             secondary=movie_genre,
                             backref=db.backref('movies', lazy='dynamic'),
                             lazy='dynamic')
    users = db.relationship('User',
                             secondary=movie_user,
                             backref=db.backref('movies', lazy='dynamic'),
                             lazy='dynamic')


    def __repr__(self):
        return '<Movie {} {}>'.format(self.title, self.year)



class Genre(db.Model):

    __tablename__ = 'genres'

    #id = db.Column(db.Integer, primary_key=True)
    genre = db.Column(db.String(20), primary_key=True)

    def __repr__(self):
        return '<Genre {}>'.format(self.genre)


class User(db.Model):

    __tablename__ = 'users'

    #id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), primary_key=True)
    randomize = db.Column(db.Boolean, default=True)
    password = db.Column(db.String(50), default='try your luck')

    def __repr__(self):
        return ' <User {}>'.format(self.username)




ia = IMDb()
#db = TinyDB('./db/movies.json')

def create_choices(movie_results):
    choices = []
    for i, movie in enumerate(movie_results):
        movie_name = '{} ({})'.format(movie.get('title', 'Unknown'), movie.get('year', 'Unknown'))
        choices.append((movie.movieID,'<a href=https://www.imdb.com/title/tt{} target=_blank>{}</a>'.format(ia.get_imdbID(movie), movie_name)))
        #choices.append((movie.movieID, movie_name))
    return choices

def check_int(string):
    try:
        return int(string)
    except ValueError:
        return None

def include_get_genre(genre):
    if Genre.query.get(genre):
        pass
    else:
        new_genre = Genre(genre=genre)
        db.session.add(new_genre)
        db.session.commit()
    return Genre.query.get(genre)

def set_new_current():
    old_current = Movie.query.filter_by(is_current=True).first()
    if old_current:
        old_current.is_current = False
        db.session.add(old_current)
        db.session.commit()
    picked_movie = None
    all_users = list(User.query.all())
    while not picked_movie:
        chosen_user = np.random.choice(all_users,1)
        movies = Movie.query.filter(Movie.users.any(username=chosen_user[0].username)).all()
        if movies:
            picked_movie = np.random.choice(movies,1)[0]
        else:
            picked_movie = None
    picked_movie.is_current = True
    db.session.add(picked_movie)
    db.session.commit()




# def include_get_user(user):
#     if User.query.get(user):
#         pass
#     else:
#         new_user = User(username=user)
#         db.session.add(new_user)
#         db.session.commit()
#     return User.query.get(user)



## Forms
class MoviePicker(FlaskForm):
    # users = [
    #     ('Fritz', 'Fritz'),
    #     ('Natasza', 'Natasza'),
    #     ('Chace', 'Chace'),
    #     ('Rachael', 'Rachael'),
    #     ('Melanie', 'Melanie'),
    #     ('Oscar', 'Oscar'),
    #     ('Cynthia', 'Cynthia')
    # ]
    user = SelectField('User', validators=[DataRequired()]) # choices=sorted(users) , validators=[DataRequired()]
    select_movie = RadioField('Select Movie', validators=[DataRequired()]) # , validators=[DataRequired()]
    submit = SubmitField('Add New Movie')

class RandomForm(FlaskForm):
    user = SelectField('User',
        validators=[DataRequired()],
        choices=sorted([(user.username, user.username) for user in User.query.all()])) # choices=sorted(users) , validators=[DataRequired()]
    password = StringField('Keyword', validators=[DataRequired()], render_kw={"placeholder": "try your luck"})


### Routes #############

@app.route("/", methods=['GET','POST'])
def index():
    form = MoviePicker()
    if request.method == 'GET':
        movie_name = request.args.get('movie_name','')
        if movie_name != '':
            movie_results = ia.search_movie(movie_name)
            choices = create_choices(movie_results[:6])
            #form.choices = [('MadMax',0),('Interstellar',1)]
            #form.select_movie.choices = [('MadMax',0),('Interstellar',1)]
            form.select_movie.choices = choices
            form.user.choices = sorted([(user.username, user.username) for user in User.query.all()])
            return render_template('index.html', movie_name=movie_name, form=form)
        return render_template('index.html', movie_name=movie_name)
    if request.method == 'POST':
        #if form.validate_on_submit():
        if form.select_movie.data:
            selected_movie = ia.get_movie(form.select_movie.data)
            flash('Your movie has been added. :)')
            # selected_movie = movie_results[int(form.select_movie.data)]
            # ia.update(selected_movie, info=['main', 'plot'])
            movie = Movie.query.filter_by(movie_id=selected_movie.movieID).first()
            user = User.query.get(form.user.data)
            if not movie:
                new_movie = Movie()
                for genre in selected_movie.get('genres'):
                    new_movie.genres.append(include_get_genre(genre))
                new_movie.title = selected_movie.get('title')
                new_movie.year = check_int(selected_movie.get('year'))
                new_movie.cover_url = selected_movie.get('cover url')
                new_movie.plot = selected_movie.get('plot outline')
                new_movie.movie_id = selected_movie.movieID
                new_movie.imdb_id = ia.get_imdbID(selected_movie)
                new_movie.users.append(user)
                new_movie.entry_date = datetime.utcnow()
                new_movie.is_current = False
                new_movie.seen = False
                db.session.add(new_movie)
                db.session.commit()
            elif user not in movie.users:
                movie.users.append(user)
                db.session.add(movie)
                db.session.commit()



            # new_movie = {
            #     'title': selected_movie.get('title'),
            #     'year': selected_movie.get('year'),
            #     'genres': selected_movie.get('genres'),
            #     'cover_url': selected_movie.get('cover url'),
            #     'plot': selected_movie.get('plot outline'),
            #     'movie_id': selected_movie.movieID,
            #     'imdb_id': ia.get_imdbID(selected_movie),
            #     'users': [form.user.data]
            # }
            # Movie= Query()
            # if not db.search(Movie.movie_id == new_movie['movie_id']):
            #     db.insert(new_movie)
            # elif db.search((Movie.movie_id == new_movie['movie_id']) & (~Movie.users.any(new_movie['users']))):
            #     db.update(add('users', new_movie['users'] ))
        return redirect('/')

@app.route("/movies")
def movies():
    #all_movies = db.all()
    all_movies = list(Movie.query.all())
    return render_template('movies.html', all_movies=all_movies)

@app.route("/randomizer", methods=['GET','POST'])
def randomizer():
    form = RandomForm()
    current_movie = Movie.query.filter_by(is_current=True).first()
    randomization_trials = len(list(User.query.filter_by(randomize=True)))
    return render_template('randomizer.html', form=form, current_movie=current_movie, randomization_trials=randomization_trials)


@app.route("/randomizer/randomize", methods=['GET','POST'])
def randomize():
    form = RandomForm()
    if form.user.data:
        user = User.query.get(form.user.data)
        if user.randomize:
            if form.password.data == 'try your luck':
                set_new_current()
                user.randomize = False
                db.session.add(user)
                db.session.commit()
                flash('New movie set, hope is a good one')
            else:
                flash('Try again with new keyword')
        else:
            flash('Sorry you have used all your randomization events')
    return redirect("/randomizer")

@app.route("/randomizer/bail/<user>")
def bail(user):
    user = User.query.get(user)
    if user.randomize:
        user.randomize = False
        db.session.add(user)
        db.session.commit()
    return redirect("/movies")
