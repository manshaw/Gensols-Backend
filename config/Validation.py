from flask_restful import Resource,reqparse
from config import Constrant

parser = reqparse.RequestParser()

def signupVerify():
    parser.add_argument('name', required=True, type=str, help=Constrant.Arg["name_req"])
    parser.add_argument('email', required=True, type=str, help=Constrant.Arg["email_req"])
    parser.add_argument('access_token', required=True, type=str, help=Constrant.Arg["access_req"])
    return parser.parse_args()


def loginVerify():
    parser.add_argument('email', required=True, type=str, help=Constrant.Arg["email_req"])
    parser.add_argument('access_token', required=True, type=str, help=Constrant.Arg["access_req"])
    return parser.parse_args()

def logoutVerify():
    parser.add_argument('user_id', required=True, type=str, help=Constrant.Arg["invalid_data"])
    parser.add_argument('access_token', required=True, type=str)
    return parser.parse_args()

def googleAuth():
    parser.add_argument('access_token', required=True, type=str,help=Constrant.Arg["access_req"]),
    return parser.parse_args()

def validReviewsInput():
    parser.add_argument('place_id', required=True, type=str,help=Constrant.Arg["empty_field"]),
    parser.add_argument('review_count', required=True, type=int,help=Constrant.Arg["empty_field"]),
    parser.add_argument('access_token', required=True, type=str,help=Constrant.Arg["empty_field"]),
    parser.add_argument('reviews_exist', required=True, type=str,help=Constrant.Arg["empty_field"]),
    return parser.parse_args()

def validReviewssInput():
    parser.add_argument('place_id', required=True, type=str,help=Constrant.Arg["empty_field"]),
    parser.add_argument('access_token', required=True, type=str,help=Constrant.Arg["empty_field"]),
    parser.add_argument('start_date', required=True, type=str,help=Constrant.Arg["empty_field"]),
    parser.add_argument('end_date', required=True, type=str,help=Constrant.Arg["empty_field"]),
    # parser.add_argument('menu_items', required=True, type=list, action='append',help=Constrant.Arg["empty_field"]),
    parser.add_argument('gpt_modal', required=True, type=str,help=Constrant.Arg["empty_field"]),
    return parser.parse_args()

def getProfileData():
    parser.add_argument('user_id', required=True, type=str,help=Constrant.Arg["access_req"]),
    return parser.parse_args()

def getBusinessProfile():
    parser.add_argument('user_id', required=True, type=str,help=Constrant.Arg["access_req"]),
    parser.add_argument('place_id', required=True, type=str,help=Constrant.Arg["access_req"]),
    return parser.parse_args()


def getHistoryValidation():
    parser.add_argument('access_token', required=True, type=str,help=Constrant.Arg["access_req"]),
    return parser.parse_args()

def validReviewsChatGPTInput():
    parser.add_argument('access_token', required=True, type=str,help=Constrant.Arg["access_req"]),
    parser.add_argument('reviews', required=True, type=dict, action='append', help=Constrant.Arg["access_req"]),
    return parser.parse_args()
