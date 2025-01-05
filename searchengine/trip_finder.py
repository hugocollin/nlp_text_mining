import requests
from bs4 import BeautifulSoup
import pandas as pd
import re
import time
import numpy as np
import random

class SearchEngine:
    
    '''
    This class is used to fetch the search results from the search engine.
    It uses the requests library to fetch the HTML content of the search results page.
    The BeautifulSoup library is used to parse the HTML content and extract the relevant information.
    The class has the following methods:
    1. get_session: This method creates a new session if it doesn't exist and returns the session object.
    2. fetcher: This method fetches the URL and returns the soup object.
    3. get_next_url: This method extracts the URL of the next page from the search results page.
    '''
    
    
    def __init__(self):
        # Initialize the base URL and session object
        self.base_url = "https://www.tripadvisor.fr"
        self.session = None
        self.cookies_list = [{'TADCID': '95got4bq91GmregYABQCrj-Ib21-TgWwDB4AzTFpg4J0pITsougolk1a7SaZZ7sYmkJu7KPOcqvM0xwqN1w93LttdFLFrqsYJ7w', 'TASameSite': '1', '__vt': 'M-4ijWLl6k7ybNR4ABQCjdMFtf3dS_auw5cMBDN7STJSRCH1nXChQ-WY5JlSnMR1uxIGdRWOqVv5tzhczv2Wi5nvq3oTCp7u5GoQG5I0EKASCq7B0TNG2mQVbmucgXvHPZ_YZpAWQnpr_ru3N91wLIMyxQ', 'TASID': 'A49FD32AED6A062F36B3FEFE390763C5', 'TAUnique': '%1%enc%3AdkjfOfw%2Ftm%2FlxUOBpOSBodxVTnjfkCfULJk9agUV4g3zZWtZ%2FjDJk605yvvNffQrNox8JbUSTxk%3D', 'datadome': 'M8Sgk8DaVoG_E_zlyrRsQ9uvHoNM93ifQS9R8PKSjGOo6Aqy6Zw5CJtbfX8jys20Iv2oN7NAJFAg6Nxh9nZYyZ4SJfCN_nRu~5g07XIDokW_jYeHO5ur5ekBFu_TMUFj'},
                             {'TADCID': 'pWOlWMQ9rTQrw4-yABQCrj-Ib21-TgWwDB4AzTFpg4J0p6pwdv5KtAcMeTPh9NOSBuZgFyPInX5N5d6kNu1rc2I3wVanAOg1bM8', 'TASameSite': '1', '__vt': 'sefjLUFgusLVzJNDABQCjdMFtf3dS_auw5cMBDN7STJSR9S-Pr6HRW4D5FmDCNJPWCEtzl8xQdfnRg4bzFOEma7R3urefPF7w7WLoAMayeWGhhXHp4zx6QgSImflSHxOSvIMhEkPhfu3H58HXPrBkr7QOZg', 'TASID': '75B03A8BF5E2467EA2B26845AF0077F0', 'TAUnique': '%1%enc%3ADcEvE9PUQEJeZRjQgnP077Hf6KJQVv679yrXSkrw1YpW2kYmdT%2BQRHxWboddzuEKNox8JbUSTxk%3D', 'datadome': 'g7cP3wnjQn88CA01ShYAzGIiwkPjcGHwla26TME5rP~S_SRPp8UuXByx~YEfrySGepZowaITWCLrRfj9Qw0PtrPEmjzdM2E0U2Sd~s_hRR5C6C0nU5tluhbf4jjw4sRD'}]
        self.soup = None
        self.cookies = None
        self.rank = 0
    def __str__(self):
        print(f"SearchEngine(base_url='{self.base_url}')")
        print(f"Session: {self.session}")
        # print headers
        print(f"cookies: {self.cookies}")
        
        
        print(f"Soup: {self.soup}")
        return ""
        
    
    
    def get_session(self):
        
        # Create a new session if it doesn't exist
        if not self.session:
            print("Creating a new session...")
            self.session = requests.Session()
            self.cookies = np.random.choice(self.cookies_list)  
            for name, value in self.cookies.items():
                self.session.cookies.set(name, value, domain='.tripadvisor.fr')
        else:
            print("Session already exists")
    
    
    def run(self, url):
        # Fetch the URL and return the soup object
        headers = {
            'User-Agent': "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
            'Accept': 'text/html',
            'Accept-Language': 'fr-FR,fr;q=0.9',
            'Referer': 'https://www.google.com/',
            'Origin': 'https://www.tripadvisor.fr',
            
        }
        self.get_session()
        response = self.session.get(url, headers=headers)
        
        if response.status_code == 200:
            self.soup = BeautifulSoup(response.content, 'html.parser')
            return None
        elif response.status_code == 404:
            print("404 Not Found")
            return None
        elif response.status_code == 403:
            print("403 Forbidden")
            time.sleep(150)
            self.rank += 1
            if self.rank < 10:
                return self.run(url)
            else:
                self.rank = 0
                return None
        elif response.status_code == 503:
            print("503 Service Unavailable")
            return None
        elif response.status_code == 500:
            print("500 Internal Server Error")
            return None
        elif response.status_code == 504:
            print("504 Gateway Timeout")
            return None
        elif response.status_code == 429:
            time.sleep(60)
            print("429 Too Many Requests")
            self.rank += 1
            if self.rank < 10:
                return self.run(url)
            else:
                self.rank = 0
                return None
        else:
            print("Unknown error")
            return None
        
    def get_next_url(self):
        # Get the next page URL
        # Locate the pagination container
        pagination = self.soup.find_all("div", class_="mkNRT j")
        if not pagination:
            return None
        
        # Find all page number links and buttons
        attrs_possible = [
            {"aria-label" : "Page suivante"},
            {"data-smoke-attr" : "pagination-next-arrow" },
            {"aria-label" : "Next page"},
        ]
        for page in pagination:
            page_elements = page.find("a", attrs=attrs_possible[0]) or page.find("button", attrs=attrs_possible[1]) or page.find("a", attrs=attrs_possible[2])
            if page_elements:
                print("Next page found", page_elements.get("href"))
                return page_elements.get("href")
            else:
                print("No next page found")
                return None

        

