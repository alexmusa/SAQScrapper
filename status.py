class Status:
    """
    Status de l'execution du script

    Attributs:
    state -- état du script
    beginDate -- date de lancement du script
    endDate -- date fin du script. nulle si non terminée
    position -- position du script dans le catalogue

    Les differents états du script sont
    STARTING
    RUNNING
    FINISHED
    """
    state = ""
    beginDate = None
    endDate = None
    position = 0