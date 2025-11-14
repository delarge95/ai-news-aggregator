"""
Unit tests for deduplication algorithms
"""

import pytest
import hashlib
from unittest.mock import Mock, patch
from datetime import datetime, timedelta
import re
from typing import List, Dict, Any


class TestDeduplicationService:
    """Test suite for deduplication service"""
    
    def setup_method(self):
        """Setup test environment before each test"""
        # Sample articles for testing
        self.sample_articles = [
            {
                "id": "1",
                "title": "Breaking: AI Technology Advances",
                "content": "Artificial Intelligence has made significant progress in machine learning algorithms this year.",
                "url": "https://example.com/ai-tech-advance",
                "published_at": datetime(2023, 12, 1, 10, 0),
                "source": "BBC"
            },
            {
                "id": "2", 
                "title": "AI Technology Shows Major Breakthrough",
                "content": "Researchers report significant advances in artificial intelligence and machine learning technologies.",
                "url": "https://example.com/ai-breakthrough",
                "published_at": datetime(2023, 12, 1, 11, 0),
                "source": "CNN"
            },
            {
                "id": "3",
                "title": "Different Article About Climate Change",
                "content": "Climate change presents new challenges for global warming mitigation strategies.",
                "url": "https://example.com/climate-change",
                "published_at": datetime(2023, 12, 1, 12, 0),
                "source": "Reuters"
            },
            {
                "id": "4",
                "title": "Latest Updates on AI Progress", 
                "content": "Artificial intelligence continues to evolve with new machine learning breakthroughs announced today.",
                "url": "https://example.com/ai-progress",
                "published_at": datetime(2023, 12, 1, 13, 0),
                "source": "The Guardian"
            },
            {
                "id": "5",
                "title": "Completely Different Topic",
                "content": "This article discusses sports and entertainment news.",
                "url": "https://example.com/sports-news",
                "published_at": datetime(2023, 12, 1, 14, 0),
                "source": "ESPN"
            }
        ]
        
        # Articles with similar content but different formatting
        self.similar_articles = [
            {
                "id": "6",
                "title": "AI Revolution: Technology Changes Everything",
                "content": "Artificial Intelligence is revolutionizing the way we work and live. Machine learning algorithms are becoming more sophisticated every day.",
                "url": "https://example.com/ai-revolution",
                "published_at": datetime(2023, 12, 1, 15, 0)
            },
            {
                "id": "7",
                "title": "The AI Revolution: How Technology Is Changing Everything",
                "content": "Artificial Intelligence is revolutionizing the way we work and live. Machine learning algorithms are becoming more sophisticated every day.",
                "url": "https://example.com/ai-revolution-v2",
                "published_at": datetime(2023, 12, 1, 16, 0)
            }
        ]

    @pytest.fixture
    def deduplication_service(self):
        """Create deduplication service instance for testing"""
        from app.services.deduplication_service import DeduplicationService
        return DeduplicationService(
            similarity_threshold=0.8,
            hash_algorithm="sha256",
            enable_semantic_similarity=True
        )

    def test_generate_content_hash(self, deduplication_service):
        """Test content hash generation"""
        content = "This is a test article content"
        title = "Test Article"
        
        hash1 = deduplication_service.generate_content_hash(title, content)
        hash2 = deduplication_service.generate_content_hash(title, content)
        
        # Same content should produce same hash
        assert hash1 == hash2
        
        # Different content should produce different hash
        hash3 = deduplication_service.generate_content_hash("Different Title", content)
        assert hash1 != hash3
        
        # Should be valid SHA-256 hash
        assert len(hash1) == 64
        assert all(c in "0123456789abcdef" for c in hash1)

    def test_normalize_text(self, deduplication_service):
        """Test text normalization for comparison"""
        test_cases = [
            ("Hello    World", "helloworld"),
            ("Hello-World!", "helloworld"),
            ("HELLO world", "helloworld"),
            ("Hello, world!", "helloworld"),
            ("123.456.789", "123456789"),
            ("", ""),
            ("Multiple   spaces   here", "multiplespaceshere")
        ]
        
        for input_text, expected in test_cases:
            result = deduplication_service.normalize_text(input_text)
            assert result == expected

    def test_calculate_text_similarity(self, deduplication_service):
        """Test text similarity calculation"""
        # Exact same text
        similarity1 = deduplication_service.calculate_text_similarity(
            "Hello world", "Hello world"
        )
        assert similarity1 == 1.0
        
        # Very similar text
        similarity2 = deduplication_service.calculate_text_similarity(
            "Hello world", "Hello world!"
        )
        assert similarity2 > 0.9
        
        # Different text
        similarity3 = deduplication_service.calculate_text_similarity(
            "Hello world", "Goodbye world"
        )
        assert similarity3 < 0.5
        
        # Completely different text
        similarity4 = deduplication_service.calculate_text_similarity(
            "Hello world", "Basketball games are fun"
        )
        assert similarity4 < 0.2

    def test_calculate_semantic_similarity(self, deduplication_service):
        """Test semantic similarity calculation"""
        # Similar topics should have higher similarity
        similarity1 = deduplication_service.calculate_semantic_similarity(
            "artificial intelligence", "machine learning"
        )
        similarity2 = deduplication_service.calculate_semantic_similarity(
            "artificial intelligence", "cooking recipes"
        )
        
        assert similarity1 > similarity2
        
        # Identical text should have similarity of 1.0
        similarity3 = deduplication_service.calculate_semantic_similarity(
            "hello world", "hello world"
        )
        assert similarity3 == 1.0

    def test_identify_duplicates_by_hash(self, deduplication_service):
        """Test duplicate identification using content hash"""
        articles_with_hashes = []
        for article in self.sample_articles[:3]:
            # Make first two articles have identical content
            if article["id"] in ["1", "2"]:
                content_to_hash = "Identical content for testing"
            else:
                content_to_hash = article["content"]
            
            hash_value = hashlib.sha256(
                (article["title"] + content_to_hash).encode()
            ).hexdigest()
            
            articles_with_hashes.append({
                **article,
                "content_hash": hash_value
            })
        
        duplicates = deduplication_service.identify_duplicates_by_hash(articles_with_hashes)
        
        # Articles 1 and 2 should be identified as duplicates
        assert len(duplicates) == 1
        assert set(duplicates[0]) == {"1", "2"}
        
        # Other articles should not be duplicates
        non_duplicate_ids = {article["id"] for article in articles_with_hashes} - {"1", "2"}
        for duplicate_group in duplicates:
            assert duplicate_group.isdisjoint(non_duplicate_ids)

    def test_identify_duplicates_by_similarity(self, deduplication_service):
        """Test duplicate identification using content similarity"""
        # Articles 1, 2, and 4 are about AI and should be similar
        similar_articles = [
            self.sample_articles[0],  # About AI
            self.sample_articles[1],  # About AI
            self.sample_articles[3],  # About AI
            self.sample_articles[2]   # About climate (different topic)
        ]
        
        duplicates = deduplication_service.identify_duplicates_by_similarity(
            similar_articles, 
            threshold=0.6
        )
        
        # Should find duplicates among AI articles
        ai_duplicate_groups = [
            group for group in duplicates 
            if all(article["id"] in ["1", "2", "4"] for article in group)
        ]
        
        assert len(duplicates) > 0
        
        # Climate article should be in its own group
        climate_groups = [
            group for group in duplicates 
            if all(article["id"] == "3" for article in group)
        ]
        assert len(climate_groups) == 1

    def test_identify_semantic_duplicates(self, deduplication_service):
        """Test semantic duplicate identification"""
        # Test with articles about similar topics
        tech_articles = [
            {
                "id": "tech1",
                "title": "New smartphone features",
                "content": "Latest mobile phone with advanced camera technology",
                "url": "https://example.com/smartphone-news",
                "published_at": datetime(2023, 12, 1, 10, 0)
            },
            {
                "id": "tech2", 
                "title": "Mobile phone cameras improve",
                "content": "Latest mobile phone with advanced camera technology",
                "url": "https://example.com/mobile-cameras",
                "published_at": datetime(2023, 12, 1, 11, 0)
            }
        ]
        
        duplicates = deduplication_service.identify_semantic_duplicates(tech_articles)
        
        assert len(duplicates) > 0
        duplicate_ids = {article["id"] for group in duplicates for article in group}
        assert "tech1" in duplicate_ids or "tech2" in duplicate_ids

    def test_group_duplicates_by_priority(self, deduplication_service):
        """Test duplicate grouping with source priority"""
        articles = [
            {
                "id": "article1",
                "title": "AI Breakthrough",
                "content": "Content about AI",
                "url": "https://example.com/article1",
                "source": "Reuters",
                "credibility_score": 0.8,
                "published_at": datetime(2023, 12, 1, 10, 0)
            },
            {
                "id": "article2",
                "title": "AI Makes Breakthrough", 
                "content": "Content about AI",
                "url": "https://example.com/article2",
                "source": "BBC",
                "credibility_score": 0.9,
                "published_at": datetime(2023, 12, 1, 11, 0)
            },
            {
                "id": "article3",
                "title": "Different Article",
                "content": "Completely different content",
                "url": "https://example.com/article3",
                "source": "The Guardian",
                "credibility_score": 0.7,
                "published_at": datetime(2023, 12, 1, 12, 0)
            }
        ]
        
        groups = deduplication_service.group_duplicates_by_priority(articles)
        
        # Should have 2 groups: one for AI duplicates, one for different article
        assert len(groups) == 2
        
        # Find the AI duplicate group
        ai_group = None
        for group in groups:
            if len(group) > 1:
                ai_group = group
                break
        
        assert ai_group is not None
        
        # BBC article should be selected as primary (highest credibility)
        primary_article = deduplication_service.get_primary_article(ai_group)
        assert primary_article["id"] == "article2"  # BBC has highest credibility

    def test_deduplicate_articles(self, deduplication_service):
        """Test complete deduplication process"""
        articles = self.sample_articles + [
            {
                "id": "duplicate1",
                "title": "AI Technology Advances (Copy)",
                "content": "Artificial Intelligence has made significant progress in machine learning algorithms this year.",
                "url": "https://example.com/duplicate",
                "published_at": datetime(2023, 12, 1, 17, 0)
            }
        ]
        
        result = deduplication_service.deduplicate_articles(articles)
        
        assert "unique_articles" in result
        assert "duplicate_groups" in result
        assert "duplicate_ids" in result
        
        # Should have fewer unique articles than original
        assert len(result["unique_articles"]) < len(articles)
        
        # All duplicate IDs should be tracked
        assert len(result["duplicate_ids"]) > 0
        
        # Primary article should be one of the duplicates
        for duplicate_id in result["duplicate_ids"]:
            assert duplicate_id in [a["id"] for a in articles]

    def test_calculate_content_fingerprint(self, deduplication_service):
        """Test content fingerprint calculation"""
        content = "This is a test article about artificial intelligence and machine learning."
        
        # Calculate fingerprint
        fingerprint = deduplication_service.calculate_content_fingerprint(content)
        
        assert isinstance(fingerprint, str)
        assert len(fingerprint) > 0
        
        # Same content should produce same fingerprint
        fingerprint2 = deduplication_service.calculate_content_fingerprint(content)
        assert fingerprint == fingerprint2
        
        # Different content should produce different fingerprint
        different_content = "This is completely different content."
        fingerprint3 = deduplication_service.calculate_content_fingerprint(different_content)
        assert fingerprint != fingerprint3

    def test_extract_key_phrases(self, deduplication_service):
        """Test key phrase extraction for similarity comparison"""
        text = "Artificial intelligence and machine learning are transforming the technology industry."
        
        phrases = deduplication_service.extract_key_phrases(text)
        
        assert isinstance(phrases, list)
        assert len(phrases) > 0
        
        # Should contain key terms
        phrase_text = " ".join(phrases).lower()
        assert "artificial intelligence" in phrase_text or "artificial" in phrase_text
        assert "machine learning" in phrase_text or "machine" in phrase_text

    def test_calculate_jaccard_similarity(self, deduplication_service):
        """Test Jaccard similarity coefficient calculation"""
        text1 = "artificial intelligence machine learning"
        text2 = "artificial intelligence deep learning"
        text3 = "climate change global warming"
        
        similarity1 = deduplication_service.calculate_jaccard_similarity(text1, text2)
        similarity2 = deduplication_service.calculate_jaccard_similarity(text1, text3)
        
        # Similar texts should have higher similarity
        assert similarity1 > similarity2
        
        # Identical texts should have similarity of 1.0
        similarity3 = deduplication_service.calculate_jaccard_similarity(text1, text1)
        assert similarity3 == 1.0
        
        # Jaccard similarity should be between 0 and 1
        assert 0 <= similarity1 <= 1
        assert 0 <= similarity2 <= 1
        assert 0 <= similarity3 <= 1

    def test_handle_time_based_duplicates(self, deduplication_service):
        """Test handling of time-based duplicate detection"""
        # Same article published by different sources at different times
        articles = [
            {
                "id": "article1",
                "title": "Breaking News: Major Event",
                "content": "This is a breaking news story about a major event.",
                "url": "https://source1.com/news1",
                "published_at": datetime(2023, 12, 1, 10, 0),
                "source": "BBC"
            },
            {
                "id": "article2",
                "title": "Breaking: Major Event Reported",
                "content": "This is a breaking news story about a major event.",
                "url": "https://source2.com/news2", 
                "published_at": datetime(2023, 12, 1, 10, 30),
                "source": "CNN"
            },
            {
                "id": "article3",
                "title": "Different News",
                "content": "This is completely different news content.",
                "url": "https://source3.com/news3",
                "published_at": datetime(2023, 12, 1, 15, 0),
                "source": "Reuters"
            }
        ]
        
        # Within 1 hour should be considered duplicates if content is similar
        result = deduplication_service.deduplicate_articles(
            articles,
            time_window_minutes=60,
            use_time_based_detection=True
        )
        
        # Should identify articles 1 and 2 as duplicates
        duplicate_found = any(
            set(group) == {"article1", "article2"} 
            for group in result["duplicate_groups"]
        )
        assert duplicate_found

    def test_calculate_source_reliability_weight(self, deduplication_service):
        """Test source reliability weight calculation"""
        sources = [
            {"name": "BBC", "credibility_score": 0.9},
            {"name": "CNN", "credibility_score": 0.8},
            {"name": "Local Blog", "credibility_score": 0.3},
            {"name": "Known Fake", "credibility_score": 0.1}
        ]
        
        for source in sources:
            weight = deduplication_service.calculate_source_reliability_weight(source)
            assert 0 <= weight <= 1
            assert source["credibility_score"] * 0.8 <= weight <= min(source["credibility_score"] * 1.2, 1.0)

    def test_select_best_duplicate(self, deduplication_service):
        """Test selection of best duplicate based on multiple criteria"""
        duplicates = [
            {
                "id": "old_article",
                "title": "AI News",
                "content": "AI content here",
                "published_at": datetime(2023, 12, 1, 10, 0),
                "source": {"name": "Local News", "credibility_score": 0.4},
                "relevance_score": 0.3
            },
            {
                "id": "good_article",
                "title": "Artificial Intelligence Breakthrough",
                "content": "Comprehensive AI content with detailed analysis",
                "published_at": datetime(2023, 12, 1, 12, 0),
                "source": {"name": "BBC", "credibility_score": 0.9},
                "relevance_score": 0.8
            },
            {
                "id": "medium_article",
                "title": "AI Technology Update",
                "content": "AI technology news",
                "published_at": datetime(2023, 12, 1, 11, 0),
                "source": {"name": "Reuters", "credibility_score": 0.8},
                "relevance_score": 0.6
            }
        ]
        
        best = deduplication_service.select_best_duplicate(duplicates)
        
        # Should select the BBC article (best combination of factors)
        assert best["id"] == "good_article"

    def test_merge_duplicate_content(self, deduplication_service):
        """Test merging content from duplicate articles"""
        duplicates = [
            {
                "id": "article1",
                "title": "AI Breakthrough",
                "content": "AI has made breakthroughs",
                "url": "https://example.com/1"
            },
            {
                "id": "article2", 
                "title": "AI Makes Progress",
                "content": "Machine learning shows progress",
                "url": "https://example.com/2"
            }
        ]
        
        merged = deduplication_service.merge_duplicate_content(duplicates)
        
        assert "title" in merged
        assert "content" in merged
        assert "source_articles" in merged
        assert len(merged["source_articles"]) == 2
        assert all(article["id"] in merged["source_articles"] for article in duplicates)

    @pytest.mark.parametrize("threshold,expected_groups", [
        (0.9, 5),  # Very strict, almost no duplicates
        (0.7, 4),  # Medium strictness
        (0.5, 3),  # More lenient
        (0.3, 1)   # Very lenient, most similar articles grouped
    ])
    def test_different_similarity_thresholds(self, deduplication_service, threshold, expected_groups):
        """Test deduplication with different similarity thresholds"""
        # Use articles with varying similarity
        test_articles = [
            {"id": "1", "content": "artificial intelligence machine learning"},
            {"id": "2", "content": "artificial intelligence deep learning"},
            {"id": "3", "content": "AI and ML technologies"},
            {"id": "4", "content": "basketball sports games"},
            {"id": "5", "content": "football soccer matches"}
        ]
        
        result = deduplication_service.deduplicate_articles(
            test_articles,
            threshold=threshold
        )
        
        # Number of groups should decrease with lower threshold
        assert len(result["duplicate_groups"]) <= expected_groups

    def test_empty_articles_handling(self, deduplication_service):
        """Test handling of empty or invalid articles"""
        empty_articles = []
        result = deduplication_service.deduplicate_articles(empty_articles)
        
        assert result["unique_articles"] == []
        assert result["duplicate_groups"] == []
        assert result["duplicate_ids"] == set()
        
        # Test with None values
        articles_with_none = [
            {"id": "1", "title": None, "content": "Content"},
            {"id": "2", "title": "Title", "content": None}
        ]
        
        result2 = deduplication_service.deduplicate_articles(articles_with_none)
        assert len(result2["unique_articles"]) == 2  # Should handle gracefully

    def test_performance_large_dataset(self, deduplication_service):
        """Test performance with large dataset"""
        # Generate large dataset
        large_dataset = []
        for i in range(100):
            # Create some duplicates
            base_content = f"Article about topic {i % 10}"
            for j in range(3):  # 3 variations per topic
                large_dataset.append({
                    "id": f"article_{i}_{j}",
                    "title": f"Topic {i % 10} Article {j}",
                    "content": base_content + f" variation {j}",
                    "url": f"https://example.com/article_{i}_{j}",
                    "published_at": datetime(2023, 12, 1, 10 + i, j * 20)
                })
        
        result = deduplication_service.deduplicate_articles(large_dataset)
        
        # Should process efficiently
        assert len(result["unique_articles"]) < len(large_dataset)
        assert len(result["duplicate_groups"]) > 0
        
        # All duplicate IDs should be tracked
        total_duplicate_ids = sum(len(group) for group in result["duplicate_groups"])
        assert total_duplicate_ids < len(large_dataset)