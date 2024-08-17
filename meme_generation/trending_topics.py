from pytrends.request import TrendReq


class trending_topics():
    # Initialize pytrends
    def __init__(self, trending_searches):
        self.trending_searches = trending_searches
        self.topics = {}
        self.topic_descriptions = {}

    def trending_topics(self):
        for i, topic in enumerate(self.trending_searches, 1):
            self.topics[i] = topic
        return self.topics

    # Function to generate a description for each trending topic
    def _generate_description(self, topic):
        # Build payload for the topic to get related queries
        pytrends.build_payload([topic])
        related_queries = pytrends.related_queries()[topic]['top']
        
        if related_queries is not None:
            # Collect the top related queries to form a description
            related_query_list = related_queries['query'].head(5).tolist()
            
            # Construct a description sentence
            description = f"The topic '{topic}' is trending due to increased interest in "
            description += ", ".join(related_query_list[:-1]) + ", and " + related_query_list[-1] + "."
            description += " People are searching for information on these topics as they relate to recent events or announcements."
        else:
            description = f"The topic '{topic}' is trending, but specific reasons are unclear based on related searches."
        
        return description


    def trend_description(self):
        # Generate and print descriptions for each trending topic
        for topic in self.trending_searches:
            description = self._generate_description(topic)
            self.topic_descriptions[topic] = description
        return self.topic_descriptions



if __name__ == "__main__":
    pytrends = TrendReq(hl='en-US', tz=360)

    # Get trending searches in real-time (you can specify different regions)
    trending_searches_df = pytrends.trending_searches()

    # Display the trending searches
    trending_searches = trending_searches_df[0].tolist()

    tt = trending_topics(trending_searches)
    trending_topics = tt.trending_topics()
    print(trending_topics)
    # trend_description= tt.trend_description()
    # print(trend_description)

    # print(pytrends.realtime_trending_searches(pn='US'))
    