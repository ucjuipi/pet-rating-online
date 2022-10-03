
import pymysql

from flask import Flask, request, session, flash

from flask_bootstrap import Bootstrap
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
from flask_babel import Babel
from flask_socketio import SocketIO
from config import Config
from flask_cors import CORS, cross_origin

app = Flask(__name__)

#CORS(app)
CORS(app, resources={r"/*": {"cors_allowed_origins":"*"} } )

#app.config['BABEL_DEFAULT_LOCALE'] = 'fin'
#app.config['BABEL_TRANSLATION_DIRECTORIES'] ='C:/Users/Timo/git/pet-rating/app/translations'
babel = Babel(app)

@babel.localeselector
def get_locale():
    if request.args.get('lang'):

        session['lang'] = request.args.get('lang')
        
        if session['lang'] == 'en':
            session['language'] = 'English'

        if session['lang'] == 'fi':
            session['language'] = 'Finnish'

        if session['lang'] == 'fa':
            session['language'] = 'Persian'

        if session['lang'] == 'el':
            session['language'] = 'Greek'
            
        if session['lang'] == 'it':
            session['language'] = 'Italian'
    
        if session['lang'] == 'zh':
            session['language'] = 'Chinese'
    
    return session.get('lang', 'en')


"""
@babel.localeselector
def get_locale():

    if session:
        
        return 'fi'
        
    else:
        
        return 'en'
"""
"""
@babel.localeselector
def get_locale():
    return request.accept_languages.best_match(app.config['LANGUAGES'])

"""



#mariabd mysql portti 3306 tarkista?

Bootstrap(app)
app.config.from_object(Config)
db = SQLAlchemy(app)
migrate = Migrate(app, db)
login = LoginManager(app)
login.login_view = 'login'

# Run flask app with socketIO
socketio = SocketIO(app, cors_allowed_origins="*")
# socketio = SocketIO()
socketio.init_app(app)

# Register blueprints
from .task.views import task_blueprint
from .experiment.views import experiment_blueprint
from .create.views import create_blueprint

app.register_blueprint(task_blueprint)
app.register_blueprint(experiment_blueprint)
app.register_blueprint(create_blueprint)

app.secret_key = 'random string'
"""app.secret_key = os.urandom(24)"""

app.jinja_env.auto_reload = True

from app import routes, models
