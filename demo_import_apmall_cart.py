import csv
from collections import defaultdict
from datetime import datetime
import matplotlib
import matplotlib.pyplot as plt
import numpy as np

import pymongo


def save(filename, list_values):
    if not isinstance(list_values, list):
        print(f"Invalid data type: {filename}, {type(list_values)}")
        return

    np.save(filename, list_values)


def load(filename):
    return np.load(filename)


def draw_hist(items, step=1000):

    values = [item['count'] for item in items]
    start = min(values)
    stop = max(values)
    # stop = min(max(values), 5000)

    boxes = range(start, stop, step)

    fig, ax = plt.subplots()
    ax.hist(x=values, bins=boxes, histtype='bar', rwidth=0.8)

    ax.set_xlabel('count')
    ax.set_ylabel('the number of sku')
    ax.set_title(f'Data distribution (max count: {stop})')

    plt.show()


def add_cart_data_from_csv(recsys_db):
    recsys_db.records.delete_many({})
    recsys_db.items.delete_many({})

    records = dict()
    items = dict()

    with open('./apmall_cart_hist_nm.csv', 'r') as f:
        _ = f.readline()

        for cols in csv.reader(f, delimiter=','):
            try:
                comcsno = int(cols[0].strip())
                tmp = cols[2].strip()
                insert_time = int(datetime.strptime(tmp, '%Y%m%d%H%M%S').timestamp())
                itemId = cols[3].strip()
                sap_code = cols[4].strip()
                buy_flag = True if cols[5].strip() == 'Y' else False
                itemName = cols[6].strip()

                if not comcsno in records:
                    record = {
                        'userId': comcsno,
                        'itemIds': []
                    }

                    records[comcsno] = record

                records[comcsno]['itemIds'].append({
                    'itemId': itemId,
                    'purchased': buy_flag,
                    'timestamp': insert_time
                })

                if not itemId in items:
                    item = {
                        'itemId': itemId,
                        'sap_code': sap_code,
                        'itemName': itemName,
                        'count': 0
                    }

                    items[itemId] = item

                items[itemId]['count'] = items[itemId]['count'] + 1

            except Exception as e:
                print(f'Exception: {str(e)}')
                return

    user_idx = 0
    for record in records.values():

        if len(record['itemIds']) < 2:
            continue

        record['itemIds'].sort(key=lambda elem: int(elem['timestamp']))
        record['sorted_items'] = [elem['itemId'] for elem in record['itemIds']]
        record['user_index'] = user_idx
        user_idx += 1

    records = list(records.values())
    items = list(items.values())

    save('records', records)
    save('items', items)

    recsys_db.records.insert_many(records)
    recsys_db.items.insert_many(items)


def add_cart_data_from_file(recsys_db):
    recsys_db.records.delete_many({})
    recsys_db.items.delete_many({})

    records = load('records.npy')
    items = load('items.npy')

    recsys_db.records.insert_many(list(records))
    recsys_db.items.insert_many(items)

    draw_hist(items)


def main():
    client = pymongo.MongoClient(host='13.209.6.203',
                                 port=27017,
                                 username='romi',
                                 password="Amore12345!",
                                 authSource='admin',
                                 authMechanism='SCRAM-SHA-256')

    db = client.recsys_apmall
    # add_cart_data_from_file(db)
    add_cart_data_from_csv(db)
    print("end")


if __name__ == '__main__':
    print('matplotlib: ', matplotlib.__version__)
    main()
