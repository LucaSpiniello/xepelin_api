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

app = FastAPI()
email = "lucafigarispiniello@gmail.com"

@app.post("/scrape/")
async def scrape_blog(category: str, webhook_url: str):
    try:
        # data = scrape_blog_posts(category)
        data =[
            {
                "title": "title1",
                "time": "time1",
                "category": "category1",
                "author": "author1"
            },
            {
                "title": "title2",
                "time": "time2",
                "category": "category2",
                "author": "author2"
            }
        ]
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
    
    # find all divs with class BlogCategorySection_articleDesc3Col__6tL_x inside one level of articles_section
    articles = [div for div in articles_section.find_all('div', class_='ArticlesPagination_articleNormal__TZRAC', recursive=False)]
    
    # articles = articles_section.find_all('div', class_='BlogCategorySection_articleDesc3Col__6tL_x')
    
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


jsonExcel = {
  "type": "service_account",
  "project_id": "xepelin-425714",
  "private_key_id": "f3ce45bfc539c3a24126d7c67f434528e0fb41cd",
  "private_key": "-----BEGIN PRIVATE KEY-----\nMIIEvQIBADANBgkqhkiG9w0BAQEFAASCBKcwggSjAgEAAoIBAQCFxJ73r0gp5j6P\nwS5l1q645e1JVuMt7+WzySns5cs7tdkMFW2obEfSz2h9kExypEm572hnQTp6GpMa\nMPAGnzcZPNVaw2hyGB+Zhm8L9W/vMYhbt48jQ8pGv0Fg3ktk9jM2aAJ/YyN4Rn4g\nYsIuAw5qcI6CRkaG7IcVzfVF7tB2sgCAiwZaf0QeSnXppMNgB7mhO8AjobVHDUHr\nlkg3v7OLQWndl2tPCgE0xA6Wjk2c9TZZhkCU+s9Y/BJZiPYdkHH3kZjh2nj3sonT\nMnqbqBjt0qYR5DALiUlu88RREhyeX5FKGixUFVDpEex0xWiX8/3px5xnPZcUtrLQ\nk/FGun7TAgMBAAECggEAMBdv1XlZduLVpCYeMbO8jjHvnLnVpBrG2NueLJKy/c0T\nctIzYeVH7yTtGpNpwJ+K+AN35ANh7CsorrZgXOkZzIN/6wkswDQnDDF2M/Tx4KtM\nrDiyh8mj68pvzU0uCuauo8VB/J1eT6v8RVVsHVGw+Zhsy65LRc+8gxzQLOu+W6V/\nE3k6D9yI6Y8u+S4cOrSQhnJCda6uo0u7f4kyCh9ksV8vGrIQIEJUkayx9I/rJYep\n+R0j2dxPVGccHx7SyFgw1yiqdu5g7jgEnGjgWWz9YfSGVaiCq6iX9xXA8letMiTR\nmgisN+0bt6emFevmYVhOv0BbqYtCHfROwIxNYNczkQKBgQC6SbQAgwnq2YW0DOfe\nPlTdODkbNMIG5E1QJFNcFABIcwDhXZaiWrtK8+7NZ98G0DLumpKVsrOos2pFFbXr\nxekA5bZkqMfgwXioOwH4cAklBkTrImZPvTlI9thc6tcLahVHKQvhIuFZVXHQJ34t\ngJAkh7NFjNx5meSmZCy9J430QwKBgQC304osSYD0ho/IofvF2OulNaL7mCxpvsS3\nbIpcNIIMYUtrncFr0eXdYlgEA5bcN+hwUaQ0lA7Hw6UgEkkBNr0Aam3dx0tNLQHu\nzUmrX5GwPf9/E8WxBM/mZW7PZPaua4Mnv3NvWbc47YlJHrc1pS8ekmxFqlb+E7uD\nC6+l47lqMQKBgGoXx5fzCRbjQy5Dm1oLDbHfb0Z7SXU7WHyn84GhMngQZxPyhPN5\n0Oji+8GnwnDS6e7RwWHYIFGXvJITx0O7tvN33+R76zmpddn5oSmoRMz9QQrY0IPh\nNFrFmntwk4BArlWUnttdThHeg68UjtvDOFRVpFeb3YSzjHDm5EPl3waZAoGBAJm/\nxotwFvluKohmYwyBd+ZATEceadcwBZxcngSsrjDol4o08ffaIOXfQTpqPh2GbVS0\nFCEdzJbsXgnLAWCQhdf5LFcYPzUXdcxjy0AYuOOtlyqUQP7jxXcwU1QHYANWTOZL\nzKLPaN2mXvLXS+kEdbqeQQyrggMUQftDJPAc3ZGhAoGASCny2lfX6MyY0Zg+I0WZ\nHN93EvNzciqTyIJxGiNYLWgk3xNhUZj7gNtfUeHhJQp5SVKlLZHFjmGdcIw8Mjgl\nSFruBE3c2wdK0AuRv1+QsIOxRTUjTipIdrPfjJDiVUCMSA3OkYss7lN1zeaaNACk\nuvsmNfHjm9FbVgFekKRAvPI=\n-----END PRIVATE KEY-----\n",
  "client_email": "xepelin-177@xepelin-425714.iam.gserviceaccount.com",
  "client_id": "100549137237467015161",
  "auth_uri": "https://accounts.google.com/o/oauth2/auth",
  "token_uri": "https://oauth2.googleapis.com/token",
  "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
  "client_x509_cert_url": "https://www.googleapis.com/robot/v1/metadata/x509/xepelin-177%40xepelin-425714.iam.gserviceaccount.com",
  "universe_domain": "googleapis.com"
}

spreadsheet_url = "https://docs.google.com/spreadsheets/d/1puAnASoMA-5M1jO-kbaCVxGiYg9wu8Zvk98S3KTfET0"
worksheet_name = "info"

def save_to_google_sheets(data: List[Dict[str, str]]):

    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]


    creds = ServiceAccountCredentials.from_json_keyfile_dict(jsonExcel, scope)
    client = gspread.authorize(creds)

    print("Connected to Google Sheets")
    sheet = client.open_by_url(spreadsheet_url)

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
        "link": spreadsheet_url
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
