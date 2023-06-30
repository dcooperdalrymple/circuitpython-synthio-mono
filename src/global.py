import os, json, math, re

# JSON

def read_json(path):
    try:
        with open(path, "r") as file:
            data = json.load(file)
    except:
        print("Failed to read JSON file: {}".format(path))
        return None
    print("Successfully read JSON file: {}".format(path))
    return data
def save_json(path, data):
    if not data:
        return False
    try:
        with open(path, "w") as file:
            json.dump(data, file)
    except:
        print("Failed to write JSON file: {}".format(path))
        return False
    print("Successfully written JSON file: {}".format(path))
    return True

# Files

def slugify(value):
    value = re.sub(r'[^\w\s-]', '', value.lower())
    return re.sub(r'[-\s]+', '-', value).strip('-_')

# Mapping

def map_value(value, min_value, max_value):
    value = min(max(value, 0.0), 1.0)
    value = (value * (max_value - min_value)) + min_value
    if type(min_value) is int:
        return round(value)
    else:
        return value
def unmap_value(value, min_value, max_value):
    return (min(max(value, min_value), max_value) - min_value) / (max_value - min_value)

def map_value_centered(value, min_value, center_value, max_value, threshold=0.0):
    if value > 0.5 + threshold:
        if threshold > 0.0:
            value = (value-(0.5+threshold))*(1/(0.5-threshold))
        return map_value(value, center_value, max_value)
    elif value < 0.5 - threshold:
        if threshold > 0.0:
            value = value*(1/(0.5-threshold))
        return map_value(value, min_value, center_value)
    else:
        return center_value
def unmap_value_centered(value, min_value, center_value, max_value, threshold=0.0):
    if value > center_value:
        value = unmap_value(value, center_value, max_value)
        if threshold > 0.0:
            return value/(1/(0.5-threshold))+(0.5+threshold)
        else:
            return value/2+0.5
    elif value < center_value:
        value = unmap_value(value, min_value, center_value)
        if threshold > 0.0:
            return value/(1/(0.5-threshold))
        else:
            return value/2
    else:
        return 0.5

def map_boolean(value):
    if type(value) == type(False):
        return value
    else:
        return value >= 0.5
def unmap_boolean(value):
    if value:
        return 1.0
    else:
        return 0.0

def map_array(value, arr, index=False):
    if type(value) == type(""):
        if not value in arr:
            i = 0
        else:
            i = arr.index(value)
    else:
        i = math.floor(max(min(value * len(arr), len(arr) - 1), 0))
    if index:
        return i
    else:
        return arr[i]
def unmap_array(value, arr):
    if not value in arr:
        return 0.0
    try:
        return arr.index(value) / len(arr)
    except:
        return 0.0

def map_dict(value, dict):
    return map_array(value, list(dict))
def unmap_dict(value, dict):
    return unmap_array(value, list(dict))