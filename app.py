import streamlit as st
import time
import json
from datetime import datetime, timedelta
import pandas as pd
# Assuming LoganEventsClient is in a file named logan_events_client.py
from logan_events_client import LoganEventsClient

# --- Page Configuration ---
st.set_page_config(
    page_title="Logan Events Explorer",
    page_icon="🏔️",
    layout="wide",
)

# --- Theme-Aware CSS ---
# Uses Streamlit's CSS variables for better compatibility with light/dark themes
st.markdown("""
<style>
    /* General Card Styling */
    .event-card, .news-section {
        background-color: var(--secondary-background-color); /* Adapts to theme */
        border-radius: 10px;
        padding: 20px;
        margin-bottom: 20px;
        border-left: 5px solid var(--primary-color); /* Use theme's primary color */
        box-shadow: 0 2px 4px rgba(0,0,0,0.1); /* Subtle shadow for depth */
        transition: background-color 0.3s ease, border-left-color 0.3s ease; /* Smooth transition */
    }

    /* Event Card Specifics */
    .event-title {
        color: var(--primary-color); /* Use theme's primary color */
        font-size: 20px;
        font-weight: bold;
        margin-bottom: 5px;
    }
    .event-date {
        color: #28a745; /* Green often works in both modes, keep for emphasis */
        font-weight: bold;
        margin-bottom: 5px;
    }
    .event-location, .event-source {
        color: var(--text-color); /* Use theme's text color */
        opacity: 0.8; /* Slightly less prominent */
        font-size: 14px;
        margin-bottom: 10px;
    }
    .event-location {
        font-style: italic;
    }
    .event-description {
        color: var(--text-color); /* Use theme's text color */
        margin-bottom: 10px;
        opacity: 0.9;
    }
    .event-source a {
        color: var(--primary-color); /* Link color matches theme */
        text-decoration: none;
    }
    .event-source a:hover {
        text-decoration: underline;
    }

    /* News Section Specifics */
    .news-title {
        color: var(--primary-color); /* Use theme's primary color */
        font-size: 24px;
        font-weight: bold;
        margin-bottom: 15px;
    }
    .news-section p {
       color: var(--text-color);
       opacity: 0.9;
    }

    /* Loading Spinner - Streamlit handles this well, but we keep the class for potential future use */
    .loading-spinner {
        text-align: center;
        margin-top: 50px;
        margin-bottom: 50px;
    }

    /* Ensure sidebar button looks consistent */
    .stButton>button {
        width: 100%; /* Make button fill sidebar width */
        /* You can add more specific button styling here if needed */
    }
</style>
""", unsafe_allow_html=True)

# --- Helper Functions ---

def parse_event_date(date_string):
    """Attempts to parse various date formats found in event strings."""
    # Example formats to try (add more as needed based on observed data)
    formats_to_try = [
        "%B %d, %Y",        # "April 01, 2025"
        "%b %d, %Y",        # "Apr 01, 2025"
        "%m/%d/%Y",         # "04/01/2025"
        "%Y-%m-%d",         # "2025-04-01"
    ]
    # Clean up the string potentially removing time, ranges, etc.
    # This is a simple approach; more robust parsing might be needed
    parts = date_string.split()
    potential_date_str = " ".join(parts[:3]).replace(',', '') # Try first 3 words

    for fmt in formats_to_try:
        try:
            return datetime.strptime(potential_date_str, fmt)
        except (ValueError, IndexError):
            continue # Try next format

    # Fallback: Try to find a year and use today's month/day if desperate
    try:
        year_str = next((p for p in parts if p.isdigit() and len(p) == 4), None)
        if year_str:
            # This is a guess, might be inaccurate
             return datetime(int(year_str), datetime.now().month, datetime.now().day)
    except:
        pass

    return None # Indicate parsing failed

