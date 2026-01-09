from resa_scraper import resa_scraper
from resa_initializer import resa_initializer
from resa_cleaner import resa_cleaner
import argparse

def main_arguments() -> object:
    parser = argparse.ArgumentParser(description = "ResaNc scraper")
    parser.add_argument('--action', '-a', dest='action', required=True, help="Choisir l'action à effectuer : 'start' pour démarrer le scrap, 'init' pour initialiser les hébergements d'une date donnée")
    parser.add_argument('--name', '-n', dest='name', help="Nom du fichier qui va contenir les données d'initialisation ou de scraping")
    parser.add_argument('--reservation', '-r', dest='reservation', type=int, help="Nombre de nuitée à réserver (uniquement pour le scraping)")
    parser.add_argument('--week_scrap','-w', dest='week_scrap', type=str, help="Date du lundi de la semaine à scraper format 'dd/mm/YYYY'")
    parser.add_argument('--end_date_scrap','-e', dest='end_date_scrap', type=str, help="Date de fin de la période à scraper format 'dd/mm/YYYY'")
    parser.add_argument('--dest_file', '-d', dest='dest_file', type=str, help="Chemin du fichier de destination contenant les urls")
    #08 01 2026 clean
    parser.add_argument('--clean', '-c', dest='clean', help="Nettoyage des résultats pour livraison")

    return parser.parse_args()

ARGS_INFO = {
    '-a' : {'acronym':'--action', 'help':"Choisir l'action à effectuer : 'start' pour démarrer le scrap"},
    '-r' : {'acronym':'--reservation', 'help':'Nombre de nuitée à réserver (uniquement pour le scraping)'},
    '-n' : {'acronym':'--name', 'help':'Nom du fichier qui va contenir les données d\'initialisation ou de scraping'},
    '-w' : {'acronym':'--week_scrap', 'help':'Date du lundi de la semaine à scraper format \'dd/mm/YYYY\' , aussi pour la création du dossier de sauvegarde'},
    '-e' : {'acronym':'--end_date_scrap', 'help':'Date de fin de la période à scraper format \'dd/mm/YYYY\''},
    '-d' : {'acronym':'--dest_file', 'help':'Chemin du fichier de destination contenant les urls'},
    '-c' : {'acronym':'--clean', 'help':'Nettoyage des résultats pour livraison'}
}

def check_args_presence(args, required_args: list) -> bool:
    missing = []
    for req_arg in required_args:
        if not getattr(args, req_arg):
            missing.append(f"Argument {ARGS_INFO['-'+req_arg]['acronym']} missing: {ARGS_INFO['-'+req_arg]['help']}")
    return missing

if __name__ == "__main__":
    args = main_arguments()

    if args.action == 'init':
        missing_args = check_args_presence(args, ['reservation', 'week_scrap', 'end_date_scrap'])
        if len(missing_args) > 0: #si il y a des arguments manquants
            raise Exception(f"Les arguments suivants sont manquants :\n" + "\n".join(missing_args))
        else:
            resa_initializer_instance = resa_initializer(
                reservation=args.reservation,
                week_scrap=args.week_scrap,
                end_date_scrap=args.end_date_scrap
            )
            resa_initializer_instance.execute()

    elif args.action == 'start':
        missing_args = check_args_presence(args, ['dest_file', 'name', 'week_scrap'])
        if len(missing_args) > 0: #si il y a des arguments manquants
            raise Exception(f"Les arguments suivants sont manquants :\n" + "\n".join(missing_args))
        else:
            resa_scraper_instance = resa_scraper(
                destination=args.dest_file,
                name=args.name,
                week_scrap=args.week_scrap
            )
            resa_scraper_instance.execute()

    elif args.action == 'clean':
        missing_args = check_args_presence(args, ['name', 'week_scrap'])
        if len(missing_args) > 0: #si il y a des arguments manquants
            raise Exception(f"Les arguments suivants sont manquants :\n" + "\n".join(missing_args))
        else:
            resa_cleaner_instance = resa_cleaner(
                name=args.name,
                week_scrap=args.week_scrap
            )
            resa_cleaner_instance.execute()
    else:
        print("Il faut spécifier une action valide. Utilisez --help pour plus d'informations.")
