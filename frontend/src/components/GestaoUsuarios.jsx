import React, { useState, useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';

const GestaoUsuarios = () => {
  const navigate = useNavigate();
  const { user } = useAuth();
  const [usuarios, setUsuarios] = useState([]);
  const [perfis, setPerfis] = useState([]);
  const [orgaos, setOrgaos] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showModal, setShowModal] = useState(false);
  const [editandoUsuario, setEditandoUsuario] = useState(null);
  const [formData, setFormData] = useState({
    email: '',
    nome: '',
    perfil_id: '',
    orgao_id: '',
    senha: '',
    ativo: true
  });

  const carregarDados = useCallback(async () => {
    try {
      console.log('🔄 Carregando dados de gestão...');

      // Carregar usuários
	  
      const apiUrl = `http://${window.location.hostname}:5000/api/usuarios`;
	  const usuariosResponse = await fetch(apiUrl, {
        headers: {
          'X-User-Email': user?.email || ''
        }
      });

      if (usuariosResponse.ok) {
        const usuariosData = await usuariosResponse.json();
        // Verificar se a resposta tem a estrutura {success: true, usuarios: [...]}
        const usuarios = usuariosData.usuarios || usuariosData;
        setUsuarios(Array.isArray(usuarios) ? usuarios : []);
        console.log('✅ Usuários carregados:', usuarios.length);
      }

      // Carregar perfis
      const perfisApiUrl = `http://${window.location.hostname}:5000/api/perfis`;
	  const perfisResponse = await fetch(perfisApiUrl );
      if (perfisResponse.ok) {
        const perfisData = await perfisResponse.json();
        const perfis = perfisData.perfis || perfisData;
        setPerfis(Array.isArray(perfis) ? perfis : []);
        console.log('✅ Perfis carregados:', perfis.length);
      }

      // Carregar órgãos
      const orgaosApiUrl = `http://${window.location.hostname}:5000/api/orgaos`;
	  const orgaosResponse = await fetch(orgaosApiUrl );
      if (orgaosResponse.ok) {
        const orgaosData = await orgaosResponse.json();
        const orgaos = orgaosData.orgaos || orgaosData;
        setOrgaos(Array.isArray(orgaos) ? orgaos : []);
        console.log('✅ Órgãos carregados:', orgaos.length);
      }

    } catch (error) {
      console.error('❌ Erro ao carregar dados:', error);
      alert('Erro ao carregar dados');
    } finally {
      setLoading(false);
    }
  }, [user]);
  
useEffect(() => {
    if (!user) {
      navigate('/login');
      return;
    }

    // Verificar se usuário tem permissão
    if (!user.permissoes?.gerenciar_usuarios) {
      alert('Você não tem permissão para acessar esta área');
      navigate('/dashboard');
      return;
    }

    carregarDados();
  }, [user, navigate]);

  const abrirModal = (usuario = null) => {
    if (usuario) {
      setEditandoUsuario(usuario);
      setFormData({
        email: usuario.email,
        nome: usuario.nome,
        perfil_id: perfis.find(p => p.nome === usuario.perfil)?.id || '',
        orgao_id: orgaos.find(o => o.nome === usuario.orgao_nome)?.id || '',
        senha: '',
        ativo: usuario.ativo
      });
    } else {
      setEditandoUsuario(null);
      setFormData({
        email: '',
        nome: '',
        perfil_id: '',
        orgao_id: '',
        senha: '',
        ativo: true
      });
    }
    setShowModal(true);
  };

  const fecharModal = () => {
    setShowModal(false);
    setEditandoUsuario(null);
    setFormData({
      email: '',
      nome: '',
      perfil_id: '',
      orgao_id: '',
      senha: '',
      ativo: true
    });
  };

  const salvarUsuario = async (e) => {
    e.preventDefault();

    try {
      const url = editandoUsuario 
        ? `http://${window.location.hostname}:5000/api/usuarios/${editandoUsuario.id}`
        : `http://${window.location.hostname}:5000/api/usuarios`;
      
      const method = editandoUsuario ? 'PUT' : 'POST';

      const response = await fetch(url, {
        method: method,
        headers: {
          'Content-Type': 'application/json',
          'X-User-Email': user?.email || ''
        },
        body: JSON.stringify(formData)
      });

      const data = await response.json();

      if (data.success) {
        alert(editandoUsuario ? 'Usuário atualizado com sucesso!' : 'Usuário criado com sucesso!');
        fecharModal();
        carregarDados();
      } else {
        alert('Erro: ' + data.message);
      }
    } catch (error) {
      console.error('Erro ao salvar usuário:', error);
      alert('Erro de conexão');
    }
  };

  const desativarUsuario = async (usuarioId, nomeUsuario) => {
    if (!window.confirm(`Tem certeza que deseja desativar o usuário "${nomeUsuario}"?`)) {
      return;
    }

    try {
      const apiUrl = `http://${window.location.hostname}:5000/api/usuarios/`;
	  const response = await fetch(apiUrl + `${usuarioId}`, {
        method: 'DELETE',
        headers: {
          'X-User-Email': user?.email || ''
        }
      });

      const data = await response.json();

      if (data.success) {
        alert('Usuário desativado com sucesso!');
        carregarDados();
      } else {
        alert('Erro: ' + data.message);
      }
    } catch (error) {
      console.error('Erro ao desativar usuário:', error);
      alert('Erro de conexão');
    }
  };

  const getStatusBadge = (ativo) => {
    return ativo 
      ? <span className="badge bg-success">Ativo</span>
      : <span className="badge bg-danger">Inativo</span>;
  };

  const getPerfilBadge = (perfil) => {
    const cores = {
      'Administrador CGE': 'bg-danger',
      'Avaliador do Órgão': 'bg-primary',
      'Consultor Externo': 'bg-info',
      'Visualizador': 'bg-secondary'
    };
    
    return <span className={`badge ${cores[perfil] || 'bg-secondary'}`}>{perfil}</span>;
  };

  if (loading) {
    return (
      <div className="d-flex justify-content-center align-items-center vh-100">
        <div className="spinner-border text-primary" role="status">
          <span className="visually-hidden">Carregando...</span>
        </div>
      </div>
    );
  }

  return (
    <div className="container-fluid">
      {/* Header */}
      <nav className="navbar navbar-expand-lg navbar-dark bg-danger mb-4">
        <div className="container">
          <span className="navbar-brand">
            <i className="bi bi-people-fill me-2"></i>
            Gestão de Usuários - CGE-MT
          </span>
          <div className="navbar-nav ms-auto">
            <button 
              className="btn btn-outline-light btn-sm"
              onClick={() => navigate('/dashboard')}
            >
              <i className="bi bi-arrow-left me-1"></i>
              Voltar ao Dashboard
            </button>
          </div>
        </div>
      </nav>

      <div className="container">
        {/* Estatísticas */}
        <div className="row mb-4">
          <div className="col-md-3">
            <div className="card bg-primary text-white">
              <div className="card-body">
                <div className="d-flex justify-content-between">
                  <div>
                    <h4>{usuarios.length}</h4>
                    <p className="mb-0">Total de Usuários</p>
                  </div>
                  <div className="align-self-center">
                    <i className="bi bi-people fs-1"></i>
                  </div>
                </div>
              </div>
            </div>
          </div>
          <div className="col-md-3">
            <div className="card bg-success text-white">
              <div className="card-body">
                <div className="d-flex justify-content-between">
                  <div>
                    <h4>{usuarios.filter(u => u.ativo).length}</h4>
                    <p className="mb-0">Usuários Ativos</p>
                  </div>
                  <div className="align-self-center">
                    <i className="bi bi-person-check fs-1"></i>
                  </div>
                </div>
              </div>
            </div>
          </div>
          <div className="col-md-3">
            <div className="card bg-info text-white">
              <div className="card-body">
                <div className="d-flex justify-content-between">
                  <div>
                    <h4>{perfis.length}</h4>
                    <p className="mb-0">Perfis Disponíveis</p>
                  </div>
                  <div className="align-self-center">
                    <i className="bi bi-shield-check fs-1"></i>
                  </div>
                </div>
              </div>
            </div>
          </div>
          <div className="col-md-3">
            <div className="card bg-warning text-white">
              <div className="card-body">
                <div className="d-flex justify-content-between">
                  <div>
                    <h4>{orgaos.length}</h4>
                    <p className="mb-0">Órgãos Cadastrados</p>
                  </div>
                  <div className="align-self-center">
                    <i className="bi bi-building fs-1"></i>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Ações */}
        <div className="card mb-4">
          <div className="card-header">
            <div className="row align-items-center">
              <div className="col">
                <h5 className="mb-0">
                  <i className="bi bi-list-ul me-2"></i>
                  Lista de Usuários
                </h5>
              </div>
              <div className="col-auto">
                <button 
                  className="btn btn-primary"
                  onClick={() => abrirModal()}
                >
                  <i className="bi bi-plus-circle me-1"></i>
                  Novo Usuário
                </button>
              </div>
            </div>
          </div>
          <div className="card-body">
            {usuarios.length === 0 ? (
              <div className="text-center py-4">
                <i className="bi bi-people fs-1 text-muted"></i>
                <p className="text-muted mt-2">Nenhum usuário cadastrado</p>
              </div>
            ) : (
              <div className="table-responsive">
                <table className="table table-hover">
                  <thead className="table-dark">
                    <tr>
                      <th>Nome</th>
                      <th>Email</th>
                      <th>Perfil</th>
                      <th>Órgão</th>
                      <th>Status</th>
                      <th>Último Acesso</th>
                      <th>Ações</th>
                    </tr>
                  </thead>
                  <tbody>
                    {usuarios.map(usuario => (
                      <tr key={usuario.id}>
                        <td>
                          <div className="d-flex align-items-center">
                            <div className="avatar-sm bg-primary rounded-circle d-flex align-items-center justify-content-center me-2">
                              <i className="bi bi-person text-white"></i>
                            </div>
                            <strong>{usuario.nome}</strong>
                          </div>
                        </td>
                        <td>{usuario.email}</td>
                        <td>{getPerfilBadge(usuario.perfil)}</td>
                        <td>
                          <small className="text-muted">
                            {usuario.orgao_nome || 'Não definido'}
                            {usuario.orgao_sigla && ` (${usuario.orgao_sigla})`}
                          </small>
                        </td>
                        <td>{getStatusBadge(usuario.ativo)}</td>
                        <td>
                          <small className="text-muted">
                            {usuario.ultimo_acesso 
                              ? new Date(usuario.ultimo_acesso).toLocaleDateString('pt-BR')
                              : 'Nunca'
                            }
                          </small>
                        </td>
                        <td>
                          <div className="btn-group btn-group-sm">
                            <button 
                              className="btn btn-outline-primary"
                              onClick={() => abrirModal(usuario)}
                              title="Editar"
                            >
                              <i className="bi bi-pencil"></i>
                            </button>
                            {usuario.ativo && (
                              <button 
                                className="btn btn-outline-danger"
                                onClick={() => desativarUsuario(usuario.id, usuario.nome)}
                                title="Desativar"
                              >
                                <i className="bi bi-person-x"></i>
                              </button>
                            )}
                          </div>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        </div>

        {/* Resumo por Perfil */}
        <div className="card mb-4">
          <div className="card-header">
            <h6 className="mb-0">
              <i className="bi bi-pie-chart me-2"></i>
              Distribuição por Perfil
            </h6>
          </div>
          <div className="card-body">
            <div className="row">
              {perfis.map(perfil => {
                const usuariosPerfil = usuarios.filter(u => u.perfil === perfil.nome);
                const usuariosAtivos = usuariosPerfil.filter(u => u.ativo);
                
                return (
                  <div key={perfil.id} className="col-md-6 col-lg-3 mb-3">
                    <div className="card h-100">
                      <div className="card-body text-center">
                        <h5 className="card-title">{perfil.nome}</h5>
                        <h3 className="text-primary">{usuariosPerfil.length}</h3>
                        <p className="text-muted mb-0">
                          {usuariosAtivos.length} ativos
                        </p>
                        <small className="text-muted">{perfil.descricao}</small>
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        </div>
      </div>

      {/* Modal de Usuário */}
      {showModal && (
        <div className="modal show d-block" tabIndex="-1" style={{backgroundColor: 'rgba(0,0,0,0.5)'}}>
          <div className="modal-dialog modal-lg">
            <div className="modal-content">
              <div className="modal-header">
                <h5 className="modal-title">
                  <i className="bi bi-person-plus me-2"></i>
                  {editandoUsuario ? 'Editar Usuário' : 'Novo Usuário'}
                </h5>
                <button type="button" className="btn-close" onClick={fecharModal}></button>
              </div>
              <form onSubmit={salvarUsuario}>
                <div className="modal-body">
                  <div className="row">
                    <div className="col-md-6 mb-3">
                      <label className="form-label">Email *</label>
                      <input
                        type="email"
                        className="form-control"
                        value={formData.email}
                        onChange={(e) => setFormData({...formData, email: e.target.value})}
                        required
                        disabled={editandoUsuario}
                      />
                      <small className="text-muted">Deve ser do domínio @cge.mt.gov.br</small>
                    </div>
                    <div className="col-md-6 mb-3">
                      <label className="form-label">Nome Completo *</label>
                      <input
                        type="text"
                        className="form-control"
                        value={formData.nome}
                        onChange={(e) => setFormData({...formData, nome: e.target.value})}
                        required
                      />
                    </div>
                  </div>
                  
                  <div className="row">
                    <div className="col-md-6 mb-3">
                      <label className="form-label">Perfil *</label>
                      <select
                        className="form-select"
                        value={formData.perfil_id}
                        onChange={(e) => setFormData({...formData, perfil_id: e.target.value})}
                        required
                      >
                        <option value="">Selecione um perfil</option>
                        {perfis.map(perfil => (
                          <option key={perfil.id} value={perfil.id}>
                            {perfil.nome} - {perfil.descricao}
                          </option>
                        ))}
                      </select>
                    </div>
                    <div className="col-md-6 mb-3">
                      <label className="form-label">Órgão</label>
                      <select
                        className="form-select"
                        value={formData.orgao_id}
                        onChange={(e) => setFormData({...formData, orgao_id: e.target.value})}
                      >
                        <option value="">Selecione um órgão</option>
                        {orgaos.map(orgao => (
                          <option key={orgao.id} value={orgao.id}>
                            {orgao.nome} ({orgao.sigla})
                          </option>
                        ))}
                      </select>
                    </div>
                  </div>

                  <div className="row">
                    <div className="col-md-6 mb-3">
                      <label className="form-label">
                        {editandoUsuario ? 'Nova Senha (deixe vazio para manter)' : 'Senha *'}
                      </label>
                      <input
                        type="password"
                        className="form-control"
                        value={formData.senha}
                        onChange={(e) => setFormData({...formData, senha: e.target.value})}
                        required={!editandoUsuario}
                        minLength="6"
                      />
                      <small className="text-muted">Mínimo 6 caracteres</small>
                    </div>
                    <div className="col-md-6 mb-3">
                      <label className="form-label">Status</label>
                      <div className="form-check form-switch mt-2">
                        <input
                          className="form-check-input"
                          type="checkbox"
                          checked={formData.ativo}
                          onChange={(e) => setFormData({...formData, ativo: e.target.checked})}
                        />
                        <label className="form-check-label">
                          {formData.ativo ? 'Usuário Ativo' : 'Usuário Inativo'}
                        </label>
                      </div>
                    </div>
                  </div>
                </div>
                <div className="modal-footer">
                  <button type="button" className="btn btn-secondary" onClick={fecharModal}>
                    Cancelar
                  </button>
                  <button type="submit" className="btn btn-primary">
                    <i className="bi bi-save me-1"></i>
                    {editandoUsuario ? 'Atualizar' : 'Criar'} Usuário
                  </button>
                </div>
              </form>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default GestaoUsuarios;
