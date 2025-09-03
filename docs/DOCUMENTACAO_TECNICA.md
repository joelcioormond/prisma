# Documentação Técnica - PRISMA-Plataforma de Riscos e Maturidade

**Versão do Documento:** 1.0
**Data:** 02 de Setembro de 2025

## 1. Introdução

Este documento fornece uma visão técnica detalhada do **PRISMA - Plataforma de Riscos e Maturidade**. O objetivo é servir como um guia para desenvolvedores, mantenedores e administradores de sistema, cobrindo a arquitetura, componentes, configuração e deploy da aplicação.

O sistema foi projetado para ser robusto, escalável e de fácil manutenção, utilizando tecnologias modernas e práticas de desenvolvimento consagradas.

### 1.1. Visão Geral da Arquitetura

A aplicação segue uma arquitetura de microsserviços desacoplada, composta por dois componentes principais:

- **Backend (API RESTful):** Uma API desenvolvida em Python com o framework Flask. É responsável por toda a lógica de negócio, autenticação, acesso ao banco de dados e geração de relatórios.
- **Frontend (Single-Page Application - SPA):** Uma aplicação rica e interativa desenvolvida em JavaScript com a biblioteca React. É responsável por toda a interface do usuário e interação com o cliente.

Essa separação clara de responsabilidades (backend e frontend) permite o desenvolvimento e a implantação independentes de cada parte, facilitando a manutenção e a escalabilidade.

### 1.2. Stack de Tecnologias

| Camada | Tecnologia | Versão | Descrição |
|---|---|---|---|
| **Backend** | Python | 3.8+ | Linguagem de programação principal |
| | Flask | 3.0.0 | Micro-framework web para a API |
| | Gunicorn | 21.2.0 | Servidor WSGI para produção |
| **Frontend** | JavaScript | ES6+ | Linguagem de programação principal |
| | React | 18+ | Biblioteca para construção da interface de usuário |
| | Bootstrap | 5+ | Framework CSS para estilização e componentes |
| **Banco de Dados** | PostgreSQL | 12+ | Banco de dados relacional para produção |
| | SQLite | 3+ | Banco de dados para desenvolvimento |
| **Autenticação** | JWT | - | Padrão para transmissão segura de informações |
| **Geração de PDF** | WeasyPrint | 60.0 | Engine para conversão de HTML/CSS para PDF |
| **Ambiente** | Docker | Opcional | Containerização para deploy simplificado |





## 2. Arquitetura do Backend

O backend é o cérebro do sistema, construído sobre o Flask, um micro-framework Python conhecido por sua simplicidade e extensibilidade. A estrutura do projeto foi organizada para promover a modularidade e a separação de conceitos.

### 2.1. Estrutura de Diretórios

```
backend/
├── src/                      # Código fonte da aplicação
│   ├── __init__.py           # Transforma o diretório em um pacote Python
│   ├── main.py               # Factory da aplicação e definição das rotas
│   ├── config.py             # Módulo de configuração (produção, dev, teste)
│   ├── database.py           # Módulo de gerenciamento de banco de dados
│   └── pdf_generator.py      # Lógica para geração de relatórios em PDF
├── venv/                     # Ambiente virtual Python
├── uploads/                  # Diretório para arquivos de evidência
├── run.py                    # Ponto de entrada para executar o servidor
├── requirements.txt          # Lista de dependências Python
├── Procfile                  # Para deploy em plataformas como Heroku
├── .env                      # Arquivo de variáveis de ambiente (não versionado)
└── .env.example              # Exemplo de arquivo .env
```

### 2.2. Módulos Principais

- **`main.py`**: Utiliza o padrão *Application Factory* (`create_app`) para inicializar a aplicação. Isso permite criar múltiplas instâncias da aplicação com diferentes configurações, o que é essencial para testes e flexibilidade no deploy. Todas as rotas da API são definidas aqui.

