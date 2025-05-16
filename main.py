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
from selenium.common.exceptions import TimeoutException, WebDriverException
import logging
from config import LINKEDIN_EMAIL, LINKEDIN_PASSWORD

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.FileHandler('scraper.log'), logging.StreamHandler()]
)

class LinkedInScraper:
    def __init__(self):
        opts = Options()
        for arg in [
            "--disable-blink-features=AutomationControlled",
            "--disable-extensions","--disable-gpu","--no-sandbox",
            "--disable-dev-shm-usage","--window-size=1920,1080",
            "--disable-webrtc","--disable-webgl","--disable-3d-apis",
            "--disable-bluetooth",
            "--disable-features=Bluetooth,AudioServiceOutOfProcess,AudioServiceSandbox,VizDisplayCompositor"
        ]:
            opts.add_argument(arg)
        opts.add_experimental_option("excludeSwitches", ["enable-logging","enable-automation"])
        service = Service(ChromeDriverManager().install(), log_path="NUL")
        self.driver = webdriver.Chrome(service=service, options=opts)
        self.logged_in = False

    def _safe_get(self, url):
        try:
            self.driver.get(url)
        except WebDriverException:
            try:
                self.driver.execute_script('window.stop();')
                self.driver.get(url)
            except WebDriverException as e:
                logging.error(f"Navigation error for {url}: {e}")
                return False
        return True

    def login(self):
        if self.logged_in:
            return True
        if not self._safe_get("https://www.linkedin.com/login"): return False
        try:
            WebDriverWait(self.driver,15).until(EC.presence_of_element_located((By.ID,"username")))
        except TimeoutException:
            logging.error("Login page load timed out")
            return False
        self.driver.find_element(By.ID,"username").send_keys(LINKEDIN_EMAIL)
        self.driver.find_element(By.ID,"password").send_keys(LINKEDIN_PASSWORD)
        btn = self.driver.find_element(By.XPATH,'//button[@type="submit"]')
        btn.click()
        try:
            WebDriverWait(self.driver,20).until(EC.url_contains("feed"))
        except TimeoutException:
            logging.error("Login did not complete in time")
            return False
        self.logged_in=True
        logging.info("Login successful")
        return True

    def search_and_get_company_url(self, company_name):
        if not self.logged_in and not self.login(): return None
        search_url = f"https://www.linkedin.com/search/results/companies/?keywords={company_name.replace(' ','%20')}"
        if not self._safe_get(search_url): return None
        try:
            WebDriverWait(self.driver,10).until(EC.presence_of_element_located((By.XPATH,'//a[contains(@href,"/company/")]')))
            link = self.driver.find_element(By.XPATH,'//a[contains(@href,"/company/")]').get_attribute("href")
            return link if link.startswith("http") else f"https://www.linkedin.com{link}"
        except TimeoutException:
            logging.error(f"No result for {company_name}")
            return None

    def scrape_company_data(self, url):
        if not self.logged_in and not self.login():
            return {"company_name":"N/A","industry":"N/A","url":url}
        if not self._safe_get(url):
            return {"company_name":"N/A","industry":"N/A","url":url}
        try:
            WebDriverWait(self.driver,10).until(EC.presence_of_element_located((By.CSS_SELECTOR,".org-top-card")))
        except TimeoutException:
            logging.error(f"Page load timeout: {url}")
            return {"company_name":"N/A","industry":"N/A","url":url}
        self.driver.execute_script("window.scrollTo(0,document.body.scrollHeight/3);")
        time.sleep(2)
        soup=BeautifulSoup(self.driver.page_source,'html.parser')
        return {"company_name":self._extract_company_name(soup),"industry":self._extract_industry(soup),"url":url}

    def _extract_company_name(self,soup):
        for sel in ["h1.top-card-layout__title","h1.org-top-card-summary__title","h1.t-24.t-black.t-normal"]:
            e=soup.select_one(sel)
            if e: return e.get_text(strip=True)
        return "N/A"

    def _extract_industry(self,soup):
        for sel in ["div.org-top-card-summary-info-list__info-item","div.industry","dd.ORG_ABOUT_INDUSTRY"]:
            e=soup.select_one(sel)
            if e: return e.get_text(strip=True)
        return "N/A"

    def close(self):
        self.driver.quit()


def main():
    os.makedirs("input",exist_ok=True)
    os.makedirs("output",exist_ok=True)
    path="input/company_names.xlsx"
    if not os.path.exists(path): logging.error(f"Missing {path}"); return
    df=pd.read_excel(path)
    if "Company Name" not in df.columns: logging.error("Missing 'Company Name'"); return
    scraper=LinkedInScraper()
    if not scraper.login(): scraper.close(); return
    results=[]
    for name in df["Company Name"]:
        if not isinstance(name,str) or not name.strip(): results.append({"input":name,"company_name":"N/A","industry":"N/A","url":"N/A"}); continue
        url=scraper.search_and_get_company_url(name)
        data=scraper.scrape_company_data(url) if url else {"company_name":"N/A","industry":"N/A","url":"N/A"}
        results.append({"input":name,**data})
        time.sleep(2)
    pd.DataFrame(results).to_excel("output/industry_data.xlsx",index=False)
    logging.info("Saved output/industry_data.xlsx")
    scraper.close()

if __name__=="__main__": main()