def display_results(data_to_display):
    """Renders the event and news data."""
    if not data_to_display:
        # Check if this was an initial load attempt or a specific search
        if st.session_state.get('search_triggered', False):
             st.warning("No events found matching your search criteria.")
        else:
             # This could be shown after the initial auto-load if nothing was found
             st.info("No events found for today, or still loading.")
        return

    if isinstance(data_to_display, dict) and "error" in data_to_display:
        st.error(f"An error occurred: {data_to_display['error']}")
        if 'raw_response' in data_to_display:
             st.code(data_to_display['raw_response'], language="json")
        return

    # Ensure data is a list
    if isinstance(data_to_display, str):
        try:
            data_to_display = json.loads(data_to_display)
        except json.JSONDecodeError:
            st.error("Received non-JSON response from the API.")
            st.code(data_to_display)
            return
    if not isinstance(data_to_display, list):
         st.error("Received unexpected data format from the API.")
         st.write(data_to_display) # Show what was received
         return


    # Separate events and potential news items
    events = [item for item in data_to_display if isinstance(item, dict) and all(k in item for k in ["title", "dates", "location", "description", "source"])]
    news_items = [item for item in data_to_display if isinstance(item, dict) and item.get("type") == "news"] # Assuming a 'type' field for news

    if not events:
        st.warning("No events found in the results.")
        # Still display news if available
    else:
        st.subheader(f"Found {len(events)} Events")
        # Display events in two columns
        col1, col2 = st.columns(2)
        for i, event in enumerate(events):
            container = col1 if i % 2 == 0 else col2
            with container:
                sanitized_title = event.get('title', 'N/A').replace('<', '&lt;').replace('>', '&gt;')
                sanitized_dates = event.get('dates', 'N/A').replace('<', '&lt;').replace('>', '&gt;')
                sanitized_location = event.get('location', 'N/A').replace('<', '&lt;').replace('>', '&gt;')
                sanitized_description = event.get('description', 'N/A').replace('<', '&lt;').replace('>', '&gt;')
                source_url = event.get('source', '#')
                # Basic check for valid URL structure
                if not source_url.startswith(('http://', 'https://')):
                    source_display = "Invalid Source URL"
                else:
                    source_display = source_url.replace('<', '&lt;').replace('>', '&gt;')


                st.markdown(f"""
                <div class="event-card">
                    <div class="event-title">{sanitized_title}</div>
                    <div class="event-date">📅 {sanitized_dates}</div>
                    <div class="event-location">📍 {sanitized_location}</div>
                    <div class="event-description">{sanitized_description}</div>
                    <div class="event-source">Source: <a href="{source_url}" target="_blank">{source_display}</a></div>
                </div>
                """, unsafe_allow_html=True)

        # --- Calendar View ---
        st.subheader("Calendar View")
        events_for_calendar = []
        for event in events:
            parsed_date = parse_event_date(event.get('dates', ''))
            if parsed_date:
                events_for_calendar.append({
                    "Date": parsed_date.strftime("%Y-%m-%d"),
                    "Event": event.get('title', 'N/A'),
                    "Location": event.get('location', 'N/A')
                })
            # else:
            #     st.caption(f"Could not parse date for event: {event.get('title', 'N/A')}") # Optional: Log parsing failures

        if events_for_calendar:
            try:
                df = pd.DataFrame(events_for_calendar)
                df['Date'] = pd.to_datetime(df['Date']) # Ensure correct type for sorting/filtering
                df = df.sort_values(by='Date') # Sort by date
                st.dataframe(df, use_container_width=True, hide_index=True)
            except Exception as e:
                st.error(f"Could not create calendar DataFrame: {e}")
        else:
            st.info("No events with parseable dates found for the calendar view.")


    # --- Display News Section (if any) ---
    if news_items:
        news_content = news_items[0].get("content", "No news content available.")
        sanitized_news = news_content.replace('<', '&lt;').replace('>', '&gt;')
        st.markdown(f"""
        <div class="news-section">
            <div class="news-title">📰 Local News Update</div>
            <p>{sanitized_news}</p>
        </div>
        """, unsafe_allow_html=True)
    # elif events: # Only show 'no news' if events were found but no news section
    #     st.info("No separate news items found in this update.")


def fetch_events(client, search_type, **kwargs):
    """Fetches events based on search type and arguments."""
    try:
        if search_type == "Today's Events":
            return client.get_today_events()
        elif search_type == "Upcoming Events":
            return client.get_upcoming_events(days=kwargs.get('days', 7))
        elif search_type == "Search by Category":
            return client.search_events_by_category(kwargs.get('category', '').lower())
        elif search_type == "Custom Search":
             query = kwargs.get('custom_query', '')
             if not query:
                 return {"error": "Please enter a custom search query.", "raw_response": ""}
             return client.get_events(query)
        else:
            return {"error": "Invalid search type selected.", "raw_response": ""}
    except Exception as e:
        # Log the error for debugging (optional)
        # print(f"API Error: {e}")
        st.error(f"An error occurred while communicating with the API: {str(e)}")
        return {"error": f"API communication failed: {str(e)}", "raw_response": ""}


