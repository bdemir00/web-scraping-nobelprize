import pandas as pd
import re
import requests
from bs4 import BeautifulSoup

# Functions
# Function to remove footnotes
def remove_footnotes(text):
    # Regex pattern to match footnotes
    pattern = re.compile(r'\[[a-zA-Z]\]')
    return pattern.sub('', text)

# Function to process the table
def process_table(table):
    # Rename columnns for readability
    table.rename(columns={'Economics (The Sveriges Riksbank Prize)[13][a]':'Economics'}, inplace=True)
    table = table.melt('Year', value_name='Name', var_name='Prize')

    # Handle empty cells & remove irrelevant data
    table.dropna(subset=['Name'], inplace=True)
    table.drop(table.tail(1).index, inplace=True)
    table = table[~table['Name'].isin(['—', 'Cancelled due to World War II', 'Physics', 'Chemistry', 'Literature', 'Economics', 'Peace'])]

    # Remove footnotes
    table = table.map(remove_footnotes)

    # Seperate rows with multiple names
    table['Name'] = table['Name'].str.split('; ')
    table = table.explode('Name').reset_index(drop=True)

    return table

# Function to scrape birthday
def get_bdate(soup):
    try:
        bdate = soup.find('span', class_='bday').get_text()
    except AttributeError:
        bdate = ''
    return bdate

def get_url(soup, name):
        a_tag = soup.find('a', href=True, string=name)
        if a_tag:
            url = a_tag['href']
            # Construct the full URL if needed
            full_url = 'https://en.wikipedia.org' + url
            return full_url
        else:
            return ''
        

# Function to find zodiac sign
def zodiac_sign(date):
    if not date:
        return ''
    
    try:
        day = int(date[3:])
        month = date[:2]
    except ValueError:
        return ''
    
    zodiac_dates = [
        ('01', 20, 'Capricorn', 'Aquarius'),
        ('02', 19, 'Aquarius', 'Pisces'),
        ('03', 21, 'Pisces', 'Aries'),
        ('04', 20, 'Aries', 'Taurus'),
        ('05', 21, 'Taurus', 'Gemini'),
        ('06', 21, 'Gemini', 'Cancer'),
        ('07', 23, 'Cancer', 'Leo'),
        ('08', 23, 'Leo', 'Virgo'),
        ('09', 23, 'Virgo', 'Libra'),
        ('10', 23, 'Libra', 'Scorpio'),
        ('11', 22, 'Scorpio', 'Sagittarius'),
        ('12', 22, 'Sagittarius', 'Capricorn')
    ]
    
    for m, d, sign1, sign2 in zodiac_dates:
        if month == m:
            return sign1 if day < d else sign2
    
    return ''

# Function to get all of the zodiac signs from individual wiki pages
def get_signs(table):
    signs = []
    table_url = 'https://en.wikipedia.org/wiki/List_of_Nobel_laureates'
    table_page = requests.get(table_url)
    soup = BeautifulSoup(table_page.content, 'html.parser' )
    for index, row in table.iterrows():
        name = row['Name']
        url = get_url(soup, name)
        print(url)
        if url:
            local_page = requests.get(url)
            local_soup = BeautifulSoup(local_page.content, 'html.parser')
            bdate = get_bdate(local_soup)
            bday = bdate[5:]
            zodiac = zodiac_sign(bday)
            signs.append(zodiac)
        else:
            signs.append('')
    return signs

if __name__ == "__main__":
    # Scrape table from wikipedia
    wikiurl = 'https://en.wikipedia.org/wiki/List_of_Nobel_laureates'
    tables = pd.read_html((wikiurl))

    # Adjust dataframe
    nobel_table = process_table(tables[0])

    # Get all signs fron individual pages
    signs = get_signs(nobel_table)

    # Insert column to dataframe
    nobel_table.insert(3, "Zodiac Sign", signs)

    # Remove rows with empty sign
    # There are organisations
    # Therefore the url doesn't contain the desired data.
    #nobel_table.drop('', inplace=True)

    # Export dataset as .csv file
    nobel_table.to_csv('nobel.csv', sep=',', encoding='utf-8', index=False)
