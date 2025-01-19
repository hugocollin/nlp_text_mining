import requests
import pandas as pd
import re
import time
import numpy as np
import platform
import tqdm
from bs4 import BeautifulSoup

# Définition de la classe SearchEngine
class SearchEngine:
    # Constructeur
    def __init__(self):
        self.base_url = "https://www.tripadvisor.fr"
        self.session = None
        self.cookies_list = [{'TADCID': '95got4bq91GmregYABQCrj-Ib21-TgWwDB4AzTFpg4J0pITsougolk1a7SaZZ7sYmkJu7KPOcqvM0xwqN1w93LttdFLFrqsYJ7w', 'TASameSite': '1', '__vt': 'M-4ijWLl6k7ybNR4ABQCjdMFtf3dS_auw5cMBDN7STJSRCH1nXChQ-WY5JlSnMR1uxIGdRWOqVv5tzhczv2Wi5nvq3oTCp7u5GoQG5I0EKASCq7B0TNG2mQVbmucgXvHPZ_YZpAWQnpr_ru3N91wLIMyxQ', 'TASID': 'A49FD32AED6A062F36B3FEFE390763C5', 'TAUnique': '%1%enc%3AdkjfOfw%2Ftm%2FlxUOBpOSBodxVTnjfkCfULJk9agUV4g3zZWtZ%2FjDJk605yvvNffQrNox8JbUSTxk%3D', 'datadome': 'M8Sgk8DaVoG_E_zlyrRsQ9uvHoNM93ifQS9R8PKSjGOo6Aqy6Zw5CJtbfX8jys20Iv2oN7NAJFAg6Nxh9nZYyZ4SJfCN_nRu~5g07XIDokW_jYeHO5ur5ekBFu_TMUFj'},
                             {'TADCID': '95got4bq91GmregYABQCrj-Ib21-TgWwDB4AzTFpg4J0pITsougolk1a7SaZZ7sYmkJu7KPOcqvM0xwqN1w93LttdFLFrqsYJ7w', 'TASameSite': '1', '__vt': 'M-4ijWLl6k7ybNR4ABQCjdMFtf3dS_auw5cMBDN7STJSRCH1nXChQ-WY5JlSnMR1uxIGdRWOqVv5tzhczv2Wi5nvq3oTCp7u5GoQG5I0EKASCq7B0TNG2mQVbmucgXvHPZ_YZpAWQnpr_ru3N91wLIMyxQ', 'TASID': 'A49FD32AED6A062F36B3FEFE390763C5', 'TAUnique': '%1%enc%3AdkjfOfw%2Ftm%2FlxUOBpOSBodxVTnjfkCfULJk9agUV4g3zZWtZ%2FjDJk605yvvNffQrNox8JbUSTxk%3D', 'datadome': 'M8Sgk8DaVoG_E_zlyrRsQ9uvHoNM93ifQS9R8PKSjGOo6Aqy6Zw5CJtbfX8jys20Iv2oN7NAJFAg6Nxh9nZYyZ4SJfCN_nRu~5g07XIDokW_jYeHO5ur5ekBFu_TMUFj'}]
        self.soup = None
        self.cookies = None
        self.rank = 0
        self.url = None

    # Méthode d'affichage
    def __str__(self):
        print(f"SearchEngine(base_url='{self.base_url}')")
        print(f"Session: {self.session}")
        print(f"cookies: {self.cookies}")
        print(f"Soup: {self.soup}")
        return ""

    # Méthode de récupération de la session
    def get_session(self):
        # Création d'une nouvelle session si elle n'existe pas
        if not self.session:
            print("Creating a new session...")
            self.session = requests.Session()
            self.cookies = np.random.choice(self.cookies_list)  
            for name, value in self.cookies.items():
                self.session.cookies.set(name, value, domain='.tripadvisor.fr')
        else:
            print("Session already exists")

    # Méthode de récupération de l'agent utilisateur en fonction du système d'exploitation
    def get_os_user_agent(self):
        os = platform.system()
        if os == "Windows":
            return "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:127.0) Gecko/20100101 Firefox/109.0"
        elif os == "Linux":
            return "Mozilla/5.0 (X11; Linux x86_64; rv:109.0) Gecko/20100101 Firefox/109.0"
        else:
            return "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/"

    # Méthode d'éxécution de la requête
    def run(self, url, reviews=None):
        
        # Récupération de l'agent utilisateur en fonction de la requête
        if reviews:
            user_agent = self.get_os_user_agent()
        else:
            user_agent = "Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) SamsungBrower/27.0 Chrome/125.0.0.0 Mobile Safari/537.36"
        self.url = url
        headers = {
            
            #'User-Agent': "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Gecko/20100101 Firefox/109.0", # AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36
            #'User-Agent': "Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) SamsungBrower/27.0 Chrome/125.0.0.0 Mobile Safari/537.36",
            'User-Agent':  user_agent,
            'Accept': 'text/html, application/xhtml+xml, application/xml;q=0.9, image/avif, image/webp, image/apng, image/*,*/*;q=0.8',
            'Accept-Language': 'fr-FR,fr;q=0.9',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'TE': 'Trailers',
            "DNT": "1",
            "Origin": "https://www.tripadvisor.fr/",
            'Referer' : url ,

        }

        # Récupération de la session
        self.get_session()

        # Mise à jour des en-têtes
        self.session.headers.update(headers)
        time.sleep(1)
        print(time.ctime())

        # Exécution de la requête
        response = self.session.get(url, headers=headers, timeout=(6, 36))
        time.sleep(1)

        # Vérification du code de statut
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
    
    # Méthode de récupération de l'URL de la page suivante
    def get_next_url(self):
        # Recherche de la pagination
        pagination = self.soup.find_all("div", class_="mkNRT j")
        if not pagination:
            return None
        
        # Attributs possibles pour le bouton de la page suivante
        attrs_possible = [
            {"aria-label" : "Page suivante"},
            {"data-smoke-attr" : "pagination-next-arrow" },
            {"aria-label" : "Next page"},
        ]

        # Recherche du bouton de la page suivante
        for page in pagination:
            page_elements = page.find("a", attrs=attrs_possible[0]) or page.find("button", attrs=attrs_possible[1]) or page.find("a", attrs=attrs_possible[2])
            if page_elements:
                return page_elements.get("href")
            else:
                print("No next page found")
                return None

