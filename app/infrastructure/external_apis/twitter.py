import tweepy
import datetime
import pandas as pd
import os
from dotenv import load_dotenv
from typing import List, Dict, Optional

load_dotenv()


class TwitterAnalyzer:
    """Twitter content analysis service"""
    
    def __init__(self, bearer_token: str = None, api_key: str = None, 
                 api_secret: str = None, access_token: str = None, 
                 access_token_secret: str = None):
        self.bearer_token = bearer_token or os.environ.get('TWITTER_BEARER_TOKEN')
        self.api_key = api_key or os.environ.get('TWITTER_API_KEY')
        self.api_secret = api_secret or os.environ.get('TWITTER_API_SECRET')
        self.access_token = access_token or os.environ.get('TWITTER_ACCESS_TOKEN')
        self.access_token_secret = access_token_secret or os.environ.get('TWITTER_ACCESS_TOKEN_SECRET')
        
        self.client = None
        self.api_v1 = None
        self._initialize_clients()
    
    def _initialize_clients(self):
        """Initialize Twitter API clients"""
        try:
            # Initialize v2 client (for most operations)
            if self.bearer_token:
                self.client = tweepy.Client(
                    bearer_token=self.bearer_token,
                    consumer_key=self.api_key,
                    consumer_secret=self.api_secret,
                    access_token=self.access_token,
                    access_token_secret=self.access_token_secret,
                    wait_on_rate_limit=True
                )
            
            # Initialize v1.1 API for some operations
            if all([self.api_key, self.api_secret, self.access_token, self.access_token_secret]):
                auth = tweepy.OAuth1UserHandler(
                    self.api_key, self.api_secret,
                    self.access_token, self.access_token_secret
                )
                self.api_v1 = tweepy.API(auth, wait_on_rate_limit=True)
                
        except Exception as e:
            print(f"Twitter API initialization failed: {str(e)}")
    
    def get_user_id(self, username: str) -> Optional[str]:
        """Get user ID from username"""
        if not self.client:
            return None
        
        try:
            user = self.client.get_user(username=username)
            return user.data.id if user.data else None
        except Exception as e:
            print(f"Error getting user ID for {username}: {str(e)}")
            return None


    def get_user_tweets(self, user_id: str, start_time: str = None, 
                       max_results: int = 100) -> List[Dict]:
        """Get all tweets from a user account"""
        if not self.client:
            return []
        
        try:
            tweets = []
            
            # If no start_time provided, default to 30 days ago
            if start_time is None:
                start_time = (datetime.datetime.now() - datetime.timedelta(days=30)).strftime('%Y-%m-%dT%H:%M:%SZ')
            
            # Pagination
            pagination_token = None
            
            while True:
                response = self.client.get_users_tweets(
                    id=user_id,
                    start_time=start_time,
                    max_results=min(max_results, 100),  # API limit
                    pagination_token=pagination_token,
                    tweet_fields=['public_metrics', 'created_at', 'context_annotations'],
                    expansions=['author_id'],
                    user_fields=['username', 'public_metrics']
                )
                
                if not response.data:
                    break
                
                for tweet in response.data:
                    tweet_data = {
                        'id': tweet.id,
                        'text': tweet.text,
                        'created_at': tweet.created_at.isoformat(),
                        'like_count': tweet.public_metrics.get('like_count', 0),
                        'reply_count': tweet.public_metrics.get('reply_count', 0),
                        'retweet_count': tweet.public_metrics.get('retweet_count', 0),
                        'quote_count': tweet.public_metrics.get('quote_count', 0)
                    }
                    tweets.append(tweet_data)
                
                if len(tweets) >= max_results:
                    break
                
                if 'next_token' in response.meta:
                    pagination_token = response.meta['next_token']
                else:
                    break
            
            return tweets[:max_results]
            
        except Exception as e:
            print(f"Error fetching user tweets: {str(e)}")
            return []
    
    def get_replies_to_tweets(self, username: str, tweet_ids: List[str], 
                             start_time: str = None, max_results: int = 100) -> List[Dict]:
        """Get all replies to user's tweets"""
        if not self.client:
            return []
        
        try:
            all_replies = []
            
            if start_time is None:
                start_time = (datetime.datetime.now() - datetime.timedelta(days=30)).strftime('%Y-%m-%dT%H:%M:%SZ')
            
            for tweet_id in tweet_ids:
                pagination_token = None
                
                while True:
                    try:
                        response = self.client.search_recent_tweets(
                            query=f'conversation_id:{tweet_id} to:{username}',
                            start_time=start_time,
                            max_results=min(max_results, 100),
                            next_token=pagination_token,
                            tweet_fields=['public_metrics', 'created_at', 'in_reply_to_user_id'],
                            expansions=['author_id'],
                            user_fields=['username']
                        )
                        
                        if not response.data:
                            break
                        
                        for reply in response.data:
                            reply_data = {
                                'id': reply.id,
                                'text': reply.text,
                                'created_at': reply.created_at.isoformat(),
                                'in_reply_to_tweet_id': tweet_id,
                                'like_count': reply.public_metrics.get('like_count', 0),
                                'reply_count': reply.public_metrics.get('reply_count', 0),
                                'retweet_count': reply.public_metrics.get('retweet_count', 0)
                            }
                            all_replies.append(reply_data)
                        
                        if 'next_token' in response.meta:
                            pagination_token = response.meta['next_token']
                        else:
                            break
                            
                    except Exception as e:
                        print(f"Error fetching replies for tweet {tweet_id}: {str(e)}")
                        break
                
                if len(all_replies) >= max_results:
                    break
            
            return all_replies[:max_results]
            
        except Exception as e:
            print(f"Error fetching replies: {str(e)}")
            return []
    
    def get_mentions(self, user_id: str, start_time: str = None, 
                    max_results: int = 100) -> List[Dict]:
        """Get all mentions of the user account"""
        if not self.client:
            return []
        
        try:
            mentions = []
            
            if start_time is None:
                start_time = (datetime.datetime.now() - datetime.timedelta(days=30)).strftime('%Y-%m-%dT%H:%M:%SZ')
            
            pagination_token = None
            
            while True:
                response = self.client.get_users_mentions(
                    id=user_id,
                    start_time=start_time,
                    max_results=min(max_results, 100),
                    pagination_token=pagination_token,
                    tweet_fields=['public_metrics', 'created_at', 'conversation_id'],
                    expansions=['author_id'],
                    user_fields=['username']
                )
                
                if not response.data:
                    break
                
                for mention in response.data:
                    mention_data = {
                        'id': mention.id,
                        'text': mention.text,
                        'created_at': mention.created_at.isoformat(),
                        'conversation_id': mention.conversation_id,
                        'like_count': mention.public_metrics.get('like_count', 0),
                        'reply_count': mention.public_metrics.get('reply_count', 0),
                        'retweet_count': mention.public_metrics.get('retweet_count', 0)
                    }
                    mentions.append(mention_data)
                
                if len(mentions) >= max_results:
                    break
                
                if 'next_token' in response.meta:
                    pagination_token = response.meta['next_token']
                else:
                    break
            
            return mentions[:max_results]
            
        except Exception as e:
            print(f"Error fetching mentions: {str(e)}")
            return []
    
    def search_tweets(self, query: str, max_results: int = 100, 
                     start_time: str = None) -> List[Dict]:
        """Search for tweets by query"""
        if not self.client:
            return []
        
        try:
            tweets = []
            
            if start_time is None:
                start_time = (datetime.datetime.now() - datetime.timedelta(days=7)).strftime('%Y-%m-%dT%H:%M:%SZ')
            
            pagination_token = None
            
            while True:
                response = self.client.search_recent_tweets(
                    query=query,
                    start_time=start_time,
                    max_results=min(max_results, 100),
                    next_token=pagination_token,
                    tweet_fields=['public_metrics', 'created_at', 'context_annotations'],
                    expansions=['author_id'],
                    user_fields=['username', 'public_metrics']
                )
                
                if not response.data:
                    break
                
                for tweet in response.data:
                    tweet_data = {
                        'id': tweet.id,
                        'text': tweet.text,
                        'created_at': tweet.created_at.isoformat(),
                        'like_count': tweet.public_metrics.get('like_count', 0),
                        'reply_count': tweet.public_metrics.get('reply_count', 0),
                        'retweet_count': tweet.public_metrics.get('retweet_count', 0),
                        'quote_count': tweet.public_metrics.get('quote_count', 0),
                        'query': query
                    }
                    tweets.append(tweet_data)
                
                if len(tweets) >= max_results:
                    break
                
                if 'next_token' in response.meta:
                    pagination_token = response.meta['next_token']
                else:
                    break
            
            return tweets[:max_results]
            
        except Exception as e:
            print(f"Error searching tweets: {str(e)}")
            return []
    
    def analyze_user_engagement(self, username: str, tweet_count: int = 100) -> Dict:
        """Analyze engagement metrics for a user"""
        user_id = self.get_user_id(username)
        if not user_id:
            return {}
        
        tweets = self.get_user_tweets(user_id, max_results=tweet_count)
        if not tweets:
            return {}
        
        total_likes = sum(tweet['like_count'] for tweet in tweets)
        total_replies = sum(tweet['reply_count'] for tweet in tweets)
        total_retweets = sum(tweet['retweet_count'] for tweet in tweets)
        total_quotes = sum(tweet.get('quote_count', 0) for tweet in tweets)
        total_tweets = len(tweets)
        
        avg_likes = total_likes / total_tweets if total_tweets > 0 else 0
        avg_replies = total_replies / total_tweets if total_tweets > 0 else 0
        avg_retweets = total_retweets / total_tweets if total_tweets > 0 else 0
        avg_quotes = total_quotes / total_tweets if total_tweets > 0 else 0
        
        engagement_rate = (total_likes + total_replies + total_retweets + total_quotes) / total_tweets if total_tweets > 0 else 0
        
        return {
            'username': username,
            'total_tweets_analyzed': total_tweets,
            'total_likes': total_likes,
            'total_replies': total_replies,
            'total_retweets': total_retweets,
            'total_quotes': total_quotes,
            'average_likes_per_tweet': avg_likes,
            'average_replies_per_tweet': avg_replies,
            'average_retweets_per_tweet': avg_retweets,
            'average_quotes_per_tweet': avg_quotes,
            'engagement_rate': engagement_rate,
            'tweets': tweets
        }