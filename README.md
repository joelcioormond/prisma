# PRISMA - Plataforma de Riscos e Maturidade

**Versão:** 1.0
**Responsável:** Joelcio Caires da Silva Ormond

## Descrição

Este sistema permite que unidades realizem autoavaliação da maturidade de seus processos de gestão de riscos. A avaliação é baseada na ISO 31000, sendo organizada em um modelo de maturidade com diferentes níveis, KPAs (Key Process Areas) e atividades.

## Funcionalidades

- **Autoavaliação de Maturidade**: Formulário completo para avaliação dos processos de gestão de riscos.
- **Gestão de Usuários e Órgãos**: Interface administrativa para gerenciar usuários e órgãos.
- **Relatórios Completos**: Geração de relatórios individuais e consolidados em PDF.
- **Autenticação Segura**: Sistema de login com email e senha, com validação e segurança.
- **Suporte a Banco de Dados**: Compatível com SQLite (desenvolvimento) e PostgreSQL (produção).

## Estrutura do Projeto

O projeto é dividido em duas partes principais:

- **Backend**: API RESTful desenvolvida em Python com Flask.
- **Frontend**: Aplicação de página única (SPA) desenvolvida em React.js.

## Como Executar

### Pré-requisitos

- Python 3.8+
- Node.js 16+
- PostgreSQL (para produção)

### Backend

1. **Clone o repositório:**
   ```bash
   git clone [URL_DO_REPOSITORIO]
   cd [NOME_DO_PROJETO]/backend
   ```

2. **Crie e ative um ambiente virtual:**
   ```bash
   python -m venv venv
   source venv/bin/activate  # Linux/macOS
   venv\Scripts\activate      # Windows
   ```

3. **Instale as dependências:**
   ```bash
   pip install -r requirements.txt
   ```
   
   ou
   
    ```bash
   python -m pip install -r requirements.txt
   ```
   
4. **Execute o servidor:**
   ```bash
   python src/main.py
   ```

### Frontend

1. **Navegue para a pasta do frontend:**
   ```bash
   cd ../frontend
   ```

2. **Instale as dependências:**
   ```bash
   npm install
   ```

3. **Execute a aplicação:**
   ```bash
   npm start
   ```

A aplicação estará disponível em `http://localhost:3000`.

## Licença

Este projeto é licenciado sob a licença MIT - veja o arquivo [LICENSE](LICENSE) para mais detalhes.

