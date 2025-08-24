import requests
import json
import hashlib
import time
from typing import Dict, List, Optional
from flask import current_app
from functools import wraps
import logging
from product_insight.services.advanced_content_analyzer import AdvancedContentAnalyzer

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class LLMCache:
    """Simple in-memory cache for LLM responses"""
    def __init__(self, max_size: int = 100, ttl_seconds: int = 3600):
        self.cache = {}
        self.timestamps = {}
        self.max_size = max_size
        self.ttl = ttl_seconds
    
    def _generate_key(self, prompt: str, model: str) -> str:
        """Generate cache key from prompt and model"""
        content = f"{model}:{prompt}"
        return hashlib.md5(content.encode()).hexdigest()
    
    def get(self, prompt: str, model: str) -> Optional[Dict]:
        """Get cached response if available and valid"""
        key = self._generate_key(prompt, model)
        
        if key in self.cache:
            # Check if cache entry is still valid
            if time.time() - self.timestamps[key] < self.ttl:
                logger.info(f"Cache hit for LLM prompt (key: {key[:8]}...)")
                return self.cache[key]
            else:
                # Remove expired entry
                del self.cache[key]
                del self.timestamps[key]
        
        return None
    
    def set(self, prompt: str, model: str, response: Dict):
        """Cache the response"""
        key = self._generate_key(prompt, model)
        
        # Remove oldest entries if cache is full
        if len(self.cache) >= self.max_size:
            oldest_key = min(self.timestamps.keys(), key=lambda k: self.timestamps[k])
            del self.cache[oldest_key]
            del self.timestamps[oldest_key]
        
        self.cache[key] = response
        self.timestamps[key] = time.time()
        logger.info(f"Cached LLM response (key: {key[:8]}...)")

# Global cache instance
llm_cache = LLMCache()

def retry_on_failure(max_retries: int = 3, delay: float = 1.0):
    """Decorator to retry LLM calls on failure"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            last_exception = None
            
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    if attempt < max_retries - 1:
                        logger.warning(f"LLM call failed (attempt {attempt + 1}/{max_retries}): {str(e)}")
                        time.sleep(delay * (attempt + 1))  # Exponential backoff
                    else:
                        logger.error(f"LLM call failed after {max_retries} attempts: {str(e)}")
            
            raise last_exception
        return wrapper
    return decorator

class LLMService:
    """Optimized service for interacting with local LLM (Ollama)"""
    
    def __init__(self):
        self.api_url = None
        self.model_name = None
        self.cache = llm_cache
        self.request_timeout = 120  # Increased timeout for complex analysis
        self.max_prompt_length = 8000  # Prevent overly long prompts
        self.advanced_analyzer = AdvancedContentAnalyzer()
    
    def _ensure_config(self):
        """Ensure configuration is loaded"""
        if self.api_url is None:
            self.api_url = current_app.config.get('OLLAMA_API_URL', 'http://localhost:11434/api/generate')
            self.model_name = current_app.config.get('OLLAMA_MODEL_NAME', 'deepseek-r1:8b')
    
    def _truncate_data(self, data: List[Dict], max_items: int = 50) -> List[Dict]:
        """Truncate data to prevent overly long prompts"""
        if len(data) <= max_items:
            return data
        
        # Take a sample that includes first, last, and middle items
        sample_size = max_items
        if sample_size >= 10:
            first_chunk = data[:sample_size//3]
            middle_start = len(data)//2 - sample_size//6
            middle_chunk = data[middle_start:middle_start + sample_size//3]
            last_chunk = data[-sample_size//3:]
            return first_chunk + middle_chunk + last_chunk
        else:
            return data[:sample_size]
    
    def _sanitize_text_data(self, data: List[Dict]) -> List[Dict]:
        """Clean and sanitize text data for analysis"""
        sanitized = []
        for item in data:
            clean_item = {}
            for key, value in item.items():
                if isinstance(value, str):
                    # Remove excessive whitespace and limit length
                    clean_value = ' '.join(value.split())[:500]
                    clean_item[key] = clean_value
                elif isinstance(value, (int, float)):
                    clean_item[key] = value
                elif key in ['date', 'created_at', 'rating', 'likes', 'comments', 'shares']:
                    clean_item[key] = value
            sanitized.append(clean_item)
        return sanitized
    
    def analyze_sentiment(self, texts: List[str]) -> Dict:
        """Analyze sentiment of given texts with improved performance"""
        logger.info(f"Starting sentiment analysis for {len(texts) if texts else 0} texts")
        
        if not texts:
            logger.warning("No texts provided for sentiment analysis")
            return {
                "sentiment": "neutral", 
                "confidence": 0.0, 
                "themes": [], 
                "counts": {"positive": 0, "negative": 0, "neutral": 0}
            }
        
        # Limit and clean texts
        original_count = len(texts)
        clean_texts = [text.strip()[:200] for text in texts if text.strip()][:20]
        logger.info(f"Cleaned and limited texts: {original_count} → {len(clean_texts)}")
        
        prompt = f"""Analyze the sentiment of these texts. Respond ONLY with valid JSON:

