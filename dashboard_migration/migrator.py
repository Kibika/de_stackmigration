import json
import requests
import logging
import sys

logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)
logging.getLogger("requests").setLevel("ERROR")

# The Redash instance you're copying from:
ORIGIN = "http://localhost"
ORIGIN_API_KEY = "BYSbo74txh79cKKcQNW2ETdEr92sD4uwJ1v3coa5" # admin API key

# The Superset account you're copying into:
DESTINATION = 'https://app.redash.io/acme'
DESTINATION_API_KEY = "..." # admin API key

# You need to create the data sources in advance in the destination account. Once created, update the map here: 
# (origin Redash data source id -> destination Redash data source id)
DATA_SOURCES = {
    3: 1234   
}

meta = {
    # include here any users you already created in the target Redash account. 
    # the key is the user id in the origin Redash instance. make sure to include the API key, as it used to recreate any objects
    # this user might have owned.
    "users": {
        "1": {
            "id": 1234,
            "email": "user@acme.com",
            "invite_link": "",
            "api_key": ""
        }, 
    },
    "queries": {},
    "visualizations": {}
}


def api_request(api):
    response = requests.get(ORIGIN + api, headers=auth_headers(ORIGIN_API_KEY))
    response.raise_for_status()

    return response.json()


def auth_headers(api_key):
        return {
            "Authorization": "Key {}".format(api_key)
        }


def import_users():
    print ("Importing users...")

    users = api_request('/api/users')
    for user in users:
        print ("   importing: {}".format(user['id']))
        data = {
            "name": user['name'],
            "email": user['email']
        }

        if str(user['id']) in meta['users']:
            print ("    ... skipping: exists.")
            continue

        if user['email'] == 'admin':
            print ("    ... skipping: admin.")
            continue

        response = requests.post(DESTINATION + '/api/users?no_invite=1', json=data, headers=auth_headers(DESTINATION_API_KEY))
        response.raise_for_status()

        new_user = response.json()
        meta['users'][user['id']] = {
            'id': new_user['id'],
            'email': new_user['email'],
            'invite_link': new_user['invite_link']
        }


def get_api_key(user_id):
    response = requests.get(DESTINATION + '/api/users/{}'.format(user_id), headers=auth_headers(DESTINATION_API_KEY))
    response.raise_for_status()

    return response.json()['api_key']


def user_with_api_key(user_id):
    user = meta['users'].get(user_id) or meta['users'].get(str(user_id))
    if 'api_key' not in user:
        user['api_key'] = get_api_key(user['id'])
    return user


def get_queries(url, api_key):
    queries = [] 
    headers = {'Authorization': 'Key {}'.format(api_key)}
    path = "{}/api/queries".format(url)
    has_more = True
    page = 1
    while has_more:
        response = requests.get(path, headers=headers, params={'page': page}).json()
        queries.extend(response['results'])
        has_more = page * response['page_size'] + 1 <= response['count']
        page += 1

    return queries


def get_queries_old(url, api_key):
    headers = {'Authorization': 'Key {}'.format(api_key)}
    path = "{}/api/queries".format(url)
    response = requests.get(path, headers=auth_headers(api_key))
    response.raise_for_status()

    return response.json()


def import_queries():
    print ("Import queries...")

    # Depends on the Redash version running in origin, you might need to use `get_queries_old`.
    queries = get_queries(ORIGIN, ORIGIN_API_KEY)
    #queries = get_queries_old(ORIGIN, ORIGIN_API_KEY)

    for query in queries:
        print ("   importing: {}".format(query['id']))
        data_source_id = DATA_SOURCES.get(query['data_source_id'])
        if data_source_id is None:
            print ("   skipped ({})".format(data_source_id))
            continue

        data = {
            "data_source_id": data_source_id,
            "query": query['query'],
            "is_archived": query['is_archived'],
            "schedule": query['schedule'],
            "description": query['description'],
            "name": query['name'],
        }
        
        user = user_with_api_key(query['user']['id'])

        response = requests.post(DESTINATION + '/api/queries', json=data, headers=auth_headers(user['api_key']))
        response.raise_for_status()

        meta['queries'][query['id']] = response.json()['id']


def import_visualizations():
    print ("Importing visualizations...")

    for query_id, new_query_id in meta['queries'].iteritems():
        query = api_request('/api/queries/{}'.format(query_id))
        print ("   importing visualizations of: {}".format(query_id))
        
        for v in query['visualizations']:
            if v['type'] == 'TABLE':
                response = requests.get(DESTINATION + '/api/queries/{}'.format(new_query_id), headers=auth_headers(DESTINATION_API_KEY))
                response.raise_for_status()

                new_vis = response.json()['visualizations']
                for new_v in new_vis:
                    if new_v['type'] == 'TABLE':
                        meta['visualizations'][v['id']] = new_v['id']
            else:
                user = user_with_api_key(query['user']['id'])
                data = {
                    "name": v['name'],
                    "description": v['description'],
                    "options": v['options'],
                    "type": v['type'],
                    "query_id": new_query_id
                }
                response = requests.post(DESTINATION + '/api/visualizations', json=data, headers=auth_headers(user['api_key']))
                response.raise_for_status()

                meta['visualizations'][v['id']] = response.json()['id']


def import_dashboards():
    print("Importing dashboards...")

    dashboards = api_request('/api/dashboards')
    
    for dashboard in dashboards:
        print ("   importing: {}".format(dashboard['slug']))
        # laod full dashboard
        d = api_request('/api/dashboards/{}'.format(dashboard['slug']))
        # create dashboard
        data = {'name': d['name']}
        user = user_with_api_key(d['user_id'])
        response = requests.post(DESTINATION + '/api/dashboards', json=data, headers=auth_headers(user['api_key']))
        response.raise_for_status()

        new_dashboard = response.json()

        # recreate widget
        for row in d['widgets']:
            for widget in row:
                data = {
                    'dashboard_id': new_dashboard['id'],
                    'options': widget['options'],
                    'width': widget['width'],
                    'text': widget['text'],
                    'visualization_id': None
                }

                if 'visualization' in widget:
                    data['visualization_id'] = meta['visualizations'].get(widget['visualization']['id'])

                if 'visualization' in widget and not data['visualization_id']:
                    print('skipping for missing viz')
                    continue

                response = requests.post(DESTINATION + '/api/widgets', json=data, headers=auth_headers(user['api_key']))
                response.raise_for_status()


def save_meta():
    print("Saving meta...")
    with open('meta.json', 'w') as f:
        json.dump(meta, f)


def import_all():
    try:
        # If you had an issue while running this the first time, fixed it and running again, uncomment the following to skip content already imported.
        #with open('meta.json') as f:
        #    meta.update(json.load(f))
        import_users()
        import_queries()
        import_visualizations()
        import_dashboards()
    except Exception as ex:
        logging.exception(ex)

    save_meta()


if __name__ == '__main__':
    import_all()