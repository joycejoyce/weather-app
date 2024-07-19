import dash
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output, State
import plotly.graph_objects as go
from dotenv import load_dotenv
import os
import requests

# Fetch Mapbox and Weather API access tokens from environment variables
load_dotenv()
mapbox_access_token = os.getenv('MAPBOX_ACCESS_TOKEN')
weather_api_key = os.getenv('WEATHER_API_KEY')

# Coordinates for three initial markers in Taiwan
marker_coords = [
    # {'lat': 25.038, 'lon': 121.5645, 'text': 'Taipei 101'},   # Taipei
    # {'lat': 24.1478, 'lon': 120.6736, 'text': 'Taichung Park'},  # Taichung
    # {'lat': 22.6273, 'lon': 120.3014, 'text': 'Kaohsiung Pier'}   # Kaohsiung
]

# Extract latitudes and longitudes for markers
latitudes = [coord['lat'] for coord in marker_coords]
longitudes = [coord['lon'] for coord in marker_coords]
texts = [coord['text'] for coord in marker_coords]

# Initialize the Dash app
app = dash.Dash(__name__)

# Create a Mapbox map with initial markers
fig = go.Figure(go.Scattermapbox(
    lat=latitudes,
    lon=longitudes,
    mode='markers+text',
    marker=go.scattermapbox.Marker(
        size=14
    ),
    text=texts,
    textposition='top right'
))

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
    height=800
)

# Define the layout of the app
app.layout = html.Div([
    # Container for the form at the top
    html.Div([
        html.H1("Map App"),
        html.Div([
            dcc.Input(id='location-input', type='text', placeholder='Enter location name...'),
            html.Button('Query', id='query-button', n_clicks=0),
        ], style={'margin-bottom': '20px'})
    ], style={'text-align': 'center'}),
    
    # Container for displaying location information and temperature
    html.Div(id='location-info'),
    
    # Container for the map
    html.Div([
        dcc.Graph(id='map', figure=fig, style={'width': '1000px', 'height': '800px'}),
    ])
])

# Function to fetch coordinates from Mapbox Geocoding API
def get_coordinates(location_name):
    geocoding_url = f'https://api.mapbox.com/geocoding/v5/mapbox.places/{location_name}.json'
    params = {
        'access_token': mapbox_access_token,
        'limit': 1
    }
    response = requests.get(geocoding_url, params=params)
    data = response.json()
    if data['features']:
        coordinates = data['features'][0]['geometry']['coordinates']
        return {'lon': coordinates[0], 'lat': coordinates[1]}
    return None

# Function to fetch weather data from Weather API
def get_weather(lat, lon):
    weather_url = 'http://api.weatherapi.com/v1/current.json'
    params = {
        'key': weather_api_key,
        'q': f'{lat},{lon}',  # Query parameter for latitude and longitude
        'aqi': 'no'           # Optional parameter to exclude air quality information
    }
    response = requests.get(weather_url, params=params)
    data = response.json()
    if 'current' in data:
        return data['current']['temp_c']  # Temperature in Celsius
    return None

# Callback to handle location queries, update the map, and fetch weather
@app.callback(
    [Output('map', 'figure'),
     Output('location-info', 'children')],
    [Input('query-button', 'n_clicks')],
    [State('location-input', 'value')]
)
def update_map(n_clicks, location_name):
    if n_clicks > 0 and location_name:
        coords = get_coordinates(location_name)
        if coords:
            lon, lat = coords['lon'], coords['lat']
            new_marker = {'lat': lat, 'lon': lon, 'text': location_name}
            
            # Update figure with new marker
            fig = go.Figure(go.Scattermapbox(
                lat=latitudes + [lat],
                lon=longitudes + [lon],
                mode='markers+text',
                marker=go.scattermapbox.Marker(size=14),
                text=texts + [location_name],
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
                    zoom=12,  # Adjust zoom level as needed
                    style='streets'
                ),
                width=1000,
                height=800
            )
            
            # Fetch the weather for the new marker's location
            temperature = get_weather(lat, lon)
            if temperature is not None:
                location_info = (f"Location '{location_name}' added at Longitude = {lon}, Latitude = {lat}. "
                                 f"Current temperature: {temperature}°C")
            else:
                location_info = f"Location '{location_name}' added at Longitude = {lon}, Latitude = {lat}. Weather data not found."
        else:
            location_info = f"Location '{location_name}' not found."
    else:
        fig = go.Figure(go.Scattermapbox(
            lat=latitudes,
            lon=longitudes,
            mode='markers+text',
            marker=go.scattermapbox.Marker(size=14),
            text=texts,
            textposition='top right'
        ))
        
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
            height=800
        )
        
        location_info = "Enter a location and click 'Query' to add a marker."
    
    return fig, location_info

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
