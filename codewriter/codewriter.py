import os


class CodeWriter:
    """
    Responsável por traduzir comandos VM já parseados em código Assembly Hack,
    escrevendo o resultado em um arquivo .asm.
    """

    SEGMENT_BASE = {
        "local": "LCL",
        "argument": "ARG",
        "this": "THIS",
        "that": "THAT",
    }

    def __init__(self, filename):
        self.output_file = open(filename, "w")
        self.label_count = 0
        base = os.path.basename(filename)
        # Usado para compor o nome das variáveis static: Nome.i
        # (pode ser sobrescrito arquivo a arquivo com set_file_name)
        self.static_prefix = os.path.splitext(base)[0]

        # Nome da função sendo traduzida no momento (para namespacing de labels)
        self.current_function = ""
        # Contador global usado para gerar endereços de retorno únicos
        self.call_count = 0

    def _write(self, lines):
        for line in lines:
            self.output_file.write(line + "\n")

    def set_file_name(self, filename):
        """
        Deve ser chamado antes de traduzir cada arquivo .vm.
        Define o prefixo usado nas variáveis static (Nome.i).
        """
        self.static_prefix = filename

    # ---------- Comandos aritméticos e lógicos ----------

    def write_arithmetic(self, command):
        if command == "add":
            self._binary_op("M=D+M")
        elif command == "sub":
            self._binary_op("M=M-D")
        elif command == "and":
            self._binary_op("M=D&M")
        elif command == "or":
            self._binary_op("M=D|M")
        elif command == "neg":
            self._unary_op("M=-M")
        elif command == "not":
            self._unary_op("M=!M")
        elif command in ("eq", "gt", "lt"):
            self._compare(command)
        else:
            raise ValueError(f"Comando aritmético desconhecido: {command}")

    def _binary_op(self, operation):
        # Desempilha o topo (D) e opera com o novo topo (M), guardando o resultado em M
        lines = [
            "@SP",
            "AM=M-1",
            "D=M",
            "A=A-1",
            operation,
        ]
        self._write(lines)

    def _unary_op(self, operation):
        lines = [
            "@SP",
            "A=M-1",
            operation,
        ]
        self._write(lines)

    def _compare(self, command):
        jump = {"eq": "JEQ", "gt": "JGT", "lt": "JLT"}[command]
        label_true = f"TRUE_{self.label_count}"
        label_end = f"END_{self.label_count}"
        self.label_count += 1

        lines = [
            "@SP",
            "AM=M-1",
            "D=M",
            "A=A-1",
            "D=M-D",
            f"@{label_true}",
            f"D;{jump}",
            "@SP",
            "A=M-1",
            "M=0",          # falso
            f"@{label_end}",
            "0;JMP",
            f"({label_true})",
            "@SP",
            "A=M-1",
            "M=-1",         # verdadeiro
            f"({label_end})",
        ]
        self._write(lines)

    # ---------- push / pop ----------

    def write_push(self, segment, index):
        if segment == "constant":
            lines = [
                f"@{index}",
                "D=A",
            ]
        elif segment in self.SEGMENT_BASE:
            base = self.SEGMENT_BASE[segment]
            lines = [
                f"@{index}",
                "D=A",
                f"@{base}",
                "A=D+M",
                "D=M",
            ]
        elif segment == "temp":
            lines = [
                f"@{5 + index}",
                "D=M",
            ]
        elif segment == "pointer":
            reg = "THIS" if index == 0 else "THAT"
            lines = [
                f"@{reg}",
                "D=M",
            ]
        elif segment == "static":
            lines = [
                f"@{self.static_prefix}.{index}",
                "D=M",
            ]
        else:
            raise ValueError(f"Segmento desconhecido: {segment}")

        lines += [
            "@SP",
            "A=M",
            "M=D",
            "@SP",
            "M=M+1",
        ]
        self._write(lines)

    def write_pop(self, segment, index):
        if segment in self.SEGMENT_BASE:
            base = self.SEGMENT_BASE[segment]
            lines = [
                f"@{index}",
                "D=A",
                f"@{base}",
                "D=D+M",
                "@R13",
                "M=D",
                "@SP",
                "AM=M-1",
                "D=M",
                "@R13",
                "A=M",
                "M=D",
            ]
        elif segment == "temp":
            lines = [
                "@SP",
                "AM=M-1",
                "D=M",
                f"@{5 + index}",
                "M=D",
            ]
        elif segment == "pointer":
            reg = "THIS" if index == 0 else "THAT"
            lines = [
                "@SP",
                "AM=M-1",
                "D=M",
                f"@{reg}",
                "M=D",
            ]
        elif segment == "static":
            lines = [
                "@SP",
                "AM=M-1",
                "D=M",
                f"@{self.static_prefix}.{index}",
                "M=D",
            ]
        else:
            raise ValueError(f"Segmento desconhecido para pop: {segment}")

        self._write(lines)

    # ---------- Bootstrap ----------

    def write_init(self):
        """
        Código de inicialização da VM: SP = 256 e chamada a Sys.init.
        Deve ser escrito uma única vez, no início do .asm, apenas quando
        traduzimos um DIRETÓRIO (múltiplos arquivos .vm).
        """
        lines = [
            "@256",
            "D=A",
            "@SP",
            "M=D",
        ]
        self._write(lines)
        self.write_call("Sys.init", 0)

    # ---------- Controle de fluxo ----------

    def write_label(self, label):
        # Namespacing pelo nome da função evita colisão entre funções distintas
        self._write([f"({self.current_function}${label})"])

    def write_goto(self, label):
        lines = [
            f"@{self.current_function}${label}",
            "0;JMP",
        ]
        self._write(lines)

    def write_if(self, label):
        # Desempilha o topo; se for diferente de 0 (verdadeiro), salta
        lines = [
            "@SP",
            "AM=M-1",
            "D=M",
            f"@{self.current_function}${label}",
            "D;JNE",
        ]
        self._write(lines)

    # ---------- Funções ----------

    def write_function(self, function_name, n_locals):
        self.current_function = function_name
        lines = [f"({function_name})"]
        # Empilha 0 para cada variável local (inicialização)
        for _ in range(n_locals):
            lines += [
                "@SP",
                "A=M",
                "M=0",
                "@SP",
                "M=M+1",
            ]
        self._write(lines)

    def write_call(self, function_name, n_args):
        return_label = f"{function_name}$ret.{self.call_count}"
        self.call_count += 1

        lines = [
            # Empilha o endereço de retorno
            f"@{return_label}",
            "D=A",
            "@SP",
            "A=M",
            "M=D",
            "@SP",
            "M=M+1",
        ]
        # Empilha LCL, ARG, THIS, THAT do chamador
        for segment in ("LCL", "ARG", "THIS", "THAT"):
            lines += [
                f"@{segment}",
                "D=M",
                "@SP",
                "A=M",
                "M=D",
                "@SP",
                "M=M+1",
            ]
        lines += [
            # ARG = SP - 5 - nArgs
            "@SP",
            "D=M",
            f"@{5 + n_args}",
            "D=D-A",
            "@ARG",
            "M=D",
            # LCL = SP
            "@SP",
            "D=M",
            "@LCL",
            "M=D",
            # goto function_name
            f"@{function_name}",
            "0;JMP",
            # rótulo de retorno
            f"({return_label})",
        ]
        self._write(lines)

    def write_return(self):
        lines = [
            # R13 (endFrame) = LCL
            "@LCL",
            "D=M",
            "@R13",
            "M=D",
            # R14 (retAddr) = *(endFrame - 5)
            "@5",
            "A=D-A",
            "D=M",
            "@R14",
            "M=D",
            # *ARG = pop() -> valor de retorno vai para a posição do 1º argumento
            "@SP",
            "AM=M-1",
            "D=M",
            "@ARG",
            "A=M",
            "M=D",
            # SP = ARG + 1
            "@ARG",
            "D=M+1",
            "@SP",
            "M=D",
            # THAT = *(endFrame - 1)
            "@R13",
            "AM=M-1",
            "D=M",
            "@THAT",
            "M=D",
            # THIS = *(endFrame - 2)
            "@R13",
            "AM=M-1",
            "D=M",
            "@THIS",
            "M=D",
            # ARG = *(endFrame - 3)
            "@R13",
            "AM=M-1",
            "D=M",
            "@ARG",
            "M=D",
            # LCL = *(endFrame - 4)
            "@R13",
            "AM=M-1",
            "D=M",
            "@LCL",
            "M=D",
            # goto retAddr
            "@R14",
            "A=M",
            "0;JMP",
        ]
        self._write(lines)

    def close(self):
        self.output_file.close()