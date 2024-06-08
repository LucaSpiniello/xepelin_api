from fastapi import FastAPI, HTTPException
import requests
from bs4 import BeautifulSoup
import gspread
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from typing import List, Dict
import os
from dotenv import load_dotenv

load_dotenv()

jsonExcel = {
    "type": os.getenv("TYPE"),
    "project_id": os.getenv("PROJECT_ID"),
    "private_key_id": os.getenv("PRIVATE_KEY_ID"),
    "private_key": os.getenv("PRIVATE_KEY"),
    "client_email": os.getenv("CLIENT_EMAIL"),
    "client_id": os.getenv("CLIENT_ID"),
    "auth_uri": os.getenv("AUTH_URI"),
    "token_uri": os.getenv("TOKEN_URI"),
    "auth_provider_x509_cert_url": os.getenv("AUTH_PROVIDER_X509_CERT_URL"),
    "client_x509_cert_url": os.getenv("CLIENT_X509_CERT_URL"),
    "universe_domain": os.getenv("UNIVERSE_DOMAIN"),
}

app = FastAPI()
email = "lucafigarispiniello@gmail.com"

@app.post("/scrape/")
async def scrape_blog(category: str, webhook_url: str):

    try:
        data = scrape_blog_posts(category)
        save_to_google_sheets(data)
        notify_webhook(webhook_url, email)
        
        return "Scraping completed successfully."

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

def scrape_blog_posts(category):
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service)
    
    driver.get("https://xepelin.com/blog")
    
    # Esperar hasta que la sección de categorías esté presente
    WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, 'div.BlogCategorySection_articlesGridDescending__hqGo4'))
    )
    
    html = driver.page_source
    soup = BeautifulSoup(html, 'html.parser')
    
    body = soup.find('body', class_='__className_5148cd').find('main')
    category_section = body.find('h2', text=category).parent
    
    div_with_link = category_section.find('div', class_='mt-9 grid md:mt-14')
    category_link = div_with_link.find('a')['href']
    print(category_link)
    all_blog_posts = []
    
    driver.get(category_link)
    
    while True:
        try:
            load_more_button = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, 'div.mt-12.grid.w-full.justify-center button'))
            )
            load_more_button.click()
            
            time.sleep(2)
            
        except Exception as e:

            break
    
    category_html = driver.page_source
    category_soup = BeautifulSoup(category_html, 'html.parser')
    
    articles_section = category_soup.find('div', class_='ArticlesPagination_articlesGridNormal__NuwYU')
    

    articles = [div for div in articles_section.find_all('div', class_='ArticlesPagination_articleNormal__TZRAC', recursive=False)]
    
    
    all_blog_posts = []

    for article in articles:
        article_box = article.find('div', class_='BlogArticle_box__JyD1X BlogArticle_boxSimple__KiPW6')
        link_tag = article_box.find('a')
        blog_post_url = link_tag['href']
        
        driver.get(blog_post_url)
                
        WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, 'body div')) 
                )
        
        post_html = driver.page_source
        post_soup = BeautifulSoup(post_html, 'html.parser')
        # find a main tag inside body
        post_body = post_soup.find('body').find('main')
        # find a h1 tag inside post_body
        post_title = post_body.find('h1').text
        # find a element with class Text_body__snVk8 text-base dark:text-text-disabled dark:[&_a]:text-tertiary-main text-grey-600
        post_time = post_body.find('div', class_='Text_body__snVk8 text-base dark:text-text-disabled dark:[&_a]:text-tertiary-main text-grey-600').text
        
        post_category = category
        # find the first div with class text-sm dark:text-text-disabled
        post_author = post_body.find('div', class_='text-sm dark:text-text-disabled').text
        
        dict_post = {
            "title": post_title,
            "time": post_time,
            "category": post_category,
            "author": post_author
        }
        all_blog_posts.append(dict_post)
        
    driver.quit()
    
    return all_blog_posts

worksheet_name = "info"

def save_to_google_sheets(data: List[Dict[str, str]]):

    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]


    creds = ServiceAccountCredentials.from_json_keyfile_dict(jsonExcel, scope)
    client = gspread.authorize(creds)

    print("Connected to Google Sheets")
    sheet = client.open_by_url(os.getenv("SPREADSHEET_URL"))

    worksheet = sheet.worksheet(worksheet_name)
    
    print("Connected to worksheet", worksheet)
    
    headers = ["Title", "Time", "Category", "Author"]
    worksheet.append_row(headers)

    for post in data:
        row = [post["title"], post["time"], post["category"], post["author"]]
        worksheet.append_row(row)

def notify_webhook(webhook_url: str, email: str):
    payload = {
        "email": email,
        "link": os.getenv("SPREADSHEET_URL")
    }
    headers = {
        'Content-Type': 'application/json'
    }
    try:
        response = requests.post(webhook_url, json=payload, headers=headers)
        response.raise_for_status()
        print(response.text)
        print("Webhook notification sent successfully.")
    except requests.exceptions.RequestException as e:
        print(f"Error sending webhook notification: {e}")
        
        
# comand curl -X POST "http://127.0.0.1:8001/scrape/?category=Pymes&webhook_url=https://hooks.zapier.com/hooks/catch/11217441/bfemddr"
