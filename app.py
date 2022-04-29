from logging import exception
import streamlit as st
import pandas as pd
import numpy as np
import pydeck as pdk
import plotly.express as px

DATE_TIME = "date/time"
DATA_URL = (
    'small_vehicle_collisions.csv'
)

@st.cache(persist=True)
def load_data():
    data = pd.read_csv(DATA_URL, parse_dates=[['CRASH_DATE', 'CRASH_TIME']])
    data.dropna(subset=['LATITUDE', 'LONGITUDE'], inplace=True)
    data.rename(lambda x: str(x).lower(), axis="columns", inplace=True)
    data.rename(columns={"crash_date_crash_time": "date/time"}, inplace=True)

    return data


def military_to_am_pm(hour):
    return 12 if hour in (12, 24) else hour % 12


def number_accidents_by_locations(data):
    st.header("In which locations in NYC do people get into more accidents?")
    max_people_hurt = max(data.groupby(by='location')['injured_persons'].sum().max(),0)
    injured_people = st.slider("Number of people injured in vehicle collisions", 1, int(max_people_hurt)+1)
    st.map(data.query("injured_persons >= @injured_people")[['latitude','longitude']].dropna(how="any"))


def select_time(data):
    hour = st.slider("Hour", 0, 23, 1)
    data = data[data['date/time'].dt.hour == hour]
    h1_am_pm = 'AM' if hour < 12 else 'PM'
    h2_am_pm = 'AM' if hour+1 < 12 else 'PM'
    start = military_to_am_pm(hour)
    end = military_to_am_pm(hour+1)
    return data, h1_am_pm, h2_am_pm, start, end, hour


def map_3d(data):
    midpoint = (np.average(data['latitude']), np.average(data['longitude']))
    try:
        initial_view_state = {
            "latitude": midpoint[0],
            "longitude": midpoint[1],
            "zoom": 11,
            "pitch": 50,
        }
    except exception:
        initial_view_state = {
            "zoom": 11,
            "pitch": 50,
        }
    st.write(pdk.Deck(
        map_style="mapbox://styles/mapbox/light-v9",
        initial_view_state=initial_view_state,
        layers=[
            pdk.Layer(
                "HexagonLayer",
                data=data[['date/time', 'latitude', 'longitude']],
                get_position=["longitude", "latitude"],
                auto_highlight=True,
                radius=100,
                extruded=True,
                pickable=True,
                elevation_scale=4,
                elevation_range=[0, 1000],
            ),
        ],
    ))


def accidents_by_minute(data, h1_am_pm, h2_am_pm, start, end, hour):
    st.subheader("Breakdown by minute between %i:00 %s and %i:00 %s" % (start, h1_am_pm, end, h2_am_pm))
    filtered_data = data[
        (data['date/time'].dt.hour >= hour) & (data['date/time'].dt.hour <= (hour+1))
    ]
    hist = np.histogram(filtered_data['date/time'].dt.minute, bins=60, range=(0,60))[0]
    chart_data = pd.DataFrame({'minute': range(60), 'crashes': hist})
    fig = px.bar(chart_data, x="minute", y="crashes", hover_data=['minute', 'crashes'], height=400, color_discrete_sequence=['indianred'])
    st.write(fig)


def accidents_by_hour(data):
    hist = np.histogram(data['date/time'].dt.hour, bins=24, range=(0,24))[0]
    chart_data = pd.DataFrame({'hour': range(24), 'crashes': hist})
    fig = px.bar(chart_data, x="hour", y="crashes", hover_data=['hour', 'crashes'], height=400, color_discrete_sequence=['indianred'])
    st.write(fig)


def top_5_dangerous_streets(data):
    st.header("Top 5 dangerous streets by type of injured")
    select = st.selectbox("Affected type of people",['pedestrians', 'cyclists', 'motorists'])

    selected_afftected_type = 'injured_' + select
    selected_afftected_type_conditional = selected_afftected_type + '>=1'

    if select:
        query = data.query(selected_afftected_type_conditional)[['on_street_name', selected_afftected_type]].sort_values(by=[selected_afftected_type], ascending=False).dropna(how='any')[:5]
        st.write(query)


def show_data(data, key):
    if st.checkbox("Show Raw Data", False, key=key):
        st.subheader("Raw data")
        st.write(data)


def main():

    # title
    st.title("Vehicle Collisions in NYC")
    st.markdown("This web app helps you analyze Motor Vehicle Collisions in NYC🗽💥🚗. \n")

    data = load_data()
    number_accidents_by_locations(data)

    original_data = data

    st.header("How many crashes occur during a given time of day?")
    accidents_by_hour(original_data)
    data, h1_am_pm, h2_am_pm, start, end, hour= select_time(data)
    st.markdown("Number of vehicle collisions between %i:00 %s and %i:00 %s: %i" % (start, h1_am_pm, end, h2_am_pm, data.shape[0]))    # Initialize 3D graph
    map_3d(data)
    accidents_by_minute(data, h1_am_pm, h2_am_pm, start, end, hour)
    show_data(data, key="filtered_by_hour_and_date")

    top_5_dangerous_streets(original_data)


if __name__ == '__main__':
    main()
