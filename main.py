from urllib.error import URLError
import folium
import altair as alt
import pandas as pd
import streamlit as st
from io import BytesIO
import plotly.express as px

st.set_page_config(page_title="BOD Analysis",
                   page_icon=r"/Users/macbookpro14/Desktop/Fake Desktop/SETEC/Year 4/Python/Covid-19/images/icons8-corona-virus-32.png")
st.title("Covid 19 Analysis Dashboard")


@st.cache_data
def get_UN_data():
    # Load the dataset
    df = pd.read_csv(
        r"/Users/macbookpro14/Desktop/Fake Desktop/SETEC/Year 4/Python/Covid-19/Datasets/worldometer_coronavirus_summary_data_with_latlong.csv")

    return df


try:
    df = get_UN_data()
    # Print the columns to check names
    st.write("Available columns in the dataset:", df.columns)

    countries = st.multiselect(
        "Choose countries", list(df['country']), ["USA", "India", "Brazil", "France", "Germany"]
    )
    if not countries:
        st.error("Please select at least one country.")
    else:
        # Check if 'country' column exists in DataFrame
        if 'country' not in df.columns or 'total_confirmed' not in df.columns:
            st.error("Required columns are missing from the dataset.")
        else:
            data = df[df['country'].isin(countries)]
            # Display the data
            st.write("### Global Covid-19 Data", data.sort_index())
            # Filter the data
            data = df[df['country'].isin(countries)][['country', 'total_confirmed', 'total_deaths', 'active_cases', 'latitude', 'longitude']]
            print(df['country'].head())
            data = data.sort_values(by='total_confirmed', ascending=False)
            data_sorted = data.sort_values(by='total_confirmed', ascending=False)
            # Create the Altair chart
            chart = (
                alt.Chart(data)
                    .mark_bar()
                    .encode(
                    x=alt.X('country:N', title='Country', sort=None),
                    y=alt.Y('total_confirmed:Q', title='Total Confirmed Cases', axis=alt.Axis(format=','))
                        .scale(domain=[0, data['total_confirmed'].max() * 1.1]),
                    color='country:N'
                )
                    .properties(title='Total Confirmed Cases by Country')
            )


            # Scatter plot with linked brushing
            brush = alt.selection(type='interval', encodings=['x', 'y'])

            scatter_plot = (
                alt.Chart(data)
                    .mark_point(size=60)
                    .encode(
                    x=alt.X('total_deaths:Q', title='Total Deaths', axis=alt.Axis(format=',')),
                    y=alt.Y('total_confirmed:Q', title='Total Confirmed Cases', axis=alt.Axis(format=',')),
                    color='country:N',
                    tooltip=
                    [
                        alt.Tooltip('country:N', title='Country'),
                        alt.Tooltip('total_confirmed:Q', title='Total Confirmed', format=',d'),
                        alt.Tooltip('total_deaths:Q', title='Total Deaths', format=',d')
                    ]
                )
                    .add_selection(brush)
                    .properties(title='Scatter Plot of Total Confirmed Cases vs. Total Deaths')
            )

            st.altair_chart(scatter_plot, use_container_width=True)

            # Bar chart for total confirmed cases
            st.altair_chart(chart, use_container_width=True)


            # Mosaic Chart
            # Calculate proportions
            data['total_deaths_proportion'] = data['total_deaths'] / data['total_deaths'].sum()

            mosaic_chart = (
                alt.Chart(data)
                    .mark_rect()
                    .encode(
                    x=alt.X('total_deaths_proportion:Q', stack='zero', title='Proportion of Total Deaths'),
                    y=alt.Y('country:N',
                            sort=alt.EncodingSortField(field='total_deaths', op='sum', order='descending')),
                    color=alt.Color('total_deaths:Q', scale=alt.Scale(scheme='blues')),
                    tooltip=[
                        alt.Tooltip('country:N', title='Country'),
                        alt.Tooltip('total_deaths:Q', title='Total Deaths', format=',d')
                    ]
                )
                    .properties(title='Mosaic Chart of Total Deaths by Country')
            )

            st.altair_chart(mosaic_chart, use_container_width=True)

        # Center the map based on the average latitude and longitude
        map_center = [data['latitude'].mean(), data['longitude'].mean()]
        covid_map = folium.Map(location=map_center, zoom_start=2, control_scale=True)

        # Add CircleMarkers to the map
        for _, row in data.iterrows():
            folium.CircleMarker(
                location=[row['latitude'], row['longitude']],
                radius=5,  # Adjust radius based on total confirmed cases
                color='red',
                fill=True,
                fill_color='red',
                fill_opacity=0.6,
                tooltip=(f"Country:{row['country']}<br>"
                         f"Active Cases:{row['active_cases']:,}<br>"
                         f"Total Confirmed:{row['total_confirmed']:,}")
            ).add_to(covid_map)

        # Save the map to an HTML file
        map_html = BytesIO()
        covid_map.save(map_html, close_file=False)
        map_html.seek(0)

        data_treemap = df[df['country'].isin(countries)][['country', 'total_deaths']]

        fig = px.treemap(data, path=['country'], values='total_deaths',
                         color='total_deaths', color_continuous_scale='Reds',
                         title='COVID-19 Deaths by Country',
                         hover_data={'country': True, 'total_deaths': True, 'latitude': False, 'longitude': False})

        # Update hover template to show only country and total deaths, and disable hover on edges
        fig.update_traces(
            hovertemplate="<b>%{label}</b><br>Total Deaths: %{value:,}",
            marker=dict(line=dict(width=0)),  # Hide borders around rectangles
            hoverinfo='label+value',  # This disables hover info on the edges
            root_color="lightgrey"  # Optionally, you can set the root background color
        )

        st.plotly_chart(fig)

        # Display the map in Streamlit
        st.write("### COVID-19 Data Map")
        st.components.v1.html(map_html.getvalue().decode(), height=600, width=800)

except URLError as e:
    st.error(
        """
        **This demo requires internet access.**
        Connection error: %s
    """
        % e.reason
    )


