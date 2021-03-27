from flask import Flask
from flask import request
from flask_restful import Api, Resource
import json
from datetime import datetime

from validation_functions import *
from database import Database

app = Flask(__name__)
api = Api(app)
db = Database()


def is_unique_courier_id(item):  # Проверка id курьера на уникальность в БД
    if db.find_document('couriers', {'courier_id': item['courier_id']}) is not None:
        return False
    return True


def is_unique_order_id(item):  # Проверка id заказа на уникальность в БД
    if db.find_document('orders', {'order_id': item['order_id']}) is not None:
        return False
    return True


def delete_courier_metadata(item):  # Удаление лишниз данных курьера
    return {
        "courier_id": item['courier_id'],
        "courier_type": item['courier_type'],
        "regions": item['regions'],
        "working_hours": item['working_hours']
    }


def delete_order_metadata(item):  # Удаление лишниз данных заказа
    return {
        "order_id": item['order_id'],
        "weight": item['weight'],
        "region": item['region'],
        "delivery_hours": item['delivery_hours']
    }


def check_timestamps_intersection(courier_time, delivery_time):  # Проверка пересечения временных отрезков
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
        return True
    return False


class Controller(Resource):
    def post(self, request_type, assign=""):  # Обработчик POST реквестов
        print(request_type, assign)
        if request_type == 'couriers' and assign == 'assign':  # Назначение заказов
            # Проверка id-шника курьера
            try:
                id = request.json['courier_id']
                if type(id) != int or id < 1:
                    raise ValueError
            except ValueError:
                return "Bad request", 400

            assigned_courier = db.find_document('couriers', {'courier_id': request.json['courier_id']})
            if assigned_courier is None:
                return "Bad request", 400

            # Возвращение заказов в коллекцию заказов
            for order in assigned_courier['orders']:
                db.insert_document('orders', order)
            # Очистка списка заказов у курьера
            db.update_document('couriers', assigned_courier, {'orders': []})
            assigned_courier = delete_courier_metadata(assigned_courier)
            assigned_courier['orders'] = []

            http_200 = {'orders': []}
            max_weight = {'foot': 10, 'bike': 15, 'car': 50}
            orders = db.find_document('orders', {}, True)
            # Подбор заказов
            for order in orders:
                # Проверка совпадения региона и веса
                if order['region'] in assigned_courier['regions'] and \
                        order['weight'] <= max_weight[assigned_courier['courier_type']]:
                    assigned_order = None
                    # Перебор всех временных отрезков работы курьера и времени доставки
                    for courier_time in assigned_courier['working_hours']:
                        for delivery_time in order['delivery_hours']:
                            if check_timestamps_intersection(courier_time, delivery_time):
                                assigned_order = order
                                break
                        if assigned_order is not None:
                            break
                    if assigned_order is not None:
                        # Назначение заказа курьеру
                        db.delete_document('orders', {'order_id': assigned_order['order_id']})
                        assigned_courier['orders'].append(assigned_order)
                        http_200['orders'].append({'id': assigned_order['order_id']})
            if len(http_200['orders']) > 0:
                http_200['assign_time'] = datetime.now().isoformat('T')[:-4] + 'Z'
            db.update_document('couriers', {'courier_id': assigned_courier['courier_id']}, assigned_courier)
            return json.dumps(http_200), 200
        # Добавление курьера
        elif request_type == 'couriers':
            http_201 = {'couriers': []}
            http_400 = {'validation_error': {'couriers': []}}

            for courier in request.json['data']:
                if check_courier_fields(courier) and is_unique_courier_id(courier):
                    courier['orders'] = []
                    # TODO: добавить поля rating и earnings я реализации 6ого обработчика
                    db.insert_document('couriers', courier)
                    http_201['couriers'].append({'id': courier['courier_id']})
                else:
                    http_400['validation_error']['couriers'].append({'id': courier['courier_id']})
            if len(http_400['validation_error']['couriers']) > 0:
                return json.dumps(http_400), 400
            return json.dumps(http_201), 201
        # Добавление заказа
        elif request_type == 'orders':
            http_201 = {'orders': []}
            http_400 = {'validation_error': {'orders': []}}

            for order in request.json['data']:
                if check_order_fields(order) and is_unique_order_id(order):
                    db.insert_document('orders', order)
                    http_201['orders'].append({'id': order['order_id']})
                else:
                    http_400['validation_error']['orders'].append({'id': order['order_id']})
            if len(http_400['validation_error']['orders']) > 0:
                return json.dumps(http_400), 400
            return json.dumps(http_201), 201
        else:
            return "Not found", 404

    def patch(self, request_type, id):  # Обработчик PATCH реквестов
        if request_type == 'couriers':
            # Проверка полей реквеста
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
            courier = db.find_document('couriers', {'courier_id': id})
            if courier is not None:
                for key, value in request.json.items():
                    courier[key] = value
                # Удаление заказов, теперь не подходящих курьеру
                max_weight = {'foot': 10, 'bike': 15, 'car': 50}
                i = 0
                while i < len(courier['orders']):
                    # Проверка веса
                    if courier['orders'][i]['weight'] > max_weight[courier['courier_type']]:
                        db.insert_document('orders', courier['orders'][i])
                        courier['orders'].pop(i)
                        i -= 1
                    # Проверка региона
                    elif courier['orders'][i]['region'] not in courier['regions']:
                        db.insert_document('orders', courier['orders'][i])
                        courier['orders'].pop(i)
                        i -= 1
                    # Проверка времени
                    else:
                        flag = False
                        for courier_time in courier['working_hours']:
                            for delivery_time in courier['orders'][i]['delivery_hours']:
                                if check_timestamps_intersection(courier_time, delivery_time):
                                    flag = True
                                    break
                            if flag:
                                break
                        if not flag:
                            db.insert_document('orders', courier['orders'][i])
                            courier['orders'].pop(i)
                            i -= 1
                    i += 1
                db.update_document('couriers', {'courier_id': id}, courier)
                courier = delete_courier_metadata(courier)
                return courier, 200
            else:
                return "Bad request", 400

        else:
            return "Not found", 404


api.add_resource(Controller, "/<string:request_type>", "/<string:request_type>/<int:id>",
                 "/<string:request_type>/<string:assign>")
if __name__ == '__main__':
    app.run(debug=True)