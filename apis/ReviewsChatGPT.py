from flask_restful import Resource
from config import Validation
from ChatGPT import ChatGPT
import threading

class GetReviewsChatGPT(Resource):

    def post(self):
        args = Validation.validReviewsChatGPTInput()
        reviews = args.get("reviews")
        data = ChatGPT.filter_and_convert_data(reviews)
        results = [None]
        thread = threading.Thread(target=ChatGPT.recursive_api_call_handler, args=(data,results, 0))
        thread.start()
        thread.join()
        responses_list = ChatGPT.response_to_json(results[0])
        if len(reviews) > 0:
            return {"status":200,"message":"success", "data":responses_list}
        else:
            return {"status":400,"message":"error", "data":[]}
        