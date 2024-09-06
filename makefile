# Makefile para deletar arquivos .ast.dot, .unique.ast.dot e .unique.ast.png na pasta tests

# Diretório alvo
DIR = tests

# Padrões de arquivos
AST_DOT = $(DIR)/*.ast.dot
UNIQUE_AST_DOT = $(DIR)/*.unique.ast.dot
UNIQUE_AST_PNG = $(DIR)/*.unique.ast.png

# Alvo para deletar todos os arquivos
clean:
	@echo "Deletando arquivos *.ast.dot, *.unique.ast.dot e *.unique.ast.png no diretório $(DIR)..."
	@rm -f $(AST_DOT) $(UNIQUE_AST_DOT) $(UNIQUE_AST_PNG)
	@echo "Arquivos deletados."

# Alvo padrão
.PHONY: clean
