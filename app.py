import streamlit as st
import time
import json
from datetime import datetime, timedelta
import pandas as pd
from logan_events_client import LoganEventsClient  # Import the class we created earlier

# Page configuration
st.set_page_config(
    page_title="Logan Events Explorer",
    page_icon="🏔️",
    layout="wide",
)

# Custom CSS for better UI
st.markdown("""
<style>
    .event-card {
        background-color: #f8f9fa;
        border-radius: 10px;
        padding: 20px;
        margin-bottom: 20px;
        border-left: 5px solid #0066cc;
    }
    .event-title {
        color: #0066cc;
        font-size: 20px;
        font-weight: bold;
        margin-bottom: 5px;
    }
    .event-date {
        color: #28a745;
        font-weight: bold;
        margin-bottom: 5px;
    }
    .event-location {
        color: #6c757d;
        font-style: italic;
        margin-bottom: 10px;
    }
    .event-description {
        margin-bottom: 10px;
    }
    .event-source {
        color: #6c757d;
        font-size: 14px;
    }
    .loading-spinner {
        text-align: center;
        margin-top: 50px;
        margin-bottom: 50px;
    }
    .news-section {
        background-color: #e9f7fe;
        border-radius: 10px;
        padding: 20px;
        margin-top: 30px;
        border-left: 5px solid #17a2b8;
    }
    .news-title {
        color: #17a2b8;
        font-size: 24px;
        font-weight: bold;
        margin-bottom: 15px;
    }
</style>
""", unsafe_allow_html=True)

def main():
    # Header
    st.title("Logan, Utah Events Explorer 🏔️")
    st.markdown("Discover local events and news in Logan, Utah and Cache County.")
    
    # Sidebar for API key and search options
    with st.sidebar:
        st.header("Settings")
        api_key = st.secrets['PPLX_API_KEY']
        
        st.header("Search Options")
        search_type = st.radio(
            "Choose search type:",
            ["Today's Events", "Upcoming Events", "Search by Category", "Custom Search"]
        )
        
        if search_type == "Upcoming Events":
            days_ahead = st.slider("Days ahead", 1, 30, 7)
        
        if search_type == "Search by Category":
            category = st.selectbox(
                "Select category",
                ["Music", "Arts", "Sports", "Family", "Education", "Community", "Food", "Outdoor"]
            )
        
        if search_type == "Custom Search":
            custom_query = st.text_input("Enter your search query")
        
        search_button = st.button("Search Events")
    
    # Main content area
    if not api_key:
        st.warning("Please enter your Perplexity API key in the sidebar to get started.")
        st.info("Don't have a key? Visit [Perplexity AI](https://www.perplexity.ai) to get one.")
        return
    
    # Initialize client
    client = LoganEventsClient(api_key)
    
    # Handle search
    if search_button:
        with st.spinner("Fetching events from Logan, Utah..."):
            # Show loading animation
            progress_placeholder = st.empty()
            progress_bar = progress_placeholder.progress(0)
            
            for i in range(100):
                time.sleep(0.01)  # Simulate loading time
                progress_bar.progress(i + 1)
            
            progress_placeholder.empty()
            
            # Perform search based on selected option
            try:
                if search_type == "Today's Events":
                    events = client.get_today_events()
                elif search_type == "Upcoming Events":
                    events = client.get_upcoming_events(days=days_ahead)
                elif search_type == "Search by Category":
                    events = client.search_events_by_category(category.lower())
                else:  # Custom Search
                    events = client.get_events(custom_query)
                
                display_results(events)
            except Exception as e:
                st.error(f"Error retrieving events: {str(e)}")
    else:
        # Display sample data on first load
        st.subheader("Sample Events for Logan, Utah")
        sample_data = get_sample_data()
        display_results(sample_data, is_sample=True)

