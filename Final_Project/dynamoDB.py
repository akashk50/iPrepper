import config
from datetime import datetime
from decimal import Decimal

question = "tell me about yourself"
emotionsDict = {'neutral': 4, 'happy': 9, 'sad': 8, 'fear': 2, 'disgust': 3}
out = """Grade: D+
Explanation: This answer lacks substance and coherence. 
It seems like you are describing your emotions rather than giving insights into your personality, 
skills, or experiences. To improve, focus on sharing relevant information about your background, interests, 
achievements, and goals. Provide examples that showcase your strengths and experiences that are relevant to the 
job you are applying for. Avoid using vague descriptions and make sure your answer is clear and easy to understand."""
totalEmotions = 26

def get_dynamodb_headers(table_name):
    # Create a DynamoDB service client using the environment's credentials
    dynamodb = config.dynamodb_resource()
    table = dynamodb.Table(table_name)

    dynamoItem = {
        "dateSubmitted": str(datetime.now()), 
        "Question": question,
        "Feedback": out, 
        "Happy": Decimal(str(round(emotionsDict.get('happy', 0) / totalEmotions, 3))),
        "Neutral": Decimal(str(round(emotionsDict.get('neutral', 0) / totalEmotions, 3))),
        "Other Emotions": Decimal(str(round((totalEmotions - (emotionsDict.get('happy', 0) + emotionsDict.get('neutral', 0))) / totalEmotions, 3)))
    }
    table.put_item(Item=dynamoItem)
    print("success!")

if __name__ == "__main__":
    get_dynamodb_headers(config.DYNAMODB_TABLE)
