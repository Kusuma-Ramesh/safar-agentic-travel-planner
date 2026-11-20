# Safar – Agentic AI-Based Travel Planning Assistant

Safar is an AI-powered travel planning assistant built using **Python, LangChain, and Streamlit**. It helps users plan trips by searching available flight and hotel options, discovering attractions, checking weather conditions, generating day-wise itineraries, and estimating travel budgets.

The application uses a LangChain-based agent to interpret travel requests and select appropriate tools. It also includes a rule-based fallback planner so that users can generate itineraries even when an LLM API is unavailable.

---

## Key Features

- **AI-Powered Travel Planning:** Understands natural-language travel requests and generates personalized itineraries using a LangChain agent.
- **Flight Search:** Searches the available flight dataset based on origin, destination, travel dates, and passenger requirements.
- **Hotel Recommendations:** Recommends accommodation based on destination, budget, and available amenities.
- **Places Discovery:** Finds attractions and activities based on destination and category.
- **Weather Forecasting:** Retrieves weather information using the Open-Meteo API.
- **Flight Weather Monitor:** Checks forecast weather conditions around scheduled departure and arrival times and displays weather-risk indicators.
- **Interactive Destination Map:** Displays destination attractions and their locations using an interactive Folium map.
- **Day-Wise Itinerary:** Generates structured travel plans for trips ranging from 3 to 7 days.
- **Budget Estimation:** Calculates flight, accommodation, food, and local transportation costs.
- **Budget Optimization:** Attempts to find lower-cost combinations and indicates when the available options still exceed the user's budget.
- **Reasoning and Tool Traces:** Displays why options were selected and which tools were used during planning.
- **Rule-Based Fallback:** Provides itinerary generation when the LLM is unavailable or an agent request fails.
- **Trip Management:** Saves and retrieves trip plans using SQLite.
- **Export Options:** Allows users to download trip information in JSON and text formats.
- **Explore Data:** Provides interactive filters to explore available flights, hotels, and places.
- **How It Works:** Explains the application's planning workflow.

---

## Technology Stack

| Component | Technologies |
|---|---|
| Programming Language | Python |
| AI Agent Framework | LangChain |
| LLM Integration | Groq, OpenAI, Anthropic |
| LLM Model | Configurable through environment variables |
| User Interface | Streamlit |
| Weather API | Open-Meteo |
| Interactive Maps | Folium, Streamlit-Folium |
| Database | SQLite |
| Data Storage | JSON |
| Testing | Pytest |
| Environment Management | Python Virtual Environment |

---

## Project Architecture

Safar follows a modular architecture that separates the user interface, agent logic, planning functionality, external API integration, data handling, and database operations.

### Application Workflow

1. **Understand the Request:** The application receives the user's travel requirements, including origin, destination, dates, number of travellers, and budget.
2. **Agent Decision-Making:** The LangChain agent interprets the request and determines which tools are required.
3. **Tool Execution:** The agent can use flight search, hotel recommendation, places discovery, weather lookup, and budget estimation tools.
4. **Itinerary Generation:** The planner combines the available information to create a day-wise travel itinerary.
5. **Verification:** The application validates selected options and recalculates costs before presenting the result.
6. **Fallback Handling:** If the LLM agent is unavailable or encounters an error, the rule-based planner can generate a trip plan.
7. **Final Output:** The application presents the itinerary, travel options, weather information, budget breakdown, and selection reasoning.

---

## Project Structure

```text
travel-planning-assistant/
│
├── app.py
│
├── ui/
│   ├── components.py
│   ├── destination_map.py
│   └── styles.py
│
├── travel_agent/
│   ├── config.py
│   ├── data_loader.py
│   ├── models.py
│   ├── planner.py
│   ├── agent.py
│   ├── query_parser.py
│   ├── formatting.py
│   ├── db.py
│   ├── cli.py
│   │
│   └── tools/
│       ├── flights.py
│       ├── hotels.py
│       ├── places.py
│       ├── weather.py
│       ├── flight_weather.py
│       ├── budget.py
│       └── lc_tools.py
│
├── data/
│   ├── flights.json
│   ├── hotels.json
│   └── places.json
│
├── docs/
│   └── sample output and documentation
│
├── tests/
│   └── automated test cases
│
├── .env.example
├── .gitignore
├── requirements.txt
└── README.md
```

