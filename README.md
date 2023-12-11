# WebScraping-Redfin
## 1. Web scraping
### RedFin

![webpage.png](https://github.com/Pisit-Janthawee/WebScraping-Redfin/blob/main/Images/webpage.png)

Website: https://www.redfin.com/county/225/AZ/Santa-Cruz-County/filter/property-type=land,min-lot-size=2-acre,max-lot-size=20-acre

## 2. Objective
Need to extract data from RedFin on a specific county in the USA. The county is Santa Cruz County, AZ.

### 2.1 Where I want to scrape?
![homecards.png](https://github.com/Pisit-Janthawee/WebScraping-Redfin/blob/main/Images/homecards.png)


I want to scrape only these cards but not directly to individual card

## 3. Expected outcome
spreadsheet or .csv file

## Work Flow
![work_flow_img](https://github.com/Pisit-Janthawee/Web-Scraping-DrugBank-Selenium/assets/133638243/e3c8dcb8-e9ba-49ee-a58d-c0ee43e311f7)

## 4. Tool
- Python
- BeautifulSoup
- Selenium 
- Requests
- Pandas

## 5. File Description

### Folder

1. **Images**
    - *Explanation*: Image of RedFin user-interface 

### 01-02 .ipynb Files

1. **init_craping.ipynb**
    - *Explanation*: This initial notebook is used for scraping the data and checking missing value after scraping 

### .py Files

1. scraper.py
    - *Explanation*: The file contains functions that define the workflow of the data processing pipeline. And export scraped data as CSV file
