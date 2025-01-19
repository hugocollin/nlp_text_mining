import requests
from bs4 import BeautifulSoup
import pandas as pd
import re
import time
import numpy as np
import platform
import tqdm
class SearchEngine:
    
    '''
    This class is used to fetch the search results from the search engine.
    It uses the requests library to fetch the HTML content of the search results page.
    The BeautifulSoup library is used to parse the HTML content and extract the relevant information.
    '''
    
    
    def __init__(self):
        # Initialize the base URL and session object
        self.base_url = "https://www.tripadvisor.fr"
        self.session = None
        self.cookies_list = [{'TADCID': '95got4bq91GmregYABQCrj-Ib21-TgWwDB4AzTFpg4J0pITsougolk1a7SaZZ7sYmkJu7KPOcqvM0xwqN1w93LttdFLFrqsYJ7w', 'TASameSite': '1', '__vt': 'M-4ijWLl6k7ybNR4ABQCjdMFtf3dS_auw5cMBDN7STJSRCH1nXChQ-WY5JlSnMR1uxIGdRWOqVv5tzhczv2Wi5nvq3oTCp7u5GoQG5I0EKASCq7B0TNG2mQVbmucgXvHPZ_YZpAWQnpr_ru3N91wLIMyxQ', 'TASID': 'A49FD32AED6A062F36B3FEFE390763C5', 'TAUnique': '%1%enc%3AdkjfOfw%2Ftm%2FlxUOBpOSBodxVTnjfkCfULJk9agUV4g3zZWtZ%2FjDJk605yvvNffQrNox8JbUSTxk%3D', 'datadome': 'M8Sgk8DaVoG_E_zlyrRsQ9uvHoNM93ifQS9R8PKSjGOo6Aqy6Zw5CJtbfX8jys20Iv2oN7NAJFAg6Nxh9nZYyZ4SJfCN_nRu~5g07XIDokW_jYeHO5ur5ekBFu_TMUFj'},
                             {'TADCID': '95got4bq91GmregYABQCrj-Ib21-TgWwDB4AzTFpg4J0pITsougolk1a7SaZZ7sYmkJu7KPOcqvM0xwqN1w93LttdFLFrqsYJ7w', 'TASameSite': '1', '__vt': 'M-4ijWLl6k7ybNR4ABQCjdMFtf3dS_auw5cMBDN7STJSRCH1nXChQ-WY5JlSnMR1uxIGdRWOqVv5tzhczv2Wi5nvq3oTCp7u5GoQG5I0EKASCq7B0TNG2mQVbmucgXvHPZ_YZpAWQnpr_ru3N91wLIMyxQ', 'TASID': 'A49FD32AED6A062F36B3FEFE390763C5', 'TAUnique': '%1%enc%3AdkjfOfw%2Ftm%2FlxUOBpOSBodxVTnjfkCfULJk9agUV4g3zZWtZ%2FjDJk605yvvNffQrNox8JbUSTxk%3D', 'datadome': 'M8Sgk8DaVoG_E_zlyrRsQ9uvHoNM93ifQS9R8PKSjGOo6Aqy6Zw5CJtbfX8jys20Iv2oN7NAJFAg6Nxh9nZYyZ4SJfCN_nRu~5g07XIDokW_jYeHO5ur5ekBFu_TMUFj'}]
        self.soup = None
        self.cookies = None
        self.rank = 0
        self.url = None
        
############### __methods__ #######################    

    def __str__(self):
        print(f"SearchEngine(base_url='{self.base_url}')")
        print(f"Session: {self.session}")
        print(f"cookies: {self.cookies}")
        print(f"Soup: {self.soup}")
        return ""

############### __methods__ #######################       

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
    
############### __methods__ #######################    

    def get_os_user_agent(self):
        # Get the user agent based on the OS
        os = platform.system()
        if os == "Windows":
            return "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:127.0) Gecko/20100101 Firefox/109.0"
        elif os == "Linux":
            return "Mozilla/5.0 (X11; Linux x86_64; rv:109.0) Gecko/20100101 Firefox/109.0"
        else:
            return "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/"
    
