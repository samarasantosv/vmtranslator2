class Parser:
    """
    Responsável por ler um arquivo .vm, remover comentários/linhas em branco
    e quebrar cada comando em seus componentes (tipo, arg1, arg2).
    """

    C_ARITHMETIC = "C_ARITHMETIC"
    C_PUSH = "C_PUSH"
    C_POP = "C_POP"
    C_LABEL = "C_LABEL"
    C_GOTO = "C_GOTO"
    C_IF = "C_IF"
    C_FUNCTION = "C_FUNCTION"
    C_CALL = "C_CALL"
    C_RETURN = "C_RETURN"

    ARITHMETIC_COMMANDS = {"add", "sub", "neg", "eq", "gt", "lt", "and", "or", "not"}

    def __init__(self, filename):
        with open(filename, "r") as f:
            raw_lines = f.readlines()

        # Remove comentários (tudo depois de "//") e linhas vazias
        self.commands = []
        for line in raw_lines:
            line = line.split("//")[0].strip()
            if line:
                self.commands.append(line)

        self.index = -1
        self.current_command = None

    def has_more_commands(self):
        """Retorna True se ainda existem comandos a processar."""
        return self.index < len(self.commands) - 1

    def advance(self):
        """Avança para o próximo comando e o torna o comando atual."""
        self.index += 1
        self.current_command = self.commands[self.index]

    def command_type(self):
        """Retorna o tipo do comando atual: C_ARITHMETIC, C_PUSH ou C_POP."""
        parts = self.current_command.split()
        cmd = parts[0]

        if cmd in self.ARITHMETIC_COMMANDS:
            return self.C_ARITHMETIC
        elif cmd == "push":
            return self.C_PUSH
        elif cmd == "pop":
            return self.C_POP
        elif cmd == "label":
            return self.C_LABEL
        elif cmd == "goto":
            return self.C_GOTO
        elif cmd == "if-goto":
            return self.C_IF
        elif cmd == "function":
            return self.C_FUNCTION
        elif cmd == "call":
            return self.C_CALL
        elif cmd == "return":
            return self.C_RETURN
        else:
            raise ValueError(f"Comando desconhecido: {cmd}")

    def arg1(self):
        """
        Retorna o primeiro argumento do comando atual.
        Para C_ARITHMETIC, retorna o próprio comando (ex: 'add').
        Não deve ser chamado para C_RETURN.
        """
        cmd_type = self.command_type()
        if cmd_type == self.C_RETURN:
            raise ValueError("C_RETURN não possui arg1")

        parts = self.current_command.split()
        if cmd_type == self.C_ARITHMETIC:
            return parts[0]
        return parts[1]

    def arg2(self):
        """
        Retorna o segundo argumento (índice / número).
        Válido apenas para C_PUSH, C_POP, C_FUNCTION e C_CALL.
        """
        parts = self.current_command.split()
        return int(parts[2])