Texts: {json.dumps(clean_texts)}

Required JSON format:
{{
    "sentiment": "positive|negative|neutral",
    "confidence": 0.85,
    "themes": ["theme1", "theme2"],
    "counts": {{"positive": 0, "negative": 0, "neutral": 0}}
}}"""
        
        try:
            logger.info("Sending sentiment analysis request to LLM")
            response = self._generate_response(prompt)
            
            if isinstance(response, dict) and "response" in response:
                # Try to parse JSON from response
                try:
                    result = json.loads(response["response"])
                    logger.info(f"LLM sentiment analysis successful: {result.get('sentiment', 'unknown')} sentiment")
                    return result
                except json.JSONDecodeError as json_error:
                    logger.warning(f"Failed to parse LLM JSON response: {json_error}, using fallback")
                    return self._fallback_sentiment_analysis(clean_texts)
            else:
                logger.warning("Invalid LLM response format, using fallback")
                return self._fallback_sentiment_analysis(clean_texts)
        except Exception as e:
            logger.error(f"Sentiment analysis failed: {str(e)}, using fallback")
            return self._fallback_sentiment_analysis(clean_texts)
    
    def _fallback_sentiment_analysis(self, texts: List[str]) -> Dict:
        """Simple fallback sentiment analysis"""
        logger.info(f"Using fallback sentiment analysis for {len(texts)} texts")
        
        positive_words = ['good', 'great', 'excellent', 'amazing', 'love', 'best', 'fantastic', 'awesome']
        negative_words = ['bad', 'terrible', 'awful', 'hate', 'worst', 'horrible', 'disappointing']
        
        positive_count = 0
        negative_count = 0
        
        for text in texts:
            text_lower = text.lower()
            pos_score = sum(1 for word in positive_words if word in text_lower)
            neg_score = sum(1 for word in negative_words if word in text_lower)
            
            if pos_score > neg_score:
                positive_count += 1
            elif neg_score > pos_score:
                negative_count += 1
        
        neutral_count = len(texts) - positive_count - negative_count
        total = len(texts)
        
        if positive_count > max(negative_count, neutral_count):
            sentiment = "positive"
            confidence = positive_count / total
        elif negative_count > max(positive_count, neutral_count):
            sentiment = "negative"
            confidence = negative_count / total
        else:
            sentiment = "neutral"
            confidence = neutral_count / total
        
        result = {
            "sentiment": sentiment,
            "confidence": round(confidence, 2),
            "themes": ["automated_analysis"],
            "counts": {
                "positive": positive_count,
                "negative": negative_count,
                "neutral": neutral_count
            }
        }
        
        logger.info(f"Fallback analysis completed: {sentiment} sentiment with {confidence:.2f} confidence")
        return result
    
    def analyze_product_reviews(self, reviews: List[Dict]) -> str:
        """Analyze Amazon product reviews with optimized performance"""
        logger.info(f"Starting product review analysis for {len(reviews) if reviews else 0} reviews")
        
        if not reviews:
            logger.warning("No reviews provided for analysis")
            return "No reviews to analyze."
        
        # Clean and truncate data
        logger.info("Sanitizing and truncating review data")
        clean_reviews = self._sanitize_text_data(reviews)
        sample_reviews = self._truncate_data(clean_reviews, 30)
        logger.info(f"Data processing: {len(reviews)} → {len(clean_reviews)} → {len(sample_reviews)} reviews")
        
        # Extract key information for analysis
        review_summary = []
        for review in sample_reviews:
            summary = {
                "rating": review.get("rating", 0),
                "text": review.get("text", "")[:200],
                "date": review.get("date", "")
            }
            review_summary.append(summary)
        
        # Calculate basic statistics for logging
        ratings = [r["rating"] for r in review_summary if r["rating"] > 0]
        avg_rating = sum(ratings) / len(ratings) if ratings else 0
        logger.info(f"Review statistics: Average rating {avg_rating:.1f}, {len(ratings)} valid ratings")
        
        prompt = f"""Analyze these Amazon product reviews and provide actionable insights:

Reviews Sample ({len(review_summary)} of {len(reviews)} total):
{json.dumps(review_summary)}

Provide analysis covering:
1. Common complaints and issues
2. Areas for improvement
3. Customer suggestions
4. Quality concerns
5. Competitive advantages

