import React, { useState, useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import GraficosRelatorio from './GraficosRelatorio';

const RelatoriosAdmin = () => {
  const navigate = useNavigate();
  const { user } = useAuth();
  const [loading, setLoading] = useState(true);
  const [dados, setDados] = useState({
    estatisticas_gerais: {},
    avaliacoes_por_orgao: [],
    ranking_maturidade: [],
    evolucao_temporal: []
  });

  const carregarDados = useCallback(async () => {
    try {
      console.log('🔄 Carregando dados dos relatórios...');

      const apiUrl = `http://${window.location.hostname}:5000/api/admin/relatorios`;
      const response = await fetch(apiUrl, {
        headers: {
          'X-User-Email': user?.email || ''
        }
      } );

      if (response.ok) {
        const data = await response.json();
        setDados(data);
        console.log('✅ Dados dos relatórios carregados:', data);
      }
    } catch (error) {
      console.error('❌ Erro ao carregar relatórios:', error);
      alert('Erro ao carregar relatórios');
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
    if (!user.permissoes?.visualizar_relatorios_gerais) {
      alert('Você não tem permissão para acessar esta área');
      navigate('/dashboard');
      return;
    }

    carregarDados();
  }, [user, navigate]);

  const exportarRelatorio = async (formato) => {
    try {
      const apiUrl = `http://${window.location.hostname}:5000/api/admin/relatorios/exportar`;
      const response = await fetch(apiUrl, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-User-Email': user?.email || ''
        },
        body: JSON.stringify({ formato } )
      });

      if (response.ok) {
        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `relatorio_consolidado.${formato}`;
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
        document.body.removeChild(a);
      }
    } catch (error) {
      console.error('Erro ao exportar:', error);
      alert('Erro ao exportar relatório');
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
      <nav className="navbar navbar-expand-lg navbar-dark bg-success mb-4">
        <div className="container">
          <span className="navbar-brand d-flex align-items-center">
            <img 
              src="/logo.png" 
              alt="Brasão MT" 
              style={{width: '32px', height: '32px', objectFit: 'contain'}}
              className="me-2"
            />
            Relatórios Administrativos
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
        {/* Estatísticas Gerais */}
        <div className="row mb-4">
          <div className="col-md-3">
            <div className="card bg-primary text-white">
              <div className="card-body">
                <div className="d-flex justify-content-between">
                  <div>
                    <h4>{dados.estatisticas_gerais.total_avaliacoes || 0}</h4>
                    <p className="mb-0">Total de Avaliações</p>
                  </div>
                  <div className="align-self-center">
                    <i className="bi bi-clipboard-data fs-1"></i>
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
                    <h4>{dados.estatisticas_gerais.avaliacoes_finalizadas || 0}</h4>
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
            <div className="card bg-info text-white">
              <div className="card-body">
                <div className="d-flex justify-content-between">
                  <div>
                    <h4>{dados.estatisticas_gerais.orgaos_participantes || 0}</h4>
                    <p className="mb-0">Órgãos Participantes</p>
                  </div>
                  <div className="align-self-center">
                    <i className="bi bi-building fs-1"></i>
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
                    <h4>{dados.estatisticas_gerais.media_maturidade || 0}%</h4>
                    <p className="mb-0">Maturidade Média</p>
                  </div>
                  <div className="align-self-center">
                    <i className="bi bi-graph-up fs-1"></i>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Ações de Exportação */}
        <div className="card mb-4">
          <div className="card-header">
            <h5 className="mb-0">
              <i className="bi bi-download me-2"></i>
              Exportar Relatórios
            </h5>
          </div>
          <div className="card-body">
            <div className="row">
              <div className="col-md-4 mb-3">
                <div className="card h-100">
                  <div className="card-body text-center">
                    <i className="bi bi-file-earmark-pdf fs-1 text-danger mb-3"></i>
                    <h6 className="card-title">Relatório PDF</h6>
                    <p className="card-text">Relatório completo em formato PDF</p>
                    <button 
                      className="btn btn-danger"
                      onClick={() => exportarRelatorio('pdf')}
                    >
                      <i className="bi bi-download me-1"></i>
                      Baixar PDF
                    </button>
                  </div>
                </div>
              </div>
              
              <div className="col-md-4 mb-3">
                <div className="card h-100">
                  <div className="card-body text-center">
                    <i className="bi bi-file-earmark-excel fs-1 text-success mb-3"></i>
                    <h6 className="card-title">Planilha Excel</h6>
                    <p className="card-text">Dados detalhados em planilha Excel</p>
                    <button 
                      className="btn btn-success"
                      onClick={() => exportarRelatorio('xlsx')}
                    >
                      <i className="bi bi-download me-1"></i>
                      Baixar Excel
                    </button>
                  </div>
                </div>
              </div>

              <div className="col-md-4 mb-3">
                <div className="card h-100">
                  <div className="card-body text-center">
                    <i className="bi bi-file-earmark-text fs-1 text-info mb-3"></i>
                    <h6 className="card-title">Dados CSV</h6>
                    <p className="card-text">Dados brutos em formato CSV</p>
                    <button 
                      className="btn btn-info"
                      onClick={() => exportarRelatorio('csv')}
                    >
                      <i className="bi bi-download me-1"></i>
                      Baixar CSV
                    </button>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Ranking de Maturidade */}
        <div className="card mb-4">
          <div className="card-header">
            <h5 className="mb-0">
              <i className="bi bi-trophy me-2"></i>
              Ranking de Maturidade por Órgão
            </h5>
          </div>
          <div className="card-body">
            {dados.ranking_maturidade.length === 0 ? (
              <div className="text-center py-4">
                <i className="bi bi-graph-up fs-1 text-muted"></i>
                <p className="text-muted mt-2">Nenhum dado de maturidade disponível</p>
              </div>
            ) : (
              <div className="table-responsive">
                <table className="table table-hover">
                  <thead className="table-dark">
                    <tr>
                      <th>Posição</th>
                      <th>Órgão</th>
                      <th>Avaliações</th>
                      <th>Maturidade Média</th>
                      <th>Última Avaliação</th>
                      <th>Status</th>
                    </tr>
                  </thead>
                  <tbody>
                    {dados.ranking_maturidade.map((item, index) => (
                      <tr key={item.orgao_id}>
                        <td>
                          <div className="d-flex align-items-center">
                            {index === 0 && <i className="bi bi-trophy-fill text-warning me-2"></i>}
                            {index === 1 && <i className="bi bi-award-fill text-secondary me-2"></i>}
                            {index === 2 && <i className="bi bi-award text-warning me-2"></i>}
                            <strong>{index + 1}º</strong>
                          </div>
                        </td>
                        <td>
                          <div>
                            <strong>{item.orgao_nome}</strong>
                            {item.orgao_sigla && <small className="text-muted d-block">({item.orgao_sigla})</small>}
                          </div>
                        </td>
                        <td>
                          <span className="badge bg-primary">{item.total_avaliacoes}</span>
                        </td>
                        <td>
                          <div className="progress" style={{height: '20px'}}>
                            <div 
                              className="progress-bar bg-success" 
                              style={{width: `${item.maturidade_media}%`}}
                            >
                              {item.maturidade_media}%
                            </div>
                          </div>
                        </td>
                        <td>
                          <small className="text-muted">
                            {item.ultima_avaliacao 
                              ? new Date(item.ultima_avaliacao).toLocaleDateString('pt-BR')
                              : 'N/A'
                            }
                          </small>
                        </td>
                        <td>
                          <span className={`badge ${item.status === 'ativo' ? 'bg-success' : 'bg-secondary'}`}>
                            {item.status === 'ativo' ? 'Ativo' : 'Inativo'}
                          </span>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        </div>
		
		{/* Gráficos Interativos */}
		<div className="card mb-4">
			<div className="card-header">
				<h5 className="mb-0">
					<i className="bi bi-graph-up me-2"></i>
					Gráficos e Indicadores
				</h5>
			</div>
			<div className="card-body">
				<GraficosRelatorio dados={dados} />
			</div>
		</div>

        {/* Avaliações por Órgão */}
        <div className="card mb-4">
          <div className="card-header">
            <h5 className="mb-0">
              <i className="bi bi-building me-2"></i>
              Avaliações por Órgão
            </h5>
          </div>
          <div className="card-body">
            <div className="row">
              {dados.avaliacoes_por_orgao.map(orgao => (
                <div key={orgao.orgao_id} className="col-md-6 col-lg-4 mb-3">
                  <div className="card h-100">
                    <div className="card-body">
                      <h6 className="card-title">{orgao.orgao_nome}</h6>
                      {orgao.orgao_sigla && <small className="text-muted">({orgao.orgao_sigla})</small>}
                      
                      <div className="mt-3">
                        <div className="d-flex justify-content-between">
                          <small>Total:</small>
                          <strong>{orgao.total_avaliacoes}</strong>
                        </div>
                        <div className="d-flex justify-content-between">
                          <small>Finalizadas:</small>
                          <span className="text-success">{orgao.finalizadas}</span>
                        </div>
                        <div className="d-flex justify-content-between">
                          <small>Em Andamento:</small>
                          <span className="text-warning">{orgao.em_andamento}</span>
                        </div>
                        <div className="d-flex justify-content-between">
                          <small>Maturidade:</small>
                          <strong className="text-primary">{orgao.maturidade_media}%</strong>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default RelatoriosAdmin;