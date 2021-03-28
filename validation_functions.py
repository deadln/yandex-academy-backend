import re

def is_courier_type_valid(item):  # Проверка типа курьра на валидность
    if type(item) != str or item not in ['foot', 'bike', 'car']:
        return False
    return True


def is_regions_valid(item):  # Проверка списка регионов на валидность
    if type(item) == list:
        for i in item:
            if type(i) != int or i < 1:
                return False
    else:
        return False
    return True


def is_hours_valid(item):  # Проверка списка часов работы на валидность
    if type(item) == list:
        for i in item:  # TODO: Проверка валидности значений данных временных отрезков
            if type(i) != str or not re.match(r'^[0-9][0-9]:[0-9][0-9]-[0-9][0-9]:[0-9][0-9]$', i) or \
                    int(i[0:2]) >= 24 or int(i[3:5]) >= 60 or int(i[6:8]) >= 24 or int(i[9:11]) >= 60 or \
                    int(i[0:2]) >= 24 or int(i[3:5]) >= 60 or int(i[0:2]) >= 24 or int(i[3:5]) >= 60 or \
                    to_abs_time(i[:5]) >= to_abs_time(i[6:]):
                return False
    else:
        return False
    return True


def is_weight_valid(item):  # Проверка веса на валидность
    if type(item) != float and type(item) != int or not 0.01 <= item <= 50:
        return False
    return True


def is_region_valid(item):  # Проверка региона на валидность
    if type(item) != int or item < 1:
        return False
    return True


def check_courier_fields(item):  # Проверка валидности полей курьера
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
    if type(item['courier_id']) != int or item['courier_id'] < 1:  # TODO: проверять уникальность id
        return False
    if not is_courier_type_valid(item['courier_type']):
        return False
    if not is_regions_valid(item['regions']):
        return False
    if not is_hours_valid(item['working_hours']):
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
    if type(item['order_id']) != int or item['order_id'] < 1: # TODO: проверять уникальность id
        return False
    if not is_weight_valid(item['weight']):
        return False
    if not is_region_valid(item['region']):
        return False
    if not is_hours_valid(item['delivery_hours']):
        return False

    return True


def to_abs_time(time_str):  # Перевод строки времени в минуты
    time = time_str.split(':')
    return int(time[0]) * 60 + int(time[1])