############### __methods__ #######################    
 
    def run(self, url, reviews=None):
        
        if reviews:
            user_agent = self.get_os_user_agent()
        else:
            user_agent = "Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) SamsungBrower/27.0 Chrome/125.0.0.0 Mobile Safari/537.36"
        self.url = url
        headers = {
            
            #'User-Agent': "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Gecko/20100101 Firefox/109.0", # AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36
            # 'User-Agent': "Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) SamsungBrower/27.0 Chrome/125.0.0.0 Mobile Safari/537.36",
            'User-Agent':  user_agent,
            'Accept': 'text/html, application/xhtml+xml, application/xml;q=0.9, image/avif, image/webp, image/apng, image/*,*/*;q=0.8',
            'Accept-Language': 'fr-FR,fr;q=0.9',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'TE': 'Trailers',
            "DNT": "1",  # Do Not Track
            "Origin": "https://www.tripadvisor.fr/",
            'Referer' : url ,

        }
        self.get_session()
        self.session.headers.update(headers)
        time.sleep(1)
        # print time to check the time of the request
        print(time.ctime())
        response = self.session.get(url, headers=headers, timeout=(6, 36))
        time.sleep(1)
        if response.status_code == 200:
            self.soup = BeautifulSoup(response.content, 'html.parser')
            return None
        elif response.status_code == 404:
            print("404 Not Found")
            return None
        elif response.status_code == 403:
            print("403 Forbidden")
            print(response.text)
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
            if self.rank < 5:
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
                return page_elements.get("href")
            else:
                print("No next page found")
                return None

############### __class__ #######################          

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

############### __methods__ #######################          
        
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

############### __methods__ #######################              
    
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
            time.sleep(5)
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
                # Update URL for next iteration
                self.current_url = self.base_url + next_page_href if next_page_href.startswith('/') else self.base_url + '/' + next_page_href
                self.current_page += 1
                print(f"Next page: {self.current_url}")
                # Add delay between requests
                time.sleep(np.random.uniform(2, 6))
        
        print(f"Found {len(self.all_restaurants)} restaurants total")
        return self.all_restaurants
    def to_dataframe(self):
        return pd.DataFrame(self.all_restaurants)
    
############### __methods__ #######################    

    def to_csv(self):
        df = self.to_dataframe()
        df.to_csv('Data/liste_restaurants.csv', index=False)
        
############### __class__ #######################

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
   
        self.rank_info = 0
        self.review_number = 0
    
############### __methods__ #######################       
            
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
    
