import config
import pandas as pd
from pymongo import MongoClient


def loadMongo():
    questions_df = pd.read_csv(config.asset_path("questions.csv"))
    
    client = MongoClient(config.MONGODB_URI)
    db = client[config.MONGODB_DATABASE]
    db.questions.insert_many(questions_df.to_dict('records'))


def main():
    substring = ""
    regex_pattern = {'$regex': substring, '$options': 'i'}
    client = MongoClient(config.MONGODB_URI)
    db = client[config.MONGODB_DATABASE]
    questions = db.questions
    for a in questions.find({"Question": regex_pattern, "Difficulty": 2}):
        print(a)

if __name__ == "__main__":
    main()

def deleteDB():
    client = MongoClient(config.MONGODB_URI)
    client.drop_database('questions')
    client.drop_database(config.MONGODB_DATABASE)