# Définition de la classe RestaurantFinder qui hérite de la classe SearchEngine
class RestaurantFinder(SearchEngine):
    # Constructeur
    def __init__(self):
        super().__init__()
        self.all_restaurants = []
        self.current_url = None
        self.current_page = 1

    # Méthode de recherche des restaurants        
    def find_restaurants(self):
        restaurants = []
        
        # Recherche des résultats de la recherche
        search_results = self.soup.find('div', {'data-automation': 'searchResults', 'class': 'Ikpld f e'})
        
        # Recherche des cartes de restaurant
        if search_results:
            restaurant_cards = search_results.find_all('div', class_='vIjFZ Gi o VOEhq')
            
            # Extraction des informations des cartes de restaurant
            for card in restaurant_cards:
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

    # Méthode de scrapping de tous les restaurants
    def scrape_all_restaurants(self,start_url = "https://www.tripadvisor.fr/Restaurants-g187265-Lyon_Rhone_Auvergne_Rhone_Alpes.html" , max_pages=10):
        self.current_url = start_url
        self.current_page = 1

        # Scrapping des restaurants
        while self.current_url:
            time.sleep(5)
            if max_pages and self.current_page > max_pages:
                break
            
            print(f"Scraping page {self.current_page}...")
            print(f"Current URL: {self.current_url}")
            
            # Exécution de la requête
            self.run(self.current_url)

            if not self.soup:
                print(f"Failed to get page {self.current_page}")
                break
                
            # Exctraction des restaurants de la page
            page_restaurants = self.find_restaurants()
            self.all_restaurants.extend(page_restaurants)
            
            # Récupération de l'URL de la page suivante
            next_page_href = self.get_next_url()
            if not next_page_href:
                print("scrapping end")
                break
            else:
                # Mise à jour de l'URL de la page courante
                self.current_url = self.base_url + next_page_href if next_page_href.startswith('/') else self.base_url + '/' + next_page_href
                self.current_page += 1
                print(f"Next page: {self.current_url}")
                time.sleep(np.random.uniform(2, 6))
        
        print(f"Found {len(self.all_restaurants)} restaurants total")
        return self.all_restaurants
    
    # Méthode de conversion en DataFrame
    def to_dataframe(self):
        return pd.DataFrame(self.all_restaurants)
    
    # Méthode de conversion en fichier CSV
    def to_csv(self):
        df = self.to_dataframe()
        df.to_csv('Data/liste_restaurants.csv', index=False)
        
