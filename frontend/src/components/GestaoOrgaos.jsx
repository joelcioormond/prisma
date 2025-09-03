import React, { useState, useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';

const GestaoOrgaos = () => {
  const navigate = useNavigate();
  const { user } = useAuth();
  const [orgaos, setOrgaos] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showModal, setShowModal] = useState(false);
  const [editandoOrgao, setEditandoOrgao] = useState(null);
  const [formData, setFormData] = useState({
	nome: '',
	sigla: '',
	orgao_superior_id: ''
  });

  const carregarOrgaos = useCallback(async () => {
    try {
      console.log('🔄 Carregando órgãos...');

      const apiUrl = `http://${window.location.hostname}:5000/api/orgaos`;
      const response = await fetch(apiUrl );
      if (response.ok) {
        const data = await response.json();
        setOrgaos(data);
        console.log('✅ Órgãos carregados:', data.length);
      }
    } catch (error) {
      console.error('❌ Erro ao carregar órgãos:', error);
      alert('Erro ao carregar órgãos');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    if (!user) {
      navigate('/login');
      return;
    }

    // Verificar se usuário tem permissão
    if (!user.permissoes?.gerenciar_orgaos) {
      alert('Você não tem permissão para acessar esta área');
      navigate('/dashboard');
      return;
    }

    carregarOrgaos();
  }, [user, navigate]);

  const abrirModal = (orgao = null) => {
    if (orgao) {
      setEditandoOrgao(orgao);
      setFormData({
		nome: orgao.nome,
		sigla: orgao.sigla || '',
		orgao_superior_id: orgao.orgao_superior_id || ''
		});
    } else {
      setEditandoOrgao(null);
      setFormData({
		nome: '',
		sigla: '',
		orgao_superior_id: ''
	  });
    }
    setShowModal(true);
  };

  const fecharModal = () => {
    setShowModal(false);
    setEditandoOrgao(null);
    setFormData({
      nome: '',
      sigla: ''
    });
  };

  const salvarOrgao = async (e) => {
    e.preventDefault();

    try {
      const url = editandoOrgao 
        ? `http://${window.location.hostname}:5000/api/orgaos/${editandoOrgao.id}`
        : `http://${window.location.hostname}:5000/api/orgaos`;
      
      const method = editandoOrgao ? 'PUT' : 'POST';

      const response = await fetch(url, {
        method: method,
        headers: {
          'Content-Type': 'application/json',
          'X-User-Email': user?.email || ''
        },
        body: JSON.stringify(formData )
      });

      const data = await response.json();

      if (data.success) {
        alert(editandoOrgao ? 'Órgão atualizado com sucesso!' : 'Órgão criado com sucesso!');
        fecharModal();
        carregarOrgaos();
      } else {
        alert('Erro: ' + data.message);
      }
    } catch (error) {
      console.error('Erro ao salvar órgão:', error);
      alert('Erro de conexão');
    }
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
      <nav className="navbar navbar-expand-lg navbar-dark bg-info mb-4">
        <div className="container">
          <span className="navbar-brand">
            <i className="bi bi-building-fill me-2"></i>
            Gestão de Órgãos
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
          <div className="col-md-4">
            <div className="card bg-info text-white">
              <div className="card-body">
                <div className="d-flex justify-content-between">
                  <div>
                    <h4>{orgaos.length}</h4>
                    <p className="mb-0">Total de Órgãos</p>
                  </div>
                  <div className="align-self-center">
                    <i className="bi bi-building fs-1"></i>
                  </div>
                </div>
              </div>
            </div>
          </div>
          <div className="col-md-4">
            <div className="card bg-success text-white">
              <div className="card-body">
                <div className="d-flex justify-content-between">
                  <div>
                    <h4>{orgaos.filter(o => o.sigla).length}</h4>
                    <p className="mb-0">Com Sigla</p>
                  </div>
                  <div className="align-self-center">
                    <i className="bi bi-check-circle fs-1"></i>
                  </div>
                </div>
              </div>
            </div>
          </div>
          <div className="col-md-4">
            <div className="card bg-warning text-white">
              <div className="card-body">
                <div className="d-flex justify-content-between">
                  <div>
                    <h4>{orgaos.filter(o => !o.sigla).length}</h4>
                    <p className="mb-0">Sem Sigla</p>
                  </div>
                  <div className="align-self-center">
                    <i className="bi bi-exclamation-triangle fs-1"></i>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Lista de Órgãos */}
        <div className="card mb-4">
          <div className="card-header">
            <div className="row align-items-center">
              <div className="col">
                <h5 className="mb-0">
                  <i className="bi bi-list-ul me-2"></i>
                  Lista de Órgãos
                </h5>
              </div>
              <div className="col-auto">
                <button 
                  className="btn btn-primary"
                  onClick={() => abrirModal()}
                >
                  <i className="bi bi-plus-circle me-1"></i>
                  Novo Órgão
                </button>
              </div>
            </div>
          </div>
          <div className="card-body">
            {orgaos.length === 0 ? (
              <div className="text-center py-4">
                <i className="bi bi-building fs-1 text-muted"></i>
                <p className="text-muted mt-2">Nenhum órgão cadastrado</p>
              </div>
            ) : (
              <div className="table-responsive">
                <table className="table table-hover">
                  <thead className="table-dark">
                    <tr>
                      <th>Nome do Órgão</th>
                      <th>Sigla</th>
					  <th>Órgão Superior</th>
                      <th>Data de Criação</th>
                      <th>Ações</th>
                    </tr>
                  </thead>
                  <tbody>
                    {orgaos.map(orgao => (
                      <tr key={orgao.id}>
                        <td>
                          <div className="d-flex align-items-center">
                            <div className="avatar-sm bg-info rounded-circle d-flex align-items-center justify-content-center me-2">
                              <i className="bi bi-building text-white"></i>
                            </div>
                            <strong>{orgao.nome}</strong>
                          </div>
                        </td>
                        <td>
                          {orgao.sigla ? (
                            <span className="badge bg-primary">{orgao.sigla}</span>
                          ) : (
                            <span className="text-muted">Não definida</span>
                          )}
                        </td>
						<td>
							{orgao.orgao_superior_nome ? (
								<div>
									<small className="text-primary">
										{orgao.orgao_superior_nome}
										{orgao.orgao_superior_sigla && ` (${orgao.orgao_superior_sigla})`}
									</small>
								</div>
							) : (
								<span className="badge bg-success">Órgão Principal</span>
							)}
						</td>
                        <td>
                          <small className="text-muted">
                            {orgao.data_criacao 
                              ? new Date(orgao.data_criacao).toLocaleDateString('pt-BR')
                              : 'Não informado'
                            }
                          </small>
                        </td>
                        <td>
                          <button 
                            className="btn btn-sm btn-outline-primary"
                            onClick={() => abrirModal(orgao)}
                            title="Editar"
                          >
                            <i className="bi bi-pencil"></i>
                          </button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Modal de Órgão */}
      {showModal && (
        <div className="modal show d-block" tabIndex="-1" style={{backgroundColor: 'rgba(0,0,0,0.5)'}}>
          <div className="modal-dialog">
            <div className="modal-content">
              <div className="modal-header">
                <h5 className="modal-title">
                  <i className="bi bi-building-add me-2"></i>
                  {editandoOrgao ? 'Editar Órgão' : 'Novo Órgão'}
                </h5>
                <button type="button" className="btn-close" onClick={fecharModal}></button>
              </div>
              <form onSubmit={salvarOrgao}>
                <div className="modal-body">
                  <div className="mb-3">
                    <label className="form-label">Nome do Órgão *</label>
                    <input
                      type="text"
                      className="form-control"
                      value={formData.nome}
                      onChange={(e) => setFormData({...formData, nome: e.target.value})}
                      placeholder="Ex: Secretaria de Estado de Saúde"
                      required
                    />
                  </div>
				  <div className="mb-3">
					<label className="form-label">Órgão Superior</label>
					<select
						 className="form-select"
						 value={formData.orgao_superior_id}
						 onChange={(e) => setFormData({...formData, orgao_superior_id: e.target.value})}
					>
						<option value="">Nenhum (Órgão Principal)</option>
						{orgaos
							 .filter(o => !editandoOrgao || o.id !== editandoOrgao.id) // Não pode ser superior de si mesmo
							 .map(orgao => (
								<option key={orgao.id} value={orgao.id}>
									{orgao.nome} {orgao.sigla && `(${orgao.sigla})`}
								</option>
						))}
					</select>
					<small className="text-muted">
						Selecione o órgão ao qual este órgão está subordinado
					</small>
				  </div>

                  <div className="mb-3">
                    <label className="form-label">Sigla</label>
                    <input
                      type="text"
                      className="form-control"
                      value={formData.sigla}
                      onChange={(e) => setFormData({...formData, sigla: e.target.value.toUpperCase()})}
                      placeholder="Ex: SES"
                      maxLength="10"
                    />
                    <small className="text-muted">
                      Sigla do órgão (opcional, máximo 10 caracteres)
                    </small>
                  </div>

                  <div className="alert alert-info">
                    <i className="bi bi-info-circle me-2"></i>
                    <strong>Informação:</strong> O órgão ficará disponível para seleção 
                    durante a criação de avaliações e cadastro de usuários.
                  </div>
                </div>
                <div className="modal-footer">
                  <button type="button" className="btn btn-secondary" onClick={fecharModal}>
                    Cancelar
                  </button>
                  <button type="submit" className="btn btn-primary">
                    <i className="bi bi-save me-1"></i>
                    {editandoOrgao ? 'Atualizar' : 'Criar'} Órgão
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

export default GestaoOrgaos;