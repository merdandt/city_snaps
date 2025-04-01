from openai import OpenAI
import json

class LoganEventsClient:
    """
    A client for retrieving local events information for Logan, Utah and Cache County
    using the Perplexity API.
    """
    
    def __init__(self, api_key):
        """
        Initialize the Logan Events client.
        
        Args:
            api_key (str): Perplexity API key
        """
        self.api_key = api_key
        self.client = OpenAI(api_key=api_key, base_url="https://api.perplexity.ai")
        
        # Create the system message that instructs the AI how to respond
        self.system_message = """
        **ROLE**: You are a local events assistant for Logan, Utah and Cache County, tasked with providing current community information exclusively from official city/county sources and trusted local organizations.

        **CORE FUNCTION**: Retrieve and present event details, news updates, and official announcements that reflect authentic local programming and community initiatives.

        **SEARCH PROTOCOL**:
        1. **Scope**:
           - Search ONLY within these domains:
              - "cachecounty.gov"
              - "logandowntown.org"
              - "cachevalleydaily.com"
              - "explorelogan.com"
              - "eventbrite.com" (only for events physically located in Cache County)
              - "cachechamber.com"
           - Include subdomains where applicable (e.g., events.logandowntown.org)
        2. **Query Execution**:
           - For the user's query: *"{query}"*, prioritize:
              - **Recency**: Events occurring in the next 90 days or news from past 3 months. If insufficient, include older content with clear date labeling.
              - **Relevance**: Official city announcements, festival details, community meetings, and local business initiatives.
           - Use domain-specific search operators (e.g., site:cachecounty.gov) to maintain focus.
        3. **Content Filtering**:
           - **Exclude**:
              - Virtual/national events not specific to Cache County
              - Classifieds/job postings unless explicitly requested
              - Duplicate listings across domains
           - **Flag**: Expired events with original dates and archive notices

        **OUTPUT REQUIREMENTS**:
        - Return all results structured as:
          1. [Event/News Title]: [Date(s)] - [Location/Venue] | [Brief description] | Source: [URL]
        - Include essential details:
           - Event dates/times
           - Registration requirements
           - Primary organizers
           - News article publication dates
        - **OUTPUT FORMAT**: **IMPORTANT:** Return the results as a JSON array, where each item is a JSON object with the following keys: "title", "dates", "location", "description", and "source".

        QUALITY ASSURANCE:
        1. Verify physical addresses map to Cache County locations.
        2. Cross-check municipal sites against chamber calendars for consistency.
        3. If no valid results: "No current Logan-area events found for [query]. Check direct sources: [list relevant domain links]"
        
        If there is news to report in addition to events, include a special object in the JSON array with "type": "news" and "content": containing the news text.
        """
    
    def get_events(self, query):
        """
        Retrieve events based on the provided query.
        
        Args:
            query (str): The search query for events
            
        Returns:
            list: List of event objects with details
        """
        messages = [
            {
                "role": "system",
                "content": self.system_message
            },
            {
                "role": "user",
                "content": query
            },
        ]
        
        # Make API request
        try:
            response = self.client.chat.completions.create(
                model="sonar-pro",
                messages=messages,
                temperature=0,
            )
            
            # Extract response content
            response_content = response.choices[0].message.content
            
            # Try to parse JSON response
            try:
                # Extract JSON from the response if it's mixed with text
                start_index = response_content.find('[')
                end_index = response_content.rfind(']') + 1
                
                if start_index != -1 and end_index != 0:
                    json_str = response_content[start_index:end_index]
                    events = json.loads(json_str)
                    
                    # Check if there's news text
                    news_text = None
                    if "In news," in response_content:
                        news_parts = response_content.split("In news,")
                        if len(news_parts) > 1:
                            news_text = news_parts[1].strip()
                    
                    if news_text:
                        events.append({
                            "type": "news",
                            "content": news_text
                        })
                    
                    return events
                else:
                    # If no JSON brackets found, return the raw text
                    return {"error": "No JSON data found in response", "raw_response": response_content}
                
            except json.JSONDecodeError:
                # If response is not valid JSON, return the raw text
                return {"error": "Failed to parse JSON response", "raw_response": response_content}
                
        except Exception as e:
            return {"error": f"API request failed: {str(e)}", "raw_response": ""}
    
    def get_today_events(self):
        """
        Convenience method to get today's events in Logan.
        
        Returns:
            list: List of today's events
        """
        return self.get_events("What news and events do we have for today in Logan?")
    
    def get_upcoming_events(self, days=7):
        """
        Get upcoming events for the specified number of days.
        
        Args:
            days (int): Number of days to look ahead
            
        Returns:
            list: List of upcoming events
        """
        return self.get_events(f"What events are happening in Logan in the next {days} days?")
    
    def search_events_by_category(self, category):
        """
        Search for events by category.
        
        Args:
            category (str): Event category (e.g., "music", "arts", "sports")
            
        Returns:
            list: List of events in the specified category
        """
        return self.get_events(f"What {category} events are happening in Logan?")