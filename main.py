import os
import time
import pandas as pd
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import logging
from config import LINKEDIN_EMAIL, LINKEDIN_PASSWORD

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('scraper.log'),
        logging.StreamHandler()
    ]
)

class LinkedInScraper:
    def __init__(self):
        self.driver = self._setup_driver()
        self.logged_in = False

    def close(self):
        if self.driver:
            self.driver.quit()
        
    def _setup_driver(self):
        """Configure Chrome WebDriver with optimized settings"""
        chrome_options = Options()
        
        # Recommended options for stability
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        chrome_options.add_argument("--disable-extensions")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--window-size=1920,1080")
        chrome_options.add_argument('--disable-webrtc')

        
        # Disable unnecessary features
        chrome_options.add_argument("--disable-webgl")
        chrome_options.add_argument("--disable-3d-apis")
        
        # For debugging (remove headless to see browser)
        # chrome_options.add_argument("--headless")
        
        driver = webdriver.Chrome(
            service=Service(ChromeDriverManager().install()),
            options=chrome_options
        )
        return driver

    def login(self):
        """Log in to LinkedIn with credentials from config.py"""
        if self.logged_in:
            return True
            
        self.driver.get("https://www.linkedin.com/login")
        time.sleep(2)
        
        try:
            # Wait for elements to be present
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.ID, "username"))
            ).send_keys(LINKEDIN_EMAIL)
            
            self.driver.find_element(By.ID, "password").send_keys(LINKEDIN_PASSWORD)
            self.driver.find_element(By.XPATH, "//button[@type='submit']").click()
            
            # Wait for login to complete
            WebDriverWait(self.driver, 10).until(
                lambda d: "feed" in d.current_url
            )
            self.logged_in = True
            logging.info("Login successful")
            return True
            
        except Exception as e:
            logging.error(f"Login failed: {str(e)}")
            return False

    def scrape_company_data(self, url):
        """Scrape company data with improved selectors"""
        if not self.logged_in and not self.login():
            return None
            
        try:
            self.driver.get(url)
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, ".org-top-card"))
            )
            
            # Scroll to load all elements
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight/3);")
            time.sleep(2)
            
            soup = BeautifulSoup(self.driver.page_source, 'html.parser')
            
            return {
                "company_name": self._extract_company_name(soup),
                "industry": self._extract_industry(soup),
                "url": url
            }
            
        except Exception as e:
            logging.error(f"Error scraping {url}: {str(e)}")
            return None

    def _extract_company_name(self, soup):
        """Extract company name with multiple fallback methods"""
        try:
            # Try multiple selectors for different LinkedIn layouts
            selectors = [
                "h1.top-card-layout__title",  # New layout
                "h1.org-top-card-summary__title",  # Old layout
                "h1.t-24.t-black.t-normal"  # Alternate layout
            ]
            
            for selector in selectors:
                name = soup.select_one(selector)
                if name:
                    return name.get_text(strip=True)
            return "N/A"
        except:
            return "N/A"

    def _extract_industry(self, soup):
        """Extract industry with multiple fallback methods"""
        try:
            # Try multiple selectors
            selectors = [
                "div.org-top-card-summary-info-list__info-item",  # New layout
                "div.industry",  # Old layout
                "dd.ORG_ABOUT_INDUSTRY"  # Alternate layout
            ]
            
            for selector in selectors:
                industry = soup.select_one(selector)
                if industry:
                    return industry.get_text(strip=True)
            return "N/A"
        except:
            return "N/A"
        
    def close(self):
        """Close the browser and clean up resources."""
        if self.driver:
            self.driver.quit()
            logging.info("Browser closed successfully.")

def main():
    # Setup directories
    os.makedirs("input", exist_ok=True)
    os.makedirs("output", exist_ok=True)
    
    # Initialize scraper
    scraper = LinkedInScraper()
    
    try:
        # Read input file
        input_path = "input/company_links.xlsx"
        if not os.path.exists(input_path):
            logging.error(f"Input file not found at {input_path}")
            return
            
        df = pd.read_excel(input_path)
        if "URL" not in df.columns:
            logging.error("Excel file must contain a 'URL' column")
            return
            
        # Process each URL
        results = []
        for url in df["URL"]:
            if not isinstance(url, str) or not url.startswith("http"):
                logging.warning(f"Skipping invalid URL: {url}")
                continue
                
            logging.info(f"Processing: {url}")
            data = scraper.scrape_company_data(url)
            results.append(data if data else {
                "company_name": "N/A",
                "industry": "N/A",
                "url": url
            })
            time.sleep(2)  # Be polite
            
        # Save results with only company_name, industry, and url
        output_df = pd.DataFrame(results)[["company_name", "industry", "url"]]
        output_path = "output/industry_data.xlsx"
        output_df.to_excel(output_path, index=False)
        logging.info(f"Success! Results saved to {output_path}")
        
    except Exception as e:
        logging.error(f"Fatal error: {str(e)}")
    finally:
        scraper.close()

if __name__ == "__main__":
    main()