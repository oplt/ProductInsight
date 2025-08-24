"""
Advanced Content Analysis Service
Enhanced content analysis with multi-dimensional insights
"""

import json
import re
import logging
from typing import Dict, List, Optional, Tuple
from collections import Counter
from datetime import datetime, timedelta
import statistics

logger = logging.getLogger(__name__)

class AdvancedContentAnalyzer:
    """Enhanced content analysis with multi-dimensional insights"""
    
    def __init__(self):
        self.emotion_keywords = {
            'joy': ['happy', 'excited', 'amazing', 'wonderful', 'fantastic', 'love', 'great', 'excellent'],
            'anger': ['angry', 'frustrated', 'terrible', 'awful', 'horrible', 'hate', 'worst', 'disgusting'],
            'fear': ['worried', 'scared', 'concerned', 'afraid', 'nervous', 'uncertain', 'risk', 'dangerous'],
            'surprise': ['unexpected', 'surprising', 'wow', 'incredible', 'unbelievable', 'shocking'],
            'sadness': ['disappointed', 'sad', 'depressed', 'unhappy', 'upset', 'regret', 'sorry'],
            'trust': ['reliable', 'trustworthy', 'dependable', 'honest', 'authentic', 'genuine', 'quality']
        }
        
        self.business_intent_keywords = {
            'purchase_intent': ['buy', 'purchase', 'order', 'get', 'want', 'need', 'shopping', 'price'],
            'complaint': ['problem', 'issue', 'broken', 'defective', 'wrong', 'error', 'complaint', 'refund'],
            'compliment': ['thank', 'appreciate', 'recommend', 'satisfied', 'perfect', 'impressed'],
            'feature_request': ['wish', 'hope', 'would like', 'suggestion', 'improve', 'add', 'feature', 'update'],
            'support_needed': ['help', 'assistance', 'support', 'how to', 'question', 'confused', 'unclear']
        }
        
        self.product_aspects = {
            'quality': ['quality', 'build', 'material', 'construction', 'durable', 'solid', 'cheap', 'flimsy'],
            'price': ['price', 'cost', 'expensive', 'cheap', 'value', 'money', 'affordable', 'budget'],
            'design': ['design', 'look', 'appearance', 'style', 'color', 'beautiful', 'ugly', 'attractive'],
            'performance': ['performance', 'speed', 'fast', 'slow', 'efficient', 'lag', 'smooth', 'responsive'],
            'usability': ['easy', 'difficult', 'user-friendly', 'complicated', 'intuitive', 'confusing'],
            'support': ['support', 'service', 'help', 'response', 'staff', 'team', 'customer service'],
            'delivery': ['delivery', 'shipping', 'fast', 'slow', 'arrived', 'late', 'on time', 'packaging']
        }

    def comprehensive_analysis(self, content_list: List[Dict], platform: str = None) -> Dict:
        """Perform comprehensive multi-dimensional content analysis"""
        logger.info(f"Starting comprehensive analysis for {len(content_list)} items on {platform}")
        
        try:
            # Extract text content
            texts = self._extract_texts(content_list)
            
            if not texts:
                logger.warning("No text content found for analysis")
                return self._empty_analysis_result()
            
            # Perform multi-dimensional analysis
            analysis_result = {
                'basic_sentiment': self._analyze_basic_sentiment(texts),
                'emotion_analysis': self._analyze_emotions(texts),
                'topic_analysis': self._extract_topics(texts),
                'aspect_sentiment': self._analyze_aspect_sentiment(texts),
                'intent_analysis': self._analyze_intent(texts),
                'business_insights': self._generate_business_insights(texts, content_list),
                'temporal_analysis': self._analyze_temporal_patterns(content_list),
                'engagement_analysis': self._analyze_engagement_patterns(content_list, platform),
                'content_quality': self._assess_content_quality(texts),
                'competitive_intelligence': self._extract_competitive_insights(texts),
                'actionable_recommendations': []  # Will be populated based on other analyses
            }
            
            # Generate actionable recommendations
            analysis_result['actionable_recommendations'] = self._generate_recommendations(analysis_result)
            
            logger.info("Comprehensive analysis completed successfully")
            return analysis_result
            
        except Exception as e:
            logger.error(f"Comprehensive analysis failed: {str(e)}")
            return self._empty_analysis_result()

    def _extract_texts(self, content_list: List[Dict]) -> List[str]:
        """Extract text content from various content formats"""
        texts = []
        for item in content_list:
            # Try different text fields
            text = (item.get('text') or 
                   item.get('description') or 
                   item.get('caption') or 
                   item.get('content') or 
                   item.get('review_text') or 
                   item.get('comment') or '')
            
            if text and isinstance(text, str) and len(text.strip()) > 0:
                texts.append(text.strip())
        
        return texts

    def _analyze_basic_sentiment(self, texts: List[str]) -> Dict:
        """Enhanced sentiment analysis with confidence and intensity"""
        if not texts:
            return {'sentiment': 'neutral', 'confidence': 0.0, 'intensity': 0.0}
        
        positive_words = ['good', 'great', 'excellent', 'amazing', 'wonderful', 'fantastic', 'love', 'perfect', 'best']
        negative_words = ['bad', 'terrible', 'awful', 'horrible', 'worst', 'hate', 'disappointing', 'poor']
        
        scores = []
        for text in texts:
            text_lower = text.lower()
            pos_count = sum(1 for word in positive_words if word in text_lower)
            neg_count = sum(1 for word in negative_words if word in text_lower)
            
            if pos_count + neg_count == 0:
                scores.append(0)  # neutral
            else:
                # Score between -1 and 1
                score = (pos_count - neg_count) / (pos_count + neg_count)
                scores.append(score)
        
        avg_score = statistics.mean(scores) if scores else 0
        
        # Determine sentiment
        if avg_score > 0.1:
            sentiment = 'positive'
        elif avg_score < -0.1:
            sentiment = 'negative'
        else:
            sentiment = 'neutral'
        
        # Calculate confidence based on consistency
        confidence = 1 - (statistics.stdev(scores) if len(scores) > 1 else 0)
        intensity = abs(avg_score)
        
        return {
            'sentiment': sentiment,
            'confidence': round(confidence, 2),
            'intensity': round(intensity, 2),
            'score': round(avg_score, 2),
            'distribution': {
                'positive': len([s for s in scores if s > 0.1]),
                'negative': len([s for s in scores if s < -0.1]),
                'neutral': len([s for s in scores if -0.1 <= s <= 0.1])
            }
        }

    def _analyze_emotions(self, texts: List[str]) -> Dict:
        """Analyze emotional content beyond basic sentiment"""
        emotion_scores = {emotion: 0 for emotion in self.emotion_keywords.keys()}
        emotion_mentions = {emotion: [] for emotion in self.emotion_keywords.keys()}
        
        for text in texts:
            text_lower = text.lower()
            for emotion, keywords in self.emotion_keywords.items():
                matches = [word for word in keywords if word in text_lower]
                if matches:
                    emotion_scores[emotion] += len(matches)
                    emotion_mentions[emotion].extend(matches)
        
        # Normalize scores
        total_mentions = sum(emotion_scores.values())
        if total_mentions > 0:
            emotion_distribution = {
                emotion: round(score / total_mentions, 2) 
                for emotion, score in emotion_scores.items()
            }
        else:
            emotion_distribution = emotion_scores
        
        # Find dominant emotions
        dominant_emotions = sorted(emotion_distribution.items(), key=lambda x: x[1], reverse=True)[:3]
        
        return {
            'emotion_distribution': emotion_distribution,
            'dominant_emotions': [emotion for emotion, score in dominant_emotions if score > 0],
            'emotion_intensity': max(emotion_distribution.values()) if emotion_distribution else 0,
            'mixed_emotions': len([score for score in emotion_distribution.values() if score > 0.1]) > 1
        }

    def _extract_topics(self, texts: List[str]) -> Dict:
        """Extract main topics and themes from content"""
        # Simple topic extraction using keyword frequency
        # In production, you'd use more sophisticated methods like LDA
        
        # Combine all texts
        combined_text = ' '.join(texts).lower()
        
        # Remove common stop words
        stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 'is', 'are', 'was', 'were', 'be', 'been', 'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could', 'should', 'this', 'that', 'these', 'those', 'i', 'you', 'he', 'she', 'it', 'we', 'they', 'my', 'your', 'his', 'her', 'its', 'our', 'their'}
        
        # Extract words (simple tokenization)
        words = re.findall(r'\b[a-zA-Z]{3,}\b', combined_text)
        words = [word for word in words if word not in stop_words]
        
        # Count word frequency
        word_freq = Counter(words)
        
        # Get top topics
        top_topics = word_freq.most_common(10)
        
        return {
            'top_topics': [{'topic': topic, 'frequency': freq} for topic, freq in top_topics],
            'total_unique_topics': len(word_freq),
            'topic_diversity': len(word_freq) / len(words) if words else 0
        }

    def _analyze_aspect_sentiment(self, texts: List[str]) -> Dict:
        """Analyze sentiment for specific product/service aspects"""
        aspect_sentiments = {}
        
        for aspect, keywords in self.product_aspects.items():
            aspect_texts = []
            for text in texts:
                text_lower = text.lower()
                if any(keyword in text_lower for keyword in keywords):
                    aspect_texts.append(text)
            
            if aspect_texts:
                sentiment_result = self._analyze_basic_sentiment(aspect_texts)
                aspect_sentiments[aspect] = {
                    'sentiment': sentiment_result['sentiment'],
                    'score': sentiment_result['score'],
                    'mentions': len(aspect_texts),
                    'confidence': sentiment_result['confidence']
                }
        
        return aspect_sentiments

    def _analyze_intent(self, texts: List[str]) -> Dict:
        """Classify user intent from content"""
        intent_scores = {intent: 0 for intent in self.business_intent_keywords.keys()}
        
        for text in texts:
            text_lower = text.lower()
            for intent, keywords in self.business_intent_keywords.items():
                matches = sum(1 for keyword in keywords if keyword in text_lower)
                intent_scores[intent] += matches
        
        # Normalize and get primary intent
        total_score = sum(intent_scores.values())
        if total_score > 0:
            intent_distribution = {
                intent: round(score / total_score, 2) 
                for intent, score in intent_scores.items()
            }
            primary_intent = max(intent_distribution.items(), key=lambda x: x[1])
        else:
            intent_distribution = intent_scores
            primary_intent = ('unknown', 0)
        
        return {
            'primary_intent': primary_intent[0],
            'intent_confidence': primary_intent[1],
            'intent_distribution': intent_distribution,
            'mixed_intent': len([score for score in intent_distribution.values() if score > 0.2]) > 1
        }

    def _generate_business_insights(self, texts: List[str], content_list: List[Dict]) -> Dict:
        """Generate actionable business insights"""
        insights = {
            'key_opportunities': [],
            'risk_areas': [],
            'improvement_suggestions': [],
            'competitive_advantages': [],
            'customer_needs': []
        }
        
        # Analyze for opportunities
        opportunity_keywords = ['want', 'need', 'wish', 'hope', 'would like', 'missing', 'lack']
        for text in texts:
            text_lower = text.lower()
            if any(keyword in text_lower for keyword in opportunity_keywords):
                insights['key_opportunities'].append(text[:100] + '...' if len(text) > 100 else text)
        
        # Analyze for risks
        risk_keywords = ['problem', 'issue', 'complaint', 'disappointed', 'angry', 'frustrated']
        for text in texts:
            text_lower = text.lower()
            if any(keyword in text_lower for keyword in risk_keywords):
                insights['risk_areas'].append(text[:100] + '...' if len(text) > 100 else text)
        
        # Limit to top insights
        insights['key_opportunities'] = insights['key_opportunities'][:5]
        insights['risk_areas'] = insights['risk_areas'][:5]
        
        return insights

    def _analyze_temporal_patterns(self, content_list: List[Dict]) -> Dict:
        """Analyze temporal patterns in content"""
        dates = []
        for item in content_list:
            date_str = item.get('date') or item.get('created_at') or item.get('timestamp')
            if date_str:
                try:
                    # Try to parse date (this is simplified - you'd want more robust parsing)
                    if isinstance(date_str, str):
                        dates.append(date_str[:10])  # Take first 10 chars (YYYY-MM-DD format)
                except:
                    continue
        
        if not dates:
            return {'temporal_data': False}
        
        # Count by date
        date_counts = Counter(dates)
        
        return {
            'temporal_data': True,
            'date_range': {'start': min(dates), 'end': max(dates)} if dates else None,
            'post_frequency': len(dates) / max(1, len(set(dates))),  # Average posts per day
            'peak_dates': date_counts.most_common(3),
            'trend': 'increasing' if len(dates) > 10 else 'stable'  # Simplified trend
        }

    def _analyze_engagement_patterns(self, content_list: List[Dict], platform: str) -> Dict:
        """Analyze engagement metrics"""
        engagements = []
        for item in content_list:
            engagement = {
                'likes': item.get('like_count', item.get('likes', 0)),
                'comments': item.get('reply_count', item.get('comment_count', item.get('comments', 0))),
                'shares': item.get('retweet_count', item.get('share_count', item.get('shares', 0)))
            }
            engagements.append(engagement)
        
        if not engagements:
            return {'engagement_data': False}
        
        # Calculate averages
        avg_likes = statistics.mean([e['likes'] for e in engagements])
        avg_comments = statistics.mean([e['comments'] for e in engagements])
        avg_shares = statistics.mean([e['shares'] for e in engagements])
        
        # Calculate engagement rate (simplified)
        total_engagement = avg_likes + avg_comments + avg_shares
        
        return {
            'engagement_data': True,
            'average_engagement': {
                'likes': round(avg_likes, 1),
                'comments': round(avg_comments, 1),
                'shares': round(avg_shares, 1)
            },
            'total_avg_engagement': round(total_engagement, 1),
            'engagement_rate': 'high' if total_engagement > 100 else 'medium' if total_engagement > 20 else 'low',
            'best_performing': max(engagements, key=lambda x: x['likes'] + x['comments'] + x['shares'])
        }

    def _assess_content_quality(self, texts: List[str]) -> Dict:
        """Assess overall content quality"""
        if not texts:
            return {'quality_score': 0}
        
        total_length = sum(len(text) for text in texts)
        avg_length = total_length / len(texts)
        
        # Simple quality metrics
        quality_indicators = {
            'average_length': avg_length,
            'length_variance': statistics.stdev([len(text) for text in texts]) if len(texts) > 1 else 0,
            'readability': 'good' if 50 < avg_length < 200 else 'needs_improvement',
            'content_richness': len(set(' '.join(texts).lower().split())) / total_length if total_length > 0 else 0
        }
        
        # Calculate overall quality score (0-1)
        quality_score = 0.7 if quality_indicators['readability'] == 'good' else 0.4
        quality_score += min(quality_indicators['content_richness'] * 10, 0.3)
        
        return {
            'quality_score': round(quality_score, 2),
            'quality_indicators': quality_indicators
        }

    def _extract_competitive_insights(self, texts: List[str]) -> Dict:
        """Extract competitive intelligence"""
        competitor_mentions = []
        comparison_keywords = ['better than', 'worse than', 'compared to', 'vs', 'versus', 'alternative to']
        
        for text in texts:
            text_lower = text.lower()
            if any(keyword in text_lower for keyword in comparison_keywords):
                competitor_mentions.append(text[:100] + '...' if len(text) > 100 else text)
        
        return {
            'competitor_mentions': competitor_mentions[:5],
            'competitive_context': len(competitor_mentions) > 0,
            'comparison_frequency': len(competitor_mentions) / len(texts) if texts else 0
        }

    def _generate_recommendations(self, analysis_result: Dict) -> List[Dict]:
        """Generate actionable recommendations based on analysis"""
        recommendations = []
        
        # Sentiment-based recommendations
        sentiment = analysis_result['basic_sentiment']['sentiment']
        if sentiment == 'negative':
            recommendations.append({
                'type': 'urgent',
                'category': 'customer_service',
                'action': 'Address negative sentiment immediately',
                'priority': 'high',
                'description': 'Negative sentiment detected. Review customer complaints and implement improvements.'
            })
        
        # Intent-based recommendations
        primary_intent = analysis_result['intent_analysis']['primary_intent']
        if primary_intent == 'complaint':
            recommendations.append({
                'type': 'reactive',
                'category': 'support',
                'action': 'Improve customer support response',
                'priority': 'high',
                'description': 'High complaint volume detected. Enhance support processes.'
            })
        elif primary_intent == 'feature_request':
            recommendations.append({
                'type': 'strategic',
                'category': 'product_development',
                'action': 'Analyze feature requests for product roadmap',
                'priority': 'medium',
                'description': 'Customer feature requests identified. Consider for product development.'
            })
        
        # Engagement-based recommendations
        if analysis_result['engagement_analysis'].get('engagement_data'):
            engagement_rate = analysis_result['engagement_analysis']['engagement_rate']
            if engagement_rate == 'low':
                recommendations.append({
                    'type': 'strategic',
                    'category': 'content_strategy',
                    'action': 'Improve content engagement strategy',
                    'priority': 'medium',
                    'description': 'Low engagement detected. Review content strategy and posting times.'
                })
        
        return recommendations

    def _empty_analysis_result(self) -> Dict:
        """Return empty analysis result for error cases"""
        return {
            'basic_sentiment': {'sentiment': 'neutral', 'confidence': 0.0, 'intensity': 0.0},
            'emotion_analysis': {'emotion_distribution': {}, 'dominant_emotions': []},
            'topic_analysis': {'top_topics': [], 'total_unique_topics': 0},
            'aspect_sentiment': {},
            'intent_analysis': {'primary_intent': 'unknown', 'intent_confidence': 0.0},
            'business_insights': {'key_opportunities': [], 'risk_areas': []},
            'temporal_analysis': {'temporal_data': False},
            'engagement_analysis': {'engagement_data': False},
            'content_quality': {'quality_score': 0},
            'competitive_intelligence': {'competitor_mentions': []},
            'actionable_recommendations': []
        }

    def generate_summary_report(self, analysis_result: Dict) -> str:
        """Generate a human-readable summary report"""
        try:
            sentiment = analysis_result['basic_sentiment']['sentiment']
            confidence = analysis_result['basic_sentiment']['confidence']
            primary_intent = analysis_result['intent_analysis']['primary_intent']
            dominant_emotions = analysis_result['emotion_analysis']['dominant_emotions']
            
            report = f"""
## Content Analysis Summary Report

### Overall Sentiment
- **Sentiment**: {sentiment.title()} (Confidence: {confidence:.0%})
- **Primary Intent**: {primary_intent.replace('_', ' ').title()}
- **Dominant Emotions**: {', '.join(dominant_emotions[:3]) if dominant_emotions else 'None detected'}

### Key Insights
- **Top Opportunities**: {len(analysis_result['business_insights']['key_opportunities'])} identified
- **Risk Areas**: {len(analysis_result['business_insights']['risk_areas'])} found
- **Content Quality**: {analysis_result['content_quality']['quality_score']:.0%}

### Recommendations
{chr(10).join([f"- {rec['action']}" for rec in analysis_result['actionable_recommendations'][:5]])}

### Engagement Analysis
"""
            
            if analysis_result['engagement_analysis'].get('engagement_data'):
                eng = analysis_result['engagement_analysis']
                report += f"- **Engagement Rate**: {eng['engagement_rate'].title()}\n"
                report += f"- **Average Likes**: {eng['average_engagement']['likes']}\n"
                report += f"- **Average Comments**: {eng['average_engagement']['comments']}\n"
            else:
                report += "- No engagement data available\n"
            
            return report.strip()
            
        except Exception as e:
            logger.error(f"Failed to generate summary report: {str(e)}")
            return "Error generating summary report"
