
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
import selenium.webdriver.support.expected_conditions as EC
from selenium.webdriver.chrome.service import Service

import requests
from bs4 import BeautifulSoup
from bs4.element import Comment
import lxml
import time

import numpy as np
import pandas as pd
import re
from datetime import datetime, timedelta

import os
# Settings and paths for this program
chromedriver_path = r"C:\Users\andre\Documents\Python\chromedriver-win64\chromedriver.exe"
path_to_crawler_functions = r"C:\Users\andre\Documents\Python\Web_Crawler\Social_Media_Crawler_2024"
startpage = 'https://www.youtube.com/'
platform = 'YouTube'
dt_str_now = None
upper_datelimit = '2025-02-01'

file_path = r"C:\Users\andre\OneDrive\Desktop\SMP_Arzneimittelhersteller_2025"
source_file = file_path + '\Auswahl_Arzneimittelhersteller 2025_2025-02-05.xlsx'
branch_keywords = ['Pharma', 'Arznei', 'Medikament', 'Wirkstoff', 'Supplement', 'Forschung', 'Studie', 'Medizin', 'leistung', 'Krank', 'krank']
#branch_keywords = ['nutrition', 'vitamin', 'mineral', 'protein', 'supplement', 'diet', 'health', 'ernährung',
#                   'ergänzung', 'gesundheit', 'nährstoff', 'fitness', 'sport', 'leistung']
#file_path = r"C:\Users\andre\OneDrive\Desktop\Nahrungsergaenzungsmittel"
#source_file = "Liste_Nahrungsergänzungsmittel_2024_Auswahl.xlsx"
########################################################################################################################

def base_url(url):
    to_remove = ['/videos', '/about', '/featured', '/playlists']
    for e in to_remove:
        url = url.replace(e,'')
    if url[-1] == '/':
        url = url[:-1]
    return url

def open_and_check_page(link):
    try:
        driver.get(link)
        time.sleep(3)
    except:
        try:
            driver.get(link)
            time.sleep(5)
        except:
            return False
    status_code = requests.head(driver.current_url).status_code
    if status_code != 200:
        driver.get(link)
        time.sleep(5)
    status_code = requests.head(link).status_code
    if status_code != 200:
        return False
    return True

def open_description(driver):
    expand = driver.find_elements(By.CSS_SELECTOR, 'tp-yt-paper-button[id*="expand"]')
    if len(expand) > 1:
        for e in expand:
            try:
                e.click()
            except:
                pass
    elif len(expand) == 1:
        expand.click()

def get_likes(soup):
    likes = ''
    like_elem = soup.find('like-button-view-model')
    if like_elem:
        likes = extract_every_number((extract_text(like_elem)))
        if not like_elem or 'Mag' in str(likes):
            like_elem = soup.find('button', {'aria-label': lambda x: x and 'mag das Video' in x})
            if like_elem:
                like_text = extract_text(like_elem['aria-label'])
                if 'mag' in like_text.lower():
                    likes = extract_number(like_text)
    if likes == 'Mag ich':
        likes = ''
    return likes

def get_video_title(soup):
    title = ''
    title_elem = soup.find('h1',class_='style-scope ytd-watch-metadata')
    title = extract_text(title_elem)
    if len(str(title)) <= 4:
        titles = soup.find_all('h1')
        for t in titles:
            t_text = extract_text(t)
            if len(str(t_text)) >= 4:
                title = t_text
                break
    return title

def get_video_details(soup):
    date_str, date, views, desc = ['' for _ in range(4)]
    desc_elem = soup.find('div',{'id':'bottom-row'})
    full_desc = extract_text(desc_elem)
    if full_desc:
        desc = full_desc
        if 'Weniger anzeigen' in desc:
            desc = desc.split('Weniger anzeigen',1)[1].strip()
        if '...mehr' in desc:
            desc = desc.split('...mehr')[0].strip()
        desc_l = full_desc.split()
        for pos, e in enumerate(desc_l):
            if 'Aufruf' in e and views == '':
                views = extract_every_number(desc_l[pos-1])
            if '.201' in e or '.202' in e and date_str == '':
                date_opt = e.strip()
                try:
                    date_dt = datetime.strptime(date_opt, "%d.%m.%Y")
                    date = date_dt.strftime("%d.%m.%Y")
                except:
                    pass
            if views != '' and date != '':
                break
    if desc == '…':
        desc = ''
    return [date_str, date, views, desc]

