from flask_restful import Resource
from config import Constrant
from config import Validation
from config import DB
import os

class GetHistory(Resource):
    def post(self):
        args = Validation.getHistoryValidation()
        access_token = args["access_token"]
        q = "SELECT * FROM `tbl_auth_token` WHERE `access_token` = '"+access_token+"'"
        DB.mycursor.execute(q)
        user_record = DB.mycursor.fetchone()

        if user_record == None:
            return {'status':0,'message':Constrant.Arg["invalid_access_er"]}
        else:
            user_id = user_record[1]
            q = f"SELECT * FROM `tbl_business_details` WHERE `user_id` = '{user_id}'"
            DB.mycursor.execute(q)
            histor = DB.mycursor.fetchall()
            response = []

            for row in histor:
                dt = row[12]
                place_id = row[3]
                file_path = 'static/reviews/'+place_id+".csv"
                review_url =  Constrant.config["baseUrl"]+file_path

                if os.path.exists(file_path):
                    item = {
                    "id" : row[0],
                    "name" : row[1],
                    "place_id" : place_id,
                    "address" : row[4],
                    "website" : row[5],
                    "phone" : row[6],
                    "logo" : row[7],
                    "reting" : float(row[8]),
                    "total_reviews" : row[9],
                    "lat" : float(row[10]),
                    "long" : float(row[11]),
                    "created_at" : dt.strftime('%Y-%m-%d %H:%M:%S'),
                    "review_download_link":review_url
                    }
                    response.append(item)

        return {"status":1,'data':response}
            