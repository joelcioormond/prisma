#!/usr/bin/env python3
# -*- coding: utf-8 -*-


from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import sqlite3
import logging
import os
import uuid
import json
import hashlib
from datetime import datetime
from werkzeug.utils import secure_filename
from pdf_generator import gerar_pdf_completo

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Criar aplicação Flask
app = Flask(__name__)
CORS(app, 
     origins=['http://localhost:3000', 'http://172.16.200.63:3000' ],
     methods=['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS'],
     allow_headers=['Content-Type', 'X-User-Email'] )

# Configuração de CORS
#CORS(app, origins=['http://localhost:3000', 'http://172.16.200.63:3000'] )

# Configuração de upload
UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif', 'doc', 'docx', 'xls', 'xlsx'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max

# Criar diretório de uploads se não existir
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

# Headers CORS
#@app.after_request
#def after_request(response):
#    response.headers['Access-Control-Allow-Origin'] = '*'
#    response.headers['Access-Control-Allow-Headers'] = 'Content-Type,X-User-Email'
#    response.headers['Access-Control-Allow-Methods'] = 'GET,POST,PUT,DELETE,OPTIONS'
#    return response

# Configuração do banco de dados
DATABASE = 'prisma.db'

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def init_db():
    """Inicializa o banco de dados"""
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    
    # ✅ TABELAS EXISTENTES (NÃO MEXER)
    # Tabela de órgãos
#    cursor.execute('''
#        CREATE TABLE IF NOT EXISTS orgaos (
#            id INTEGER PRIMARY KEY AUTOINCREMENT,
#            nome TEXT NOT NULL,
#            sigla TEXT,
#            data_criacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP
#        )
#    ''')
    
    # Migração: adicionar coluna orgao_superior_id se não existir
    try:
        cursor.execute('ALTER TABLE orgaos ADD COLUMN orgao_superior_id INTEGER')
        conn.commit()
        print("✅ Coluna orgao_superior_id adicionada")
    except sqlite3.OperationalError:
        print("ℹ️ Coluna orgao_superior_id já existe")
        
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS orgaos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL,
            sigla TEXT,
            orgao_superior_id INTEGER,
            data_criacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (orgao_superior_id) REFERENCES orgaos (id)
    )''')
    
    # Tabela de avaliações
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS avaliacoes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            titulo TEXT NOT NULL,
            orgao_id INTEGER,
            nivel_desejado INTEGER,
            status TEXT DEFAULT 'em_andamento',
            data_criacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            data_atualizacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            usuario_email TEXT,
            FOREIGN KEY (orgao_id) REFERENCES orgaos (id)
        )
    ''')
    
    # Tabela de respostas
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS respostas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            avaliacao_id INTEGER,
            atividade_id TEXT,
            instituido BOOLEAN DEFAULT 0,
            institucionalizado BOOLEAN DEFAULT 0,
            justificativa_instituido TEXT,
            justificativa_institucionalizado TEXT,
            evidencias_instituido TEXT,
            evidencias_institucionalizado TEXT,
            arquivos_instituido TEXT,
            arquivos_institucionalizado TEXT,
            data_criacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            data_atualizacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (avaliacao_id) REFERENCES avaliacoes (id)
        )
    ''')
    
    # 🆕 NOVAS TABELAS PARA GESTÃO DE USUÁRIOS
    
    # Tabela de perfis de usuário
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS perfis (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL UNIQUE,
            descricao TEXT,
            permissoes TEXT, -- JSON com permissões
            data_criacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Tabela de usuários
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS usuarios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT NOT NULL UNIQUE,
            nome TEXT NOT NULL,
            perfil_id INTEGER,
            orgao_id INTEGER,
            ativo BOOLEAN DEFAULT 1,
            senha_hash TEXT,
            ultimo_acesso TIMESTAMP,
            data_criacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            data_atualizacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (perfil_id) REFERENCES perfis (id),
            FOREIGN KEY (orgao_id) REFERENCES orgaos (id)
        )
    ''')
    
    # Tabela de sessões de usuário
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS sessoes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            usuario_id INTEGER,
            token TEXT NOT NULL UNIQUE,
            data_criacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            data_expiracao TIMESTAMP,
            ativo BOOLEAN DEFAULT 1,
            FOREIGN KEY (usuario_id) REFERENCES usuarios (id)
        )
    ''')
    
    # Inserir perfis padrão se não existirem
    cursor.execute('SELECT COUNT(*) FROM perfis')
    if cursor.fetchone()[0] == 0:
        perfis_padrao = [
            ('Administrador CGE', 'Acesso total ao sistema', json.dumps({
                'gerenciar_usuarios': True,
                'gerenciar_orgaos': True,
                'gerar_relatorios': True,
                'visualizar_relatorios_gerais': True,
                'visualizar_todas_avaliacoes': True,
                'criar_avaliacoes': True,
                'editar_avaliacoes': True,
                'finalizar_avaliacoes': True,                
                'exportar_dados': True
            })),
            ('Avaliador do Órgão', 'Pode criar e editar avaliações do seu órgão', json.dumps({
                'gerenciar_usuarios': False,
                'gerenciar_orgaos': False,
                'gerar_relatorios': True,
                'visualizar_relatorios_gerais': False,
                'visualizar_todas_avaliacoes': False,
                'criar_avaliacoes': True,
                'editar_avaliacoes': True,
                'finalizar_avaliacoes': True,                
                'exportar_dados': False
            })),
            ('Consultor Externo', 'Pode visualizar e comentar avaliações', json.dumps({
                'gerenciar_usuarios': False,
                'gerenciar_orgaos': False,
                'gerar_relatorios': True,
                'visualizar_relatorios_gerais': False,
                'visualizar_todas_avaliacoes': True,
                'criar_avaliacoes': False,
                'editar_avaliacoes': False,
                'finalizar_avaliacoes': False,               
                'exportar_dados': False
            })),
            ('Visualizador', 'Apenas consulta relatórios', json.dumps({
                'gerenciar_usuarios': False,
                'gerenciar_orgaos': False,
                'gerar_relatorios': True,
                'visualizar_relatorios_gerais': False,
                'visualizar_todas_avaliacoes': False,
                'criar_avaliacoes': False,
                'editar_avaliacoes': False,
                'finalizar_avaliacoes': False,                
                'exportar_dados': False
            }))
        ]
        cursor.executemany('INSERT INTO perfis (nome, descricao, permissoes) VALUES (?, ?, ?)', perfis_padrao)
    
    # Inserir órgãos básicos se não existirem
    cursor.execute('SELECT COUNT(*) FROM orgaos')
    if cursor.fetchone()[0] == 0:
        orgaos_basicos = [
            ('Casa Civil', 'CASA CIVIL'),
            ('Controladoria Geral do Estado', 'CGE'),
            ('Procuradoria Geral do Estado', 'PGE'),
            ('Secretaria de Estado de Fazenda', 'SEFAZ'),
            ('Secretaria de Estado de Saúde', 'SES'),
            ('Secretaria de Estado de Educação', 'SEDUC'),
            ('Secretaria de Estado de Segurança Pública', 'SESP')
        ]
        cursor.executemany('INSERT INTO orgaos (nome, sigla) VALUES (?, ?)', orgaos_basicos)
    
    # Criar usuário administrador padrão se não existir
    cursor.execute('SELECT COUNT(*) FROM usuarios WHERE email = ?', ('admin@cge.mt.gov.br',))
    if cursor.fetchone()[0] == 0:
        # Buscar ID do perfil administrador
        cursor.execute('SELECT id FROM perfis WHERE nome = ?', ('Administrador CGE',))
        perfil_admin_id = cursor.fetchone()[0]
        
        # Buscar ID do órgão CGE
        cursor.execute('SELECT id FROM orgaos WHERE sigla = ?', ('CGE',))
        orgao_cge_id = cursor.fetchone()[0]
        
        # Criar hash da senha padrão
        senha_padrao = 'admin123'
        senha_hash = hashlib.sha256(senha_padrao.encode()).hexdigest()
        
        cursor.execute('''
            INSERT INTO usuarios (email, nome, perfil_id, orgao_id, senha_hash)
            VALUES (?, ?, ?, ?, ?)
        ''', ('admin@cge.mt.gov.br', 'Administrador do Sistema', perfil_admin_id, orgao_cge_id, senha_hash))
    
    conn.commit()
    conn.close()

# 🆕 FUNÇÕES AUXILIARES PARA GESTÃO DE USUÁRIOS

def verificar_permissao(user_email, permissao):
    """Verifica se o usuário tem uma permissão específica"""
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT p.permissoes 
        FROM usuarios u 
        JOIN perfis p ON u.perfil_id = p.id 
        WHERE u.email = ? AND u.ativo = 1
    ''', (user_email,))
    
    result = cursor.fetchone()
    conn.close()
    
    if result:
        permissoes = json.loads(result[0])
        return permissoes.get(permissao, False)
    
    return False

def obter_dados_usuario(user_email):
    """Obtém dados completos do usuário"""
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT u.id, u.email, u.nome, u.ativo, u.ultimo_acesso,
               p.nome as perfil_nome, p.permissoes,
               o.id as orgao_id, o.nome as orgao_nome, o.sigla as orgao_sigla
        FROM usuarios u
        LEFT JOIN perfis p ON u.perfil_id = p.id
        LEFT JOIN orgaos o ON u.orgao_id = o.id
        WHERE u.email = ?
    ''', (user_email,))
    
    result = cursor.fetchone()
    conn.close()
    
    if result:
        return {
            'id': result[0],
            'email': result[1],
            'nome': result[2],
            'ativo': bool(result[3]),
            'ultimo_acesso': result[4],
            'perfil': result[5],
            'permissoes': json.loads(result[6]) if result[6] else {},
            'orgao_id': result[7],
            'orgao_nome': result[8],
            'orgao_sigla': result[9]
        }
    
    return None

# ✅ ROTAS EXISTENTES (NÃO MEXER)

@app.route('/')
def status():
    """Status do sistema"""
    return jsonify({
        'status': 'ok',
        'message': 'Sistema CGE-MT v4.3 funcionando',
        'version': '4.3',
        'cors': 'configurado',
        'gestao_usuarios': 'habilitada',
        'endpoints': [
            'GET  / (status)',
            'POST /api/auth/login (autenticação)',
            'GET  /api/orgaos (listar órgãos)',
            'POST /api/orgaos (criar órgão)',
            'GET  /api/avaliacoes (listar avaliações)',
            'POST /api/avaliacoes (criar avaliação)',
            'GET  /api/avaliacoes/<id> (obter avaliação)',
            'GET  /api/avaliacoes/<id>/respostas (obter respostas)',
            'POST /api/avaliacoes/<id>/respostas (salvar resposta)',
            'POST /api/avaliacoes/<id>/finalizar (finalizar avaliação)',
            'POST /api/upload (upload de arquivos)',
            'GET  /api/dashboard (dados dashboard)',
            '--- NOVOS ENDPOINTS ---',
            'GET  /api/usuarios (listar usuários)',
            'POST /api/usuarios (criar usuário)',
            'PUT  /api/usuarios/<id> (atualizar usuário)',
            'DELETE /api/usuarios/<id> (desativar usuário)',
            'GET  /api/perfis (listar perfis)',
            'GET  /api/admin/relatorios (relatórios administrativos)',
            'POST /api/admin/relatorios/exportar (exportar relatórios)',            
            'GET  /api/auth/me (dados do usuário logado)'
            'GET  /api/relatorio-individual (relatório do órgão)',
            'POST /api/relatorio-individual/exportar (exportar relatório individual)',
            'GET  /api/auth/verify (verificação de usuário)',
        ]
    })
    
    
    
@app.route("/api/relatorio-individual/exportar-completo", methods=["POST"])
def exportar_relatorio_individual_completo():
    user_email = request.headers.get("X-User-Email", "")
    dados_usuario = obter_dados_usuario(user_email)
    if not dados_usuario:
        return jsonify({"success": False, "message": "Usuário não encontrado"}), 404

    orgao_id = dados_usuario.get("orgao_id")
    if not orgao_id:
        return jsonify({"success": False, "message": "Usuário não vinculado a um órgão"}), 400

    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()

    try:
        # ===== DADOS DO ÓRGÃO =====
        cursor.execute("SELECT id, nome, sigla FROM orgaos WHERE id = ?", (orgao_id,))
        orgao_data = cursor.fetchone()
        
        if not orgao_data:
            return jsonify({"success": False, "message": "Órgão não encontrado"}), 404
        
        orgao = {
            "id": orgao_data[0],
            "nome": orgao_data[1],
            "sigla": orgao_data[2]
        }
        
        # ===== TODAS AS AVALIAÇÕES =====
        cursor.execute("""
            SELECT id, titulo, status, data_criacao, nivel_desejado
            FROM avaliacoes 
            WHERE orgao_id = ? 
            ORDER BY data_criacao DESC
        """, (orgao_id,))
        
        avaliacoes = []
        for row in cursor.fetchall():
            avaliacoes.append({
                "id": row[0],
                "titulo": row[1],
                "status": row[2],
                "data_criacao": row[3],
                "nivel_desejado": row[4]
            })
        
        # ===== RESPOSTAS DA AVALIAÇÃO MAIS RECENTE =====
        respostas = []
        if avaliacoes:
            avaliacao_mais_recente_id = avaliacoes[0]["id"]
            cursor.execute("SELECT * FROM respostas WHERE avaliacao_id = ?", (avaliacao_mais_recente_id,))
            for row in cursor.fetchall():
                respostas.append({
                    "id": row[0],
                    "avaliacao_id": row[1],
                    "atividade_id": row[2],
                    "instituido": row[3],
                    "institucionalizado": row[4],
                    "justificativa_instituido": row[5],
                    "justificativa_institucionalizado": row[6],
                    "evidencias_instituido": row[7],
                    "evidencias_institucionalizado": row[8],
                    "arquivos_instituido": row[9],
                    "arquivos_institucionalizado": row[10],
                })


        dados_relatorio = {
            "orgao": orgao,
            "avaliacoes": avaliacoes,
            "respostas": respostas
        }

        pdf_buffer = gerar_pdf_completo(dados_relatorio)

        from flask import Response
        from datetime import datetime

        orgao_sigla = dados_usuario.get("orgao_sigla", "orgao")
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"relatorio_completo_{orgao_sigla}_{timestamp}.pdf"
        
        return Response(
            pdf_buffer.getvalue(),
            mimetype="application/pdf",
            headers={
                "Content-Disposition": f"attachment; filename={filename}"
            }
        )

    except Exception as e:
        logger.error(f"Erro ao exportar relatório completo: {str(e)}")
        return jsonify({"success": False, "message": f"Erro: {str(e)}"}), 500
    finally:
        conn.close()


@app.route('/debug/routes')
def list_routes():
    routes = []
    for rule in app.url_map.iter_rules():
        routes.append({
            'endpoint': rule.endpoint,
            'methods': list(rule.methods),
            'rule': rule.rule
        })
    return jsonify(routes)

@app.route('/api/auth/alterar-senha', methods=['OPTIONS'])
def alterar_senha_preflight():
    return '', 200

@app.route('/api/auth/alterar-senha', methods=['POST'])
def alterar_senha():
    """Permite ao usuário alterar sua própria senha"""

    user_email = request.headers.get('X-User-Email', '')
    
    if not user_email:
        return jsonify({
            'success': False,
            'message': 'Usuário não autenticado'
        }), 401
    
    data = request.get_json()
    senha_atual = data.get('senha_atual', '')
    senha_nova = data.get('senha_nova', '')
    confirmar_senha = data.get('confirmar_senha', '')
    
    # Validações
    if not senha_atual:
        return jsonify({
            'success': False,
            'message': 'Senha atual é obrigatória'
        }), 400
    
    if not senha_nova:
        return jsonify({
            'success': False,
            'message': 'Nova senha é obrigatória'
        }), 400
    
    if senha_nova != confirmar_senha:
        return jsonify({
            'success': False,
            'message': 'Confirmação de senha não confere'
        }), 400
    
    if len(senha_nova) < 6:
        return jsonify({
            'success': False,
            'message': 'Nova senha deve ter pelo menos 6 caracteres'
        }), 400
    
    try:
        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()
        
        # Verificar senha atual
        senha_atual_hash = hashlib.sha256(senha_atual.encode()).hexdigest()
        cursor.execute('SELECT id FROM usuarios WHERE email = ? AND senha_hash = ? AND ativo = 1', 
                      (user_email, senha_atual_hash))
        
        usuario = cursor.fetchone()
        
        if not usuario:
            conn.close()
            return jsonify({
                'success': False,
                'message': 'Senha atual incorreta'
            }), 401
        
        # Atualizar com nova senha
        senha_nova_hash = hashlib.sha256(senha_nova.encode()).hexdigest()
        cursor.execute('UPDATE usuarios SET senha_hash = ?, data_atualizacao = CURRENT_TIMESTAMP WHERE id = ?', 
                      (senha_nova_hash, usuario[0]))
        
        conn.commit()
        conn.close()
        
        return jsonify({
            'success': True,
            'message': 'Senha alterada com sucesso'
        })
        
    except Exception as e:
        logger.error(f"Erro ao alterar senha: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'Erro interno do servidor'
        }), 500








@app.route('/api/auth/login', methods=['POST'])
def login():
    """Autenticação de usuário - VERSÃO CORRIGIDA"""
    data = request.get_json()
    email = data.get('email', '')
    senha = data.get('senha', '')
    
    # Validações básicas
    if not email:
        return jsonify({
            'success': False,
            'message': 'Email é obrigatório'
        }), 400
    
    if not senha:
        return jsonify({
            'success': False,
            'message': 'Senha é obrigatória'
        }), 400
    
    # Verificar se email termina com mt.gov.br
    if not email.endswith('mt.gov.br'):
        return jsonify({
            'success': False,
            'message': 'Apenas emails mt.gov.br são permitidos'
        }), 400
    
    try:
        # Hash da senha fornecida
        senha_hash = hashlib.sha256(senha.encode()).hexdigest()
        
        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()
        
        # Buscar usuário com email e senha
        cursor.execute('''
            SELECT u.id, u.email, u.nome, u.ativo,
                   p.nome as perfil_nome, p.permissoes,
                   o.id as orgao_id, o.nome as orgao_nome, o.sigla as orgao_sigla
            FROM usuarios u
            LEFT JOIN perfis p ON u.perfil_id = p.id
            LEFT JOIN orgaos o ON u.orgao_id = o.id
            WHERE u.email = ? AND u.senha_hash = ? AND u.ativo = 1
        ''', (email, senha_hash))
        
        result = cursor.fetchone()
        
        if result:
            # Atualizar último acesso
            cursor.execute('UPDATE usuarios SET ultimo_acesso = CURRENT_TIMESTAMP WHERE id = ?', (result[0],))
            conn.commit()
            
            user_data = {
                'id': result[0],
                'email': result[1],
                'nome': result[2],
                'perfil': result[4],
                'permissoes': json.loads(result[5]) if result[5] else {},
                'orgao_id': result[6],
                'orgao_nome': result[7],
                'orgao_sigla': result[8]
            }
            
            conn.close()
            
            return jsonify({
                'success': True,
                'message': 'Login realizado com sucesso',
                'user': user_data
            })
        else:
            conn.close()
            return jsonify({
                'success': False,
                'message': 'Email ou senha incorretos'
            }), 401
            
    except Exception as e:
        logger.error(f"Erro no login: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'Erro interno do servidor'
        }), 500
            
@app.route('/api/auth/verify', methods=['GET'])
def verificar_usuario():
    """Verifica dados do usuário logado"""
    user_email = request.headers.get('X-User-Email', '')
    
    # DEBUG: Se não tem email no header, usar admin para teste
    if not user_email:
        user_email = 'admin@cge.mt.gov.br'
    
    dados_usuario = obter_dados_usuario(user_email)
    
    if dados_usuario:
        return jsonify({
            'success': True,
            'user': dados_usuario,
            'debug_email': user_email
        })
    else:
        return jsonify({'success': False, 'message': 'Usuário não encontrado', 'debug_email': user_email}), 404


# 🆕 NOVOS ENDPOINTS PARA GESTÃO DE USUÁRIOS

@app.route('/api/auth/me')
def obter_usuario_logado():
    """Obtém dados do usuário logado"""
    user_email = request.headers.get('X-User-Email', '')
    
    if not user_email:
        return jsonify({'success': False, 'message': 'Usuário não autenticado'}), 401
    
    dados_usuario = obter_dados_usuario(user_email)
    
    if dados_usuario:
        return jsonify({'success': True, 'user': dados_usuario})
    else:
        return jsonify({'success': False, 'message': 'Usuário não encontrado'}), 404

@app.route('/api/usuarios')
def listar_usuarios():
    """Lista todos os usuários (apenas para administradores)"""
    user_email = request.headers.get('X-User-Email', '')
    
    if not verificar_permissao(user_email, 'gerenciar_usuarios'):
        return jsonify({'success': False, 'message': 'Sem permissão para gerenciar usuários'}), 403
    
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT u.id, u.email, u.nome, u.ativo, u.ultimo_acesso, u.data_criacao,
               p.nome as perfil_nome,
               o.nome as orgao_nome, o.sigla as orgao_sigla
        FROM usuarios u
        LEFT JOIN perfis p ON u.perfil_id = p.id
        LEFT JOIN orgaos o ON u.orgao_id = o.id
        ORDER BY u.nome
    ''')
    
    usuarios = []
    for row in cursor.fetchall():
        usuarios.append({
            'id': row[0],
            'email': row[1],
            'nome': row[2],
            'ativo': bool(row[3]),
            'ultimo_acesso': row[4],
            'data_criacao': row[5],
            'perfil': row[6],
            'orgao_nome': row[7],
            'orgao_sigla': row[8]
        })
    
    conn.close()
    return jsonify(usuarios)

