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
module = None
builder = None
varList = []

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
    flutuante = ["flutuante","NUM_PONTO_FLUTUANTE"]

    if(str in inteiro):
        return "INTEIRO"

    if(str in flutuante):
        return "FLUTUANTE"
    
def createTypeVar(str):

    type = whatType(str)

    if(type == "INTEIRO"):
        return ir.IntType(32)
    
    if(type == "FLUTUANTE"):
        return ir.FloatType()
    
    return None

def createVar(node,scope):
    global varList 
    global builder
    global module

    type = createTypeVar(browseNode(node, [0,0]).name)
    nodeAux = browseNode(node, [2])
    while len(nodeAux.children) > 2:

        name = browseNode(nodeAux,[2,0,0]).name
        # CASO GLOBAL
        if(scope == None):
            var = ir.GlobalVariable(module, type, name)
        else:
            var = builder.alloca(type, name=name)

        var.initializer = ir.Constant(type, 0)
        var.align = 4
        varList.append({"scope": scope, "name": name,"var" : var})
        nodeAux = browseNode(nodeAux, [0])
    
    name = browseNode(nodeAux,[0,0,0]).name

    if(scope == None):
        var = ir.GlobalVariable(module, type, name)
    else:
        var = builder.alloca(type, name=name)

    var.initializer = ir.Constant(type, 0)
    var.align = 4
    varList.append({"scope": scope, "name": name,"var" : var})

def getVarInList(varName, scope):
    global varList

    for var in varList:
        if( varName == var["name"] and scope == var["scope"]):
            return var["var"]

    for var in varList:
        if( varName == var["name"] and None == var["scope"]):
            return var["var"]

def atribuition(node, scope):
    global builder
    global module
    #print(module)
    #TODO : FAZER ISSO FUNCIONAR
    NodeAux = None
    
    var = browseNode(node, [0,0,0])
    var_name = var.name
    var_ptr = getVarInList(var_name, scope)  # Espera-se que isso retorne um ponteiro (i32*)
    
    NodeAux = browseNode(node, [2])
    varRes = expressions(NodeAux, scope)
    print(var_ptr, ' a')
    print(varRes, ' b')


    builder.store(varRes,var_ptr)

def expressionsAux(x_temp, y_temp, operation):
    # Definir a operação
    print(operation)
    if operation == '>':
        result = builder.icmp_signed('>', x_temp, y_temp, name='maior')
    elif operation == '<':
        result = builder.icmp_signed('<', x_temp, y_temp, name='menor')
    elif operation == '>=':
        result = builder.icmp_signed('>=', x_temp, y_temp, name='maiorIgual')
    elif operation == '<=':
        result = builder.icmp_signed('<=', x_temp, y_temp, name='menorIgual')
    elif operation == '==':
        result = builder.icmp_signed('==', x_temp, y_temp, name='igual')
    elif operation == '!=':
        result = builder.icmp_signed('!=', x_temp, y_temp, name='diferente')
    elif operation == '&&':
        result = builder.and_(x_temp, y_temp, name='and')
    elif operation == '||':
        result = builder.or_(x_temp, y_temp, name='or')
    elif operation == '!':
        result = builder.not_(x_temp, name='not')
    elif operation == '+':
        result = builder.add(x_temp, y_temp, name='soma')
    elif operation == '-':
        result = builder.sub(x_temp, y_temp, name='subtracao')
    elif operation == '*':
        result = builder.mul(x_temp, y_temp, name='multiplicacao')
    elif operation == '/':
        result = builder.sdiv(x_temp, y_temp, name='divisao')
    elif operation == '%':
        result = builder.srem(x_temp, y_temp, name='modulo')
    elif operation == '>>':
        um = ir.Constant(ir.IntType(32), 1)
        result = builder.ashr(x_temp, um, name='shiftDireita')
    elif operation == '<<':
        um = ir.Constant(ir.IntType(32), 1)
        result = builder.shl(x_temp, um, name='shiftEsquerda')
    else:
        raise ValueError("Operação desconhecida")
    
    return result

def expressions(node, scope):
    inteiro = ["INTEIRO","inteiro","NUM_INTEIRO"]
    flutuante = ["flutuante","NUM_PONTO_FLUTUANTE"]
    sinais_aritmeticos = ["+", "-", "*", "/", "%"]
    sinais_logicos = [">", "<", ">=", "<=", "==", "!=", "&&", "||", "!"]

    global builder

    x_temp = None
    y_temp = None
    nodeAux = None
    type = None

    for node in (PreOrderIter(node)):
        if node.name == "fator":
            nodeAux = browseNode(node, [0,0])
            if(nodeAux.name == "ID"):
                #CASO SEJA UM ID
                nodeAux = browseNode(nodeAux, [0])
                if(x_temp == None):
                    x_temp = builder.load(getVarInList(nodeAux.name, scope), name='x_temp')
                else:
                    y_temp = builder.load(getVarInList(nodeAux.name, scope), name='x_temp')
            elif(nodeAux.name in flutuante or nodeAux.name in inteiro):
                #CASO SEJA UMA CONSTANTE
                type = createTypeVar(nodeAux.name)
                nodeAux = browseNode(nodeAux, [0])
                if(x_temp == None):
                    x_temp = ir.Constant(type,float(nodeAux.name))
                else:
                    y_temp = ir.Constant(type,float(nodeAux.name))
        if(node.name in sinais_aritmeticos or node.name in sinais_logicos): 
            x_temp = expressionsAux(x_temp, y_temp, node.name)
            y_temp = None

    
    return(x_temp)

                
                





def generateCode(tree):
    llvm.initialize()
    llvm.initialize_all_targets()
    llvm.initialize_native_target()
    llvm.initialize_native_asmprinter()

    global module
    global builder
    global varList

    module = ir.Module('meu_modulo.bc')
    module.triple = llvm.get_process_triple()
    target = llvm.Target.from_triple(module.triple)
    target_machine = target.create_target_machine()
    module.data_layout = target_machine.target_data

    #builder = None Ja declarado
    entryBlock = None
    endBasicBlock = None
    scope = None

    for node in (PreOrderIter(tree)):
        nodeAux = None
        type = None
        var = None
        functInfo = None
        func = None
        name = None

        if(node.name == "declaracao_funcao"):
            

            name = browseNode(node, [1,0,0]).name
            scope = name
            type = browseNode(node, [0,0,0]).name
            
            var = createTypeVar(type)
            functInfo = ir.FunctionType(var, ())
            #print(functInfo, name, var, type)
            func = ir.Function(module, functInfo, name=name)

            entryBlock = func.append_basic_block('entry')
            endBasicBlock = func.append_basic_block('exit')

            builder = ir.IRBuilder(entryBlock)

        if(node.name == "FIM"):
            if(browseNode(node, [-1,-1]).name == "declaracao_funcao"):
                # Cria um salto para o bloco de saída
                #builder.branch(endBasicBlock)
                scope = None
                builder = ir.IRBuilder(endBasicBlock)
                # Adiciona o bloco de saida
                builder.position_at_end(endBasicBlock)

                

        #Para lidar com a estrutura estranha do retorna
        if(node.name == "retorna" and len(node.children) > 1):
            
            builder.ret(ir.Constant(ir.IntType(32), 0))
        
        if(node.name == "declaracao_variaveis"):
            createVar(node, scope)

        if(node.name == "atribuicao"):
            atribuition(node, scope)
    print(varList)
            
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
