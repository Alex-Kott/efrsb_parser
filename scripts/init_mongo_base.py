from pymongo import MongoClient, ASCENDING

from efrsb_parser.settings import MONGO_HOST, MONGO_PORT


def run(*args):
    client = MongoClient(host=MONGO_HOST, port=MONGO_PORT)
    db = client['EFRSB']
    trade_cards = db.trade_cards.create_index([('id', ASCENDING)], unique=True)

