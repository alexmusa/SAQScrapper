class Product:
    """Produit de la SAQ"""
    code_SAQ = ""
    code_CUP = ""
    name_ = ""
    type_ = ""
    infos = []

    def __init__( self, code_SAQ, code_CUP, name_, type_, paragraphe ):
        self.code_SAQ = code_SAQ
        self.code_CUP = code_CUP
        self.name_ = name_
        self.type_ = type_
        self.infos = []
        if paragraphe:
            self.infos.append(["Paragraphe", str(paragraphe)])

    def add_info( self, info):
        self.infos.append(info)