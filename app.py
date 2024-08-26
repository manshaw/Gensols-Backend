from flask import Flask,request,jsonify
from flask_restful import Api,abort
from flask_jwt_extended import JWTManager
from config import Constrant
from config import DB
from flask_cors import CORS
from apis import AuthWithGoogle, Logout,Profiles, Reviews,Reviewss, History, ReviewsChatGPT
from dotenv import load_dotenv
import os

load_dotenv()

app = Flask(__name__)
api = Api(app)

app.config["JWT_SECRET_KEY"] = os.getenv("JWT_KEY")
jwt = JWTManager(app)

# To allow this domain
CORS(app, origins=["http://localhost:3000"])

@app.route("/")
def start():
    return "Working Fine"

@app.before_request
def gather_request_data():
    protected_links = [
        "logout_user",
        "get_profile_data",
        "get_business_details",
        "get_reviews",
        "get_history"
    ]
    api_name = request.url.split("/")[-1]

    if api_name in protected_links:
        try:
            data = request.get_json(force=True)

            if data is None or "access_token" not in data:
                abort(401, message="Invalid access token")
            else:
                access_tok = data["access_token"]
                q = "SELECT id FROM tbl_auth_token WHERE access_token = '"+access_tok+"'"
                DB.mycursor.execute(q)
                user_record = DB.mycursor.fetchone()

                if user_record == None:
                    abort(401, message="Invalid access token")
        except Exception as e:
            return jsonify({"message": str(e)}), 400

# =============== Accessable without JWT verification =====================
api.add_resource(AuthWithGoogle.UserAuth,'/user_auth')


# =============== JWT verification is required <access_token> ==============
api.add_resource(Logout.LogoutUser,'/logout_user')
api.add_resource(Profiles.Profile,'/get_profile_data')
api.add_resource(Profiles.BusinessProfile,'/get_business_details')
api.add_resource(Reviews.GetReviews,'/get_reviews')
api.add_resource(Reviewss.GetReviewss,'/get_reviewss')
api.add_resource(ReviewsChatGPT.GetReviewsChatGPT,'/filtered_reviews')
api.add_resource(History.GetHistory,'/get_history')
