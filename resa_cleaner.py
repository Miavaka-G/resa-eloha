import pandas as pd
import csv
import os, json
from dotenv import load_dotenv

load_dotenv()
OUTPUT_RESULTS_PATH = os.getenv('OUTPUT_RESULTS_PATH')

#16 01 2026 : normalisation des nom des headers avec g2a
class resa_cleaner:
    def __init__(self, name: str, week_scrap: str):
        self.name = name
        self.week_scrap = week_scrap

    def load_result_file(self,):
        print('- > Load du fichier de résultats')
        try:
            full_result_file_path = f"{OUTPUT_RESULTS_PATH}{self.week_scrap.replace('/','_')}/{self.name}.csv"
            self.df_results = pd.read_csv(full_result_file_path)
        except Exception as e:
            input(f"Erreur lors du chargement du fichier de résultats : {e}, stopper et verifier le chemin et le nom du fichier.")

    def remove_duplicate(self,):
        print('- > Suppression des doublons')
        try:
            self.df_results.drop_duplicates(inplace=True,subset=['date_debut','date_fin','prix_init','prix_actuel','currency','typologie','nom','localite','Nb semaines'])
        except Exception as e:
            input(f"Erreur lors de la suppression des doublons : {e}, stopper et verifier le fichier de résultats.")

    def sort(self,):
        print('- > Tri par le checkin date')
        try:
            #avant mila atao datetime ny checkin satria str izy izao
            self.df_results['date_debut'] = pd.to_datetime(self.df_results['date_debut'], format='%d/%m/%Y')
            self.df_results.sort_values(by=['date_debut'], inplace=True)
            #averina amin'ny str indray ny checkin aorian'ny tri
            self.df_results['date_debut'] = self.df_results['date_debut'].dt.strftime('%d/%m/%Y')
        except Exception as e:
            input(f"Erreur lors du tri par le checkin date : {e}, stopper et verifier le fichier de résultats.")

    def remove_comma(self,):
        print('- > Suppression des virgules dans les champs texte')
        try:
            cols = ['nom','localite','typologie','prix_init','prix_actuel']
            self.df_results[cols] = self.df_results[cols].apply(lambda col : col.astype(str).str.replace(',','', regex=False))
        except Exception as e:
            input(f"Erreur lors de la suppression des virgules dans les champs texte : {e}, stopper et verifier le fichier de résultats.")

    def remove_entries_with_undefined_values(self,):
        print('- > Suppression des lignes avec les valeurs UNDEFINED inscrites dans leur colonne')
        try:
            self.df_results = self.df_results[self.df_results['prix_init'] != 'undefined']
        except Exception as e:
            input(f"Erreur lors de la suppression des lignes avec les valeurs UNDEFINED inscrites dans leur colonne : {e}, stopper et verifier le fichier de résultats.")   

    def save(self,):
        print('- > Sauvegarde du fichier nettoyé')
        try:
            self.df_results.to_csv(f"{OUTPUT_RESULTS_PATH}{self.week_scrap.replace('/','_')}/{self.name}_cleaned.csv", index=False)
        except Exception as e:
            input(f"Erreur lors de la sauvegarde du fichier nettoyé : {e}, stopper et verifier le chemin et le nom du fichier.")

    def execute(self,):
        print(f"----> Nettoyage des résultats pour le fichier {self.name} de la semaine {self.week_scrap}")
        self.load_result_file()
        self.remove_entries_with_undefined_values()
        self.remove_comma()
        self.remove_duplicate()
        self.sort()
        self.save()
        print('----> Nettoyage terminé.')