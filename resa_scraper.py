import re
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from datetime import datetime, timedelta
import time 
from random import randint, uniform
from pathlib import Path
import os, csv, json
from webdriver_manager.chrome import ChromeDriverManager #SUr serveur quand le chrome est MAJ
from selenium.webdriver.chrome.service import Service
from bs4 import BeautifulSoup
from dotenv import load_dotenv
import sys
import random

#09 01 2026
from selenium.webdriver.support.ui import Select
from selenium.common.exceptions import NoSuchElementException

load_dotenv()

OUTPUT_LOGS_PATH = os.getenv('OUTPUT_LOGS_PATH')
OUTPUT_PATH_DEST = os.getenv('OUTPUT_PATH_DEST')
OUTPUT_RESULTS_PATH = os.getenv('OUTPUT_RESULTS_PATH')
OUTPUT_PATH_INCOMPLETE = os.getenv('OUTPUT_PATH_INCOMPLETE')
SYSTEM = os.getenv("SYSTEM")
PROFILE_CHROME = os.getenv('PROFILE_CHROME')

# FIELD_NAMES = [
#                 'date_price',
#                 'checkin', 
#                 'checkout',
#                 'price',
#                 'currency',
#                 'typology',
#                 'name',
#                 'locality',
#                 'week_number',
#             ]
#Normalisation avec les g2a 16 01 2026
FIELD_NAMES = [ 
                'web-scraper-order',
                'date_price',
                'date_debut', 
                'date_fin',
                'prix_init',
                'prix_actuel',
                'typologie',
                'n_offre',
                'nom',
                'localite',
                'date_debut-jour',
                'Nb semaines',
                'currency'
            ] 

