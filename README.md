******
Pour lancer les commandes, il faut se situer à l'extérieur du dossier du projet "resanc"
Commandes :
1 - Initialisation : python3 resanc/ -a init -r "fréquences de réservation" -w "semaine de scrap" -e "date de fin de scrap"
-a : choix de l'action à faire, ici c'est init car on est dans l'initialisation
-r : fréquence de réservation en jour, valeur acceptée : 1,3 ou 7
-w : semaine de scrap, toujours un lundi. Par contre, parce que c'est une initialisation et qu'avec resa nc les dates déja passées n'afficheront aucuns résultats donc dans le programme ça initialise automatiquement à partir du jour même. La date donnée pour -w est surtout utilisé pour le nommage du dossier qui va contenir les destinations initialisées. Format : xx/xx/xxxx
-e : date de fin de scrap, extension du scrap : ça sera la date jusqu'à laquelle on scrap les données

Détails : cette commande effectuera l'extraction des urls des établissements qui sont affichés en statut disponible pour les fréquences de dates données avec le paramètre -r, si c'est "1" ça extraira les urls des établissements disponibles pour des réservations de 1 jour à partir du jour de lancement de la commande et ainsi de suite en suivant l'intervalle de 1 jour jusqu'à la date donnée en paramètre -e. 
Ces urls seront stockés dans le dossiers dests/ et classés dans un fichiers contenus dans un dossier portant comme intitulé par la date donné par le paramètre -w (voir le chemin complet dans le fichier .env)

2 - Démarrage : python3 resanc/ -a start -d "fichier_contenant_url_destination" -n "fichier_sortie_résutlat" -w "semaine de scrap" 
-a : choix de l'action à faire, on est dans le start
-d : fichier contenant les urls de destination initialisé par la commande init (selon les fréquences de jour)
-n : nom qui sera donné au fichier de sortie qui contiendra les résultats issus du fichier de dest
-w : semaine du scrap, toujours un lundi, ça sera également le nom du dossier qui contiendra les résultats

Détails : cette commande effectuera l'extraction des données depuis la page des établissements enregistrés dans le fichier de dest.
******