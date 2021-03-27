from flask import Flask
from flask import request
from flask_restful import Api, Resource
import json
from datetime import datetime

from validation_functions import *

app = Flask(__name__)
api = Api(app)

couriers = []  # Курьеры

orders = []  # Заказы

# TODO: рефакторинг действий проверки данных!!!

class Controller(Resource):
    def post(self, request_type, assign=""):
        print(request_type, assign)
        if request_type == 'couriers' and assign == 'assign':  # Назначение заказов
            # Проверка id-шника курьера
            try:
                id = request.json['courier_id']
                if type(id) != int or id < 1:
                    raise ValueError
            except ValueError:
                return "Bad request", 400

            assigned_courier = None
            for courier in couriers:
                if courier['courier_id'] == id:
                    courier['orders'] = []
                    assigned_courier = courier
                    break
            if assigned_courier is None:
                return "Bad request", 400

            # TODO: Возвращать заказы принадлежащие курьеру обратно в БД

            http_200 = {'orders': []}
            max_weight = {'foot': 10, 'bike': 15, 'car': 50}
            # Подбор заказов
            for order in orders:
                if order['region'] in assigned_courier['regions'] and \
                        order['weight'] <= max_weight[assigned_courier['courier_type']]:
                    assigned_order = None
                    for courier_time in assigned_courier['working_hours']:
                        for delivery_time in order['delivery_hours']:
                            # Приведение часов работы и доставки к абсолютному формату
                            courier_time_split = courier_time.split('-')
                            delivery_time_split = delivery_time.split('-')
                            courier_time_start = to_abs_time(courier_time_split[0])
                            courier_time_end = to_abs_time(courier_time_split[1])
                            delivery_time_start = to_abs_time(delivery_time_split[0])
                            delivery_time_end = to_abs_time(delivery_time_split[1])
                            # Проверка пересечения часов работы и доставки
                            if courier_time_start < delivery_time_start < courier_time_end or \
                                courier_time_start < delivery_time_end < courier_time_end or \
                                delivery_time_start < courier_time_start < delivery_time_end or \
                                    delivery_time_start < courier_time_end < delivery_time_end:
                                assigned_order = order
                                break
                        if assigned_order is not None:
                            break
                    if assigned_order is not None:
                        # TODO: Удалять назначенные заказы из БД
                        assigned_courier['orders'].append(assigned_order)
                        http_200['orders'].append({'id': assigned_order['order_id']})
            if len(http_200['orders']) > 0:
                http_200['assign_time'] = datetime.now().isoformat('T')[:-4] + 'Z'
            return json.dumps(http_200), 200
        # Добавление курьера
        elif request_type == 'couriers':
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
        # Добавление заказа
        elif request_type == 'orders':
            http_201 = {'orders': []}
            http_400 = {'validation_error': {'orders': []}}

            for order in request.json['data']:
                if check_order_fields(order):  # TODO: Проверять уникальность id в БД
                    orders.append(order)  # TODO: Заменить на добавление в БД
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
            if 'courier_type' in request.json.keys() and not is_courier_type_valid(request.json['courier_type']):
                return "Bad request", 400
            if 'regions' in request.json.keys() and not is_regions_valid(request.json['regions']):
                return "Bad request", 400
            if 'working_hours' in request.json.keys() and not is_hours_valid(request.json['working_hours']):
                return "Bad request", 400
            # Применение изменений
            for courier in couriers:
                if courier['courier_id'] == id:
                    for key, value in request.json.items():
                        courier[key] = value # TODO: Заменить на изменение данных в БД
                    # TODO: отмена неподходящих по региону, времени и неподъёмных заказов
                    print(couriers)
                    return courier, 200
            return "Bad request", 400

        else:
            return "Not found", 404


api.add_resource(Controller, "/<string:request_type>", "/<string:request_type>/<int:id>",
                 "/<string:request_type>/<string:assign>")
if __name__ == '__main__':
    app.run(debug=True)