@app.route('/api/usuarios', methods=['POST'])
def criar_usuario():
    """Cria um novo usuário"""
    user_email = request.headers.get('X-User-Email', '')
    
    if not verificar_permissao(user_email, 'gerenciar_usuarios'):
        return jsonify({'success': False, 'message': 'Sem permissão para gerenciar usuários'}), 403
    
    data = request.get_json()
    email = data.get('email')
    nome = data.get('nome')
    perfil_id = data.get('perfil_id')
    orgao_id = data.get('orgao_id')
    senha = data.get('senha')
    
    # Validações
    if not all([email, nome, perfil_id, senha]):
        return jsonify({'success': False, 'message': 'Todos os campos são obrigatórios (email, nome, perfil, senha)'}), 400
    
    if not email.endswith('mt.gov.br'):
        return jsonify({'success': False, 'message': 'Apenas emails mt.gov.br são permitidos'}), 400
    
    if len(senha) < 6:
        return jsonify({'success': False, 'message': 'Senha deve ter pelo menos 6 caracteres'}), 400
    
    try:
        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()
        
        # Verificar se email já existe
        cursor.execute('SELECT id FROM usuarios WHERE email = ?', (email,))
        if cursor.fetchone():
            conn.close()
            return jsonify({'success': False, 'message': 'Email já cadastrado'}), 400
        
        # Criar hash da senha
        senha_hash = hashlib.sha256(senha.encode()).hexdigest()
        
        # Inserir usuário
        cursor.execute('''
            INSERT INTO usuarios (email, nome, perfil_id, orgao_id, senha_hash)
            VALUES (?, ?, ?, ?, ?)
        ''', (email, nome, perfil_id, orgao_id, senha_hash))
        
        usuario_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        return jsonify({
            'success': True,
            'message': 'Usuário criado com sucesso',
            'usuario_id': usuario_id
        })
        
    except Exception as e:
        logger.error(f"Erro ao criar usuário: {str(e)}")
        return jsonify({'success': False, 'message': 'Erro interno do servidor'}), 500

@app.route('/api/usuarios/<int:usuario_id>', methods=['PUT'])
def atualizar_usuario(usuario_id):
    """Atualiza um usuário"""
    user_email = request.headers.get('X-User-Email', '')
    
    if not verificar_permissao(user_email, 'gerenciar_usuarios'):
        return jsonify({'success': False, 'message': 'Sem permissão para gerenciar usuários'}), 403
    
    data = request.get_json()
    
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    
    # Construir query de atualização dinamicamente
    campos = []
    valores = []
    
    if 'nome' in data:
        campos.append('nome = ?')
        valores.append(data['nome'])
    
    if 'perfil_id' in data:
        campos.append('perfil_id = ?')
        valores.append(data['perfil_id'])
    
    if 'orgao_id' in data:
        campos.append('orgao_id = ?')
        valores.append(data['orgao_id'])
    
    if 'ativo' in data:
        campos.append('ativo = ?')
        valores.append(data['ativo'])
    
    if 'senha' in data and data['senha']:
        campos.append('senha_hash = ?')
        valores.append(hashlib.sha256(data['senha'].encode()).hexdigest())
    
    if campos:
        campos.append('data_atualizacao = CURRENT_TIMESTAMP')
        valores.append(usuario_id)
        
        query = f"UPDATE usuarios SET {', '.join(campos)} WHERE id = ?"
        cursor.execute(query, valores)
        
        conn.commit()
    
    conn.close()
    
    return jsonify({'success': True, 'message': 'Usuário atualizado com sucesso'})

@app.route('/api/usuarios/<int:usuario_id>', methods=['DELETE'])
def desativar_usuario(usuario_id):
    """Desativa um usuário"""
    user_email = request.headers.get('X-User-Email', '')
    
    if not verificar_permissao(user_email, 'gerenciar_usuarios'):
        return jsonify({'success': False, 'message': 'Sem permissão para gerenciar usuários'}), 403
    
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    
    cursor.execute('''
        UPDATE usuarios 
        SET ativo = 0, data_atualizacao = CURRENT_TIMESTAMP 
        WHERE id = ?
    ''', (usuario_id,))
    
    conn.commit()
    conn.close()
    
    return jsonify({'success': True, 'message': 'Usuário desativado com sucesso'})

@app.route('/api/perfis')
def listar_perfis():
    """Lista todos os perfis disponíveis"""
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    
    cursor.execute('SELECT id, nome, descricao FROM perfis ORDER BY nome')
    
    perfis = []
    for row in cursor.fetchall():
        perfis.append({
            'id': row[0],
            'nome': row[1],
            'descricao': row[2]
        })
    
    conn.close()
    return jsonify(perfis)

# ✅ ROTAS EXISTENTES MANTIDAS (todas as outras rotas permanecem iguais)

@app.route('/api/orgaos')
def listar_orgaos():
    """Lista todos os órgãos"""
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute('''
        SELECT o.id, o.nome, o.sigla, o.data_criacao, o.orgao_superior_id,
               os.nome as orgao_superior_nome, os.sigla as orgao_superior_sigla
        FROM orgaos o
        LEFT JOIN orgaos os ON o.orgao_superior_id = os.id
        ORDER BY o.nome
    ''')
    orgaos = [{
        'id': row[0], 
        'nome': row[1], 
        'sigla': row[2], 
        'data_criacao': row[3],
        'orgao_superior_id': row[4],
        'orgao_superior_nome': row[5],
        'orgao_superior_sigla': row[6]
    } for row in cursor.fetchall()]
    conn.close()
    return jsonify(orgaos)

@app.route('/api/orgaos', methods=['POST'])
def criar_orgao():
    """Cria um novo órgão"""
    data = request.get_json()
    nome = data.get('nome')
    sigla = data.get('sigla', '')
    orgao_superior_id = data.get('orgao_superior_id')
    
    if not nome:
        return jsonify({'success': False, 'message': 'Nome é obrigatório'}), 400
    
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute('INSERT INTO orgaos (nome, sigla, orgao_superior_id) VALUES (?, ?, ?)', 
               (nome, sigla, orgao_superior_id if orgao_superior_id else None))
    orgao_id = cursor.lastrowid
    conn.commit()
    conn.close()
    
    return jsonify({
        'success': True,
        'message': 'Órgão criado com sucesso',
        'orgao': {'id': orgao_id, 'nome': nome, 'sigla': sigla}
    })

@app.route('/api/orgaos/<int:orgao_id>', methods=['PUT'])
def atualizar_orgao(orgao_id):
    """Atualiza um órgão"""
    user_email = request.headers.get('X-User-Email', '')
    
    if not verificar_permissao(user_email, 'gerenciar_orgaos'):
        return jsonify({'success': False, 'message': 'Sem permissão para gerenciar órgãos'}), 403
    
    data = request.get_json()
    nome = data.get('nome')
    sigla = data.get('sigla', '')
    orgao_superior_id = data.get('orgao_superior_id')
    
    if not nome:
        return jsonify({'success': False, 'message': 'Nome é obrigatório'}), 400
    
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    
    # Verificar se órgão existe
    cursor.execute('SELECT id FROM orgaos WHERE id = ?', (orgao_id,))
    if not cursor.fetchone():
        conn.close()
        return jsonify({'success': False, 'message': 'Órgão não encontrado'}), 404
    
    # Atualizar órgão
    cursor.execute('UPDATE orgaos SET nome = ?, sigla = ?, orgao_superior_id = ? WHERE id = ?', 
               (nome, sigla, orgao_superior_id if orgao_superior_id else None, orgao_id))
    conn.commit()
    conn.close()
    
    return jsonify({
        'success': True,
        'message': 'Órgão atualizado com sucesso'
    })

#@app.route('/api/orgaos/<int:orgao_id>', methods=['PUT'])
#def atualizar_orgao(orgao_id):
#    """Atualiza um órgão"""
#    user_email = request.headers.get('X-User-Email', '')
#    
#    if not verificar_permissao(user_email, 'gerenciar_orgaos'):
#        return jsonify({'success': False, 'message': 'Sem permissão para gerenciar órgãos'}), 403
#    
#    data = request.get_json()
#    nome = data.get('nome')
#    sigla = data.get('sigla', '')
#    
#    if not nome:
#        return jsonify({'success': False, 'message': 'Nome é obrigatório'}), 400
#    
#    conn = sqlite3.connect(DATABASE)
#    cursor = conn.cursor()
#    
#    # Verificar se órgão existe
#    cursor.execute('SELECT id FROM orgaos WHERE id = ?', (orgao_id,))
#    if not cursor.fetchone():
#        conn.close()
#        return jsonify({'success': False, 'message': 'Órgão não encontrado'}), 404
#    
#    # Atualizar órgão
#    cursor.execute('UPDATE orgaos SET nome = ?, sigla = ? WHERE id = ?', (nome, sigla, orgao_id))
#    conn.commit()
#    conn.close()
#    
#    return jsonify({
#        'success': True,
#        'message': 'Órgão atualizado com sucesso'
#    })

@app.route('/api/avaliacoes')
def listar_avaliacoes():
    """Lista avaliações do usuário"""
    user_email = request.headers.get('X-User-Email', '')
    
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute('''
        SELECT a.id, a.titulo, a.nivel_desejado, a.status, a.data_criacao,
               o.nome as orgao_nome
        FROM avaliacoes a
        LEFT JOIN orgaos o ON a.orgao_id = o.id
        WHERE a.usuario_email = ?
        ORDER BY a.data_criacao DESC
    ''', (user_email,))
    
    avaliacoes = []
    for row in cursor.fetchall():
        avaliacoes.append({
            'id': row[0],
            'titulo': row[1],
            'nivel_desejado': row[2],
            'status': row[3],
            'data_criacao': row[4],
            'orgao_nome': row[5]
        })
    
    conn.close()
    return jsonify(avaliacoes)

@app.route('/api/avaliacoes', methods=['POST'])
def criar_avaliacao():
    """Cria uma nova avaliação"""
    data = request.get_json()
    user_email = request.headers.get('X-User-Email', '')
    
    titulo = data.get('titulo')
    orgao_id = data.get('orgao_id')
    nivel_desejado = data.get('nivel_desejado')
    
    if not all([titulo, orgao_id, nivel_desejado]):
        return jsonify({'success': False, 'message': 'Dados incompletos'}), 400
    
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO avaliacoes (titulo, orgao_id, nivel_desejado, usuario_email)
        VALUES (?, ?, ?, ?)
    ''', (titulo, orgao_id, nivel_desejado, user_email))
    
    avaliacao_id = cursor.lastrowid
    conn.commit()
    conn.close()
    
    return jsonify({
        'success': True,
        'message': 'Avaliação criada com sucesso',
        'avaliacao_id': avaliacao_id
    })

@app.route('/api/avaliacoes/<int:avaliacao_id>')
def obter_avaliacao(avaliacao_id):
    """Obtém uma avaliação específica"""
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute('''
        SELECT a.id, a.titulo, a.nivel_desejado, a.status, a.data_criacao,
               o.nome as orgao_nome
        FROM avaliacoes a
        LEFT JOIN orgaos o ON a.orgao_id = o.id
        WHERE a.id = ?
    ''', (avaliacao_id,))
    
    row = cursor.fetchone()
    if not row:
        conn.close()
        return jsonify({'success': False, 'message': 'Avaliação não encontrada'}), 404
    
    avaliacao = {
        'id': row[0],
        'titulo': row[1],
        'nivel_desejado': row[2],
        'status': row[3],
        'data_criacao': row[4],
        'orgao_nome': row[5]
    }
    
    conn.close()
    return jsonify({'success': True, 'avaliacao': avaliacao})

@app.route('/api/avaliacoes/<int:avaliacao_id>/respostas', methods=['GET'])
def obter_respostas(avaliacao_id):
    """Obtém respostas de uma avaliação"""
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute('''
        SELECT atividade_id, instituido, institucionalizado,
               justificativa_instituido, justificativa_institucionalizado,
               evidencias_instituido, evidencias_institucionalizado,
               arquivos_instituido, arquivos_institucionalizado
        FROM respostas
        WHERE avaliacao_id = ?
    ''', (avaliacao_id,))
    
    respostas = []
    for row in cursor.fetchall():
        respostas.append({
            'atividade_id': row[0],
            'instituido': bool(row[1]),
            'institucionalizado': bool(row[2]),
            'justificativa_instituido': row[3] or '',
            'justificativa_institucionalizado': row[4] or '',
            'evidencias_instituido': row[5] or '',
            'evidencias_institucionalizado': row[6] or '',
            'arquivos_instituido': json.loads(row[7]) if row[7] else [],
            'arquivos_institucionalizado': json.loads(row[8]) if row[8] else []
        })
    
    conn.close()
    return jsonify(respostas)

@app.route('/api/avaliacoes/<int:avaliacao_id>/respostas', methods=['POST'])
def salvar_resposta(avaliacao_id):
    """Salva uma resposta"""
    data = request.get_json()
    
    atividade_id = data.get('atividade_id')
    instituido = data.get('instituido', False)
    institucionalizado = data.get('institucionalizado', False)
    justificativa_instituido = data.get('justificativa_instituido', '')
    justificativa_institucionalizado = data.get('justificativa_institucionalizado', '')
    evidencias_instituido = data.get('evidencias_instituido', '')
    evidencias_institucionalizado = data.get('evidencias_institucionalizado', '')
    arquivos_instituido = json.dumps(data.get('arquivos_instituido', []))
    arquivos_institucionalizado = json.dumps(data.get('arquivos_institucionalizado', []))
    
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    
    # Verificar se já existe resposta para esta atividade
    cursor.execute('''
        SELECT id FROM respostas 
        WHERE avaliacao_id = ? AND atividade_id = ?
    ''', (avaliacao_id, atividade_id))
    
    if cursor.fetchone():
        # Atualizar resposta existente
        cursor.execute('''
            UPDATE respostas 
            SET instituido = ?, institucionalizado = ?,
                justificativa_instituido = ?, justificativa_institucionalizado = ?,
                evidencias_instituido = ?, evidencias_institucionalizado = ?,
                arquivos_instituido = ?, arquivos_institucionalizado = ?,
                data_atualizacao = CURRENT_TIMESTAMP
            WHERE avaliacao_id = ? AND atividade_id = ?
        ''', (instituido, institucionalizado, 
              justificativa_instituido, justificativa_institucionalizado,
              evidencias_instituido, evidencias_institucionalizado,
              arquivos_instituido, arquivos_institucionalizado,
              avaliacao_id, atividade_id))
    else:
        # Criar nova resposta
        cursor.execute('''
            INSERT INTO respostas (
                avaliacao_id, atividade_id, instituido, institucionalizado,
                justificativa_instituido, justificativa_institucionalizado,
                evidencias_instituido, evidencias_institucionalizado,
                arquivos_instituido, arquivos_institucionalizado
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (avaliacao_id, atividade_id, instituido, institucionalizado,
              justificativa_instituido, justificativa_institucionalizado,
              evidencias_instituido, evidencias_institucionalizado,
              arquivos_instituido, arquivos_institucionalizado))
    
    conn.commit()
    conn.close()
    
    return jsonify({'success': True, 'message': 'Resposta salva com sucesso'})

@app.route('/api/avaliacoes/<int:avaliacao_id>/finalizar', methods=['POST'])
def finalizar_avaliacao(avaliacao_id):
    """Finaliza uma avaliação"""
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    
    # Atualizar status da avaliação
    cursor.execute('''
        UPDATE avaliacoes 
        SET status = 'finalizada', data_atualizacao = CURRENT_TIMESTAMP
        WHERE id = ?
    ''', (avaliacao_id,))
    
    conn.commit()
    conn.close()
    
    return jsonify({'success': True, 'message': 'Avaliação finalizada com sucesso'})

