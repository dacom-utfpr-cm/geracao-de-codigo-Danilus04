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

leiaF = None
leiaI = None
escrevaF = None
escrevaI = None
showKey = False 
haveTPP = False
arrError = []
module = None
builder = None
varList = []
iftrue = []
iffalse = []
ifend = []

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
    flutuante = ["flutuante","NUM_PONTO_FLUTUANTE","FLUTUANTE"]

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
    typel = whatType(browseNode(node, [0,0]).name)
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
        varList.append({"scope": scope, "name": name,"var" : var, "type": typel})
        nodeAux = browseNode(nodeAux, [0])
    
    name = browseNode(nodeAux,[0,0,0]).name

    if(scope == None):
        var = ir.GlobalVariable(module, type, name)
    else:
        var = builder.alloca(type, name=name)

    var.initializer = ir.Constant(type, 0)
    var.align = 4
    varList.append({"scope": scope, "name": name,"var" : var, "type": typel})

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
    
    NodeAux = None
    
    var = browseNode(node, [0,0,0])
    var_name = var.name
    var_ptr = getVarInList(var_name, scope)  # Espera-se que isso retorne um ponteiro (i32*)
    
    NodeAux = browseNode(node, [2])
    varRes = expressions(NodeAux, scope)
    #print(var_ptr, ' a')
    #print(varRes, ' b')


    builder.store(varRes,var_ptr)

def expressionsAux(x_temp, y_temp, operation):
    # Definir a operação
    #print(operation)
    if operation == '>':
        result = builder.icmp_signed('>', x_temp, y_temp, name='maior')
    elif operation == '<':
        result = builder.icmp_signed('<', x_temp, y_temp, name='menor')
    elif operation == '>=':
        result = builder.icmp_signed('>=', x_temp, y_temp, name='maiorIgual')
    elif operation == '<=':
        result = builder.icmp_signed('<=', x_temp, y_temp, name='menorIgual')
    elif operation == '=':
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
    flutuante = ["flutuante","NUM_PONTO_FLUTUANTE", "FLUTUANTE"]
    sinais_aritmeticos = ["+", "-", "*", "/", "%"]
    sinais_logicos = [">", "<", ">=", "<=", "=", "!=", "&&", "||", "!"]

    global builder

    x_temp = None
    y_temp = None
    nodeAux = None
    type = None
    expression = None

    for node in (PreOrderIter(node)):
        if node.name == "fator":
            nodeAux = browseNode(node, [0,0])
            if(nodeAux.name == "ID"):
                #CASO SEJA UM ID
                nodeAux = browseNode(nodeAux, [0])
                if(x_temp == None):
                    x_temp = builder.load(getVarInList(nodeAux.name, scope), name='x_temp')
                else:
                    y_temp = builder.load(getVarInList(nodeAux.name, scope), name='y_temp')
                    x_temp = expressionsAux(x_temp, y_temp, expression)
                    y_temp = None
                    expression = None
            elif(nodeAux.name in flutuante or nodeAux.name in inteiro):
                #CASO SEJA UMA CONSTANTE
                type = createTypeVar(nodeAux.name)
                nodeAux = browseNode(nodeAux, [0])
                if(x_temp == None):
                    x_temp = ir.Constant(type,float(nodeAux.name))
                else:
                    y_temp = ir.Constant(type,float(nodeAux.name))
                    x_temp = expressionsAux(x_temp, y_temp, expression)
                    y_temp = None
                    expression = None
        if(node.name in sinais_aritmeticos or node.name in sinais_logicos): 
            expression = node.name
            #TODO : TRATAR PARENTESES COM RECURSIVIDADE !!!!!!

    
    return(x_temp)

def condicao(node, scope, func):
    global builder
    global iftrue
    global iffalse
    global ifend
    
    haveElse = len(node.children) > 5
    
    nodeAux = browseNode(node, [1])
    expressionRes = expressions(nodeAux, scope)
    
    if(haveElse):
        iftrue.append(func.append_basic_block('iftrue_1'))
        iffalse.append(func.append_basic_block('iffalse_1'))
        ifend.append(func.append_basic_block('ifend_1'))

        builder.cbranch(expressionRes,iftrue[-1], iffalse[-1])
    else : 
        iftrue.append(func.append_basic_block('iftrue_1'))
        print('teste')
        ifend.append(func.append_basic_block('ifend_1'))
        
        builder.cbranch(expressionRes,iftrue[-1], ifend[-1])

    builder.position_at_end(iftrue.pop())

    #SE NÃO TEM SENÃO, iffalse_1 leva pra saida!