############### __methods__ #######################    
    def extract_note(self,text):
                        match = re.search(r'\d,\d', text)
                        return match.group() if match else None
                    
    def get_restaurant_info(self, soup):
        # Notes et avis
        notes_avis_section = soup.find('div', class_='QSyom f e Q3 _Z')
        if not notes_avis_section:
            print("No notes found")
            if self.rank_info < 2:
                print("No data found")
                self.rank_info += 1
                # print tqdm progress bar for waiting 5 seconds
                for i in tqdm.tqdm(range(5)):
                    time.sleep(1)
                print(self.session.cookies)
                self.session.cookies.clear()
                self.session = None
                return self.scrape_info(self.url)
            
            if self.rank_info == 2:
                self.rank_info = 0
                with open('restaurant_info.html', 'w', encoding='utf-8') as f:
                    f.write(str(soup))
                print("No data found correctly")
                
        notes = {}
        global_note = cuisine_note = service_note = quality_price_note = ambiance_note = None

        if notes_avis_section:
            
            global_note_tag = notes_avis_section.find('span', class_='biGQs _P fiohW uuBRH')
            global_note = global_note_tag.text if global_note_tag else None
            print(global_note)


            other_notes_tags = notes_avis_section.find('div', class_='khxWm f e Q3')
            if other_notes_tags:
                other_notes_div = other_notes_tags.find_all('div', class_='YwaWb u f')
                if other_notes_div and len(other_notes_div) == 4:
                    
                
                    cuisine_note = self.extract_note(other_notes_div[0].text)
                    service_note = self.extract_note(other_notes_div[1].text)
                    quality_price_note = self.extract_note(other_notes_div[2].text)
                    ambiance_note = self.extract_note(other_notes_div[3].text)
                
            
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
            details = {'Fourchette de prix': None , 'Cuisines': None, 'Régimes spéciaux': None}

        # Emplacement et coordonnées
        location_section = soup.find('div', class_='Zb w')
        if location_section:
            address_tag = location_section.find('a', href=True)
            address = address_tag.text.strip() if address_tag else None
            # get href attribute of the <a> tag
            google_map = address_tag['href'] if address_tag else None
            # extract latitude and longitude from the href attribute
            def extract_lat_lon(href):
                match = re.search(r'@(-?\d+\.\d+),(-?\d+\.\d+)', href)
                return match.groups() if match else (None, None)
            lat, lon = extract_lat_lon(google_map)
            
            email_tag = soup.find('a', href=lambda href: href and href.startswith('mailto:'))
            email = email_tag['href'].split(':')[1] if email_tag else None

            phone_tag = location_section.find('a', href=lambda x: x and x.startswith('tel:'))
            phone_numer = phone_tag['href'].split(':')[1] if phone_tag else None
            # phone = phone_tag.text.strip() if phone_tag else 'N/A'
        else:
            address = email = phone_numer = None

        # Organiser les informations dans un dictionnaire
        restaurant_info = {
            'Notes et avis': {
                'NOTE GLOBALE': global_note,
                **notes
            },
            'Détails': details,
            'Emplacement et coordonnées': {
                'ADRESSE': address,
                'GOOGLE MAP': google_map,
                'LATITUDE': lat,
                'LONGITUDE': lon,
                'EMAIL': email,
                'TELEPHONE': phone_numer
            }
        }
        stars = self.michelin_star_finder(soup)
        restaurant_info['Détails']['ÉTOILES MICHELIN'] = stars
        image_url = self.get_images(soup)
        restaurant_info['Détails']['IMAGE'] = image_url

        time.sleep(1)
        fonctionnalite , horaires , rank = self.google_scrapping_info(self.url)
        print("1")
        print(fonctionnalite)
        print(horaires)
        print(rank)
        print("2")
        if fonctionnalite is None:
            if self.rank_info < 3:
                for i in tqdm.tqdm(range(3)):
                    time.sleep(1)
                self.google_scrapping_info(self.url)
                self.rank_info += 1
            else:
                self.rank_info = 0
                
        restaurant_info['Détails']['FONCTIONNALITE'] = fonctionnalite if fonctionnalite else None
        restaurant_info['Détails']['HORAIRES'] = horaires if horaires else None
        restaurant_info['Détails']['RANK'] = rank if rank else None
        print(restaurant_info['Détails']['FONCTIONNALITE'])
        print(restaurant_info['Détails']['HORAIRES'])
        print(restaurant_info['Détails']['RANK'])
        
        
        if  restaurant_info['Détails']['RANK'] is None:
            restaurant_info['Détails']['RANK'] = self.get_ranking(soup)
        
        return restaurant_info
    
############### __methods__ #######################     
    
    def get_images(self, soup):
        photo_viewer_div = soup.find('div', {'data-section-signature': 'photo_viewer'})
        if photo_viewer_div:
            # Trouver toutes les balises <source> et <img> à l'intérieur de ce div
            media_tags = photo_viewer_div.find( 'img')
            print(media_tags)
            # Extraire les URLs des attributs srcset
            srcset_urls = []
            media_tags
            srcset = media_tags.get('srcset')
            src = media_tags.get('src')
            if srcset:
                    # Séparer les différentes résolutions et extraire les URLs
                urls = [s.split(' ')[0] for s in srcset.split(',')]
                srcset_urls.extend(urls)
                first_url = srcset_urls[0]
                cleaned_url = first_url.split('?')[0]
                
            elif src:
                urls = [s.split(' ')[0] for s in src.split(',')]
                srcset_urls.extend(urls)
                first_url = srcset_urls[0]
                cleaned_url  = first_url.split('?')[0]
            else :
                cleaned_url = None
        else:
            cleaned_url = None
            
        return cleaned_url

