import logging
import aiohttp
import asyncio
from datetime import datetime
import json
from outscraper import ApiClient
import os
import threading
import pandas as pd
import requests



menu_items = '''
Chicken Shawarma Wrap,
Beef Shawarma Wrap,
Falafel Wrap,
Lamb Shawarma Wrap,
Osmow’s Special Wrap,
Chicken Kebab Wrap,
Philly Chicken Wrap,
Philly Cheese Steak Wrap,
Beef Kofta Wrap,
Beyond Steak Shawarma Wrap,
Beyond Steak Philly Wrap,
Chicken on the ROX,
Chicken on the Stix,
Half and Half Chicken,
Beef on the stix,
Beef on the Rox,
Lamb on the Rox,
Lamb on the stix,
Falafel on the Rox,
Falafel on the stix,
Beyond Steak On The Rox,
Beyond Steak™ On The Stix,
Philly chicken on the Rox,
Philly chicken on the stix,
Philly Cheese steak on the Rox,
Philly Cheese steak on the stix,
Beyond Steak Salad,
Chicken Salad,
Beef Salad,
Lamb Salad,
Falafel Salad,
Philly Chicken Salad,
Philly Chicken Salad,
Philly Cheese steak salad,
Chicken Stix Supreme,
Caesar Salad,
Fattoush Salad,
Greek Salad,
Taboule,
Hummus,
Baklava,
Brownies,
Falafel,
Light & vegan garlic sauce
'''

services='''
Food quality and taste,
Value for money,
Wait time and speed of service,
Cleanliness and hygiene,
Store atmosphere and decor,
Online and mobile ordering experience,
Delivery and takeout service,
Staff friendliness and attentiveness
'''
example_5 = "{'response':[{'Category Name 01':{'sentiment':'positive','theme':'fresh','score':7, 'date':'2024-02-08'}]}"
example_6 = "{'response':[{'Category Name 02':{'sentiment':'negative','theme':'low','score':2, 'date':'2024-02-08'}]}"
example_7 = "{'response':[{'Category Name 03':{'sentiment':'positive','theme':'clean','score':10, 'date':'2024-02-08'}]}"
example_8 = "{'response':[{'Menu Item 01':{'sentiment':'negative','theme':'poor','score':9, 'date':'2024-02-08'}]}"
example_9 = "{'response':[{'Menu Item 02':{'sentiment':'negative','theme':'average','score':2, 'date':'2024-02-08'}]}"
example_10 = "{'response':[{'Menu Item 03':{'sentiment':'positive','theme':'improved','score':4, 'date':'2024-02-08'}]}"
example_11 = '''
{
"response":{
"review_score":8,
"review":{
"review_id":"",
"review_date":"dd-mm-YYYY",
"review_rating":"4.0"
},
"category_name":[
{
"Category Name 01":{
"sentiment":"positive",
"theme":"friendly",
"score":7
}
},
{
"Category Name 02":{
"sentiment":"positive",
"theme":"clean",
"score":10
}
}
],
"menu_name":[
{"Menu Item Name 01":{"sentiment": "negative", "theme": "awfull", "score": 8}}]
}}
'''


