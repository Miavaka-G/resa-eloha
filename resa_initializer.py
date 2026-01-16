from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from datetime import datetime, timedelta
import time 
from random import randint, uniform
from pathlib import Path
import os, json, csv
from webdriver_manager.chrome import ChromeDriverManager #miasa rehefa sur serveur
from selenium.webdriver.chrome.service import Service
from bs4 import BeautifulSoup
from urllib.parse import urlencode
from dotenv import load_dotenv

#A PRENDRE EN COMPTE QUE : avec resanc les dates déja passé n'afficheront rien'
load_dotenv()
OUTPUT_PATH_DEST = os.getenv('OUTPUT_PATH_DEST')
OUTPUT_INIT_LOG = os.getenv('OUTPUT_LOG_INIT')

class resa_initializer(object):
    def __init__(self, reservation : int, week_scrap : str, end_date_scrap : str):
        self.reservation = reservation
        # self.name = name nesorina fa tsy ilaina , aleo tonga dia hoentin ilay reservation MAJ 05/01/2026
        #Après reflexion, puisque les jours déja passés n'afficheront aucun établissement, donc on démarre le scrap à partir de la date du jours
        self.start_date_scrap = datetime.strptime(datetime.now().strftime('%d/%m/%Y'), '%d/%m/%Y')
        self.name_of_file_output = f'resanc_dest{reservation}' #comme ça on verra nettement si jamais on se trompe de paramètre -r
        self.name_of_folder_output = f'{week_scrap}' #mais le nom du dossier sera la semaine de scrap pour plus de visibilité
        self.end_date_scrap = datetime.strptime(end_date_scrap, '%d/%m/%Y')

        #on aura besoin de cette variable pour le log de suivi, MAJ 08 01 2026
        self.nb_day_remaining = int((self.end_date_scrap - self.start_date_scrap).days) + 1

        #variable pour les urls d'hébergements disponibles par date (contiendra des dictionnaires avec checkin, checkout et url)
        self.dest_by_date = []
        self.url_base_hebergement = 'https://www.resa.nc/hebergements/'

        self.count_url_extracted = 1

        self.chrome_options = webdriver.ChromeOptions()
        self.chrome_options.add_argument("--no-image")
        self.chrome_options.add_argument('--ignore-certificate-errors')
        self.chrome_options.add_argument('--disable-gpu')
        self.chrome_options.add_argument('--incognito')
        self.chrome_options.add_argument("--no-sandbox") 
        self.chrome_options.add_argument("--disable-dev-shm-usage")
        # self.chrome_options.add_argument("--headless=new") 
        self.chrome_options.add_argument("--log-level=3") 
        self.chrome_options.add_experimental_option("excludeSwitches", ["enable-logging"])
        

    def goto_resa_hebergement_page(self, url : str):
        self.driver = webdriver.Chrome(options=self.chrome_options)
        self.driver.maximize_window()
        time.sleep(uniform(0.5, 1.8))
        self.driver.get(url)
        time.sleep(randint(2,4))

    def save(self):
        #création du dossier de sauvegarde si inexistant
        output_path_dest = f'{OUTPUT_PATH_DEST}/{self.name_of_folder_output.replace("/", "_")}/'
        dest_file_name = f'{output_path_dest}{self.name_of_file_output}.json'
        #créer si le sossier n'existe pas
        if not os.path.exists(output_path_dest):
            os.makedirs(output_path_dest)
        try:
            if os.path.exists(dest_file_name):
                #si le fichier existe déjà, on ajoute les nouvelles données à la suite
                with open(dest_file_name, 'r', encoding='utf-8') as f:
                    existing_data = json.load(f)
                #ajout dees nouvelles données en forme de liste de dictionnaire (amzay tsy manisy crochet manuel otran edomizil)
                existing_data.extend(self.dest_by_date)
                #écriture des données mises à jour dans le fichier
                with open(dest_file_name, 'w', encoding='utf-8') as f:
                    json.dump(existing_data, f, ensure_ascii=False, indent=4)
            else:
                with open(dest_file_name, 'w', encoding='utf-8') as f:
                    json.dump(self.dest_by_date, f, ensure_ascii=False, indent=4)
                
            #noombre d'url sauvegardé
            self.count_url_extracted += 1
            print('                ')
            print(f'url numéro {self.count_url_extracted}')
            print('                ')
            
            self.dest_by_date = [] #on vide la liste après chaque sauvegarde
        except Exception as e:
            print("                ")
            print(f'Erreur lors de la sauvegarde des données: {e}')
            input("                ")


    def generate_date_ranges(self):
        #on génèrera ici les dates de checkin et checkout qu'on insèrera dans les inputs de la page resa.nc/hebergements via une boucle
        pass

    def put_params_url(self, url : str, checkin : str, checkout : str) -> str:
        params_to_put = {
            "dispo_type" : "Hebergements", #MAJ 05/01/2026
            "dispo_du" : checkin,
            "dispo_au" : checkout,
            "dispo_nb_pers" : 1
        }

        return f"{url}?{urlencode(params_to_put)}"

    def check_hebergement_disponibility_by_date(self): #MAJ 08 01 2026 pour insérer le log d'initialisation
        if self.reservation in [1,3,7]:
            #si le log est = au nombre de date self.nb_day_remaining, on démarre le l'initialisation depuis le début en prenant les paramètres de date via la ligne de commande
            check_log_init = self.load_log_file()
            if check_log_init['days_remaining'] == self.nb_day_remaining:

                print('démarrage de l\'initialisation depuis le début')

                self.extract_url_by_hebergement_disponible(check_log_init)

            elif check_log_init['days_remaining'] < self.nb_day_remaining:
                print('Reprise de l\'initialisation depuis la coupure')

                self.extract_url_by_hebergement_disponible(check_log_init)

            time.sleep(uniform(1.5,2.2))
        else:
            input('La fréquence de réservation doit être de 1, 3 ou 7 jours. Relancer le programme avec une valeur correcte.')
            self.driver.quit()

    #08 01 2026
    def extract_url_by_hebergement_disponible(self, check_log):
        #Méthode d'extraction proprement
        date_space_scrap = check_log['days_remaining']
        print(f'Reste de jours jusqu\'à la dernière date de scraping: {date_space_scrap} days')

        chekin_dates = datetime.strptime(check_log['last_checkin_date'], '%d/%m/%y')
        checkout_dates = datetime.strptime(check_log['last_checkout_date'], '%d/%m/%y')

        for day in range(date_space_scrap): #on laisse tel quel, date space scrap mais lorsque c'est coupé ça sera changé par le log
            hebergement_dispo = self.put_params_url(self.url_base_hebergement, chekin_dates.strftime("%d/%m/%Y"), checkout_dates.strftime("%d/%m/%Y"))
            self.goto_resa_hebergement_page(hebergement_dispo)

            #attente de chargement des hébergements, ça prend du temps
            print('             ')
            print('attente du chargement des hébergements disponibles...')
            print('             ')
            time.sleep(randint(1,4))
            while self.driver.find_elements(By.CSS_SELECTOR,'p[class="chargement-en-cours"]'):
                print('             ')
                print('Toujours en cours de chargement...')
                print('             ')
                time.sleep(2)
            print('             ')
            print('Chargement des hébergements disponibles pour nos dates terminé.')
            print('             ')                

            #aleo atao anaty Soup fa indraindray miactualise ilay page (19 12 2025)
            soup = BeautifulSoup(self.driver.page_source, 'lxml')

            link_hebergement_container = soup.find('div',{'class':'wrapper-cards'})  
            link_hebergements = link_hebergement_container.find('div', {'data-loading': 'Chargement en cours'}).find_all('a')

            print(f'Hebergements trouvés pour la date {chekin_dates.strftime("%d/%m/%Y")} au {checkout_dates.strftime("%d/%m/%Y")}: {len(link_hebergements)}')
            print("                     ")
            for link in link_hebergements:
                hebergement_url = link.get('href')
                print(f'Hebergement found: {hebergement_url}')
                self.dest_by_date.append({
                    'checkin' : chekin_dates.strftime("%d/%m/%Y"),
                    'checkout' : checkout_dates.strftime("%d/%m/%Y"),
                    'url' : hebergement_url
                })
                # input(f'Donnée reçu => {self.dest_by_date}')

                #on sauvegarde à chaque itération pour éviter de tout perdre en cas de problème et aussi pour alléger la mémoire
                self.save()

            #incrémentation des dates de checkin et checkout pour la prochaine itération
            chekin_dates += timedelta(days=1)
            checkout_dates += timedelta(days=1)

            #mise à jour du fichier de log d'initialisation
            check_log['days_remaining'] -= 1
            # input(f'Nouvel espace de date à scraper => {check_log["days_remaining"]} days')
            self.update_init_log_file(check_log['days_remaining'], chekin_dates.strftime('%d/%m/%y'), checkout_dates.strftime('%d/%m/%y'))

            #vider le parser
            soup.decompose()

    #08 01 2026
    def load_log_file(self) -> dict: #on peut passer un dictionnaire vide pour initialiser le log
        output_log_init_path = f"{OUTPUT_INIT_LOG}{self.name_of_folder_output.replace('/','_')}/"
        log_init_file_name = f'{output_log_init_path}init_resanc_dest{self.reservation}.json'
        if not os.path.exists(output_log_init_path):
            os.makedirs(output_log_init_path)
        if not os.path.exists(log_init_file_name):
            #création du fichier de log initial
            init_log = {'days_remaining' : self.nb_day_remaining, 
                        'last_checkin_date' : self.start_date_scrap.strftime('%d/%m/%y'), 
                        'last_checkout_date' : (self.start_date_scrap + timedelta(days=self.reservation)).strftime('%d/%m/%y')} #ça ajoutera toujours le nombre de jour de réservation à la date de checkin pour avoir la date de checkout
            # input(f'ireto le format de date ato => {init_log}')
            with open(log_init_file_name, 'w', encoding='utf-8') as f:
                json.dump(init_log, f, ensure_ascii=False, indent=4)
            return init_log
        else:
            #chargement du fichier de log existant
            with open(log_init_file_name, 'r', encoding='utf-8') as f:
                existing_log = json.load(f)
            return existing_log
    
    #08 01 2026
    def update_init_log_file(self, days_remaining : int, last_checkin_date : datetime, last_checkout_date : datetime):
        output_log_init_path = f"{OUTPUT_INIT_LOG}{self.name_of_folder_output.replace('/','_')}/"
        log_init_file_name = f'{output_log_init_path}init_resanc_dest{self.reservation}.json'
        try:
            updated_init_log = {'days_remaining' : days_remaining,
                                'last_checkin_date' : last_checkin_date,
                                'last_checkout_date' : last_checkout_date}
            with open(log_init_file_name, 'w', encoding='utf-8') as f:
                json.dump(updated_init_log, f, ensure_ascii=False, indent=4)
        except Exception as e:
            print(f'Erreur lors de la mise à jour du fichier de log initial: {e}, stopper le programme et vérifier manuellement le fichier.')
            input('                ')
            
        
    def extract_url_for_all_hebergement_exist(self):
        #rehefa isauv an'ity dia asio ny date nanaovana azy, amin'izay hita hoe firy no isan'ny hebergement misy amin'ilay jour nanaovana extract all
        pass

    def execute(self):
        print(' => Starting ResaNc Initializer ')
        print('                 ')

        # print(' Step 1 - Going to ResaNc hebergement page ')
        # self.goto_resa_hebergement_page()
        # self.extract_url_for_all_hebergement_exist()
        print(' Step 1 - Load log file ')
        self.load_log_file()

        print(' Step 2 - Check des hébergements disponibles par date (params url) et sauvegarde')
        self.check_hebergement_disponibility_by_date()

        print('                 ')
        print(f' => ResaNc Initializer Finished , on a extrait {self.count_url_extracted} URLs d\'hébergements disponibles ')

        time.sleep(1.5)
