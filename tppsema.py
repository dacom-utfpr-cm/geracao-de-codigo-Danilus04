import sys
import os

from sys import argv, exit

import logging

showKey = False 
haveTPP = False
arrError = []
semTable = []

logging.basicConfig(
     level = logging.DEBUG,
     filename = "sema.log",
     filemode = "w",
     format = "%(filename)10s:%(lineno)4d:%(message)s"
)
log = logging.getLogger()


import ply.yacc as yacc

# Get the token map from the lexer.  This is required.
from tpplex import tokens

#from anytree.exporter import DotExporter, UniqueDotExporter
from mytree import MyNode
from anytree import RenderTree, AsciiStyle, PreOrderIter

from tppparser import generate_syntax_tree

from myerror import MyError
from enum import Enum

import pprint
#TODO: REMOVER ISSO AQ DEPOIS

error_handler = MyError('SemaErrors')

#root = None

class PalavrasChaves(Enum):
    declaracao_funcao = "declaracao_funcao"
    declaracao_variaveis = "declaracao_variaveis"
    atribuicao = "atribuicao"
    chamada_funcao = "chamada_funcao"
    fim = "FIM"
    retorna = "retorna"
    fator = "fator"
    parametro = "parametro"
    var = "var"


#Não é eficiente para declaração de função
def find_ID_and_factor(node):
    """
    Função recursiva para encontrar todos os nós com o nome especificado.

    :param node: O nó inicial a partir do qual a busca começa.
    :param name: O nome do nó que estamos buscando.
    :return: Uma lista de nós que correspondem ao nome fornecido.
    """
    found_nodes = []
    nodeAux = None

    #print(node.name)
    
    # Verifica se o nome do nó atual corresponde ao nome buscado
    if node.name == PalavrasChaves.chamada_funcao.value:
        return found_nodes

    if node.name == PalavrasChaves.fator.value:
        nodeAux = node.children[0]
        nodeAux = nodeAux.children[0]
        if(nodeAux.name == 'ID'):
            nodeAux = nodeAux.children[0]
            found_nodes.append(nodeAux.name)    
        else: 
            found_nodes.append(nodeAux.name)
    
    # Busca recursivamente nos filhos do nó atual
    for child in node.children:
        found_nodes.extend(find_ID_and_factor(child))
    
    return found_nodes

def find_parameters(node,semtable,scope,data):
    """
    Função recursiva para encontrar todos os nós com o nome especificado.

    :param node: O nó inicial a partir do qual a busca começa.
    :param name: O nome do nó que estamos buscando.
    :return: Uma lista de nós que correspondem ao nome fornecido.
    """
    nodeAux = None
    type = None
    name = None
    #print(node.name)
    
    # Verifica se o nome do nó atual corresponde ao nome buscado

    if node.name == PalavrasChaves.parametro.value:
        nodeAux = node.children[0]
        nodeAux = nodeAux.children[0]
        type = nodeAux.name
        nodeAux = node.children[2]
        nodeAux = nodeAux.children[0]
        name = nodeAux.name
        data.append(name)

        semtable.append({"declaration": PalavrasChaves.declaracao_variaveis.value
                         , "type": type
                         , "id": name
                         , "scope": scope
                         , "data": "Param"})
   
    
    
    # Busca recursivamente nos filhos do nó atual
    for child in node.children:
        find_parameters(child,semtable,scope,data)

#Manda a lista de variavel e coloca na tabela semântica
def declaracaVariavelAux(node,semtable,scope,type):
    nodeAux = node
    name = None
    data = None
    if len(node.children) > 2:
        nodeAux = nodeAux.children[2]
        if len(node.children) > 1:
            data = find_ID_and_factor(nodeAux)            
        nodeAux = nodeAux.children[0]
        nodeAux = nodeAux.children[0]
        name = nodeAux.name
        
    else:
    
        nodeAux = nodeAux.children[0]
        if len(nodeAux.children) > 1:
            data = find_ID_and_factor(nodeAux)  
        nodeAux = nodeAux.children[0]
        nodeAux = nodeAux.children[0]
        name = nodeAux.name

    #print(name, data)
    semtable.append({"declaration": PalavrasChaves.declaracao_variaveis.value,
                    "type": type,
                    "id": name,
                    "scope": scope,
                    "data": data
                    })

    
