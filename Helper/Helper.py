import pandas as pd
import os
from config import Constrant
import re
import tiktoken
import logging
import aiohttp
import asyncio
import requests
import ast

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
Food quanlity and taste,
Value for money,
Wait time and speed of service,
Staff friendliness and attentiveness,
Cleanliness and hygiene,
Store atmosphere and decor,
Online and mobile ordering experience,
Delivery and takeout service
'''
example_5 = "{'response':[{'Food quality and taste':{'sentiment':'positive','theme':'friendly','score':7, 'date':'2024-02-08'}]}"
example_6 = "{'response':[{'Value for money':{'sentiment':'positive','theme':'friendly','score':7, 'date':'2024-02-08'}]}"
example_7 = "{'response':[{'Cleanliness and hygiene':{'sentiment':'positive','theme':'friendly','score':7, 'date':'2024-02-08'}]}"
example_8 = '''
{"response":{"review_score":8,"review":{"review_id":"","review_date":"dd-mm-YYYY","review_rating":"4.0"},"category_name":[{"sentiment":"positive","theme":"friendly","score":7}],"menu_name":["sentiment": "positive" , "score": 9,"theme":"tasty"}]}}
'''

prompt = '''
{"review_text":'Agar kisi ne apnay paysay saarnay hayn to please make your way to Tandoori for iftari.

Astaghfirullah intihai fazool khana aur service.

First they served the Iftari which was guzara then after 45mins they decided to finally serve the dinner which was so so bad!

The chicken items had a weird heik smell even the chinese rice. Other items were so mediocre. We barely ate like two bites and couldnt take more. It was pathetic.

At the time of payment we let the waiter know our thoughts, to which they said they will call the supervisor who never showed up. Lol

I am surprised k logon ka koi taste nahe ha because it was jam packed! like how…

I feel so sad for wasting 10k on this. Never again in my life.', "review_date":"20-02-2024","review_id":"223kkddk",'review_rating':1}
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

* categories:- here is the possible list of categories - stay WITHIN THESE CATEGORIES : separated by,: {services}.
* menu items:- here is the possible list of menu items - you can add menu item by yourself if found in the review by not in the list of these MENU ITEMS : separated by,: {menu_items}.
* sentiment:- can be positive, negative, neutral.
* theme:- one word theme, e.g crispy, juicy, expensive, friendly, unprofessional etc.
* score:- ranging from 0 to 10. 10 being the highest.
* date:- date is already provided in the review.

# Notes: 
    - A review may talk about multiple catagories and services aspects. Similarly, a review can only talk about category, or service. Analyze only about what is give. DO NOT MAKE THINGS UP.
    - For categories, stay with in the categories provided. 
    - Score for the 'over all' is basically the NPS of the entire review.

# Formatting
Your response will be an array of json objects where each object will be showing review rating as per above discussed parameters
DO NOT add new lines or any other formatting to the response.

training data: 
dataset1:{example_5}.
dataset2:{example_6}.
dataset3:{example_7}.
expected response:{example_8}
In response i am expecting overall review_score key which will have value [0-10]
If you do not find an answer, do not return anything new out of what is expected.
Your job is to provide analysis of review

"""

def processReviewCsv(path=""):
    if path != "" :
        try:
            csv_file_path = 'static/reviews/'+path
            if os.path.isfile(csv_file_path):
                df = pd.read_csv(csv_file_path,sep=";")
                user_reviews = []
                for index, row in df.iterrows():
                    item = {
                       "review_id" : row["review_id"],
                       "author_title" : row["author_title"],
                       "author_id" : row["author_id"],
                       "author_image" : row["author_image"],
                       "review_text" : row["review_text"],
                       "review_rating" : row["review_rating"],
                       "review_datetime_utc" : row["review_datetime_utc"],
                    }

                    user_reviews.append(item)

                return {'status':1,'data':user_reviews}
            else:
                return {'status':0,'message':Constrant.Arg['file_not_exist']}
        except:
            return {'status':0,'message':Constrant.Arg["general_error"]}

    else:
        return {'status':0,'message':Constrant.Arg["invalid_path"]}
    

def preprocess_text(text):
    # Convert to lowercase
    text = text.lower()
    
    # Remove URLs
    text = re.sub(r'https?://\S+|www\.\S+', '', text)
    
    # Remove special characters except punctuation marks conveying sentiments
    text = re.sub(r'[^a-zA-Z0-9\s!.?]', '', text)
    
    # Replace multiple punctuation with single (e.g., '!!!' -> '!')
    text = re.sub(r'([!?.]){2,}', r'\1', text)
    
    # Remove extra spaces
    text = re.sub(r'\s+', ' ', text).strip()
    
    
    return text


def isEmtpy(strings):
    return len(strings.strip()) == 0


def preprocess_text(text):
        # Convert to lowercase
        text = text.lower()
        
        # Remove URLs
        text = re.sub(r'https?://\S+|www\.\S+', '', text)
        
        # Remove special characters except punctuation marks conveying sentiments
        text = re.sub(r'[^a-zA-Z0-9\s!.?]', '', text)
        
        # Replace multiple punctuation with single (e.g., '!!!' -> '!')
        text = re.sub(r'([!?.]){2,}', r'\1', text)
        
        # Remove extra spaces
        text = re.sub(r'\s+', ' ', text).strip()
        
        return text

def filer_and_clean_data(data):
    return (
                data
                # only keep required columns
                [['review_text','review_datetime_utc']]
                
                # convert review_datetime_utc to date only 
                .assign(date = lambda x: pd.to_datetime(x['review_datetime_utc']).dt.date)
                .drop(columns=['review_datetime_utc'])
                
                # drop rows with missing values
                .dropna()
                
                # review text clean
                .assign(reviewText_clean = lambda x: x['review_text'].apply(preprocess_text))
                
                # create a separate column for that counts the number of words in the review
                .assign(wordCount = lambda x: x['reviewText_clean'].str.split().apply(len))
                
                # only show where the word count is greater than 50
                .query('wordCount >= 10 and wordCount < 1000') # < ================= change this line according to your needs

                )


def num_tokens_from_string(string: str) -> int:
    # calculate tokens
    encoding = tiktoken.encoding_for_model("gpt-3.5-turbo")
    """Returns the number of tokens in a text string."""
    num_tokens = len(encoding.encode(string))
    return num_tokens

def cost_calculations(file):
    # GPT 3.5 turbo cost = 	$0.50 / 1M tokens
    # GPT 4 cost = $30 / 1M tokens
    # total input cost 
    file['numTokens'] = file['reviewText_clean'].apply(num_tokens_from_string)
    gpt3 = float(((file['numTokens'].sum())/1_000_000) * .50)
    gpt4 = float(((file['numTokens'].sum())/1_000_000) * 30)
    return {
        "cost-gpt-3.5-turbo":gpt3,
        "cost-gpt-4":gpt4
    }
    
async def call_api(prompt, session):
    token = os.getenv("OPENAI_KEY")
    api_url = "https://api.openai.com/v1/chat/completions"
    headers = {"Authorization": f"Bearer {token}"}
    data = {
        "model":"gpt-4-turbo", #gpt-3.5-turbo-1106", gpt-4-turbo
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
  
    
def divide_file_in_chunks(chunk_size,file ):
        chunks = [file.iloc[i:i+chunk_size] for i in range(0, len(file), chunk_size)]
        return chunks[0]['reviewText_clean'].to_list()

async def call_handler(prompts):
    async with aiohttp.ClientSession() as session:       
        tasks = [call_api(prompt, session) for prompt in prompts]
        results = await asyncio.gather(*tasks)
        return results

def recursive_api_call_handler(prompts, results, index):
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    results[index] = loop.run_until_complete(call_handler(prompts))

def extract_score(rating):
        try:
            scores_with_default = [attributes.get('score', None) for category, attributes in rating]
            return scores_with_default[0]
        except Exception as e:
            # In case of error, return None
            return None
        
def process_ratings(data):
    
    # Function to extract score from ratings
    data['score'] = data['ratings'].apply(extract_score)
    # Create a new DataFrame with required columns
    output_data = data[['score', 'review_date']]
    
    # sort the data by date
    output_data = output_data.sort_values('review_date')
    
    # remove na
    output_data = output_data.dropna()  
    
    return output_data

def response_to_json(data):
    responses_list = []
    for response in data:
            try:
                # Extracting content field from each choice
                content = response['choices'][0]['message']['content']
                # Converting the string representation of dictionary into an actual dictionary
                data_dict = ast.literal_eval(content)
                # Extracting 'response' key
                if 'response' in data_dict:
                    responses_list.extend(data_dict['response'])  # Using extend instead of append
                else:
                    responses_list.append({'no_applicable': 'error'})
            except Exception as e:
                # Handling any errors in parsing or extraction
                responses_list.append({'no_applicable': 'error'})
    return responses_list

def chatgpt_final_result(prompts, responses_list, file):
    result = pd.DataFrame()
    result['review'] = prompts
    result['ratings'] = responses_list
    # convert each value of ratings into a list for every dictionary items
    result['ratings'] = result['ratings'].apply(lambda x: [(k,v) for k,v in x.items()])
    result['review_date'] = file['date']
    return result