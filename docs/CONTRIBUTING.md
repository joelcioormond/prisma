# Guia de Contribuição

Ficamos felizes com o seu interesse em contribuir para o PRISMA - Plataforma de Riscos e Maturidade! Para garantir um processo tranquilo e eficiente para todos, por favor, siga estas diretrizes.

## Como Contribuir

### Reportando Bugs

- **Verifique se o bug já não foi reportado**: Pesquise nas [Issues](https://github.com/seu-usuario/seu-repositorio/issues) para garantir que você não está criando um ticket duplicado.
- **Seja específico**: Forneça o máximo de detalhes possível. Inclua:
  - Passos para reproduzir o bug.
  - O que você esperava que acontecesse.
  - O que de fato aconteceu (incluindo screenshots e logs de erro).
  - A versão do sistema que você está usando.

### Sugerindo Melhorias

- Abra uma nova issue com o título começando com `[Sugestão] `.
- Descreva a melhoria proposta e por que ela seria útil.

### Pull Requests

1. **Fork o repositório** e clone-o localmente.
2. **Crie uma nova branch** para suas alterações:
   ```bash
   git checkout -b feature/nome-da-sua-feature
   ```
3. **Faça suas alterações**. Siga os padrões de código do projeto.
4. **Adicione testes** para suas alterações, se aplicável.
5. **Faça o commit** de suas alterações com uma mensagem clara e descritiva, seguindo o padrão [Conventional Commits](https://www.conventionalcommits.org/).
   ```bash
   git commit -m "feat: Adiciona funcionalidade de exportar para Excel"
   ```
6. **Envie suas alterações** para o seu fork:
   ```bash
   git push origin feature/nome-da-sua-feature
   ```
7. **Abra um Pull Request** no repositório principal.

## Padrões de Código

- **Python**: Siga o guia de estilo [PEP 8](https://www.python.org/dev/peps/pep-0008/).
- **JavaScript/React**: Use o [ESLint](https://eslint.org/) e [Prettier](https://prettier.io/) para manter o código consistente.
- **Comentários**: Comente o código que não for óbvio. Explique o *porquê*, não o *o quê*.

Obrigado por sua contribuição!

