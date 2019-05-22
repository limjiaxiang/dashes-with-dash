import json
import datetime
import requests
from collections import deque

import dash
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Output, Input

import plotly
import plotly.graph_objs as go


# x-axis (datetime)
datetime_deque = deque(maxlen=10)
# y-axis (lots)
lots_deque = deque(maxlen=10)

# instantiate dash object
app = dash.Dash(__name__)
# setting html of dashboard and graph components
app.layout = html.Div(children=
    [
        dcc.Graph(id='live-lots-graph', animate=True),
        dcc.Interval(
            id='update-lots-graph',
            interval=30000
        )
    ]
)

# callback update graph function
@app.callback(Output('live-lots-graph', 'figure'),
              [Input('update-lots-graph', 'n_intervals')])
def update_graph(self):
    api_url = 'https://api.data.gov.sg/v1/transport/carpark-availability'
    curr_datetime = datetime.datetime.now().strftime('%Y-%m-%dT%H:%M:%S')
    api_params = {'date_time': curr_datetime}
    data = requests.get(url=api_url, params=api_params)

    carpark_str = data.content.decode('utf-8')
    carpark_dict = json.loads(carpark_str)
    carpark_lst = carpark_dict['items']

    if carpark_lst:
        carpark_lst = carpark_lst[0]['carpark_data']

        # testing
        test_carpark_num = 'HE12'

        for data in carpark_lst:
            if data['carpark_number'] == test_carpark_num:
                test_carpark_info = data['carpark_info']
                test_carpark_update_datetime = data['update_datetime']
                break

        test_carpark_lots = test_carpark_info[0]


        # obtain current time data
        datetime_deque.append(test_carpark_update_datetime)
        lots_deque.append(int(test_carpark_lots['lots_available']))

        total_lots = test_carpark_lots['total_lots']

    data = go.Scatter(
        x=list(datetime_deque),
        y=list(lots_deque),
        name='Lots Available',
        mode='lines+markers'
    )

    return {'data': [data], 'layout': go.Layout(xaxis=dict(range=[min(datetime_deque), max(datetime_deque)]),
                                                yaxis=dict(range=[0, total_lots]),
                                                title=f'Carpark: {test_carpark_num}')}

# show num of unique lot types charts

# data attributes to filter by:
# 1. carpark_number - automatically show charts based on number of different type of lots
# 2. number of lots available (range) - line chart
# 3. percentage of free lots: add to hover labels

# add dropdown filter for carparks available

if __name__ == '__main__':
    app.run_server(debug=True)
