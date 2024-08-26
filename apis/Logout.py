from flask_restful import Resource
from config import Constrant
from config import Validation
from config import DB


class LogoutUser(Resource):
    def post(self):
      args = Validation.logoutVerify()

      if "message" not in args:
        user_id = args.get("user_id")
        access_token = args.get("access_token")

        sql = "DELETE FROM tbl_auth_token WHERE user_id = "+user_id+" AND access_token = '"+access_token+"'"
        print(sql)
        DB.mycursor.execute(sql)
        DB.mydb.commit()

        return {
           'status' : 1,
           'message' : Constrant.Arg["logout_msg"]
        }

      else:
         return args