system_message = f"""
# Background
Your job is to analyze web reviews of a restaurant. Where review is json object having follwing key value pairs,
* review_text:- actual user review about the restaurant.
* review_date:- date in which user wrote the review.
* review_id:- id provided by google.
* review_rating:- actual review rating given by the user.

You need to analyze three dimensions: a) categories (if available), b)customer service (if available) &  c) over all text & d) menu items .
These dimensions are further split into three sub dimensions: sentiment, theme, score and date of review where date is already provided in the review

* categories:- here is the possible list of categories - stay WITHIN THESE CATEGORIES : separated by,: {services}, - DO NOT add anything out of provided categories list
* menu items:- here is the possible list of menu items - you can add menu item by yourself if found in the review by not in the list of these MENU ITEMS : separated by,: {menu_items}.
* sentiment:- sentiment can be only be positive or negative. It MUST NOT have neutral as value.
* theme:- one word theme, e.g crispy, juicy, expensive, friendly, unprofessional etc.
* score:- ranging from 0 to 10. 10 being the highest. In case of menu items, this score value means user's sentiment level for example sentiment negative with value 0 means user disliked the menu item but dislikness was not too much whereas sentiment negative with value 10 means user hated the menu item and dislikeness was maximum. Same behaviour for positive sentiment as well. 
* date:- date is already provided in the review.

# Notes: 
    - A review may talk about multiple catagories and services aspects. Similarly, a review can only talk about category, or service. Analyze only about what is given. DO NOT MAKE THINGS UP.
    - For categories, stay with in the categories provided. DO NOT add anything out of provided categories list.
    - Score for the 'over all' is basically the NPS of the entire review.
    - For Menu Items, Score ranges from 0 to 10 for both positve and negative sentiments individually. Negative sentiment with 10 values means user disliked the menu item very much. 

# Formatting
Your response will be an array of json objects where each object will be showing review rating as per above discussed parameters.
DO NOT add new lines or any other formatting to the response.

training data: 
dataset1:{example_5}.
dataset2:{example_6}.
dataset3:{example_7}.
dataset3:{example_8}.
dataset3:{example_9}.
dataset3:{example_10}.
expected response:{example_11}
In response i am expecting overall review_score key which will have value [0-10]
If you do not find an answer, do not return anything new out of what is expected.
Your job is to provide analysis of review.

"""

async def call_api(prompt, gpt_modal, session):
    token = os.getenv("OPENAI_KEY")
    api_url = "https://api.openai.com/v1/chat/completions"
    headers = {"Authorization": f"Bearer {token}"}
    data = {
        "model":gpt_modal, 
        "messages": [
    {"role": "system", "content": system_message},
    {"role": "user", "content": prompt}
    ],
        "max_tokens": 4000,
        "temperature": 0,
    }
    
    try:
        async with session.post(api_url, json=data, headers=headers) as response:
            if response.status == 200:
                return await response.json()
            else:
                return {'error': f'HTTP error {response.status}: {await response.text()}'}
    except Exception as e:
        logging.error(f"Failed to communicate with API: {e}")
        return None

async def call_handler(prompts, gpt_modal):
    async with aiohttp.ClientSession() as session:       
        tasks = [call_api(prompt, gpt_modal, session) for prompt in prompts]
        results = await asyncio.gather(*tasks)
        return results

def recursive_api_call_handler(prompts,gpt_modal, results, index):
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    results[index] = loop.run_until_complete(call_handler(prompts, gpt_modal))
    
# Function to convert date format
def convert_date_format(date_str):
    # Parse the date string
    date_obj = datetime.strptime(date_str, "%m/%d/%Y %H:%M:%S")
    # Format the date object
    return date_obj.strftime("%d-%m-%Y")

def filter_and_convert_data2(data):
    # Process the data
    filtered_data = []
    keys_to_remove = ['author_title', 'author_id', 'author_image']
    for review in data:
         
        # Create a new dictionary with the desired modifications
        new_review = {
            key: value for key, value in review.items() if key not in keys_to_remove
        }
        
        # Convert review_datetime_utc to review_date
        if 'review_datetime_utc' in review:
            new_review['review_date'] = convert_date_format(review['review_datetime_utc'])
        new_review = {
            key: value for key, value in new_review.items() if key != 'review_datetime_utc'
        }
        
        json_string = json.dumps(new_review, indent=4, separators=(',', ': '), ensure_ascii=False)
       
        filtered_data.append(json_string)
    return filtered_data

