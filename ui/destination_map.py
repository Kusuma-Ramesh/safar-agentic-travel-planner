
"""Interactive destination map for Safar."""

from __future__ import annotations

import folium
import streamlit as st
from streamlit_folium import st_folium

from travel_agent.data_loader import (
    load_places,
    load_place_coordinates,
)


PLACE_ICONS = {
    "beach": "umbrella-beach",
    "fort": "landmark",
    "monument": "landmark",
    "museum": "building-columns",
    "temple": "place-of-worship",
    "park": "tree",
    "market": "store",
    "lake": "water",
}


def render_destination_map(
    city: str,
    selected_types: list[str] | None = None,
) -> None:
    """Render an interactive map showing attractions in a destination."""

    places = [
        place for place in load_places()
        if place["city"] == city
    ]

    coordinates = load_place_coordinates()

    map_places = [
        (place, coordinates[place["place_id"]])
        for place in places
        if place["place_id"] in coordinates
        and (
            not selected_types
            or place["type"] in selected_types
        )
    ]

    if not map_places:
        st.warning("No attractions with coordinates are available.")
        return

    center_lat = sum(
        coords["lat"] for _, coords in map_places
    ) / len(map_places)

    center_lon = sum(
        coords["lon"] for _, coords in map_places
    ) / len(map_places)

    destination_map = folium.Map(
        location=[center_lat, center_lon],
        zoom_start=11,
        tiles="OpenStreetMap",
        control_scale=True,
    )

    for place, coords in map_places:
        popup_html = f"""
        <div style="width:190px">
            <h4>{place['name']}</h4>
            <p>Category: {place['type'].title()}</p>
            <p>Rating: {place['rating']} / 5</p>
        </div>
        """

        folium.Marker(
            location=[coords["lat"], coords["lon"]],
            tooltip=place["name"],
            popup=folium.Popup(popup_html, max_width=250),
            icon=folium.Icon(
                color="blue",
                icon="info-sign",
            ),
        ).add_to(destination_map)

    st_folium(
        destination_map,
        use_container_width=True,
        height=520,
        returned_objects=[],
        key=f"safar_map_{city}",
    )

    st.caption(
        f"Showing {len(map_places)} attractions in {city}. "
        "Select a marker to view attraction details."
    )