def get_comment_number(driver,soup):
    comments = ''
    comments_elem = soup.find('h2',{'id':'count'})
    if comments_elem:
        comments_text = extract_text(comments_elem)
        if 'Kommentar' in comments_text or 'comment' in comments_text:
            comments = extract_number(comments_elem)
    else:
        for i in range(8):
            driver.execute_script("window.scrollBy(0,400)", "")
            time.sleep(3)
            soup = BeautifulSoup(driver.page_source, 'html.parser')
            comments_elem = soup.find('h2', {'id': 'count'})
            if comments_elem:
                comments_text = extract_text(comments_elem)
                if 'Kommentar' in comments_text or 'comment' in comments_text:
                    comments = extract_number(comments_elem)
                    if comments != '':
                        break
        if not comments and str(comments) != '0':
            try:
                comments_elem = driver.find_element(By.CLASS_NAME, 'style-scope ytd-comments-header-renderer').text
                if 'Kommentar' in comments:
                    comments = extract_number(comments_elem)
            except:
                pass
    return comments


def crawl_video(driver, link):
    date, title, views, likes, comments, desc = ['' for _ in range(6)]
    page_status = open_and_check_page(link)
    if not page_status:
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        pagetext = extract_text(soup)
        return [pagetext] + ['' for _ in range(6)]
    link = driver.current_url
    open_description(driver)
    driver.execute_script("window.scrollBy(0,1000)", "")
    time.sleep(2)
    soup = BeautifulSoup(driver.page_source,'html.parser')
    pagetext = extract_text(soup)
    likes = get_likes(soup)
    title = get_video_title(soup)
    date_str, date, views, desc = get_video_details(soup)
    if '0 Kommentare' in pagetext:
        comments = 0
    if not 'Kommentare sind deaktiviert' in pagetext and not str(comments) == '0':
        comments = get_comment_number(driver, soup)
    return [date, title, views, likes, comments, link, desc]

# A function to open the targetpage and scrape the profile stats
def scrapeProfile(url, comp_keywords):
    p_name, follower, total_posts, last_post, link, desc = ['' for _ in range(6)]
    url = base_url(url)
    driver.get(url + '/videos')
    time.sleep(3)
    soup = BeautifulSoup(driver.page_source, 'lxml')
    pagetext = extract_text(get_visible_text(Comment, soup))
    restricted = ['potenziell ungeeignet für', 'dass du alt genug', 'leider nicht verfügbar']
    if any(e in pagetext for e in restricted) or len(pagetext) <= 1000:
        return [p_name, follower, total_posts, last_post, url, pagetext]
#    p_name = extract_text(soup.find('ytd-channel-name',{'id':'channel-name'}))
    name_options = soup.find_all('h1')
    for n in name_options:
        n_text = extract_text(n)
        if any(c.lower() in n_text.lower() for c in comp_keywords):
            p_name = n_text
            if len(p_name):
                break
