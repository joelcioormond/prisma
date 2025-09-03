# Documentação Técnica - PRISMA-Plataforma de Riscos e Maturidade

**Versão do Documento:** 1.0
**Data:** 02 de Setembro de 2025

## 1. Introdução

Esta documentação técnica detalha a arquitetura, organização do código, tecnologias e procedimentos para a configuração e execução da plataforma PRISMA (Plataforma de Riscos e Maturidade). O objetivo é fornecer a desenvolvedores e mantenedores as informações necessárias para compreender, manter e evoluir o sistema de forma eficiente.

O PRISMA é uma aplicação web full-stack projetada para permitir que organizações realizem autoavaliações de maturidade em gestão de riscos, com base na norma ISO 31000. O sistema é composto por um backend em Python (Flask) que serve uma API RESTful e um frontend em React.js que consome essa API para fornecer uma interface de usuário rica e interativa.




## 2. Arquitetura Geral

A aplicação segue uma arquitetura cliente-servidor desacoplada, onde o frontend (cliente) é totalmente independente do backend (servidor). A comunicação entre eles ocorre exclusivamente através de chamadas à API RESTful.

- **Backend**: Uma API RESTful desenvolvida em Python com o microframework Flask. É responsável por toda a lógica de negócio, incluindo autenticação de usuários, gerenciamento de avaliações, persistência de dados e geração de relatórios.

- **Frontend**: Uma Single-Page Application (SPA) construída com React.js. É responsável por toda a interface do usuário, renderizando os componentes, gerenciando o estado da aplicação e realizando as chamadas para a API do backend.

- **Banco de Dados**: O sistema utiliza SQLite como banco de dados padrão para simplicidade e facilidade de configuração em ambientes de desenvolvimento. O banco de dados é armazenado em um arquivo local gerenciado pelo backend.

### Estrutura de Diretórios

A estrutura de diretórios do projeto foi organizada para separar claramente as responsabilidades do backend e do frontend:

```
prisma/
├── backend/                 # Código-fonte da API (Python/Flask)
│   ├── src/
│   │   ├── main.py         # Arquivo principal da aplicação Flask com as rotas da API
│   │   └── pdf_generator.py # Módulo para geração de relatórios em PDF
│   └── requirements.txt    # Dependências do ambiente Python
├── frontend/               # Código-fonte da interface (React.js)
│   ├── public/             # Arquivos estáticos (HTML, imagens, manifestos)
│   ├── src/
│   │   ├── components/     # Componentes reutilizáveis da interface
│   │   ├── contexts/       # Contextos do React (ex: autenticação)
│   │   ├── App.js          # Componente raiz da aplicação
│   │   ├── index.js        # Ponto de entrada do React
│   │   └── ...             # Outros arquivos de configuração e estilos
│   └── package.json        # Dependências e scripts do Node.js
├── docs/                   # Pasta para documentação adicional
├── .gitignore              # Configuração de arquivos a serem ignorados pelo Git
├── LICENSE                 # Licença de uso do software
└── README.md               # Documentação principal do projeto
```

## 3. Backend (API RESTful)

O backend é construído em Python 3.8+ com Flask, um microframework leve e flexível.

### 3.1. Tecnologias Utilizadas

- **Flask**: Framework web para a construção da API.
- **Flask-CORS**: Extensão para lidar com Cross-Origin Resource Sharing (CORS), permitindo que o frontend (em um domínio diferente) acesse a API.
- **SQLite**: Banco de dados relacional embarcado, utilizado como padrão.
- **ReportLab**: Biblioteca para a geração programática de documentos PDF, utilizada para criar os relatórios de avaliação.
- **Werkzeug**: Biblioteca de utilitários WSGI, utilizada pelo Flask para o tratamento de senhas (hash e verificação).

### 3.2. Arquivos Principais

- **`backend/src/main.py`**: Este é o coração da aplicação backend. Ele é responsável por:
  - Inicializar a aplicação Flask.
  - Configurar o banco de dados SQLite e criar as tabelas necessárias na primeira execução.
  - Definir todas as rotas (endpoints) da API, como `/login`, `/usuarios`, `/avaliacoes`, etc.
  - Implementar a lógica para cada rota, incluindo a interação com o banco de dados.

- **`backend/src/pdf_generator.py`**: Módulo dedicado exclusivamente à criação dos relatórios em PDF. Ele contém a lógica para:
  - Receber os dados de uma avaliação.
  - Estruturar o layout do relatório, incluindo cabeçalhos, parágrafos, tabelas e gráficos.
  - Gerar o arquivo PDF e retorná-lo como uma resposta da API.