def display_results(data, is_sample=False):
    if is_sample:
        st.info("⚠️ Showing sample data. Use the search button to fetch real-time events.")
    
    if isinstance(data, dict) and "error" in data:
        st.error(f"Error: {data['error']}")
        st.code(data['raw_response'], language="json")
        return
    
    # Make sure we're working with the right data structure
    if isinstance(data, str):
        try:
            data = json.loads(data)
        except json.JSONDecodeError:
            st.error("Could not parse response as JSON")
            st.code(data)
            return
    
    # Display events in cards
    if len(data) > 0:
        # Extract just the events (filter out any news items)
        events = [item for item in data if all(key in item for key in ["title", "dates", "location"])]
        
        # Create columns for the events
        col1, col2 = st.columns(2)
        
        # Display events in two columns
        for i, event in enumerate(events):
            with col1 if i % 2 == 0 else col2:
                st.markdown(f"""
                <div class="event-card">
                    <div class="event-title">{event['title']}</div>
                    <div class="event-date">📅 {event['dates']}</div>
                    <div class="event-location">📍 {event['location']}</div>
                    <div class="event-description">{event['description']}</div>
                    <div class="event-source">Source: <a href="{event['source']}" target="_blank">{event['source']}</a></div>
                </div>
                """, unsafe_allow_html=True)
        
        # See if there's news in the response
        news_text = None
        if isinstance(data, list) and len(data) > 0:
            # If we have news, it might be in a special news item
            news_items = [item for item in data if "type" in item and item["type"] == "news"]
            
            if news_items:
                news_text = news_items[0].get("content", "")
        
        # Add news section if available
        if news_text:
            st.markdown("""
            <div class="news-section">
                <div class="news-title">📰 Local News</div>
                <p>{news_text}</p>
            </div>
            """.format(news_text=news_text), unsafe_allow_html=True)
        
        # Add calendar view
        st.subheader("Calendar View")
        events_for_calendar = []
        
        for event in events:
            try:
                # Extract date from the event dates string
                date_str = event['dates'].split()[0:3]
                date_str = " ".join(date_str)
                event_date = datetime.strptime(date_str, "%B %d, %Y")
                
                events_for_calendar.append({
                    "Date": event_date.strftime("%Y-%m-%d"),
                    "Event": event['title'],
                    "Location": event['location']
                })
            except:
                # Skip events with unparseable dates
                continue
        
        if events_for_calendar:
            df = pd.DataFrame(events_for_calendar)
            st.dataframe(df, use_container_width=True)
    else:
        st.warning("No events found for your search criteria.")

def get_sample_data():
    # Sample data to display when the app first loads
    return [
        {
            "title": "Toddler Time",
            "dates": "April 1, 2025 10:10 am - 10:30 am",
            "location": "North Logan City Library, 475 E 2500 N, North Logan, UT 84341",
            "description": "Toddler story time at the North Logan City Library",
            "source": "https://northlogancity.org"
        },
        {
            "title": "Story Time", 
            "dates": "April 1, 2025 11:00 am - 11:30 am",
            "location": "North Logan City Library, 475 E 2500 N, North Logan, UT 84341",
            "description": "Story time for children at the North Logan City Library",
            "source": "https://northlogancity.org"
        },
        {
            "title": "Adult Fiber Crafts",
            "dates": "April 1, 2025 12:30 pm - 2:00 pm",
            "location": "North Logan City Library",
            "description": "Come stitch and share stories with friends. This group meets every 1st and 3rd Tuesday of the month. No sign-up required.",
            "source": "https://northlogancity.org"
        },
        {
            "title": "Jazz Kicks",
            "dates": "April 1, 2025 7:30 pm",
            "location": "Chase Fine Arts Center, Morgan Theatre",
            "description": "Jazz Kicks Band is a 17-piece band playing exciting jazz music, featuring accomplished musicians from Northern Utah. Free for USU students, faculty, and staff!",
            "source": "https://www.usu.edu/calendar/?day=2025%2F4%2F1&subsponsor=82"
        }
    ]

if __name__ == "__main__":
    main()