# Définition de la classe restaurant_info_extractor qui hérite de la classe SearchEngine
class restaurant_info_extractor(SearchEngine):
    # Constructeur
    def __init__(self):
        super().__init__()
        self.restaurant_info = {}
        self.reviews = []
        self.rank_info = 0
        self.review_number = 0
                
    # Méthode pour définir le nombre d'étoiles Michelin
    def michelin_star_finder(self,soup): 
        if soup.find('img', src="https://static.tacdn.com/img2/restaurant-awards/michelin/1-Star.svg"):
            return 1
        elif soup.find('img', src="https://static.tacdn.com/img2/restaurant-awards/michelin/2-Stars.svg"):
            return 2
        elif soup.find('img', src="https://static.tacdn.com/img2/restaurant-awards/michelin/3-Stars.svg"):
            return 3
        else:
            return 0

    # Méthode pour extraire la note 
    def extract_note(self,text):
                        match = re.search(r'\d,\d', text)
                        return match.group() if match else None

    # Méthode pour extraire les informations du restaurant      
    def get_restaurant_info(self, soup):
        # Notes et avis
        notes_avis_section = soup.find('div', class_='QSyom f e Q3 _Z')

        # Si la section des notes et avis n'est pas trouvée
        if not notes_avis_section:
            print("No notes found")
            if self.rank_info < 2:
                print("No data found")
                self.rank_info += 1
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

        # Si la section des notes et avis est trouvée
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
                
        # Définition des notes
        notes = {
            'CUISINE': cuisine_note,
            'SERVICE': service_note,
            'RAPPORT QUALITÉ-PRIX': quality_price_note,
            'AMBIANCE': ambiance_note
        }

        # Récupération de la section des détails
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

        # Récupération des coordonnées
        location_section = soup.find('div', class_='Zb w')
        if location_section:
            address_tag = location_section.find('a', href=True)
            address = address_tag.text.strip() if address_tag else None
            google_map = address_tag['href'] if address_tag else None

            # Fonction pour extraire la latitude et la longitude de l'URL Google Maps
            def extract_lat_lon(href):
                match = re.search(r'@(-?\d+\.\d+),(-?\d+\.\d+)', href)
                return match.groups() if match else (None, None)
            lat, lon = extract_lat_lon(google_map)
            
            email_tag = soup.find('a', href=lambda href: href and href.startswith('mailto:'))
            email = email_tag['href'].split(':')[1] if email_tag else None

            phone_tag = location_section.find('a', href=lambda x: x and x.startswith('tel:'))
            phone_numer = phone_tag['href'].split(':')[1] if phone_tag else None
        else:
            address = email = phone_numer = None

        # Oragnisation des informations du restaurant
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
        if restaurant_info['Détails']['RANK'] is None:
            restaurant_info['Détails']['RANK'] = self.get_ranking(soup)
        
        return restaurant_info
    
    # Méthode pour extraire les images    
    def get_images(self, soup):
        photo_viewer_div = soup.find('div', {'data-section-signature': 'photo_viewer'})
        if photo_viewer_div:
            media_tags = photo_viewer_div.find( 'img')

            # Extraction des URLs des attributs srcset
            srcset_urls = []
            media_tags
            srcset = media_tags.get('srcset')
            src = media_tags.get('src')
            if srcset:
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

    # Méthode pour extraire les avis    
    def extract_reviews(self, soup):
        
        reviews = soup.find_all("div", class_="_c")
        # Itération sur les avis
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
                
                # Extraire la note de l'avis
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
                
                self.review_number += 1
                
            except AttributeError:
                continue

    # Méthode pour extraire les informations de Google
    def get_soup(self,url):
        
        # Définition des en-têtes
        header = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
                    'Accept': 'text/html, application/xhtml+xml, application/xml;q=0.9, image/avif, image/webp, image/apng, image/*,*/*;q=0.8',
                    'Accept-Language': 'fr-FR,fr;q=0.9',
                    'Connection': 'keep-alive',
                    'Upgrade-Insecure-Requests': '1',
                    'TE': 'Trailers',
                    "DNT": "1",
                    "Origin": "https://www.tripadvisor.fr/",
                    'Referer' : url ,
                    
        }

        # Exécution de la requête
        response = requests.get(url, headers=header, timeout=(3.05, 27), params={"_": str(int(time.time()))})
        if response.status_code != 200:
            print(f"Failed to get page {url}")
            return None
        return BeautifulSoup(response.text, 'html.parser')

    # Méthode pour extraire les horaires de travail
    def get_workdays(self,soup_google):
        hours_div = soup_google.find('div', class_='OlkEn AdWFC')
        if not hours_div:
            return None
        hours_div_plus = hours_div.select('div[class="f"]')
        if not hours_div_plus:
            return None
        horaires = {}

        # Parcours des blocs pour extraire les informations
        for div in hours_div_plus:
            jour_div = div.find('div', class_='klgPI Nk')
            jours_precis = jour_div.find('div', class_='fOtGX')
            if jours_precis:
                jour = jours_precis.text.strip()
            else:
                continue

            # Extraction des horaires où l'indication est Fermé
            horaires_div = div.find('div', class_='f e')

            horaires[jour] = []
            if horaires_div:
                horaires_span = horaires_div.find_all('span')
                for span in horaires_span:
                    horaires[jour].append(span.text)
            else:
                horaires[jour].append("Fermé")
            
        # Mise en forme des horaires
        horaires_text = ""
        for jour, horaire in horaires.items():
            horaires_text += f"{jour}: {', '.join(horaire)}; "
        return horaires_text

    # Méthode pour extraire le classement
    def get_ranking(self,soup_google):
        ranking = soup_google.find(attrs={"data-test-target": "restaurant-detail-info"})
        if not ranking:
            return None
        ranking = ranking.find('span', class_='ffHqI')
        if not ranking:
            return None
        ranking = ranking.text
        ranking = ranking.replace('\u202f', '')
        numbers  = re.findall(r'\d+', ranking)

        if len(numbers) >= 2:
            rank = int(numbers[0])
        else:
            rank = None
            
        return rank
    
    # Méthode pour extraire les fonctionnalités
    def get_fonctionnalite(self, soup_google):

        # Recherche de la section des fonctionnalités
        fonctionnalite = soup_google.find('div', class_='kYFok f e Q1 BUDdf')
        if not fonctionnalite:
            return None
        features = []
        feature_containers = fonctionnalite.find_all('div', class_='fQXjj')
        if not feature_containers:
            return None
        
        # Recherche des fonctionnalités
        for container in feature_containers:
            feature_text = container.find('span')
            if feature_text and feature_text.text.strip():
                features.append(feature_text.text.strip())
        fonct_text = ""
        for feature in features:
            fonct_text += f"{feature}; "
        return fonct_text

    # Méthode pour extraire les informations de Google
    def google_scrapping_info(self, url):
        soup_google = self.get_soup(url)
        fonctionnalite = self.get_fonctionnalite(soup_google)
        horaires = self.get_workdays(soup_google)
        rank = self.get_ranking(soup_google)
        return  fonctionnalite, horaires, rank

    # Méthode pour scraper les informations du restaurant
    def scrape_info(self, url):
        self.run(url)
        if not self.soup:
            print(f"Failed to get restaurant page {url}")
            return None
        self.restaurant_info = self.get_restaurant_info(self.soup)
        return self.restaurant_info

    # Méthode pour scraper les avis du restaurant
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
    
    # Méthode pour convertir les données en DataFrame
    def to_dataframe(self):
        
        if self.reviews:
            # Nettoyage des données
            for review in self.reviews:
                for key, value in review.items():
                    if isinstance(value, str):
                        review[key] = re.sub(r'\s+', ' ', value).strip()
                    elif isinstance(value, list):
                        review[key] = ', '.join(value)

            # Création du DataFrame des avis
            df_reviews = pd.DataFrame(self.reviews)
        else:
            df_reviews = pd.DataFrame()
       
        # Création des DataFrames des informations du restaurant
        if self.restaurant_info:
            df_avis = pd.DataFrame(self.restaurant_info['Notes et avis'], index=[0])
            df_details = pd.DataFrame(self.restaurant_info['Détails'] , index=[0])
            df_location = pd.DataFrame(self.restaurant_info['Emplacement et coordonnées'], index=[0]) 
        else:
            df_avis = pd.DataFrame()
            df_details = pd.DataFrame()
            df_location = pd.DataFrame()  
        return df_avis, df_details, df_location, df_reviews

    # Méthode pour convertir les données en fichier CSV    
    def to_csv(self):
        df_avis, df_details, df_location, df_reviews = self.to_dataframe()
        df_avis.to_csv('avis.csv', index=False)
        df_details.to_csv('details.csv', index=False)
        df_location.to_csv('location.csv', index=False)
        df_reviews.to_csv('reviews.csv', index=False)