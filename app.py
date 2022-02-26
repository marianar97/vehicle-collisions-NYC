import streamlit as st
import pandas as pd
import numpy as np
import pydeck as pdk
import plotly.express as px

DATE_TIME = "date/time"
DATA_URL = (
    'vehicle_collisions.csv'
)

@st.cache(persist=True)
def load_data(nrows):
    data = pd.read_csv(DATA_URL, nrows=nrows, parse_dates=[['CRASH_DATE', 'CRASH_TIME']])
    data.dropna(subset=['LATITUDE', 'LONGITUDE'], inplace=True)
    data.rename(lambda x: str(x).lower(), axis="columns", inplace=True)
    data.rename(columns={"crash_date_crash_time": "date/time"}, inplace=True)

    return data


def military_to_am_pm(hour):
    return 12 if hour in (12, 24) else hour % 12


def main():

    # title
    st.title("Vehicle Collisions in NYC")
    st.markdown("This web app helps you analyze Motor Vehicle Collisions in NYC 🗽💥🚗. ")

    # get period to analyze
    st.subheader("Please select the period of time you want to analyze")
    data = load_data(20000)
    start = st.date_input(
        "From:",
        data['date/time'].min())
    end = st.date_input(
        "To:",
        data['date/time'].max())
    start = pd.Timestamp(start)
    end = pd.Timestamp(end)
    data['date/time'] = pd.to_datetime(data['date/time'])
    start_date = data["date/time"] >= start
    end_date = data["date/time"] <= end
    between_two_dates = start_date & end_date
    data = data.loc[between_two_dates]
    

    # show date filtered data
    if st.checkbox("Show Raw Data", False, key='date_filtered'):
        st.subheader("Raw data")
        st.write(data)

    # Analyze location
    st.header("In which locations in NYC do people get into more accidents?")
    max_people_hurt = data.groupby(by='location')['injured_persons'].sum().max()
    injured_people = st.slider("Number of people injured in vehicle collisions", 0, int(max_people_hurt))
    st.map(data.query("injured_persons == @injured_people")[['latitude','longitude']].dropna(how="any"), zoom=2)
    original_data = data

    # Analyze time
    st.header("How many collisions occur during a given time of day?")
    hour = st.slider("Hour", 0, 23, 1)
    data = data[data['date/time'].dt.hour == hour]
    h1_am_pm = 'AM' if hour < 12 else 'PM'
    h2_am_pm = 'AM' if hour+1 < 12 else 'PM'
    start = military_to_am_pm(hour)
    end = military_to_am_pm(hour+1)
    st.markdown("Number of vehicle collisions between %i:00 %s and %i:00 %s: %i" % (start, h1_am_pm, end, h2_am_pm, data.shape[0]))

    # Initialize 3D graph
    midpoint = (np.average(data['latitude']), np.average(data['longitude']))
    st.write(pdk.Deck(
        map_style="mapbox://styles/mapbox/light-v9",
        initial_view_state={
            "latitude": midpoint[0],
            "longitude": midpoint[1],
            "zoom": 11,
            "pitch": 50,
        },
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

    st.subheader("Breakdown by minute between %i:00 %s and %i:00 %s" % (start, h1_am_pm, end, h2_am_pm))
    filtered_data = data[
        (data['date/time'].dt.hour >= hour) & (data['date/time'].dt.hour <= (hour+1))
    ]
    hist = np.histogram(filtered_data['date/time'].dt.minute, bins=60, range=(0,60))[0]
    chart_data = pd.DataFrame({'minute': range(60), 'crashes': hist})
    fig = px.bar(chart_data, x="minute", y="crashes", hover_data=['minute', 'crashes'], height=400)
    st.write(fig)

    st.header("Top 5 dangerous streets by type of injured")
    select = st.selectbox("Affected type of people",['pedestrians', 'cyclists', 'motorists'])

    selected_afftected_type = 'injured_' + select
    selected_afftected_type_conditional = selected_afftected_type + '>=1'

    if select:
        query = original_data.query(selected_afftected_type_conditional)[['on_street_name', selected_afftected_type]].sort_values(by=[selected_afftected_type], ascending=False).dropna(how='any')[:5]
        st.write(query)



    # show time filtered data
    if st.checkbox("Show Raw Data", False):
        st.subheader("Raw data")
        st.write(data)


if __name__ == '__main__':
    main()
