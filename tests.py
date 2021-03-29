import datetime as dt
from app import app
from unittest import TestCase


class TestIntegrations(TestCase):
    def setUp(self):
        # Создание файла для активации режима тестирования (ещё раз простите)
        with open('test_status.txt', 'w') as f:
            f.write('true')
        self.app = app.test_client()
        # Отправка запроса для активации режима тестирования
        self.app.options('testing')

    def test_post_courier(self):  # Тест добавления курьеров
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
        self.assertEqual(201, response.status_code, 'Wrong status code')
        self.assertEqual(correct_response, response.get_json(), 'Wrong JSON response')

    def test_post_courier_bad(self):  # Тест добавления курьеров с неверными полями
        self.app.delete()
        test_request = {
            "data":
                [
                    {
                        "courier_id": -3,
                        "courier_type": "foot",
                        "regions": 1,
                        "working_hours": ["11:35-14:05", "09:00-11:00"]
                    },
                    {
                        "courier_id": 2,
                        "courier_type": "skate",
                        "regions": [22, "33"],
                        "working_hours": ["09:00-18:00", "22:00"],
                        "kaboom": "yes"
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
            "validation_error":
                {"couriers":
                    [
                        {
                            "id": -3,
                            "invalid_fields":
                                [
                                    "courier_id",
                                    "regions"
                                ]
                        },
                        {
                            "id": 2,
                            "invalid_fields":
                                [
                                    "kaboom",
                                    "courier_type",
                                    "regions",
                                    "working_hours"
                                ]
                        }
                    ]
                }
        }
        response = self.app.post('/couriers', json=test_request)
        self.assertEqual(400, response.status_code, 'Wrong status code')
        self.assertEqual(correct_response, response.get_json(), 'Wrong JSON response')

    def test_post_courier_not_unique(self):  # Тест добавления курьера с неуникальным id
        self.app.delete()
        test_request1 = {
            "data":
                [
                    {
                        "courier_id": 1,
                        "courier_type": "foot",
                        "regions": [1, 12, 22],
                        "working_hours": ["11:35-14:05", "09:00-11:00"]
                    }
                ]
        }
        test_request2 = {
            "data":
                [
                    {
                        "courier_id": 1,
                        "courier_type": "foot",
                        "regions": [1, 12, 22],
                        "working_hours": ["11:35-14:05", "09:00-11:00"]
                    }
                ]
        }
        correct_response1 = {
            'couriers':
                [
                    {'id': 1}
                ]
        }
        correct_response2 = {
            "validation_error":
                {
                    "couriers":
                        [
                            {
                                "id": 1,
                                "invalid_fields":
                                    [
                                        "courier_id"
                                    ]
                            }
                        ]
                }
        }
        response1 = self.app.post('/couriers', json=test_request1)
        response2 = self.app.post('/couriers', json=test_request2)
        self.assertEqual(201, response1.status_code, 'Wrong status code')
        self.assertEqual(correct_response1, response1.get_json(), 'Wrong JSON response')
        self.assertEqual(400, response2.status_code, 'Wrong status code')
        self.assertEqual(correct_response2, response2.get_json(), 'Wrong JSON response')

    def test_patch_courier(self):  # Тест изменения курьера
        self.app.delete()
        test_request = {
            "data":
                [
                    {
                        "courier_id": 1,
                        "courier_type": "car",
                        "regions": [12, 22, 23, 33],
                        "working_hours": ["15:00-22:00"]
                    }
                ]
        }
        self.app.post('/couriers', json=test_request)

        test_request = {
            "courier_type": "bike",
            "regions": [12, 54, 23, 10],
            "working_hours": ["09:00-22:00"]
        }
        correct_response = {
            "courier_id": 1,
            "courier_type": "bike",
            "regions": [12, 54, 23, 10],
            "working_hours": ["09:00-22:00"]
        }

        response = self.app.patch('/couriers/1', json=test_request)
        self.assertEqual(200, response.status_code, 'Wrong status code')
        self.assertEqual(correct_response, response.get_json(), 'Wrong JSON response')

    def test_patch_courier_bad(self):  # Тест изменения курьера с некорректными полям
        self.app.delete()
        test_request = {
            "data":
                [
                    {
                        "courier_id": 1,
                        "courier_type": "car",
                        "regions": [12, 22, 23, 33],
                        "working_hours": ["15:00-22:00"]
                    }
                ]
        }
        self.app.post('/couriers', json=test_request)

        test_request = {
            "courier_type": "helicopter",
            "regions": [12, 54, 23, 10, -4],
            "working_hours": ["always"],
            "vacation": "never"
        }
        correct_response = {
            "validation_error":
                {
                    "invalid_fields": ["vacation", "courier_type", "regions", "working_hours"]
                }
        }

        response = self.app.patch('/couriers/1', json=test_request)
        self.assertEqual(400, response.status_code, 'Wrong status code')
        self.assertEqual(correct_response, response.get_json(), 'Wrong JSON response')

    def test_post_order(self):  # Тест добавления заказов
        self.app.delete()
        test_request = {
            "data":
                [
                    {
                        "order_id": 1,
                        "weight": 0.23,
                        "region": 12,
                        "delivery_hours": ["09:00-18:00"]
                    },
                    {
                        "order_id": 2,
                        "weight": 15,
                        "region": 1,
                        "delivery_hours": ["09:00-18:00"]
                    },
                    {
                        "order_id": 3,
                        "weight": 45,
                        "region": 22,
                        "delivery_hours": ["09:00-12:00", "16:00-21:30"]
                    }
                ]
        }
        correct_response = {
            'orders':
                [
                    {'id': 1},
                    {'id': 2},
                    {'id': 3}
                ]
        }
        response = self.app.post('/orders', json=test_request)
        self.assertEqual(201, response.status_code, 'Wrong status code')
        self.assertEqual(correct_response, response.get_json(), 'Wrong JSON response')

    def test_post_order_bad(self):  # Тест добавления заказов с некорректными полями
        self.app.delete()
        test_request = {
            "data":
                [
                    {
                        "order_id": 1.1,
                        "weight": 0.23,
                        "region": "12",
                        "delivery_hours": ["09:00-18:00"]
                    },
                    {
                        "order_id": 2,
                        "weight": 500,
                        "region": 1,
                        "delivery_hours": ["09:00-18:00", "never"],
                        "is_explosive": "yes"
                    },
                    {
                        "order_id": 3,
                        "weight": 45,
                        "region": 22,
                        "delivery_hours": ["09:00-12:00", "16:00-21:30"]
                    }
                ]
        }
        correct_response = {
            "validation_error":
                {"orders":
                    [
                        {
                            "id": 1.1,
                            "invalid_fields":
                                [
                                    "order_id",
                                    "region"
                                ]
                        },
                        {
                            "id": 2,
                            "invalid_fields":
                                [
                                    "is_explosive",
                                    "weight",
                                    "delivery_hours"
                                ]
                        }
                    ]
                }
        }
        response = self.app.post('/orders', json=test_request)
        self.assertEqual(400, response.status_code, 'Wrong status code')
        self.assertEqual(correct_response, response.get_json(), 'Wrong JSON response')

    def test_post_order_not_unique(self):  # Тест добавления заказа с неуникальным id
        self.app.delete()
        test_request1 = {
            "data":
                [
                    {
                        "order_id": 1,
                        "weight": 0.23,
                        "region": 12,
                        "delivery_hours": ["09:00-18:00"]
                    }
                ]
        }
        test_request2 = {
            "data":
                [
                    {
                        "order_id": 1,
                        "weight": 0.23,
                        "region": 12,
                        "delivery_hours": ["09:00-18:00"]
                    }
                ]
        }
        correct_response1 = {
            'orders':
                [
                    {'id': 1}
                ]
        }
        correct_response2 = {
            "validation_error":
                {
                    "orders":
                        [
                            {
                                "id": 1,
                                "invalid_fields":
                                    [
                                        "order_id"
                                    ]
                            }
                        ]
                }
        }
        response1 = self.app.post('/orders', json=test_request1)
        response2 = self.app.post('/orders', json=test_request2)
        self.assertEqual(201, response1.status_code, 'Wrong status code')
        self.assertEqual(correct_response1, response1.get_json(), 'Wrong JSON response')
        self.assertEqual(400, response2.status_code, 'Wrong status code')
        self.assertEqual(correct_response2, response2.get_json(), 'Wrong JSON response')

    def test_post_orders_assign(self):  # Тест назначения заказов
        self.app.delete()
        test_request = {
            "data":
                [
                    {
                        "courier_id": 3,
                        "courier_type": "car",
                        "regions": [12, 22, 23, 33],
                        "working_hours": ["15:00-22:00"]
                    }
                ]
        }
        self.app.post('/couriers', json=test_request)

        test_request = {
            "data":
                [
                    {
                        "order_id": 1,
                        "weight": 0.23,
                        "region": 12,
                        "delivery_hours": ["09:00-18:00"]
                    },
                    {
                        "order_id": 2,
                        "weight": 15,
                        "region": 1,
                        "delivery_hours": ["09:00-18:00"]
                    },
                    {
                        "order_id": 3,
                        "weight": 45,
                        "region": 22,
                        "delivery_hours": ["09:00-12:00", "16:00-21:30"]
                    }
                ]
        }
        self.app.post('/orders', json=test_request)

        test_request = {
            "courier_id": 3
        }

        correct_response = [{"id": 1}, {"id": 3}]

        response = self.app.post("/couriers/assign", json=test_request)
        self.assertEqual(200, response.status_code, "Wrong status code")
        self.assertEqual(correct_response, response.get_json()['orders'], 'Wrong JSON response')
        self.assertEqual(correct_response, response.get_json()['orders'], "Controller is not idempotent")

    def test_post_orders_complete(self):  # Тест принятия заказов
        self.app.delete()
        test_request = {
            "data":
                [
                    {
                        "courier_id": 3,
                        "courier_type": "car",
                        "regions": [12, 22, 23, 33],
                        "working_hours": ["15:00-22:00"]
                    }
                ]
        }
        self.app.post('/couriers', json=test_request)

        test_request = {
            "data":
                [
                    {
                        "order_id": 1,
                        "weight": 0.23,
                        "region": 12,
                        "delivery_hours": ["09:00-18:00"]
                    },
                    {
                        "order_id": 2,
                        "weight": 15,
                        "region": 1,
                        "delivery_hours": ["09:00-18:00"]
                    },
                    {
                        "order_id": 3,
                        "weight": 45,
                        "region": 22,
                        "delivery_hours": ["09:00-12:00", "16:00-21:30"]
                    }
                ]
        }
        self.app.post('/orders', json=test_request)

        test_request = {
            "courier_id": 3
        }

        response = self.app.post("/couriers/assign", json=test_request)
        assign_time = response.get_json()['assign_time']
        assign_time = dt.datetime.strptime(assign_time, '%Y-%m-%dT%H:%M:%S.%fZ')
        complete_time = assign_time + dt.timedelta(1 / 72)

        test_request = {
            "courier_id": 3,
            "order_id": 1,
            "complete_time": complete_time.isoformat('T')[:-4] + 'Z'
        }

        correct_response = {"order_id": 1 }

        response = self.app.post('/orders/complete', json=test_request)
        self.assertEqual(200, response.status_code, "Wrong status code")
        self.assertEqual(correct_response, response.get_json(), "Wrong orders ids")

    def test_post_orders_complete_bad(self):  # Тест принятия заказов с неправильным временем доставки
        self.app.delete()
        test_request = {
            "data":
                [
                    {
                        "courier_id": 3,
                        "courier_type": "car",
                        "regions": [12, 22, 23, 33],
                        "working_hours": ["15:00-22:00"]
                    }
                ]
        }
        self.app.post('/couriers', json=test_request)

        test_request = {
            "data":
                [
                    {
                        "order_id": 1,
                        "weight": 0.23,
                        "region": 12,
                        "delivery_hours": ["09:00-18:00"]
                    },
                    {
                        "order_id": 2,
                        "weight": 15,
                        "region": 1,
                        "delivery_hours": ["09:00-18:00"]
                    },
                    {
                        "order_id": 3,
                        "weight": 45,
                        "region": 22,
                        "delivery_hours": ["09:00-12:00", "16:00-21:30"]
                    }
                ]
        }
        self.app.post('/orders', json=test_request)

        test_request = {
            "courier_id": 3
        }

        response = self.app.post("/couriers/assign", json=test_request)
        assign_time = response.get_json()['assign_time']
        complete_time = assign_time

        test_request = {
            "courier_id": 3,
            "order_id": 1,
            "complete_time": complete_time
        }

        correct_response = {
            "validation_error": {
                "invalid_fields": ["complete_time"]
            }
        }

        response = self.app.post('/orders/complete', json=test_request)
        self.assertEqual(400, response.status_code, "Wrong status code")
        self.assertEqual(correct_response, response.get_json(), 'Wrong JSON response')

    def test_get_couriers(self):  # Тест получения информации о курьерах
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
                        "courier_id": 3,
                        "courier_type": "car",
                        "regions": [12, 22, 23, 33],
                        "working_hours": ["15:00-22:00"]
                    }
                ]
        }
        self.app.post('/couriers', json=test_request)

        test_request = {
            "data":
                [
                    {
                        "order_id": 1,
                        "weight": 0.23,
                        "region": 12,
                        "delivery_hours": ["09:00-18:00"]
                    },
                    {
                        "order_id": 2,
                        "weight": 15,
                        "region": 1,
                        "delivery_hours": ["09:00-18:00"]
                    },
                    {
                        "order_id": 3,
                        "weight": 45,
                        "region": 22,
                        "delivery_hours": ["09:00-12:00", "16:00-21:30"]
                    }
                ]
        }
        self.app.post('/orders', json=test_request)

        test_request = {
            "courier_id": 3
        }

        response = self.app.post("/couriers/assign", json=test_request)
        assign_time = response.get_json()['assign_time']
        assign_time = dt.datetime.strptime(assign_time, '%Y-%m-%dT%H:%M:%S.%fZ')
        complete_time1 = assign_time + dt.timedelta(1 / 72)
        complete_time2 = assign_time + dt.timedelta(2 / 72)

        test_request = {
            "courier_id": 3,
            "order_id": 1,
            "complete_time": complete_time1.isoformat('T')[:-4] + 'Z'
        }
        self.app.post('/orders/complete', json=test_request)
        test_request = {
            "courier_id": 3,
            "order_id": 3,
            "complete_time": complete_time2.isoformat('T')[:-4] + 'Z'
        }
        self.app.post('/orders/complete', json=test_request)

        correct_response = {
            "courier_id": 3,
            "courier_type": "car",
            "regions": [12, 22, 23, 33],
            "working_hours": ["15:00-22:00"],
            "rating": 3.333333333333333,
            "earnings": 9000
        }

        response = self.app.get('couriers/3')
        self.assertEqual(200, response.status_code, "Wrong status code")
        self.assertEqual(correct_response, response.get_json(), "Wrong orders ids")

        correct_response = {
            "courier_id": 1,
            "courier_type": "foot",
            "regions": [1, 12, 22],
            "working_hours": ["11:35-14:05", "09:00-11:00"]
        }

        response = self.app.get('couriers/1')
        self.assertEqual(200, response.status_code, "Wrong status code")
        self.assertEqual(correct_response, response.get_json(), "Wrong orders ids")