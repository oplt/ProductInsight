from instagrapi import Client
from typing import List, Dict, Optional
import pandas as pd
from datetime import datetime
import os


class InstagramAnalyzer:
    """Instagram content analysis service"""
    
    def __init__(self, username: str = None, password: str = None):
        self.client = Client()
        self.username = username or os.environ.get('INSTAGRAM_USERNAME')
        self.password = password or os.environ.get('INSTAGRAM_PASSWORD')
        self.is_authenticated = False
    
    def authenticate(self) -> bool:
        """Authenticate with Instagram"""
        try:
            if self.username and self.password:
                self.client.login(self.username, self.password)
                self.is_authenticated = True
                return True
        except Exception as e:
            print(f"Instagram authentication failed: {str(e)}")
        return False
    
    def get_user_posts(self, username: str, count: int = 20) -> List[Dict]:
        """Get recent posts for a user"""
        if not self.is_authenticated:
            if not self.authenticate():
                return []
        
        try:
            user_id = self.client.user_id_from_username(username)
            medias = self.client.user_medias(user_id, count)
            
            posts = []
            for media in medias:
                post_data = {
                    'id': media.id,
                    'caption': media.caption_text or '',
                    'created_at': media.taken_at.isoformat(),
                    'likes': media.like_count or 0,
                    'comments': media.comment_count or 0,
                    'media_type': media.media_type.name,
                    'url': f"https://www.instagram.com/p/{media.code}/"
                }
                posts.append(post_data)
            
            return posts
            
        except Exception as e:
            print(f"Error fetching Instagram posts: {str(e)}")
            return []
    
    def get_post_comments(self, media_id: str, count: int = 50) -> List[Dict]:
        """Get comments for a specific post"""
        if not self.is_authenticated:
            if not self.authenticate():
                return []
        
        try:
            comments = self.client.media_comments(media_id, count)
            
            comment_data = []
            for comment in comments:
                comment_info = {
                    'id': comment.pk,
                    'text': comment.text,
                    'username': comment.user.username,
                    'created_at': comment.created_at.isoformat(),
                    'likes': comment.like_count or 0
                }
                comment_data.append(comment_info)
            
            return comment_data
            
        except Exception as e:
            print(f"Error fetching Instagram comments: {str(e)}")
            return []
    
    def get_hashtag_posts(self, hashtag: str, count: int = 20) -> List[Dict]:
        """Get recent posts for a hashtag"""
        if not self.is_authenticated:
            if not self.authenticate():
                return []
        
        try:
            medias = self.client.hashtag_medias_recent(hashtag, count)
            
            posts = []
            for media in medias:
                post_data = {
                    'id': media.id,
                    'caption': media.caption_text or '',
                    'created_at': media.taken_at.isoformat(),
                    'likes': media.like_count or 0,
                    'comments': media.comment_count or 0,
                    'username': media.user.username,
                    'hashtag': hashtag,
                    'url': f"https://www.instagram.com/p/{media.code}/"
                }
                posts.append(post_data)
            
            return posts
            
        except Exception as e:
            print(f"Error fetching Instagram hashtag posts: {str(e)}")
            return []
    
    def get_user_followers_sample(self, username: str, count: int = 100) -> List[Dict]:
        """Get a sample of user's followers (limited by Instagram API)"""
        if not self.is_authenticated:
            if not self.authenticate():
                return []
        
        try:
            user_id = self.client.user_id_from_username(username)
            followers = self.client.user_followers(user_id, count)
            
            follower_data = []
            for user_id, user_info in followers.items():
                follower_info = {
                    'user_id': user_id,
                    'username': user_info.username,
                    'full_name': user_info.full_name or '',
                    'follower_count': user_info.follower_count or 0,
                    'following_count': user_info.following_count or 0,
                    'is_verified': user_info.is_verified or False
                }
                follower_data.append(follower_info)
            
            return follower_data
            
        except Exception as e:
            print(f"Error fetching Instagram followers: {str(e)}")
            return []
    
    def analyze_user_engagement(self, username: str, post_count: int = 20) -> Dict:
        """Analyze engagement metrics for a user"""
        posts = self.get_user_posts(username, post_count)
        
        if not posts:
            return {}
        
        total_likes = sum(post['likes'] for post in posts)
        total_comments = sum(post['comments'] for post in posts)
        total_posts = len(posts)
        
        avg_likes = total_likes / total_posts if total_posts > 0 else 0
        avg_comments = total_comments / total_posts if total_posts > 0 else 0
        engagement_rate = (total_likes + total_comments) / total_posts if total_posts > 0 else 0
        
        return {
            'username': username,
            'total_posts_analyzed': total_posts,
            'total_likes': total_likes,
            'total_comments': total_comments,
            'average_likes_per_post': avg_likes,
            'average_comments_per_post': avg_comments,
            'engagement_rate': engagement_rate,
            'posts': posts
        }
