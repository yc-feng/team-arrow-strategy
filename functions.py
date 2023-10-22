import pandas as pd
import folium
from folium import PolyLine, Marker
import folium.plugins as plugins
import requests
import json
from datetime import datetime, timedelta
import math
import pytz
from solcast import forecast


# time: datetime
# timesteps: minutely/ hourly
def get_weather_forecast_hourly(latitude, longitude, time, timesteps, API_KEY):
  """
    Fetches hourly weather forecast data for a given latitude and longitude.

    Args:
        latitude (float): The latitude of the location.
        longitude (float): The longitude of the location.
        time (datetime): The reference time for the forecast.
        timesteps (str): Specifies if the data should be 'minutely' or 'hourly'.
        API_KEY (str): The API key for the weather data provider.

    Returns:
        dict: A dictionary containing the forecasted weather details for the specified time.
    """
  BASE_URL = 'https://api.tomorrow.io/v4/weather/forecast'

  # Prepare request parameters
  params = {
      'location': f'{latitude},{longitude}',
      'units': 'metric',
      'apikey': API_KEY
  }

  # Make the request
  response = requests.get(BASE_URL, params=params)
  if response.status_code == 200:
    data = response.json()
    timeline = data['timelines'][timesteps]
    for hour in timeline:
      # Convert string to datetime object
      hour_time = datetime.strptime(hour['time'], "%Y-%m-%dT%H:%M:%SZ")
      if (timesteps == 'minutely'
          or timesteps == 'hourly') and hour_time > time:
        return {
            'Time': hour_time,
            'Temperature (°C)': hour['values']['temperature'],
            'Cloud Cover (%)': hour['values']['cloudCover'],
            'UV Index': hour['values']['uvIndex'],
            'Visibility': hour['values']['visibility'],
            'Weather Code': hour['values']['weatherCode'],
            'Wind Speed (m/s)': hour['values']['windSpeed'],
            'Wind Direction': hour['values']['windDirection']
        }
  else:
    print(
        f"Error with status code: {response.status_code}. Message: {response.text}"
    )
    return None


def get_weather_forecast(latitude, longitude, time):

  df = forecast.radiation_and_weather(latitude=latitude,
                                      longitude=longitude,
                                      output_parameters=[
                                          'air_temp', 'cloud_opacity', 'dni',
                                          'ghi', 'gti', 'wind_direction_10m',
                                          'wind_speed_10m'
                                      ]).to_pandas()

  dt_tz_aware = time.replace(tzinfo=pytz.UTC)

  for index, row in df.iterrows():
    if index >= dt_tz_aware:

      index_as_datetime = index.to_pydatetime().replace(
          tzinfo=pytz.UTC) + timedelta(hours=10, minutes=30)

      result_dict = dict(row)
      result_dict['Time'] = index_as_datetime
      return result_dict

  return None


def add_wind_arrow(m, start_lat, start_lon, wind_direction, color='red'):
  """
    Add a small arrow to the map to visualize wind direction.

    Args:
    - m (folium.Map): The map object.
    - start_lat (float): Starting latitude.
    - start_lon (float): Starting longitude.
    - wind_direction (float): Wind direction in degrees.
    - color (str): Color of the arrow.
    """
  # Calculate end point using a small distance and the wind direction
  radius = 0.5
  end_lat = start_lat + radius * math.sin(math.radians(90 - wind_direction))
  end_lon = start_lon + radius * math.cos(math.radians(90 - wind_direction))

  # Create a line from start to end
  line = folium.PolyLine([(start_lat, start_lon), (end_lat, end_lon)],
                         color=color,
                         opacity=0.0).add_to(m)

  # Attach an arrow to the line
  plugins.PolyLineTextPath(
      line,
      '\u27A4',  # This is a Unicode character for an arrow
      repeat=True,
      orientation=180,
      attributes={
          'fill': color,
          'font-weight': 'bold',
          'font-size': '40'
      }).add_to(m)


def get_weather_name(weather_code, day_type="default"):
  """
    Function to get the weather name based on the code and day type.

    Args:
    - weather_code (str): The weather code to search for.
    - day_type (str): The type of day (default, fullDay, day, night). Default is "default".

    Returns:
    - str: The weather name corresponding to the provided code and day type.
    """

  # Load the JSON data
  with open("weatherCode.json", 'r') as file:
    data = json.load(file)

  # Dictionaries for each day type
  weather_dicts = {
      "default": data["weatherCode"],
      "fullDay": data["weatherCodeFullDay"],
      "day": data["weatherCodeDay"],
      "night": data["weatherCodeNight"]
  }

  # Get the appropriate dictionary based on the day type
  weather_dict = weather_dicts[day_type]

  # Return the weather name or "Unknown" if the code is not found
  return weather_dict.get(str(weather_code), "Unknown")


def get_near_point(lat, lon, path_df):
  """
    Function to get the nearest point to the provided coordinates.

    Args:
    - lat (float): The latitude of the location.
    - lon (float): The longitude of the location.
    - path_df (pd.DataFrame): The dataframe containing the path coordinates.

    Returns:
    - index of path_df: The nearest point to the provided coordinates.
    """

  # Calculate the squared distance for each row in the dataframe
  distances = path_df.apply(lambda x: (x['Latitude'] - lat)**2 +
                            (x['Longitude'] - lon)**2,
                            axis=1)

  # Get the index of the minimum distance
  nearest_idx = distances.idxmin()

  return path_df.iloc[nearest_idx]