@app.route('/api/upload', methods=['POST'])
def upload_arquivo():
    """Upload de arquivo"""
    try:
        if 'arquivo' not in request.files:
            return jsonify({'success': False, 'message': 'Nenhum arquivo enviado'}), 400
        
        arquivo = request.files['arquivo']
        
        if arquivo.filename == '':
            return jsonify({'success': False, 'message': 'Nenhum arquivo selecionado'}), 400
        
        # Criar diretório de uploads se não existir
        import os
        upload_dir = 'uploads'
        if not os.path.exists(upload_dir):
            os.makedirs(upload_dir)
        
        # Salvar arquivo com nome único
        import uuid
        filename = f"{uuid.uuid4()}_{arquivo.filename}"
        filepath = os.path.join(upload_dir, filename)
        arquivo.save(filepath)
        
        return jsonify({
            'success': True,
            'message': 'Arquivo enviado com sucesso',
            'filename': filename,
            'url': f'/uploads/{filename}',
            'filepath': filepath
        })
        
    except Exception as e:
        return jsonify({'success': False, 'message': f'Erro no upload: {str(e)}'}), 500

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    """Serve arquivos enviados"""
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)
    

    
@app.route('/api/admin/relatorios', methods=['GET'])
def obter_relatorios_admin():
    """Obtém relatórios administrativos com debug detalhado"""
    print("🔍 DEBUG: Iniciando obter_relatorios_admin()")
    
    user_email = request.headers.get('X-User-Email', '')
    print(f"   User email: {user_email}")
    
    # Verificar permissões de administrador
    try:
        print("   🔍 Verificando dados do usuário...")
        dados_usuario = obter_dados_usuario(user_email)
        print(f"   Dados usuário obtidos: {dados_usuario is not None}")
        
        if not dados_usuario:
            print("   ❌ Usuário não encontrado")
            return jsonify({'success': False, 'message': 'Usuário não encontrado'}), 404
            
        permissoes = dados_usuario.get('permissoes', {})
        print(f"   Permissões: {list(permissoes.keys())}")
        
        if not permissoes.get('gerar_relatorios'):
            print("   ❌ Acesso negado - sem permissão gerar_relatorios")
            return jsonify({'success': False, 'message': 'Acesso negado'}), 403
        
        print("   ✅ Permissões OK")
        
    except Exception as e:
        print(f"   ❌ Erro ao verificar usuário: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'message': 'Erro ao verificar usuário'}), 500
    
    try:
        print("   🔍 Conectando ao banco...")
        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()
        print("   ✅ Conexão estabelecida")
        
        print("   🔍 Buscando órgãos...")
        # Buscar todos os órgãos
        cursor.execute('SELECT id, nome, sigla FROM orgaos ORDER BY nome')
        orgaos = cursor.fetchall()
        print(f"   ✅ {len(orgaos)} órgãos encontrados")
        
        # ===== RANKING DE MATURIDADE POR ÓRGÃO (CORRIGIDO) =====
        ranking_maturidade = []
        
        for i, orgao in enumerate(orgaos):
            print(f"   🔍 Processando órgão {i+1}/{len(orgaos)}: {orgao[1]}")
            
            try:
                orgao_id = orgao[0]
                orgao_nome = orgao[1]
                orgao_sigla = orgao[2]
                
                print(f"      Calculando maturidade para órgão {orgao_id}...")
                
                # ✅ USAR A MESMA LÓGICA DO RELATÓRIO INDIVIDUAL
                classificacao_maturidade = calcular_nivel_maturidade_orgao(orgao_id)
                print(f"      ✅ Maturidade calculada: Nível {classificacao_maturidade.get('nivel_maturidade', 1)}")
                
                # Contar avaliações por status (para estatísticas)
                print(f"      Contando avaliações...")
                cursor.execute('''
                    SELECT status, COUNT(*) 
                    FROM avaliacoes 
                    WHERE orgao_id = ? 
                    GROUP BY status
                ''', (orgao_id,))
                
                avaliacoes_stats = dict(cursor.fetchall())
                total_avaliacoes = sum(avaliacoes_stats.values())
                avaliacoes_finalizadas = avaliacoes_stats.get('finalizada', 0)
                avaliacoes_andamento = avaliacoes_stats.get('em_andamento', 0)
                
                print(f"      Avaliações: {total_avaliacoes} total, {avaliacoes_finalizadas} finalizadas, {avaliacoes_andamento} em andamento")
                
                # Buscar última avaliação do órgão
                print(f"      Buscando última avaliação...")
                cursor.execute('''
                    SELECT data_criacao, data_atualizacao
                    FROM avaliacoes 
                    WHERE orgao_id = ? 
                    ORDER BY COALESCE(data_atualizacao, data_criacao) DESC 
                    LIMIT 1
                ''', (orgao_id,))

                ultima_avaliacao_data = cursor.fetchone()
                ultima_avaliacao = None
                if ultima_avaliacao_data:
                    # Usar data de atualização se existir, senão data de criação
                    data_ref = ultima_avaliacao_data[1] or ultima_avaliacao_data[0]
                    if data_ref:
                        ultima_avaliacao = data_ref[:10]  # Apenas a data (YYYY-MM-DD)
                
                print(f"      Última avaliação: {ultima_avaliacao}")

                # Calcular maturidade média baseada no nível certificado
                nivel = classificacao_maturidade.get('nivel_maturidade', 1)
                maturidade_media = nivel * 20  # Nível 1=20%, 2=40%, 3=60%, 4=80%, 5=100%

                # Status baseado em atividade recente
                status = 'ativo' if total_avaliacoes > 0 else 'inativo'
                
                print(f"      Nível: {nivel}, Maturidade: {maturidade_media}%, Status: {status}")

                # Dados para o ranking
                ranking_item = {
                    'orgao_id': orgao_id,
                    'orgao_nome': orgao_nome,
                    'orgao_sigla': orgao_sigla,
                    'nivel_maturidade': nivel,
                    'maturidade_media': maturidade_media,
                    'ultima_avaliacao': ultima_avaliacao,
                    'status': status,
                    'status_certificacao': classificacao_maturidade.get('status', 'inicial'),
                    'descricao_maturidade': classificacao_maturidade.get('descricao', 'Nível Inicial'),
                    'data_certificacao': classificacao_maturidade.get('data_certificacao'),
                    'total_avaliacoes': total_avaliacoes,
                    'avaliacoes_finalizadas': avaliacoes_finalizadas,
                    'avaliacoes_andamento': avaliacoes_andamento,
                    'criterios_atendidos': classificacao_maturidade.get('criterios_atendidos', False),
                    'finalizadas': avaliacoes_finalizadas,
                    'em_andamento': avaliacoes_andamento
                }
                
                ranking_maturidade.append(ranking_item)
                print(f"      ✅ Órgão {orgao_nome} processado com sucesso")
                
            except Exception as e:
                print(f"      ❌ Erro ao processar órgão {orgao[1]}: {e}")
                import traceback
                traceback.print_exc()
                continue
        
        print(f"   ✅ Ranking processado: {len(ranking_maturidade)} órgãos")
        
        
        # ✅ PREPARAR DADOS PARA 'avaliacoes_por_orgao'
        avaliacoes_por_orgao_data = []
        for item in ranking_maturidade:
            avaliacoes_por_orgao_data.append({
                'orgao_id': item['orgao_id'],
                'orgao_nome': item['orgao_nome'],
                'orgao_sigla': item['orgao_sigla'],
                'total_avaliacoes': item['total_avaliacoes'],
                'finalizadas': item['avaliacoes_finalizadas'],
                'em_andamento': item['avaliacoes_andamento'],
                'maturidade_media': item['maturidade_media'] # Reutiliza a maturidade calculada
            })

        
        # Ordenar por nível de maturidade (decrescente) e depois por nome
        ranking_maturidade.sort(key=lambda x: (-x['nivel_maturidade'], x['orgao_nome']))
        
        print("   🔍 Processando avaliações em andamento...")
        
        # ===== AVALIAÇÕES EM ANDAMENTO (SIMPLIFICADO PARA DEBUG) =====
        avaliacoes_andamento = []
        
        print("   🔍 Calculando estatísticas gerais...")
        
        # ===== ESTATÍSTICAS GERAIS =====
        total_orgaos = len(orgaos)
        orgaos_certificados = len([r for r in ranking_maturidade if r['criterios_atendidos']])
        
        # Total de avaliações no sistema
        cursor.execute('SELECT COUNT(*) FROM avaliacoes')
        total_avaliacoes_sistema = cursor.fetchone()[0]
        
        # Avaliações por status
        cursor.execute('''
            SELECT status, COUNT(*) 
            FROM avaliacoes 
            GROUP BY status
        ''')
        avaliacoes_por_status = dict(cursor.fetchall())
        
        print(f"   Estatísticas: {total_orgaos} órgãos, {orgaos_certificados} certificados, {total_avaliacoes_sistema} avaliações")
        
        orgaos_por_nivel = {}
        for item in ranking_maturidade:
            nivel = item['nivel_maturidade']
            if nivel not in orgaos_por_nivel:
                orgaos_por_nivel[nivel] = 0
            orgaos_por_nivel[nivel] += 1

        print(f"   Estatísticas: {total_orgaos} órgãos, {orgaos_certificados} certificados, {total_avaliacoes_sistema} avaliações")
        print(f"   Órgãos por nível: {orgaos_por_nivel}")
        
        conn.close()
        print("   ✅ Conexão fechada")
        
        # Calcular média de maturidade
        if ranking_maturidade:
            media_maturidade = int(sum([r['maturidade_media'] for r in ranking_maturidade]) / len(ranking_maturidade))
        else:
            media_maturidade = 0
        
        print(f"   Média de maturidade calculada: {media_maturidade}%")
        
        resultado = {
            'success': True,
            'ranking_maturidade': ranking_maturidade,
            'avaliacoes_andamento': avaliacoes_andamento,
            'avaliacoes_recentes': [],
            
            # ✅ COMPATIBILIDADE COM FRONTEND EXISTENTE
            'avaliacoes_por_orgao': ranking_maturidade,
            'evolucao_temporal': [],
            
            # ✅ ESTATÍSTICAS NO FORMATO ESPERADO PELO FRONTEND
            'estatisticas_gerais': {
                'total_avaliacoes': total_avaliacoes_sistema,
                'avaliacoes_finalizadas': avaliacoes_por_status.get('finalizada', 0),
                'orgaos_participantes': total_orgaos,
                'media_maturidade': media_maturidade
            }
        }
        
        print("   ✅ Resultado preparado, retornando...")
        return jsonify({
            'success': True,
            'ranking_maturidade': ranking_maturidade,
            'avaliacoes_andamento': avaliacoes_andamento,
            'avaliacoes_recentes': [], # Manter vazio por enquanto ou preencher se tiver dados
    
            # ✅ CORRIGIDO: Enviar dados específicos para 'avaliacoes_por_orgao'
            'avaliacoes_por_orgao': avaliacoes_por_orgao_data,
            'evolucao_temporal': [],  # Manter vazio por enquanto
    
            'estatisticas_gerais': {  
                'total_avaliacoes': total_avaliacoes_sistema,
                'avaliacoes_finalizadas': avaliacoes_por_status.get('finalizada', 0),
                'orgaos_participantes': total_orgaos,
                'media_maturidade': media_maturidade
            },
    
            'estatisticas_detalhadas': { # Manter para futuras expansões
                'total_orgaos': total_orgaos,
                'orgaos_certificados': orgaos_certificados,
                'orgaos_por_nivel': orgaos_por_nivel,
                'avaliacoes_por_status': avaliacoes_por_status
            }
        })
        
    except Exception as e:
        print(f"❌ ERRO GERAL na função: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'message': f'Erro interno: {str(e)}'}), 500
        
def calcular_media_maturidade_sistema(ranking_maturidade):
    """Calcula a média de maturidade do sistema baseada nos níveis certificados"""
    if not ranking_maturidade:
        return 0
    
    # Calcular média baseada nos níveis de maturidade certificados
    # Nível 1 = 20%, Nível 2 = 40%, Nível 3 = 60%, Nível 4 = 80%, Nível 5 = 100%
    total_pontos = 0
    total_orgaos = len(ranking_maturidade)
    
    for orgao in ranking_maturidade:
        nivel = orgao.get('nivel_maturidade', 1)
        # Converter nível para percentual (Nível 1=20%, 2=40%, 3=60%, 4=80%, 5=100%)
        percentual_nivel = nivel * 20
        total_pontos += percentual_nivel
    
    media_sistema = int(total_pontos / total_orgaos) if total_orgaos > 0 else 0
    return min(100, media_sistema)  # Garantir que não passe de 100%

@app.route('/api/relatorio-individual', methods=['GET'])
def relatorio_individual():
    """Relatório individual do órgão do usuário - VERSÃO CORRIGIDA"""
    user_email = request.headers.get('X-User-Email', '')
    
    # Obter dados do usuário
    dados_usuario = obter_dados_usuario(user_email)
    if not dados_usuario:
        return jsonify({'success': False, 'message': 'Usuário não encontrado'}), 404
    
    orgao_id = dados_usuario.get('orgao_id')
    if not orgao_id:
        return jsonify({'success': False, 'message': 'Usuário não vinculado a um órgão'}), 400
    
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    
    try:
        # Dados do órgão
        cursor.execute('SELECT id, nome, sigla FROM orgaos WHERE id = ?', (orgao_id,))
        orgao_data = cursor.fetchone()
        
        if not orgao_data:
            return jsonify({'success': False, 'message': 'Órgão não encontrado'}), 404
        
        orgao = {
            'id': orgao_data[0],
            'nome': orgao_data[1],
            'sigla': orgao_data[2]
        }
        
        # Todas as avaliações do órgão
        cursor.execute('''
            SELECT id, titulo, status, data_criacao, nivel_desejado
            FROM avaliacoes 
            WHERE orgao_id = ? 
            ORDER BY data_criacao DESC
        ''', (orgao_id,))
        
        avaliacoes = []
        for row in cursor.fetchall():
            avaliacoes.append({
                'id': row[0],
                'titulo': row[1],
                'status': row[2],
                'data_criacao': row[3],
                'nivel_desejado': row[4]
            })
        
        # 🆕 EVOLUÇÃO TEMPORAL CORRIGIDA
        # Buscar a avaliação mais recente finalizada de cada nível
        evolucao_temporal = []
        for nivel in [2, 3, 4, 5]:  # Níveis implementáveis
            cursor.execute('''
                SELECT a.id, a.data_criacao, a.titulo, a.nivel_desejado
                FROM avaliacoes a
                WHERE a.orgao_id = ? AND a.status = 'finalizada' AND a.nivel_desejado = ?
                ORDER BY a.data_criacao DESC
                LIMIT 1
            ''', (orgao_id, nivel))
            
            resultado = cursor.fetchone()
            if resultado:
                avaliacao_id = resultado[0]
                
                # Calcular maturidade desta avaliação específica
                cursor.execute('''
                    SELECT 
                        COUNT(*) as total,
                        COUNT(CASE WHEN instituido = 1 THEN 1 END) as instituidas,
                        COUNT(CASE WHEN institucionalizado = 1 THEN 1 END) as institucionalizadas
                    FROM respostas
                    WHERE avaliacao_id = ?
                ''', (avaliacao_id,))
                
                resultado_respostas = cursor.fetchone()
                if resultado_respostas and resultado_respostas[0] > 0:
                    total = resultado_respostas[0]
                    instituidas = resultado_respostas[1]
                    institucionalizadas = resultado_respostas[2]
                    
                    # Maturidade baseada em institucionalização
                    maturidade_geral = int((institucionalizadas / total) * 100)
                    
                    evolucao_temporal.append({
                        'data_avaliacao': resultado[1],
                        'titulo_avaliacao': resultado[2],
                        'nivel': resultado[3],
                        'maturidade_geral': maturidade_geral,
                        'total_atividades': total,
                        'instituidas': instituidas,
                        'institucionalizadas': institucionalizadas
                    })
        
        # Ordenar por nível para mostrar evolução
        evolucao_temporal.sort(key=lambda x: x['nivel'])
        
        # 🆕 MATURIDADE POR KPA CORRIGIDA
        # Considerar apenas avaliações mais recentes finalizadas por nível
        maturidade_por_kpa = []
        
        # Para cada nível, pegar a avaliação mais recente finalizada
        avaliacoes_consideradas = []
        for nivel in [2, 3, 4, 5]:
            cursor.execute('''
                SELECT a.id
                FROM avaliacoes a
                WHERE a.orgao_id = ? AND a.status = 'finalizada' AND a.nivel_desejado = ?
                ORDER BY a.data_criacao DESC
                LIMIT 1
            ''', (orgao_id, nivel))
            
            resultado = cursor.fetchone()
            if resultado:
                avaliacoes_consideradas.append(resultado[0])
        
        # Agrupar respostas por KPA das avaliações consideradas
        if avaliacoes_consideradas:
            placeholders = ','.join(['?' for _ in avaliacoes_consideradas])
            cursor.execute(f'''
                SELECT r.atividade_id, r.instituido, r.institucionalizado
                FROM respostas r
                WHERE r.avaliacao_id IN ({placeholders})
            ''', avaliacoes_consideradas)
            
            respostas_por_atividade = {}
            for row in cursor.fetchall():
                atividade_id = row[0]
                kpa_codigo = '.'.join(atividade_id.split('.')[:2])  # Ex: "2.1.1" -> "2.1"
                
                if kpa_codigo not in respostas_por_atividade:
                    respostas_por_atividade[kpa_codigo] = {
                        'total': 0,
                        'instituidas': 0,
                        'institucionalizadas': 0
                    }
                
                respostas_por_atividade[kpa_codigo]['total'] += 1
                if row[1]:  # instituido
                    respostas_por_atividade[kpa_codigo]['instituidas'] += 1
                if row[2]:  # institucionalizado
                    respostas_por_atividade[kpa_codigo]['institucionalizadas'] += 1
            
            # Converter para lista com percentuais
            for kpa_codigo, dados in respostas_por_atividade.items():
                if dados['total'] > 0:
                    percentual_instituidas = int((dados['instituidas'] / dados['total']) * 100)
                    percentual_institucionalizadas = int((dados['institucionalizadas'] / dados['total']) * 100)
                    
                    maturidade_por_kpa.append({
                        'kpa_codigo': kpa_codigo,
                        'area_modelo': obter_area_kpa(kpa_codigo),
                        'total_atividades': dados['total'],
                        'instituidas': dados['instituidas'],
                        'institucionalizadas': dados['institucionalizadas'],
                        'percentual_instituidas': percentual_instituidas,
                        'percentual_institucionalizadas': percentual_institucionalizadas
                    })
        
        # Ordenar por KPA
        maturidade_por_kpa.sort(key=lambda x: x['kpa_codigo'])
        
        # 🆕 DETALHAMENTO POR KPA CORRIGIDO
        # Mostrar avaliações finalizadas mais recentes por nível + avaliações em andamento
        detalhamento_kpas = []
        
        # Avaliações finalizadas (uma por nível)
        for nivel in [2, 3, 4, 5]:
            cursor.execute('''
                SELECT a.id, a.titulo, a.data_criacao
                FROM avaliacoes a
                WHERE a.orgao_id = ? AND a.status = 'finalizada' AND a.nivel_desejado = ?
                ORDER BY a.data_criacao DESC
                LIMIT 1
            ''', (orgao_id, nivel))
            
            resultado = cursor.fetchone()
            if resultado:
                avaliacao_id = resultado[0]
                
                # Buscar KPAs desta avaliação
                cursor.execute('''
                    SELECT r.atividade_id, r.instituido, r.institucionalizado
                    FROM respostas r
                    WHERE r.avaliacao_id = ?
                ''', (avaliacao_id,))
                
                kpas_nivel = {}
                for row in cursor.fetchall():
                    atividade_id = row[0]
                    kpa_codigo = '.'.join(atividade_id.split('.')[:2])
                    
                    if kpa_codigo not in kpas_nivel:
                        kpas_nivel[kpa_codigo] = {
                            'total': 0,
                            'instituidas': 0,
                            'institucionalizadas': 0
                        }
                    
                    kpas_nivel[kpa_codigo]['total'] += 1
                    if row[1]:
                        kpas_nivel[kpa_codigo]['instituidas'] += 1
                    if row[2]:
                        kpas_nivel[kpa_codigo]['institucionalizadas'] += 1
                
                # Adicionar ao detalhamento
                for kpa_codigo, dados in kpas_nivel.items():
                    todas_institucionalizadas = dados['institucionalizadas'] == dados['total']
                    todas_instituidas = dados['instituidas'] == dados['total']
                    
                    if todas_institucionalizadas:
                        status = 'Institucionalizado'
                        cor_status = 'success'
                    elif todas_instituidas:
                        status = 'Instituído'
                        cor_status = 'warning'
                    else:
                        status = 'Parcial'
                        cor_status = 'danger'
                    
                    detalhamento_kpas.append({
                        'kpa_codigo': kpa_codigo,
                        'area_modelo': obter_area_kpa(kpa_codigo),
                        'nivel': nivel,
                        'tipo': 'finalizada',
                        'titulo_avaliacao': resultado[1],
                        'data_avaliacao': resultado[2],
                        'total_atividades': dados['total'],
                        'instituidas': dados['instituidas'],
                        'institucionalizadas': dados['institucionalizadas'],
                        'status': status,
                        'cor_status': cor_status
                    })
        
        # Avaliações em andamento (uma por nível)
        for nivel in [2, 3, 4, 5]:
            cursor.execute('''
                SELECT a.id, a.titulo, a.data_criacao
                FROM avaliacoes a
                WHERE a.orgao_id = ? AND a.status = 'em_andamento' AND a.nivel_desejado = ?
                ORDER BY a.data_criacao DESC
                LIMIT 1
            ''', (orgao_id, nivel))
            
            resultado = cursor.fetchone()
            if resultado:
                avaliacao_id = resultado[0]
                
                # Calcular percentual de preenchimento
                cursor.execute('''
                    SELECT COUNT(*) FROM respostas WHERE avaliacao_id = ?
                ''', (avaliacao_id,))
                respostas_preenchidas = cursor.fetchone()[0]
                
                # Total de atividades do nível (baseado no modelo)
                total_atividades_nivel = obter_total_atividades_nivel(nivel)
                
                percentual_preenchimento = 0
                if total_atividades_nivel > 0:
                    percentual_preenchimento = int((respostas_preenchidas / total_atividades_nivel) * 100)
                
                # Buscar KPAs desta avaliação em andamento
                cursor.execute('''
                    SELECT r.atividade_id
                    FROM respostas r
                    WHERE r.avaliacao_id = ?
                ''', (avaliacao_id,))
                
                kpas_preenchidos = set()
                for row in cursor.fetchall():
                    atividade_id = row[0]
                    kpa_codigo = '.'.join(atividade_id.split('.')[:2])
                    kpas_preenchidos.add(kpa_codigo)
                
                # Adicionar KPAs do nível ao detalhamento
                kpas_do_nivel = [f"{nivel}.{i}" for i in range(1, 7)]  # 6 KPAs por nível
                for kpa_codigo in kpas_do_nivel:
                    preenchido = kpa_codigo in kpas_preenchidos
                    
                    detalhamento_kpas.append({
                        'kpa_codigo': kpa_codigo,
                        'area_modelo': obter_area_kpa(kpa_codigo),
                        'nivel': nivel,
                        'tipo': 'em_andamento',
                        'titulo_avaliacao': resultado[1],
                        'data_avaliacao': resultado[2],
                        'percentual_preenchimento': percentual_preenchimento,
                        'kpa_preenchido': preenchido,
                        'status': 'Em Andamento',
                        'cor_status': 'info'
                    })
        
        # Ordenar detalhamento por nível e KPA
        detalhamento_kpas.sort(key=lambda x: (x['nivel'], x['kpa_codigo']))
        
        # Gerar recomendações baseadas no detalhamento
        recomendacoes = gerar_recomendacoes_corrigidas(detalhamento_kpas)
        
        # 🆕 CALCULAR NÍVEL DE MATURIDADE DO ÓRGÃO
        classificacao_maturidade = calcular_nivel_maturidade_orgao(orgao_id)
        dados_selo = gerar_dados_selo_maturidade(
            classificacao_maturidade['nivel_maturidade'],
            classificacao_maturidade['status']
        )
        
        conn.close()
        
        return jsonify({
            'success': True,
            'orgao': orgao,
            'avaliacoes': avaliacoes,
            'maturidade_por_kpa': maturidade_por_kpa,
            'evolucao_temporal': evolucao_temporal,
            'detalhamento_kpas': detalhamento_kpas,
            'recomendacoes': recomendacoes,
            'classificacao_maturidade': classificacao_maturidade,
            'selo_maturidade': dados_selo
        })
        
    except Exception as e:
        conn.close()
        logger.error(f"Erro ao gerar relatório individual: {str(e)}")
        return jsonify({'success': False, 'message': 'Erro interno do servidor'}), 500
        
def obter_total_atividades_nivel(nivel):
    """Retorna o total de atividades de um nível baseado no modelo"""
    # Baseado no modelo da planilha - cada nível tem 6 KPAs com diferentes quantidades de atividades
    atividades_por_nivel = {
        2: 30,  # Aproximadamente 5 atividades por KPA
        3: 30,
        4: 30,
        5: 30
    }
    return atividades_por_nivel.get(nivel, 30)

def obter_area_kpa(kpa_codigo):
    """Retorna a área do modelo baseada no código KPA"""
    areas = {
        '2.1': 'Governança de Riscos',
        '2.2': 'Estratégia e Objetivos',
        '2.3': 'Implementação',
        '2.4': 'Avaliação e Melhoria',
        '2.5': 'Comunicação e Consulta',
        '2.6': 'Monitoramento e Análise Crítica',
        '3.1': 'Governança de Riscos',
        '3.2': 'Estratégia e Objetivos',
        '3.3': 'Implementação',
        '3.4': 'Avaliação e Melhoria',
        '3.5': 'Comunicação e Consulta',
        '3.6': 'Monitoramento e Análise Crítica',
        '4.1': 'Governança de Riscos',
        '4.2': 'Estratégia e Objetivos',
        '4.3': 'Implementação',
        '4.4': 'Avaliação e Melhoria',
        '4.5': 'Comunicação e Consulta',
        '4.6': 'Monitoramento e Análise Crítica',
        '5.1': 'Governança de Riscos',
        '5.2': 'Estratégia e Objetivos',
        '5.3': 'Implementação',
        '5.4': 'Avaliação e Melhoria',
        '5.5': 'Comunicação e Consulta',
        '5.6': 'Monitoramento e Análise Crítica'
    }
    return areas.get(kpa_codigo, 'Área não identificada')
    
def calcular_nivel_maturidade_orgao(orgao_id):
    """
    Calcula o nível de maturidade do órgão baseado nos critérios CORRETOS:
    - TODAS as atividades de TODOS os KPAs do nível devem estar respondidas
    - TODAS as atividades respondidas devem estar institucionalizadas
    - Deve existir avaliação finalizada para o nível
    - Todos os níveis inferiores devem também atender os mesmos critérios
    """
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    
    try:
        print(f"🔍 DEBUG CLASSIFICAÇÃO - Órgão ID: {orgao_id}")
        
        # Carregar modelo completo para saber quantas atividades cada nível deve ter
        modelo_atividades = carregar_modelo_atividades()
        print(f"📋 Modelo carregado: {len(modelo_atividades)} níveis")
        
        # Verificar níveis de 5 para 2 (do maior para o menor)
        for nivel_candidato in [5, 4, 3, 2]:
            # Verificar se existe avaliação finalizada para este nível
            cursor.execute('''
                SELECT a.id, a.titulo, a.data_criacao
                FROM avaliacoes a
                WHERE a.orgao_id = ? AND a.status = 'finalizada' AND a.nivel_desejado = ?
                ORDER BY a.data_criacao DESC
                LIMIT 1
            ''', (orgao_id, nivel_candidato))
            
            avaliacao_nivel = cursor.fetchone()
            if not avaliacao_nivel:
                print(f"   ❌ Não há avaliação finalizada para o nível {nivel_candidato}")
                continue
            
            # Verificar se TODOS os níveis de 2 até o nível candidato atendem os critérios
            niveis_validos = True
            
            for nivel_verificar in range(2, nivel_candidato + 1):
                # Buscar avaliação mais recente finalizada deste nível
                cursor.execute('''
                    SELECT a.id, a.titulo
                    FROM avaliacoes a
                    WHERE a.orgao_id = ? AND a.status = 'finalizada' AND a.nivel_desejado = ?
                    ORDER BY a.data_criacao DESC
                    LIMIT 1
                ''', (orgao_id, nivel_verificar))
                
                avaliacao_verificar = cursor.fetchone()
                if not avaliacao_verificar:
                    niveis_validos = False
                    break
                
                avaliacao_id = avaliacao_verificar[0]
                
                # Obter todas as atividades que DEVERIAM estar no nível
                atividades_esperadas = modelo_atividades.get(nivel_verificar, [])
                total_atividades_esperadas = len(atividades_esperadas)
                
                
                if total_atividades_esperadas == 0:
                    niveis_validos = False
                    break
                
                # Verificar quantas atividades foram respondidas nesta avaliação
                cursor.execute('''
                    SELECT atividade_id, institucionalizado, instituido
                    FROM respostas
                    WHERE avaliacao_id = ?
                ''', (avaliacao_id,))
                
                respostas = cursor.fetchall()
                atividades_respondidas = {row[0]: {'institucionalizado': row[1], 'instituido': row[2]} for row in respostas}
                
                
                # Verificar se TODAS as atividades esperadas foram respondidas
                atividades_faltantes = []
                atividades_nao_institucionalizadas = []
                
                for atividade_id in atividades_esperadas:
                    if atividade_id not in atividades_respondidas:
                        atividades_faltantes.append(atividade_id)
                    elif not atividades_respondidas[atividade_id]['institucionalizado']:  # não institucionalizada
                        atividades_nao_institucionalizadas.append(atividade_id)
                
                # Se há atividades faltantes ou não institucionalizadas, nível não é válido
                if atividades_faltantes or atividades_nao_institucionalizadas:
                    niveis_validos = False
                    break
                else:
                    print(f"      ✅ Nível {nivel_verificar} atende critérios")
            
            # Se todos os níveis até o candidato são válidos, este é o nível de maturidade
            if niveis_validos:
                conn.close()
                return {
                    'nivel_maturidade': nivel_candidato,
                    'status': 'certificado',
                    'descricao': f'Nível {nivel_candidato} de Maturidade em Gestão de Riscos',
                    'data_certificacao': datetime.now().isoformat(),
                    'criterios_atendidos': True,
                    'detalhes': f'Todas as atividades dos níveis 2 a {nivel_candidato} estão institucionalizadas'
                }
            else:
                print(f"   ❌ Nível {nivel_candidato} não atende todos os critérios")
        
        print(f"\n❌ NENHUM NÍVEL CERTIFICADO")
        conn.close()
        return {
            'nivel_maturidade': 1,
            'status': 'inicial',
            'descricao': 'Nível Inicial - Critérios de certificação não atendidos',
            'data_certificacao': None,
            'criterios_atendidos': False,
            'detalhes': 'Nem todas as atividades dos níveis estão institucionalizadas ou avaliações não finalizadas'
        }
        
    except Exception as e:
        conn.close()
        logger.error(f"Erro ao calcular nível de maturidade: {str(e)}")
        print(f"❌ ERRO: {str(e)}")
        return {
            'nivel_maturidade': 1,
            'status': 'erro',
            'descricao': 'Erro ao calcular nível de maturidade',
            'data_certificacao': None,
            'criterios_atendidos': False,
            'detalhes': f'Erro: {str(e)}'
        }

def carregar_modelo_atividades():
    """
    Carrega o modelo de atividades do arquivo JSON para saber 
    exatamente quais atividades cada nível deve ter
    """
    try:
        # Tentar carregar do arquivo modelo_avaliacao.json
        import json
        import os
        
        # Procurar o arquivo no diretório atual ou public
        caminhos_possiveis = [
            'modelo_avaliacao.json',
            'public/modelo_avaliacao.json',
            '../public/modelo_avaliacao.json',
            'upload/modelo_avaliacao.json'  # ✅ ADICIONAR este caminho
        ]
        
        modelo_data = None
        caminho_encontrado = None
        for caminho in caminhos_possiveis:
            if os.path.exists(caminho):
                with open(caminho, 'r', encoding='utf-8') as f:
                    modelo_data = json.load(f)
                caminho_encontrado = caminho
                break
        
        if not modelo_data:
            print("❌ Arquivo modelo não encontrado, usando modelo básico")
            return gerar_modelo_basico()
        
        print(f"✅ Modelo carregado de: {caminho_encontrado}")
        
        # ✅ CORRIGIR: Usar a estrutura correta do JSON
        atividades_por_nivel = {}
        
        # O arquivo tem a estrutura: {"kpas_por_nivel": {"2": [...], "3": [...]}}
        if 'kpas_por_nivel' in modelo_data:
            for nivel_str, kpas_lista in modelo_data['kpas_por_nivel'].items():
                nivel_num = int(nivel_str)
                atividades_por_nivel[nivel_num] = []
                
                # kpas_lista é uma lista de KPAs
                for kpa in kpas_lista:
                    if 'atividades' in kpa:
                        for atividade in kpa['atividades']:
                            if 'id' in atividade:  # ✅ CORRIGIR: usar 'id' não 'codigo'
                                atividades_por_nivel[nivel_num].append(atividade['id'])
        
        # ✅ ADICIONAR: Debug para verificar quantas atividades foram carregadas
        for nivel, atividades in atividades_por_nivel.items():
            print(f"📋 Nível {nivel}: {len(atividades)} atividades carregadas")
            if nivel == 2:  # Debug detalhado para nível 2
                print(f"   Atividades: {atividades}")
        
        return atividades_por_nivel
        
    except Exception as e:
        print(f"❌ Erro ao carregar modelo de atividades: {str(e)}")
        logger.error(f"Erro ao carregar modelo de atividades: {str(e)}")
        return gerar_modelo_basico()

def gerar_modelo_basico():
    """
    Gera modelo básico automaticamente baseado na estrutura real conhecida
    Se conseguir ler o JSON, usa os dados reais. Senão, usa estrutura conhecida.
    """
    import json
    import os
    
    # PRIMEIRO: Tentar ler o arquivo JSON real
    caminhos_json = [
        'modelo_avaliacao',
        'public/modelo_avaliacao.json',
        '../public/modelo_avaliacao.json',
        'upload/modelo_avaliacao.json'
    ]
    
    for caminho in caminhos_json:
        try:
            if os.path.exists(caminho):
                with open(caminho, 'r', encoding='utf-8') as f:
                    modelo_data = json.load(f)
                
                print(f"✅ Gerando modelo básico a partir de: {caminho}")
                
                # Extrair atividades do JSON real
                modelo_basico = {}
                
                if 'kpas_por_nivel' in modelo_data:
                    for nivel_str, kpas_lista in modelo_data['kpas_por_nivel'].items():
                        nivel_num = int(nivel_str)
                        modelo_basico[nivel_num] = []
                        
                        for kpa in kpas_lista:
                            if 'atividades' in kpa:
                                for atividade in kpa['atividades']:
                                    if 'id' in atividade:
                                        modelo_basico[nivel_num].append(atividade['id'])
                
                print(f"📋 Modelo gerado automaticamente:")
                for nivel, atividades in modelo_basico.items():
                    print(f"   Nível {nivel}: {len(atividades)} atividades")
                
                return modelo_basico
                
        except Exception as e:
            print(f"⚠️ Erro ao ler {caminho}: {e}")
            continue
    
    # SEGUNDO: Se não conseguiu ler o JSON, usar estrutura conhecida inteligente
    print("⚠️ JSON não encontrado, usando estrutura conhecida")
    
    # Estrutura real conhecida (baseada no que você confirmou)
    estrutura_real = {
        2: {
            1: 5,  # KPA 2.1: 5 atividades (2.1.1 a 2.1.5)
            2: 5,  # KPA 2.2: 5 atividades (2.2.1 a 2.2.5)
            3: 5,  # KPA 2.3: 5 atividades (2.3.1 a 2.3.5)
            4: 6,  # KPA 2.4: 6 atividades (2.4.1 a 2.4.6)
            5: 5,  # KPA 2.5: 5 atividades (2.5.1 a 2.5.5)
            6: 4   # KPA 2.6: 4 atividades (2.6.1 a 2.6.4) ← SEM 2.6.5!
        },
        3: {
            1: 5, 2: 5, 3: 5, 4: 5, 5: 5, 6: 5  # Assumir 5 para cada KPA do nível 3
        },
        4: {
            1: 5, 2: 5, 3: 5, 4: 5, 5: 5, 6: 5  # Assumir 5 para cada KPA do nível 4
        },
        5: {
            1: 5, 2: 5, 3: 5, 4: 5, 5: 5, 6: 5  # Assumir 5 para cada KPA do nível 5
        }
    }
    
    modelo_basico = {}
    
    for nivel, kpas_info in estrutura_real.items():
        modelo_basico[nivel] = []
        
        for kpa_num, qtd_atividades in kpas_info.items():
            for atividade_num in range(1, qtd_atividades + 1):
                codigo = f"{nivel}.{kpa_num}.{atividade_num}"
                modelo_basico[nivel].append(codigo)
    
    print(f"📋 Modelo gerado por estrutura conhecida:")
    for nivel, atividades in modelo_basico.items():
        print(f"   Nível {nivel}: {len(atividades)} atividades")
    
    return modelo_basico

def verificar_completude_nivel(orgao_id, nivel, avaliacao_id=None):
    """
    Verifica se um nível específico está completo (todas atividades institucionalizadas)
    """
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    
    try:
        # Se não foi passada avaliação específica, buscar a mais recente finalizada
        if not avaliacao_id:
            cursor.execute('''
                SELECT a.id
                FROM avaliacoes a
                WHERE a.orgao_id = ? AND a.status = 'finalizada' AND a.nivel_desejado = ?
                ORDER BY a.data_criacao DESC
                LIMIT 1
            ''', (orgao_id, nivel))
            
            resultado = cursor.fetchone()
            if not resultado:
                return False, "Nenhuma avaliação finalizada encontrada"
            
            avaliacao_id = resultado[0]
        
        # Carregar atividades esperadas para o nível
        modelo_atividades = carregar_modelo_atividades()
        atividades_esperadas = modelo_atividades.get(nivel, [])
        
        if not atividades_esperadas:
            return False, "Modelo de atividades não encontrado"
        
        # Buscar respostas da avaliação
        cursor.execute('''
            SELECT atividade_id, institucionalizado
            FROM respostas
            WHERE avaliacao_id = ?
        ''', (avaliacao_id,))
        
        respostas = cursor.fetchall()
        atividades_respondidas = {row[0]: row[1] for row in respostas}
        
        # Verificar completude
        total_esperadas = len(atividades_esperadas)
        total_respondidas = len([a for a in atividades_esperadas if a in atividades_respondidas])
        total_institucionalizadas = len([a for a in atividades_esperadas 
                                       if a in atividades_respondidas and atividades_respondidas[a]])
        
        completo = (total_respondidas == total_esperadas and 
                   total_institucionalizadas == total_esperadas)
        
        detalhes = {
            'total_esperadas': total_esperadas,
            'total_respondidas': total_respondidas,
            'total_institucionalizadas': total_institucionalizadas,
            'percentual_completude': int((total_respondidas / total_esperadas) * 100) if total_esperadas > 0 else 0,
            'percentual_institucionalizacao': int((total_institucionalizadas / total_esperadas) * 100) if total_esperadas > 0 else 0
        }
        
        conn.close()
        return completo, detalhes
        
    except Exception as e:
        conn.close()
        return False, f"Erro: {str(e)}"

def gerar_dados_selo_maturidade(nivel_maturidade, status):
    """Gera dados para o selo de maturidade"""
    
    cores_por_nivel = {
        1: {'cor_principal': '#6c757d', 'cor_secundaria': '#495057', 'nome_cor': 'Cinza'},
        2: {'cor_principal': '#ffc107', 'cor_secundaria': '#e0a800', 'nome_cor': 'Bronze'},
        3: {'cor_principal': '#fd7e14', 'cor_secundaria': '#e8590c', 'nome_cor': 'Prata'},
        4: {'cor_principal': '#20c997', 'cor_secundaria': '#1aa179', 'nome_cor': 'Ouro'},
        5: {'cor_principal': '#6f42c1', 'cor_secundaria': '#59359a', 'nome_cor': 'Platina'}
    }
    
    if status == 'certificado' and nivel_maturidade in cores_por_nivel:
        cor_info = cores_por_nivel[nivel_maturidade]
        return {
            'mostrar_selo': True,
            'nivel': nivel_maturidade,
            'titulo': f'Nível {nivel_maturidade}',
            'subtitulo': 'Gestão de Riscos ISO 31000',
            'cor_principal': cor_info['cor_principal'],
            'cor_secundaria': cor_info['cor_secundaria'],
            'nome_cor': cor_info['nome_cor'],
            'icone': 'bi-award-fill',
            'certificado': True
        }
    else:
        return {
            'mostrar_selo': False,
            'nivel': 1,
            'titulo': 'Nível Inicial',
            'subtitulo': 'Continue avaliando para obter certificação',
            'cor_principal': '#6c757d',
            'cor_secundaria': '#495057',
            'nome_cor': 'Sem Certificação',
            'icone': 'bi-hourglass-split',
            'certificado': False
        }

    
def gerar_recomendacoes_corrigidas(detalhamento_kpas):
    """Gera recomendações baseadas no detalhamento corrigido"""
    recomendacoes = []
    
    # Agrupar por nível e tipo
    niveis_finalizados = {}
    niveis_em_andamento = {}
    
    for item in detalhamento_kpas:
        nivel = item['nivel']
        tipo = item['tipo']
        
        if tipo == 'finalizada':
            if nivel not in niveis_finalizados:
                niveis_finalizados[nivel] = []
            niveis_finalizados[nivel].append(item)
        else:
            if nivel not in niveis_em_andamento:
                niveis_em_andamento[nivel] = []
            niveis_em_andamento[nivel].append(item)
    
    # Recomendações para níveis finalizados
    for nivel, kpas in niveis_finalizados.items():
        kpas_parciais = [k for k in kpas if k['status'] == 'Parcial']
        kpas_instituidos = [k for k in kpas if k['status'] == 'Instituído']
        
        if kpas_parciais:
            recomendacoes.append({
                'titulo': f'Completar Nível {nivel}',
                'descricao': f'Há {len(kpas_parciais)} KPAs com implementação parcial no Nível {nivel}. Foque em institucionalizar as práticas.',
                'prioridade': 'Alta'
            })
        
        if kpas_instituidos:
            recomendacoes.append({
                'titulo': f'Institucionalizar Nível {nivel}',
                'descricao': f'Há {len(kpas_instituidos)} KPAs apenas instituídos no Nível {nivel}. Desenvolva histórico de práticas.',
                'prioridade': 'Média'
            })
    
    # Recomendações para níveis em andamento
    for nivel, kpas in niveis_em_andamento.items():
        if kpas:
            percentual = kpas[0]['percentual_preenchimento']
            if percentual < 50:
                recomendacoes.append({
                    'titulo': f'Continuar Avaliação Nível {nivel}',
                    'descricao': f'Avaliação do Nível {nivel} está {percentual}% completa. Continue o preenchimento.',
                    'prioridade': 'Média'
                })
    
    return recomendacoes[:6]  # Limitar a 6 recomendações

def gerar_recomendacoes(maturidade_por_kpa):
    """Gera recomendações baseadas na maturidade dos KPAs"""
    recomendacoes = []
    
    for kpa in maturidade_por_kpa:
        if kpa['maturidade_percentual'] < 40:
            recomendacoes.append({
                'titulo': f'Melhorar {kpa["area_modelo"]} (KPA {kpa["kpa_codigo"]})',
                'descricao': f'Foco em institucionalizar as práticas básicas desta área. Maturidade atual: {kpa["maturidade_percentual"]}%',
                'prioridade': 'Alta'
            })
        elif kpa['maturidade_percentual'] < 60:
            recomendacoes.append({
                'titulo': f'Aprimorar {kpa["area_modelo"]} (KPA {kpa["kpa_codigo"]})',
                'descricao': f'Consolidar as práticas já implementadas e buscar melhorias incrementais. Maturidade atual: {kpa["maturidade_percentual"]}%',
                'prioridade': 'Média'
            })
    
    # Limitar a 6 recomendações
    return recomendacoes[:6]
    

def gerar_pdf_simples(dados):
    """Gera PDF completo do relatório individual - VERSÃO FINAL"""
    from reportlab.lib.pagesizes import A4
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib import colors
    from reportlab.lib.units import inch
    from io import BytesIO
    from datetime import datetime
    import sqlite3
    
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, topMargin=0.5*inch, bottomMargin=0.5*inch)
    styles = getSampleStyleSheet()
    
    # Estilos customizados
    titulo_secao = ParagraphStyle(
        'TituloSecao',
        parent=styles['Heading1'],
        fontSize=14,
        textColor=colors.HexColor('#2e75b6'),
        spaceAfter=10,
        borderWidth=1,
        borderColor=colors.HexColor('#2e75b6'),
        borderPadding=5,
        backColor=colors.HexColor('#f2f8ff')
    )
    
    subtitulo = ParagraphStyle(
        'Subtitulo',
        parent=styles['Heading2'],
        fontSize=12,
        textColor=colors.HexColor('#4472c4'),
        spaceAfter=8
    )
    
    subtitulo_verde = ParagraphStyle(
        'SubtituloVerde',
        parent=styles['Heading2'],
        fontSize=11,
        textColor=colors.HexColor('#2d5016'),
        spaceAfter=6,
        backColor=colors.HexColor('#e8f5e8'),
        borderWidth=1,
        borderColor=colors.HexColor('#4caf50'),
        borderPadding=3
    )
    
    subtitulo_azul = ParagraphStyle(
        'SubtituloAzul',
        parent=styles['Heading2'],
        fontSize=11,
        textColor=colors.HexColor('#1565c0'),
        spaceAfter=6,
        backColor=colors.HexColor('#e3f2fd'),
        borderWidth=1,
        borderColor=colors.HexColor('#2196f3'),
        borderPadding=3
    )
    
    # Estilos para recomendações
    rec_alta = ParagraphStyle(
        'RecomendacaoAlta',
        parent=styles['Normal'],
        fontSize=10,
        textColor=colors.HexColor('#d32f2f'),
        backColor=colors.HexColor('#ffebee'),
        borderWidth=1,
        borderColor=colors.HexColor('#f44336'),
        borderPadding=5,
        spaceAfter=8
    )
    
    rec_media = ParagraphStyle(
        'RecomendacaoMedia',
        parent=styles['Normal'],
        fontSize=10,
        textColor=colors.HexColor('#f57c00'),
        backColor=colors.HexColor('#fff3e0'),
        borderWidth=1,
        borderColor=colors.HexColor('#ff9800'),
        borderPadding=5,
        spaceAfter=8
    )
    
    rec_baixa = ParagraphStyle(
        'RecomendacaoBaixa',
        parent=styles['Normal'],
        fontSize=10,
        textColor=colors.HexColor('#1976d2'),
        backColor=colors.HexColor('#e3f2fd'),
        borderWidth=1,
        borderColor=colors.HexColor('#2196f3'),
        borderPadding=5,
        spaceAfter=8
    )
    
    story = []
    
    # ===== CABEÇALHO =====
    story.append(Paragraph("RELATÓRIO DE MATURIDADE EM GESTÃO DE RISCOS", styles['Title']))
    story.append(Spacer(1, 20))
    
    story.append(Paragraph(f"<b>Órgão:</b> {dados['orgao_nome']}", styles['Normal']))
    story.append(Paragraph(f"<b>Sigla:</b> {dados['orgao_sigla']}", styles['Normal']))
    story.append(Paragraph(f"<b>Usuário:</b> {dados['usuario_nome']}", styles['Normal']))
    story.append(Paragraph(f"<b>Data:</b> {datetime.now().strftime('%d/%m/%Y às %H:%M')}", styles['Normal']))
    story.append(Spacer(1, 30))
    
    # Obter orgao_id para as próximas seções
    orgao_id = None
    try:
        from main import obter_dados_usuario
        user_email = dados.get('usuario_email', '')
        if user_email:
            dados_usuario = obter_dados_usuario(user_email)
            orgao_id = dados_usuario.get('orgao_id') if dados_usuario else None
    except:
        pass
    
    # ===== 1. CERTIFICAÇÃO =====
    story.append(Paragraph("1. CERTIFICAÇÃO DE MATURIDADE", titulo_secao))
    
    classificacao = None
    try:
        if orgao_id:
            from main import calcular_nivel_maturidade_orgao
            classificacao = calcular_nivel_maturidade_orgao(orgao_id)
            
            if classificacao.get('status') == 'certificado':
                story.append(Paragraph(f"🏆 <b>NÍVEL {classificacao.get('nivel_maturidade')} CERTIFICADO</b>", subtitulo))
                story.append(Paragraph(f"<b>Status:</b> {classificacao.get('descricao', 'N/A')}", styles['Normal']))
                
                data_cert = classificacao.get('data_certificacao', '')
                if data_cert:
                    data_formatada = data_cert[:10] if len(data_cert) >= 10 else data_cert
                    story.append(Paragraph(f"<b>Data de Certificação:</b> {data_formatada}", styles['Normal']))
                    
                story.append(Paragraph(f"<b>Detalhes:</b> {classificacao.get('detalhes', 'N/A')}", styles['Normal']))
            else:
                story.append(Paragraph("⚠️ <b>NÍVEL INICIAL</b>", subtitulo))
                story.append(Paragraph(f"<b>Status:</b> {classificacao.get('descricao', 'Critérios não atendidos')}", styles['Normal']))
                story.append(Paragraph(f"<b>Detalhes:</b> {classificacao.get('detalhes', 'N/A')}", styles['Normal']))
        else:
            story.append(Paragraph("⚠️ Órgão não identificado", styles['Normal']))
            
    except Exception as e:
        story.append(Paragraph(f"⚠️ Erro ao obter certificação: {str(e)}", styles['Normal']))
    
    story.append(Spacer(1, 20))
    
    # ===== 2. MATURIDADE POR KPA =====
    story.append(Paragraph("2. MATURIDADE POR ÁREA DE PROCESSO (KPA)", titulo_secao))
    
    maturidade_kpas = []  # Guardar para usar no detalhamento e recomendações
    
    try:
        if orgao_id:
            conn = sqlite3.connect('sistema_cge.db')
            cursor = conn.cursor()
            
            # Buscar maturidade por KPA das avaliações finalizadas mais recentes
            for nivel in [2, 3, 4, 5]:
                # Buscar avaliação mais recente finalizada do nível
                cursor.execute('''
                    SELECT a.id, a.titulo, a.data_criacao
                    FROM avaliacoes a
                    WHERE a.orgao_id = ? AND a.status = 'finalizada' AND a.nivel_desejado = ?
                    ORDER BY a.data_criacao DESC
                    LIMIT 1
                ''', (orgao_id, nivel))
                
                resultado = cursor.fetchone()
                if resultado:
                    avaliacao_id = resultado[0]
                    
                    # Agrupar respostas por KPA
                    cursor.execute('''
                        SELECT atividade_id, instituido, institucionalizado
                        FROM respostas
                        WHERE avaliacao_id = ?
                    ''', (avaliacao_id,))
                    
                    kpas_nivel = {}
                    for row in cursor.fetchall():
                        atividade_id = row[0]
                        kpa_codigo = '.'.join(atividade_id.split('.')[:2])
                        
                        if kpa_codigo not in kpas_nivel:
                            kpas_nivel[kpa_codigo] = {
                                'total': 0,
                                'instituidas': 0,
                                'institucionalizadas': 0
                            }
                        
                        kpas_nivel[kpa_codigo]['total'] += 1
                        if row[1]:  # instituido
                            kpas_nivel[kpa_codigo]['instituidas'] += 1
                        if row[2]:  # institucionalizado
                            kpas_nivel[kpa_codigo]['institucionalizadas'] += 1
                    
                    # Adicionar à lista de maturidade
                    for kpa_codigo, dados_kpa in kpas_nivel.items():
                        if dados_kpa['total'] > 0:
                            perc_instituidas = int((dados_kpa['instituidas'] / dados_kpa['total']) * 100)
                            perc_institucionalizadas = int((dados_kpa['institucionalizadas'] / dados_kpa['total']) * 100)
                            
                            # Obter nome da área
                            area_nome = obter_area_kpa_segura(kpa_codigo)
                            
                            maturidade_kpas.append({
                                'kpa_codigo': kpa_codigo,
                                'area_nome': area_nome,
                                'nivel': nivel,
                                'perc_instituidas': perc_instituidas,
                                'perc_institucionalizadas': perc_institucionalizadas,
                                'total_atividades': dados_kpa['total'],
                                'atividades_institucionalizadas': dados_kpa['institucionalizadas'],
                                'atividades_instituidas': dados_kpa['instituidas'],
                                'avaliacao_id': avaliacao_id,
                                'titulo_avaliacao': resultado[1],
                                'data_avaliacao': resultado[2][:10] if resultado[2] else 'N/A'
                            })
            
            # Criar tabela de maturidade por KPA
            if maturidade_kpas:
                dados_tabela = [['KPA', 'Área', 'Nível', 'Instituídas', 'Institucionalizadas', 'Status']]
                
                for kpa in maturidade_kpas:
                    # Determinar status
                    if kpa['perc_institucionalizadas'] == 100:
                        status = "✅ Completo"
                    elif kpa['perc_institucionalizadas'] > 0:
                        status = "⚠️ Parcial"
                    else:
                        status = "❌ Inicial"
                    
                    dados_tabela.append([
                        kpa['kpa_codigo'],
                        kpa['area_nome'][:20] + '...' if len(kpa['area_nome']) > 20 else kpa['area_nome'],
                        str(kpa['nivel']),
                        f"{kpa['perc_instituidas']}%",
                        f"{kpa['perc_institucionalizadas']}%",
                        status
                    ])
                
                # Criar tabela formatada
                tabela_kpas = Table(dados_tabela, colWidths=[0.6*inch, 1.8*inch, 0.5*inch, 0.8*inch, 1*inch, 0.8*inch])
                tabela_kpas.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2e75b6')),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, 0), 9),
                    ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
                    ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                    ('GRID', (0, 0), (-1, -1), 1, colors.black),
                    ('FONTSIZE', (0, 1), (-1, -1), 8),
                    ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ]))
                
                story.append(tabela_kpas)
                
                # Resumo estatístico
                story.append(Spacer(1, 15))
                story.append(Paragraph("<b>Resumo Estatístico:</b>", subtitulo))
                
                total_kpas = len(maturidade_kpas)
                kpas_completos = len([k for k in maturidade_kpas if k['perc_institucionalizadas'] == 100])
                kpas_parciais = len([k for k in maturidade_kpas if 0 < k['perc_institucionalizadas'] < 100])
                kpas_iniciais = len([k for k in maturidade_kpas if k['perc_institucionalizadas'] == 0])
                
                story.append(Paragraph(f"• <b>Total de KPAs avaliados:</b> {total_kpas}", styles['Normal']))
                story.append(Paragraph(f"• <b>KPAs completos (100%):</b> {kpas_completos}", styles['Normal']))
                story.append(Paragraph(f"• <b>KPAs parciais (1-99%):</b> {kpas_parciais}", styles['Normal']))
                story.append(Paragraph(f"• <b>KPAs iniciais (0%):</b> {kpas_iniciais}", styles['Normal']))
                
            else:
                story.append(Paragraph("Nenhum dado de maturidade por KPA disponível.", styles['Normal']))
            
            conn.close()
        else:
            story.append(Paragraph("Órgão não identificado para buscar dados de maturidade.", styles['Normal']))
            
    except Exception as e:
        story.append(Paragraph(f"Erro ao obter maturidade por KPA: {str(e)}", styles['Normal']))
    
    story.append(Spacer(1, 20))
    
    # ===== 3. EVOLUÇÃO TEMPORAL =====
    story.append(Paragraph("3. EVOLUÇÃO DA MATURIDADE AO LONGO DO TEMPO", titulo_secao))
    
    evolucao_temporal = []
    try:
        if orgao_id:
            conn = sqlite3.connect('sistema_cge.db')
            cursor = conn.cursor()
            
            # Buscar evolução temporal - uma avaliação finalizada por nível
            for nivel in [2, 3, 4, 5]:
                cursor.execute('''
                    SELECT a.id, a.titulo, a.data_criacao, a.nivel_desejado
                    FROM avaliacoes a
                    WHERE a.orgao_id = ? AND a.status = 'finalizada' AND a.nivel_desejado = ?
                    ORDER BY a.data_criacao DESC
                    LIMIT 1
                ''', (orgao_id, nivel))
                
                resultado = cursor.fetchone()
                if resultado:
                    avaliacao_id = resultado[0]
                    
                    # Calcular maturidade desta avaliação específica
                    cursor.execute('''
                        SELECT 
                            COUNT(*) as total,
                            COUNT(CASE WHEN instituido = 1 THEN 1 END) as instituidas,
                            COUNT(CASE WHEN institucionalizado = 1 THEN 1 END) as institucionalizadas
                        FROM respostas
                        WHERE avaliacao_id = ?
                    ''', (avaliacao_id,))
                    
                    resultado_respostas = cursor.fetchone()
                    if resultado_respostas and resultado_respostas[0] > 0:
                        total = resultado_respostas[0]
                        instituidas = resultado_respostas[1]
                        institucionalizadas = resultado_respostas[2]
                        
                        # Maturidade baseada em institucionalização
                        maturidade_geral = int((institucionalizadas / total) * 100)
                        maturidade_instituidas = int((instituidas / total) * 100)
                        
                        # Formatar data
                        data_avaliacao = resultado[2][:10] if resultado[2] else 'N/A'
                        
                        evolucao_temporal.append({
                            'nivel': resultado[3],
                            'titulo': resultado[1],
                            'data': data_avaliacao,
                            'maturidade_institucionalizada': maturidade_geral,
                            'maturidade_instituida': maturidade_instituidas,
                            'total_atividades': total,
                            'atividades_institucionalizadas': institucionalizadas,
                            'atividades_instituidas': instituidas
                        })
            
            # Ordenar por nível
            evolucao_temporal.sort(key=lambda x: x['nivel'])
            
            if evolucao_temporal:
                story.append(Paragraph("<b>Histórico de Progresso por Nível:</b>", subtitulo))
                
                # Criar tabela de evolução
                dados_tabela = [['Nível', 'Data Avaliação', 'Título', 'Maturidade', 'Atividades', 'Tendência']]
                
                maturidade_anterior = 0
                for i, item in enumerate(evolucao_temporal):
                    # Calcular tendência
                    if i == 0:
                        tendencia = "🆕 Inicial"
                    else:
                        if item['maturidade_institucionalizada'] > maturidade_anterior:
                            tendencia = "📈 Crescimento"
                        elif item['maturidade_institucionalizada'] == maturidade_anterior:
                            tendencia = "➡️ Estável"
                        else:
                            tendencia = "📉 Declínio"
                    
                    dados_tabela.append([
                        f"Nível {item['nivel']}",
                        item['data'],
                        item['titulo'][:15] + '...' if len(item['titulo']) > 15 else item['titulo'],
                        f"{item['maturidade_institucionalizada']}%",
                        f"{item['atividades_institucionalizadas']}/{item['total_atividades']}",
                        tendencia
                    ])
                    
                    maturidade_anterior = item['maturidade_institucionalizada']
                
                # Criar tabela formatada
                tabela_evolucao = Table(dados_tabela, colWidths=[0.8*inch, 1*inch, 1.5*inch, 0.8*inch, 0.8*inch, 1*inch])
                tabela_evolucao.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2e75b6')),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, 0), 9),
                    ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
                    ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                    ('GRID', (0, 0), (-1, -1), 1, colors.black),
                    ('FONTSIZE', (0, 1), (-1, -1), 8),
                    ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ]))
                
                story.append(tabela_evolucao)
                
                # Análise da evolução
                story.append(Spacer(1, 15))
                story.append(Paragraph("<b>Análise da Evolução:</b>", subtitulo))
                
                if len(evolucao_temporal) >= 2:
                    primeiro = evolucao_temporal[0]
                    ultimo = evolucao_temporal[-1]
                    
                    crescimento = ultimo['maturidade_institucionalizada'] - primeiro['maturidade_institucionalizada']
                    niveis_avaliados = len(evolucao_temporal)
                    
                    story.append(Paragraph(f"• <b>Níveis avaliados:</b> {niveis_avaliados} ({primeiro['nivel']} ao {ultimo['nivel']})", styles['Normal']))
                    story.append(Paragraph(f"• <b>Período:</b> {primeiro['data']} a {ultimo['data']}", styles['Normal']))
                    story.append(Paragraph(f"• <b>Crescimento total:</b> {crescimento:+d} pontos percentuais", styles['Normal']))
                    
                    if crescimento > 0:
                        story.append(Paragraph(f"• <b>Tendência:</b> 📈 Evolução positiva da maturidade", styles['Normal']))
                    elif crescimento == 0:
                        story.append(Paragraph(f"• <b>Tendência:</b> ➡️ Maturidade estável", styles['Normal']))
                    else:
                        story.append(Paragraph(f"• <b>Tendência:</b> 📉 Necessita atenção", styles['Normal']))
                        
                    # Nível atual
                    nivel_atual = ultimo['nivel']
                    maturidade_atual = ultimo['maturidade_institucionalizada']
                    story.append(Paragraph(f"• <b>Status atual:</b> Nível {nivel_atual} com {maturidade_atual}% de maturidade", styles['Normal']))
                    
                else:
                    story.append(Paragraph("• Apenas um nível avaliado. Evolução temporal será disponível com mais avaliações.", styles['Normal']))
                
            else:
                story.append(Paragraph("Nenhuma avaliação finalizada encontrada para análise temporal.", styles['Normal']))
            
            conn.close()
        else:
            story.append(Paragraph("Órgão não identificado para análise temporal.", styles['Normal']))
            
    except Exception as e:
        story.append(Paragraph(f"Erro ao obter evolução temporal: {str(e)}", styles['Normal']))
    
    # ===== QUEBRA DE PÁGINA =====
    story.append(PageBreak())
    
    # ===== 4. DETALHAMENTO POR KPA =====
    story.append(Paragraph("4. DETALHAMENTO POR KPA", titulo_secao))
    
    avaliacoes_andamento = []
    try:
        if orgao_id:
            conn = sqlite3.connect('sistema_cge.db')
            cursor = conn.cursor()
            
            # ===== 4.1 AVALIAÇÕES FINALIZADAS =====
            story.append(Paragraph("4.1. Avaliações Finalizadas", subtitulo_verde))
            
            if maturidade_kpas:
                for kpa in maturidade_kpas:
                    # Determinar status detalhado
                    if kpa['perc_institucionalizadas'] == 100:
                        status_icon = "✅"
                        status_texto = "Institucionalizado"
                    elif kpa['perc_institucionalizadas'] > 0:
                        status_icon = "⚠️"
                        status_texto = "Parcialmente Implementado"
                    else:
                        status_icon = "❌"
                        status_texto = "Não Implementado"
                    
                    # Informações do KPA
                    story.append(Paragraph(f"<b>{kpa['kpa_codigo']} - {kpa['area_nome']}</b>", styles['Normal']))
                    story.append(Paragraph(f"Nível {kpa['nivel']} | Data: {kpa['data_avaliacao']} | Status: {status_icon} {status_texto}", styles['Normal']))
                    story.append(Paragraph(f"Atividades: {kpa['atividades_institucionalizadas']}/{kpa['total_atividades']} institucionalizadas, {kpa['atividades_instituidas']}/{kpa['total_atividades']} instituídas", styles['Normal']))
                    story.append(Paragraph(f"Avaliação: {kpa['titulo_avaliacao']}", styles['Normal']))
                    story.append(Spacer(1, 8))
            else:
                story.append(Paragraph("Nenhuma avaliação finalizada encontrada.", styles['Normal']))
            
            story.append(Spacer(1, 15))
            
            # ===== 4.2 AVALIAÇÕES EM ANDAMENTO =====
            story.append(Paragraph("4.2. Avaliações em Andamento", subtitulo_azul))
            
            # Buscar avaliações em andamento
            cursor.execute('''
                SELECT a.id, a.titulo, a.nivel_desejado, a.data_criacao
                FROM avaliacoes a
                WHERE a.orgao_id = ? AND a.status = 'em_andamento'
                ORDER BY a.data_criacao DESC
            ''', (orgao_id,))
            
            avaliacoes_andamento = cursor.fetchall()
            
            if avaliacoes_andamento:
                for avaliacao in avaliacoes_andamento:
                    avaliacao_id = avaliacao[0]
                    titulo = avaliacao[1]
                    nivel = avaliacao[2]
                    data_criacao = avaliacao[3][:10] if avaliacao[3] else 'N/A'
                    
                    # Calcular progresso por KPA desta avaliação
                    cursor.execute('''
                        SELECT atividade_id, instituido, institucionalizado
                        FROM respostas
                        WHERE avaliacao_id = ?
                    ''', (avaliacao_id,))
                    
                    respostas_andamento = cursor.fetchall()
                    
                    # Agrupar por KPA
                    kpas_andamento = {}
                    for resposta in respostas_andamento:
                        atividade_id = resposta[0]
                        kpa_codigo = '.'.join(atividade_id.split('.')[:2])
                        
                        if kpa_codigo not in kpas_andamento:
                            kpas_andamento[kpa_codigo] = {
                                'respondidas': 0,
                                'total_esperado': 0
                            }
                        
                        kpas_andamento[kpa_codigo]['respondidas'] += 1
                    
                    # Calcular total esperado por KPA (baseado no modelo)
                    from main import carregar_modelo_atividades
                    modelo = carregar_modelo_atividades()
                    atividades_nivel = modelo.get(nivel, [])
                    
                    for atividade_id in atividades_nivel:
                        kpa_codigo = '.'.join(atividade_id.split('.')[:2])
                        if kpa_codigo not in kpas_andamento:
                            kpas_andamento[kpa_codigo] = {
                                'respondidas': 0,
                                'total_esperado': 0
                            }
                        kpas_andamento[kpa_codigo]['total_esperado'] += 1
                    
                    # Mostrar informações da avaliação
                    story.append(Paragraph(f"<b>Avaliação: {titulo}</b>", styles['Normal']))
                    story.append(Paragraph(f"Nível {nivel} | Criada em: {data_criacao}", styles['Normal']))
                    story.append(Spacer(1, 5))
                    
                    # Mostrar progresso por KPA
                    if kpas_andamento:
                        for kpa_codigo, dados in kpas_andamento.items():
                            if dados['total_esperado'] > 0:
                                percentual = int((dados['respondidas'] / dados['total_esperado']) * 100)
                                area_nome = obter_area_kpa_segura(kpa_codigo)
                                
                                # Ícone baseado no progresso
                                if percentual == 100:
                                    icone = "✅"
                                elif percentual >= 50:
                                    icone = "🔄"
                                else:
                                    icone = "⏳"
                                
                                story.append(Paragraph(f"  {icone} <b>{kpa_codigo} - {area_nome}</b>", styles['Normal']))
                                story.append(Paragraph(f"     Preenchimento: {percentual}% ({dados['respondidas']}/{dados['total_esperado']} atividades)", styles['Normal']))
                    else:
                        story.append(Paragraph("  Nenhuma atividade respondida ainda.", styles['Normal']))
                    
                    story.append(Spacer(1, 10))
            else:
                story.append(Paragraph("Nenhuma avaliação em andamento encontrada.", styles['Normal']))
            
            conn.close()
        else:
            story.append(Paragraph("Órgão não identificado para detalhamento.", styles['Normal']))
            
    except Exception as e:
        story.append(Paragraph(f"Erro ao obter detalhamento por KPA: {str(e)}", styles['Normal']))
    
    story.append(Spacer(1, 20))
    
    # ===== 5. RECOMENDAÇÕES =====
    story.append(Paragraph("5. RECOMENDAÇÕES", titulo_secao))
    
    # Gerar recomendações baseadas nos dados coletados
    recomendacoes = gerar_recomendacoes_inteligentes(maturidade_kpas, avaliacoes_andamento, classificacao, evolucao_temporal)
    
    if recomendacoes:
        # Separar por prioridade
        alta_prioridade = [r for r in recomendacoes if r['prioridade'] == 'alta']
        media_prioridade = [r for r in recomendacoes if r['prioridade'] == 'media']
        baixa_prioridade = [r for r in recomendacoes if r['prioridade'] == 'baixa']
        
        # Alta prioridade
        if alta_prioridade:
            story.append(Paragraph("🔴 <b>ALTA PRIORIDADE</b>", subtitulo))
            for rec in alta_prioridade:
                story.append(Paragraph(f"<b>• {rec['titulo']}</b>", rec_alta))
                story.append(Paragraph(f"  {rec['descricao']}", styles['Normal']))
                story.append(Spacer(1, 5))
        
        # Média prioridade
        if media_prioridade:
            story.append(Paragraph("🟡 <b>MÉDIA PRIORIDADE</b>", subtitulo))
            for rec in media_prioridade:
                story.append(Paragraph(f"<b>• {rec['titulo']}</b>", rec_media))
                story.append(Paragraph(f"  {rec['descricao']}", styles['Normal']))
                story.append(Spacer(1, 5))
        
        # Baixa prioridade
        if baixa_prioridade:
            story.append(Paragraph("🔵 <b>BAIXA PRIORIDADE</b>", subtitulo))
            for rec in baixa_prioridade:
                story.append(Paragraph(f"<b>• {rec['titulo']}</b>", rec_baixa))
                story.append(Paragraph(f"  {rec['descricao']}", styles['Normal']))
                story.append(Spacer(1, 5))
    else:
        story.append(Paragraph("Nenhuma recomendação específica no momento. Continue monitorando o progresso das avaliações.", styles['Normal']))
    
    story.append(Spacer(1, 20))
    
    # ===== 6. RESUMO DE AVALIAÇÕES =====
    story.append(Paragraph("6. RESUMO DE AVALIAÇÕES", titulo_secao))
    
    try:
        if orgao_id:
            conn = sqlite3.connect('sistema_cge.db')
            cursor = conn.cursor()
            
            # Contar avaliações por status
            cursor.execute('''
                SELECT status, COUNT(*) 
                FROM avaliacoes 
                WHERE orgao_id = ? 
                GROUP BY status
            ''', (orgao_id,))
            
            resultados = cursor.fetchall()
            
            if resultados:
                dados_tabela = [['Status', 'Quantidade']]
                for status, count in resultados:
                    status_nome = 'Finalizada' if status == 'finalizada' else 'Em Andamento'
                    dados_tabela.append([status_nome, str(count)])
                
                tabela = Table(dados_tabela, colWidths=[2*inch, 1*inch])
                tabela.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2e75b6')),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, 0), 10),
                    ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                    ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ]))
                story.append(tabela)
            else:
                story.append(Paragraph("Nenhuma avaliação encontrada.", styles['Normal']))
            
            conn.close()
        else:
            story.append(Paragraph("Órgão não identificado para buscar avaliações.", styles['Normal']))
            
    except Exception as e:
        story.append(Paragraph(f"Erro ao obter resumo: {str(e)}", styles['Normal']))
    
    story.append(Spacer(1, 30))
    
    # ===== RODAPÉ =====
    story.append(Paragraph("---", styles['Normal']))
    story.append(Paragraph("Relatório gerado pelo Sistema de Gestão de Riscos CGE-MT", styles['Normal']))
    story.append(Paragraph(f"Versão: {datetime.now().strftime('%Y.%m.%d')} | Relatório Completo", styles['Normal']))
    
    # Construir PDF
    doc.build(story)
    buffer.seek(0)
    
    return buffer

