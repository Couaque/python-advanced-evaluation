from concurrent.futures import ThreadPoolExecutor
from queue import Queue
import sys
import threading, time, os

def parse_puzzle(puzzle_string, move_count=0):
    """Cette fonction prend en paramètre un string, au format utilisé dans les fichiers samples. Il renvoie un objet State.

    Args:
        puzzle_string (string): La chaîne de caractères brute venant généralement d'un fichier
        move_count (int, optional): Si jamais on veut créer un State qui n'est pas l'ancêtre de tous les autres états on peut choisir cette variable. Defaults to 0.

    Returns:
        State : un objet State, sans parent.
    """
    state = []
    #On sépare les trois lignes au format texte, en trois tuples.
    tmp_array = puzzle_string.split("\n")[0:3]
    for ligne in tmp_array :
        #Chaque tuple possède lui-même trois tuples, correspondants chacun à un chiffre
        state.append(ligne.split(" ")[0:3])
    for i, ligne in enumerate(state) :
        for j, chiffre in enumerate(ligne) :
            #Si le fichier d'input contient un - ou un . à la place d'un 0, on le remplace.
            if chiffre == '-' or chiffre == '.' :
                state[i][j] = '0'
    
    return State(board = state, move_count = move_count)

def parse_file(path):
    """Récupère un chemin vers un fichier pour l'envoyer à parse_puzzle.

    Args:
        path (String): Chemin vers le fichier

    Returns:
        State : un objet State, sans parent.
    """
    inputFile = open(path, "r")
    return parse_puzzle(inputFile.read())

class Position:
    """La classe position contient une coordonnée X et Y. Elle ne sert pas à grand-chose, mais aide le code à être plus lisible.
    """
    def __init__(self, x, y):
        self.x = x
        self.y = y