- **`config.py`**: Centraliza todas as configurações da aplicação. Utiliza classes para separar configurações de diferentes ambientes (Desenvolvimento, Produção, Testes). As configurações são carregadas a partir de variáveis de ambiente, seguindo as melhores práticas do [The Twelve-Factor App](https://12factor.net/config).

- **`database.py`**: Abstrai a complexidade da conexão e manipulação do banco de dados. A classe `DatabaseManager` fornece uma interface unificada para interagir tanto com SQLite quanto com PostgreSQL. O uso de um *context manager* (`@contextmanager`) garante que as conexões sejam sempre fechadas corretamente, prevenindo vazamento de recursos.

- **`pdf_generator.py`**: Isola a lógica de criação de relatórios em PDF. Atualmente, utiliza a biblioteca WeasyPrint, que renderiza HTML e CSS para PDF, permitindo a criação de relatórios complexos e bem estilizados a partir de templates.

### 2.3. Fluxo de Requisição

1. Uma requisição HTTP chega ao servidor WSGI (Gunicorn em produção).
2. O Gunicorn repassa a requisição para a aplicação Flask (`app`).
3. O Flask faz o roteamento da URL para a função (view) correspondente (ex: `/api/auth/login` para a função `login`).
4. A função da view processa a requisição, interagindo com o `DatabaseManager` para operações de banco de dados.
5. Os dados são processados e uma resposta JSON é gerada.
6. O middleware do Flask-CORS adiciona os headers CORS necessários à resposta.
7. A resposta é enviada de volta ao cliente.

### 2.4. Configuração para PostgreSQL

A transição de SQLite para PostgreSQL é gerenciada inteiramente pelo `config.py` e `database.py`.

1. **Configuração:** No arquivo `.env`, a variável `DATABASE_TYPE` deve ser alterada para `postgresql` e as variáveis `POSTGRES_*` devem ser preenchidas com as credenciais do banco de dados.

2. **Conexão:** O `DatabaseManager` detecta o tipo de banco e utiliza a biblioteca `psycopg2-binary` para se conectar ao PostgreSQL.

3. **SQL:** O `database.py` contém as instruções SQL de `CREATE TABLE` específicas para cada dialeto (SQLite e PostgreSQL), garantindo a compatibilidade dos tipos de dados (ex: `INTEGER PRIMARY KEY AUTOINCREMENT` no SQLite vs. `SERIAL PRIMARY KEY` no PostgreSQL).




## 3. Arquitetura do Frontend

O frontend é uma Single-Page Application (SPA) construída com React, projetada para oferecer uma experiência de usuário fluida e responsiva.

### 3.1. Estrutura de Diretórios (Recomendada)

```
frontend/
├── public/                   # Arquivos estáticos (index.html, favicon, etc.)
│   ├── index.html
│   └── brasao-mt.png
|   └── modelo_completo_final2.json
├── src/                      # Código fonte da aplicação
│   ├── components/           # Componentes React reutilizáveis
│   │   ├── LoginSimples.js
│   │   ├── Dashboard.js
│   │   ├── FormularioAvaliacao.js
│   │   └── ...
│   ├── contexts/             # Contextos React para gerenciamento de estado
│   │   └── AuthContext.js
│   ├── services/             # Lógica de comunicação com a API
│   │   └── api.js
│   ├── App.js                # Componente raiz e roteamento
│   ├── index.js              # Ponto de entrada da aplicação React
│   └── index.css             # Estilos globais
├── package.json              # Dependências e scripts do projeto
├── .env                      # Variáveis de ambiente do frontend
└── .gitignore
```

### 3.2. Gerenciamento de Estado

O estado global da aplicação, especialmente o estado de autenticação do usuário, é gerenciado através do **React Context API**.

- **`AuthContext.js`**: Este contexto provê informações sobre o usuário logado (`user`), o status de carregamento (`loading`) e as funções de `login` e `logout` para todos os componentes aninhados. O hook customizado `useAuth` simplifica o acesso a este contexto.

O estado local dos componentes (como dados de formulários) é gerenciado com o hook `useState`.

### 3.3. Roteamento

O roteamento da aplicação é gerenciado pela biblioteca **React Router DOM**.

- **`App.js`**: Define todas as rotas da aplicação, incluindo rotas públicas (como `/login`) e rotas protegidas.
- **Rotas Protegidas**: Um componente `RotaProtegida` é utilizado para envolver as rotas que exigem autenticação. Ele verifica o estado do usuário no `AuthContext` e redireciona para a página de login caso o usuário não esteja autenticado.

### 3.4. Comunicação com a API

Toda a comunicação com o backend é feita através de requisições HTTP (fetch API) para a API RESTful.

- **URLs Dinâmicas**: Para garantir que o frontend funcione em qualquer ambiente (desenvolvimento local ou produção), as URLs da API são construídas dinamicamente usando `window.location.hostname`.
  ```javascript
  const apiUrl = `http://${window.location.hostname}:5000/api/auth/login`;
  ```
- **Tratamento de Erros**: As requisições são envolvidas em blocos `try...catch` para lidar com erros de rede e respostas inesperadas da API, fornecendo feedback adequado ao usuário.




## 4. Segurança

A segurança foi uma preocupação central no desenvolvimento do sistema.

### 4.1. Autenticação e Autorização

- **Hashing de Senhas**: As senhas dos usuários nunca são armazenadas em texto plano. Elas são hasheadas no backend usando o algoritmo **SHA-256** antes de serem salvas no banco de dados.
- **Autenticação de Rotas**: O frontend envia o email do usuário no header `X-User-Email` em requisições para rotas protegidas. O backend utiliza este header para verificar a identidade e as permissões do usuário antes de processar a requisição.
- **Controle de Acesso Baseado em Perfil (RBAC)**: O sistema utiliza perfis (`admin`, `gestor`, `usuario`) para controlar o acesso a diferentes funcionalidades. As permissões são definidas no backend e enviadas ao frontend no momento do login.

### 4.2. CORS (Cross-Origin Resource Sharing)

O backend utiliza a extensão **Flask-CORS** para gerenciar as políticas de CORS, permitindo que o frontend (hospedado em um domínio diferente, como `localhost:3000`) faça requisições seguras para a API (hospedada em `localhost:5000`).

### 4.3. Variáveis de Ambiente

Informações sensíveis como chaves de API, segredos e credenciais de banco de dados não são codificadas diretamente no código. Elas são gerenciadas através de variáveis de ambiente, carregadas a partir de um arquivo `.env` (que não deve ser versionado no Git).

## 5. Deploy

### 5.1. Configuração de Produção

1. **Variáveis de Ambiente**: Crie um arquivo `.env` no servidor de produção e preencha com as configurações de produção, incluindo:
   - `FLASK_ENV=production`
   - `SECRET_KEY` com um valor longo e aleatório.
   - `DATABASE_TYPE=postgresql` e as credenciais do banco de dados PostgreSQL.
   - `CORS_ORIGINS` com a URL do seu frontend em produção.

2. **Servidor WSGI**: Em produção, o servidor de desenvolvimento do Flask não deve ser usado. O projeto está configurado para usar o **Gunicorn** como servidor WSGI. O `Procfile` (`web: gunicorn run:app`) define como iniciar a aplicação.

3. **Servir o Frontend**: O frontend (build de produção) deve ser servido por um servidor web como Nginx ou Apache, ou através de uma plataforma de hospedagem de sites estáticos como Vercel ou Netlify.

### 5.2. Exemplo com Docker (Opcional)

Para um deploy mais robusto e isolado, a aplicação pode ser containerizada com Docker.

**Dockerfile para o Backend:**
```Dockerfile
# Usar uma imagem base do Python
FROM python:3.9-slim

# Definir o diretório de trabalho
WORKDIR /app

# Copiar o arquivo de dependências
COPY requirements.txt .

# Instalar as dependências
RUN pip install --no-cache-dir -r requirements.txt

# Copiar o resto do código da aplicação
COPY . .

# Expor a porta que o Gunicorn irá rodar
EXPOSE 5000

# Comando para iniciar a aplicação
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "run:app"]
```

Este Dockerfile pode ser usado para construir uma imagem Docker do backend e implantá-la em qualquer ambiente que suporte containers.