def get_selected_indices(nearest_point, path_df, current_speed):
  '''
    Function to get the indices of the points to be selected based on the current speed.

    Args:
    - nearest_point (pd.DataFrame): The nearest point to the provided coordinates.
    - path_df (pd.DataFrame): The dataframe containing the path coordinates.
    - current_speed (float): The current speed.

    Returns:
    - list: The indices of the points to be selected.

    e.g. 
    selected_indices # [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
    '''
  if current_speed == 0:
    return []

  selected_indices = []
  for i in range(int() + 1, len(path_df)):
    if len(selected_indices) > 10:
      break
    if path_df.iloc[i]['Cumulative Distance'] - path_df.iloc[
        selected_indices[-1] if selected_indices else int(nearest_point[0])][
            'Cumulative Distance'] >= (current_speed):
      selected_indices.append(i)
  return selected_indices


def get_weather_popup(weather_dic, head=True, current_speed=0):
  '''
    Function to get the popup for the weather information.

    Args:
    - weather_dic (dict): The dictionary containing the weather information.
    - head (bool): Whether to include the heading for the popup. Default is True.
    - current_speed (float): The current speed. Default is 0.

    Returns:
    - folium.Popup: The popup for the weather information.
    '''

  if head:
    current_speed_text = f'Current Speed: {current_speed} km/hr<br>'
  else:
    current_speed_text = ''

  iframe = folium.IFrame(f'''<font face="monospace">
                                    Time: {weather_dic['Time'].strftime("%Y-%m-%d %H:%M:%S")}<br>
                                    {current_speed_text}
                                    Temperature: {weather_dic['air_temp']} °C<br>
                                    Cloud Cover: {weather_dic['cloud_opacity']} %<br>
                                    DHI: {weather_dic['dni']} W/m2<br>
                                    GHI: {weather_dic['ghi']} W/m2<br>
                                    GTI: {weather_dic['gti']} W/m2<br>
                                    Wind Speed (m/s): {weather_dic['wind_speed_10m']} m/s<br>
                                    Wind Direction: {weather_dic['wind_direction_10m']} </font>'''
                         )

  popup = folium.Popup(iframe, min_width=250, max_width=250)

  return popup


# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
# Main Functions
# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -


def get_map(start_lat=-12.466296, start_lon=130.843145, current_speed=0):
  """
    Generate a map with the racing strategy dashboard.
    """
  path_df = pd.read_csv('path.csv')

  # Get the nearest point to the start coordinates
  nearest_point = get_near_point(start_lat, start_lon, path_df)

  my_map = folium.Map(
      location=[nearest_point['Latitude'], nearest_point['Longitude']],
      zoom_start=8)

  path_coordinates = path_df[['Latitude', 'Longitude']].values.tolist()

  path = PolyLine(locations=path_coordinates, color='blue', weight=5)
  path.add_to(my_map)

  # Select points every 60 mins depend on current speed
  selected_indices = get_selected_indices(nearest_point, path_df,
                                          current_speed)

  #weather_dic = get_weather_forecast_hourly(nearest_point['Latitude'], nearest_point['Longitude'], datetime.utcnow(), 'minutely', tomorrow_key)
  weather_dic = get_weather_forecast(nearest_point['Latitude'],
                                     nearest_point['Longitude'],
                                     datetime.utcnow())

  # keep the weather data for visualization
  weather_df = pd.DataFrame(weather_dic, index=[0])
  popup = get_weather_popup(weather_dic, True, current_speed)
  Marker([nearest_point['Latitude'], nearest_point['Longitude']],
         popup=popup,
         icon=folium.Icon(color='red', icon='location-dot',
                          prefix='fa')).add_to(my_map)

  add_wind_arrow(my_map, nearest_point['Latitude'], nearest_point['Longitude'],
                 weather_dic['wind_direction_10m'])

  # Add other points to the map
  for count, idx in enumerate(selected_indices):
    if count > 9:
      break
    lat, lon = path_df.iloc[idx]['Latitude'], path_df.iloc[idx]['Longitude']

    weather_dic = get_weather_forecast(
        lat, lon,
        datetime.utcnow() + timedelta(hours=count + 1))

    weather_df = pd.concat(
        [weather_df, pd.DataFrame(weather_dic, index=[0])],
        axis=0,
        ignore_index=True)

    popup = get_weather_popup(weather_dic, False)
    Marker([lat, lon], popup=popup).add_to(my_map)
    #time.sleep(1) # Sleep for 1 seconds

    add_wind_arrow(my_map, lat, lon, weather_dic['wind_direction_10m'])

  # Extract map content
  map_html = my_map._repr_html_()

  # Extract time and speed data
  time_labels = [t.strftime('%H:%M:%S') for t in weather_df['Time'].dt.time]
  cloud_cover_data = weather_df['cloud_opacity'].tolist()
  irradiance_data = weather_df['gti'].tolist()
  wind_speed_data = weather_df['wind_speed_10m'].tolist()
  wind_direction_data = weather_df['wind_direction_10m'].tolist()

  return map_html, time_labels, cloud_cover_data, irradiance_data, wind_speed_data, wind_direction_data