class State:
    """La classe State contient trois variables permettant de matérialiser un état à un moment donné.
    """
    def __init__(self, board, move_count, previous = None):
        """Constructeur de la classe.

        Args:
            board ([String][String]): Contient l'état actuel du plateau
            move_count (int): Combien de changements ont été nécessaires pour arriver là ?
            previous (State, optional): Contient l'état duquel est issu ce State. Je voulais l'utiliser pour remonter le graphe lors de la sortie dans un fichier. Defaults to None.
        """
        self.board = board
        self.move_count = move_count
        self.previous = previous
    
    def displayBoard(self):
        """Affiche le plateau d'une manière facile à lire pour l'utilisateur. Utile pour le débugging, je comptais l'utiliser pour l'output dans un fichier.
        """
        for ligne in self.board :
            for chiffre in ligne :
                print(chiffre, end='')
                print(" ", end='')
            print("\n", end='')
    
    def returnPos(self, number):
        """Donne la position d'un chiffre en input, dans le board. Utile pour swap deux chiffres du plateau.

        Args:
            number (int): Le chiffre qu'on veut localiser

        Returns:
            Array[int] : Les deux coordonnées d'un chiffre.
        """
        for y in range(0,3) :
            for x in range (0,3):
                if self.board[y][x] == str(number) :
                    return [y, x]
    
    def swapNumber(self, number):
        """Permet d'échanger un chiffre non-nul avec le 0 dans le board.

        Args:
            number (String): Le chiffre à échanger avec le 0.

        Returns:
            [String][String]: Renvoie un board temporaire qui pourra être utilisé plus tard dans d'autres fonctions.
        """
        pos_zero = self.returnPos(0)
        pos_number = self.returnPos(number)
        tmp_board = self.board
        tmp_board[pos_zero[0]][pos_zero[1]], tmp_board[pos_number[0]][pos_number[1]] = tmp_board[pos_number[0]][pos_number[1]], tmp_board[pos_zero[0]][pos_zero[1]]
        return tmp_board

    def manhattan(self):
        """Cette fonction est censée pouvoir renvoyer la distance de manhattan d'un board donné.

        Returns:
            int: Contient la distance de manhattan calculée avec l'algorithme.
        """
        res = 0
        ideal_state  = parse_puzzle("1 2 3 \n4 5 6 \n7 8 0")
        for ligne in self.board:
            for chiffre in ligne :
                #Ici, je comptais faire le calcul suivant : coordonnées de A - coordonnées de B, en valeur absolue
                current_pos = Position(x = self.returnPos(chiffre)[1], y = self.returnPos(chiffre)[0])
                ideal_pos = Position(x = ideal_state.returnPos(chiffre)[1], y = ideal_state.returnPos(chiffre)[0])
                res += ( abs((current_pos.x) - (ideal_pos.x)) + abs((current_pos.y) - (ideal_pos.y)) )
        return res
    
    def createChildren(self, direction = "NONE"):
        """Crée un nouvel état de classe State, en fonction de la direction où l'on veut bouger le 0.

        Args:
            direction (str, optional): Choisit une direction pour déplacer le 0. Defaults to "NONE".

        Returns:
            State: L'état fils généré.
        """
        pos_zero = Position(x = self.returnPos(0)[1], y = self.returnPos(0)[0])
        res = None
        if direction == "UP" :
            if pos_zero.y != 0 :
                return State(board = self.swapNumber(self.board[pos_zero.y-1][pos_zero.x]), move_count = self.move_count+1, previous = self)
        if direction == "DOWN" :
            if pos_zero.y != 2 :
                return State(board = self.swapNumber(self.board[pos_zero.y+1][pos_zero.x]), move_count = self.move_count+1, previous = self)
        if direction == "RIGHT" :
            if pos_zero.x != 2 :
                return State(board = self.swapNumber(self.board[pos_zero.y][pos_zero.x+1]), move_count = self.move_count+1, previous = self)
        if direction == "LEFT" :
            if pos_zero.x != 0 :
                return State(board = self.swapNumber(self.board[pos_zero.y][pos_zero.x-1]), move_count = self.move_count+1, previous = self)
    
    def isSolvable(self):
        """Renvoie True si le board est résolvable, False le cas contraire.

        Returns:
            bool : Est-ce que le board est solvable ?
        """
        oneDimensionArray = []
        count = 0
        #On transforme l'array en 2D à un array en 1D, en enlevant le zéro.
        for ligne in self.board :
            for chiffre in ligne :
                if chiffre != '0' :
                    oneDimensionArray.append(int(chiffre))
        #Pour chaque chiffre dans l'array en 1D, on regarde le nombre de chiffres plus petits qui sont après.
        for chiffre in oneDimensionArray :
            if oneDimensionArray.index(chiffre)+1 != chiffre :
                for subset in oneDimensionArray[oneDimensionArray.index(chiffre)+1:] :
                    if int(subset) < int(chiffre) :
                        #On ajoute 1 au compteur pour chaque chiffre plus petit trouvé
                        count += 1
        #Si le nombre de permutations est impair, on renvoie False. Sinon, on renvoie True.
        return (count/2)%2 == 0

def resolve(origin, target = parse_puzzle("1 2 3 \n4 5 6 \n7 8 0")):
    """L'algorithme censé pouvoir résoudre un jeu de taquin.

    Args:
        target (State): La configuration souhaitée
        origin (State): La configuration de départ

    Returns:
        State / None : Renvoie un State si la solution est trouvée en moins de 36 coups, sinon renvoie un None.
    """
    potential_wins = [origin]
    past_states = [origin]
    counter = 0
    #On lance une boucle qui ne s'arrête que si on a trouvé la solution ou que l'on a fait plus de 36 coups.
    while True :
        #Pour chaque direction, on crée un état enfant, si les conditions le permettent.
        for direction in ["DOWN","UP", "LEFT", "RIGHT"]:
            for etat in potential_wins:
                enfant = etat.createChildren(direction)
                for potential_win in potential_wins:
                    #Si la distance de manhattan est plus petite pour un enfant, on enlève tous les états qui ont une distance plus élevée et on recommence.
                    if enfant.manhattan() < potential_win.manhattan():
                        potential_wins.remove(potential_win)
                        
        #Si le board d'un état est égal à celui de notre état cible, on return l'état en question
        for etat in potential_wins:
            if etat.board == target.board:
                return etat
        counter += 1

        #Après 36 coups, on return None si on a rien trouvé.
        if counter == 36 :
            return None
