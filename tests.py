#from app import app
import os
import json
from app import app
from database import Database
from unittest import TestCase

class TestIntegrations(TestCase):
    def setUp(self):
        #print('tests.py')
        #print(os.getcwd())
        with open('test_status.txt', 'w') as f:
            f.write('true')
        #app.testing = True
        #app.db = Database('test')
        #app.app.testing = True
        self.app = app.test_client()
        self.app.options('testing')




    def test_post_courier(self):
        self.app.delete()
        test_request = {
            "data":
                [
                    {
                        "courier_id": 1,
                        "courier_type": "foot",
                        "regions": [1, 12, 22],
                        "working_hours": ["11:35-14:05", "09:00-11:00"]
                    },
                    {
                        "courier_id": 2,
                        "courier_type": "bike",
                        "regions": [22],
                        "working_hours": ["09:00-18:00"]
                    },
                    {
                        "courier_id": 3,
                        "courier_type": "car",
                        "regions": [12, 22, 23, 33],
                        "working_hours": ["15:00-22:00"]
                    }
                ]
        }
        correct_response = {
            'couriers':
                [
                    {'id': 1},
                    {'id': 2},
                    {'id': 3}
                ]
        }
        response = self.app.post('/couriers', json=test_request)
        print('RESPONSE', type(response.get_json()))
        #assert correct_response == response.get_json()
        self.assertEqual(correct_response, json.loads(response.get_json()))
        #print('RESPONSE', response.json)
        #self.app.db.clear_database()
        #assert response == "Not found"