def gerar_recomendacoes_inteligentes(maturidade_kpas, avaliacoes_andamento, classificacao, evolucao_temporal):
    """Gera recomendações inteligentes baseadas nos dados do relatório"""
    recomendacoes = []
    
    # 1. KPAs parcialmente implementados (ALTA PRIORIDADE)
    kpas_parciais = [k for k in maturidade_kpas if 0 < k['perc_institucionalizadas'] < 100]
    for kpa in kpas_parciais:
        faltantes = kpa['total_atividades'] - kpa['atividades_institucionalizadas']
        recomendacoes.append({
            'prioridade': 'alta',
            'titulo': f"Completar {kpa['kpa_codigo']} - {kpa['area_nome']}",
            'descricao': f"Faltam {faltantes} de {kpa['total_atividades']} atividades para institucionalização completa. Priorize a implementação das atividades pendentes para alcançar 100% de maturidade nesta área."
        })
    
    # 2. Avaliações em andamento com baixo progresso (MÉDIA PRIORIDADE)
    if avaliacoes_andamento:
        for avaliacao in avaliacoes_andamento:
            # Calcular progresso geral da avaliação (simplificado)
            titulo = avaliacao[1]
            nivel = avaliacao[2]
            
            recomendacoes.append({
                'prioridade': 'media',
                'titulo': f"Retomar avaliação \"{titulo}\"",
                'descricao': f"Avaliação do Nível {nivel} está em andamento. Recomenda-se definir cronograma para conclusão e designar responsáveis para cada KPA pendente."
            })
    
    # 3. Evolução temporal negativa (ALTA PRIORIDADE)
    if len(evolucao_temporal) >= 2:
        primeiro = evolucao_temporal[0]
        ultimo = evolucao_temporal[-1]
        crescimento = ultimo['maturidade_institucionalizada'] - primeiro['maturidade_institucionalizada']
        
        if crescimento < 0:
            recomendacoes.append({
                'prioridade': 'alta',
                'titulo': "Reverter tendência de declínio",
                'descricao': f"A maturidade apresentou declínio de {abs(crescimento)} pontos percentuais. Recomenda-se revisar os processos implementados e reforçar as práticas de gestão de riscos."
            })
    
    # 4. Próximo nível de maturidade (BAIXA PRIORIDADE)
    if classificacao and classificacao.get('status') == 'certificado':
        nivel_atual = classificacao.get('nivel_maturidade', 1)
        if nivel_atual < 5:
            proximo_nivel = nivel_atual + 1
            recomendacoes.append({
                'prioridade': 'baixa',
                'titulo': f"Preparar para Nível {proximo_nivel}",
                'descricao': f"Com o Nível {nivel_atual} certificado, considere iniciar a preparação para avaliação do Nível {proximo_nivel}. Estude os requisitos e planeje a implementação das novas práticas."
            })
    
    # 5. Melhores práticas gerais (BAIXA PRIORIDADE)
    if len(maturidade_kpas) > 0:
        kpas_completos = len([k for k in maturidade_kpas if k['perc_institucionalizadas'] == 100])
        total_kpas = len(maturidade_kpas)
        
        if kpas_completos == total_kpas:
            recomendacoes.append({
                'prioridade': 'baixa',
                'titulo': "Manter excelência operacional",
                'descricao': "Todos os KPAs avaliados estão com 100% de institucionalização. Mantenha as práticas implementadas e considere auditorias periódicas para garantir a continuidade."
            })
        elif kpas_completos > total_kpas * 0.7:
            recomendacoes.append({
                'prioridade': 'baixa',
                'titulo': "Consolidar boas práticas",
                'descricao': f"Boa performance com {kpas_completos} de {total_kpas} KPAs completos. Documente as práticas bem-sucedidas e replique para as áreas pendentes."
            })
    
    # 6. Recomendação de monitoramento (BAIXA PRIORIDADE)
    recomendacoes.append({
        'prioridade': 'baixa',
        'titulo': "Monitoramento contínuo",
        'descricao': "Estabeleça rotina de monitoramento mensal do progresso das avaliações e revisão trimestral da maturidade em gestão de riscos. Utilize este relatório como baseline para acompanhamento."
    })
    
    return recomendacoes

