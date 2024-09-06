import sys
import os

from sys import argv, exit

import logging

logging.basicConfig(
     level=logging.DEBUG,
     filename="gencode.log",
     filemode="w",
     format="%(filename)10s:%(lineno)4d:%(message)s"
)
log = logging.getLogger()

import ply.yacc as yacc

# Get the token map from the lexer. This is required.
from tpplex import tokens

from mytree import MyNode
from anytree.exporter import DotExporter, UniqueDotExporter
from anytree import RenderTree, AsciiStyle

from tppparser import generate_syntax_tree
from myerror import MyError

error_handler = MyError('GenCodeErrors')

root = None

showKey = False 
haveTPP = False
arrError = []


# Função Principal que recebe os argumentos
def main(args):
    global showKey
    global haveTPP
    locationTTP = None

    for i in range(len(args)):
        aux = argv[i].split('.')
        if aux[-1] == 'tpp':
            haveTPP = True
            locationTTP = i 
        if(argv[i] == '-k'):
            showKey = True

    try:
        if(len(args) < 3 and showKey == True):
            raise TypeError(error_handler.newError(showKey,'ERR-GC-USE'))

        if haveTPP == False:
            raise IOError(error_handler.newError(showKey,'ERR-GC-NOT-TPP'))
        elif not os.path.exists(argv[locationTTP]):
            raise IOError(error_handler.newError(showKey,'ERR-GC-FILE-NOT-EXISTS'))
        else:
            
            tree = generate_syntax_tree(args)  

            print(tree)      
            #if tree:
    
    except Exception as e:
        print(e)


# Chama a função main passando os argumentos da linha de comando
if __name__ == "__main__":
    main(sys.argv)
