# TeamArrow strategy team
This project was built for TeamArrow to make strategy decisions during the **World Solar Challenge**. <br>
https://replit.com/@yc-feng/team-arrow-strategy

## Weather Monitor Web Application
The Weather Monitor is a web application that provides real-time weather forecasts tailored for solar racing car strategies. Utilising both user-inputted geolocation and automatically fetched geolocation data, this application visualizes hourly weather forecasts on an interactive map.

### Features
1. **Interactive Map**: Visualize the racing path, and get an overview of the weather conditions.
2. **Dynamic Weather Data**: Fetch hourly weather data based on the user's location and speed. Visualize cloud cover, irradiance, and wind data in real-time.
3. **Geolocation**: Users can either manually input their location or use the browser's geolocation feature.

### Tech Stack
- Backend: Flask
- Frontend: HTML, CSS, JavaScript, and Bootstrap
- Data Visualization: Chart.js and Folium
- <del>Data Source: Solcast API<del>

27/11/2023 update:
- Data Source: Tomorrow.io API

### Usage
1. Home Page:
Accessible at the base URL ```(/)``` or ```/index```.
Users can view the current weather conditions on the interactive map.
The weather conditions can be refreshed based on latitude, longitude, and speed.
2. Cronjob Endpoint:
Located at ```/cronjob```.
Returns a success message when accessed. Useful for testing and monitoring.
3. Refresh Endpoint:
Located at ```/refresh```.
Accepts both GET and POST requests.
Users can refresh the weather data by providing latitude, longitude, and speed.

### Future Improvements
- Integrate with real-time solar car data.
- Enhance the user interface for better user experience.
