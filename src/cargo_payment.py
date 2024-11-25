# Plotting data from the openttd wiki
# https://wiki.openttd.org/en/Manual/Game%20Mechanics/Cargo%20income

# import libraries
from enum import Enum
import pandas as pd
import plotly.express as px
import dash 
import dash_bootstrap_components as dbc
# defining types

# Cargo (Base Pay, Days1, Days2)
class Cargo(Enum):
    Batteries        = (4322,  2,  30)
    Bubbles          = (5077, 20,  80)
    Candyfloss       = (5005, 10,  25)
    Coal             = (5916,  7, 255)
    Cola             = (4892,  5,  75)
    Copper_Ore       = (4892, 12, 255)
    Diamonds         = (5802, 10, 255)
    Fizzy_Drinks     = (6250, 30,  50)
    Food             = (5688,  0,  30)
    Fruit            = (4209,  0,  15)
    Gold             = (5802, 10,  40)
    Goods            = (6144,  5,  28)
    Grain            = (4778,  4,  40)
    Iron_Ore         = (5120,  9, 255)
    Livestock        = (4322,  4,  18)
    Mail             = (4550, 20,  90)
    Maize            = (4322,  4,  40)
    Oil              = (4437, 25, 255)
    Oil_subtropical  = (4892, 25, 255)
    Paper            = (5461,  7,  60)
    Passengers       = (3185,  0,  24)
    Plastic          = (4664, 30, 255)
    Rubber           = (4437,  2,  20)
    Steel            = (5688,  7, 255)
    Sugar            = (4437, 20, 255)
    Sweets           = (6144,  8,  40)
    Toffee           = (4778, 14,  60)
    Toys             = (5574, 25, 255)
    Valuables        = (7509,  1,  32)
    Water            = (4664, 20,  80)
    Wheat            = (4778,  4,  40)
    Wood             = (5005, 15, 255)
    Wood_subtropical = (7964, 15, 255)

# defining functions

# Calculate income for a given cargo
# cargo:    Cargo
# amount:   +int
# distance: +float
# time:     +int
# Note: Time in formula is ingamedays *2.5
def income(cargo,amount,distance,time, ingametime=True):
    # Convert ingame time for formula
    if ingametime:
        time = time*2.5
    # Unpack cargo
    base_pay,days1,days2 = cargo.value
    # Find formula based on time and days1, days2
    if time <= days1:
        tbonus = 255
    elif days1 < time <= days1 + days2:
        tbonus = 255 - (time - days1)
    else: # time > days1 + days2
        tbonus = 255 - 2*(time - days1) + days2

    # Calculate income
    if tbonus < 31:
        return base_pay * amount * 31*pow(2,-21)
    else:
        return base_pay * amount * distance * tbonus*pow(2,-21)

# returns time in ingamedays for a given speed and distance
# speed:    +int (km/h)
# distance: +int (tiles)
def speed_distance_to_time(speed,distance,aircraft=False):
    if aircraft:
        speed = speed/4
    # 668 km
    speed_tiles_per_day = speed *24 / 668
    return distance / speed_tiles_per_day
        
# returns a plotly figure of income vs distance for a given cargo and speed or range of speeds
# cargo:            Cargo
# distance_bounds:  [+int, +int] (tiles)
# speeds:           n*[+int] (km/h)
# is_aircraft:      bool - aircraft fly at quarter listed speed
def income_vs_distance_speed(cargo, distance_bounds=[0,500],speeds=[50], is_aircraft=False):
    if len(speeds) != len(is_aircraft):
        raise ValueError("speeds and aircraft must be of same length")
    
    # Create dataframe
    # columns = ['Speed','Distance','Time','Income']

    # Populate Speed column with copies of each speed value
    # Populate Distance column with range of distances, repeated for each speed
    # Populate Time column with time for each distance and speed
    # Populate Income column with income for each distance, speed, and cargo
    speed_col = []
    distance_col = []
    time_col = []
    income_col = []
    for i in range(len(speeds)):
        speed_col += [speeds[i]]*len(range(distance_bounds[0],distance_bounds[1]+1))
        distance_col += list(range(distance_bounds[0],distance_bounds[1]+1))
        for distance in range(distance_bounds[0],distance_bounds[1]+1):
            time_col.append(speed_distance_to_time(speeds[i],distance,is_aircraft))
            income_col.append(income(cargo,1,distance,time_col[-1]))

    df = pd.DataFrame({'Speed':speed_col,'Distance':distance_col,'Time':time_col,'Income':income_col})

    # Create figure
    # Line plot
    # Group by speed
    # X-axis: Distance
    #   Label: Distance (tiles)
    # Y-axis: Income
    #   Label: Income (currency / cargo unit)

    fig = px.line(
            df,
            x='Distance',
            y='Income',
            color='Speed',
            labels={
                'Distance': 'Distance (tiles)',
                'Income':   'Income (£)'
                }
            )
    return fig

def start_dash_app():
    cargo_list = [cargo.name for cargo in Cargo]
    app = dash.Dash(__name__, external_stylesheets=[dbc.themes.CYBORG])
    # Build elements of the app
    scheduler = dash.dcc.Interval( id='interval-component', interval=1*250, n_intervals=0)
    app_title = dash.dcc.Markdown(
                "# Cargo Payment Calculator",
                style={'textAlign':'center'},
                className='mb-4'
                )
    amount_slider = dash.dcc.Slider(
                            id="amount",
                            min=1,
                            max=1000
                            )
    distance_slider = dash.dcc.RangeSlider(
                            id="distance",
                            min=0,
                            max=1000
                            )
    speed_options = dash.dcc.Dropdown(
                        id="speed",
                        options=[{'label':f'{speed}{"km/h"}','value':speed} for speed in range(50,300,25)],
                        multi=True
                        )                      
    aircraft_checkbox = dash.dcc.Checklist(
                        id="is_aircraft",
                        options=[{'label':'Aircraft','value':False}],
                        )
    cargo_dropdown = dash.dcc.Dropdown(
                        id="cargo",
                        options=[{'label':cargo,'value':cargo} for cargo in cargo_list],
                        multi=True
                        )
    
    # Build layout
    # Title
    # Graph
    # Amount slider
    # Distance slider
    # Speed dropdown
    # Aircraft checkbox
    # Cargo dropdown

    app.layout = dbc.Container([
        app_title,
        dbc.Tabs([
            dbc.Tab([
                dash.dcc.Graph(id='graph')
            ],label='Graph')
        ]),
        scheduler,
        amount_slider,
        distance_slider,
        speed_options,
        aircraft_checkbox,
        cargo_dropdown
    ])

    # Define callback for updating graph
    @app.callback(
        dash.dependencies.Output('graph','figure'),

        [dash.dependencies.Input('interval-component','n_intervals'),
        dash.dependencies.Input('amount','value'),
        dash.dependencies.Input('distance','value'),
        dash.dependencies.Input('speed','value'),
        dash.dependencies.Input('is_aircraft','value'),
        dash.dependencies.Input('cargo','value')]
    )
    def update_graph(n_intervals,amount,distance,speed,is_aircraft,cargo):

        print(n_intervals)
        print(amount)
        print(distance)
        print(speed)
        print(is_aircraft)
        print(cargo)
        return income_vs_distance_speed(cargo,amount,[distance[0],distance[1]],speed,is_aircraft)
    return app

if __name__ == '__main__':
    app = start_dash_app()
    app.run_server(debug=True)