from travel_agent.tools.flight_weather import _risk


def test_flight_weather_low_risk():
    level, _ = _risk([{
        "available": True, "weather_code": 0, "precipitation_probability": 5,
        "wind_gusts_kmh": 15, "visibility_m": 10000,
    }])
    assert level == "Low"


def test_flight_weather_high_risk_for_thunderstorm():
    level, explanation = _risk([{
        "available": True, "weather_code": 95, "precipitation_probability": 90,
        "wind_gusts_kmh": 75, "visibility_m": 500,
    }])
    assert level == "High"
    assert "Thunderstorm" in explanation


def test_flight_weather_moderate_for_heavy_rain_probability():
    level, _ = _risk([{
        "available": True, "weather_code": 61, "precipitation_probability": 65,
        "wind_gusts_kmh": 20, "visibility_m": 8000,
    }])
    assert level == "Moderate"


def test_flight_weather_unavailable_when_no_forecasts():
    level, _ = _risk([{"available": False}, {"available": False}])
    assert level == "Unavailable"