def creatingSemanticTable(tree):
    global haveTPP
    global showKey
    global arrError

    nodeAux = None
    type = None
    name = None
    scope = None
    data = []
    semTable = []

    # Explora a árvore nó por nó
    for node in PreOrderIter(tree):
        data = []
        # Tabela palavre chaves
        # Declaração de Variavel
        if hasattr(node, 'name') and node.name == PalavrasChaves.declaracao_variaveis.value:
            
            nodeAux = node.children[0] 
            nodeAux = nodeAux.children[0] 
            type = nodeAux.name
            
            nodeAux = node.children[2] 
            while nodeAux.name == "lista_variaveis":
                declaracaVariavelAux(nodeAux,semTable,scope,type)
                nodeAux = nodeAux.children[0]
                
            
            #name = nodeAux.name
            #semTable.append({"declaration": node.name, "type": type, "id": name, "scope": scope})

        if hasattr(node, 'name') and node.name == PalavrasChaves.fim.value:
            scope = None

        # Declaração de Função
        if hasattr(node, 'name') and node.name == PalavrasChaves.declaracao_funcao.value:
            
            #Pega o tipo
            nodeAux = node.children[0] 
            nodeAux = nodeAux.children[0] 
            type = nodeAux.name

            #Pega o nome
            nodeAux = node.children[1] 
            nodeAux = nodeAux.children[0]
            nodeAux = nodeAux.children[0]
            name = nodeAux.name

            nodeAux = node.children[1] 
            nodeAux = nodeAux.children[2] 
            data = []

            scopeAux = scope
            scope = name
            find_parameters(nodeAux,semTable,scope,data)
            
            scope = scopeAux
            semTable.append({"declaration": node.name, "type": type, "id": name, "scope": scope, "data": data})
            
            scope = name

        # Atribuição
        if hasattr(node, 'name') and node.name == PalavrasChaves.atribuicao.value:
            
            nodeAux = node.children[0] 
            nodeAux = nodeAux.children[0] 
            nodeAux = nodeAux.children[0] 
            name = nodeAux.name
            
            data = find_ID_and_factor(node)
            
            #print(f"nodeAux = {nodeAux.name}")
            
            semTable.append({"declaration": node.name, "type": '-', "id": name, "scope": scope, "data": data}) 
        
        # Chamada de Função
        if hasattr(node, 'name') and node.name == PalavrasChaves.chamada_funcao.value:
            
            nodeAux = node.children[0] 
            nodeAux = nodeAux.children[0] 
            name = nodeAux.name

            nodeAux = node.children[2] 
            data = find_ID_and_factor(nodeAux)
            
            #print(f"nodeAux = {nodeAux.name}")
            semTable.append({"declaration": node.name, "type": '-', "id": name, "scope": scope, "data": data}) 

        # Retorno
        if hasattr(node, 'name') and node.name == PalavrasChaves.retorna.value:

            if len(node.children) > 2:
                nodeAux = node.children[2]
                data = find_ID_and_factor(nodeAux)
                name = None
                semTable.append({"declaration": node.name, "type": '-', "id": name, "scope": scope, "data": data}) 

        if hasattr(node, 'name') and node.name == PalavrasChaves.var.value:

            nodeAux = node.children[0]
            nodeAux = nodeAux.children[0]
            #data = find_ID_and_factor(nodeAux)
            name = nodeAux.name

            nodeAux = node.parent
            while nodeAux.name == 'lista_variaveis':
                nodeAux = nodeAux.parent

            #VERIFICA SE ELE FOI USADO FORA DE ATRIBUIÇÕES E DECLARAÇÕES
            if nodeAux.name != PalavrasChaves.declaracao_variaveis.value and (node.parent).name != PalavrasChaves.atribuicao.value:
                semTable.append({"declaration": node.name, "id": name, "scope": scope}) 
                

    
    #pprint.pprint(semTable)
    # if len(arrError) > 0:
    #     raise IOError(arrError)
    
    return semTable

def extrair_funcoes_declaradas(declaracoes):
    funcoes_declaradas = []
    
    for declaracao in declaracoes:
        if declaracao['declaration'] == 'declaracao_funcao':
            funcoes_declaradas.append(declaracao['id'])
    
    return funcoes_declaradas

def verificarFuncaoPrincipal(semTable):
    global arrError
    global showKey
    principal_existe = False
    for table in semTable:
        if table['declaration'] == 'declaracao_funcao' and table['id'] == 'principal':
            principal_existe = True
            break
    if not principal_existe:
        arrError.append(error_handler.newError(showKey, 'ERR-SEM-MAIN-NOT-DECL'))