#    follower_elem = extract_text(soup.find('yt-formatted-string',{'id':'subscriber-count'}))
    span_text = [extract_text(e) for e in soup.find_all('span')]
    for s in span_text:
        if 'Abonnenten' in s and not follower:
            follower = extract_every_number(s)
        if 'Videos' in s and not total_posts:
            total_posts = extract_every_number(s)
        if follower and total_posts:
            break
    video_d = soup.find_all('div', {'id': 'details'})
    if len(video_d) >= 1:
        videolinks = ['https://www.youtube.com' + v.find('a', href=True)['href'] for v in video_d if v.find('a', href=True)]
        if len(videolinks) >= 1:
            link = videolinks[0]
    driver.get(url + '/about')
    time.sleep(3)
    if not '/about' in driver.current_url:
        try:
            desc_link = driver.find_element('xpath', "//*[contains(text(), 'weitere Links')]")
            desc_link.click()
            time.sleep(2)
        except:
            pass
    soup = BeautifulSoup(driver.page_source, 'lxml')
    desc_elem = soup.find('tp-yt-paper-dialog')
    if desc_elem:
        desc = get_visible_text(Comment, desc_elem).replace('Kanalinfo','').strip()
    # Get the date of the latest video
    if len(link) >= 10:
        result_row = crawl_video(driver, link)
        last_post = result_row[0]
    return [p_name, follower, total_posts, last_post, url, desc]
########################################################################################################################

# Profile crawler
if __name__ == '__main__':
    # Settings for profile scraping
    os.chdir(path_to_crawler_functions)
    from crawler_functions import *
    import credentials_file as cred
    os.chdir(file_path)
    df_source, col_list, comp_header, name_header, dt, dt_str = settings(source_file)

    # Start crawling
    data = []
    driver = start_browser(webdriver, Service, chromedriver_path, headless=False, muted=True)
    go_to_page(driver, startpage)

    # Iterating over the companies
    for n, row in df_source.iterrows():
        id = row['ID']
        if id < 0:  # If you want to skip some rows / if n < 0:
            continue
        company = extract_text(row[comp_header])
        comp_keywords = get_company_keywords(company, row, col_list)
        url = str(row[platform])
        if len(url) < 10:
            empty_row = [id, company, dt_str] + ['' for _ in range(6)]
            data.append(empty_row)
            continue

        scraped_data = scrapeProfile(url, comp_keywords)
        full_row = [id, company, dt_str] + scraped_data
        data.append(full_row)
        print(n, full_row[:-1])


    # DataFrame
    header = ['ID', 'company', 'date', 'profile_name', 'follower', 'all_posts', 'last_post', 'url', 'description']
    df_profiles = pd.DataFrame(data, columns=header)
    df_profiles.set_index('ID')

    # Export to Excel
#    dt_str_now = datetime.now().strftime("%Y-%m-%d_%H_%M_%S")
    dt_str_now = datetime.now().strftime("%Y-%m-%d")
    recent_filename = 'Profile_' + platform + '_' + dt_str_now + '.xlsx'
    df_profiles.to_excel(recent_filename)

    driver.quit()

########################################################################################################################
# Collect all the videolinks after scrolling
def getVideolinks(url):
    transform_url = ['/videos', '/about', '/featured', '/playlists']
    for e in transform_url:
        url = url.replace(e, '')
    if url[-1] == '/':
        url = url[:-1]
    try:
        driver.get(url + '/videos')
        time.sleep(4)
    except:
        return []
    driver.execute_script("window.scrollBy(0, 3000);")
    time.sleep(2)
    soup = BeautifulSoup(driver.page_source, 'lxml')
    pagetext = extract_text(get_visible_text(Comment, soup))
    if 'potenziell unangemessene Inhalte' in pagetext or 'existiert nicht' in pagetext or 'Automatisch von YouTube erstellt' in pagetext:
        return []
    scrolls = 0
    while True:
        old_dates = [f'vor {i} Jahren' for i in range(2, 11)]
        if any(date in pagetext for date in old_dates):
            break
        scrheight = driver.execute_script("return document.documentElement.scrollHeight")
        driver.execute_script("window.scrollBy(0, 3000);")
        scrolls += 1
        time.sleep(1)
        soup = BeautifulSoup(driver.page_source, 'lxml')
        pagetext = extract_text(get_visible_text(Comment, soup))
        newheight = driver.execute_script("return document.documentElement.scrollHeight")
        if scrheight == newheight or scrolls == 10:
            break
    videos = soup.find_all('div',{'id':'details'})
    videolinks = ['https://www.youtube.com' + v.find('a',href=True)['href'] for v in videos if v.find('a',href=True)]