class RestaurantFinder(SearchEngine):
    
    '''
    This class is used to fetch the search results of restaurants from the search engine.
    It inherits the SearchEngine class and has the following methods:
    1. get_restaurant_info: This method extracts the restaurant information from the search results page.
    '''

    
    def __init__(self):
        # Initialize the base URL and session object
        super().__init__()
        self.all_restaurants = []
        self.current_url = None
        self.current_page = 1
        
        
    def find_restaurants(self):
        """
        Extract restaurant names and URLs from TripAdvisor search results page
        
        Args:
            soup: BeautifulSoup object of the page HTML
            
        Returns:
            list: List of dicts containing restaurant info (name, url)
        """
        restaurants = []
        
        # Find the main container with search results
        search_results = self.soup.find('div', {'data-automation': 'searchResults', 'class': 'Ikpld f e'})
        
        if search_results:
            # Find all restaurant cards
            restaurant_cards = search_results.find_all('div', class_='vIjFZ Gi o VOEhq')
            
            for card in restaurant_cards:
                # Find link element
                card_embedded = card.find('div', class_='XIWnB z y')
                link = card_embedded.find('a')
                if link:
                    name = link.text
                    name =  re.sub(r'^\d+\.\s*', '', name).strip()
                    url = 'https://www.tripadvisor.fr' + link['href'] if link['href'].startswith('/') else link['href']
                    
                    restaurants.append({
                        'name': name,
                        'url': url
                    })
        
        return restaurants
            
    
    def scrape_all_restaurants(self,start_url = "https://www.tripadvisor.fr/Restaurants-g187265-Lyon_Rhone_Auvergne_Rhone_Alpes.html" , max_pages=10):
        """
        Scrape restaurant information from multiple pages
        
        Args:
            start_url (str): Starting URL to scrape
            session (requests.Session, optional): Session object for requests
            max_pages (int, optional): Maximum number of pages to scrape
            
        Returns:
            list: Combined list of restaurant dictionaries
        """
        self.current_url = start_url
        self.current_page = 1
    
        while self.current_url:

            # Break if max_pages limit reached
            if max_pages and self.current_page > max_pages:
                break
                
            print(f"Scraping page {self.current_page}...")
            print(f"Current URL: {self.current_url}")
            # Get soup for current page
            self.run(self.current_url)

            if not self.soup:
                print(f"Failed to get page {self.current_page}")
                break
                
            # Extract restaurants from current page
            page_restaurants = self.find_restaurants()
            self.all_restaurants.extend(page_restaurants)
            
            # Get next page URL
            next_page_href = self.get_next_url()
            if not next_page_href:
                print("scrapping end")
                break
            else:
                print(f"Next page: {next_page_href}")
                # Update URL for next iteration
                self.current_url = self.base_url + next_page_href if next_page_href.startswith('/') else self.base_url + '/' + next_page_href
                self.current_page += 1
                print(f"Next page: {self.current_url}")
                # Add delay between requests
                time.sleep(random.uniform(1, 3))
        
        print(f"Found {len(self.all_restaurants)} restaurants total")
        return self.all_restaurants
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
class restaurant_info_extractor(SearchEngine):
 
 
    '''
    This class is used to extract the restaurant information from the restaurant page.
    It inherits the RestaurantFinder class and has the following methods:
    1. michelin_star_finder: This method finds the number of Michelin stars of the restaurant.
    2. get_restaurant_info: This method extracts the restaurant information from the restaurant page.
    '''
    
    def __init__(self):
        # Initialize the base URL and session object
        super().__init__()
        self.restaurant_info = {}
        self.reviews = []
        
            
    # Trouver les étoiles Michelin renvoie le nombre d'étoiles du restaurant (0, 1, 2 ou 3)
    def michelin_star_finder(self,soup): 
        if soup.find('img', src="https://static.tacdn.com/img2/restaurant-awards/michelin/1-Star.svg"):
            return 1
        elif soup.find('img', src="https://static.tacdn.com/img2/restaurant-awards/michelin/2-Stars.svg"):
            return 2
        elif soup.find('img', src="https://static.tacdn.com/img2/restaurant-awards/michelin/3-Stars.svg"):
            return 3
        else:
            return 0
    
    def get_restaurant_info(self, soup):
        # Notes et avis
        notes_avis_section = soup.find('div', class_='QSyom f e Q3 _Z')
        notes = {}
        if notes_avis_section:
            global_note_tag = notes_avis_section.find('span', class_='biGQs _P fiohW uuBRH')
            global_note = global_note_tag.text if global_note_tag else 'N/A'

            other_notes_tags = notes_avis_section.find('div', class_='khxWm f e Q3')
            other_notes_div = other_notes_tags.find_all('div', class_='YwaWb u f')
            if other_notes_div:
                cuisine_note = re.search(r'\d,\d', other_notes_div[0].text).group()
                service_note = re.search(r'\d,\d', other_notes_div[1].text).group()
                quality_price_note = re.search(r'\d,\d', other_notes_div[2].text).group()
                ambiance_note = re.search(r'\d,\d', other_notes_div[3].text).group()
                
            else:
                cuisine_note = service_note = quality_price_note = ambiance_note = 'N/A'
        else:
            global_note = cuisine_note = service_note = quality_price_note = ambiance_note = 'N/A'
        
        notes = {
            'CUISINE': cuisine_note,
            'SERVICE': service_note,
            'RAPPORT QUALITÉ-PRIX': quality_price_note,
            'AMBIANCE': ambiance_note
        }

        # Détails
        details_section = soup.find('div', class_='MTwbb f e')
        if details_section:
            details = {}
            detail_items = details_section.find_all('div', class_='biGQs _P pZUbB alXOW oCpZu GzNcM nvOhm UTQMg ZTpaU W hmDzD')
            labels = details_section.find_all('div', class_='Wf')
            for label, value in zip(labels, detail_items):
                key = label.find('div', class_='biGQs _P ncFvv NaqPn').text.strip()
                val = value.text.strip()
                details[key.upper()] = val
        else:
            details = {'Fourchette de prix': 'N/A', 'Cuisines': 'N/A', 'Régimes spéciaux': 'N/A'}

        # Emplacement et coordonnées
        location_section = soup.find('div', class_='Zb w')
        if location_section:
            address_tag = location_section.find('a', href=True)
            address = address_tag.text.strip() if address_tag else 'N/A'

            email_tag = soup.find('a', href=lambda href: href and href.startswith('mailto:'))
            email = email_tag['href'].split(':')[1] if email_tag else 'N/A'

            phone_tag = location_section.find('a', href=lambda x: x and x.startswith('tel:'))
            phone = phone_tag.text.strip() if phone_tag else 'N/A'
        else:
            address = email = phone = 'N/A'

        # Organiser les informations dans un dictionnaire
        restaurant_info = {
            'Notes et avis': {
                'NOTE GLOBALE': global_note,
                **notes
            },
            'Détails': details,
            'Emplacement et coordonnées': {
                'ADRESSE': address,
                'EMAIL': email,
                'TELEPHONE': phone
            }
        }
        stars = self.michelin_star_finder(soup)
        restaurant_info['Détails']['ÉTOILES MICHELIN'] = stars
        
        return restaurant_info
    
    def extract_reviews(self, soup):
        
        reviews = soup.find_all("div", class_="_c")
        for review in reviews:
            try:
                user = review.find("a", class_="BMQDV _F Gv wSSLS SwZTJ FGwzt ukgoS")
                user_profil = user['href'].replace('/Profile/', '') if user and 'href' in user.attrs else 'N/A'
                title = review.find("div", class_="biGQs _P fiohW qWPrE ncFvv fOtGX").text.strip()
                avis = review.find_all("span", class_="JguWG")
                date_review = review.find("div", class_="biGQs _P pZUbB ncFvv osNWb").text.replace('Rédigé le ', '').strip()
                type_visits = review.find("span", class_="DlAxN")
                if type_visits is not None:
                    type_visits = type_visits.text
                else:
                    type_visits = "No information"
                 # Extract rating
                rating_tag = review.find("div", class_="OSBmi J k")
                rating_title = rating_tag.find("title").text.strip() if rating_tag and rating_tag.find("title") else 'N/A'
                rating = float(re.search(r'\d,\d', rating_title).group().replace(',', '.')) if re.search(r'\d,\d', rating_title) else None
                
                contrib_container = review.find("div", class_="vYLts")
                num_contributions_tag = contrib_container.find("span", class_="b") if contrib_container else None
                num_contributions = int(num_contributions_tag.text.strip()) if num_contributions_tag else 0
                
                
                
                self.reviews.append({
                    'user': user.text.strip() if user else 'N/A',
                    'user_profile': user_profil if user_profil else 'N/A',
                    'date_review': date_review if date_review else 'N/A',
                    'title': title if title else 'N/A',
                    'rating': rating,
                    'type_visit': type_visits,
                    'num_contributions': num_contributions, 
                    'review': avis[0].text if avis else 'N/A',
                    
                })
            except AttributeError:
                continue
            
    
    
    def scrape_restaurant(self, url):
        self.run(url)
        if not self.soup:
            print(f"Failed to get restaurant page {url}")
            return None
        self.restaurant_info = self.get_restaurant_info(self.soup)
        next_page_href = self.get_next_url()
        while next_page_href:
            self.extract_reviews(self.soup)
            self.run(self.base_url + next_page_href)
            next_page_href = self.get_next_url()
    
        return self.restaurant_info, self.reviews
    
    
    
    
    
    
    
    def to_dataframe(self):
        df_reviews = pd.DataFrame(self.reviews)
        df_avis = pd.DataFrame(self.restaurant_info['Notes et avis'], index=[0])
        df_details = pd.DataFrame(self.restaurant_info['Détails'], index=[0])
        df_location = pd.DataFrame(self.restaurant_info['Emplacement et coordonnées'], index=[0])   
        return df_avis, df_details, df_location, df_reviews
    
    def to_csv(self):
        df_avis, df_details, df_location, df_reviews = self.to_dataframe()
        df_avis.to_csv('avis.csv', index=False)
        df_details.to_csv('details.csv', index=False)
        df_location.to_csv('location.csv', index=False)
        df_reviews.to_csv('reviews.csv', index=False)
        
        
        
    
    
    
    
    
    
    
    
    
    