def verificarDeclaracaoDeFuncoes(semTable):
    global arrError
    global showKey
    funcoesDeclaradas = extrair_funcoes_declaradas(semTable)

    for declaracao in semTable:
        if declaracao['declaration'] == 'chamada_funcao':
            func_id = declaracao['id']
            if func_id not in funcoesDeclaradas:
                arrError.append(error_handler.newError(showKey, 'ERR-SEM-CALL-FUNC-NOT-DECL'))

def verificarParametrosFuncoes(semantic_table):
    global arrError
    global showKey

    # Cria um dicionário para armazenar as funções e seus parâmetros formais
    declaracoes_funcoes = {}
    
    for item in semantic_table:
        if item['declaration'] == 'declaracao_funcao':
            
            declaracoes_funcoes[item['id']] = len(item.get('data', []))  # Armazena a quantidade de parâmetros formais

    # Itera sobre a tabela para verificar as chamadas de função
    for item in semantic_table:
        if item['declaration'] == PalavrasChaves.chamada_funcao.value:
            func_id = item['id']
            parametros_reais = len(item.get('data', []))  # Conta os parâmetros reais da chamada

            if func_id in declaracoes_funcoes:
                parametros_formais = declaracoes_funcoes[func_id]

                if parametros_reais < parametros_formais:
                    arrError.append(error_handler.newError(showKey, 'ERR-SEM-CALL-FUNC-WITH-FEW-ARGS'))
                    #print(f"Erro (ERR-SEM-CALL-FUNC-WITH-FEW-ARGS): Chamada à função '{func_id}' com número de parâmetros menor que o declarado.")
                elif parametros_reais > parametros_formais:
                    arrError.append(error_handler.newError(showKey, 'ERR-SEM-CALL-FUNC-WITH-MANY-ARGS'))
                    #print(f"Erro (ERR-SEM-CALL-FUNC-WITH-MANY-ARGS): Chamada à função '{func_id}' com número de parâmetros maior que o declarado.")
            else:
                print(f"Erro: Função '{func_id}' chamada, mas não declarada.")

def verificarFuncoesNaoUtilizadas(semTable):
    funcoesDeclaradas = extrair_funcoes_declaradas(semTable)
    funcoesUtilizadas = set()

    # Coletar todas as funções utilizadas
    for declaracao in semTable:
        if declaracao['declaration'] == PalavrasChaves.chamada_funcao.value:
            func_id = declaracao['id']
            funcoesUtilizadas.add(func_id)

    funcoesUtilizadas.add('principal')
    #para não falar que a função principal nao foi declarada

    # Verificar se há funções declaradas que não foram utilizadas
    for func in funcoesDeclaradas:
        if func not in funcoesUtilizadas:
            arrError.append(error_handler.newError(showKey, f"WAR-SEM-FUNC-DECL-NOT-USED"))

def verificarTipoRetorno(semTable):
    global arrError
    global showKey
    
    for declaracao in semTable:
        tipoDaFuncao = None
        mesmoRetorno = True
        achouRetorno = False

        if declaracao['declaration'] == PalavrasChaves.declaracao_funcao.value:
            for declaracao2 in semTable:
                if declaracao2['declaration'] == PalavrasChaves.retorna.value and declaracao2['scope'] == declaracao['id']:
                    achouRetorno = True
                    tipoDaFuncao = declaracao['type']
                    data = declaracao2['data']
                    for var in data:

                        tipoVar = verificarTipoDaVariavel(semTable, var, declaracao2['scope'])
                        
                        if tipoVar != tipoDaFuncao:
                            
                            mesmoRetorno = False
                            
            if(not mesmoRetorno):
                
                arrError.append(error_handler.newError(showKey, f"ERR-SEM-FUNC-RET-TYPE-ERROR"))

            if(not achouRetorno):
                #print('aq')
                arrError.append(error_handler.newError(showKey, f"ERR-SEM-FUNC-RET-TYPE-ERROR"))

def verificarTipoDaVariavel(semTable, name, scope):
    
    #RESOLVER bug ONDE INTEIRO != NUM_INTEIRO
    outrasPalavrasChaves = ['NUM_INTEIRO', 'FLUTUANTE']
    if(name in outrasPalavrasChaves):
        if name == 'NUM_INTEIRO':
            return 'INTEIRO'
        return name    

    for declaracao in semTable:
        
        if declaracao['declaration'] == PalavrasChaves.declaracao_variaveis.value or declaracao['declaration'] == PalavrasChaves.declaracao_funcao.value:
            if (declaracao['scope'] == scope or declaracao['scope'] == None) and declaracao['id'] == name:
                return declaracao['type']