def filter_and_convert(data, start_date, end_date):
    response = []
    for review in data:
        # Parse the existing date string
        date_str = review["review_datetime_utc"]
        date_format = "%m/%d/%Y %H:%M:%S"  # The format of the input date string

        # Convert the string to a datetime object
        date_obj = datetime.strptime(date_str, date_format)
        
        

        # Format the datetime object to the desired format
        formatted_date_str = date_obj.strftime("%d-%m-%Y")

        # Update the JSON object
        review["review_date"] = formatted_date_str
        del review["review_datetime_utc"] 
        review_string = json.dumps(review, indent=4, separators=(',', ': '), ensure_ascii=False)
        date_format2 = '%d-%m-%Y'
        date_sd = datetime.strptime(start_date, date_format2)
        date_ed = datetime.strptime(end_date, date_format2)
        date_r = datetime.strptime(formatted_date_str, date_format2)
        
        if date_sd <= date_r <= date_ed:
            response.append(review_string)
    return response

def response_to_json(data):
    responses_list = []
    for response in data:
            try:
                # Extracting content field from each choice
                content = response['choices'][0]['message']['content']
                data = json.loads(content)
                responses_list.append(data) 
            except Exception as e:
                # Handling any errors in parsing or extraction
                responses_list.append({'no_applicable': 'error'})
    return responses_list

def fetch_reviews(place_id, review_count):
    outscraper_key = os.getenv("OUTSCRAPER_KEY")
    client = ApiClient(api_key=outscraper_key)
    reviews = client.google_maps_reviews(place_id, reviews_limit=review_count, ignore_empty=True, language='en')
    data = reviews[0].get("reviews_data")  
    response = []    
    for i in data:
            row = {
                                "review_id" : i.get("review_id"),
                                "review_text" :i.get("review_text"),
                                "review_rating" : i.get("review_rating"),
                                "review_datetime_utc" : i.get("review_datetime_utc"),
            }
            response.append(row)
    return response
    
    
def chatGPT(data, gpt_modal):
    results = [None]
    thread = threading.Thread(target=recursive_api_call_handler, args=(data,gpt_modal,results, 0))
    thread.start()
    thread.join()
    return results

def final_data_cleaning(data):
    category_scores = {
            "Food quality and taste":{
                "score": 0,
                "count":0,
                "positive":0,
                "negative":0,
                },
            "Value for money":{
                "score": 0,
                "count":0,
                "positive":0,
                "negative":0,
                },
            "Wait time and speed of service":{
                "score": 0,
                "count":0,
                "positive":0,
                "negative":0,
                },
            "Staff friendliness and attentiveness":{
                "score": 0,
                "count":0,
                "positive":0,
                "negative":0,
                },
            "Cleanliness and hygiene":{
                "score": 0,
                "count":0,
                "positive":0,
                "negative":0,
                },
            "Store atmosphere and decor":{
                "score": 0,
                "count":0,
                "positive":0,
                "negative":0,
                },
            "Online and mobile ordering experience":{
                "score": 0,
                "count":0,
                "positive":0,
                "negative":0,
                },
            "Delivery and takeout service":{
                "score": 0,
                "count":0,
                "positive":0,
                "negative":0,
                }
        }
    menu_scores = {}

    # Aggregate the scores
    for entry in data:
        response = entry['response']        
        # Sum menu item scores
        for menu in response.get('menu_name', []):
            for key, value in menu.items():
                if key not in menu_scores:
                    menu_scores[key] = {
                            "score": 0,
                            "count":0,
                            "positive":0,
                            "negative":0,
                        }


    # Aggregate the scores
    for entry in data:
        response = entry['response']
        if 'category_name' in response:
            # Sum category scores
            for category in response['category_name']:
                for key, value in category.items():
                    if key in category_scores:
                        category_scores[key]['score'] += value['score']
                        category_scores[key]['count'] += 1
                        if value['sentiment'] == 'positive':
                            category_scores[key]['positive'] += 1
                        if value['sentiment'] == 'negative':
                            category_scores[key]['negative'] += 1
                     
        if 'menu_name' in response:
            # # Sum menu item scores
            for menu in response.get('menu_name', []):
                for key, value in menu.items():
                    if key in menu_scores:
                        menu_scores[key]['score'] += value['score']
                        menu_scores[key]['count'] += 1
                        if value['sentiment'] == 'positive':
                            menu_scores[key]['positive'] += 1
                        if value['sentiment'] == 'negative':
                            menu_scores[key]['negative'] += 1
                     

    # Print the results
    dataframe = []
    for category in category_scores.items():
        score = category[1]['score']
        count = category[1]['count']
        positive = category[1]['positive']
        negative = category[1]['negative']
        name = category[0]
        if count !=0:
            avg = score/count
        else:
            avg = 0
        dataframe.append({
            "Category Name": name,
            "Average Rating": avg,
            "Accumulated Score": score,
            "Total Reviews":count,
            "Positive": positive,
            "Negative": negative, 
        })


    df = pd.DataFrame(dataframe)
    print(df)
        
    dataframe2 = []
    for menu in menu_scores.items():
        score = menu[1]['score']
        count = menu[1]['count']
        positive = menu[1]['positive']
        negative = menu[1]['negative']
        name = menu[0]
        if count !=0:
            avg = score/count
        else:
            avg = 0
        dataframe2.append({
            "Menu Item Name": name,
            "Average Rating": avg,
            "Accumulated Score": score,
            "Total Reviews":count,
            "Positive": positive,
            "Negative": negative, 
        })
        
    df2 = pd.DataFrame(dataframe2)
    print(df2) 
    res1 = generate_graph_summary(dataframe, "gpt-4o-mini")
    res2 = generate_graph_summary(dataframe2, "gpt-4o-mini")
    
    return {
        "summary": res1,
        "data":dataframe
    },{
        "summary": res2,
        "data":dataframe2
    }

