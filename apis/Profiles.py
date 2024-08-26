from flask import Flask,url_for
from flask_restful import Resource
from config import Constrant
from config import Validation
from config import DB
import os


class Profile(Resource):
    def post(self):
        args = Validation.getProfileData()
        user_id = args.get("user_id")

        q = "SELECT * FROM tbl_user WHERE id = '"+user_id+"'"
        DB.mycursor.execute(q)
        user_record = DB.mycursor.fetchone()
        
        if user_record == None:
           return {
              "status":0,
              "message":"Record not found!"
           }
        else:   
           dt = user_record[6]
           return {
               "status":1,
               "message":"Action successfull",
                "user":{
                    "id" : user_record[0],
                    "google_id" : user_record[1],
                    "name" : user_record[2],
                    "email" : user_record[3],
                    "image" : user_record[4],
                    "created_at" : dt.strftime('%Y-%m-%d %H:%M:%S'),
                }
           }
    

class BusinessProfile(Resource):
    def post(self):
        args = Validation.getBusinessProfile()
        user_id = args.get("user_id")
        place_id = args.get("place_id")

        q = "SELECT * FROM `tbl_business_details` WHERE `user_id` = '"+user_id+"' AND `place_id` = '"+place_id+"'"
        DB.mycursor.execute(q)
        user_record = DB.mycursor.fetchone()

        place_id = user_record[3]
        file_path = 'static/reviews/'+place_id+".csv"
        review_url = ''
        
        if os.path.exists(file_path):
           review_url =  Constrant.config["baseUrl"]+file_path
        else:
            review_url = ''
        
        if user_record == None:
           return {
              "status":0,
              "message":"Record not found!"
           }
        else:   
           dt = user_record[12]
           return {
               "status":1,
               "message":"Action successfull",
                "user":{
                    "id" : user_record[0],
                    "name" : user_record[1],
                    "place_id" : user_record[3],
                    "address" : user_record[4],
                    "site" : user_record[5],
                    "phone" : user_record[6],
                    "logo" : user_record[7],
                    "rating" : float(user_record[8]),
                    "total_reviews" : user_record[9],
                    "location":{
                        "latitude" : user_record[10],
                        "longitude" : user_record[11]
                    },
                    "created_at" : dt.strftime('%Y-%m-%d %H:%M:%S'),
                    "reviews_download_link":review_url
                }
           }