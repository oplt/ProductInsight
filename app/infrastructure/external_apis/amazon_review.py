from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from webdriver_manager.chrome import ChromeDriverManager
import time
import pandas as pd
from dotenv import load_dotenv
import json
from datetime import datetime
import requests
import browser_cookie3
from typing import List, Dict, Optional
import os
import logging

# Configure logger for this module
logger = logging.getLogger(__name__)

load_dotenv()


class AmazonReviewAnalyzer:
    """Amazon product review analysis service"""
    
    def __init__(self, cookies_path: str = None):
        self.cookies_path = cookies_path or os.environ.get('AMAZON_COOKIES_PATH', 'cookies.json')
        self.driver = None
    
    def get_domain_cookies(self, domain: str = "amazon.com") -> bool:
        """Extract cookies from browser for Amazon domain"""
        try:
            cookies = browser_cookie3.chrome(domain_name=domain)
            cookies_list = []
            
            for cookie in cookies:
                cookies_list.append({
                    "name": cookie.name,
                    "value": cookie.value,
                    "domain": cookie.domain,
                    "path": cookie.path,
                    "expires": cookie.expires,
                    "secure": cookie.secure and True or False,
                    "httponly": cookie.has_nonstandard_attr("HttpOnly"),
                })
            
            with open(self.cookies_path, "w") as f:
                json.dump(cookies_list, f, indent=4)
            
            return True
        except Exception as e:
            print(f"Error extracting cookies: {str(e)}")
            return False
    
    def create_driver(self, headless: bool = True) -> webdriver.Chrome:
        """Create and configure Chrome WebDriver"""
        chrome_options = Options()
        chrome_options.add_argument("--window-size=1920,1080")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        
        if headless:
            chrome_options.add_argument("--headless")
        
        driver = webdriver.Chrome(
            service=Service(ChromeDriverManager().install()), 
            options=chrome_options
        )
        
        # Execute script to remove webdriver property
        driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        
        return driver
    
    def amazon_login(self) -> Optional[webdriver.Chrome]:
        """Login to Amazon using saved cookies"""
        try:
            self.driver = self.create_driver()
            self.driver.get("https://www.amazon.com")
            
            # Wait for page load
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            
            # Load cookies if available
            if os.path.exists(self.cookies_path):
                with open(self.cookies_path, "r") as file:
                    cookies = json.load(file)
                    for cookie in cookies:
                        cookie.pop("expiry", None)
                        try:
                            self.driver.add_cookie(cookie)
                        except Exception as e:
                            continue  # Skip invalid cookies
                
                self.driver.refresh()
                time.sleep(2)
            
            return self.driver
            
        except Exception as e:
            print(f"Amazon login failed: {str(e)}")
            if self.driver:
                self.driver.quit()
            return None
    
    def get_product_review_page(self, asin: str) -> bool:
        """Navigate to product reviews page"""
        if not self.driver:
            return False
        
        try:
            product_url = f"https://www.amazon.com/dp/{asin}"
            self.driver.get(product_url)
            
            # Wait for page load and find reviews link
            wait = WebDriverWait(self.driver, 10)
            reviews_link = wait.until(
                EC.element_to_be_clickable((By.XPATH, "//a[contains(@href, '/product-reviews/')]"))
            )
            
            self.driver.execute_script("arguments[0].click();", reviews_link)
            time.sleep(2)
            
            return True
            
        except (TimeoutException, NoSuchElementException) as e:
            print(f"Could not find reviews link for ASIN {asin}: {str(e)}")
            return False
    
    def scrape_reviews(self, max_reviews: int = 50) -> List[Dict]:
        """Scrape reviews from Amazon product page"""
        if not self.driver:
            return []
        
        reviews = []
        review_count = 0
        pages_scraped = 0
        max_pages = 5  # Limit to prevent infinite loops
        
        while review_count < max_reviews and pages_scraped < max_pages:
            try:
                # Wait for reviews to load
                wait = WebDriverWait(self.driver, 10)
                wait.until(
                    EC.presence_of_element_located((By.XPATH, "//li[@data-hook='review']"))
                )
                
                review_elements = self.driver.find_elements(By.XPATH, "//li[@data-hook='review']")
                
                for review in review_elements:
                    if review_count >= max_reviews:
                        break
                    
                    try:
                        # Extract review text
                        text_element = review.find_element(By.XPATH, ".//span[@data-hook='review-body']")
                        text = text_element.text.strip()
                        
                        # Extract rating
                        rating_element = review.find_element(By.XPATH, ".//a[@data-hook='review-title']/i")
                        rating_text = rating_element.get_attribute("textContent") or rating_element.get_attribute("class")
                        rating = self._extract_rating(rating_text)
                        
                        # Extract date
                        date_element = review.find_element(By.XPATH, ".//span[@data-hook='review-date']")
                        date = self._extract_date(date_element.text)
                        
                        # Extract reviewer name (optional)
                        try:
                            reviewer_element = review.find_element(By.XPATH, ".//a[@data-hook='review-author']")
                            reviewer = reviewer_element.text.strip()
                        except NoSuchElementException:
                            reviewer = "Anonymous"
                        
                        # Extract helpful votes (optional)
                        try:
                            helpful_element = review.find_element(By.XPATH, ".//span[@data-hook='helpful-vote-statement']")
                            helpful_votes = self._extract_helpful_votes(helpful_element.text)
                        except NoSuchElementException:
                            helpful_votes = 0
                        
                        review_data = {
                            'date': date,
                            'text': text,
                            'rating': rating,
                            'reviewer': reviewer,
                            'helpful_votes': helpful_votes
                        }
                        
                        reviews.append(review_data)
                        review_count += 1
                        
                    except Exception as e:
                        print(f"Error extracting individual review: {str(e)}")
                        continue
                
                # Try to go to next page
                if review_count < max_reviews:
                    try:
                        next_button = self.driver.find_element(
                            By.XPATH, "//li[@class='a-last']/a[contains(text(), 'Next page')]"
                        )
                        self.driver.execute_script("arguments[0].click();", next_button)
                        time.sleep(3)
                        pages_scraped += 1
                    except NoSuchElementException:
                        print("No more pages available")
                        break
                else:
                    break
                    
            except TimeoutException:
                print("Timeout waiting for reviews to load")
                break
            except Exception as e:
                print(f"Error during review scraping: {str(e)}")
                break
        
        return reviews
    
    def _extract_rating(self, rating_text: str) -> float:
        """Extract rating number from rating text or class"""
        try:
            if "star" in rating_text.lower():
                # Extract from text like "5.0 out of 5 stars"
                parts = rating_text.split()
                for part in parts:
                    try:
                        return float(part)
                    except ValueError:
                        continue
            return 0.0
        except Exception:
            return 0.0
    
    def _extract_date(self, date_text: str) -> str:
        """Extract and format date from review date text"""
        try:
            # Remove "Reviewed in" and extract date part
            date_str = date_text.replace("Reviewed in", "").strip()
            if "on " in date_str:
                date_str = date_str.split("on ")[-1].strip()
            
            # Parse date
            date_obj = datetime.strptime(date_str, "%B %d, %Y")
            return date_obj.strftime("%d/%m/%Y")
        except ValueError:
            try:
                # Alternative format
                date_obj = datetime.strptime(date_str, "%B %Y")
                return date_obj.strftime("%m/%Y")
            except ValueError:
                return "Unknown"
    
    def _extract_helpful_votes(self, helpful_text: str) -> int:
        """Extract helpful votes count from text"""
        try:
            # Text like "5 people found this helpful"
            parts = helpful_text.split()
            for part in parts:
                try:
                    return int(part)
                except ValueError:
                    continue
            return 0
        except Exception:
            return 0
    
    def analyze_product(self, asin: str, max_reviews: int = 50) -> Dict:
        """Complete product analysis workflow"""
        logger.info(f"Starting Amazon product analysis for ASIN: {asin}, max_reviews: {max_reviews}")
        
        results = {
            'asin': asin,
            'reviews': [],
            'summary': {},
            'success': False,
            'error': None
        }
        
        try:
            # Get cookies and login
            logger.info("Extracting browser cookies for Amazon")
            if not self.get_domain_cookies():
                logger.error("Failed to extract browser cookies")
                results['error'] = "Failed to extract browser cookies"
                return results
            
            logger.info("Attempting to login to Amazon")
            if not self.amazon_login():
                logger.error("Failed to login to Amazon")
                results['error'] = "Failed to login to Amazon"
                return results
            
            # Navigate to reviews page
            logger.info(f"Navigating to reviews page for ASIN: {asin}")
            if not self.get_product_review_page(asin):
                logger.error(f"Failed to access reviews page for ASIN: {asin}")
                results['error'] = f"Failed to access reviews for ASIN {asin}"
                return results
            
            # Scrape reviews
            logger.info(f"Starting review scraping (max: {max_reviews})")
            start_time = time.time()
            reviews = self.scrape_reviews(max_reviews)
            scrape_time = time.time() - start_time
            
            if not reviews:
                logger.warning(f"No reviews found for ASIN: {asin}")
                results['error'] = "No reviews found"
                return results
            
            logger.info(f"Successfully scraped {len(reviews)} reviews in {scrape_time:.2f} seconds")
            
            # Generate summary statistics
            total_reviews = len(reviews)
            valid_ratings = [r['rating'] for r in reviews if r['rating'] > 0]
            avg_rating = sum(valid_ratings) / len(valid_ratings) if valid_ratings else 0
            rating_distribution = {}
            
            for review in reviews:
                rating = int(review['rating']) if review['rating'] > 0 else 0
                rating_distribution[rating] = rating_distribution.get(rating, 0) + 1
            
            results['reviews'] = reviews
            results['summary'] = {
                'total_reviews': total_reviews,
                'average_rating': round(avg_rating, 2),
                'rating_distribution': rating_distribution
            }
            results['success'] = True
            
            logger.info(f"Analysis completed successfully: {total_reviews} reviews, avg rating: {avg_rating:.2f}")
            
        except Exception as e:
            logger.error(f"Amazon analysis failed for ASIN {asin}: {str(e)}")
            results['error'] = f"Analysis failed: {str(e)}"
        
        finally:
            logger.info("Cleaning up browser resources")
            self.cleanup()
        
        return results
    
    def cleanup(self):
        """Clean up resources"""
        if self.driver:
            try:
                self.driver.quit()
            except Exception:
                pass
            self.driver = None