#    print(f'Anzahl der Videolinks: {len(videolinks)}')
    return videolinks

def check_conditions(count, row, start_at=0):
    if count < start_at:      # If you want to skip some rows
        return False
    p_name = str(row['profile_name'])
    url = str(row['url'])
    last_post = str(row['last_post'])
    if len(p_name) <= 1 or p_name.lower() == 'nan' or p_name == 'None' or len(url) < 10:
        return False
    date_element = row['last_post']
    if not isinstance(date_element, datetime):
        last_datestr = extract_text(date_element)
        if not last_datestr or len(url) < 10 or len(last_post) <= 4 or 'Keine Beiträge' in last_post:
            print([id, url, 'no posts'])
            return False
        try:
            date_element = datetime.strptime(last_datestr, "%d.%m.%Y")
        except:
            return False
    if (lower_dt - timedelta(days=31)) < date_element:
        return True
    return False

def crawl_all_videos(dt_str, row, videolinks):
    id = str(row['ID'])
    p_name = str(row['profile_name'])
    data_per_company = []
    id_p = 0
    for link in videolinks:
        scraped_data = crawl_video(driver, link)
        if not scraped_data:
            continue
        post_date = scraped_data[0]
        try:
            post_dt = datetime.strptime(post_date, "%d.%m.%Y")
            if post_dt >= upper_dt:
                continue
            elif post_dt < lower_dt:
                return data_per_company
        except:
            pass
        id_p += 1
        full_row = [id, p_name, id_p, dt_str] + scraped_data
        data_per_company.append(full_row)
        print(full_row)
    return data_per_company

########################################################################################################################

# Post Crawler
if __name__ == '__main__':
    # Settings for the post crawler
    os.chdir(path_to_crawler_functions)
    from crawler_functions import *
    import credentials_file as cred
    os.chdir(file_path)
    file ='Profile_' + platform + '_2025'
    df_source, dt, dt_str, upper_dt, lower_dt = post_crawler_settings(file, platform, dt_str_now, upper_datelimit)

    # Driver and Browser setup
    all_data = []
    driver = start_browser(webdriver, Service, chromedriver_path, headless=False, muted=True)
    go_to_page(driver, startpage)

    # Iterate over the companies
    for count, row in df_source.iterrows():
        url = str(row['url'])
        go_crawl = check_conditions(count,row,start_at=82)
        if not go_crawl:
            continue

        videolinks = getVideolinks(url)
        if len(videolinks) == 0:
            print([count, str(row['ID']), 'Page not available'])
            continue

        data_per_company = crawl_all_videos(dt_str, row, videolinks)
        all_data += data_per_company

        # Create a DataFrame with all posts
        header1 = ['ID_A', 'profile_name', 'ID_P', 'Erhebung', 'Datum']
        header2 = ['Titel', 'Aufrufe', 'Likes', 'Kommentare', 'Link', 'Content']
        dfPosts = pd.DataFrame(all_data, columns=header1 + header2)

        # Export dfPosts to Excel (with the current time)
        dt_str_now = datetime.now().strftime("%Y-%m-%d_%H_%M_%S")
        file_name = 'Beiträge_' + platform + '_' + dt_str_now + '.xlsx'
        dfPosts.to_excel(file_name)


    driver.quit()
########################################################################################################################
print(all_data[-1])


'''        # Restart the driver after 3 companies
        if count % 3 == 0:
            driver.quit()
            time.sleep(5)
            driver = start_browser(webdriver, Service, chromedriver_path, headless=False, muted=True)
            go_to_page(driver, startpage)
            time.sleep(1)
'''

soup = BeautifulSoup(driver.page_source,'lxml')
elements = soup.find_all('p',class_='small')
distinct_companies = []
for e in elements:
    company = extract_text(e)
    if company not in distinct_companies:
        distinct_companies.append(company)

for e in distinct_companies:
    print(e)