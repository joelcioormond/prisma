import React, { useState, useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  BarElement,
  Title,
  Tooltip,
  Legend,
  ArcElement,
  PointElement,
  LineElement,
  RadialLinearScale,
} from 'chart.js';
import { Radar, Line, Bar } from 'react-chartjs-2';

ChartJS.register(
  CategoryScale,
  LinearScale,
  BarElement,
  Title,
  Tooltip,
  Legend,
  ArcElement,
  PointElement,
  LineElement,
  RadialLinearScale
);

const RelatorioIndividual = () => {
  const navigate = useNavigate();
  const { user } = useAuth();
  const [loading, setLoading] = useState(true);
  const [dados, setDados] = useState({
    orgao: {},
    avaliacoes: [],
    maturidade_por_kpa: [],
    evolucao_temporal: [],
    detalhamento_kpas: [],
    recomendacoes: []
  });

  const carregarDados = useCallback(async () => {
    try {
      console.log('🔄 Carregando relatório individual...');

      const apiUrl = `http://${window.location.hostname}:5000/api/relatorio-individual`;
      const response = await fetch(apiUrl, {
        headers: {
          'X-User-Email': user?.email || ''
        }
      });

      if (response.ok) {
        const data = await response.json();
        setDados(data);
        console.log('✅ Relatório individual carregado:', data);
      }
    } catch (error) {
      console.error('❌ Erro ao carregar relatório:', error);
      alert('Erro ao carregar relatório individual');
    } finally {
      setLoading(false);
    }
  }, [user]);

  useEffect(() => {
    if (!user) {
      navigate('/login');
      return;
    }

    carregarDados();
  }, [user, navigate, carregarDados]);

  const exportarRelatorioIndividual = async () => {
    try {
      const apiUrl = `http://${window.location.hostname}:5000/api/relatorio-individual/exportar`;
      const response = await fetch(apiUrl, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-User-Email': user?.email || ''
        },
        body: JSON.stringify({ formato: 'pdf' })
      });

      if (response.ok) {
        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `relatorio_${dados.orgao.sigla || 'orgao'}_${new Date().toISOString().split('T')[0]}.pdf`;
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

  // 🆕 DADOS PARA GRÁFICO DE MATURIDADE POR KPA (BARRAS LADO A LADO)
  const dadosBarras = {
    labels: dados.maturidade_por_kpa.map(item => `KPA ${item.kpa_codigo}`),
    datasets: [
      {
        label: 'Instituídas (%)',
        data: dados.maturidade_por_kpa.map(item => item.percentual_instituidas),
        backgroundColor: 'rgba(255, 193, 7, 0.8)',
        borderColor: 'rgba(255, 193, 7, 1)',
        borderWidth: 1
      },
      {
        label: 'Institucionalizadas (%)',
        data: dados.maturidade_por_kpa.map(item => item.percentual_institucionalizadas),
        backgroundColor: 'rgba(40, 167, 69, 0.8)',
        borderColor: 'rgba(40, 167, 69, 1)',
        borderWidth: 1
      }
    ]
  };

  const opcoesBarras = {
    responsive: true,
    plugins: {
      title: {
        display: true,
        text: 'Maturidade por KPA - Instituídas vs Institucionalizadas',
        font: { size: 16 }
      },
      legend: {
        position: 'top',
      }
    },
    scales: {
      y: {
        beginAtZero: true,
        max: 100,
        ticks: {
          callback: function(value) {
            return value + '%';
          }
        }
      }
    }
  };

  // Dados para gráfico de evolução temporal (por níveis)
  const dadosEvolucao = {
    labels: dados.evolucao_temporal.map(item => `Nível ${item.nivel}`),
    datasets: [
      {
        label: 'Institucionalização (%)',
        data: dados.evolucao_temporal.map(item => item.maturidade_geral),
        borderColor: 'rgba(40, 167, 69, 1)',
        backgroundColor: 'rgba(40, 167, 69, 0.1)',
        borderWidth: 3,
        fill: true,
        tension: 0.4,
        pointBackgroundColor: 'rgba(40, 167, 69, 1)',
        pointBorderColor: '#fff',
        pointBorderWidth: 2,
        pointRadius: 6,
      }
    ]
  };

  const opcoesEvolucao = {
    responsive: true,
    plugins: {
      title: {
        display: true,
        text: 'Evolução da Maturidade por Níveis',
        font: { size: 16 }
      },
      legend: {
        position: 'top',
      }
    },
    scales: {
      y: {
        beginAtZero: true,
        max: 100,
        ticks: {
          callback: function(value) {
            return value + '%';
          }
        }
      }
    }
  };
  
// COMPONENTE SELO DE MATURIDADE
// ==============================

const SeloMaturidade = ({ dados }) => {
  if (!dados || !dados.mostrar_selo) {
    return (
      <div className="card border-secondary">
        <div className="card-body text-center py-4">
          <i className="bi bi-hourglass-split fs-1 text-muted mb-3"></i>
          <h6 className="text-muted">Nível Inicial</h6>
          <p className="text-muted small mb-0">Continue avaliando para obter certificação</p>
        </div>
      </div>
    );
  }

  const estiloSelo = {
    background: `linear-gradient(135deg, ${dados.cor_principal} 0%, ${dados.cor_secundaria} 100%)`,
    border: `3px solid ${dados.cor_secundaria}`,
    borderRadius: '15px',
    boxShadow: `0 8px 25px rgba(0,0,0,0.15), 0 0 0 1px ${dados.cor_secundaria}40`,
    position: 'relative',
    overflow: 'hidden'
  };

  const estiloIcone = {
    fontSize: '3rem',
    color: 'white',
    textShadow: '0 2px 4px rgba(0,0,0,0.3)',
    filter: 'drop-shadow(0 2px 4px rgba(0,0,0,0.2))'
  };

  return (
    <div className="card border-0" style={estiloSelo}>
      {/* Efeito de brilho */}
      <div 
        style={{
          position: 'absolute',
          top: '-50%',
          left: '-50%',
          width: '200%',
          height: '200%',
          background: 'linear-gradient(45deg, transparent 30%, rgba(255,255,255,0.1) 50%, transparent 70%)',
          transform: 'rotate(45deg)',
          pointerEvents: 'none'
        }}
      ></div>
      
      <div className="card-body text-center py-4 position-relative">
        {/* Ícone principal */}
        <div className="mb-3">
          <i className={`${dados.icone} ${estiloIcone}`} style={estiloIcone}></i>
        </div>
        
        {/* Título do nível */}
        <h4 className="text-white fw-bold mb-1" style={{textShadow: '0 2px 4px rgba(0,0,0,0.3)'}}>
          {dados.titulo}
        </h4>
        
        {/* Subtítulo */}
        <p className="text-white-50 small mb-3" style={{textShadow: '0 1px 2px rgba(0,0,0,0.3)'}}>
          {dados.subtitulo}
        </p>
        
        {/* Badge de certificação */}
        {dados.certificado && (
          <div className="d-flex justify-content-center">
            <span 
              className="badge px-3 py-2"
              style={{
                backgroundColor: 'rgba(255,255,255,0.2)',
                color: 'white',
                border: '1px solid rgba(255,255,255,0.3)',
                fontSize: '0.75rem',
                textShadow: '0 1px 2px rgba(0,0,0,0.3)'
              }}
            >
              <i className="bi bi-check-circle me-1"></i>
              CERTIFICADO
            </span>
          </div>
        )}
        
        {/* Estrelas decorativas para níveis altos */}
        {dados.nivel >= 4 && (
          <div className="position-absolute" style={{top: '10px', right: '10px'}}>
            <i className="bi bi-star-fill text-white-50" style={{fontSize: '0.8rem'}}></i>
          </div>
        )}
        {dados.nivel === 5 && (
          <div className="position-absolute" style={{top: '10px', left: '10px'}}>
            <i className="bi bi-star-fill text-white-50" style={{fontSize: '0.8rem'}}></i>
          </div>
        )}
      </div>
    </div>
  );
};

  // Agrupar detalhamento por tipo
  const detalhamentoFinalizado = dados.detalhamento_kpas.filter(item => item.tipo === 'finalizada');
  const detalhamentoAndamento = dados.detalhamento_kpas.filter(item => item.tipo === 'em_andamento');

  return (
    <div className="container-fluid">
      {/* Header */}
      <nav className="navbar navbar-expand-lg navbar-dark bg-info mb-4">
        <div className="container">
          <span className="navbar-brand d-flex align-items-center">
            Relatório Individual - {dados.orgao.nome}
          </span>
          <div className="navbar-nav ms-auto">
            <button 
              className="btn btn-outline-light btn-sm me-2"
              onClick={exportarRelatorioIndividual}
            >
              <i className="bi bi-download me-1"></i>
              Exportar PDF
            </button>
            <button 
              className="btn btn-outline-light btn-sm"
              onClick={() => navigate('/dashboard')}
            >
              <i className="bi bi-arrow-left me-1"></i>
              Voltar
            </button>
          </div>
        </div>
      </nav>

      <div className="container">
        {/* Informações do Órgão */}
        <div className="card mb-4">
          <div className="card-header bg-primary text-white">
            <h5 className="mb-0">
              <i className="bi bi-building me-2"></i>
              Informações do Órgão
            </h5>
          </div>
          <div className="card-body">
            <div className="row">
              <div className="col-md-6">
                <p><strong>Nome:</strong> {dados.orgao.nome}</p>
                <p><strong>Sigla:</strong> {dados.orgao.sigla || 'Não definida'}</p>
              </div>
              <div className="col-md-6">
                <p><strong>Total de Avaliações:</strong> {dados.avaliacoes.length}</p>
                <p><strong>Última Avaliação:</strong> {
                  dados.avaliacoes.length > 0 
                    ? new Date(dados.avaliacoes[0].data_criacao).toLocaleDateString('pt-BR')
                    : 'Nenhuma avaliação'
                }</p>
              </div>
            </div>
          </div>
        </div>
		
		{/* 🆕 SELO DE MATURIDADE */}
        {dados.selo_maturidade && (
          <div className="row mb-4">
            <div className="col-md-4 mx-auto">
              <div className="text-center mb-3">
                <h5 className="text-muted">
                  <i className="bi bi-award me-2"></i>
                  Nível de Maturidade Certificado
                </h5>
              </div>
              <SeloMaturidade dados={dados.selo_maturidade} />
              
              {/* Informações da classificação */}
              {dados.classificacao_maturidade && (
                <div className="card mt-3">
                  <div className="card-body">
                    <h6 className="card-title">
                      <i className="bi bi-info-circle me-2"></i>
                      Detalhes da Certificação
                    </h6>
                    <p className="card-text small">
                      <strong>Status:</strong> {dados.classificacao_maturidade.descricao}
                    </p>
                    {dados.classificacao_maturidade.data_certificacao && (
                      <p className="card-text small">
                        <strong>Data:</strong> {new Date(dados.classificacao_maturidade.data_certificacao).toLocaleDateString('pt-BR')}
                      </p>
                    )}
                    <div className="mt-2">
                      {dados.classificacao_maturidade.criterios_atendidos ? (
                        <span className="badge bg-success">
                          <i className="bi bi-check-circle me-1"></i>
                          Critérios Atendidos
                        </span>
                      ) : (
                        <span className="badge bg-warning">
                          <i className="bi bi-exclamation-triangle me-1"></i>
                          Critérios Pendentes
                        </span>
                      )}
                    </div>
                  </div>
                </div>
              )}
            </div>
          </div>
        )}

        {/* Gráficos */}
        <div className="row mb-4">
          {/* Gráfico de Barras - Maturidade por KPA */}
          <div className="col-md-6">
            <div className="card h-100">
              <div className="card-body">
                {dados.maturidade_por_kpa.length > 0 ? (
                  <Bar data={dadosBarras} options={opcoesBarras} />
                ) : (
                  <div className="text-center py-5">
                    <i className="bi bi-graph-up fs-1 text-muted"></i>
                    <p className="text-muted mt-2">Nenhum dado de maturidade disponível</p>
                  </div>
                )}
              </div>
            </div>
          </div>

          {/* Gráfico de Evolução por Níveis */}
          <div className="col-md-6">
            <div className="card h-100">
              <div className="card-body">
                {dados.evolucao_temporal.length > 0 ? (
                  <Line data={dadosEvolucao} options={opcoesEvolucao} />
                ) : (
                  <div className="text-center py-5">
                    <i className="bi bi-clock-history fs-1 text-muted"></i>
                    <p className="text-muted mt-2">Nenhuma avaliação finalizada para análise temporal</p>
                  </div>
                )}
              </div>
            </div>
          </div>
        </div>

        {/* 🆕 DETALHAMENTO POR KPA - AVALIAÇÕES FINALIZADAS */}
        {detalhamentoFinalizado.length > 0 && (
          <div className="card mb-4">
            <div className="card-header bg-success text-white">
              <h5 className="mb-0">
                <i className="bi bi-check-circle me-2"></i>
                Avaliações Finalizadas por Nível
              </h5>
            </div>
            <div className="card-body">
              <div className="table-responsive">
                <table className="table table-hover">
                  <thead className="table-dark">
                    <tr>
                      <th>Nível</th>
                      <th>KPA</th>
                      <th>Área</th>
                      <th>Atividades</th>
                      <th>Instituídas</th>
                      <th>Institucionalizadas</th>
                      <th>Status</th>
                      <th>Avaliação</th>
                    </tr>
                  </thead>
                  <tbody>
                    {detalhamentoFinalizado.map((item, index) => (
                      <tr key={index}>
                        <td><strong>Nível {item.nivel}</strong></td>
                        <td><strong>{item.kpa_codigo}</strong></td>
                        <td>{item.area_modelo}</td>
                        <td>
                          <span className="badge bg-info">{item.total_atividades}</span>
                        </td>
                        <td>
                          <span className="badge bg-warning">{item.instituidas}</span>
                        </td>
                        <td>
                          <span className="badge bg-success">{item.institucionalizadas}</span>
                        </td>
                        <td>
                          <span className={`badge bg-${item.cor_status}`}>
                            {item.status}
                          </span>
                        </td>
                        <td>
                          <small className="text-muted">
                            {item.titulo_avaliacao}<br/>
                            {new Date(item.data_avaliacao).toLocaleDateString('pt-BR')}
                          </small>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          </div>
        )}

        {/* 🆕 DETALHAMENTO POR KPA - AVALIAÇÕES EM ANDAMENTO */}
        {detalhamentoAndamento.length > 0 && (
          <div className="card mb-4">
            <div className="card-header bg-info text-white">
              <h5 className="mb-0">
                <i className="bi bi-clock me-2"></i>
                Avaliações em Andamento por Nível
              </h5>
            </div>
            <div className="card-body">
              <div className="table-responsive">
                <table className="table table-hover">
                  <thead className="table-dark">
                    <tr>
                      <th>Nível</th>
                      <th>KPA</th>
                      <th>Área</th>
                      <th>Preenchimento</th>
                      <th>KPA Iniciado</th>
                      <th>Status</th>
                      <th>Avaliação</th>
                    </tr>
                  </thead>
                  <tbody>
                    {detalhamentoAndamento.map((item, index) => (
                      <tr key={index}>
                        <td><strong>Nível {item.nivel}</strong></td>
                        <td><strong>{item.kpa_codigo}</strong></td>
                        <td>{item.area_modelo}</td>
                        <td>
                          <div className="progress" style={{height: '20px', minWidth: '100px'}}>
                            <div 
                              className="progress-bar bg-info"
                              style={{width: `${item.percentual_preenchimento}%`}}
                            >
                              {item.percentual_preenchimento}%
                            </div>
                          </div>
                        </td>
                        <td>
                          <span className={`badge ${item.kpa_preenchido ? 'bg-success' : 'bg-secondary'}`}>
                            {item.kpa_preenchido ? 'Sim' : 'Não'}
                          </span>
                        </td>
                        <td>
                          <span className={`badge bg-${item.cor_status}`}>
                            {item.status}
                          </span>
                        </td>
                        <td>
                          <small className="text-muted">
                            {item.titulo_avaliacao}<br/>
                            {new Date(item.data_avaliacao).toLocaleDateString('pt-BR')}
                          </small>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          </div>
        )}

        {/* Recomendações */}
        <div className="card mb-4">
          <div className="card-header bg-warning text-dark">
            <h5 className="mb-0">
              <i className="bi bi-lightbulb me-2"></i>
              Recomendações para Melhoria
            </h5>
          </div>
          <div className="card-body">
            {dados.recomendacoes.length > 0 ? (
              <div className="row">
                {dados.recomendacoes.map((recomendacao, index) => (
                  <div key={index} className="col-md-6 mb-3">
                    <div className={`alert ${
                      recomendacao.prioridade === 'Alta' ? 'alert-danger' :
                      recomendacao.prioridade === 'Média' ? 'alert-warning' : 'alert-info'
                    }`}>
                      <h6 className="alert-heading">
                        <i className="bi bi-arrow-right-circle me-1"></i>
                        {recomendacao.titulo}
                      </h6>
                      <p className="mb-0">{recomendacao.descricao}</p>
                      <small className="text-muted">
                        <strong>Prioridade:</strong> {recomendacao.prioridade}
                      </small>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <div className="alert alert-success">
                <h6 className="alert-heading">
                  <i className="bi bi-check-circle me-2"></i>
                  Parabéns!
                </h6>
                <p className="mb-0">
                  Seu órgão apresenta um bom nível de maturidade. 
                  Continue mantendo as boas práticas implementadas.
                </p>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default RelatorioIndividual;