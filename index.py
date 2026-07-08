"""Vercel entrypoint.

Vercel's Python runtime looks for a top-level variable named `app` in one
of a few supported files (app.py, index.py, server.py, main.py, wsgi.py,
asgi.py) at the project root. This file just imports the Flask app
created by the application factory in app/__init__.py and exposes it
under that name so Vercel can run it as a WSGI application.

Locally, keep using `python run.py` — this file is only needed for
Vercel's build/runtime detection.
"""

from app import create_app

app = create_app()
