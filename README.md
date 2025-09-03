# PRISMA - Plataforma de Riscos e Maturidade

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://www.python.org/)
[![React](https://img.shields.io/badge/React-18.2+-61DAFB.svg)](https://reactjs.org/)
[![Flask](https://img.shields.io/badge/Flask-3.0+-000000.svg)](https://flask.palletsprojects.com/)

## 📋 Sobre o Projeto

O **PRISMA** é uma plataforma web completa para avaliação da maturidade em gestão de riscos organizacionais. Baseado na **ISO 31000**, o sistema permite que organizações realizem autoavaliações estruturadas de seus processos de gestão de riscos através de um modelo de maturidade com diferentes níveis, KPAs (Key Process Areas) e atividades específicas.

### 🎯 Objetivos

- Facilitar a autoavaliação da maturidade em gestão de riscos
- Fornecer relatórios detalhados e insights sobre o nível de maturidade
- Permitir o acompanhamento da evolução ao longo do tempo
- Oferecer uma interface intuitiva e acessível

## ✨ Funcionalidades Principais

### 🔍 **Avaliação de Maturidade**
- Formulário estruturado baseado na ISO 31000
- Modelo de maturidade com 5 níveis progressivos
- Avaliação por KPAs (Key Process Areas)
- Sistema de evidências e justificativas

### 👥 **Gestão Administrativa**
- Gerenciamento de usuários e perfis
- Controle de órgãos e unidades organizacionais
- Sistema de autenticação seguro
- Controle de acesso baseado em permissões

### 📊 **Relatórios e Analytics**
- Relatórios individuais detalhados em PDF
- Relatórios consolidados para administradores
- Gráficos e visualizações interativas
- Histórico de avaliações e evolução temporal

### 🔒 **Segurança**
- Autenticação com email e senha
- Criptografia de senhas (SHA256)
- Controle de sessões
- Validação de dados de entrada

## 🏗️ Arquitetura do Sistema

```
prisma/
├── backend/                 # API RESTful (Python/Flask)
│   ├── src/
│   │   ├── main.py         # Aplicação principal Flask
│   │   └── pdf_generator.py # Geração de relatórios PDF
│   └── requirements.txt    # Dependências Python
├── frontend/               # Interface web (React.js)
│   ├── public/            # Arquivos estáticos
│   ├── src/
│   │   ├── components/    # Componentes React
│   │   ├── contexts/      # Contextos (AuthContext)
│   │   ├── App.js        # Componente principal
│   │   ├── index.js      # Ponto de entrada
│   │   ├── index.css     # Estilos globais
│   │   └── setupProxy.js # Configuração de proxy
│   ├── package.json      # Dependências Node.js
│   └── package-lock.json # Lock de versões
├── docs/                 # Documentação
├── .gitignore           # Arquivos ignorados pelo Git
├── LICENSE              # Licença MIT
└── README.md           # Este arquivo
```

## 🚀 Como Executar

### 📋 Pré-requisitos

- **Python 3.8+**
- **Node.js 16+**
- **SQLite** (incluído no Python) ou **PostgreSQL** (para produção)

### 🔧 Configuração do Backend

1. **Clone o repositório:**
   ```bash
   git clone https://github.com/joelcioormond/prisma.git
   cd prisma/backend
   ```

2. **Crie e ative um ambiente virtual:**
   ```bash
   python -m venv venv
   
   # Linux/macOS
   source venv/bin/activate
   
   # Windows
   venv\Scripts\activate
   ```

3. **Instale as dependências:**
   ```bash
   pip install -r requirements.txt
   ```
   ou
   ```bash
   python -m pip install -r requirements.txt
   ```

5. **Execute o servidor:**
   ```bash
   python src/main.py
   ```

   O backend estará disponível em `http://localhost:5000`

### 🎨 Configuração do Frontend

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

   O frontend estará disponível em `http://localhost:3000`

## 🗄️ Configuração do Banco de Dados

### SQLite (Padrão)
O sistema usa SQLite por padrão. O banco de dados será criado automaticamente na primeira execução.

### PostgreSQL (Produção)
Para usar PostgreSQL, configure as variáveis de ambiente no sistema:

```bash
DATABASE_TYPE=postgresql
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=prisma
POSTGRES_USER=seu_usuario
POSTGRES_PASSWORD=sua_senha
```

## 📚 Documentação

- [Documentação Técnica](docs/DOCUMENTACAO_TECNICA.md)
- [Guia de Contribuição](CONTRIBUTING.md)
- [Planejamento de Evolução](docs/PLANEJAMENTO_EVOLUCAO.md)

## 🔐 Credenciais Padrão

**Administrador:**
- Email: `admin@cge.mt.gov.br`
- Senha: `admin123`

> ⚠️ **Importante:** Altere as credenciais padrão antes de usar em produção!

## 🛠️ Tecnologias Utilizadas

### Backend
- **Python 3.8+** - Linguagem principal
- **Flask 3.0+** - Framework web
- **SQLite/PostgreSQL** - Banco de dados
- **ReportLab** - Geração de PDFs
- **Flask-CORS** - Controle de CORS

### Frontend
- **React 18.2+** - Biblioteca de interface
- **Bootstrap 5.2+** - Framework CSS
- **Chart.js** - Gráficos e visualizações
- **React Router** - Roteamento

## 🤝 Como Contribuir

1. Faça um fork do projeto
2. Crie uma branch para sua feature (`git checkout -b feature/AmazingFeature`)
3. Commit suas mudanças (`git commit -m 'Add some AmazingFeature'`)
4. Push para a branch (`git push origin feature/AmazingFeature`)
5. Abra um Pull Request

Leia nosso [Guia de Contribuição](CONTRIBUTING.md) para mais detalhes.

## 📄 Licença

Este projeto está licenciado sob a Licença MIT - veja o arquivo [LICENSE](LICENSE) para detalhes.

A Licença MIT permite:
- ✅ Uso comercial
- ✅ Modificação
- ✅ Distribuição
- ✅ Uso privado

Apenas exige:
- 📝 Incluir a licença e copyright nos arquivos
- 📝 Mencionar as mudanças feitas

## 👨‍💻 Autor

**Joelcio Caires da Silva Ormond**
- GitHub: [@joelcioormond](https://github.com/joelcioormond)

## 🙏 Agradecimentos

- Baseado na norma **ISO 31000** para gestão de riscos
- Desenvolvido para apoiar organizações na melhoria de seus processos de gestão de riscos
- Contribuições da comunidade são sempre bem-vindas!

## 📈 Status do Projeto

- ✅ **Versão 1.0** - Sistema completo funcional
- 🔄 **Em desenvolvimento** - Melhorias contínuas

---

⭐ **Se este projeto foi útil para você, considere dar uma estrela no repositório!**

📧 **Dúvidas ou sugestões?** Abra uma [issue](https://github.com/joelcioormond/prisma/issues) ou entre em contato!

