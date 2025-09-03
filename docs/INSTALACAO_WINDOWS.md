# Guia de Instalação - Windows

Este guia resolve problemas específicos de instalação no Windows.

## Problema com psycopg2-binary

O erro que você encontrou é comum no Windows. Aqui estão as soluções:

### Solução 1: Usar apenas SQLite (Recomendado para desenvolvimento)

1. **Use o arquivo requirements alternativo:**
   ```bash
   pip install -r requirements_windows.txt
   ```

2. **Configure o .env para usar SQLite:**
   ```env
   DATABASE_TYPE=sqlite
   SQLITE_DATABASE=sistema_cge.db
   ```

3. **O sistema funcionará perfeitamente com SQLite** para desenvolvimento e testes.

### Solução 2: Instalar PostgreSQL corretamente no Windows

Se você precisar usar PostgreSQL:

1. **Instale o PostgreSQL oficial:**
   - Baixe de: https://www.postgresql.org/download/windows/
   - Instale a versão completa (não apenas o cliente)

2. **Instale as ferramentas de desenvolvimento:**
   ```bash
   # No prompt de comando como administrador
   pip install --upgrade pip setuptools wheel
   ```

3. **Instale o psycopg2 específico:**
   ```bash
   pip install psycopg2-binary==2.9.5
   ```

### Solução 3: Usar conda (Alternativa)

Se ainda tiver problemas:

1. **Instale o Anaconda ou Miniconda**
2. **Crie um ambiente conda:**
   ```bash
   conda create -n cge-sistema python=3.9
   conda activate cge-sistema
   ```

3. **Instale o psycopg2 via conda:**
   ```bash
   conda install psycopg2
   pip install -r requirements.txt
   ```

## Executando o Sistema no Windows

### Backend

1. **Ative o ambiente virtual:**
   ```bash
   venv\Scripts\activate
   ```

2. **Execute o servidor:**
   ```bash
   python run.py
   ```

### Frontend

1. **Instale as dependências:**
   ```bash
   npm install
   ```

2. **Execute a aplicação:**
   ```bash
   npm start
   ```

## Problemas Comuns no Windows

### Erro de "Microsoft Visual C++ 14.0"

Se aparecer este erro:

1. **Instale o Visual Studio Build Tools:**
   - Baixe de: https://visualstudio.microsoft.com/visual-cpp-build-tools/
   - Instale apenas as "C++ build tools"

2. **Ou use a versão pré-compilada:**
   ```bash
   pip install --only-binary=all psycopg2-binary
   ```

### Erro de "pg_config"

Se aparecer erro sobre pg_config:

1. **Adicione o PostgreSQL ao PATH:**
   - Adicione `C:\Program Files\PostgreSQL\15\bin` ao PATH do sistema
   - Reinicie o prompt de comando

2. **Ou use apenas SQLite** (mais simples)

### Porta 5000 ocupada

No Windows, a porta 5000 pode estar ocupada:

1. **Use uma porta diferente:**
   ```bash
   # No .env
   PORT=5001
   ```

2. **Ou pare o processo que usa a porta 5000:**
   ```bash
   netstat -ano | findstr :5000
   taskkill /PID [PID_NUMBER] /F
   ```

## Script de Instalação Automática (Windows)

Crie um arquivo `instalar_windows.bat`:

```batch
@echo off
echo Instalando Sistema de Avaliacao CGE-MT...

echo 1. Criando ambiente virtual...
python -m venv venv
call venv\Scripts\activate

echo 2. Atualizando pip...
python -m pip install --upgrade pip

echo 3. Instalando dependencias (versao Windows)...
pip install -r requirements_windows.txt

echo 4. Copiando arquivo de configuracao...
copy .env.example .env

echo 5. Instalacao concluida!
echo.
echo Para executar o sistema:
echo 1. Backend: venv\Scripts\activate && python run.py
echo 2. Frontend: npm install && npm start
pause
```

Execute este arquivo como administrador para instalação automática.