- **`backend/requirements.txt`**: Lista todas as bibliotecas Python necessárias para que o backend funcione. O ambiente virtual pode ser populado com o comando `pip install -r requirements.txt`.

### 3.3. Banco de Dados

O banco de dados é configurado para usar SQLite por padrão. O arquivo do banco de dados, chamado `prisma.db`, é criado automaticamente na pasta raiz do backend (`backend/`) na primeira vez que a aplicação é executada. Todas as tabelas (`usuarios`, `orgaos`, `avaliacoes`, etc.) são também criadas nesse momento, caso não existam.

Não há necessidade de configuração manual para o banco de dados em ambiente de desenvolvimento.

## 4. Frontend (React.js)

O frontend é uma aplicação moderna construída com React.js, proporcionando uma experiência de usuário fluida e responsiva.

### 4.1. Tecnologias Utilizadas

- **React**: Biblioteca JavaScript para a construção de interfaces de usuário.
- **React Router**: Para o gerenciamento de rotas no lado do cliente, permitindo a navegação entre diferentes "páginas" da SPA.
- **Bootstrap**: Framework de CSS para a criação de um design responsivo e estilizado.
- **Chart.js**: Biblioteca para a criação de gráficos e visualizações de dados interativas, utilizada nos dashboards e relatórios.
- **Axios** (ou `fetch` nativo): Para realizar as requisições HTTP para a API do backend.

### 4.2. Estrutura de Arquivos

- **`frontend/src/components/`**: Contém todos os componentes React reutilizáveis que formam a interface, como formulários, modais, tabelas, cabeçalhos, etc. A componentização permite um código mais limpo e de fácil manutenção.

- **`frontend/src/contexts/`**: Armazena os contextos do React, como o `AuthContext`, que é responsável por gerenciar o estado de autenticação do usuário em toda a aplicação.

- **`frontend/src/App.js`**: É o componente principal que organiza o layout geral e o roteamento da aplicação.

- **`frontend/src/index.js`**: É o ponto de entrada da aplicação React, onde o componente `App` é renderizado no DOM.

- **`frontend/public/`**: Contém os arquivos estáticos que não são processados pelo Webpack, como o `index.html` (template base), `favicon.ico`, e imagens.

- **`frontend/package.json`**: Arquivo de configuração do Node.js que lista as dependências do projeto e define scripts úteis (como `npm start`, `npm build`).




## 5. Instalação e Execução

Siga os passos abaixo para configurar e executar o ambiente de desenvolvimento localmente.

### 5.1. Pré-requisitos

- **Python 3.8+**
- **Node.js 16+**
- **Git**

### 5.2. Configuração do Backend

1.  **Clone o repositório:**
    ```shell
    git clone https://github.com/joelcioormond/prisma.git
    cd prisma/backend
    ```

2.  **Crie e ative um ambiente virtual:**
    ```shell
    # Em Linux/macOS
    python3 -m venv venv
    source venv/bin/activate

    # Em Windows
    python -m venv venv
    venv\Scripts\activate
    ```

3.  **Instale as dependências:**
    ```shell
    pip install -r requirements.txt
    ```

4.  **Execute o servidor:**
    ```shell
    python src/main.py
    ```

    O servidor backend estará em execução e acessível em `http://localhost:5000`.

### 5.3. Configuração do Frontend

1.  **Abra um novo terminal e navegue até a pasta do frontend:**
    ```shell
    cd prisma/frontend
    ```

2.  **Instale as dependências:**
    ```shell
    npm install
    ```

3.  **Execute a aplicação:**
    ```shell
    npm start
    ```

    A aplicação frontend será aberta automaticamente no seu navegador padrão e estará acessível em `http://localhost:3000`.

## 6. Endpoints da API

A seguir, uma descrição dos principais endpoints fornecidos pelo backend.

- `POST /login`: Autentica um usuário e retorna um token de sessão.
- `GET /usuarios`: Retorna a lista de todos os usuários (requer autenticação de administrador).
- `POST /usuarios`: Cria um novo usuário.
- `PUT /usuarios/<id>`: Atualiza um usuário existente.
- `DELETE /usuarios/<id>`: Deleta um usuário.
- `GET /orgaos`: Retorna a lista de órgãos.
- `POST /avaliacoes`: Submete uma nova avaliação de maturidade.
- `GET /avaliacoes`: Retorna o histórico de avaliações de um usuário ou todas as avaliações (para admin).
- `GET /relatorio_individual/<id>`: Gera e retorna o relatório de uma avaliação específica em formato PDF.

> **Nota:** Para uma lista completa e detalhada de todos os endpoints, consulte o código-fonte em `backend/src/main.py`.


