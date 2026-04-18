import sys
import os

# Path to your project directory
path = '/home/hisham2k9/qr_root/qr_app'
if path not in sys.path:
    sys.path.insert(0, path)


from flaskApp import app
# Expose the Flask app as "application" (WSGI standard)
application = app

if __name__ == "__main__":
    application.run()