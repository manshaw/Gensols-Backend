from flask_restful import Resource,reqparse
from config import Validation
from datetime import datetime
from config import DB
from flask import Flask,jsonify
import requests
from flask_jwt_extended import create_access_token

class UserAuth(Resource):
    def post(self):
        args = Validation.googleAuth()
        print(args)
        now = datetime.now()
        c_date = now.strftime("%Y-%m-%d %H:%M:%S")
        error_resp = {'status':0,'message':"Invalid access token"}

        if "message" not in args:
            access_token = args.get("access_token")
            url = "https://www.googleapis.com/oauth2/v3/userinfo?access_token="+access_token
            response = requests.get(url)
            print(response)
            if response.status_code == 200:
                data = response.json()
                if "sub" in data:
                    google_id = data.get("sub")
                    full_name = data.get("name")
                    image = data.get("picture")
                    email = data.get("email")
                    
                    DB.mycursor.execute("SELECT * FROM tbl_user WHERE email = '"+email+"' AND google_id = '"+google_id+"'")
                    checkUser = DB.mycursor.fetchone()

                    if checkUser != None:
                       user_id = checkUser[0]
                       sql = "UPDATE tbl_user SET access_token = '"+access_token+"' WHERE id = "+str(user_id)
                       DB.mycursor.execute(sql)
                       DB.mydb.commit()
                       
                       access_jwt = create_access_token(identity=google_id+"_"+str(user_id))
                       q = "SELECT * FROM tbl_auth_token WHERE user_id = "+str(user_id)
                       DB.mycursor.execute(q)
                       myresult = DB.mycursor.fetchone()

                       if myresult == None:
                            sql = "INSERT INTO tbl_auth_token (user_id, access_token,created_at) VALUES (%s, %s,%s)"
                            val = (user_id, access_jwt,c_date)
                            DB.mycursor.execute(sql, val)
                            DB.mydb.commit()
                       else:
                            sql = "UPDATE tbl_auth_token SET access_token = '"+access_jwt+"', created_at = '"+c_date+"' WHERE user_id = "+str(user_id)
                            DB.mycursor.execute(sql)
                            DB.mydb.commit()

                       return {
                            "status":1,
                            "access_token": access_jwt,
                            "message":"Login successful",
                            "user":{
                                "id":user_id,
                                "name":full_name,
                                "email":email,
                                "image":image,
                            }
                        }
                                    
                    else:
                        q = "INSERT INTO tbl_user (name, email,access_token,created_at,google_id,image) VALUES (%s, %s,%s,%s,%s,%s)"
                        val = (full_name, email,access_token,c_date,google_id,image)
                        DB.mycursor.execute(q, val)
                        DB.mydb.commit()

                        user_id = DB.mycursor.lastrowid
                        access_jwt = create_access_token(identity=google_id+"_"+str(user_id))

                        sql = "INSERT INTO tbl_auth_token (user_id, access_token,created_at) VALUES (%s, %s,%s)"
                        val = (user_id, access_jwt,c_date)
                        DB.mycursor.execute(sql, val)
                        DB.mydb.commit()

                        return {
                            'status':1,
                            "access_token": access_jwt,
                            'message':"Account created successfully",
                            'user':{
                               'google_id':google_id,
                               "name":full_name,
                               'email':email,
                               'image':image
                            }
                        }
                else:
                    return error_resp
            else:
                return error_resp

        else:
            return jsonify(args)
        