############### __methods__ #######################     
    
    def extract_reviews(self, soup):
        
        reviews = soup.find_all("div", class_="_c")
        print("longueur des reviews", len(reviews))
        for review in reviews:
            try:
                user = review.find("a", class_="BMQDV _F Gv wSSLS SwZTJ FGwzt ukgoS")
                user_profil = user['href'].replace('/Profile/', '') if user and 'href' in user.attrs else None
                title = review.find("div", class_="biGQs _P fiohW qWPrE ncFvv fOtGX").text.strip()
                avis = review.find("span", class_="JguWG")
                date_review = review.find("div", class_="biGQs _P pZUbB ncFvv osNWb").text.replace('Rédigé le ', '').strip()
                type_visits = review.find("span", class_="DlAxN")
                if type_visits is not None:
                    type_visits = type_visits.text
                else:
                    type_visits = "No information"
                 # Extract rating
                rating_tag = review.find("div", class_="OSBmi J k")
                rating_title = rating_tag.find("title").text.strip() if rating_tag and rating_tag.find("title") else None
                rating = float(re.search(r'\d,\d', rating_title).group().replace(',', '.')) if re.search(r'\d,\d', rating_title) else None
                
                contrib_container = review.find("div", class_="vYLts")
                num_contributions_tag = contrib_container.find("span", class_="b") if contrib_container else None
                num_contributions = int(num_contributions_tag.text.strip()) if num_contributions_tag else 0 
                print("user", user.text)
                print("user_profil", user_profil)
                print("date_review", date_review)
                print("avis",   avis.text.strip())
                
                
                
                self.reviews.append({
                    'user': user.text.strip() if user else None,
                    'user_profile': user_profil if user_profil else None,
                    'date_review': date_review if date_review else None,
                    'title': title if title else None,
                    'rating': rating,
                    'type_visit': type_visits,
                    'num_contributions': num_contributions, 
                    'review': avis.text if avis else None
                    
                })
                
                # #write the reviews in a file
                # with open(f'review/{self.review_number}.txt', 'w', encoding='utf-8') as f:
                #     f.write(f"{user.text.strip()}|{user_profil}|{date_review}|{title}|{rating}|{type_visits}|{num_contributions}|{avis.text.strip()}\n")
                self.review_number += 1
                
            except AttributeError:
                continue

    def get_soup(self,url):
    
        header = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
                    'Accept': 'text/html, application/xhtml+xml, application/xml;q=0.9, image/avif, image/webp, image/apng, image/*,*/*;q=0.8',
                    'Accept-Language': 'fr-FR,fr;q=0.9',
                    'Connection': 'keep-alive',
                    'Upgrade-Insecure-Requests': '1',
                    'TE': 'Trailers',
                    "DNT": "1",  # Do Not Track
                    "Origin": "https://www.tripadvisor.fr/",
                    'Referer' : url ,
                    
        }
   
        response = requests.get(url, headers=header, timeout=(3.05, 27), params={"_": str(int(time.time()))})
        if response.status_code != 200:
            print(f"Failed to get page {url}")
            return None
        return BeautifulSoup(response.text, 'html.parser')

    def get_workdays(self,soup_google):
        hours_div = soup_google.find('div', class_='OlkEn AdWFC')
        if not hours_div:
            return None
        hours_div_plus = hours_div.select('div[class="f"]')
        if not hours_div_plus:
            return None
        horaires = {}
        # class contenant un div jour klgPI Nk
        # Parcourir les blocs pour extraire les informations
        for div in hours_div_plus:
            # Extraire le jour
            
            jour_div = div.find('div', class_='klgPI Nk')
            jours_precis = jour_div.find('div', class_='fOtGX')
            if jours_precis:
                jour = jours_precis.text.strip()
            
            else:
                continue
            # class conternant un div horraire f e
            # Extraire les horaires ou l'indication "Fermé"
            horaires_div = div.find('div', class_='f e')

        
            horaires[jour] = []
            if horaires_div:
                # get all span inside the div
                horaires_span = horaires_div.find_all('span')
                for span in horaires_span:
                    horaires[jour].append(span.text)
            else:
                horaires[jour].append("Fermé")
            
        ## creer un texte sous la forme : "Lundi: 12h-14h, 19h-22h; Mardi: 12h-14h, 19h-22h; Mercredi: 12h-14h, 19h-22h; Jeudi: 12h-14h, 19h-22h; Vendredi: 12h-14h, 19h-22h; Samedi: 12h-14h, 19h-22h; Dimanche: 12h-14h, 19h-22h"
        horaires_text = ""
        for jour, horaire in horaires.items():
            horaires_text += f"{jour}: {', '.join(horaire)}; "
        return horaires_text

    def get_ranking(self,soup_google):
        # rank restaurant
        # Clean the ranking string by removing non-breaking spaces and narrowing spaces
        ranking = soup_google.find(attrs={"data-test-target": "restaurant-detail-info"})
        if not ranking:
            return None
        ranking = ranking.find('span', class_='ffHqI')
        if not ranking:
            return None
        ranking = ranking.text
        ranking = ranking.replace('\u202f', '')
        # Extract the current rank and total number of restaurants using regex
        numbers  = re.findall(r'\d+', ranking)
        # Extraire les deux nombres
        if len(numbers) >= 2:
            rank = int(numbers[0])
        else:
            rank = None
            
        return rank
    
    def get_fonctionnalite(self, soup_google):
        # rank restaurant
        # Clean the ranking string by removing non-breaking spaces and narrowing spaces
        fonctionnalite = soup_google.find('div', class_='kYFok f e Q1 BUDdf')
        if not fonctionnalite:
            return None
        features = []
        feature_containers = fonctionnalite.find_all('div', class_='fQXjj')
        if not feature_containers:
            return None
        
        for container in feature_containers:
            # Trouver les balises <span> qui contiennent le texte des fonctionnalités
            feature_text = container.find('span')
            if feature_text and feature_text.text.strip():
                features.append(feature_text.text.strip())
        fonct_text = ""
        for feature in features:
            fonct_text += f"{feature}; "
        return fonct_text

    def google_scrapping_info(self, url):
        
        soup_google = self.get_soup(url)
        fonctionnalite = self.get_fonctionnalite(soup_google)
        horaires = self.get_workdays(soup_google)
        rank = self.get_ranking(soup_google)
        return  fonctionnalite, horaires, rank