def group_by_month(data):
    # Create a DataFrame
    df = pd.DataFrame(data)

    # Convert the 'date' column to datetime format
    df['date'] = pd.to_datetime(df['date'], format="%d-%m-%Y")

    # Extract month from the 'date' column and convert to month name
    df['month'] = df['date'].dt.month_name()

    # Group by 'month' and calculate the average rating for each month
    grouped = df.groupby('month')['rating'].mean().reset_index()

    # Convert the DataFrame to the desired format
    # grouped = grouped.rename(columns={'rating': 'average_rating'})
    grouped['month'] = grouped['month'].apply(lambda x: x.capitalize())
    result = grouped.to_dict(orient='records')
    
    # List of months in chronological order
    month_order = [
        "January", "February", "March", "April", "May", "June", "July",
        "August", "September", "October", "November", "December"
    ]

    # Create a mapping of month names to their position in the year
    month_index = {month: index for index, month in enumerate(month_order)}

    # Sort data by month based on the predefined month order
    sorted_data = sorted(result, key=lambda x: month_index[x["month"]])
    return sorted_data

def graph_1(data):
    response = []
    average = 0
    # Aggregate the scores
    for entry in data:
        score = entry['response']['review_score']
        date = entry['response']['review']['review_date']
        average += score
        response.append({
            "rating": score,
            "date": date
        })

        # Sort data based on the date
        sorted_data = sorted(response, key=parse_date)
        grouped_data = group_by_month(sorted_data)
        
    return {
        "average_rating": average/len(data),
        "summary":generate_graph_summary(sorted_data, "gpt-4o-mini"),
        "data":grouped_data
    }

def parse_date(item):
    return datetime.strptime(item["date"], "%d-%m-%Y")