def verificarPricipalChamada(semTable):
    global arrError
    global showKey

    for declaracao in semTable:
        if declaracao['declaration'] == PalavrasChaves.chamada_funcao.value:
            if declaracao['id'] == 'principal':
                arrError.append(error_handler.newError(showKey, "ERR-SEM-CALL-FUNC-MAIN-NOT-ALLOWED"))
                if declaracao['scope'] == 'principal':
                    arrError.append(error_handler.newError(showKey, "WAR-SEM-CALL-REC-FUNC-MAIN"))

def verificarDeclaracaoEInicializacao(semTable):
    global arrError
    global showKey
    
    variaveisDeclaradas = {}
    variaveisInicializadas = {}
    variaveisUtilizadas = {}
    variaveisNaoDeclarada = set()
    variaveisDeclaradasEUtilizadas = {}
    variaveisDeclaradasEInicializadas = {}
    variaveisDeclaradasENaoUtilizada = set()
    variaveisDeclaradasENaoInicializada = set()


    # Itera sobre a tabela semântica para preencher as variáveis declaradas e inicializadas
    for declaracao in semTable:
        
        scope = declaracao.get('scope', None)
        var_id = declaracao.get('id', None)

        
        
        # Preenche o dicionário de variáveis declaradas por escopo
        if declaracao['declaration'] == 'declaracao_variaveis':     
            if declaracao['data'] == "Param":
                if scope not in variaveisInicializadas:
                    variaveisInicializadas[scope] = set()
                variaveisInicializadas[scope].add(var_id)
            
            if scope not in variaveisDeclaradas:
                variaveisDeclaradas[scope] = set()  # Usar set para evitar duplicatas
            if(var_id in variaveisDeclaradas[scope]): 
                arrError.append(error_handler.newError(showKey,'WAR-SEM-VAR-DECL-PREV'))
            variaveisDeclaradas[scope].add(var_id)
        
        # Preenche o dicionário de variáveis inicializadas por escopo
        elif declaracao['declaration'] == 'atribuicao':
            if scope not in variaveisInicializadas:
                variaveisInicializadas[scope] = set()
            variaveisInicializadas[scope].add(var_id)
        
        
        # Preenche o dicionário de variáveis utilizadas por escopo
        elif declaracao['declaration'] == 'var':
            if scope not in variaveisUtilizadas:
                variaveisUtilizadas[scope] = set()
            variaveisUtilizadas[scope].add(var_id)

    #print(variaveisDeclaradas)
    #print(variaveisInicializadas)
    #print(variaveisUtilizadas)
    #print("-------------------")
    

    

    for scope, vars_inicializadas in variaveisInicializadas.items():
        vars_declaradas = variaveisDeclaradas.get(scope, set())
        vars_declaradas.update(variaveisDeclaradas.get(None, set()))
        
        for var in vars_inicializadas:
            if var not in vars_declaradas:
                if(var not in variaveisNaoDeclarada):
                    arrError.append(error_handler.newError(showKey,'ERR-SEM-VAR-NOT-DECL'))
                    variaveisNaoDeclarada.add(var)
            else:
                if scope not in variaveisDeclaradasEInicializadas:
                    variaveisDeclaradasEInicializadas[scope] = set()
                variaveisDeclaradasEInicializadas[scope].add(var)

    for scope, vars_utilizadas in variaveisUtilizadas.items():
        vars_declaradas = variaveisDeclaradas.get(scope, set())
        vars_declaradas.update(variaveisDeclaradas.get(None, set()))
        
        for var in vars_utilizadas:
            
            if var not in vars_declaradas:
                if(var not in variaveisNaoDeclarada):
                    arrError.append(error_handler.newError(showKey,'ERR-SEM-VAR-NOT-DECL'))
                    variaveisNaoDeclarada.add(var)
            else:
                if scope not in variaveisDeclaradasEUtilizadas:
                    variaveisDeclaradasEUtilizadas[scope] = set()
                variaveisDeclaradasEUtilizadas[scope].add(var)
    
    #print(variaveisDeclaradasEUtilizadas)
    #print(variaveisDeclaradasEInicializadas)
    #print("-------------")

    
    for scope, vars_declaradas in variaveisDeclaradas.items():
        if scope is None:
            # Cria um conjunto vazio para armazenar todas as variáveis declaradas em todos os escopos
            vars_declaradasEUtil = set()
            vars_declaradasEInit = set()
            
            # Itera sobre todos os escopos e adiciona suas variáveis ao conjunto
            for all_scope, all_vars in variaveisDeclaradasEUtilizadas.items():
                vars_declaradasEUtil.update(all_vars)
            for all_scope, all_vars in variaveisDeclaradasEInicializadas.items():
                vars_declaradasEInit.update(all_vars)
        else:
            # Caso o escopo não seja None, continue normalmente
            vars_declaradasEUtil = variaveisDeclaradasEUtilizadas.get(scope, set())
            vars_declaradasEInit = variaveisDeclaradasEInicializadas.get(scope, set())
            vars_declaradasEInit.update(variaveisDeclaradasEInicializadas.get(None, set()))

        
        for var in vars_declaradas:
            if var not in vars_declaradasEUtil:
                if(var not in variaveisDeclaradasENaoUtilizada):
                    variaveisDeclaradasENaoUtilizada.add(var)
                    #if(var not in vars_declaradasEInit):
                    arrError.append(error_handler.newError(showKey,'WAR-SEM-VAR-DECL-NOT-USED'))
            else:
                #print(scope, var, vars_declaradasEInit)
                if(var not in vars_declaradasEInit):
                    if( var not in variaveisDeclaradasENaoInicializada):
                        variaveisDeclaradasENaoInicializada.add(var)
                        arrError.append(error_handler.newError(showKey,'WAR-SEM-VAR-DECL-NOT-INIT'))


    #print(variaveisDeclaradasENaoInicializada)
    #print(variaveisDeclaradasENaoUtilizada)

