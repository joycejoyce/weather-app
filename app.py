import dash
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output, State
import plotly.graph_objects as go
import os
import requests
import pandas as pd
from datetime import datetime, timedelta

# Fetch Mapbox and Weather API access tokens from environment variables
mapbox_access_token = os.getenv('MAPBOX_ACCESS_TOKEN')
weather_api_key = os.getenv('WEATHER_API_KEY')

# Initialize the Dash app
app = dash.Dash(__name__)

# Create an empty Mapbox map
fig = go.Figure()

fig.update_layout(
    autosize=True,
    hovermode='closest',
    mapbox=dict(
        accesstoken=mapbox_access_token,
        bearing=0,
        center=dict(
            lat=23.6978,
            lon=120.9605
        ),
        pitch=0,
        zoom=7,
        style='streets'
    ),
    width=1000,
    height=450
)

# Define the layout of the app
app.layout = html.Div(className='container', children=[
    # Header
    html.Div([
        html.H1("Mapbox Map Centered on Taiwan with Historical Weather Data"),
    ], style={'margin-top': '10px'}),  # Adjust top margin as needed
    
    # Location info
    html.Div(id='location-info', style={'margin-top': '20px'}),
    
    # Form for querying location
    html.Div([
        dcc.Input(id='location-input', type='text', placeholder='Enter location name...'),
        html.Button('Query', id='query-button', n_clicks=0),
    ], style={'margin-bottom': '20px'}),
    
    # Row containing the line chart and the map
    html.Div([
        html.Div([
            dcc.Graph(id='weather-line-chart'),
        ], style={'width': '40%', 'display': 'inline-block'}),
        
        html.Div([
            dcc.Graph(id='map', figure=fig),
        ], style={'width': '50%', 'display': 'inline-block'}),
    ], style={'display': 'flex', 'gap': '1rem'})
])

# Function to fetch coordinates from Mapbox Geocoding API
def get_coordinates(location_name):
    try:
        geocoding_url = f'https://api.mapbox.com/geocoding/v5/mapbox.places/{location_name}.json'
        params = {
            'access_token': mapbox_access_token,
            'limit': 1
        }
        response = requests.get(geocoding_url, params=params)
        response.raise_for_status()
        data = response.json()
        if data['features']:
            coordinates = data['features'][0]['geometry']['coordinates']
            return {'lon': coordinates[0], 'lat': coordinates[1]}
    except Exception as e:
        print(f"Error fetching coordinates: {e}")
    return None

# Function to fetch historical weather data from WeatherAPI
def get_historical_weather(lat, lon, days=7):
    historical_data = []
    try:
        for i in range(days):
            date = (datetime.now() - timedelta(days=i)).strftime('%Y-%m-%d')
            weather_url = f'http://api.weatherapi.com/v1/history.json'
            params = {
                'key': weather_api_key,
                'q': f'{lat},{lon}',  # Query parameter for latitude and longitude
                'dt': date
            }
            response = requests.get(weather_url, params=params)
            response.raise_for_status()
            data = response.json()
            if 'forecast' in data and 'forecastday' in data['forecast']:
                temperature = data['forecast']['forecastday'][0]['day']['avgtemp_c']
                historical_data.append({'date': date, 'temperature': temperature})
    except Exception as e:
        print(f"Error fetching historical weather: {e}")
    return historical_data

# Function to fetch weather data from WeatherAPI
def get_weather(lat, lon):
    try:
        weather_url = 'http://api.weatherapi.com/v1/current.json'
        params = {
            'key': weather_api_key,
            'q': f'{lat},{lon}',  # Query parameter for latitude and longitude
            'aqi': 'no'           # Optional parameter to exclude air quality information
        }
        response = requests.get(weather_url, params=params)
        response.raise_for_status()
        data = response.json()
        if 'current' in data:
            return data['current']['temp_c']  # Temperature in Celsius
    except Exception as e:
        print(f"Error fetching current weather: {e}")
    return None

# Callback to handle location queries, update the map, and fetch weather
@app.callback(
    [Output('map', 'figure'),
     Output('weather-line-chart', 'figure'),
     Output('location-info', 'children')],
    [Input('query-button', 'n_clicks')],
    [State('location-input', 'value')]
)
def update_map_and_weather(n_clicks, location_name):
    if n_clicks > 0 and location_name:
        coords = get_coordinates(location_name)
        if coords:
            lon, lat = coords['lon'], coords['lat']
            new_marker = {'lat': lat, 'lon': lon, 'text': location_name}
            
            # Update figure with new marker
            fig = go.Figure(go.Scattermapbox(
                lat=[lat],
                lon=[lon],
                mode='markers+text',
                marker=go.scattermapbox.Marker(size=22),
                text=[location_name],
                textposition='top right'
            ))
            
            # Center the map on the new marker
            fig.update_layout(
                autosize=True,
                hovermode='closest',
                mapbox=dict(
                    accesstoken=mapbox_access_token,
                    bearing=0,
                    center=dict(
                        lat=lat,
                        lon=lon
                    ),
                    pitch=0,
                    zoom=7,  # Adjust zoom level as needed
                    style='streets'
                ),
                width=1000,
                height=450
            )
            
            # Fetch the weather for the new marker's location
            temperature = get_weather(lat, lon)
            if temperature is not None:
                # location_info = (f"Location '{location_name}' added at Longitude = {lon}, Latitude = {lat}. "
                #                  f"Current temperature: {temperature}°C")
                location_info = (f"Current temperature: {temperature}°C")
            # else:
            #     location_info = f"Location '{location_name}' added at Longitude = {lon}, Latitude = {lat}. Weather data not found."
            
            # Fetch historical weather data
            historical_data = get_historical_weather(lat, lon)
            df = pd.DataFrame(historical_data)
            line_chart = go.Figure()
            if not df.empty:
                line_chart.add_trace(go.Scatter(
                    x=df['date'],
                    y=df['temperature'],
                    mode='lines+markers',
                    name='Temperature'
                ))
                line_chart.update_layout(
                    title=f'Historical Weather Data for {location_name}',
                    xaxis_title='Date',
                    yaxis_title='Temperature (°C)',
                    xaxis=dict(type='category')
                )
            else:
                line_chart.update_layout(title='No historical data available')
        else:
            location_info = f"Location '{location_name}' not found."
            line_chart = go.Figure()  # Empty chart
    else:
        fig = go.Figure()
        fig.update_layout(
            autosize=True,
            hovermode='closest',
            mapbox=dict(
                accesstoken=mapbox_access_token,
                bearing=0,
                center=dict(
                    lat=23.6978,
                    lon=120.9605
                ),
                pitch=0,
                zoom=7,
                style='streets'
            ),
            width=1000,
            height=450
        )
        
        location_info = "Enter a location and click 'Query' to show the weather data and location on the map"
        line_chart = go.Figure()  # Empty chart
    
    return fig, line_chart, location_info

# Callback to print coordinates to console when a marker is clicked
@app.callback(
    Output('map', 'clickData'),
    [Input('map', 'clickData')]
)
def print_coordinates(clickData):
    if clickData is not None:
        point = clickData['points'][0]
        longitude = point['lon']
        latitude = point['lat']
        print(f"Clicked coordinates: Longitude = {longitude}, Latitude = {latitude}")
    return clickData

# Run the app
if __name__ == '__main__':
    app.run_server(debug=True)