# --- Main App Logic ---
def main():
    st.title("Logan, Utah Events Explorer 🏔️")
    st.markdown("Discover local events and news in Logan, Utah and Cache County.")

    # --- Initialize Session State ---
    # Used to track initial load and store data between reruns
    if 'initial_load_done' not in st.session_state:
        st.session_state.initial_load_done = False
    if 'events_data' not in st.session_state:
        st.session_state.events_data = None # Will store fetched events or error dict
    if 'search_triggered' not in st.session_state:
        st.session_state.search_triggered = False # Differentiates initial load from user search


    # --- Sidebar Setup ---
    with st.sidebar:
        st.header("⚙️ Settings")
        # Use secrets for the API key
        try:
            api_key = st.secrets['PPLX_API_KEY']
            st.success("API Key loaded successfully.")
        except KeyError:
            api_key = None
            st.warning("API Key not found. Please set `PPLX_API_KEY` in your Streamlit secrets.")
            st.markdown("Visit [Perplexity AI](https://www.perplexity.ai) if you need a key.")

        st.header("🔍 Search Options")
        search_type = st.radio(
            "Choose search type:",
            ["Today's Events", "Upcoming Events", "Search by Category", "Custom Search"],
            key="search_type_radio" # Add key for stability
        )

        # Conditional inputs based on search type
        days_ahead = 7
        category = "Music" # Default category
        custom_query = ""

        if search_type == "Upcoming Events":
            days_ahead = st.slider("Days ahead", 1, 30, 7, key="days_slider")
        elif search_type == "Search by Category":
            category = st.selectbox(
                "Select category",
                ["Music", "Arts", "Sports", "Family", "Education", "Community", "Food", "Outdoor"],
                index=0, # Default to Music
                key="category_select"
            )
        elif search_type == "Custom Search":
            custom_query = st.text_input("Enter your search query", key="custom_query_input")

        search_button = st.button("Search Events")

    # --- Main Content Area ---

    # Initialize Client only if API key is available
    client = None
    if api_key:
        client = LoganEventsClient(api_key)
    else:
        # No API Key - Stop further processing
        st.error("API Key is required to fetch events. Please configure it in your Streamlit secrets.")
        return # Exit the main function

    # --- Initial Data Load (Runs only once per session if API key exists) ---
    if client and not st.session_state.initial_load_done:
        st.session_state.search_triggered = False # This is not a user search
        with st.spinner("Fetching today's events..."):
            st.session_state.events_data = fetch_events(client, "Today's Events")
            st.session_state.initial_load_done = True
            st.rerun() # Rerun immediately to display the fetched data

    # --- Handle User Search Request ---
    if search_button and client:
        st.session_state.search_triggered = True # Mark as user-initiated search
        search_params = {}
        if search_type == "Upcoming Events":
            search_params['days'] = days_ahead
        elif search_type == "Search by Category":
            search_params['category'] = category
        elif search_type == "Custom Search":
            search_params['custom_query'] = custom_query

        with st.spinner(f"Searching for {search_type}..."):
            # Simulate a short delay for visual feedback (optional)
            # time.sleep(0.5)
            st.session_state.events_data = fetch_events(client, search_type, **search_params)
            # No rerun needed here, Streamlit will automatically rerun after button press handling

    # --- Display Data ---
    # Always try to display whatever data is in the session state
    # This covers initial load results and subsequent search results
    if st.session_state.initial_load_done: # Only display after initial attempt
        display_results(st.session_state.events_data)
    elif api_key and not st.session_state.initial_load_done:
        # Show a message while the initial load is happening on the first proper run
        st.info("Initializing and fetching today's events...")


if __name__ == "__main__":
    # Assume LoganEventsClient class definition is available
    # Example placeholder if the class isn't imported correctly:
    try:
        from logan_events_client import LoganEventsClient
    except ImportError:
        st.error("`logan_events_client.py` not found. Please ensure it's in the same directory.")
        # Define a dummy class to prevent NameError during development/testing
        class LoganEventsClient:
            def __init__(self, api_key):
                if not api_key: raise ValueError("API Key required")
                st.warning("Using Dummy LoganEventsClient!")
            def get_today_events(self): return self._get_sample_data()
            def get_upcoming_events(self, days): return self._get_sample_data()[:2] # Fewer samples
            def search_events_by_category(self, category): return [e for e in self._get_sample_data() if category.lower() in e['description'].lower() or category.lower() in e['title'].lower()] or self._get_sample_data()[0:1]
            def get_events(self, query): return [e for e in self._get_sample_data() if query.lower() in e['description'].lower() or query.lower() in e['title'].lower()] or self._get_sample_data()[1:2]
            def _get_sample_data(self):
                # Reusing the sample data function from the original code
                return [
                    {"title": "Sample: Toddler Time", "dates": "April 7, 2025 10:10 am", "location": "Sample Library", "description": "Sample toddler story time", "source": "http://example.com/library"},
                    {"title": "Sample: Jazz Kicks", "dates": "April 8, 2025 7:30 pm", "location": "Sample Arts Center", "description": "Sample jazz band performance", "source": "http://example.com/usu"},
                    {"title": "Sample: Community Picnic", "dates": "April 12, 2025 12:00 pm", "location": "Sample Park", "description": "Sample family friendly picnic event", "source": "http://example.com/parks"},
                     {"type": "news", "content": "This is a sample news update. Road construction on Main Street continues this week."} # Sample news item
                ]

    main()