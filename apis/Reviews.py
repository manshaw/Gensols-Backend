from flask_restful import Resource
from config import Constrant
from config import Validation
from config import DB
from openai import OpenAI
import requests
from datetime import datetime
from outscraper import ApiClient
import csv
from Helper import Helper
import os
import pandas as pd
import threading
from flask import jsonify
import json


class GetReviews(Resource):
    def post(self):

        places_key = os.getenv("GOOGLE_PLACES_KEY")
        outscraper_key = os.getenv("OUTSCRAPER_KEY")
        args = Validation.validReviewsInput()
        now = datetime.now()
        c_date = now.strftime("%Y-%m-%d %H:%M:%S")

        access_token = args.get("access_token")
        place_id = args.get("place_id")
        review_count = args.get("review_count")
        reviews_exist = args.get("reviews_exist")

        path = place_id+".csv"
        csv_file_path = 'static/reviews/'+path
        client = ApiClient(api_key=outscraper_key)

        reviews = client.google_maps_reviews(place_id, reviews_limit=review_count, language='en')
        

        # Incase review exist
        if reviews_exist == 'null' and os.path.isfile(csv_file_path):
            return {"status":2,"message":Constrant.Arg["reviews_exist"]}
        
        # User want to use the old review
        elif reviews_exist == 'yes' and os.path.isfile(csv_file_path):
            try:
                file_path = place_id+'.csv'
                access_csv = Helper.processReviewCsv(file_path)
                if access_csv["status"] == 1:
                   review_data = access_csv["data"]
                else:
                   return access_csv
            except:
                return {'status':0,'message':'Something went wrong try again'}
            

        # User want to get new reviews
        else:
            q = "SELECT user_id FROM tbl_auth_token WHERE access_token = '"+access_token+"'"
            DB.mycursor.execute(q)
            user_record = DB.mycursor.fetchone()

            if user_record != None:
                user_id = user_record[0]
                client = ApiClient(api_key=outscraper_key)
                print("CALL SENT")
                reviews = client.google_maps_reviews(place_id, reviews_limit=review_count, language='en')
                return reviews
                if len(reviews[0].get("reviews_data")) > 0:
                    data = reviews[0]
                    totla_reviews = data.get("reviews_data") 
                    business_id = 0 

                    q = "SELECT id FROM `tbl_business_details` WHERE `user_id` = '"+str(user_id)+"' AND `place_id` = '"+str(place_id)+"'"
                    DB.mycursor.execute(q)
                    check_business = DB.mycursor.fetchone()
                    
                    if check_business == None:
                        sql = "INSERT INTO tbl_business_details (name,user_id,place_id,address,site,phone,logo,rating,total_reviews,latitude,longitude,created_at) VALUES (%s,%s, %s,%s,%s, %s,%s,%s, %s,%s,%s, %s)"
                        val = (data.get("name"),user_id,data.get("place_id"),data.get("full_address"),data.get("site"),data.get("phone"),data.get("logo"),data.get("rating"),data.get("reviews"),data.get("latitude"),data.get("longitude"),c_date)
                        DB.mycursor.execute(sql, val)
                        DB.mydb.commit()
                        business_id = DB.mycursor.lastrowid
                    else:
                        business_id = check_business[0]

                    review_data = []

                    for item in totla_reviews:
                        review_str = Helper.preprocess_text(item.get("review_text"))

                        row = {
                                "review_id" : item.get("review_id"),
                                "author_title" : item.get("author_title"),
                                "author_id" : item.get("author_id"),
                                "author_image" : item.get("author_image"),
                                "review_text" : review_str,
                                "review_rating" : item.get("review_rating"),
                                "review_datetime_utc" : item.get("review_datetime_utc"),
                        }

                        if Helper.isEmtpy(review_str) == False:
                            review_data.append(row)

                    # try:
                    #    filename = "static/reviews/"+place_id+".csv"
                    #    csvtags = ['review_id','author_title','author_id','author_image','review_text','review_rating','review_datetime_utc']
                    #    with open(filename, 'w', newline='') as file:
                    #       writer = csv.DictWriter(file, delimiter=';', fieldnames=csvtags)
                    #       writer.writeheader()
                    #       writer.writerows(review_data)
                    # except:
                    #    return {'status':0,'message':Constrant.Arg["csv_gen_error"]}

                else:
                    return {"status":"0","message":Constrant.Arg["invalid_data"]},400

            else:
                return {"status":"0","message":Constrant.Arg["invalid_data"]},400
            
            
        file_raw= pd.DataFrame(review_data)
        file = Helper.filer_and_clean_data(file_raw)        
        cost = Helper.cost_calculations(file)
        prompts = Helper.divide_file_in_chunks(500, file)
        results = [None]
        thread = threading.Thread(target=Helper.recursive_api_call_handler, args=(prompts,results, 0))
        thread.start()
        thread.join()
        responses_list = Helper.response_to_json(results[0])
        result = Helper.chatgpt_final_result(prompts, responses_list, file)        
        print(result.explode('ratings'))
        # result.to_csv("rating_results.csv", index=False)
        rating_by_date = Helper.process_ratings(result)
        print(rating_by_date)
        rating_by_date['review_date'] = rating_by_date['review_date'].astype(str)
        rating_by_date_json = rating_by_date.to_json(orient='records')
        rense = {
            "reviews": review_data,
            "cost": cost,
            "rating_by_date": json.loads(rating_by_date_json)
        }    
        
        return {"status":1,"message":"success","data":rense},200

      # client = OpenAI(api_key=os.getenv("CHATGPT_KEY"))
      # model = "gpt-4o"
      # messages = [
      #            {"role":"user","content":"Write 1 lines paragraph and sentence must be consit of 5 words"},
      #            {"role":"user","content":"Describe interesting facts about Pakistan"},
      #       ]
      
      # response = client.chat.completions.create(
      #    messages=messages,
      #    model=model
      # )

      # print(response)
      # return {
      #    "result": response.choices[0].message.content
      # }
      
