from os import getenv, name
from flask import Flask
# from flask_cors import CORS


def create_app():
    appl = Flask(__name__)
    appl.secret_key = getenv("FLASK_API_KEY")
    # CORS(appl)
    from api import api
    appl.register_blueprint(api)
    return appl

if __name__ == "__main__":
    app = create_app()
    app.run(debug=True if name.upper() == 'NT' else False)
