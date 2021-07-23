import subprocess
import os
import inspect
from flask import Flask, Blueprint
from flask_cors import CORS
from . import db
from . import BP


def create_app():
    # create and cofigure the app
    app = Flask(__name__, instance_relative_config=True)

    if app.config["ENV"] == 'production':
        subprocess.run('/srv/cron/setup_cron.sh', shell=True)
        app.logger.debug(
            '\033[01;07:m executed: /srv/cron/setup_cron.sh \033[m')
    CORS(app)
    app.teardown_appcontext(db.close_db)

    # ensure the instance folder exists
    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass

    # register blueprints
    with app.app_context():
        def predic(m): return inspect.isclass(m) and issubclass(m, Blueprint)
        for name, bpclass in inspect.getmembers(BP, predic):
            bp = bpclass()
            app.logger.debug(
                f'\033[01;07:mBLUEPRINT REGISTERED: {bp.url_prefix}\033[m')
            app.register_blueprint(bp)

    app.get('/')(readme)

    return app


def readme():
    return 'readme(to do)'
