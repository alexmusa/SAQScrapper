import sqlite3

conn = None

def connect( parameters ):
    try:
        conn = sqlite3.connect('test.db')

        cur = conn.cursor()
        cur.execute('SELECT SQLITE_VERSION()')

        data = cur.fetchone()

        print("SQLite version: %s" % data)
        print("Connecté à la base de donnée :D")
        return True

    except sqlite3.Error as err:

        print("Error %s:" % err.args[0])
        return False

def add( product ):
    try:
        cur = conn.cursor()
        ### Vérifie que toutes les colonnes nécessaires existent ###
        cur.execute("SELECT name FROM (PRAGMA table_info('Products')) AS Columns")

        columns = cur.fetchall()
        for info in product.infos:
            if all(column != info[0] for column in columns):
                cur.execute('ALTER TABLE Products ADD COLUMN' + info[0] + ' text')

        ### Crée la requête pour enregistrer le produit ###
        # Réécrire toute les concaténation de manière plus élégante
        query = 'INSERT INTO table_name(CodeSAQ, CodeCUP, Name, Type'

        for info in product.infos:
            query += ', ' +  info[0]

        query += ') VALUES("' + product.code_SAQ \
                 + '", "' + product.code_CUP \
                 + '", "' + product.name_ \
                 + '", "' + product.type_

        for info in product.infos:
            query += '", "' + info[1]

        query += '")'

        cur.execute(query)
        return True

    except sqlite3.Error as err:
        print("Error %s:" % err.args[0])
        return False


def initialize( parameters ):
    try:
        cur = conn.cursor()
        cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='Products'")

        # "EXISTS(SELECT * "
        # "FROM INFORMATION_SCHEMA.TABLES "
        # "WHERE TABLE_NAME = 'Products')"

        exists = cur.fetchone()
        if not exists:
            print("La table n'existe pas dans la base de données. Elle va être créé.")
            #cur = conn.cursor()
            cur.execute("CREATE TABLE Products (ProductID int, "
                        "CodeSAQ text, "
                        "CodeCUP text, "
                        "Name text, "
                        "Type text )")
        else:
            print("La table existe déjà dans la base de données.")
        return True

    except sqlite3.Error as err:
        print("Error %s:" % err.args[0])
        return False

def save( parameters ):
    try:
        conn.commit()
        return True

    except sqlite3.Error as err:
        print("Error %s:" % err.args[0])
        return False


def close( parameters ):
    try:
        conn.close()
        return True

    except sqlite3.Error as err:
        print("Error %s:" % err.args[0])
        return False