def graph_3(data):
    category_scores = {
            "Food quality and taste":{
                "accumulated_rating": 0,
                "total_reviews":0,
                "data":[]
                },
            "Value for money":{
                "accumulated_rating": 0,
                "total_reviews":0,
                "data":[]
                },
            "Wait time and speed of service":{
                "accumulated_rating": 0,
                "total_reviews":0,
                "data":[]
                },
            "Staff friendliness and attentiveness":{
                "accumulated_rating": 0,
                "total_reviews":0,
                "data":[]
                },
            "Cleanliness and hygiene":{
                "accumulated_rating": 0,
                "total_reviews":0,
                "data":[]
                },
            "Store atmosphere and decor":{
                "accumulated_rating": 0,
                "total_reviews":0,
                "data":[]
                },
            "Online and mobile ordering experience":{
                "accumulated_rating": 0,
                "total_reviews":0,
                "data":[]
                },
            "Delivery and takeout service":{
                "accumulated_rating": 0,
                "total_reviews":0,
                "data":[]
                }
        }
    for entry in data:
        response = entry['response']
        date = entry['response']['review']['review_date']
        if 'category_name' in response:
            # Sum category scores
            for category in response['category_name']:
                for key, value in category.items():
                    if key in category_scores:
                        category_scores[key]['accumulated_rating'] += value['score']
                        category_scores[key]['total_reviews'] += 1
                        category_scores[key]['data'].append({
                            "date": date,
                            "rating": value['score']
                        })
                        
    for entry in category_scores:
        category_scores[entry]['data'] = sorted(category_scores[entry]['data'], key=parse_date)
        # category_scores[entry]['data'] = group_by_month(category_scores[entry]['data'])
        if category_scores[entry]['total_reviews'] != 0:
            category_scores[entry]['average_rating'] = category_scores[entry]['accumulated_rating']/category_scores[entry]['total_reviews'] 
        
    summary = generate_graph_summary(category_scores, "gpt-4o-mini")
    
    for item in category_scores:
        if len(category_scores[item]["data"]) > 0:
            category_scores[item]["data"] = group_by_month(category_scores[item]["data"])
    
    # grouped_category_date = group_by_month(category_scores)
    return {
        "summary": summary,
        "data": category_scores
    }

def generate_graph_summary(info, modal):
    token = os.getenv("OPENAI_KEY")
    prompt2 = f'''
    Time series rating data of my restaurant is : {info}
    '''
    
    system_message2 = """
    # Background

    Your job is to summarize data of my restaurant in words where data is an array of json objects,

    # Expected Result
    Your summary text must be short and must not be more than three lines.
    """

    url2 = "https://api.openai.com/v1/chat/completions"
    data2 = {
            "model":modal,
            "messages": [
                {"role": "system", "content": system_message2},
                {"role": "user", "content": prompt2}
                ],
            "max_tokens": 4096,
            "temperature": 0,
            }
    payload2 = json.dumps(data2)
    headers2 = {
    'Content-Type': 'application/json',
    'Authorization': f"Bearer {token}"
    }

    response2 = requests.request("POST", url2, headers=headers2, data=payload2)
    a = response2.text
    b = json.loads(a)
    c = b.get("choices")[0]
    d = c.get("message").get("content")
    print(d)
    return d

def month_wise_aggregation_for_graph_5(data, month):
    response = {"month": month}
    for entry in data:
        response[entry] = next((item['rating'] for item in data[entry]["data"] if item['month'] == month),0)
    return response
    
def graph_5(data):  
    info = [
        month_wise_aggregation_for_graph_5(data, "January"),
        month_wise_aggregation_for_graph_5(data, "February"),
        month_wise_aggregation_for_graph_5(data, "March"),
        month_wise_aggregation_for_graph_5(data, "April"),
        month_wise_aggregation_for_graph_5(data, "May"),
        month_wise_aggregation_for_graph_5(data, "June"),
        month_wise_aggregation_for_graph_5(data, "July"),
        month_wise_aggregation_for_graph_5(data, "August"),
        month_wise_aggregation_for_graph_5(data, "September"),
        month_wise_aggregation_for_graph_5(data, "October"),
        month_wise_aggregation_for_graph_5(data, "November"),
        month_wise_aggregation_for_graph_5(data, "December"),
    ]
    
    summary = generate_graph_summary(info,"gpt-4o-mini")
    return {
        "summary": summary,
        "data": info
    }
    