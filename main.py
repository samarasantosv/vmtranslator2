# Importa módulos do sistema para manipulação de argumentos da linha de comando
# e operações com arquivos e diretórios.
import sys
import os

# Importa a classe responsável por ler e interpretar comandos VM.
from parser.parser import Parser

# Importa a classe responsável por gerar o código Assembly Hack.
from codewriter.codewriter import CodeWriter


def process_file(vm_path, codewriter):
    """
    Processa um único arquivo .vm.

    Para cada comando encontrado no arquivo, identifica seu tipo e chama
    o método correspondente do CodeWriter para gerar o código Assembly.
    """

    # Define o nome do arquivo atual (sem extensão).
    # Esse nome é utilizado principalmente para o segmento static.
    codewriter.set_file_name(os.path.splitext(os.path.basename(vm_path))[0])

    # Cria o parser responsável por ler o arquivo VM.
    parser = Parser(vm_path)

    # Percorre todos os comandos presentes no arquivo.
    while parser.has_more_commands():

        # Avança para o próximo comando válido.
        parser.advance()

        # Obtém o tipo do comando atual.
        cmd_type = parser.command_type()

        # Verifica o tipo do comando e chama o método correspondente.

        # Operações aritméticas e lógicas.
        if cmd_type == Parser.C_ARITHMETIC:
            codewriter.write_arithmetic(parser.arg1())

        # Comando push.
        elif cmd_type == Parser.C_PUSH:
            codewriter.write_push(parser.arg1(), parser.arg2())

        # Comando pop.
        elif cmd_type == Parser.C_POP:
            codewriter.write_pop(parser.arg1(), parser.arg2())

        # Declaração de label.
        elif cmd_type == Parser.C_LABEL:
            codewriter.write_label(parser.arg1())

        # Desvio incondicional.
        elif cmd_type == Parser.C_GOTO:
            codewriter.write_goto(parser.arg1())

        # Desvio condicional.
        elif cmd_type == Parser.C_IF:
            codewriter.write_if(parser.arg1())

        # Declaração de função.
        elif cmd_type == Parser.C_FUNCTION:
            codewriter.write_function(parser.arg1(), parser.arg2())

        # Chamada de função.
        elif cmd_type == Parser.C_CALL:
            codewriter.write_call(parser.arg1(), parser.arg2())

        # Retorno de função.
        elif cmd_type == Parser.C_RETURN:
            codewriter.write_return()


def main():
    """
    Função principal do tradutor VM.

    Verifica os argumentos recebidos, identifica se a entrada é um
    arquivo ou diretório, cria o CodeWriter e realiza a tradução.
    """

    # Verifica se foi informado um caminho de entrada.
    if len(sys.argv) < 2:
        print("Uso: python main.py <arquivo.vm | diretorio>")
        sys.exit(1)

    # Remove barras extras do final do caminho.
    input_path = sys.argv[1].rstrip("/\\")

    # Caso a entrada seja um diretório.
    if os.path.isdir(input_path):

        # Obtém todos os arquivos .vm do diretório.
        vm_files = [
            os.path.join(input_path, f)
            for f in sorted(os.listdir(input_path))
            if f.endswith(".vm")
        ]

        # Encerra o programa caso nenhum arquivo .vm seja encontrado.
        if not vm_files:
            print("Nenhum arquivo .vm encontrado no diretorio.")
            sys.exit(1)

        # Define o nome do arquivo Assembly de saída.
        output_path = os.path.join(
            input_path,
            os.path.basename(input_path) + ".asm"
        )

        # Em projetos completos é necessário gerar o código bootstrap,
        # responsável por inicializar a pilha e chamar Sys.init.
        write_bootstrap = True

    else:
        # Verifica se o arquivo informado possui extensão .vm.
        if not input_path.endswith(".vm"):
            print("O arquivo de entrada deve ter extensao .vm")
            sys.exit(1)

        # Armazena o arquivo em uma lista para processamento.
        vm_files = [input_path]

        # Define o nome do arquivo Assembly de saída.
        output_path = input_path.replace(".vm", ".asm")

        # Arquivos individuais normalmente não necessitam de bootstrap.
        write_bootstrap = False

    # Cria o objeto responsável por escrever o código Assembly.
    codewriter = CodeWriter(output_path)

    # Gera o bootstrap caso necessário.
    if write_bootstrap:
        codewriter.write_init()

    # Traduz cada arquivo VM encontrado.
    for vm_file in vm_files:
        process_file(vm_file, codewriter)

    # Fecha o arquivo de saída.
    codewriter.close()

    # Exibe mensagem indicando que a tradução foi concluída.
    print(f"Traducao concluida: {output_path}")


# Executa a função principal apenas quando este arquivo é executado diretamente.
if __name__ == "__main__":
    main()