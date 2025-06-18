# Lambda Calculus Interpreter

Esse repositório contém a implementação de um interpretador de lambda calculus. O código sempre espera o uso de `()`, tanto para iniciar quanto em separações das funções.

O código foi escrito em `python3` e pode salvar expressões usando `nome: expressão`. Além disso, pode carregar expressões de um arquivo `.lam`. Isso pode ser feito de duas formas: 
- Como Argumento:
```
python3 interpreter.py arquivo.lam
```
- Como um `load` interno:
```
λ> :load arquivo.lam
```

Além disso, há algumas implementações básicas de prompt, como `Ctrl + C` para interromper e o que foi escrito e pular para uma nova linha e `Ctrl + D` para interromper o programa. Também tem instruções inicias de como usar o interpretador.

