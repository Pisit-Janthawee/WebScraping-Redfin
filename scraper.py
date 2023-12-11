import numpy as np
import re
import pandas as pd
import time
from datetime import datetime
import json
from bs4 import BeautifulSoup
import requests
# Selenium
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

def redfin_scraper(county_information, filter, file_name, latitude_n=None, latitude_s=None, longitude_n=None, longitude_s=None):
    def _load_soup(driver, page=None, index=None):
        get_url = driver.current_url
        print(f'Loading content... {get_url}')
        start_loading_time = time.time()
        if page is not None:
            driver.get(f'{website_path}/page-{page}')

        driver, index = _find_element_scrolling(driver=driver, index=index)
        innerHTML = driver.execute_script('return document.body.innerHTML')
        time.sleep(1)
        loading_time = time.time() - start_loading_time
        print(f'Loaded! Time taken: {loading_time:.2f} seconds')
        soup = BeautifulSoup(innerHTML, "html.parser")
        return soup, driver, index

    def extract_numerical(string, as_integer=False):
        if string is None:
            return None
        
        matches = re.findall(r'[-+]?\d*\.?\d+(?:,\d{3})*(?=\s|\b|$)', string)
        numerical_value = matches[0].replace(',', '') if matches else None

        if numerical_value is not None:
            if as_integer:
                return int(float(numerical_value))
            else:
                return float(numerical_value)

        return None

    def _find_element_scrolling(driver, index=None):
        wait_time, max_index = 0.2, 40
        wait = WebDriverWait(driver, 5)
        index = index if index else 0
        while True:
            try:
                element = wait.until(EC.visibility_of_all_elements_located((By.XPATH, f'//*[@id="MapHomeCard_{index}"]')))
                driver.execute_script("arguments[0].scrollIntoView();", element[-1])
                time.sleep(wait_time)
                index += 1
                if index % max_index == 0:
                    break
            except Exception as e:
                print(f"An error occurred: {e}")
                break
        return driver, index

    def _get_json_content(script_tag):
        try:
            json_content = json.loads(script_tag.contents[0])
            return json_content
        except (KeyError, json.JSONDecodeError, IndexError):
            pass
        return None
    def _extract_offer_info(json_content):
        if isinstance(json_content, list):
            offers = json_content[1].get('offers', {})
            return offers.get('price'), offers.get('priceCurrency')
        elif isinstance(json_content, dict):
            offers = json_content.get('offers', {})
            return offers.get('price'), offers.get('priceCurrency')
        return None, None

    def _extract_address_fields(json_content):
        address_fields = ['streetAddress', 'addressLocality', 'addressRegion', 'postalCode', 'addressCountry']
        if isinstance(json_content, list) and len(json_content) >= 2:
            for item in json_content:
                if item.get('address'):
                    return [item['address'].get(field) for field in address_fields]
        elif isinstance(json_content, dict) and json_content.get('address'):
            return [json_content['address'].get(field) for field in address_fields]
        return [None] * 5

    def _extract_home_stats(home_stat):
        pattern_1 = r"(\d+\.\d+) (\w+ \(lot\))"
        pattern_2 = r"(\d{1,3}(?:,\d{3})*) sq ft"
        pattern_3 = r"\d+(\.\d+)? bed(s)?"
        pattern_4 = r"\d+(\.\d+)? bath(s)?"
        if home_stat:
            text = home_stat.text
            reg_size = re.search(pattern_1, text)
            reg_size_sqft = re.search(pattern_2, text)
            reg_bed = re.search(pattern_3, text)
            reg_bath = re.search(pattern_4, text)
    
            size = extract_numerical(string=reg_size.group(0) if reg_size else None, as_integer=True)
            size_unit = reg_size.group(2) if reg_size else None
            size_sqft = extract_numerical(string=reg_size_sqft.group(1) if reg_size_sqft else None,as_integer=False)
            bed = extract_numerical(string=reg_bed.group(0) if reg_bed else None, as_integer=True)
            bath = extract_numerical(string=reg_bath.group(0) if reg_bath else None,as_integer=True)
        return size_unit, bed, bath, size, size_sqft
    
    def _extract_and_convert_datetime(date_string):
        try:
            components = date_string.split(' ')[1:]
            # Remove any unexpected characters (e.g., '3D', 'WALKTHROUGH')
            components = [comp for comp in components if comp.isalpha()]
            if len(components) >= 3:
                month, day, year = components[:3]
                print(f'Date string components: month={month}, day={day}, year={year}')
                # Convert to datetime
                datetime_obj = datetime.strptime(f'{month} {day} {year}', '%b %d %Y')
                return datetime_obj
        except Exception as e:
            print(f"An error occurred during date conversion: {e}")
        return None
    def _extract_type(json_content):
        if isinstance(json_content, list):
            type1 = json_content[0].get('@type', {})
            type2 = json_content[1].get('@type', {})

            return type1, type2
        elif isinstance(json_content, dict):
            type1 = json_content.get('@type', {})
            return type1, None
        
    def _extract_number_of_rooms(json_content):
        if isinstance(json_content, list):
            num_of_room = json_content[0].get('numberOfRooms', {})
            return num_of_room
        elif isinstance(json_content, dict):
            num_of_room = json_content.get('numberOfRooms', {})
            return num_of_room

    base_url = "www.redfin.com"
    scraped_homes = []
    viewport = f'viewport={latitude_n}:{latitude_s}:{longitude_n}:{longitude_s}'
    website_path = None

    if filter.lower() == 'for sale':
        website_path = f"https://{base_url}/{county_information}"
        if latitude_n and latitude_s and longitude_n and longitude_s:
            website_path = f"https://{base_url}/{county_information}/filter/{viewport}"
    elif filter.lower() == 'for rent':
        website_path = f"https://{base_url}/{county_information}/apartments-for-rent"
        if latitude_n and latitude_s and longitude_n and longitude_s:
            website_path = f"https://{base_url}/{county_information}/apartments-for-rent/filter/{viewport}"
    elif re.match('sold-(1wk|1mo|3mo|6mo|1yr|2yr|3yr|5yr)', filter.lower()):
        print(f'Filter: {filter}')
        website_path = f"https://{base_url}/{county_information}/filter/include={filter}"
        if latitude_n and latitude_s and longitude_n and longitude_s:
            website_path = f"https://{base_url}/{county_information}/filter/include={filter},{viewport}"

    driver = webdriver.Chrome()
    driver.get(website_path)
    soup, driver, index = _load_soup(driver)
    n_home = int(soup.find('div', {'class': 'homes summary'}).text.split()[0].replace(',', ''))
    homecards = soup.find_all('div', {'data-rf-test-name': 'mapHomeCard'})
    len_home = len(homecards)
    n_page = int(np.ceil(n_home / len_home))  
    print('-'*30)
    print(f'Total page: {n_page}\nTotal home: {n_home}')
    print('-'*30)
    start_scraping_time = time.time()
    for page in tqdm(range(1, n_page + 1), desc='scraping...', total=n_page):
        print(f'Page: {page}')
        if page != 1:
            soup, driver, index = _load_soup(driver, page, index)
            homecards = soup.find_all('div', {'data-rf-test-name': 'mapHomeCard'})
            n_home = int(soup.find('div', {'class': 'homes summary'}).text.split()[0].replace(',', ''))
            homecards = soup.find_all('div', {'data-rf-test-name': 'mapHomeCard'})
            len_home = len(homecards)

        for home in homecards:
            href = home.find('a').get('href')
            home_url = f'https://{base_url}{href}'
            homecardV2, bottomV2 = home.find('div', {'class': 'homecardv2'}), home.find('div', {'class': 'bottomV2'})
            
            sold_datetime = homecardV2.find('div', {'class': 'topleft'}).text if homecardV2.find('div', {'class': 'topleft'}) else None
            if sold_datetime:
                home_sold_date = _extract_and_convert_datetime(sold_datetime)
            else:
                home_sold_date = None
            
            home_img, home_title = homecardV2.find('img').get('src') if homecardV2.find('img') else None, bottomV2.find('a').get('title') if bottomV2.find('a') else None
            home_price = bottomV2.find('span', {'class': 'homecardV2Price'}).text if bottomV2.find('span', {'class': 'homecardV2Price'}) else None
            if home_price:
                home_price = extract_numerical(string=home_price, as_integer=False)
            else:
                home_price = None
            # Json
            script_tag = bottomV2.find('script', {'type': 'application/ld+json'})
            json_content = _get_json_content(script_tag)
            address_street, address_locality, address_region, address_postal, address_country = _extract_address_fields(json_content)
            type1, type2 = _extract_type(json_content)
            number_of_rooms = _extract_number_of_rooms(json_content)
            price_usd, price_currency = _extract_offer_info(json_content)
            # Home Status
            home_stat = home.find('div', {'class': 'HomeStatsV2 font-size-small'})
            size_unit, home_bed, home_bath, home_size, home_sqft = _extract_home_stats(home_stat)

            result_dict = {
                'image': home_img,
                'title': home_title,
                'sold_date':home_sold_date,
                'json': json_content,
                'address_street': address_street,
                'address_locality': address_locality,
                'address_region': address_region,
                'address_postal': address_postal,
                'address_country': address_country,
                'type1': type1,
                'type2': type2,
                'number_of_rooms': number_of_rooms,
                'price': home_price,
                'price_usd': price_usd,
                'price_currency': price_currency,
                'url': home_url,
                'size': home_size,
                'size_unit': size_unit,
                'size_sqft': home_sqft,
                'bed': home_bed,
                'bath': home_bath,
                'remark': home.text,
            }

            scraped_homes.append(result_dict)

    scraping_time = time.time() - start_scraping_time
    print(f'Scraping completed! Time taken: {scraping_time:.2f} seconds ({scraping_time / 3600:.2f} hours)')

    driver.quit()
    pd.DataFrame(scraped_homes).to_csv(f'{file_name}.csv', index=False)
    return pd.DataFrame(scraped_homes)

if __name__ == "__main__":
    # Example Usage
    file_name = 'for_sale_az'
    county_information = "county/225/AZ/Santa-Cruz-County"
    filter = "For sale"
    latitude_n = 31.74205
    latitude_s = 31.29132
    longitude_n = -110.51157
    longitude_s = -111.30327

    redfin_scraper(county_information, 
                                   filter, 
                                   latitude_n, 
                                   latitude_s, 
                                   longitude_n, 
                                   longitude_s,
                                   file_name
                                   )