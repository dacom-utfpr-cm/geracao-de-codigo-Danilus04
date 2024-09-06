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
from anytree import RenderTree, AsciiStyle, PreOrderIter

from tppparser import generate_syntax_tree
from tppsema import semanticMain
from myerror import MyError

#Biblioteca para geração de código
from llvmlite import ir
from llvmlite import binding as llvm

error_handler = MyError('GenCodeErrors')

root = None

showKey = False 
haveTPP = False
arrError = []

#node, caminho = [0,1,0,0] (caminho que vai percorrer entre os filhos)
#Retorna o node onde o caminho o levou
def browseNode(node, caminho):
    nodeAux = node
    for prox in caminho:
        if prox < 0: 
            nodeAux = nodeAux.parent
        else:
            nodeAux = nodeAux.children[prox]
    return nodeAux
    
#Ja que na propria arvore tem varios nomes para o mesmo tipo, essa função ve a entrada e diz corretamente o tipo
def whatType(str):
    inteiro = ["INTEIRO","inteiro","NUM_INTEIRO"]
    flutuante = ["flutuante"]

    if(str in inteiro):
        return "INTEIRO"

    if(str in flutuante):
        return "FLUTUANTE"
    
def createVar(str):

    type = whatType(str)

    if(type == "INTEIRO"):
        return ir.IntType(32)
    
    if(type == "FLUTUANTE"):
        return ir.FloatType()

def generateCode(tree):
    llvm.initialize()
    llvm.initialize_all_targets()
    llvm.initialize_native_target()
    llvm.initialize_native_asmprinter()

    module = ir.Module('meu_modulo.bc')
    module.triple = llvm.get_process_triple()
    target = llvm.Target.from_triple(module.triple)
    target_machine = target.create_target_machine()
    module.data_layout = target_machine.target_data

    #print(module)


    entryBlock = None
    endBasicBlock = None
    builder = None

    for node in (PreOrderIter(tree)):
        nodeAux = None
        type = None
        var = None
        functInfo = None
        func = None
        name = None

        if(node.name == "declaracao_funcao"):
            name = browseNode(node, [1,0,0]).name
            type = browseNode(node, [0,0,0]).name
            
            var = createVar(type)
            functInfo = ir.FunctionType(var, ())
            #print(functInfo, name, var, type)
            func = ir.Function(module, functInfo, name=name)

            entryBlock = func.append_basic_block('entry')
            endBasicBlock = func.append_basic_block('exit')

            builder = ir.IRBuilder(entryBlock)

        if(node.name == "FIM"):
            if(browseNode(node, [-1,-1]).name == "declaracao_funcao"):
                # Cria um salto para o bloco de saída
                builder.branch(endBasicBlock)
                #print('')
                # Adiciona o bloco de saida
                builder.position_at_end(endBasicBlock)

            
    arquive = open('./tests/meu_modulo.ll', 'w')
    arquive.write(str(module))
    arquive.close()

        


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
            
            #semanticMain(args)
            
            generateCode(tree)
            print("Codigo Gerado!")
            #if tree:
    
    except Exception as e:
        print(e)


# Chama a função main passando os argumentos da linha de comando
if __name__ == "__main__":
    main(sys.argv)
