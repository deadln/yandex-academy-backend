from flask import Flask
from flask import request, jsonify
from flask_restful import Api, Resource, reqparse
import json
import re
from datetime import datetime

app = Flask(__name__)
api = Api(app)

couriers = [] # Курьеры

orders = [] # Заказы

def check_courier_fields(item): # Проверка валидности полей курьера
    # Проверка на наличие полей
    courier_fields = ["courier_id", "courier_type", "regions", "working_hours"]
    for key in item.keys():
        if key not in courier_fields:
            return False
        else:
            courier_fields.remove(key)
    if len(courier_fields) > 0:
        return False
    # Проверка на валидность значений полей
    if type(item['courier_id']) != int or item['courier_id'] < 1:
        return False
    if type(item['courier_type']) != str or item['courier_type'] not in ['foot', 'bike', 'car']:
        return False
    if type(item['regions']) == list:
        for i in item['regions']:
            if type(i) != int:
                return False
    else:
        return False
    if type(item['working_hours']) == list:
        for i in item['working_hours']: # TODO: Проверка валидности значений данных временных отрезков
            if type(i) != str or not re.match(r'^[0-9][0-9]:[0-9][0-9]-[0-9][0-9]:[0-9][0-9]$', i):
                return False
    else:
        return False

    return True

def check_order_fields(item): # Проверка валидности полей заказа
    # Проверка на наличие полей
    order_fields = ["order_id", "weight", "region", "delivery_hours"]
    for key in item.keys():
        if key not in order_fields:
            return False
        else:
            order_fields.remove(key)
    if len(order_fields) > 0:
        return False
    # Проверка на валидность значений полей
    if type(item['order_id']) != int or item['order_id'] < 1:
        return False
    if (type(item['weight']) != float and type(item['weight']) != int) or item['weight'] < 0.01 or item['weight'] > 50:
        return False
    if type(item['region']) != int or item['region'] < 1:
        return False
    if type(item['delivery_hours']) == list:
        for i in item['delivery_hours']: # TODO: Проверка валидности значений данных временных отрезков
            if type(i) != str or not re.match(r'^[0-9][0-9]:[0-9][0-9]-[0-9][0-9]:[0-9][0-9]$', i):
                return False
    else:
        return False

    return True

def to_abs_time(time_str):
    time = time_str.split(':')
    return int(time[0]) * 60 + int(time[1])

class Controller(Resource):
    def post(self, request_type, assign=""):
        print(request_type, assign)
        if request_type == 'couriers' and assign == 'assign':  # Назначение заказов
            print('DICK')
            # Проверка id-шника курьера
            try:
                id = request.json['courier_id']
                if type(id) != int or id < 1:
                    raise ValueError
            except ValueError:
                return "Bad request", 400

            # TODO: проверять наличие курьера по id в БД
            assigned_courier = None
            for courier in couriers:
                if courier['courier_id'] == id:
                    courier['orders'] = []
                    assigned_courier = courier
                    break
            if assigned_courier is None:
                return "Bad request", 400

            http_200 = {'orders': []}
            for order in orders:
                if order['region'] in assigned_courier['regions']:  # TODO: Сделать проверку по весу груза
                    assigned_order = None
                    for courier_time in assigned_courier['working_hours']:
                        for delivery_time in order['delivery_hours']:
                            courier_time_split = courier_time.split('-')
                            delivery_time_split = delivery_time.split('-')
                            courier_time_start = to_abs_time(courier_time_split[0])
                            courier_time_end = to_abs_time(courier_time_split[1])
                            delivery_time_start = to_abs_time(delivery_time_split[0])
                            delivery_time_end = to_abs_time(delivery_time_split[1])
                            if courier_time_start < delivery_time_start < courier_time_end or \
                                courier_time_start < delivery_time_end < courier_time_end or \
                                delivery_time_start < courier_time_start < delivery_time_end or \
                                    delivery_time_start < courier_time_end < delivery_time_end:
                                assigned_order = order
                                break
                        if assigned_courier is not None:
                            break
                    if assigned_courier is not None:
                        assigned_courier['orders'].append(assigned_order)
                        http_200['orders'].append({'id': assigned_order['order_id']})
            http_200['assign_time'] = datetime.now().isoformat('T')[:-4] + 'Z'
            return json.dumps(http_200), 200


        elif request_type == 'couriers': # Добавление курьера
            http_201 = {'couriers': []}
            http_400 = {'validation_error': {'couriers': []}}

            for courier in request.json['data']:
                if check_courier_fields(courier):
                    # TODO: Проверять уникальность id в БД
                    courier['orders'] = []
                    couriers.append(courier) # TODO: Заменить на добавление в БД
                    http_201['couriers'].append({'id': courier['courier_id']})
                else:
                    http_400['validation_error']['couriers'].append({'id': courier['courier_id']})
            print(couriers)
            if len(http_400['validation_error']['couriers']) > 0:
                return json.dumps(http_400), 400
            return json.dumps(http_201), 201
        elif request_type == 'orders': # Добавление заказа
            http_201 = {'orders': []}
            http_400 = {'validation_error': {'orders': []}}

            for order in request.json['data']:
                if check_order_fields(order):
                    # TODO: Проверять уникальность id в БД
                    orders.append(order) # TODO: Заменить на добавление в БД
                    http_201['orders'].append({'id': order['order_id']})
                else:
                    http_400['validation_error']['orders'].append({'id': order['order_id']})
            print(orders)
            if len(http_400['validation_error']['orders']) > 0:
                return json.dumps(http_400), 400
            return json.dumps(http_201), 201
        else:
            return "Not found", 404

    def patch(self, request_type, id):
        if request_type == 'couriers':
            courier_fields = ["courier_type", "regions", "working_hours"]
            for key, value in request.json.items():
                if key not in courier_fields:
                    return "Bad request", 400
                else:
                    courier_fields.remove(key)
            if len(courier_fields) == 3:
                return "Bad request", 400

            # Проверка на валидность значений полей
            if 'courier_type' in request.json.keys() and (type(request.json['courier_type']) != str or \
                                                          request.json['courier_type'] not in ['foot', 'bike', 'car']):
                return "Bad request", 400
            if 'regions' in request.json.keys():
                if type(request.json['regions']) == list:
                    for i in request.json['regions']:
                        if type(i) != int:
                            return "Bad request", 400
                else:
                    return "Bad request", 400
            if 'working_hours' in request.json.keys():
                if type(request.json['working_hours']) == list:
                    for i in request.json['working_hours']: # TODO: Проверка валидности значений данных временных отрезков
                        if type(i) != str or not re.match(r'^[0-9][0-9]:[0-9][0-9]-[0-9][0-9]:[0-9][0-9]$', i):
                            return "Bad request", 400
                else:
                    return "Bad request", 400
            # Применение изменений
            for courier in couriers:
                if courier['courier_id'] == id:
                    for key, value in request.json.items():
                        courier[key] = value # TODO: Заменить на изменение данных в БД
                    # TODO: отмена неподъёмных заказов
                    print(couriers)
                    return courier, 200
            return "Bad request", 400

        else:
            return "Not found", 404


#api.add_resource(Controller, "/ai-quotes", "/ai-quotes/", "/ai-quotes/<int:id>")
api.add_resource(Controller, "/<string:request_type>", "/<string:request_type>/<int:id>",
                 "/<string:request_type>/<string:assign>")
if __name__ == '__main__':
    app.run(debug=True)