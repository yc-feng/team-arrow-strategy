from flask import Flask, render_template, request
import functions

app = Flask(__name__, template_folder='template')

@app.route("/index")
@app.route("/")
def home():

  map_html, time_labels, cloud_cover_data, irradiance_data, wind_speed_data, wind_direction_data = functions.get_map()

  return render_template('dashboard.html', 
                         speed = 0, 
                         map_content = map_html, 
                         time_labels = time_labels, 
                         cloud_cover_data = cloud_cover_data, 
                         irradiance_data = irradiance_data,
                         wind_speed_data = wind_speed_data,
                         wind_direction_data = wind_direction_data)

@app.route("/cronjob")
def test():
  return "Successful"

@app.route('/refresh', methods=['GET', 'POST'])
def refresh():
  if request.method == 'POST':
    latitude = request.form.get('latitude')
    longitude = request.form.get('longitude')
    speed = request.form.get('speed')

    # Process the data or perform any action with the received data here
    map_html, time_labels, cloud_cover_data, irradiance_data, wind_speed_data, wind_direction_data =\
      functions.get_map(float(latitude), float(longitude), int(speed))  
  else:
    speed = 0
    map_html, time_labels, cloud_cover_data, irradiance_data, wind_speed_data, wind_direction_data = functions.get_map()

  return render_template('dashboard.html', 
                         speed = speed, 
                         map_content = map_html, 
                         time_labels = time_labels, 
                         cloud_cover_data = cloud_cover_data, 
                         irradiance_data = irradiance_data,
                         wind_speed_data = wind_speed_data,
                         wind_direction_data = wind_direction_data)



if __name__ == "__main__":
  from waitress import serve
  app.run(host='0.0.0.0', port = 8080)