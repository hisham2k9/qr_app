from flaskApp import app
# Expose the Flask app as "application" (WSGI standard)
application = app

if __name__ == "__main__":
    application.run()