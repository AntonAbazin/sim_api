from flask import Blueprint

bp = Blueprint('app', __name__)

from app.api import routes