class resa_scraper(object):
    def __init__(self, destination : str, name : str, week_scrap : str):
        self.week_scrap = datetime.strptime(week_scrap, '%d/%m/%Y')
        self.name_of_file_output = name
        self.name_of_folder_output = f'/{week_scrap}'
        self.name_of_destination_file = destination

        self.chrome_options = webdriver.ChromeOptions()
        #no image
        pas_image = {"profile.managed_default_content_settings.images": 2}
        # self.chrome_options.add_experimental_option("prefs", pas_image)
        # self.chrome_options.add_argument('--ignore-certificate-errors')
        # self.chrome_options.add_argument('--disable-gpu')
        # self.chrome_options.add_argument('--incognito')
        # self.chrome_options.add_argument("--no-sandbox") 
        # self.chrome_options.add_argument("--disable-dev-shm-usage") commenté le 19 01 2025
        # self.chrome_options.add_argument("--log-level=3") 
        # self.chrome_options.add_experimental_option("excludeSwitches", ["enable-logging"])
        # self.chrome_options.add_argument("--headless=new") #le clique vers eloha semble e pas marche si headless

        # 01 06 2026 : optimisation car sur serveur, aujourd'hui ça a capté des erreurs lorsque ça passe dans la deuxième page de réservation
        user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36',
        ] 
                
        self.chrome_options.add_argument("--disable-geolocation")
        self.chrome_options.add_argument('--disable-fingerprinting')
        self.chrome_options.add_argument('--disable-blink-features=AutomationControlled')
        self.chrome_options.add_argument("--enable-javascript")
        self.chrome_options.add_argument('--log-level=3') 
        self.chrome_options.add_argument(f"user-agent={random.choice(user_agents)}") #décommenter ça aussi car sinon meme user agent
        self.chrome_options.add_experimental_option("prefs", pas_image)
        self.chrome_options.add_argument('--ignore-certificate-errors')
        self.chrome_options.add_argument('--disable-gpu')
        self.chrome_options.add_argument('--incognito')
        self.chrome_options.add_argument("--no-sandbox")
        self.chrome_options.add_experimental_option("excludeSwitches", ["enable-logging"])

        self.data_container = []
        self.count_url_no_price = 0
        self.recheck = True
        #03 02 2026 : utiliser pour checker le container d'offre car parfois il n'existe pas si pas de réservation dispo à une date pour une fréquence donnée
        self.check_big_container = True
        self.count_refresh = 10

    def checkin_log_file(self) -> dict:
        self.log_output_path = f'{OUTPUT_LOGS_PATH}{self.week_scrap.strftime("%d-%m-%Y").replace("-", "_")}/'
        self.log_file_name = f'{self.log_output_path}log_{self.name_of_file_output}.json'
        if not os.path.exists(self.log_output_path):
            os.makedirs(self.log_output_path)
            print('                 ')
            print('Dossier de logs créé. Création du fichier de log')
        elif not os.path.exists(self.log_file_name) and os.path.exists(self.log_output_path):
            log = {"last_index_url_scraped":0, "week_scrap":self.week_scrap.strftime("%d/%m/%Y")}
            with open(self.log_file_name, 'w', encoding='utf-8') as log_file:
                json.dump(log, log_file, ensure_ascii=False, indent=4)
            print('Fichier de log créé.')
            with open(self.log_file_name, 'r', encoding='utf-8') as log_file:
                return json.load(log_file)
        else:
            with open(self.log_file_name, 'r', encoding='utf-8') as log_file:
                return json.load(log_file)

    def update_log_file(self, log_file : dict):
        try:
            #tokony ity 05 01 2025
            if os.path.exists(self.log_file_name):
                log = {"last_index_url_scraped":log_file['last_index_url_scraped'], "week_scrap":log_file['week_scrap']}
                with open(self.log_file_name, 'w', encoding='utf-8') as log_file:
                    json.dump(log, log_file, ensure_ascii=False, indent=4)
        except Exception as e:
            print("                ")
            print(f'Erreur lors de la mise à jour du fichier de log: {e}, stopper, vérifier et relancer ')
            input("                ")
        
    def load_destination_file(self) -> list:
        output_path_dest = f'{OUTPUT_PATH_DEST}{self.week_scrap.strftime("%d-%m-%Y").replace("-", "_")}/'
        dest_file_name = f'{output_path_dest}{self.name_of_destination_file}.json'
        try:
            with open(dest_file_name, 'r', encoding='utf-8') as dest_file:
                urls = json.load(dest_file)
            print('> > > Fichier de destination chargé.')
            print('                  ')
            return urls
        except Exception as e:
            print("                ")
            input(f'Erreur lors du chargement du fichier de destination: {e},stopper, vérifier le fichier et relancer ')

    def start_driver(self,): #19 01 2026 , utilise pour l'utilisation de profile car sinon chrome essayera de créer un driver à chaque boucle pour un profil, impossible
        if SYSTEM == "windows":
            self.driver = webdriver.Chrome(options=self.chrome_options)
        if SYSTEM == "linux":
            self.driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()),options=self.chrome_options)
        self.driver.maximize_window()

    def goto_resa_page(self, url: str):
        time.sleep(randint(2,4))
        self.driver.get(url)
        time.sleep(randint(1,2))

    def save_in_csv(self):
        output_path_results = f'{OUTPUT_RESULTS_PATH}{self.week_scrap.strftime("%d-%m-%Y").replace("-", "_")}/'
        results_file_name = f'{output_path_results}{self.name_of_file_output}.csv'
        #créer si le sossier n'existe pas
        if not os.path.exists(output_path_results):
            os.makedirs(output_path_results)
            print('Dossier de résultats créé.')
        if not os.path.exists(results_file_name):
            try:
                with open(results_file_name, 'a', newline='', encoding='utf-8') as csvfile:
                    writer = csv.DictWriter(csvfile, fieldnames=FIELD_NAMES)
                    writer.writeheader()
                    writer.writerows(self.data_container)
                    print("                 ")
                    print('Save successful.')
            except Exception as e:
                print("                ")
                input(f'Erreur lors de la création du fichier de résultats: {e}, stopper, vérifier et relancer ')
        else:
            try:
                with open(results_file_name, 'a', newline='', encoding='utf-8') as csvfile:
                    writer = csv.DictWriter(csvfile, fieldnames=FIELD_NAMES)
                    writer.writerows(self.data_container)
                print("                 ")
                print('Save successful.')
            except Exception as e:
                print("                ")
                input(f'Erreur lors de l\'ajout des données au fichier de résultats: {e}, stopper, vérifier et relancer ')

        #vider la variable data_container après chaque sauvegarde
        self.data_container = []

    def save_url_incomplete_data_resanc(self, url_data : dict):
        output_path_incomplete = f'{OUTPUT_PATH_INCOMPLETE}{self.week_scrap.strftime("%d-%m-%Y").replace("-", "_")}/'
        incomplete_file_name = f'{output_path_incomplete}incomplete_{self.name_of_file_output}.json'
        #créer si le sossier n'existe pas
        if not os.path.exists(output_path_incomplete):
            os.makedirs(output_path_incomplete)
        try:
            if os.path.exists(incomplete_file_name):
                #si le fichier existe déjà, on ajoute les nouvelles données à la suite
                with open(incomplete_file_name, 'r', encoding='utf-8') as f:
                    existing_data = json.load(f)
                #ajout dees nouvelles données en forme de liste de dictionnaire (amzay tsy manisy crochet manuel otran edomizil)
                existing_data.append(url_data)
                #écriture des données mises à jour dans le fichier
                with open(incomplete_file_name, 'w', encoding='utf-8') as f:
                    json.dump(existing_data, f, ensure_ascii=False, indent=4)
            else:
                with open(incomplete_file_name, 'w', encoding='utf-8') as f:
                    json.dump([url_data], f, ensure_ascii=False, indent=4)
            
        except Exception as e:
            print("                ")
            print(f'Erreur lors de la sauvegarde des URL avec données incomplètes: {e}, stopper, vérifier et relancer ')
            input("                ")

    def get_history_index(self) -> None:
        self.log_file = self.checkin_log_file()

    def set_history_index(self, index : int):
        
        self.log_file['last_index_url_scraped'] = index + 1
        self.update_log_file(self.log_file)

    def extract_data(self, datas : list):
        print('                 ')
        print('> > > Extraction des données')
        #format de fichier liste de dictionnaire [{checkin : , checkout: , url: }]

        #un seul driver pour toute la boucle 19 01 2026
        self.start_driver()

        for index_dest in range(self.log_file["last_index_url_scraped"], len(datas)):
            #on lit le dest puis à la fin de chaque itération de notre boucle, on mettra à jour le fichier de log 
            #rehefa tsy vakiana à chaque itération le log_file dia tsy poinsa, mila mjery solution hoe tsy hamakiana azy nefa mba tsy hinana memoire

            print(f'> > > Url {self.log_file["last_index_url_scraped"] + 1} / {len(datas)} / checkin_date = {datas[index_dest]["checkin"]} / checkout_date = {datas[index_dest]["checkout"]}')
            self.goto_resa_page(datas[index_dest]["url"])
            input(f'check url = {datas[index_dest]["url"]}')

            #02 01 2026 : La paillote génère une erreur lors du passage dans eloha, donc pour l'instant on va le sauter (j'ai tester à plusieurs reprise mais error à chaque fois)
            if "paillotes" in str(datas[index_dest]["url"]):
                print("                 ")
                print(f'> > > La paillote génère une erreur lors du passage dans eloha, skip et passer à la suivante')
                print("                 ")
                self.set_history_index(self.log_file['last_index_url_scraped'])
                continue

            #extraction proprement dite 05 01 2026
            soupe = BeautifulSoup(self.driver.page_source.encode('utf-8').decode('utf-8'), 'html.parser')

            try:
                container_offres = soupe.find('div', {'class':'bloc sit-tarifs'}) #existe meme si pas de typo et de prix sur eloha
                offres_chambres_dispo = container_offres.find_all('li', {'class':'item-row'})
            except Exception as e:
                #05 02 2026 : sur serveur , page introuvable rencontré pour un url, on va gérer ici car c'est ici que ça entre
                check_page_introuvable = soupe.find("h1", string=re.compile("Page non trouvée", re.IGNORECASE))
                if check_page_introuvable != None:
                    print("                 ")
                    print(f'********Page introuvable pour l\'url {datas[index_dest]["url"]}, skip et passer à la suivante')
                    print("                 ")
                    self.set_history_index(self.log_file['last_index_url_scraped'])
                    continue
                else:
                    input(' Le tag container n\'existe pas, check selecteur sur navigateur et relancer ')
            
            # print(f'Nombre d\'offres trouvées: {len(offres_chambres_dispo)} pour l\' url {datas[index_dest]["url"]}') PAs besoin car on ne prend plus dans resa.nc
            if len(offres_chambres_dispo) == 0:
                self.save_url_incomplete_data_resanc(datas[index_dest]['url'])
                self.count_url_no_price += 1

                #Reflexion le 07 01 2026 : mettre quand même les données incompletes dans le csv avec les autres données (checkin, checkout, date_price, week_number) mais sans price et typology)
                #on predn les nom et locality dans resa et on complete les prix et typo dans eloha
                try:
                    container_name_localite = soupe.find('div', {'class':'panel-reservation__heading'})
                except:
                    input('Check selector, container name localite not found')
                try:
                    nom = container_name_localite.find('h1').text.strip()
                except:
                    input('Check selector, nom not found')
                    pass
                try:
                    #remise pour seulement le NOM DE VILLE 20 01 2026 par demande de Nicolas
                    localite = container_name_localite.find('span', {'class':'location --size-big'}).text.strip()
                    #si jamais on aura besoin de l'adresse complete (19 01 2026)
                    # localite = self.driver.find_element(By.CLASS_NAME, 'contact-adress__text').text.strip().replace(',','')
                except:
                    input('Check selector, localite not found')

                #Reflexion du 09 01 2026 , plusieurs des pages resanc aujourd'hui CE JOUR , n'affichent plus de typo ni de prix donc j'opte pour eloha
                # self.close_cookies()
                self.go_to_eloha_website(nom)
                #16 01 2025 : button go to eloha inexistant
                if self.recheck == True:
                    self.switch_window()
                    self.open_filter_popup_in_eloha()
                    #pour eloha on n'a besoin que du checkin car on selectionne le nombre de nuit par un select , on a besoin du -r ou bien on l'extrait du -d nom du dest
                    check_dispo = self.filter_eloha(datas[index_dest]['checkin'], self.name_of_destination_file, nom) #retourne un bool pour disponibilité ou pas
                    #ce if le 17 02 2026
                    if check_dispo == True:
                        #24 02 2026
                        self.currency_choice()
                        #21 01 2026
                        self.extract_in_eloha(check_dispo, nom, localite, datas, index_dest) #tout se fera dans extract eloha car 21 01 2026 j'au=i aperçu d'autre typologie en ouvrant un établissement par hasard

                #fin reflexion 07 01 2026

            else: #si par chance les typologies réapparaissent sur resa.nc
                #09 01 2026 mettre pass car on ne va pas utiliser les infos du resanc meme si il y en a
                # for offre in offres_chambres_dispo:
                #     try:
                #         typology = offre.find('strong').text.strip() + ' ' + offre.find('span', {'class':'sit-tarifs__offer-description'}).text.strip()
                #         # input(f'Typology found: {typology}')
                #     except:
                #         input('Check selector, typology not found')
                #     try:
                #         #Demande du 06 01 2026 : récupérer la currency aussi
                #         price_with_currency = offre.find('span', {'class':'item-row__value sit-tarifs__offer-price'}).text.strip().replace(' ','')
                #         if 'XPF' in price_with_currency:
                #             price = price_with_currency.replace('XPF','')
                #             currency = 'XPF'
                #         elif ('EUR' or 'eur' or 'euro' or 'euros') in price_with_currency:
                #             price = price_with_currency.replace('EUR','').replace('eur','').replace('euro','').replace('euros','')
                #             currency = 'EUR'
                #         else:
                #             price = price_with_currency
                #         # input(f'Price found: {price_with_currency} / Price only: {price} / Currency only: {currency}')
                #     except:
                #         input('Check selector, price not found')
                #     try:
                #         container_name_localite = soupe.find('div', {'class':'panel-reservation__heading'})
                #     except:
                #         input('Check selector, container name localite not found')
                #     try:
                #         nom = container_name_localite.find('h1').text.strip()
                #     except:
                #         input('Check selector, nom not found')
                #         pass
                #     try:
                #         localite = container_name_localite.find('span', {'class':'location --size-big'}).text.strip()
                #     except:
                #         input('Check selector, localite not found')        

                #     # input(f'Nom found: {nom} / Localite found: {localite} / Typology found: {typology} / Price found: {price}')

                #     self.data_container.append({
                #         'date_price' : self.week_scrap.strftime('%d/%m/%Y'),
                #         'checkin' : datas[index_dest]['checkin'],
                #         'checkout' : datas[index_dest]['checkout'],
                #         'price' : price,
                #         'currency' : currency,
                #         'typology' : typology,
                #         'name' : nom,
                #         'locality' : localite,
                #         'week_number' : datetime.strptime(datas[index_dest]['checkin'], '%d/%m/%Y').isocalendar()[1]
                #     })

                #     self.save_in_csv()
                pass
            #fin reflexion 09 01 2026

            self.set_history_index(self.log_file['last_index_url_scraped'])
            time.sleep(randint(2,4))

            #24 02 2026 : fermer l'onglet mère
            self.close_old_windows_after_extract()
    
    #09 01 2026
    def close_cookies(self,):
        time.sleep(1)
        while self.recheck:
            try:
                self.driver.find_element(By.XPATH, '/html/body/div[8]/div[3]/button[1]').click() #full xpath amzay tsy mila id class fa miova le anaran ireo fa rehefa full dia ilay element no
                print('Cookies closed')
                self.recheck = False
                break #09 01 2026
            except:
                time.sleep(0.5)
                print('recheck cookies')
                pass
    
    #09 01 2026
    def go_to_eloha_website(self, etablissement):
        self.recheck = True #car a été mis False dans le close cookies
        while self.recheck:
            try:
                #16 01 2026 : ce button go to eloha peut ne jamais exister (comme l'établissement Betikura), donc on ajoute une condition pour gérer
                button_exist = WebDriverWait(self.driver, 8).until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, 'span[class="title-reservation"]')) #button go eloha container, ça existe toujours si le site le propose
                )
                if button_exist:
                    time.sleep(2) #pour être sûr que le button soit là
                    # print('Button to eloha found')
                    button_to_eloha = self.driver.find_element(By.CSS_SELECTOR, 'button[id="BtnLaunchBooking"]')
                    try:
                        button_to_eloha.click()
                        time.sleep(randint(2,4))
                        self.recheck = True #pour la suite du process cet non pour cette boucle, d'ailleur, on break
                        break #09 01 2026
                    except:
                        try:
                            #16 01 2026
                            time.sleep(2,4)
                            #17 02 2026 : on le fait avec JS
                            self.driver.execute_script("arguments[0].click();",button_to_eloha)
                            time.sleep(randint(2,4))
                            self.recheck = True #pour la suite du process cet non pour cette boucle, d'ailleur, on break
                            break
                        except:
                            print('Button found but not clickable, recheck.')
                            time.sleep(uniform(0.5,1.5))
                            self.recheck = True
            except:
                print("                 ")
                print(f'> > > {etablissement} ne possède pas de lien vers le site de réservation, break et saut.')
                print("                 ")
                self.recheck = False #pour la suite et no pour cette boucle
                break
    #16 01 2026 séparé de open filtre car besoin de relancer la fonction open parfois
    def switch_window(self,):
        # print(f'liste des fenetres ouvertes => {self.driver.window_handles}')
        if len(self.driver.window_handles) > 1:
            self.driver.switch_to.window(self.driver.window_handles[1])
            print('> > > Switched to the new window eloha website')
            time.sleep(randint(2,4))
            #normalement nous sommes sur l'onglet voulu
    
    #24 02 2026 : Ne fermer l'onglet mère qu'après l'extraction, peut être est ce la cause des not recognise parfois car je ferme trop rapidement
    def close_old_windows_after_extract(self,):
        if len(self.driver.window_handles) > 1:
            self.driver.close()
            time.sleep(randint(2,3))
            self.driver.switch_to.window(self.driver.window_handles[0])

    #09 01 2026
    def open_filter_popup_in_eloha(self):
        try:
            #14 01 2026 un peu de time car il me semble trop rapide lors du monitoring sur navigateur
            time.sleep(randint(4,6))
            self.recheck = False
            #16 01 2026
            while self.recheck == False:
                try:
                    button_filter_exist = WebDriverWait(self.driver, 10).until(
                        EC.element_to_be_clickable((By.XPATH, '/html/body/div[4]/div/div[2]/button'))
                        # EC.element_to_be_clickable((By.CSS_SELECTOR, 'div.new-main-resume  bg-primary w-100p with-pax > button[data-target="#SearchModal"]'))
                    )
                    # input(f'valeur bouton filter exist => {button_filter_exist}')
                    if button_filter_exist:
                        break
                except:
                    print('Page non chargé, refresh')
                    self.driver.refresh()
                    return self.open_filter_popup_in_eloha() #12 02 2026 , oublié

            button_filtre_on_eloha = self.driver.find_element(By.XPATH, '/html/body/div[4]/div/div[2]/button')
            button_filtre_on_eloha.click()
            time.sleep(uniform(3.2,4.9))
            # print('Button eloha filtre clicked')
        except Exception as e:
            print(f'Button eloha filtre not found, refresh current page -> {e}')
            self.driver.refresh()
            return self.open_filter_popup_in_eloha()

    def filter_eloha(self, checkin_date, name_file_dest_to_split, etablissement) -> bool: #j'ai mis explicitement le second variable comme ça pour ne pas oublier
        #on donne toujours un str dans un value en html
        checkin = checkin_date
        checkout = name_file_dest_to_split.split('t')[1] #ça va prendre la fréquence de jour de réservation
        self.driver.execute_script(f"document.getElementById('StartDate').value='{checkin}';")
        print(f'Date checkin {checkin} entrée avec succès ')

        time.sleep(uniform(2.4,3.5))

        #mamapiasa import hafa mihitsy selenium am select
        select_checkout = Select(self.driver.find_elements(By.ID, 'Duration')[0]) #misy 2 ao anatin'ny page ao , raha full xpath = "/html/body/div[5]/div/div/div[2]/form/div/div[4]/div[1]/div[2]/div/select"
        select_checkout.select_by_value(checkout)
        print('         ')
        print(f'Date checkout entrée avec succès ')

        #ilay nombre de personne aleo atao 1 foana aloha comme pour les scrap de maeva, sns, 2 no ao am resa eloha par defaut dia atao 1 , ahena tsindriaa ilay button
        try:
            change_nb_room_container = self.driver.find_elements(By.CSS_SELECTOR, 'span[class="input-group-btn nb-room"]')[0]
            change_nb_room_container.find_element(By.TAG_NAME, 'button').click()
            # print('Mofidier cliqué')
            time.sleep(uniform(2.4,3.5))
            # change_nb_room = driver.find_elements(By.CSS_SELECTOR, 'input[name="AdultNumber0"]')[0]
            try:
                change_nb_room = self.driver.find_elements(By.CSS_SELECTOR, 'input[name="AdultNumber0"]')[0].get_attribute('value')
                # print(f'nb personne actuel{change_nb_room}')
                change_nb_room = int(change_nb_room)
            except Exception as e:
                input(f'Erreur check nb personnes => {e}')
            if change_nb_room > 1:
                try:
                    button_to_substract = self.driver.find_elements(By.CSS_SELECTOR, 'button[class="bg-primary input-number-substract"]')[0] #il y en a 4 selecteur et le premier est ce dont on a besoin
                    button_to_substract.click()
                    print('Nb personne modifié')
                    time.sleep(uniform(1.1,3.1))
                except:
                    input('Erreur soustraction nb personne')
        except:
            input('Modifié non cliqué')

        time.sleep(uniform(1.1,2.1))
        try:
            #button rechercher après avoir filtrer
            go_filter_button = self.driver.find_element(By.CSS_SELECTOR, 'input[value="RECHERCHER"]')
            go_filter_button.click()
            # print('filtre cliqué')
            time.sleep(uniform(1.1,3.1))
        except Exception as e:
            input('Erreur de clique sur le go_filter_button, donc aucun filtre appliqué, CHECK')
            sys.exit("Arret depuis go_gilter_button click dans filter eloha()")

        #resultat de la recherche , tadidio tsara fa raha xx/xx/xxxx no format izany hoe 4 chiffres ilay année dia %Y en grand Y ilay année sinon erreur
        try:
            self.driver.find_element(
                By.XPATH,
                "//div[contains(., 'Aucune disponibilité')]" #. estplus flexible que text() si jamais il y a un span dans le div par exemple
            )
            print("                 ")
            print(
                f"Pas de disponibilité pour {etablissement} pour la date {checkin} "
                f"jusqu'au {datetime.strftime(datetime.strptime(checkin, '%d/%m/%Y') + timedelta(days=int(checkout)),'%d/%m/%Y')}"
            )
            return False

        except NoSuchElementException:
            try:
                self.driver.find_element(
                    By.XPATH,
                    "//div[contains(., \"L'établissement n'est pas disponible\")]"
                )
                print("                 ")
                print(
                    f"Pas de disponibilité pour {etablissement} pour la date {checkin} "
                    f"jusqu'au {datetime.strftime(datetime.strptime(checkin, '%d/%m/%Y') + timedelta(days=int(checkout)),'%d/%m/%Y')}"
                )
                return False

            except NoSuchElementException:
                print("                 ")
                print(
                    f"{etablissement} est disponible pour la date {checkin} "
                    f"jusqu'au {datetime.strftime(datetime.strptime(checkin, '%d/%m/%Y') + timedelta(days=int(checkout)),'%d/%m/%Y')}"
                )
                print("                 ")
                return True
    
    #24 02 2026 : séparer le check currency pour essayer de gérer les coupures not recognize
    def currency_choice(self,):
        #la devise
        try:
            list_currency = self.driver.find_element(By.CSS_SELECTOR, "div.btn-currency div.dropdown")
            list_currency.click()
            print('Menu currency clicked')
            time.sleep(1.2)
            select_currency = self.driver.find_element(By.CSS_SELECTOR, "ul.dropdown-menu-devise li[data-devise='XPF']") #demande 02 02 2026 19h50
            select_currency.click()
            print('XPF clicked')
            self.currency = "XPF"
            time.sleep(uniform(2.1,3.2)) #chargement
        except:
            #17 02 2026
            try:
                print('Currency menu not clicked ou XPF not clicked, refresh')
                #16 02 2026 : la page a besoin d'unn refresh 
                print('refresh de la page car probablement => error module does not recognize this error rencontré')
                self.driver.refresh() #les dates en paramètres sont retenus j'ai regardé et vérifier, le currency XPF aussi
                time.sleep(1)
                self.driver.refresh() #oui une deuxième fois
                time.sleep(uniform(2.1,2.5))
                return self.currency_choice()
            except:
                print('XPF non enregistré encore, il se peut que XPF ne soit pas cliqué')
                soup = BeautifulSoup(self.driver.page_source, "html.parser")
                print(f'Voici ce qui est affiché dans le body au moment de l\'erreur -> {soup.find("body").get_text(strip=True)}') #là on voit mieux si c'est du module not recognize
                sys.exit('STOP , CHECK NAVIGATEUR si non fermé')
    
    def extract_in_eloha(self, check_dispo : bool, nom, localite, datas, index_for_datas):
        #selecteur price, topology, name, locality, currency
        if check_dispo:
            #nouvel résolution 25 02 2026  
            while True:
                soup = BeautifulSoup(self.driver.page_source, "html.parser")

                body_text = soup.find("body").get_text(strip=True)

                if body_text == "The custom error module does not recognize this error.":
                    print(f"Vue erreur détectée pour {nom}, refresh")
                    self.driver.refresh()
                    time.sleep(2)
                    continue   

                big_container_offer = soup.find('div', {'class': 'offer-list offer-list0 last m-top-30'})

                if big_container_offer == None:
                    if soup.find("div",string=re.compile("la durée minimum", re.IGNORECASE)) != None: #c'est ce qui contient l'offre en temps normal , si c'est None, cela peut dire que la date de réservation inférieur à nos dates entrée ne peut pas être effctuée pour cet établissement
                        no_reservable = soup.find("div",string=re.compile("la durée minimum", re.IGNORECASE))
                        # if no_reservable != None:
                        print(no_reservable.text, "pour", nom)
                        self.check_big_container = False
                        break
                        
                        # if no_reservable == None: #si je met ça , ça sera deux check double car la vue erroné est déja traité par le if body_text
                        #     print("No reservable non trouvé, pas normal, on refresh")
                        #     self.driver.refresh()
                        #     time.sleep(2)
                        #     continue
                    #25 02 2026 : normalement , c'est le cas où le selecteur est obsolète, car si le programme entre dedans et que la vue n'a plus de This custom... , donc c'est bon, on peut gérer maintenant le cas d'un selecteur
                    elif soup.find("div",string=re.compile("L'établissement n'est pas disponible", re.IGNORECASE)) != None: #ça revient ici, d'après ce que j'ai pu voir sur serveur
                        print(f'Pas de disponibilité pour {nom} pour les dates entrées')
                        self.check_big_container = False
                        break
                    elif soup.find("div",string=re.compile("Aucune disponibilité", re.IGNORECASE)) != None: #ça revient ici, d'après ce que j'ai pu voir sur serveur
                        print(f'Pas de disponibilité pour {nom} pour les dates entrées')
                        self.check_big_container = False
                        break
                    else:
                        input('Check navigator, le selecteur de big_container_offer a peut être changé')
                # si l'offre est bien visible
                if big_container_offer != None:
                    self.check_big_container = True
                    break

            #A partir d'ici safe, jamais eu de coupure, sauf selecteur changé
            if self.check_big_container == True:
                #MAJ pour 26 01 2026
                #NB : le premier div est à exclure d'après ce que j'ai vu car c'est CHoisir qu'il y a dedans
                container_offer = big_container_offer.find_all('div', {'class' : 'offer'})
                print(f'- > {len(container_offer)} typologie(s) trouvé(s) pour {nom} ')
                for offer in container_offer:
                    attribut_of_offer = offer.attrs
                    # input(f'les attribut du div => {attribut_of_offer}')
                    try:
                        typology_name = attribut_of_offer['data-track-product-name']
                        details_typology = offer.find('span', {'class' : 'bedding-resume'}).text
                        details_typology = details_typology.replace(',',' ') #pour le csv
                        typology = typology_name + " - " + details_typology
                    except:
                        input('Selecteur typology not found')
                    try:
                        price = attribut_of_offer['data-track-product-price'] #en str avec virgule

                        price = price.replace(',','.') #pour le csv
                    except:
                        input('Selecteur price not found')
                    print(f"> > > Name = {nom} Typology = {typology} | Price = {price} | Currency = {self.currency} < < <")

                    #normalisation avec les g2a , donc on met meme les champs qui seront vides (par demande du 15 01 2026)
                    self.data_container.append({
                        'web-scraper-order': '',
                        'date_price' : self.week_scrap.strftime('%d/%m/%Y'),
                        'date_debut' : datas[index_for_datas]['checkin'],
                        'date_fin' : datas[index_for_datas]['checkout'],
                        'prix_init' : price if  price else 'undefined',
                        'prix_actuel' : price if price else 'undefined',
                        'currency' : self.currency if self.currency else 'undefined',
                        'typologie' : typology if typology else 'undefined',
                        'n_offre': '',
                        'nom' : nom,
                        'localite' : localite,
                        'date_debut-jour': '',
                        'Nb semaines' : datetime.strptime(datas[index_for_datas]['checkin'], '%d/%m/%Y').isocalendar()[1]
                    })
                    self.save_in_csv()

    def execute(self):
        print('> > > Starting ResaNc scraper ')
                                                                                                                                                                                                                                                                                                                                                                                                                                                              
        print(' Step 1  ')
        #self car j'en ai besoin dans le rappel dans la condition après menu currency cliekd si jamais la pafge ne charge pas
        self.urls_and_dates = self.load_destination_file() #format de fichier liste de dictionnaire [{checkin : , checkout: , url: }]

        print(' Step 2  ')
        print('> > > Chargement des logs ... ')
        self.checkin_log_file()

        print(' Step 3  ')
        self.get_history_index()
        self.extract_data(self.urls_and_dates)

        print('                 ')
        print(f'> > > ResaNc Scraper finished avec succès. Nombre d\'hébergement sans prix: {self.count_url_no_price} ')

        self.driver.quit() #sur linux, cette instruction ne tue pas le driver immédiatement, donc ajoutons un sleep 19 01 2026

        time.sleep(5)