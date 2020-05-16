from flask import Flask, render_template, request, redirect, flash
from flask_bootstrap import Bootstrap
from flask_wtf import FlaskForm
from wtforms import RadioField, SubmitField, SelectField
from wtforms.validators import DataRequired
from imdb import IMDb
from tinydb import TinyDB, Query
from tinydb.operations import add

app = Flask(__name__)
Bootstrap(app)

app.secret_key = 'merenero456perenzejo'

ia = IMDb()
db = TinyDB('./db/movies.json')

class MoviePicker(FlaskForm):
    users = [
        ('Fritz', 'Fritz'),
        ('Natasza', 'Natasza'),
        ('Chace', 'Chace'),
        ('Rachael', 'Rachael'),
        ('Melanie', 'Melanie'),
        ('Oscar', 'Oscar'),
        ('Cynthia', 'Cynthia')
    ]
    user = SelectField('User', choices=sorted(users)) # , validators=[DataRequired()]
    select_movie = RadioField('Select Movie') # , validators=[DataRequired()]
    submit = SubmitField('Add New Movie')

def create_choices(movie_results):
    choices = []    
    for i, movie in enumerate(movie_results):
        movie_name = '{} ({})'.format(movie.get('title', 'Unknown'), movie.get('year', 'Unknown'))
        choices.append((movie.movieID,'<a href=https://www.imdb.com/title/tt{} target=_blank>{}</a>'.format(ia.get_imdbID(movie), movie_name)))
        #choices.append((movie.movieID, movie_name))
    return choices       


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
            return render_template('index.html', movie_name=movie_name, form=form)
        return render_template('index.html', movie_name=movie_name)
    if request.method == 'POST':
        if form.select_movie.data:
            selected_movie = ia.get_movie(form.select_movie.data)
            flash('Your movie has been added. :)')
            # selected_movie = movie_results[int(form.select_movie.data)]
            # ia.update(selected_movie, info=['main', 'plot'])
            new_movie = {
                'title': selected_movie.get('title'),
                'year': selected_movie.get('year'),
                'genres': selected_movie.get('genres'),
                'cover_url': selected_movie.get('cover url'),
                'plot': selected_movie.get('plot outline'),
                'movie_id': selected_movie.movieID,
                'imdb_id': ia.get_imdbID(selected_movie),
                'users': [form.user.data]
            }
            Movie= Query()
            if not db.search(Movie.movie_id == new_movie['movie_id']):
                db.insert(new_movie)
            elif db.search((Movie.movie_id == new_movie['movie_id']) & (~Movie.users.any(new_movie['users']))):
                db.update(add('users', new_movie['users'] ))
        return redirect('/')

@app.route("/movies")
def movies():
    all_movies = db.all()
    return render_template('movies.html', all_movies=all_movies)