Keep response concise and actionable."""
        
        try:
            logger.info("Sending product review analysis request to LLM")
            response = self._generate_response(prompt)
            
            if isinstance(response, dict) and "response" in response:
                result = response["response"]
                logger.info(f"LLM review analysis successful: {len(result)} characters generated")
                return result
            else:
                logger.warning("Invalid LLM response format for review analysis, using fallback")
                return self._generate_fallback_review_analysis(review_summary)
        except Exception as e:
            logger.error(f"Review analysis failed: {str(e)}, using fallback")
            return self._generate_fallback_review_analysis(review_summary)
    
    def analyze_social_media_content(self, content: List[Dict], platform: str) -> str:
        """Analyze social media content with platform-specific insights"""
        if not content:
            return f"No {platform} content to analyze."
        
        # Clean and truncate data
        clean_content = self._sanitize_text_data(content)
        sample_content = self._truncate_data(clean_content, 25)
        
        # Extract platform-specific metrics
        content_summary = []
        for item in sample_content:
            summary = {
                "text": item.get("text", item.get("description", item.get("caption", "")))[:150],
                "engagement": {
                    "likes": item.get("like_count", item.get("likes", 0)),
                    "comments": item.get("reply_count", item.get("comment_count", item.get("comments", 0))),
                    "shares": item.get("retweet_count", item.get("share_count", item.get("shares", 0)))
                },
                "date": item.get("created_at", item.get("date", ""))[:10]
            }
            content_summary.append(summary)
        
        prompt = f"""Analyze this {platform} content for insights:

Content Sample ({len(content_summary)} of {len(content)} total):
{json.dumps(content_summary)}

Provide insights on:
1. Engagement patterns and trends
2. Top performing content types
3. Audience response indicators
4. Content optimization recommendations
5. Platform-specific strategy suggestions

Focus on actionable insights for {platform}."""
        
        try:
            response = self._generate_response(prompt)
            if isinstance(response, dict) and "response" in response:
                return response["response"]
            else:
                return self._generate_fallback_social_analysis(content_summary, platform)
        except Exception as e:
            logger.error(f"Social media analysis failed: {str(e)}")
            return self._generate_fallback_social_analysis(content_summary, platform)
    
    def _generate_fallback_review_analysis(self, reviews: List[Dict]) -> str:
        """Generate basic review analysis without LLM"""
        if not reviews:
            return "No reviews available for analysis."
        
        total_reviews = len(reviews)
        ratings = [r.get("rating", 0) for r in reviews if r.get("rating")]
        avg_rating = sum(ratings) / len(ratings) if ratings else 0
        
        # Count ratings
        rating_dist = {}
        for rating in ratings:
            rating_dist[rating] = rating_dist.get(rating, 0) + 1
        
        analysis = f"""**Review Analysis Summary**

**Overview:**
- Total Reviews Analyzed: {total_reviews}
- Average Rating: {avg_rating:.1f}/5.0
- Rating Distribution: {rating_dist}

**Key Insights:**
- {'High customer satisfaction' if avg_rating >= 4 else 'Mixed customer satisfaction' if avg_rating >= 3 else 'Low customer satisfaction'}
- Most common rating: {max(rating_dist.keys(), key=lambda k: rating_dist[k]) if rating_dist else 'N/A'}
- Review text analysis requires full LLM processing

**Recommendations:**
- Monitor low-rated reviews for specific issues
- Analyze high-rated reviews for strengths to emphasize
- Consider implementing feedback collection improvements"""
        
        return analysis
    
    def _generate_fallback_social_analysis(self, content: List[Dict], platform: str) -> str:
        """Generate basic social media analysis without LLM"""
        if not content:
            return f"No {platform} content available for analysis."
        
        total_posts = len(content)
        engagements = []
        
        for item in content:
            eng = item.get("engagement", {})
            total_eng = eng.get("likes", 0) + eng.get("comments", 0) + eng.get("shares", 0)
            engagements.append(total_eng)
        
        avg_engagement = sum(engagements) / len(engagements) if engagements else 0
        max_engagement = max(engagements) if engagements else 0
        
        analysis = f"""**{platform.title()} Content Analysis**

**Overview:**
- Total Posts Analyzed: {total_posts}
- Average Engagement: {avg_engagement:.1f}
- Peak Engagement: {max_engagement}

**Engagement Metrics:**
- Average Likes: {sum(item.get("engagement", {}).get("likes", 0) for item in content) / total_posts:.1f}
- Average Comments: {sum(item.get("engagement", {}).get("comments", 0) for item in content) / total_posts:.1f}
- Average Shares: {sum(item.get("engagement", {}).get("shares", 0) for item in content) / total_posts:.1f}

