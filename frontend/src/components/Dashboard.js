import React, { useState, useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import NovaAvaliacaoModal from './NovaAvaliacaoModal';

const Dashboard = () => {
  const navigate = useNavigate();
  const { user, logout } = useAuth();
  const [stats, setStats] = useState({});
  const [avaliacoes, setAvaliacoes] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showModal, setShowModal] = useState(false);

  useEffect(() => {
    if (!user) {
      navigate('/login');
      return;
    }
    carregarDados();
  }, [user, navigate]);

  const carregarDados = useCallback(async () => {
    try {
      console.log('🔄 Carregando dados do dashboard...');
      
      const apiUrl = `http://${window.location.hostname}:5000/api/dashboard`;
	  const response = await fetch(apiUrl, {
        headers: {
          'X-User-Email': user?.email || ''
        }
      });

      if (response.ok) {
        const data = await response.json();
        setStats(data.stats || {});
        setAvaliacoes(data.avaliacoes_recentes || []);
        console.log('✅ Dados carregados:', data);
      } else {
        console.error('❌ Erro na resposta:', response.status);
      }
    } catch (error) {
      console.error('❌ Erro ao carregar dados:', error);
    } finally {
      setLoading(false);
    }
  }, [user]);

  const getStatusBadge = (status) => {
    const badges = {
      'em_andamento': 'bg-warning text-dark',
      'finalizada': 'bg-success',
      'rascunho': 'bg-secondary'
    };
    
    const labels = {
      'em_andamento': 'Em Andamento',
      'finalizada': 'Finalizada',
      'rascunho': 'Rascunho'
    };

    return (
      <span className={`badge ${badges[status] || 'bg-secondary'}`}>
        {labels[status] || status}
      </span>
    );
  };

  const abrirAvaliacao = (avaliacaoId) => {
    navigate(`/avaliacao/${avaliacaoId}`);
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

      <div className="container">
        {/* Estatísticas */}
        <div className="row mb-4">
          <div className="col-md-3">
            <div className="card bg-primary text-white">
              <div className="card-body">
                <div className="d-flex justify-content-between">
                  <div>
                    <h4>{stats.em_andamento || 0}</h4>
                    <p className="mb-0">Em Andamento</p>
                  </div>
                  <div className="align-self-center">
                    <i className="bi bi-clock-history fs-1"></i>
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
                    <h4>{stats.finalizada || 0}</h4>
                    <p className="mb-0">Finalizadas</p>
                  </div>
                  <div className="align-self-center">
                    <i className="bi bi-check-circle fs-1"></i>
                  </div>
                </div>
              </div>
            </div>
          </div>
          <div className="col-md-3">
            <div className="card bg-secondary text-white">
              <div className="card-body">
                <div className="d-flex justify-content-between">
                  <div>
                    <h4>{stats.rascunho || 0}</h4>
                    <p className="mb-0">Rascunhos</p>
                  </div>
                  <div className="align-self-center">
                    <i className="bi bi-file-earmark fs-1"></i>
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
                    <h4>{(stats.em_andamento || 0) + (stats.finalizada || 0) + (stats.rascunho || 0)}</h4>
                    <p className="mb-0">Total</p>
                  </div>
                  <div className="align-self-center">
                    <i className="bi bi-graph-up fs-1"></i>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* 🆕 SEÇÃO DE ADMINISTRAÇÃO - NOVA */}
        {user?.permissoes?.gerenciar_usuarios && (
          <div className="card mb-4 border-danger">
            <div className="card-header bg-danger text-white">
              <h5 className="mb-0">
                <i className="bi bi-shield-lock me-2"></i>
                Área Administrativa
              </h5>
            </div>
            <div className="card-body">
              <div className="row">
                <div className="col-md-4 mb-3">
                  <div className="card h-100 border-primary">
                    <div className="card-body text-center">
                      <i className="bi bi-people-fill fs-1 text-primary mb-3"></i>
                      <h6 className="card-title">Gestão de Usuários</h6>
                      <p className="card-text text-muted">
                        Criar, editar e gerenciar usuários do sistema
                      </p>
                      <button 
                        className="btn btn-primary"
                        onClick={() => navigate('/admin/usuarios')}
                      >
                        <i className="bi bi-person-gear me-1"></i>
                        Gerenciar Usuários
                      </button>
                    </div>
                  </div>
                </div>
                
                <div className="col-md-4 mb-3">
                  <div className="card h-100 border-info">
                    <div className="card-body text-center">
                      <i className="bi bi-building fs-1 text-info mb-3"></i>
                      <h6 className="card-title">Gestão de Órgãos</h6>
                      <p className="card-text text-muted">
                        Cadastrar e gerenciar órgãos do estado
                      </p>
                      <button 
                        className="btn btn-info"
                        onClick={() => navigate('/admin/orgaos')}
                      >
                        <i className="bi bi-building-gear me-1"></i>
                        Gerenciar Órgãos
                      </button>					  
                    </div>
                  </div>
                </div>

                <div className="col-md-4 mb-3">
                  <div className="card h-100 border-success">
                    <div className="card-body text-center">
                      <i className="bi bi-graph-up-arrow fs-1 text-success mb-3"></i>
                      <h6 className="card-title">Relatórios Gerais</h6>
                      <p className="card-text text-muted">
                        Visualizar relatórios de todos os órgãos
                      </p>
                      <button 
                        className="btn btn-success"
                        onClick={() => navigate('/admin/relatorios')}
                      >
                        <i className="bi bi-graph-up me-1"></i>
                        Ver Relatórios
                      </button>
                    </div>
                  </div>
                </div>
              </div>

              <div className="alert alert-info mt-3">
                <i className="bi bi-info-circle me-2"></i>
                <strong>Área Restrita:</strong> Estas funcionalidades estão disponíveis apenas para administradores do sistema.
              </div>
            </div>
          </div>
        )}

        {/* Ações Principais */}
        <div className="card mb-4">
          <div className="card-header">
            <div className="row align-items-center">
              <div className="col">
                <h5 className="mb-0">
                  <i className="bi bi-plus-circle me-2"></i>
                  Ações Rápidas
                </h5>
              </div>
            </div>
          </div>
          <div className="card-body">
            <div className="row">
              <div className="col-md-4 mb-3">
                <div className="card h-100">
                  <div className="card-body text-center">
                    <i className="bi bi-file-plus fs-1 text-primary mb-3"></i>
                    <h6 className="card-title">Nova Avaliação</h6>
                    <p className="card-text">Iniciar uma nova avaliação de gestão de riscos</p>
                    <button 
                      className="btn btn-primary"
                      onClick={() => setShowModal(true)}
                    >
                      <i className="bi bi-plus me-1"></i>
                      Criar Avaliação
                    </button>
                  </div>
                </div>
              </div>
              
              <div className="col-md-4 mb-3">
                <div className="card h-100">
                  <div className="card-body text-center">
                    <i className="bi bi-list-check fs-1 text-success mb-3"></i>
                    <h6 className="card-title">Minhas Avaliações</h6>
                    <p className="card-text">Visualizar e continuar avaliações existentes</p>
                    <button 
                      className="btn btn-outline-primary"
                      onClick={() => {
						  // Rolar para a seção de avaliações recentes
						  const avaliacoesSection = document.getElementById('avaliacoes-recentes');
						  if (avaliacoesSection) {
							avaliacoesSection.scrollIntoView({ behavior: 'smooth' });
						  }
					}}
                    >
                      <i className="bi bi-eye me-1"></i>
                      Ver Avaliações
                    </button>
                  </div>
                </div>
              </div>

              <div className="col-md-4 mb-3">
                <div className="card h-100">
                  <div className="card-body text-center">
                    <i className="bi bi-graph-up fs-1 text-info mb-3"></i>
                    <h6 className="card-title">Relatórios</h6>
                    <p className="card-text">Gerar relatórios e análises das avaliações</p>
                    <button 
                      className="btn btn-outline-success"
					  onClick={() => navigate('/relatorio-individual')}
                    >
                      <i className="bi bi-graph-up me-1"></i>
                      Ver Relatórios
                    </button>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Avaliações Recentes */}
        <div className="card mb-4" id="avaliacoes-recentes">
          <div className="card-header">
            <h5 className="mb-0">
              <i className="bi bi-clock-history me-2"></i>
              Avaliações Recentes
            </h5>
          </div>
          <div className="card-body">
            {avaliacoes.length === 0 ? (
              <div className="text-center py-4">
                <i className="bi bi-clipboard-x fs-1 text-muted"></i>
                <p className="text-muted mt-2">Nenhuma avaliação encontrada</p>
                <button 
                  className="btn btn-primary"
                  onClick={() => setShowModal(true)}
                >
                  <i className="bi bi-plus me-1"></i>
                  Criar Primeira Avaliação
                </button>
              </div>
            ) : (
              <div className="table-responsive">
                <table className="table table-hover">
                  <thead className="table-light">
                    <tr>
                      <th>Título</th>
                      <th>Órgão</th>
                      <th>Nível</th>
                      <th>Status</th>
                      <th>Data de Criação</th>
                      <th>Ações</th>
                    </tr>
                  </thead>
                  <tbody>
                    {avaliacoes.map(avaliacao => (
                      <tr key={avaliacao.id}>
                        <td>
                          <strong>{avaliacao.titulo}</strong>
                        </td>
                        <td>
                          <small className="text-muted">{avaliacao.orgao_nome}</small>
                        </td>
                        <td>
                          <span className="badge bg-primary">Nível {avaliacao.nivel_desejado}</span>
                        </td>
                        <td>
                          {getStatusBadge(avaliacao.status)}
                        </td>
                        <td>
                          <small className="text-muted">
                            {new Date(avaliacao.data_criacao).toLocaleDateString('pt-BR')}
                          </small>
                        </td>
                        <td>
                          <button 
                            className="btn btn-sm btn-outline-primary"
                            onClick={() => abrirAvaliacao(avaliacao.id)}
                          >
                            <i className="bi bi-eye me-1"></i>
                            Abrir
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

        {/* Informações do Sistema */}
        <div className="card mb-4">
          <div className="card-header">
            <h6 className="mb-0">
              <i className="bi bi-info-circle me-2"></i>
              Informações do Sistema
            </h6>
          </div>
          <div className="card-body">
            <div className="row">
              <div className="col-md-6">
                <p><strong>Usuário:</strong> {user?.nome || user?.email}</p>
                <p><strong>Perfil:</strong> {user?.perfil || 'Usuário'}</p>
              </div>
              <div className="col-md-6">
                <p><strong>Órgão:</strong> {user?.orgao_nome || 'Não definido'}</p>
                <p><strong>Versão:</strong> PRISMA v. 1.0</p>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Modal Nova Avaliação */}
	  {showModal && (
		<NovaAvaliacaoModal 
			show={showModal}
			onClose={() => setShowModal(false)}
			onSuccess={() => {
				setShowModal(false);
				carregarDados();
			}}
		/>
	  )}
    </div>
  );
};

export default Dashboard;