def obter_area_kpa_segura(kpa_codigo):
    """Retorna a área do KPA de forma segura"""
    areas = {
        '2.1': 'Governança de Riscos',
        '2.2': 'Identificação de Riscos',
        '2.3': 'Análise e Avaliação',
        '2.4': 'Tratamento de Riscos',
        '2.5': 'Monitoramento e Análise',
        '2.6': 'Integração Organizacional',
        '3.1': 'Governança Avançada',
        '3.2': 'Estratégia e Objetivos',
        '3.3': 'Implementação Avançada',
        '3.4': 'Avaliação e Melhoria',
        '3.5': 'Comunicação e Consulta',
        '3.6': 'Monitoramento Avançado',
        '4.1': 'Governança Estratégica',
        '4.2': 'Estratégia Integrada',
        '4.3': 'Implementação Otimizada',
        '4.4': 'Avaliação Contínua',
        '4.5': 'Comunicação Efetiva',
        '4.6': 'Monitoramento Estratégico',
        '5.1': 'Governança Excelente',
        '5.2': 'Estratégia Inovadora',
        '5.3': 'Implementação Excelente',
        '5.4': 'Melhoria Contínua',
        '5.5': 'Comunicação Integrada',
        '5.6': 'Monitoramento Inteligente'
    }
    return areas.get(kpa_codigo, 'Área não identificada')
    
    