############### __methods__ #######################    
      
    def scrape_info(self, url):
        self.run(url)
        if not self.soup:
            print(f"Failed to get restaurant page {url}")
            return None
        self.restaurant_info = self.get_restaurant_info(self.soup)
        return self.restaurant_info

############### __methods__ #######################    

    def scrape_restaurant(self, url):
        self.session = None
        self.run(url, reviews=True)
        if not self.soup:
            print(f"Failed to get restaurant page {url}")
            return None
        self.extract_reviews(self.soup)
        next_page_href = self.get_next_url()
        print("Next page : " , next_page_href)
        while next_page_href:
            for i in tqdm.tqdm(range(5)):
                        time.sleep(1)
            
            self.extract_reviews(self.soup)
            self.run(self.base_url + next_page_href)
            next_page_href = self.get_next_url()
    
        return self.restaurant_info, self.reviews
    
############### __methods__ #######################     
    
    def to_dataframe(self):
        
        if self.reviews:
            # Nettoyage des données
            for review in self.reviews:
                for key, value in review.items():
                    if isinstance(value, str):
                        review[key] = re.sub(r'\s+', ' ', value).strip()
                    elif isinstance(value, list):
                        review[key] = ', '.join(value)  # Convertit les listes en chaînes

            # Créer le DataFrame
            df_reviews = pd.DataFrame(self.reviews)
        else:
            df_reviews = pd.DataFrame()
       
        if self.restaurant_info:
            df_avis = pd.DataFrame(self.restaurant_info['Notes et avis'], index=[0])
            df_details = pd.DataFrame(self.restaurant_info['Détails'] , index=[0])
            df_location = pd.DataFrame(self.restaurant_info['Emplacement et coordonnées'], index=[0]) 
        else:
            df_avis = pd.DataFrame()
            df_details = pd.DataFrame()
            df_location = pd.DataFrame()  
        return df_avis, df_details, df_location, df_reviews

############### __methods__ #######################    
    
    def to_csv(self):
        df_avis, df_details, df_location, df_reviews = self.to_dataframe()
        df_avis.to_csv('avis.csv', index=False)
        df_details.to_csv('details.csv', index=False)
        df_location.to_csv('location.csv', index=False)
        df_reviews.to_csv('reviews.csv', index=False)
        
        
        
    
    
    
    
    
    
    
    
    
    
