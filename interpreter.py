import re
import sys
import readline

class Var:
    def __init__(self, name):
        self.name = name
    def __repr__(self):
        return self.name

class Lam:
    def __init__(self, param, body):
        self.param = param
        self.body = body
    def __repr__(self):
        return f"(λ{self.param}.{self.body})"

class App:
    def __init__(self, func, arg):
        self.func = func
        self.arg = arg
    def __repr__(self):
        return f"({self.func} {self.arg})"

TOKEN_REGEX = re.compile(r"""
    \s*
    (?P<lambda>λ|\\|lambda) |
    (?P<dot>\.) |
    (?P<colon>\:) |
    (?P<lpar>\() |
    (?P<rpar>\)) |
    (?P<name>[a-zA-Z0-9_]+) |
    (?P<newline>\n|\r\n?) |
    (?P<ignore>\#.*?$)
""", re.VERBOSE | re.MULTILINE)

def tokenize(code):
    for match in TOKEN_REGEX.finditer(code):
        kind = match.lastgroup
        if kind in ('ignore', None):
            continue
        value = match.group(kind)
        yield (kind, value)
    yield ('EOF', '')

class Parser:
    def __init__(self, tokens):
        self.tokens = list(tokens)
        self.pos = 0
        self.env = {}

    def peek(self):
        return self.tokens[self.pos]

    def eat(self, expected_type=None):
        tok = self.tokens[self.pos]
        if expected_type and tok[0] != expected_type:
            raise SyntaxError(f"Expected {expected_type}, got {tok}")
        self.pos += 1
        return tok

    def parse_session(self):
        while self.peek()[0] != 'EOF':
            if self.peek()[0] == 'newline':
                self.eat('newline')
                continue
            stmt = self.parse_statement()
            if self.peek()[0] == 'newline':
                self.eat('newline')
            if isinstance(stmt, tuple):
                name, expr = stmt
                self.env[name] = expr
            else:
                result = evaluate(stmt, self.env)
                print(f"=> {result}")

    def parse_statement(self):
        tok = self.peek()
        if tok[0] == 'name' and self.tokens[self.pos+1][0] == 'colon':
            name = self.eat('name')[1]
            self.eat('colon')
            expr = self.parse_expression()
            return (name, expr)
        else:
            return self.parse_expression()

    def parse_expression(self):
        tok = self.peek()
        if tok[0] == 'name':
            return Var(self.eat('name')[1])
        elif tok[0] == 'lpar':
            self.eat('lpar')
            inner = self.peek()
            if inner[0] == 'lambda':
                self.eat('lambda')
                param = self.eat('name')[1]
                self.eat('dot')
                body = self.parse_expression()
                self.eat('rpar')
                return Lam(param, body)
            else:
                func = self.parse_expression()
                arg = self.parse_expression()
                self.eat('rpar')
                return App(func, arg)
        else:
            raise SyntaxError(f"Unexpected token: {tok}")

def fresh_var(name, used):
    i = 0
    while f"{name}_{i}" in used:
        i += 1
    return f"{name}_{i}"

def free_vars(expr):
    if isinstance(expr, Var):
        return {expr.name}
    elif isinstance(expr, Lam):
        return free_vars(expr.body) - {expr.param}
    elif isinstance(expr, App):
        return free_vars(expr.func) | free_vars(expr.arg)

def subst(expr, var, value):
    if isinstance(expr, Var):
        return value if expr.name == var else expr
    elif isinstance(expr, App):
        return App(subst(expr.func, var, value), subst(expr.arg, var, value))
    elif isinstance(expr, Lam):
        if expr.param == var:
            return expr 
        elif expr.param in free_vars(value):
            new_param = fresh_var(expr.param, free_vars(expr.body) | free_vars(value))
            renamed_body = subst(expr.body, expr.param, Var(new_param))
            return Lam(new_param, subst(renamed_body, var, value))
        else:
            return Lam(expr.param, subst(expr.body, var, value))

def is_reducible(expr):
    if isinstance(expr, App):
        return True
    elif isinstance(expr, Lam):
        return is_reducible(expr.body)
    return False

def evaluate(expr, env=None):
    env = env or {}

    if isinstance(expr, Var):
        return evaluate(env[expr.name], env) if expr.name in env else expr

    elif isinstance(expr, App):
        func = evaluate(expr.func, env)
        arg = evaluate(expr.arg, env)
        if isinstance(func, Lam):
            return evaluate(subst(func.body, func.param, arg), env)
        else:
            return App(func, arg)

    elif isinstance(expr, Lam):
        return Lam(expr.param, evaluate(expr.body, env))

    return expr

def repl(env=None):
    """Inicia o REPL com um ambiente opcional e suporte a histórico de comandos"""
    print("λ Lambda Calculus Interpreter")
    print("Digite 'exit' ou 'quit' para sair.")
    print("Use ':load arquivo.lam' para carregar definições.")
    
    while True:
        try:
            line = input("λ> ").strip()
            if not line:
                continue
            if line in ('exit', 'quit'):
                print("Saindo.")
                break
            elif line.startswith(':load '):
                filename = line[6:].strip()
                if not filename.endswith('.lam'):
                    filename += '.lam'
                env = load_file(filename, env)
            else:
                tokens = tokenize(line)
                parser = Parser(tokens)
                parser.env = env
                stmt = parser.parse_statement()
                if isinstance(stmt, tuple):
                    name, expr = stmt
                    env[name] = expr
                    print(f"{name} := {expr}")
                else:
                    result = evaluate(stmt, env)
                    print(f"=> {result}")
        except KeyboardInterrupt:
            print("\n[Interrompido - Ctrl+C]")
        except EOFError:
            print("\n[Encerrado - Ctrl+D]")
            break
        except Exception as e:
            print(f"Erro: {e}")

def load_file(filename, env):
    """Carrega definições de um arquivo para o ambiente e retorna o ambiente atualizado"""
    try:
        with open(filename, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#'):
                    try:
                        tokens = tokenize(line)
                        parser = Parser(tokens)
                        parser.env = env
                        stmt = parser.parse_statement()
                        if isinstance(stmt, tuple):
                            name, expr = stmt
                            env[name] = expr
                            print(f"[{filename}] {name} := {expr}")
                    except Exception as e:
                        print(f"Erro ao processar linha '{line}': {e}")
        return env
    except FileNotFoundError:
        print(f"Erro: Arquivo '{filename}' não encontrado.")
        return env
    except Exception as e:
        print(f"Erro ao ler arquivo: {e}")
        return env

if __name__ == "__main__":
    import sys
    env = {}
    
    if len(sys.argv) == 2:
        filename = sys.argv[1]
        if not filename.endswith('.lam'):
            filename += '.lam'
        env = load_file(filename, env)
    
    repl(env)
