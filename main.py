import sys
import os
from parser.parser import Parser
from codewriter.codewriter import CodeWriter


def process_file(vm_path, codewriter):
    """Traduz um único arquivo .vm, escrevendo o resultado no CodeWriter."""
    codewriter.set_file_name(os.path.splitext(os.path.basename(vm_path))[0])
    parser = Parser(vm_path)

    while parser.has_more_commands():
        parser.advance()
        cmd_type = parser.command_type()

        if cmd_type == Parser.C_ARITHMETIC:
            codewriter.write_arithmetic(parser.arg1())
        elif cmd_type == Parser.C_PUSH:
            codewriter.write_push(parser.arg1(), parser.arg2())
        elif cmd_type == Parser.C_POP:
            codewriter.write_pop(parser.arg1(), parser.arg2())
        elif cmd_type == Parser.C_LABEL:
            codewriter.write_label(parser.arg1())
        elif cmd_type == Parser.C_GOTO:
            codewriter.write_goto(parser.arg1())
        elif cmd_type == Parser.C_IF:
            codewriter.write_if(parser.arg1())
        elif cmd_type == Parser.C_FUNCTION:
            codewriter.write_function(parser.arg1(), parser.arg2())
        elif cmd_type == Parser.C_CALL:
            codewriter.write_call(parser.arg1(), parser.arg2())
        elif cmd_type == Parser.C_RETURN:
            codewriter.write_return()


def main():
    if len(sys.argv) < 2:
        print("Uso: python main.py <arquivo.vm | diretorio>")
        sys.exit(1)

    input_path = sys.argv[1].rstrip("/\\")

    if os.path.isdir(input_path):
        vm_files = [
            os.path.join(input_path, f)
            for f in sorted(os.listdir(input_path))
            if f.endswith(".vm")
        ]
        if not vm_files:
            print("Nenhum arquivo .vm encontrado no diretorio.")
            sys.exit(1)
        output_path = os.path.join(
            input_path, os.path.basename(input_path) + ".asm"
        )
        # Bootstrap só é necessário quando traduzimos um projeto completo
        # (múltiplos arquivos .vm, geralmente incluindo Sys.vm)
        write_bootstrap = True
    else:
        if not input_path.endswith(".vm"):
            print("O arquivo de entrada deve ter extensao .vm")
            sys.exit(1)
        vm_files = [input_path]
        output_path = input_path.replace(".vm", ".asm")
        write_bootstrap = False

    codewriter = CodeWriter(output_path)

    if write_bootstrap:
        codewriter.write_init()

    for vm_file in vm_files:
        process_file(vm_file, codewriter)

    codewriter.close()
    print(f"Traducao concluida: {output_path}")


if __name__ == "__main__":
    main()