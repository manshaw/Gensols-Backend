from flask_restful import Resource
from config import Validation
from ChatGPT import ChatGPT

class GetReviewss(Resource):
    def post(self):
        args = Validation.validReviewssInput()
        place_id = args.get("place_id")
        start_date = args.get("start_date")
        end_date = args.get("end_date")
        gpt_modal = args.get("gpt_modal")
        review_count = 50
        reviews = ChatGPT.fetch_reviews(place_id, review_count)
        filtered = ChatGPT.filter_and_convert(reviews, start_date, end_date)
        raw = ChatGPT.chatGPT(filtered, gpt_modal)
        system_response = ChatGPT.response_to_json(raw[0])
        g1 = ChatGPT.graph_1(system_response)
        g11 = ChatGPT.graph_11(system_response)
        g3 = ChatGPT.graph_3(system_response)
        g2,g4 = ChatGPT.final_data_cleaning(system_response)
        g5 = ChatGPT.graph_5(g3["data"])
        return {
            "total_reviews":len(reviews),
            "graph_1": g1,
            "graph_11": g11,
            "graph_2": g2,
            "graph_3": g3,
            "graph_4": g4,
            "graph_5": g5,
        }