def getTypeInList(varName, scope, list):

    for var in list:
        if( varName == var["name"] and scope == var["scope"]):
            return var["type"]

    for var in list:
        if( varName == var["name"] and None == var["scope"]):
            return var["type"]

#ESSA LISTA É PARA VERIFICAR NOME DE VARIAVEL E TIPO
#PARA VERIFICAR SE PRECISA DE FUNÇÃO DE ESCREVER E LER
def ADDAnotherVarInList(node, scope, list):

    varType = whatType(browseNode(node, [0,0]).name)
    nodeAux = browseNode(node, [2])
    while len(nodeAux.children) > 2:
        name = browseNode(nodeAux,[2,0,0]).name
        #print(name)
        
        list.append({"name": name, "scope": scope, "type": varType})
        nodeAux = browseNode(nodeAux, [0])
    
    name = browseNode(nodeAux,[0,0,0]).name

    list.append({"name": name, "scope": scope, "type": varType})

def findFirstTypeVar(expressionNode,list,scope):
    nodeAux = None
    for node in (PreOrderIter(expressionNode)):
        if(node.name == 'fator'):
            nodeAux = browseNode(node, [0,0])
            if(nodeAux.name == 'ID'):
                #print(nodeAux.name)
                nodeAux = browseNode(nodeAux, [0])
                return getTypeInList(nodeAux.name,scope,list)
            else:
                return whatType(nodeAux.name)    

def verifyReadPrint(tree):
    inteiro = ["INTEIRO","inteiro","NUM_INTEIRO"]
    flutuante = ["flutuante","NUM_PONTO_FLUTUANTE", "FLUTUANTE"]
    global module
    global builder
    global leiaF
    global leiaI
    global escrevaF
    global escrevaI
    
    haveReadInt = False
    haveReadFloat = False
    havePrintInt = False
    havePrintFloat = False

    nodeAux = None
    nameVar = None
    type = None
    scope = None
    list = []

    for node in (PreOrderIter(tree)):
        
        #print(node.name)
        if(node.name == "declaracao_funcao"):
            scope = browseNode(node, [1,0,0]).name

        if(node.name == "declaracao_variaveis"):
            ADDAnotherVarInList(node,scope,list)

        if(node.name == "leia" and len(node.children) > 1):
            #por enquanto ta com nome da variavel
            nameVar = browseNode(node,[2,0,0]).name
            type = getTypeInList(nameVar, scope, list)

            if(type in flutuante and not haveReadFloat):
                _leiaF = ir.FunctionType(ir.FloatType(), [])
                leiaF = ir.Function(module, _leiaF, "leiaFlutuante")
                haveReadFloat = True
            
            if(type in inteiro and not haveReadInt):
                _leiaI = ir.FunctionType(ir.IntType(32), [])
                leiaI = ir.Function(module, _leiaI, "leiaInteiro")
                haveReadInt = True
            
        if(node.name == "escreva" and len(node.children) > 1):
            
            nodeAux = browseNode(node, [2])
            type = findFirstTypeVar(nodeAux,list,scope)
            if(type in flutuante and not havePrintFloat):
                _escrevaF = ir.FunctionType(ir.VoidType(), [ir.FloatType()])
                escrevaF = ir.Function(module, _escrevaF, "escrevaFlutuante")
                havePrintFloat = True

            if(type in inteiro and not havePrintInt):
                _escrevaI = ir.FunctionType(ir.VoidType(), [ir.IntType(32)])
                escrevaI = ir.Function(module, _escrevaI, "escrevaInteiro")
                havePrintInt = True

        
    #if(havePrint):
        