def verificacaoDeArranjos(semTable):
    global arrError
    global showKey

    for declaration in semTable:
        inteiro = True
        if declaration["declaration"] == PalavrasChaves.declaracao_variaveis.value:
            if declaration["data"] != "Param" and declaration["data"] != None:
                data = declaration['data']
                for var in data:

                    tipoVar = verificarTipoDaVariavel(semTable, var, declaration['scope'])
                    
                    if tipoVar != "INTEIRO":
                        
                        inteiro = False
        if not inteiro:
            arrError.append(error_handler.newError(showKey,'ERR-SEM-ARRAY-INDEX-NOT-INT'))

                
    

def checkingTable(semTable):
    #1.1
    verificarFuncaoPrincipal(semTable)
    #1.2
    verificarDeclaracaoDeFuncoes(semTable)
    #1.3    
    verificarParametrosFuncoes(semTable)
    #1.4
    verificarFuncoesNaoUtilizadas(semTable)
    #1.5
    verificarTipoRetorno(semTable)
    #1.6 e 1.7
    verificarPricipalChamada(semTable)
    #2
    verificarDeclaracaoEInicializacao(semTable)
    #4 arranjos Vetor
    verificacaoDeArranjos(semTable)
    #verificarVariavelDeclarada(semTable)

def semanticMain(args):
    global haveTPP
    global showKey
    global arrError

    for i in range(len(args)):
        aux = args[i].split('.')
        if aux[-1] == 'tpp':
            haveTPP = True
            locationTTP = i 
        if(args[i] == '-k'):
            showKey = True

    try:
        if len(args) < 3 and showKey:
            arrError.append(error_handler.newError(showKey, 'ERR-SEM-USE'))
            raise IOError(arrError)
        
        if not haveTPP:
            arrError.append(error_handler.newError(showKey, 'ERR-SEM-NOT-TPP'))
            raise IOError(arrError)
        
        if not os.path.exists(args[locationTTP]):
            arrError.append(error_handler.newError(showKey, 'ERR-SEM-FILE-NOT-EXISTS'))
            raise IOError(arrError)
        
        # Se chegou aqui, tudo está OK
        tree = generate_syntax_tree(args)        
        if tree:
        
            # Exemplo de renderização da árvore (descomente se necessário)
            # print(tree)
            # print(RenderTree(tree, style=AsciiStyle()).by_attr())
            # for pre, fill, node in RenderTree(root):
            #     print("%s%s" % (pre, node.name))
            
            semanticTable = creatingSemanticTable(tree)
            checkingTable(semanticTable)

        # Verifica se há erros após a análise semântica
        if len(arrError) > 0:
            raise IOError(arrError)

    except Exception as e:
        for i in range(len(e.args[0])):
            print(e.args[0][i])
            return e.args[0]
            #TODO : sem a flag -k, imprime de maneira errada

    return 0

# Programa Principal.
if __name__ == "__main__":
    semanticMain(sys.argv)