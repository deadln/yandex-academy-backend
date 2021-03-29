from flask import Flask
from flask import request
from flask_restful import Api, Resource
from pyrfc3339 import parse

import json
from datetime import datetime
import sys

from validation_functions import *
from database import Database

app = Flask(__name__)
api = Api(app)
db = Database()  # Объект для взаимодействия с базой данных


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
            delivery_time_start < courier_time_end < delivery_time_end or \
            courier_time_start == delivery_time_start and courier_time_end == delivery_time_end:
        return True
    return False


def calculate_delivery_time(start_time, end_time):  # Расчёт времени доставки
    delivery_time = (parse(end_time) - parse(start_time)).total_seconds()
    if delivery_time <= 0:
        raise ValueError
    return delivery_time


def merge_dicts(dict1, dict2):  # Слияние словарей вида <ключ: список>
    for key, lst in dict2.items():
        if key not in dict1.keys():
            dict1[key] = lst[:]
        else:
            dict1[key] = dict1[key] + lst


class Controller(Resource):
    def post(self, request_type, request_action=""):  # Обработчик POST реквестов
        if request_type == 'couriers' and request_action == 'assign':  # Назначение заказов
            # Проверка id-шника курьера
            try:
                id = request.json['courier_id']
                if type(id) != int or id < 1:
                    raise ValueError
            except ValueError:
                return "Bad request", 400

            # Поиск курьера в БД
            assigned_courier = db.find_document('couriers', {'courier_id': request.json['courier_id']})
            if assigned_courier is None:
                return "Bad request", 400

            orders = db.find_document('orders', {}, True)
            assign_time = datetime.now().isoformat('T')[:-4] + 'Z'
            http_200 = {'orders': list(map(lambda x: {'id': x}, assigned_courier['orders'][:])),
                        'assign_time': assigned_courier['assign_time']}

            # Если развоз не завершён
            if len(http_200['orders']) > 0:
                return json.dumps(http_200), 200
            max_weight = {'foot': 10, 'bike': 15, 'car': 50}

            # Подбор заказов
            for order in orders:
                # Проверка совпадения региона и веса
                if order['region'] in assigned_courier['regions'] and \
                        order['weight'] <= max_weight[assigned_courier['courier_type']] and \
                        order['status'] == 'unassigned':
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
                        db.update_document('orders', {'order_id': assigned_order['order_id']},
                                           {'status': 'assigned', 'assign_time': assign_time})
                        assigned_courier['orders'].append(assigned_order['order_id'])

                        # Обновление времени назначения заказа у курьера
                        assigned_courier['assign_time'] = assign_time
                        http_200['orders'].append({'id': assigned_order['order_id']})
                        http_200['assign_time'] = assign_time

            db.update_document('couriers', {'courier_id': assigned_courier['courier_id']}, assigned_courier)
            if len(http_200['orders']) == 0:
                del http_200['assign_time']
            return json.dumps(http_200), 200

        # Заказ выполнен
        elif request_type == 'orders' and request_action == 'complete':
            # Проверка существования курьера
            courier = db.find_document('couriers', {'courier_id': request.json['courier_id']})
            if courier is None:
                return {'validation_error': {'invalid_fields': ['courier_id']}}, 400

            # Поиск заказа в списке курьера
            completed_order = None
            for order_id in courier['orders']:
                order = db.find_document('orders', {'order_id': order_id})
                if order['order_id'] == request.json['order_id']:
                    completed_order = order
                    break
            
            if completed_order is not None:
                # Установка временных рамок выполнения заказа
                if courier['complete_time'] == "":
                    start_time = completed_order['assign_time']
                else:
                    start_time = courier['complete_time']
                end_time = request.json['complete_time']

                # Вычисление времени доставки
                try:
                    delivery_time = calculate_delivery_time(start_time, end_time)
                except ValueError:
                    return {'validation_error': {'invalid_fields': ['complete_time']}}, 400

                # Ведение статистики времени доставки заказов по районам для текущего развоза
                if str(completed_order['region']) not in courier['preliminary_statistics'].keys():
                    courier['preliminary_statistics'][str(completed_order['region'])] = []
                courier['preliminary_statistics'][str(completed_order['region'])].append(delivery_time)

                # Удаление выполненного заказа
                courier['orders'].remove(completed_order['order_id'])

                # Установка времени последнего выполненного заказа у курьера
                courier['complete_time'] = request.json['complete_time']

                # Закрепление общей статистики при завершении развоза
                if len(courier['orders']) == 0:
                    merge_dicts(courier['statistics'], courier['preliminary_statistics'])
                    courier['preliminary_statistics'] = {}

                # Добавление очков доставки за выполнение заказа
                delivery_points_range = {'foot': 2, 'bike': 5, 'car': 9}
                courier['delivery_points'] += delivery_points_range[courier['courier_type']]
                db.update_document('orders', {'order_id': completed_order['order_id']},
                                   {'status': 'completed', 'complete_time': request.json['complete_time']})
                db.update_document('couriers', {'courier_id': courier['courier_id']}, courier)
                return {'order_id': completed_order['order_id']}, 200
            else:
                return {'validation_error': {'invalid_fields': ['order_id']}}, 400
        # Добавление курьера
        elif request_type == 'couriers':
            http_201 = {'couriers': []}
            http_400 = {'validation_error': {'couriers': []}}

            for courier in request.json['data']:
                invalid_fields = check_courier_fields(courier)  # Получение списка невалидных полей курьера
                unique_courier_id = is_unique_courier_id(courier)  # Флаг уникальности курьера
                if not unique_courier_id:
                    invalid_fields.append('courier_id')
                if len(invalid_fields) == 0 and unique_courier_id:
                    courier['orders'] = []  # Список заказов, которые выполняет курьер
                    courier['delivery_points'] = 0  # "Очки доставки", сумма коэффициентов за выполнение заказов
                    courier['assign_time'] = ""  # Время назначения последнего заказа
                    courier['complete_time'] = ""  # Время выполнения последнего заказа
                    courier['statistics'] = {}  # Статистика заказов с завершёнными развозами
                    courier['preliminary_statistics'] = {}  # Предварительная статистика текущего развоза
                    db.insert_document('couriers', courier)
                    http_201['couriers'].append({'id': courier['courier_id']})
                else:
                    http_400['validation_error']['couriers'].append({'id': courier['courier_id'],
                                                                     'invalid_fields': invalid_fields})
            if len(http_400['validation_error']['couriers']) > 0:
                return json.dumps(http_400), 400
            return json.dumps(http_201), 201
        # Добавление заказа
        elif request_type == 'orders':
            http_201 = {'orders': []}
            http_400 = {'validation_error': {'orders': []}}

            for order in request.json['data']:
                invalid_fields = check_order_fields(order)  # Получение списка невалидных полей заказа
                unique_order_id = is_unique_order_id(order)  # Флаг уникальности заказа
                if not unique_order_id:
                    invalid_fields.append('order_id')
                if len(invalid_fields) == 0 and unique_order_id:
                    order['status'] = 'unassigned'  # Статусы заказа: unassigned assigned completed
                    order['assign_time'] = ''  # Время назначения заказа
                    order['complete_time'] = ''  # Время выполнения заказа
                    db.insert_document('orders', order)
                    http_201['orders'].append({'id': order['order_id']})
                else:
                    http_400['validation_error']['orders'].append({'id': order['order_id'],
                                                                   'invalid_fields': invalid_fields})
            if len(http_400['validation_error']['orders']) > 0:
                return json.dumps(http_400), 400
            return json.dumps(http_201), 201
        else:
            return "Not found", 404

    def patch(self, request_type, id):  # Обработчик PATCH реквестов
        if request_type == 'couriers':
            # Проверка полей реквеста
            invalid_fields = []
            courier_fields = ["courier_type", "regions", "working_hours"]
            for key, value in request.json.items():
                if key not in courier_fields:
                    invalid_fields.append(key)
                else:
                    courier_fields.remove(key)
            if len(courier_fields) == 3:
                return {'validation_error': {'invalid_fields': courier_fields + invalid_fields}}, 400
                # return "Bad request", 400

            # Проверка на валидность значений полей
            if 'courier_type' in request.json.keys() and not is_courier_type_valid(request.json['courier_type']):
                invalid_fields.append('courier_type')
            if 'regions' in request.json.keys() and not is_regions_valid(request.json['regions']):
                invalid_fields.append('regions')
            if 'working_hours' in request.json.keys() and not is_hours_valid(request.json['working_hours']):
                invalid_fields.append('working_hours')

            # Если нашлись невалидные поля
            if len(invalid_fields) > 0:
                return {'validation_error': {'invalid_fields': invalid_fields}}, 400

            # Применение изменений
            courier = db.find_document('couriers', {'courier_id': id})
            if courier is not None:
                for key, value in request.json.items():
                    courier[key] = value
                # Удаление заказов, теперь не подходящих курьеру
                max_weight = {'foot': 10, 'bike': 15, 'car': 50}
                i = 0
                while i < len(courier['orders']):
                    order = db.find_document('orders', {'order_id': courier['orders'][i]})

                    # Проверка веса
                    if order['weight'] > max_weight[courier['courier_type']]:
                        db.update_document('orders', {'order_id': order['order_id']},
                                           {'status': 'unassigned'})
                        courier['orders'].pop(i)
                        i -= 1

                    # Проверка региона
                    elif order['region'] not in courier['regions']:
                        db.update_document('orders', {'order_id': order['order_id']},
                                           {'status': 'unassigned'})
                        courier['orders'].pop(i)
                        i -= 1

                    # Проверка времени
                    else:
                        flag = False
                        for courier_time in courier['working_hours']:
                            for delivery_time in order['delivery_hours']:
                                if check_timestamps_intersection(courier_time, delivery_time):
                                    flag = True
                                    break
                            if flag:
                                break
                        if not flag:
                            db.update_document('orders', {'order_id': order['order_id']},
                                               {'status': 'unassigned'})
                            courier['orders'].pop(i)
                            i -= 1
                    i += 1
                # Закрепление общей статистики при завершении развоза
                if len(courier['orders']) == 0:
                    merge_dicts(courier['statistics'], courier['preliminary_statistics'])
                    courier['preliminary_statistics'] = {}
                db.update_document('couriers', {'courier_id': id}, courier)
                courier = delete_courier_metadata(courier)
                return courier, 200
            else:
                return "Bad request", 400

        else:
            return "Not found", 404

    def get(self, request_type, id):
        if request_type == 'couriers':
            courier = db.find_document('couriers', {'courier_id': id})
            if courier is not None:
                if len(courier['statistics']) > 0:  # Если есть завершённые развозы
                    avg_delivery_times = []  # Средние времена доставки по районам
                    for region, times in courier['statistics'].items():
                        avg_delivery_times.append(sum(times) / len(times))
                    # Расчёт рейтинга и заработка
                    t = min(avg_delivery_times)
                    rating = (60 * 60 - min(t, 60*60)) / (60*60) * 5
                    summ = courier['delivery_points'] * 500
                    courier = delete_courier_metadata(courier)
                    courier['rating'] = rating
                    courier['earnings'] = summ
                else:
                    courier = delete_courier_metadata(courier)
                return courier, 200
            else:
                return "Not found", 404


api.add_resource(Controller, "/<string:request_type>", "/<string:request_type>/<int:id>",
                 "/<string:request_type>/<string:request_action>")
if __name__ == '__main__':
    ip = '127.0.0.1'
    port = '5000'
    if len(sys.argv) >= 2:
        ip = sys.argv[1]
    if len(sys.argv) == 3:
        port = sys.argv[2]
    app.run(host=ip, port=port)  # Flask по умолчанию способен обрабатывать несколько запросов одновременно