def generateCode(tree):
    llvm.initialize()
    llvm.initialize_all_targets()
    llvm.initialize_native_target()
    llvm.initialize_native_asmprinter()

    global module
    global builder
    global varList
    global iftrue
    global iffalse
    global ifend
    global leiaF
    global leiaI
    global escrevaF
    global escrevaI

    module = ir.Module('meu_modulo.bc')
    module.triple = llvm.get_process_triple()
    target = llvm.Target.from_triple(module.triple)
    target_machine = target.create_target_machine()
    module.data_layout = target_machine.target_data

    #builder = None Ja declarado
    entryBlock = None
    endBasicBlock = None
    scope = None
    func = None
    escreva = False
    loop = None
    loopVal = []
    lopeEnd = []
    #Esses 3 com formato de pilha, para ajudar na lógica
    #Eles guardam blocos de código os ifs
    #iftrue = []
    #iffalse = []
    #ifend = []
               

    verifyReadPrint(tree)
    varList = []

    for node in (PreOrderIter(tree)):
        nodeAux = None
        type = None
        var = None
        functInfo = None
        name = None

        #print(node.name)
       
        if(node.name == "declaracao_funcao"):
            
            #TODO: FUNÇÃO PRINCIPAL TEM QUE SE CHAMAR 'main'
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

        if(node.name == "fim"):
            if(browseNode(node, [-1,-1,-1]).name == "declaracao_funcao"):
                # Cria um salto para o bloco de saída
                #builder.branch(endBasicBlock)
                scope = None
                builder = ir.IRBuilder(endBasicBlock)
                # Adiciona o bloco de saida
                
                builder.position_at_end(endBasicBlock)

            if(browseNode(node, [-1,-1]).name == "se"):
                #print("ue")
                builder.branch(ifend[-1])
                builder.position_at_end(ifend.pop())

                

        #Para lidar com a estrutura estranha do retorna
        if(node.name == "retorna" and len(node.children) > 1):
            nodeAux = browseNode(node, [2])
            builder.ret(expressions(nodeAux, scope))
        
        if(node.name == "declaracao_variaveis"):
            createVar(node, scope)

        if(node.name == "atribuicao"):
            atribuition(node, scope)

        if(node.name == "se" and len(node.children) > 1):
            
            condicao(node,scope,func)

        if(node.name == "SENAO"):
            builder.branch(ifend[-1])
            builder.position_at_end(iffalse.pop())
            #print('teste')

        if(node.name == "escreva" and len(node.children) > 1):
            nodeAux = browseNode(node, [2])
            type = findFirstTypeVar(nodeAux, varList, scope)

            if(type == 'INTEIRO'):
                builder.call(escrevaI, args=[expressions(nodeAux, scope)]) 

            if(type == 'FLUTUANTE'):
                builder.call(escrevaF, args=[expressions(nodeAux, scope)])                

        if(node.name == "leia" and len(node.children) > 1):
            nodeAux = browseNode(node, [2,0,0])
            name = nodeAux.name
            type = getTypeInList(name, scope, varList)
            var = getVarInList(name, scope)
            if(type == 'INTEIRO'):
                resultado_leia = builder.call(leiaI, args=[])
                builder.store(resultado_leia, var)

            if(type == 'FLUTUANTE'):
                resultado_leia = builder.call(leiaF, args=[])
                builder.store(resultado_leia, var)
        
        if(node.name == 'repita' and len(node.children) > 1):
            loop = builder.append_basic_block('loop')
            builder.branch(loop)
            builder.position_at_end(loop)

        if(node.name == 'ATE' and browseNode(node,[-1]).name == 'repita'):
            lopp_val = builder.append_basic_block('loop_val')
            loop_end = builder.append_basic_block('loop_end')
            # Pula para o laço de validação
            builder.branch(lopp_val)
            # Posiciona no inicio do bloco de validação e define o que o loop de validação irá executar
            builder.position_at_end(lopp_val)
            nodeAux = browseNode(node, [-1,3])
            #FAZER EXPRESSÃO DE ATE
            var = expressions(nodeAux, scope)
            builder.cbranch(var, loop, loop_end)

            # Posiciona no inicio do bloco do fim do loop (saída do laço) e define o que o será executado após o fim (o resto do programa)  
            builder.position_at_end(loop_end)
        

    #print(varList)
            
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
