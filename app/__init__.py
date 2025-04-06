from flask import Flask
from dotenv import load_dotenv
import os
from app.db import init_db

def create_app():
    load_dotenv()

    app = Flask(__name__)
    app.config['SECRET_KEY'] = os.getenv("FLASK_SECRET_KEY", "supersecret")

    app.config['SQLALCHEMY_DATABASE_URI'] = (
        f"postgresql://{os.getenv('DB_USER')}:{os.getenv('DB_PASSWORD')}"
        f"@{os.getenv('DB_HOST')}:{os.getenv('DB_PORT')}/{os.getenv('DB_NAME')}"
    )
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    # Init DB
    init_db(app)

    # Register blueprint
    from app.routes import main
    app.register_blueprint(main)

    # ✅ Now safe to use
    @app.context_processor
    def inject_globals():
        return {
            'WP_URL': os.getenv("WP_SITE_URL")
        }

    return app