#def gerar_pdf_relatorio_individual(dados_relatorio, dados_usuario):
#    """Gera PDF completo do relatório individual - VERSÃO ROBUSTA"""
#    
#    from reportlab.lib.pagesizes import A4
#    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
#    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
#    from reportlab.lib import colors
#    from reportlab.lib.units import inch
#    from io import BytesIO
#    from datetime import datetime
#    
#    buffer = BytesIO()
#    doc = SimpleDocTemplate(buffer, pagesize=A4, topMargin=0.5*inch, bottomMargin=0.5*inch)
#    
#    # Estilos
#    styles = getSampleStyleSheet()
#    
#    titulo_principal = ParagraphStyle(
#        'TituloPrincipal',
#        parent=styles['Title'],
#        fontSize=18,
#        spaceAfter=20,
#        textColor=colors.HexColor('#1f4e79'),
#        alignment=1
#    )
#    
#    titulo_secao = ParagraphStyle(
#        'TituloSecao',
#        parent=styles['Heading1'],
#        fontSize=14,
#        spaceAfter=12,
#        textColor=colors.HexColor('#2e75b6')
#    )
#    
#    story = []
#    
#    # ===== CABEÇALHO =====
#    story.append(Paragraph("RELATÓRIO DE MATURIDADE EM GESTÃO DE RISCOS", titulo_principal))
#    story.append(Paragraph(f"<b>Órgão:</b> {dados_usuario.get('orgao_nome', 'N/A')}", styles['Normal']))
#    story.append(Paragraph(f"<b>Sigla:</b> {dados_usuario.get('orgao_sigla', 'N/A')}", styles['Normal']))
#    story.append(Paragraph(f"<b>Data de Geração:</b> {datetime.now().strftime('%d/%m/%Y às %H:%M')}", styles['Normal']))
#    story.append(Spacer(1, 20))
#    
#    # ===== CERTIFICAÇÃO =====
#    story.append(Paragraph("1. CERTIFICAÇÃO DE MATURIDADE", titulo_secao))
#    
#    classificacao = dados_relatorio.get('classificacao_maturidade', {})
#    
#    if classificacao.get('status') == 'certificado':
#        story.append(Paragraph(f"🏆 <b>NÍVEL {classificacao.get('nivel_maturidade', 'N/A')} CERTIFICADO</b>", styles['Normal']))
#        story.append(Paragraph(f"<b>Status:</b> {classificacao.get('descricao', 'N/A')}", styles['Normal']))
#        data_cert = classificacao.get('data_certificacao', '')
#        if data_cert:
#            data_formatada = data_cert[:10] if len(data_cert) >= 10 else data_cert
#            story.append(Paragraph(f"<b>Data de Certificação:</b> {data_formatada}", styles['Normal']))
#    else:
#        story.append(Paragraph("⚠️ <b>NÍVEL INICIAL</b>", styles['Normal']))
#        story.append(Paragraph(f"<b>Status:</b> {classificacao.get('descricao', 'Critérios não atendidos')}", styles['Normal']))
#    
#    story.append(Spacer(1, 15))
#    
#    # ===== MATURIDADE POR KPA =====
#    story.append(Paragraph("2. MATURIDADE POR KPA", titulo_secao))
#    
#    maturidade_kpas = dados_relatorio.get('maturidade_por_kpa', [])
#    if maturidade_kpas:
#        dados_tabela = [['KPA', 'Área', 'Instituídas', 'Institucionalizadas']]
#        
#        for kpa in maturidade_kpas:
#            if kpa.get('kpa_codigo', '') != 'GERAL':
#                dados_tabela.append([
#                    str(kpa.get('kpa_codigo', 'N/A')),
#                    str(kpa.get('area_modelo', 'N/A'))[:30] + '...' if len(str(kpa.get('area_modelo', ''))) > 30 else str(kpa.get('area_modelo', 'N/A')),
#                    f"{kpa.get('percentual_instituido', 0):.0f}%",
#                    f"{kpa.get('percentual_institucionalizado', 0):.0f}%"
#                ])
#        
#        if len(dados_tabela) > 1:  # Se tem dados além do cabeçalho
#            tabela = Table(dados_tabela, colWidths=[0.8*inch, 2.5*inch, 1*inch, 1.2*inch])
#            tabela.setStyle(TableStyle([
#                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2e75b6')),
#                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
#                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
#                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
#                ('FONTSIZE', (0, 0), (-1, 0), 10),
#                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
#                ('GRID', (0, 0), (-1, -1), 1, colors.black),
#                ('FONTSIZE', (0, 1), (-1, -1), 9),
#            ]))
#            story.append(tabela)
#        else:
#            story.append(Paragraph("Nenhum dado de maturidade por KPA disponível.", styles['Normal']))
#    else:
#        story.append(Paragraph("Nenhum dado de maturidade por KPA disponível.", styles['Normal']))
#    
#    story.append(Spacer(1, 15))
#    
#    # ===== EVOLUÇÃO TEMPORAL =====
#    story.append(Paragraph("3. EVOLUÇÃO DA MATURIDADE", titulo_secao))
#    
#    evolucao = dados_relatorio.get('evolucao_temporal', [])
#    if evolucao:
#        story.append(Paragraph("<b>Histórico de Avaliações:</b>", styles['Normal']))
#        
#        for item in evolucao:
#            # Acesso seguro aos dados
#            nivel = item.get('nivel') or item.get('nivel_avaliacao') or 'N/A'
#            data = item.get('data') or item.get('data_avaliacao') or 'N/A'
#            if data != 'N/A' and len(str(data)) >= 10:
#                data = str(data)[:10]
#            maturidade = item.get('maturidade_media') or item.get('maturidade_geral') or 0
#            
#            story.append(Paragraph(f"• <b>Nível {nivel}</b> - {data} - Maturidade: {maturidade:.1f}%", styles['Normal']))
#    else:
#        story.append(Paragraph("Nenhuma avaliação finalizada encontrada.", styles['Normal']))
#    
#    story.append(Spacer(1, 15))
#    
#    # ===== DETALHAMENTO =====
#    story.append(Paragraph("4. RESUMO GERAL", titulo_secao))
#    
#    total_avaliacoes = len(dados_relatorio.get('avaliacoes', []))
#    story.append(Paragraph(f"• <b>Total de Avaliações:</b> {total_avaliacoes}", styles['Normal']))
#    
#    detalhamento = dados_relatorio.get('detalhamento_kpas', [])
#    finalizadas = [d for d in detalhamento if d.get('status_avaliacao') == 'finalizada']
#    em_andamento = [d for d in detalhamento if d.get('status_avaliacao') == 'em_andamento']
#    
#    story.append(Paragraph(f"• <b>KPAs Finalizados:</b> {len(finalizadas)}", styles['Normal']))
#    story.append(Paragraph(f"• <b>KPAs em Andamento:</b> {len(em_andamento)}", styles['Normal']))
#    
#    # ===== RECOMENDAÇÕES =====
#    story.append(Spacer(1, 15))
#    story.append(Paragraph("5. RECOMENDAÇÕES", titulo_secao))
#    
#    recomendacoes = dados_relatorio.get('recomendacoes', [])
#    if recomendacoes:
#        for i, rec in enumerate(recomendacoes[:5], 1):  # Máximo 5 recomendações
#            titulo = rec.get('titulo', 'Recomendação')
#            descricao = rec.get('descricao', 'Sem descrição')
#            story.append(Paragraph(f"<b>{i}. {titulo}</b>", styles['Normal']))
#            story.append(Paragraph(descricao, styles['Normal']))
#            story.append(Spacer(1, 8))
#    else:
#        story.append(Paragraph("Nenhuma recomendação específica no momento.", styles['Normal']))
#    
#    # ===== RODAPÉ =====
#    story.append(Spacer(1, 30))
#    story.append(Paragraph("---", styles['Normal']))
#    story.append(Paragraph("Relatório gerado automaticamente pelo Sistema CGE-MT", styles['Normal']))
#    story.append(Paragraph(f"Data: {datetime.now().strftime('%d/%m/%Y às %H:%M')}", styles['Normal']))
#    
#    # Construir PDF
#    doc.build(story)
#    buffer.seek(0)
#    
#    return buffer
    
    
@app.route('/api/relatorio-individual/exportar', methods=['POST'])
def exportar_relatorio_individual():
    """Exporta relatório individual em PDF - VERSÃO SIMPLES"""
    user_email = request.headers.get('X-User-Email', '')
    
    # Obter dados do usuário
    dados_usuario = obter_dados_usuario(user_email)
    if not dados_usuario:
        return jsonify({'success': False, 'message': 'Usuário não encontrado'}), 404
    
    try:
        # Dados básicos para o PDF
        dados_basicos = {
            'orgao_nome': dados_usuario.get('orgao_nome', 'N/A'),
            'orgao_sigla': dados_usuario.get('orgao_sigla', 'N/A'),
            'usuario_nome': dados_usuario.get('nome', 'N/A'),
            'usuario_email': user_email
        }
        
        # Gerar PDF simples
        pdf_buffer = gerar_pdf_simples(dados_basicos)
        
        from flask import Response
        from datetime import datetime
        
        return Response(
            pdf_buffer.getvalue(),
            mimetype='application/pdf',
            headers={
                'Content-Disposition': f'attachment; filename=relatorio_{dados_usuario.get("orgao_sigla", "orgao")}_{datetime.now().strftime("%Y%m%d_%H%M%S")}.pdf'
            }
        )
        
    except Exception as e:
        logger.error(f"Erro ao exportar relatório: {str(e)}")
        return jsonify({'success': False, 'message': f'Erro: {str(e)}'}), 500
    