---

## Installation and Setup

### 1. Clone the Repository

```bash
git clone <your-github-repository-url>
cd travel-planning-assistant
```

### 2. Create a Virtual Environment

**Windows PowerShell:**

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

**macOS / Linux:**

```bash
python -m venv .venv
source .venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure Environment Variables

Create a `.env` file in the project root using `.env.example` as a reference.

Safar supports the following LLM providers:

- Groq
- OpenAI
- Anthropic

Add the API key for the provider you want to use.

Example configuration for Groq:

```env
GROQ_API_KEY=your_groq_api_key
LLM_PROVIDER=groq
LLM_MODEL=openai/gpt-oss-120b
```

The provider and model can be changed through environment variables.

If no supported API key is configured, the application can use its rule-based planning engine.

**Important:** Never upload your actual `.env` file or API keys to GitHub.

### 5. Run the Application

```bash
streamlit run app.py
```

The application will open in your browser.

---

## Application Modules

| Module | Description |
|---|---|
| `travel_agent/tools/flights.py` | Searches available flight options from the flight dataset. |
| `travel_agent/tools/hotels.py` | Recommends hotels based on user requirements and available amenities. |
| `travel_agent/tools/places.py` | Discovers destination attractions and activities. |
| `travel_agent/tools/weather.py` | Retrieves destination weather information through Open-Meteo. |
| `travel_agent/tools/flight_weather.py` | Evaluates forecast weather conditions around flight departure and arrival times. |
| `travel_agent/tools/budget.py` | Estimates trip expenses and budget breakdowns. |
| `travel_agent/tools/lc_tools.py` | Exposes application functions as LangChain tools. |
| `travel_agent/agent.py` | Handles LLM-based agent execution and tool selection. |
| `travel_agent/planner.py` | Generates and coordinates travel itineraries. |
| `travel_agent/query_parser.py` | Processes and extracts travel requirements. |
| `travel_agent/formatting.py` | Formats generated travel plans for presentation. |
| `travel_agent/data_loader.py` | Loads and manages JSON-based travel datasets. |
| `travel_agent/db.py` | Handles SQLite trip storage and retrieval. |
| `ui/destination_map.py` | Creates interactive destination maps with attraction markers. |
| `ui/components.py` | Contains reusable Streamlit interface components. |
| `ui/styles.py` | Manages application styling. |
| `app.py` | Main Streamlit application entry point. |

---

## AI Agent and Tool Integration

The application uses LangChain to connect an LLM with specialized travel-planning tools.

The agent interprets the user's request and selects the tools needed to gather relevant information and construct a travel plan.

### Available Agent Tools

1. **Flight Search Tool:** Retrieves available flight options.
2. **Hotel Recommendation Tool:** Finds accommodation options.
3. **Places Discovery Tool:** Retrieves attractions and activities.
4. **Weather Tool:** Obtains destination weather information.
5. **Budget Estimation Tool:** Calculates estimated travel expenses.

The application also displays tool execution information and selection reasoning to make the planning process easier to understand.

When the LLM-based agent cannot be used, the rule-based planner provides an alternative itinerary-generation path.

---

## Interactive Destination Map

Safar includes an interactive destination map built using **Folium and Streamlit-Folium**.

The map:

- Displays attractions for the selected destination.
- Uses configured geographical coordinates to position attractions.
- Provides markers for available places.
- Allows users to explore destination locations visually.

The map uses the application's configured place-coordinate data.

---

## Flight Weather Monitor

The Flight Weather Monitor uses Open-Meteo hourly forecast data to examine weather conditions around scheduled flight departure and arrival times.

It provides:

- Weather information near the departure location.
- Weather information near the arrival location.
- Weather-risk indicators such as Low, Moderate, High, or Unavailable.
- Weather information associated with the selected flight schedule.

**Important:** This feature evaluates forecast weather conditions. It does not provide live airline flight status, operational delays, cancellations, or real-time aviation tracking.

---

## Dataset and Data Handling

Safar uses JSON datasets to provide sample travel information.

### 1. Flight Dataset

The flight dataset contains available flight information, including route details, airline information, timings, and fares.

- Flight searches use the available dataset.
- The application can attempt to identify one-stop alternatives when direct routes are unavailable.
- Where applicable, estimated fares are clearly treated as estimates.
- The dataset contains sample schedules rather than live airline inventory.

### 2. Hotel Dataset

The hotel dataset contains accommodation information, including hotel names, destinations, prices, ratings, and available amenities.

Hotel recommendations are generated using the available dataset and user requirements.

### 3. Places Dataset

The places dataset contains destination attractions and their associated information.

- Includes 40 places across 8 cities.
- Supports attraction categories such as beaches, monuments, forts, and markets.
- Provides destination-specific recommendations.
- Supports the interactive destination map through configured geographical coordinates.

### 4. Weather Data

Weather information is retrieved using Open-Meteo.

The application uses forecast information when available and can use its configured archive or seasonal fallback logic when forecast data is unavailable.

Forecast availability depends on the requested dates and API availability.

---

## Budget Estimation

Safar calculates an estimated travel budget using the selected flights, accommodation, food, and local transportation assumptions.

The current configurable daily expense assumptions are:

| Budget Category | Estimated Cost Per Person Per Day |
|---|---:|
| Budget | ₹700 |
| Comfort | ₹1,100 |
| Luxury | ₹2,200 |

Additional calculation assumptions:

- Flight fares are calculated per traveller.
- Hotel accommodation is calculated based on the number of nights.
- The default accommodation calculation assumes one room for every two guests.
- The number of hotel nights is generally one less than the number of trip days.
- Food and local transportation estimates depend on the selected budget category.

The application attempts to optimize the available flight and hotel combinations to fit the user's budget.

If the lowest-cost available combination still exceeds the budget, the application displays the difference instead of claiming that the trip fits within the budget.

**Note:** All displayed costs are estimates based on the application's configured datasets and assumptions. Users should confirm actual prices and availability before making bookings.

---

## Database and Trip Management

Safar uses SQLite to store and retrieve saved trip plans.

Users can:

- Save generated travel itineraries.
- Retrieve previously saved trips.
- Review trip details.
- Export trip information in JSON and text formats.

The database is managed through `travel_agent/db.py`.

---

## Testing

The project includes automated tests using Pytest.

The tests cover application functionality, including:

- Travel data loading and validation.
- Flight search functionality.
- Hotel recommendation logic.
- Places discovery.
- Weather integration.
- Flight weather monitoring.
- Budget calculations.
- Itinerary generation.
- Agent and fallback behaviour.

Run the automated test suite:

```bash
python -m pytest -q
```

Check Python compilation:

```bash
python -m compileall -q app.py travel_agent ui
```

---

## Limitations

- Flight and hotel information is based on sample datasets and is not live booking inventory.
- Flight schedules and fares should be treated as sample information or estimates, not confirmed airline offers.
- The application does not book flights or hotels.
- Weather information depends on Open-Meteo forecast availability and API connectivity.
- Flight Weather Monitor provides forecast-based weather indicators, not live flight tracking.
- Attraction recommendations are limited to the places available in the configured dataset.
- Budget calculations are estimates and may differ from actual travel expenses.
- LLM-based planning requires a valid API key and network connectivity. The rule-based fallback can be used when the LLM is unavailable.

---

## Future Enhancements

Potential future improvements include:

- Integration with live flight and hotel booking APIs.
- Real-time flight status and delay information.
- More destination datasets and attraction coverage.
- Advanced route optimization.
- Improved personalization based on travel preferences.
- Additional language support.
- More detailed travel cost prediction.

---

## Conclusion

Safar demonstrates how **Agentic AI, LangChain, API integration, structured datasets, and interactive interfaces** can be combined to build an intelligent travel-planning application.

By integrating travel search tools, weather forecasting, budget estimation, itinerary generation, interactive maps, and trip management, Safar provides a unified platform for exploring and planning trips.

---

**Project:** Safar – Agentic AI-Based Travel Planning Assistant Using LangChain  
**Domain:** Travel and Tourism  
**Interface:** Streamlit  
**Core Framework:** LangChain  
**Language:** Python