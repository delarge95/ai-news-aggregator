-- AI News Aggregator Database Initialization Script

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Create enum types
CREATE TYPE sentiment_type AS ENUM ('positive', 'negative', 'neutral');
CREATE TYPE notification_frequency AS ENUM ('realtime', 'hourly', 'daily', 'weekly');
CREATE TYPE reading_level AS ENUM ('simple', 'mixed', 'complex');

-- Insert initial news sources
INSERT INTO sources (name, url, api_name, country, language, credibility_score, rate_limit_per_hour) VALUES
('BBC News', 'https://www.bbc.com/news', 'newsapi', 'GB', 'en', 0.95, 100),
('The Guardian', 'https://www.theguardian.com', 'guardian', 'GB', 'en', 0.90, 100),
('The New York Times', 'https://www.nytimes.com', 'nytimes', 'US', 'en', 0.95, 100),
('CNN', 'https://www.cnn.com', 'newsapi', 'US', 'en', 0.85, 100),
('Reuters', 'https://www.reuters.com', 'newsapi', 'US', 'en', 0.92, 100);

-- Create sample user preference
INSERT INTO user_preferences (user_id, preferred_sources, preferred_topics, sentiment_preference, reading_level) VALUES
('demo-user', 
 ARRAY['bbc', 'guardian', 'nytimes'], 
 ARRAY['technology', 'politics', 'health'], 
 'all', 
 'mixed'
);

-- Create index for better performance
CREATE INDEX idx_articles_title_search ON articles USING gin(to_tsvector('english', title));
CREATE INDEX idx_articles_content_search ON articles USING gin(to_tsvector('english', content));

-- Create function to update timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Create triggers for updated_at columns
CREATE TRIGGER update_sources_updated_at BEFORE UPDATE ON sources
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_articles_updated_at BEFORE UPDATE ON articles
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_user_preferences_updated_at BEFORE UPDATE ON user_preferences
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();