# EXPORTAÇÃO COMPLETA DO RELATÓRIO INDIVIDUAL EM PDF
# ===================================================
#@app.route('/api/relatorio-individual/exportar', methods=['POST'])
#def exportar_relatorio_individual():
#    """Exporta relatório individual completo em PDF com TODOS os dados"""
#    
#    print("🔍 INÍCIO EXPORTAÇÃO PDF")
#    
#    user_email = request.headers.get('X-User-Email', '')
#    print(f"   User email: {user_email}")
#    
#    # Obter dados do usuário
#    dados_usuario = obter_dados_usuario(user_email)
#    print(f"   Dados usuário: {dados_usuario is not None}")
#    
#    
#    user_email = request.headers.get('X-User-Email', '')
#    
#    # Obter dados do usuário
#    dados_usuario = obter_dados_usuario(user_email)
#   if not dados_usuario:
#        return jsonify({'success': False, 'message': 'Usuário não encontrado'}), 404
#    
#    orgao_id = dados_usuario.get('orgao_id')
#    if not orgao_id:
#        return jsonify({'success': False, 'message': 'Usuário não vinculado a um órgão'}), 400
#    
#    conn = sqlite3.connect(DATABASE)
#    cursor = conn.cursor()
#    
#   try:
#        # ===== DADOS DO ÓRGÃO =====
#        cursor.execute('SELECT id, nome, sigla FROM orgaos WHERE id = ?', (orgao_id,))
#        orgao_data = cursor.fetchone()
#        
#        if not orgao_data:
#            return jsonify({'success': False, 'message': 'Órgão não encontrado'}), 404
#        
#        orgao = {
#            'id': orgao_data[0],
#            'nome': orgao_data[1],
#            'sigla': orgao_data[2]
#        }
#        
#        # ===== TODAS AS AVALIAÇÕES =====
#        cursor.execute('''
#            SELECT id, titulo, status, data_criacao, nivel_desejado
#            FROM avaliacoes 
#            WHERE orgao_id = ? 
#            ORDER BY data_criacao DESC
#        ''', (orgao_id,))
#        
#        avaliacoes = []
#        for row in cursor.fetchall():
#            avaliacoes.append({
#                'id': row[0],
#                'titulo': row[1],
#                'status': row[2],
#                'data_criacao': row[3],
#                'nivel_desejado': row[4]
#            })
#        
#        # ===== EVOLUÇÃO TEMPORAL =====
#        evolucao_temporal = []
#        for nivel in [2, 3, 4, 5]:
#            cursor.execute('''
#                SELECT a.id, a.data_criacao, a.titulo, a.nivel_desejado
#                FROM avaliacoes a
#                WHERE a.orgao_id = ? AND a.status = 'finalizada' AND a.nivel_desejado = ?
#                ORDER BY a.data_criacao DESC
#                LIMIT 1
#            ''', (orgao_id, nivel))
#            
#            resultado = cursor.fetchone()
#            if resultado:
#                avaliacao_id = resultado[0]
#                
#                # Calcular maturidade desta avaliação específica
#                cursor.execute('''
#                    SELECT 
#                        COUNT(*) as total,
#                        COUNT(CASE WHEN instituido = 1 THEN 1 END) as instituidas,
#                        COUNT(CASE WHEN institucionalizado = 1 THEN 1 END) as institucionalizadas
#                    FROM respostas
#                    WHERE avaliacao_id = ?
#                ''', (avaliacao_id,))
#                
#                resultado_respostas = cursor.fetchone()
#                if resultado_respostas and resultado_respostas[0] > 0:
#                    total = resultado_respostas[0]
#                    instituidas = resultado_respostas[1]
#                    institucionalizadas = resultado_respostas[2]
#                    
#                    # Maturidade baseada em institucionalização
#                    maturidade_geral = int((institucionalizadas / total) * 100)
#                    
#                    evolucao_temporal.append({
#                        'data': resultado[1],
#                        'titulo': resultado[2],
#                        'nivel': resultado[3],
#                        'maturidade_media': maturidade_geral,
#                        'total_atividades': total,
#                        'institucionalizadas': institucionalizadas
#                    })
#        
#        # ===== MATURIDADE POR KPA =====
#        maturidade_por_kpa = []
#        
#        # Para cada nível, buscar a avaliação mais recente finalizada
#        for nivel in [2, 3, 4, 5]:
#            cursor.execute('''
#                SELECT a.id, a.titulo, a.data_criacao
#                FROM avaliacoes a
#                WHERE a.orgao_id = ? AND a.status = 'finalizada' AND a.nivel_desejado = ?
#                ORDER BY a.data_criacao DESC
#                LIMIT 1
#            ''', (orgao_id, nivel))
#            
#            resultado = cursor.fetchone()
#            if resultado:
#                avaliacao_id = resultado[0]
#                
#                # Agrupar respostas por KPA
#                cursor.execute('''
#                    SELECT atividade_id, instituido, institucionalizado
#                    FROM respostas
#                    WHERE avaliacao_id = ?
#                ''', (avaliacao_id,))
#               
#                kpas_nivel = {}
#                for row in cursor.fetchall():
#                    atividade_id = row[0]
#                    kpa_codigo = '.'.join(atividade_id.split('.')[:2])
#                    
#                    if kpa_codigo not in kpas_nivel:
#                        kpas_nivel[kpa_codigo] = {
#                            'total': 0,
#                            'instituidas': 0,
#                            'institucionalizadas': 0
#                        }
#                    
#                    kpas_nivel[kpa_codigo]['total'] += 1
#                    if row[1]:
#                        kpas_nivel[kpa_codigo]['instituidas'] += 1
#                    if row[2]:
#                        kpas_nivel[kpa_codigo]['institucionalizadas'] += 1
#                
#                # Adicionar à maturidade por KPA
#                for kpa_codigo, dados in kpas_nivel.items():
#                    perc_instituidas = int((dados['instituidas'] / dados['total']) * 100) if dados['total'] > 0 else 0
#                    perc_institucionalizadas = int((dados['institucionalizadas'] / dados['total']) * 100) if dados['total'] > 0 else 0
#                    
#                    maturidade_por_kpa.append({
#                        'kpa_codigo': kpa_codigo,
#                        'area_modelo': obter_area_kpa(kpa_codigo),
#                        'nivel': nivel,
#                        'percentual_instituido': perc_instituidas,
#                        'percentual_institucionalizado': perc_institucionalizadas,
#                        'total_atividades': dados['total'],
#                        'data_avaliacao': resultado[2]
#                    })
#        
#        # ===== DETALHAMENTO POR KPA =====
#        detalhamento_kpas = []
#        
#        # Avaliações finalizadas
#        for nivel in [2, 3, 4, 5]:
#            cursor.execute('''
#                SELECT a.id, a.titulo, a.data_criacao
#                FROM avaliacoes a
#                WHERE a.orgao_id = ? AND a.status = 'finalizada' AND a.nivel_desejado = ?
#                ORDER BY a.data_criacao DESC
#                LIMIT 1
#            ''', (orgao_id, nivel))
#            
#            resultado = cursor.fetchone()
#            if resultado:
#                avaliacao_id = resultado[0]
#                
#                # Agrupar por KPA
#                cursor.execute('''
#                    SELECT atividade_id, instituido, institucionalizado
#                    FROM respostas
#                    WHERE avaliacao_id = ?
#                ''', (avaliacao_id,))
#                
#                kpas_nivel = {}
#                for row in cursor.fetchall():
#                    atividade_id = row[0]
#                    kpa_codigo = '.'.join(atividade_id.split('.')[:2])
#                    
#                    if kpa_codigo not in kpas_nivel:
#                        kpas_nivel[kpa_codigo] = {
#                            'total': 0,
#                            'instituidas': 0,
#                            'institucionalizadas': 0
#                        }
#                    
#                    kpas_nivel[kpa_codigo]['total'] += 1
#                    if row[1]:
#                        kpas_nivel[kpa_codigo]['instituidas'] += 1
#                    if row[2]:
#                        kpas_nivel[kpa_codigo]['institucionalizadas'] += 1
#                
#                # Adicionar ao detalhamento
#                for kpa_codigo, dados in kpas_nivel.items():
#                    todas_institucionalizadas = dados['institucionalizadas'] == dados['total']
#                    todas_instituidas = dados['instituidas'] == dados['total']
#                    
#                    if todas_institucionalizadas:
#                        status = 'Institucionalizado'
#                        cor_status = 'success'
#                    elif todas_instituidas:
#                        status = 'Instituído'
#                        cor_status = 'warning'
#                    else:
#                        status = 'Parcial'
#                        cor_status = 'danger'
#                    
#                    detalhamento_kpas.append({
#                        'kpa_codigo': kpa_codigo,
#                        'area_modelo': obter_area_kpa(kpa_codigo),
#                        'nivel_avaliacao': nivel,
#                        'status_avaliacao': 'finalizada',
#                        'titulo_avaliacao': resultado[1],
#                        'data_avaliacao': resultado[2],
#                        'total_atividades': dados['total'],
#                        'instituidas': dados['instituidas'],
#                        'institucionalizadas': dados['institucionalizadas'],
#                        'status': status,
#                        'cor_status': cor_status
#                    })
#        
#        # Avaliações em andamento
#        for nivel in [2, 3, 4, 5]:
#            cursor.execute('''
#                SELECT a.id, a.titulo, a.data_criacao
#                FROM avaliacoes a
#                WHERE a.orgao_id = ? AND a.status = 'em_andamento' AND a.nivel_desejado = ?
#                ORDER BY a.data_criacao DESC
#                LIMIT 1
#            ''', (orgao_id, nivel))
#            
#            resultado = cursor.fetchone()
#            if resultado:
#                avaliacao_id = resultado[0]
#                
#                # Calcular preenchimento
#                total_atividades_nivel = obter_total_atividades_nivel(nivel)
#                
#                cursor.execute('''
#                    SELECT COUNT(*) FROM respostas WHERE avaliacao_id = ?
#                ''', (avaliacao_id,))
#                
#                atividades_preenchidas = cursor.fetchone()[0]
#                percentual_preenchimento = int((atividades_preenchidas / total_atividades_nivel) * 100) if total_atividades_nivel > 0 else 0
#                
#                # Agrupar por KPA para em andamento
#                cursor.execute('''
#                    SELECT atividade_id FROM respostas WHERE avaliacao_id = ?
#                ''', (avaliacao_id,))
#                
#                kpas_preenchidos = set()
#                for row in cursor.fetchall():
#                    atividade_id = row[0]
#                    kpa_codigo = '.'.join(atividade_id.split('.')[:2])
#                    kpas_preenchidos.add(kpa_codigo)
#                
#                for kpa_codigo in kpas_preenchidos:
#                    detalhamento_kpas.append({
#                        'kpa_codigo': kpa_codigo,
#                        'area_modelo': obter_area_kpa(kpa_codigo),
#                        'nivel_avaliacao': nivel,
#                        'status_avaliacao': 'em_andamento',
#                        'titulo_avaliacao': resultado[1],
#                        'data_avaliacao': resultado[2],
#                        'percentual_preenchimento': percentual_preenchimento,
#                        'kpa_preenchido': True
#                    })
#        
#        # ===== RECOMENDAÇÕES =====
#        recomendacoes = gerar_recomendacoes_corrigidas(detalhamento_kpas)
#        
#        # ===== CLASSIFICAÇÃO DE MATURIDADE =====
#        classificacao_maturidade = calcular_nivel_maturidade_orgao(orgao_id)
#        dados_selo = gerar_dados_selo_maturidade(
#            classificacao_maturidade['nivel_maturidade'],
#            classificacao_maturidade['status']
#        )
#        
#        # ===== DADOS COMPLETOS DO RELATÓRIO =====
#        dados_relatorio = {
#            'orgao': orgao,
#            'avaliacoes': avaliacoes,
#            'classificacao_maturidade': classificacao_maturidade,
#            'selo_maturidade': dados_selo,
#            'maturidade_por_kpa': maturidade_por_kpa,
#            'evolucao_temporal': evolucao_temporal,
#            'detalhamento_kpas': detalhamento_kpas,
#            'recomendacoes': recomendacoes
#        }
#        
#        conn.close()
#        
#        # ===== GERAR PDF =====
#        pdf_buffer = gerar_pdf_relatorio_individual(dados_relatorio, dados_usuario)
#        
#        from flask import Response
#        from datetime import datetime
#        
#        return Response(
#            pdf_buffer.getvalue(),
#            mimetype='application/pdf',
#            headers={
#                'Content-Disposition': f'attachment; filename=relatorio_maturidade_{dados_usuario.get("orgao_sigla", "orgao")}_{datetime.now().strftime("%Y%m%d_%H%M%S")}.pdf'
#            }
#        )
#        
#    except Exception as e:
#        conn.close()
#        logger.error(f"Erro ao exportar relatório individual: {str(e)}")
#        return jsonify({'success': False, 'message': 'Erro interno do servidor'}), 500
        
