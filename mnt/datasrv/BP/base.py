from .. import db
from flask import (
    Blueprint,
    current_app as app)
import os


class Base(Blueprint):
    '''
    Usage:

    ------------------------------------------------
    from .base import Base


    class test(Base):

        def __init__(self):
            super().__init__("name")
            self.add_routes('/')(self.hello)

        def hello(self):
            return "hello"

    ------------------------------------------------
    Don't forget add import statement to __init__.py
    '''

    def __init__(self, name):

        super().__init__(
            name,
            __name__,
            url_prefix=f'/{name}',
            template_folder=f'templates/{name}'
        )
        self.DB_PATH = os.path.join(app.instance_path, f'{self.name}.sqlite')
        self.DB_SCHEMA = f'schema/{self.name}.sql'

        self.add_command("initdb")(self.initdb)

    def add_command(self, cmd):
        def set_command(f):
            self.cli.command(cmd)(f)
        return set_command

    def _get_db(self):
        return db.get_db(self.DB_PATH)

    def initdb(self):
        if os.path.exists(self.DB_PATH):
            print(f'🤢 {self.name} database is already exist. 🌩️')
            return
        con = db.get_db(self.DB_PATH)
        with app.open_resource(self.DB_SCHEMA, 'rt') as f:
            con.executescript(f.read())
        print(f'🌟Initialized {self.name} database.🌟')