**Recommendations:**
- {'Strong engagement performance' if avg_engagement > 100 else 'Moderate engagement' if avg_engagement > 20 else 'Focus on improving engagement'}
- Analyze top-performing posts for successful content patterns
- Consider timing and frequency optimization"""
        
        return analysis
    
    @retry_on_failure(max_retries=2, delay=2.0)
    def _generate_response(self, prompt: str) -> Dict:
        """Generate response from LLM with caching and retry logic"""
        self._ensure_config()
        
        # Check cache first
        cached_response = self.cache.get(prompt, self.model_name)
        if cached_response:
            return cached_response
        
        # Limit prompt length
        if len(prompt) > self.max_prompt_length:
            prompt = prompt[:self.max_prompt_length] + "...\n\nProvide analysis based on available data."
        
        try:
            payload = {
                "model": self.model_name,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": 0.3,  # Lower temperature for more consistent results
                    "top_k": 40,
                    "top_p": 0.9,
                    "num_predict": 1000,  # Reasonable response length
                }
            }
            
            logger.info(f"Sending request to LLM API: {self.api_url}")
            start_time = time.time()
            
            response = requests.post(
                self.api_url, 
                json=payload, 
                timeout=self.request_timeout,
                headers={'Content-Type': 'application/json'}
            )
            
            end_time = time.time()
            logger.info(f"LLM API response received in {end_time - start_time:.2f} seconds")
            
            if response.status_code == 200:
                response_data = response.json()
                
                # Cache the response
                self.cache.set(prompt, self.model_name, response_data)
                
                return response_data
            else:
                error_msg = f"LLM API error: {response.status_code} - {response.text}"
                logger.error(error_msg)
                return {"error": error_msg}
                
        except requests.exceptions.Timeout:
            error_msg = f"LLM API timeout after {self.request_timeout} seconds"
            logger.error(error_msg)
            raise Exception(error_msg)
        except requests.exceptions.ConnectionError:
            error_msg = "Failed to connect to LLM API - check if Ollama is running"
            logger.error(error_msg)
            raise Exception(error_msg)
        except requests.exceptions.RequestException as e:
            error_msg = f"LLM API request failed: {str(e)}"
            logger.error(error_msg)
            raise Exception(error_msg)
        except Exception as e:
            error_msg = f"Unexpected LLM error: {str(e)}"
            logger.error(error_msg)
            raise Exception(error_msg)
    
    def analyze_content_comprehensive(self, content: List[Dict], platform: str = None) -> Dict:
        """Comprehensive multi-dimensional content analysis"""
        logger.info(f"Starting comprehensive content analysis for {len(content)} items on {platform}")
        
        try:
            # Use advanced analyzer for detailed analysis
            advanced_analysis = self.advanced_analyzer.comprehensive_analysis(content, platform)
            
            # Enhance with LLM insights if available
            try:
                # Create a focused prompt for LLM enhancement
                sample_content = content[:10]  # Use first 10 items for LLM analysis
                content_texts = [item.get('text', item.get('description', ''))[:200] for item in sample_content]
                
                llm_prompt = f"""Analyze this {platform or 'content'} data and provide strategic business insights:

Content Sample: {json.dumps(content_texts)}

Please provide:
1. Strategic opportunities based on customer feedback
2. Potential risks or threats to monitor
3. Competitive positioning insights
4. Actionable recommendations for business growth
5. Market trends or patterns you observe

Focus on business-actionable insights rather than just sentiment."""
                
                logger.info("Enhancing analysis with LLM insights")
                llm_response = self._generate_response(llm_prompt)
                
                if isinstance(llm_response, dict) and "response" in llm_response:
                    advanced_analysis['llm_enhanced_insights'] = llm_response["response"]
                    logger.info("LLM enhancement successful")
                else:
                    logger.warning("LLM enhancement failed, using advanced analysis only")
                    advanced_analysis['llm_enhanced_insights'] = "LLM enhancement unavailable"
                    
            except Exception as e:
                logger.warning(f"LLM enhancement failed: {str(e)}")
                advanced_analysis['llm_enhanced_insights'] = "LLM enhancement unavailable"
            
            # Generate comprehensive summary
            advanced_analysis['executive_summary'] = self.advanced_analyzer.generate_summary_report(advanced_analysis)
            
            logger.info("Comprehensive content analysis completed")
            return advanced_analysis
            
        except Exception as e:
            logger.error(f"Comprehensive content analysis failed: {str(e)}")
            return {
                'error': str(e),
                'basic_sentiment': {'sentiment': 'neutral', 'confidence': 0.0},
                'executive_summary': 'Analysis failed due to technical error'
            }
    
    def test_connection(self) -> Dict:
        """Test LLM connection and return status"""
        try:
            test_prompt = "Say 'Hello' if you can hear me."
            response = self._generate_response(test_prompt)
            
            if "error" in response:
                return {"success": False, "error": response["error"]}
            else:
                return {"success": True, "message": "LLM connection successful"}
                
        except Exception as e:
            return {"success": False, "error": str(e)}