@app.route('/api/admin/relatorios/exportar', methods=['POST'])
def exportar_relatorio():
    """Exporta relatórios em diferentes formatos"""
    user_email = request.headers.get('X-User-Email', '')
    
    if not verificar_permissao(user_email, 'visualizar_relatorios_gerais'):
        return jsonify({'success': False, 'message': 'Sem permissão para exportar relatórios'}), 403
    
    data = request.get_json()
    formato = data.get('formato', 'pdf')
    
    try:
        # Buscar dados para o relatório
        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()
        
        # Dados consolidados
        cursor.execute('SELECT COUNT(*) FROM avaliacoes')
        total_avaliacoes = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*) FROM avaliacoes WHERE status = "finalizada"')
        avaliacoes_finalizadas = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(DISTINCT orgao_id) FROM avaliacoes')
        orgaos_participantes = cursor.fetchone()[0]
        
        # Dados por órgão
        cursor.execute('''
            SELECT 
                o.nome as orgao_nome,
                o.sigla as orgao_sigla,
                COUNT(a.id) as total_avaliacoes,
                COUNT(CASE WHEN a.status = 'finalizada' THEN 1 END) as finalizadas,
                COUNT(CASE WHEN a.status = 'em_andamento' THEN 1 END) as em_andamento
            FROM orgaos o
            LEFT JOIN avaliacoes a ON o.id = a.orgao_id
            GROUP BY o.id, o.nome, o.sigla
            ORDER BY o.nome
        ''')
        
        dados_orgaos = cursor.fetchall()
        conn.close()
        
        if formato == 'pdf':
            return gerar_pdf_relatorio(total_avaliacoes, avaliacoes_finalizadas, orgaos_participantes, dados_orgaos)
        elif formato == 'xlsx':
            return gerar_excel_relatorio(total_avaliacoes, avaliacoes_finalizadas, orgaos_participantes, dados_orgaos)
        elif formato == 'csv':
            return gerar_csv_relatorio(dados_orgaos)
        else:
            return jsonify({'success': False, 'message': 'Formato não suportado'}), 400
            
    except Exception as e:
        logger.error(f"Erro ao exportar relatório: {str(e)}")
        return jsonify({'success': False, 'message': f'Erro interno: {str(e)}'}), 500
        
        
def gerar_pdf_relatorio(total_avaliacoes, avaliacoes_finalizadas, orgaos_participantes, dados_orgaos):
    """Gera relatório consolidado em PDF - VERSÃO CORRIGIDA"""
    from reportlab.lib.pagesizes import letter, A4
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import inch
    from reportlab.lib import colors
    from reportlab.lib.enums import TA_CENTER, TA_LEFT
    from io import BytesIO
    from datetime import datetime
    
    # Criar buffer em memória
    buffer = BytesIO()
    
    # Criar documento com margens adequadas
    doc = SimpleDocTemplate(
        buffer, 
        pagesize=A4, 
        rightMargin=50, 
        leftMargin=50, 
        topMargin=50, 
        bottomMargin=50
    )
    
    # Estilos personalizados
    styles = getSampleStyleSheet()
    
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=20,
        spaceAfter=30,
        alignment=TA_CENTER,
        textColor=colors.darkblue
    )
    
    subtitle_style = ParagraphStyle(
        'CustomSubtitle',
        parent=styles['Heading2'],
        fontSize=14,
        spaceAfter=15,
        spaceBefore=20,
        textColor=colors.darkblue
    )
    
    # Conteúdo do documento
    story = []
    
    # Cabeçalho
    story.append(Paragraph("RELATÓRIO CONSOLIDADO", title_style))
    story.append(Paragraph("Sistema de Avaliação de Maturidade CGE-MT", styles['Heading3']))
    story.append(Spacer(1, 10))
    story.append(Paragraph(f"Gerado em: {datetime.now().strftime('%d/%m/%Y às %H:%M')}", styles['Normal']))
    story.append(Spacer(1, 30))
    
    # ===== ESTATÍSTICAS GERAIS =====
    story.append(Paragraph("1. ESTATÍSTICAS GERAIS", subtitle_style))
    
    taxa_conclusao = (avaliacoes_finalizadas/total_avaliacoes*100) if total_avaliacoes > 0 else 0
    
    estatisticas_data = [
        ['Métrica', 'Valor'],
        ['Total de Avaliações', str(total_avaliacoes)],
        ['Avaliações Finalizadas', str(avaliacoes_finalizadas)],
        ['Avaliações em Andamento', str(total_avaliacoes - avaliacoes_finalizadas)],
        ['Órgãos Participantes', str(orgaos_participantes)],
        ['Taxa de Conclusão', f"{taxa_conclusao:.1f}%"]
    ]
    
    estatisticas_table = Table(estatisticas_data, colWidths=[3.5*inch, 2*inch])
    estatisticas_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.darkblue),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 12),
        ('FONTSIZE', (0, 1), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('TOPPADDING', (0, 1), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 1), (-1, -1), 8),
        ('BACKGROUND', (0, 1), (-1, -1), colors.lightgrey),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE')
    ]))
    
    story.append(estatisticas_table)
    story.append(Spacer(1, 30))
    
    # ===== AVALIAÇÕES POR ÓRGÃO =====
    story.append(Paragraph("2. AVALIAÇÕES POR ÓRGÃO", subtitle_style))
    
    if dados_orgaos:
        # Cabeçalho da tabela
        orgaos_data = [['Órgão', 'Sigla', 'Total', 'Finalizadas', 'Em Andamento', 'Taxa (%)']]
        
        for orgao in dados_orgaos:
            nome_orgao = str(orgao[0]) if orgao[0] else 'N/A'
            sigla_orgao = str(orgao[1]) if orgao[1] else '-'
            total = int(orgao[2]) if orgao[2] else 0
            finalizadas = int(orgao[3]) if orgao[3] else 0
            em_andamento = int(orgao[4]) if orgao[4] else 0
            
            # Calcular taxa de conclusão por órgão
            taxa_orgao = (finalizadas / total * 100) if total > 0 else 0
            
            # Quebrar nome longo em múltiplas linhas se necessário
            if len(nome_orgao) > 40:
                nome_orgao = nome_orgao[:37] + "..."
            
            orgaos_data.append([
                nome_orgao,
                sigla_orgao,
                str(total),
                str(finalizadas),
                str(em_andamento),
                f"{taxa_orgao:.1f}%"
            ])
        
        # Criar tabela com larguras ajustadas
        orgaos_table = Table(orgaos_data, colWidths=[2.8*inch, 0.8*inch, 0.6*inch, 0.8*inch, 1*inch, 0.8*inch])
        orgaos_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.darkblue),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('ALIGN', (0, 0), (0, -1), 'LEFT'),  # Nome do órgão alinhado à esquerda
            ('ALIGN', (1, 0), (-1, -1), 'CENTER'),  # Demais colunas centralizadas
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('FONTSIZE', (0, 1), (-1, -1), 9),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('TOPPADDING', (0, 1), (-1, -1), 6),
            ('BOTTOMPADDING', (0, 1), (-1, -1), 6),
            ('BACKGROUND', (0, 1), (-1, -1), colors.lightgrey),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            # Alternar cores das linhas
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.lightgrey, colors.white])
        ]))
        
        story.append(orgaos_table)
    else:
        story.append(Paragraph("Nenhum dado de órgão disponível.", styles['Normal']))
    
    story.append(Spacer(1, 30))
    
    # ===== RESUMO EXECUTIVO =====
    story.append(Paragraph("3. RESUMO EXECUTIVO", subtitle_style))
    
    # Análise automática dos dados
    if total_avaliacoes > 0:
        if taxa_conclusao >= 80:
            status_geral = "Excelente"
        elif taxa_conclusao >= 60:
            status_geral = "Bom"
        elif taxa_conclusao >= 40:
            status_geral = "Regular"
        else:
            status_geral = "Necessita Atenção"
        
        story.append(Paragraph(f"• <b>Status Geral do Sistema:</b> {status_geral}", styles['Normal']))
        story.append(Paragraph(f"• <b>Taxa de Conclusão:</b> {taxa_conclusao:.1f}% das avaliações foram finalizadas", styles['Normal']))
        story.append(Paragraph(f"• <b>Participação:</b> {orgaos_participantes} órgãos estão participando do processo de avaliação", styles['Normal']))
        
        # Identificar órgão com melhor desempenho
        if dados_orgaos:
            melhor_orgao = None
            melhor_taxa = 0
            
            for orgao in dados_orgaos:
                total_orgao = int(orgao[2]) if orgao[2] else 0
                finalizadas_orgao = int(orgao[3]) if orgao[3] else 0
                
                if total_orgao > 0:
                    taxa_orgao = (finalizadas_orgao / total_orgao * 100)
                    if taxa_orgao > melhor_taxa:
                        melhor_taxa = taxa_orgao
                        melhor_orgao = orgao[0]
            
            if melhor_orgao and melhor_taxa > 0:
                story.append(Paragraph(f"• <b>Melhor Desempenho:</b> {melhor_orgao} ({melhor_taxa:.1f}% de conclusão)", styles['Normal']))
    else:
        story.append(Paragraph("• Nenhuma avaliação foi iniciada no sistema.", styles['Normal']))
    
    # Rodapé
    story.append(Spacer(1, 50))
    story.append(Paragraph("---", styles['Normal']))
    story.append(Paragraph("Relatório gerado automaticamente pelo Sistema CGE-MT", styles['Normal']))
    story.append(Paragraph("Controladoria Geral do Estado de Mato Grosso", styles['Normal']))
    
    # Gerar PDF
    doc.build(story)
    
    # Preparar resposta
    buffer.seek(0)
    
    from flask import Response
    return Response(
        buffer.getvalue(),
        mimetype='application/pdf',
        headers={
            'Content-Disposition': f'attachment; filename=relatorio_consolidado_cge_mt_{datetime.now().strftime("%Y%m%d_%H%M%S")}.pdf'
        }
    )

def gerar_excel_relatorio(total_avaliacoes, avaliacoes_finalizadas, orgaos_participantes, dados_orgaos):
    """Gera relatório em Excel"""
    import pandas as pd
    from io import BytesIO
    from datetime import datetime
    
    # Criar buffer em memória
    buffer = BytesIO()
    
    # Criar workbook
    with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
        # Aba de estatísticas gerais
        estatisticas_df = pd.DataFrame({
            'Métrica': ['Total de Avaliações', 'Avaliações Finalizadas', 'Órgãos Participantes', 'Taxa de Conclusão'],
            'Valor': [
                total_avaliacoes,
                avaliacoes_finalizadas,
                orgaos_participantes,
                f"{(avaliacoes_finalizadas/total_avaliacoes*100):.1f}%" if total_avaliacoes > 0 else "0%"
            ]
        })
        estatisticas_df.to_excel(writer, sheet_name='Estatísticas Gerais', index=False)
        
        # Aba de dados por órgão
        if dados_orgaos:
            orgaos_df = pd.DataFrame(dados_orgaos, columns=[
                'Órgão', 'Sigla', 'Total Avaliações', 'Finalizadas', 'Em Andamento'
            ])
            orgaos_df.to_excel(writer, sheet_name='Dados por Órgão', index=False)
        
        # Aba de informações
        info_df = pd.DataFrame({
            'Informação': ['Data de Geração', 'Sistema', 'Versão'],
            'Valor': [datetime.now().strftime('%d/%m/%Y %H:%M:%S'), 'Sistema CGE-MT', '4.2']
        })
        info_df.to_excel(writer, sheet_name='Informações', index=False)
    
    # Preparar resposta
    buffer.seek(0)
    
    from flask import Response
    return Response(
        buffer.getvalue(),
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        headers={
            'Content-Disposition': f'attachment; filename=relatorio_cge_mt_{datetime.now().strftime("%Y%m%d_%H%M%S")}.xlsx'
        }
    )

def gerar_csv_relatorio(dados_orgaos):
    """Gera relatório em CSV"""
    import pandas as pd
    from io import StringIO
    from datetime import datetime
    
    if dados_orgaos:
        # Criar DataFrame
        df = pd.DataFrame(dados_orgaos, columns=[
            'Órgão', 'Sigla', 'Total Avaliações', 'Finalizadas', 'Em Andamento'
        ])
        
        # Converter para CSV
        csv_buffer = StringIO()
        df.to_csv(csv_buffer, index=False, encoding='utf-8-sig')
        csv_content = csv_buffer.getvalue()
    else:
        csv_content = "Órgão,Sigla,Total Avaliações,Finalizadas,Em Andamento\n"
    
    from flask import Response
    return Response(
        csv_content,
        mimetype='text/csv',
        headers={
            'Content-Disposition': f'attachment; filename=relatorio_cge_mt_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
        }
    )

@app.route('/api/dashboard')
def dashboard():
    """Dados do dashboard"""
    user_email = request.headers.get('X-User-Email', '')
    
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    
    # Contar avaliações por status
    cursor.execute('''
        SELECT status, COUNT(*) 
        FROM avaliacoes 
        WHERE usuario_email = ?
        GROUP BY status
    ''', (user_email,))
    
    stats = {'em_andamento': 0, 'finalizada': 0, 'rascunho': 0}
    for row in cursor.fetchall():
        stats[row[0]] = row[1]
    
    # Avaliações recentes
    cursor.execute('''
        SELECT a.id, a.titulo, a.nivel_desejado, a.status, a.data_criacao,
               o.nome as orgao_nome
        FROM avaliacoes a
        LEFT JOIN orgaos o ON a.orgao_id = o.id
        WHERE a.usuario_email = ?
        ORDER BY a.data_criacao DESC
        LIMIT 5
    ''', (user_email,))
    
    avaliacoes_recentes = []
    for row in cursor.fetchall():
        avaliacoes_recentes.append({
            'id': row[0],
            'titulo': row[1],
            'nivel_desejado': row[2],
            'status': row[3],
            'data_criacao': row[4],
            'orgao_nome': row[5]
        })
    
    conn.close()
    
    return jsonify({
        'stats': stats,
        'avaliacoes_recentes': avaliacoes_recentes,
        'total_avaliacoes': sum(stats.values())
    })
    
    
def atualizar_permissoes_admin():
    """Atualiza permissões do administrador com novas permissões"""
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    
    # Buscar perfil Administrador CGE
    cursor.execute('SELECT id FROM perfis WHERE nome = ?', ('Administrador CGE',))
    result = cursor.fetchone()
    
    if result:
        perfil_id = result[0]
        
        # Novas permissões completas
        novas_permissoes = json.dumps({
            'gerenciar_usuarios': True,
            'gerenciar_orgaos': True,
            'gerar_relatorios': True,
            'visualizar_relatorios_gerais': True,
            'visualizar_todas_avaliacoes': True,
            'criar_avaliacoes': True,
            'editar_avaliacoes': True,
            'finalizar_avaliacoes': True,                
            'exportar_dados': True
        })
        
        # Atualizar permissões
        cursor.execute('UPDATE perfis SET permissoes = ? WHERE id = ?', (novas_permissoes, perfil_id))
        conn.commit()
        print(f"✅ Permissões do Administrador CGE atualizadas")
        
def corrigir_vinculacao_admin():
    """Corrige vinculação do usuário admin ao órgão CGE"""
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    
    # Buscar ID do órgão CGE
    cursor.execute('SELECT id FROM orgaos WHERE sigla = ? OR nome LIKE ?', ('CGE', '%Controladoria%'))
    result = cursor.fetchone()
    
    if result:
        orgao_cge_id = result[0]
        print(f"✅ Órgão CGE encontrado com ID: {orgao_cge_id}")
        
        # Atualizar usuário admin
        cursor.execute('''
            UPDATE usuarios 
            SET orgao_id = ? 
            WHERE email = ?
        ''', (orgao_cge_id, 'joelciocaires@cge.mt.gov.br'))
        
        # Verificar se atualizou
        if cursor.rowcount > 0:
            conn.commit()
            print(f"✅ Usuário joelciocaires@cge.mt.gov.br vinculado ao órgão CGE")
        else:
            print(f"❌ Usuário joelciocaires@cge.mt.gov.br não encontrado")
    else:
        print(f"❌ Órgão CGE não encontrado")
    
    conn.close()

if __name__ == '__main__':
    logger.info("🚀 Iniciando Sistema de Autoavaliação CGE-MT v4.3...")
    
    # Inicializar banco de dados
    init_db()
    #atualizar_permissoes_admin()
    corrigir_vinculacao_admin()

    logger.info("✅ Tabelas do banco de dados criadas")
    logger.info("👥 Sistema de gestão de usuários habilitado")
    
    logger.info("✅ Sistema inicializado com sucesso")
    logger.info("📊 Backend disponível em: http://localhost:5000")
    logger.info("🎯 Todos os endpoints disponíveis")
    logger.info("✅ CORS configurado para desenvolvimento")
    logger.info("📁 Upload de arquivos habilitado")
    logger.info("👤 Usuário admin padrão: admin@cge.mt.gov.br / admin123")
    
    # Executar aplicação
    app.run(host='0.0.0.0', port=5000, debug=True)