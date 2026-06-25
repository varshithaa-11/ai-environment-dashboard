import streamlit as st
import requests
import os
from dotenv import load_dotenv
import plotly.graph_objects as go
from groq import Groq

# Load API keys
load_dotenv()
WEATHER_API_KEY = os.getenv("WEATHER_API_KEY") or st.secrets.get("WEATHER_API_KEY")
GROQ_API_KEY = os.getenv("GROQ_API_KEY") or st.secrets.get("GROQ_API_KEY")

# Configure Groq
groq_client = Groq(api_key=GROQ_API_KEY)

# Page config
st.set_page_config(
    page_title="AI Environmental Dashboard",
    page_icon="🌍",
    layout="wide"
)

# Helper: Get AQI category
def get_aqi_info(aqi):
    if aqi <= 50:
        return "🟢", "Good"
    elif aqi <= 100:
        return "🟡", "Moderate"
    elif aqi <= 150:
        return "🟠", "Unhealthy for Sensitive Groups"
    elif aqi <= 200:
        return "🔴", "Unhealthy"
    elif aqi <= 300:
        return "🟣", "Very Unhealthy"
    else:
        return "⚫", "Hazardous"

# Title
st.title("🌍 AI Environmental & Pollution Dashboard")
st.markdown("Real-time weather, air quality and AI health tips")

# City input
city = st.text_input("🔍 Enter City Name", value="Hyderabad")

if city:
    # WEATHER DATA
    weather_url = f"http://api.openweathermap.org/data/2.5/weather?q={city}&appid={WEATHER_API_KEY}&units=metric"
    weather_res = requests.get(weather_url).json()

    if weather_res.get("cod") == 200:
        lat = weather_res["coord"]["lat"]
        lon = weather_res["coord"]["lon"]
        temp = weather_res["main"]["temp"]
        feels_like = weather_res["main"]["feels_like"]
        humidity = weather_res["main"]["humidity"]
        description = weather_res["weather"][0]["description"].title()
        wind_speed = weather_res["wind"]["speed"]

        # AIR POLLUTION DATA
        pollution_url = f"http://api.openweathermap.org/data/2.5/air_pollution?lat={lat}&lon={lon}&appid={WEATHER_API_KEY}"
        pollution_res = requests.get(pollution_url).json()

        aqi_raw = pollution_res["list"][0]["main"]["aqi"]
        components = pollution_res["list"][0]["components"]

        aqi_map = {1: 25, 2: 75, 3: 125, 4: 175, 5: 250}
        aqi = aqi_map.get(aqi_raw, 0)

        pm25 = round(components.get("pm2_5", 0), 2)
        pm10 = round(components.get("pm10", 0), 2)
        no2 = round(components.get("no2", 0), 2)
        co = round(components.get("co", 0), 2)
        o3 = round(components.get("o3", 0), 2)
        so2 = round(components.get("so2", 0), 2)

        aqi_color, aqi_status = get_aqi_info(aqi)

        # WEATHER CARDS
        st.markdown("---")
        st.subheader(f"📍 {city.title()} — {description}")

        col1, col2, col3, col4 = st.columns(4)
        col1.metric("🌡️ Temperature", f"{temp}°C", f"Feels {feels_like}°C")
        col2.metric("💧 Humidity", f"{humidity}%")
        col3.metric("💨 Wind Speed", f"{wind_speed} m/s")
        col4.metric(f"{aqi_color} AQI", f"{aqi}", aqi_status)

        # POLLUTION CARDS
        st.markdown("---")
        st.subheader("🌫️ Pollution Parameters")

        col5, col6, col7, col8 = st.columns(4)
        col5.metric("PM2.5", f"{pm25} µg/m³")
        col6.metric("PM10", f"{pm10} µg/m³")
        col7.metric("NO2", f"{no2} µg/m³")
        col8.metric("CO", f"{co} µg/m³")

        col9, col10 = st.columns(2)
        col9.metric("O3 (Ozone)", f"{o3} µg/m³")
        col10.metric("SO2", f"{so2} µg/m³")

        # AQI GAUGE
        st.markdown("---")
        st.subheader("📊 AQI Health Risk Gauge")

        fig = go.Figure(go.Indicator(
            mode="gauge+number",
            value=aqi,
            title={"text": f"Air Quality Index — {aqi_status}"},
            gauge={
                "axis": {"range": [0, 300]},
                "bar": {"color": "darkblue"},
                "steps": [
                    {"range": [0, 50], "color": "green"},
                    {"range": [50, 100], "color": "yellow"},
                    {"range": [100, 150], "color": "orange"},
                    {"range": [150, 200], "color": "red"},
                    {"range": [200, 300], "color": "purple"},
                ]
            }
        ))
        st.plotly_chart(fig, use_container_width=True)

        # CITY COMPARISON
        st.markdown("---")
        st.subheader("🏙️ City AQI Comparison")

        compare_cities = ["Delhi", "Mumbai", "Hyderabad", "Chennai", "Kolkata"]
        aqi_values = []
        city_names = []

        for c in compare_cities:
            try:
                w = requests.get(
                    f"http://api.openweathermap.org/data/2.5/weather?q={c}&appid={WEATHER_API_KEY}&units=metric"
                ).json()
                if w.get("cod") == 200:
                    la = w["coord"]["lat"]
                    lo = w["coord"]["lon"]
                    p = requests.get(
                        f"http://api.openweathermap.org/data/2.5/air_pollution?lat={la}&lon={lo}&appid={WEATHER_API_KEY}"
                    ).json()
                    raw = p["list"][0]["main"]["aqi"]
                    converted = aqi_map.get(raw, 0)
                    aqi_values.append(converted)
                    city_names.append(c)
            except:
                pass

        if city_names:
            bar_fig = go.Figure(go.Bar(
                x=city_names,
                y=aqi_values,
                marker_color=[
                    "green" if v <= 50
                    else "yellow" if v <= 100
                    else "orange" if v <= 150
                    else "red"
                    for v in aqi_values
                ]
            ))
            bar_fig.update_layout(
                title="AQI Comparison Across Major Cities",
                xaxis_title="City",
                yaxis_title="AQI Value"
            )
            st.plotly_chart(bar_fig, use_container_width=True)

        # AI TIPS
        st.markdown("---")
        st.subheader("🤖 AI Health Tips")

        if st.button("Get AI Health Tips"):
            with st.spinner("AI analyzing conditions..."):
                prompt = f"""
                City: {city}
                Temperature: {temp}°C
                Humidity: {humidity}%
                AQI: {aqi} ({aqi_status})
                PM2.5: {pm25} µg/m³
                PM10: {pm10} µg/m³
                NO2: {no2} µg/m³
                CO: {co} µg/m³
                O3: {o3} µg/m³
                SO2: {so2} µg/m³

                Give 5 practical daily health tips based on these environmental conditions.
                Keep it simple and actionable. Use emojis.
                """
                response = groq_client.chat.completions.create(
                    model="llama-3.3-70b-versatile",
                    messages=[{"role": "user", "content": prompt}]
                )
                st.success(response.choices[0].message.content)

    else:
        st.error("❌ City not found! Please check the city name.")