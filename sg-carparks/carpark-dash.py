import json
import requests
from datetime import datetime
from collections import deque

import dash
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Output, Input

import plotly.graph_objs as go


def curr_carpark_data():
    api_url = 'https://api.data.gov.sg/v1/transport/carpark-availability'
    curr_datetime = datetime.now().strftime('%Y-%m-%dT%H:%M:%S')
    api_params = {'date_time': curr_datetime}
    rq_data = requests.get(url=api_url, params=api_params)

    carpark_str = rq_data.content.decode('utf-8')
    carpark_dict = json.loads(carpark_str)
    carpark_lst = carpark_dict['items']

    return carpark_lst


def reset_graph_meta(new_carpark_number=None):
    global datetime_deque, lots_deque_dict, total_lots, curr_carpark_number
    # x-axis (datetime)
    datetime_deque = deque(maxlen=10)
    # y-axis (lots)
    lots_deque_dict = {0: deque(maxlen=10)}
    # total lots counter
    total_lots = 0
    if new_carpark_number:
        curr_carpark_number = new_carpark_number


# initialise empty graph metas
reset_graph_meta()

# instantiate dash object
app = dash.Dash(__name__)
# obtaining dictionary of available carparks
temp_carpark_lst = curr_carpark_data()[0]['carpark_data']
carpark_label_value_mapping = [{'label': carpark_info_dict['carpark_number'],
                                'value': carpark_info_dict['carpark_number']}
                               for carpark_info_dict in temp_carpark_lst]
# set first carpark number as initial value
curr_carpark_number = carpark_label_value_mapping[0]['value']


# setting html of dashboard and graph components
app.layout = html.Div(children=[
                                  dcc.Dropdown(id='carpark_number',
                                               options=carpark_label_value_mapping,
                                               value=curr_carpark_number),
                                  dcc.Graph(id='live-lots-graph', animate=False),
                                  dcc.Interval(
                                      id='update-lots-graph',
                                      interval=60000
                                  )
                                ]
                      )

# initialise empty graph figure
fig = None


# callback update graph function
@app.callback(Output('live-lots-graph', 'figure'),
              [Input('update-lots-graph', 'n_intervals'),
               Input('carpark_number', 'value')])
def update_graph(_, carpark_number):
    global total_lots, curr_carpark_number, fig

    if curr_carpark_number != carpark_number:
        reset_graph_meta(carpark_number)

    carpark_lst = curr_carpark_data()

    if carpark_lst:
        carpark_lst = carpark_lst[0]['carpark_data']

        for carpark_data in carpark_lst:
            if carpark_data['carpark_number'] == carpark_number:
                carpark_info = carpark_data['carpark_info']
                carpark_update_datetime = datetime.strptime(carpark_data['update_datetime'], '%Y-%m-%dT%H:%M:%S')

                datetime_deque.append(carpark_update_datetime)

                graph_data = []
                for index, single_carpark_info in enumerate(carpark_info):
                    if index not in lots_deque_dict:
                        lots_deque_dict[index] = deque(maxlen=10)
                    lots_deque_dict[index].append(int(single_carpark_info['lots_available']))
                    if int(single_carpark_info['total_lots']) > total_lots:
                        total_lots = int(single_carpark_info['total_lots'])
                    graph_data.append(go.Scatter(
                        x=list(datetime_deque),
                        y=list(lots_deque_dict[index]),
                        text=[f'Total Lots: {int(single_carpark_info["total_lots"])}<br>'
                              f'Proportion of Available Lots: '
                              f'{float(lots_available)/int(single_carpark_info["total_lots"])*100:.2f}%'
                              for lots_available in lots_deque_dict[index]],
                        name=f'Lot Type {single_carpark_info["lot_type"]}',
                        mode='lines+markers'
                    ))
                fig = {'data': graph_data,
                       'layout': go.Layout(xaxis=dict(range=[min(datetime_deque), max(datetime_deque)]),
                                           yaxis=dict(range=[0, total_lots]),
                                           title=f'Carpark {curr_carpark_number}: Number of Available Lots',
                                           showlegend=True)}
    return fig


if __name__ == '__main__':
    app.run_server(debug=True)
