from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_smorest import Api
# from database import db

# Create app function for the multiple batch testing approach
def create_app():
    app = Flask(__name__)
    # vv this line vv is to comm between react + flask..?
    CORS(app)

    app.config["API_TITLE"] = "Predicative demand intelligence for ride-sharing operators"
    app.config["API_VERSION"] = "s1"
    app.config["OPENAPI_VERSION"] = "3.0.2"

    # start database here
    # afhghearuiohgorgh

    api = Api(app)
    # api.register_blueprint()

    @app.route("/")
    def hello():
        return jsonify({"testMessage": "Backend successfully running!"})
    
    return app


app = create_app()

if __name__ == "__main__":
    app.run(debug=True)