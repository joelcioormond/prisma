import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';

const FormularioAvaliacao = () => {
  const { id } = useParams();
  const navigate = useNavigate();
  const { user } = useAuth();
  const [avaliacao, setAvaliacao] = useState(null);
  const [kpas, setKpas] = useState([]);
  const [respostas, setRespostas] = useState({});
  const [loading, setLoading] = useState(true);
  const [kpaAtivo, setKpaAtivo] = useState(null);
  const [progresso, setProgresso] = useState(0);

  useEffect(() => {
    if (!user) {
      navigate('/login');
      return;
    }
    carregarDados();
  }, [id, user, navigate]);

  const carregarDados = async () => {
    try {
      console.log('🔄 Carregando dados da avaliação...');
      
      // Carregar avaliação
      const avaliacaoResponse = await fetch(`http://${window.location.hostname}:5000/api/avaliacoes/${id}`, {
        headers: {
          'X-User-Email': user?.email || ''
        }
      });
      const avaliacaoData = await avaliacaoResponse.json();
      
      if (avaliacaoData.success) {
        setAvaliacao(avaliacaoData.avaliacao);
        console.log('✅ Avaliação carregada:', avaliacaoData.avaliacao);
        
        // Carregar modelo baseado no arquivo JSON do usuário
        try {
          const modeloResponse = await fetch('/modelo_completo_final2.json');
          const modeloData = await modeloResponse.json();
          
          const nivelDesejado = avaliacaoData.avaliacao.nivel_desejado;
          const kpasDoNivel = modeloData.kpas_por_nivel[nivelDesejado.toString()] || [];
          
          setKpas(kpasDoNivel);
          
          if (kpasDoNivel.length > 0) {
            setKpaAtivo(kpasDoNivel[0]);
          }
          
          console.log('✅ Modelo carregado:', kpasDoNivel.length, 'KPAs');
        } catch (error) {
          console.error('❌ Erro ao carregar modelo:', error);
        }
      }

      // Carregar respostas existentes
      const respostasResponse = await fetch(`http://${window.location.hostname}:5000/api/avaliacoes/${id}/respostas`, {
        headers: {
          'X-User-Email': user?.email || ''
        }
      });
      
      if (respostasResponse.ok) {
        const respostasData = await respostasResponse.json();
        const respostasMap = {};
        respostasData.forEach(resposta => {
          respostasMap[resposta.atividade_id] = resposta;
        });
        setRespostas(respostasMap);
        console.log('✅ Respostas carregadas:', Object.keys(respostasMap).length);
      }

    } catch (error) {
      console.error('❌ Erro ao carregar dados:', error);
    } finally {
      setLoading(false);
    }
  };

  const salvarResposta = async (atividadeId, dadosResposta) => {
    try {
      console.log('💾 Salvando resposta:', { atividadeId, dadosResposta });
      
      const response = await fetch(`http://${window.location.hostname}:5000/api/avaliacoes/${id}/respostas`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-User-Email': user?.email || ''
        },
        body: JSON.stringify({
          atividade_id: atividadeId,
          ...dadosResposta
        })
      });

      if (response.ok) {
        setRespostas({
          ...respostas,
          [atividadeId]: { ...respostas[atividadeId], ...dadosResposta }
        });
        
        calcularProgresso();
        console.log('✅ Resposta salva com sucesso');
      } else {
        console.error('❌ Erro ao salvar resposta:', response.status);
      }
    } catch (error) {
      console.error('❌ Erro ao salvar resposta:', error);
    }
  };

  const calcularProgresso = () => {
    const totalAtividades = kpas.reduce((total, kpa) => total + (kpa.atividades?.length || 0), 0);
    const atividadesRespondidas = Object.keys(respostas).length;
    const percentual = totalAtividades > 0 ? (atividadesRespondidas / totalAtividades) * 100 : 0;
    setProgresso(Math.round(percentual));
  };

  const finalizarAvaliacao = async () => {
    try {
      const response = await fetch(`http://${window.location.hostname}:5000/api/avaliacoes/${id}/finalizar`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-User-Email': user?.email || ''
        }
      });

      if (response.ok) {
        alert('Avaliação finalizada com sucesso!');
        navigate('/dashboard');
      } else {
        alert('Erro ao finalizar avaliação');
      }
    } catch (error) {
      console.error('Erro ao finalizar avaliação:', error);
      alert('Erro de conexão');
    }
  };

  const uploadArquivo = async (file, tipo, atividadeId) => {
    const formData = new FormData();
    formData.append('file', file);

    try {
      const response = await fetch('http://${window.location.hostname}:5000/api/upload', {
        method: 'POST',
        body: formData
      });

      if (response.ok) {
        const data = await response.json();
        
        // Atualizar lista de arquivos na resposta
        const respostaAtual = respostas[atividadeId] || {};
        const campoArquivos = tipo === 'instituido' ? 'arquivos_instituido' : 'arquivos_institucionalizado';
        const arquivosAtuais = respostaAtual[campoArquivos] || [];
        
        const novosArquivos = [...arquivosAtuais, {
          nome: file.name,
          url: data.url,
          filename: data.filename
        }];

        salvarResposta(atividadeId, {
          ...respostaAtual,
          [campoArquivos]: novosArquivos
        });

        return data;
      } else {
        throw new Error('Erro no upload');
      }
    } catch (error) {
      console.error('Erro no upload:', error);
      alert('Erro ao enviar arquivo');
      return null;
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
      <nav className="navbar navbar-expand-lg navbar-dark bg-primary mb-4">
        <div className="container">
          <span className="navbar-brand">
            <i className="bi bi-clipboard-check me-2"></i>
            Avaliação da Maturidade da Gestão de Riscos
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
        {/* Informações da Avaliação */}
        {avaliacao && (
          <div className="card mb-4">
            <div className="card-header bg-info text-white">
              <div className="row align-items-center">
                <div className="col">
                  <h5 className="mb-0">
                    <i className="bi bi-file-earmark-check me-2"></i>
                    {avaliacao.titulo}
                  </h5>
                </div>
                <div className="col-auto">
                  <div className="progress bg-white" style={{width: '200px', height: '25px'}}>
                    <div 
                      className="progress-bar bg-success" 
                      role="progressbar" 
                      style={{width: `${progresso}%`}}
                    >
                      <strong>{progresso}%</strong>
                    </div>
                  </div>
                </div>
              </div>
            </div>
            <div className="card-body">
              <div className="row">
                <div className="col-md-4">
                  <p><strong><i className="bi bi-building me-1"></i>Órgão:</strong> {avaliacao.orgao_nome}</p>
                </div>
                <div className="col-md-4">
                  <p><strong><i className="bi bi-bar-chart-steps me-1"></i>Nível Desejado:</strong> 
                    <span className="badge bg-primary ms-2">Nível {avaliacao.nivel_desejado}</span>
                  </p>
                </div>
                <div className="col-md-4">
                  <p><strong><i className="bi bi-calendar me-1"></i>Data de Criação:</strong> {new Date(avaliacao.data_criacao).toLocaleDateString('pt-BR')}</p>
                </div>
              </div>
              
              <div className="alert alert-info">
                <h6><i className="bi bi-info-circle me-2"></i>Instruções de Avaliação:</h6>
                <div className="row">
                  <div className="col-md-6">
                    <ul className="mb-0">
                      <li><strong>Instituído:</strong> A atividade possui normativo, política ou documento formal</li>
                      <li><strong>Institucionalizado:</strong> A atividade possui histórico de práticas que utilizem os normativos</li>
                    </ul>
                  </div>
                  <div className="col-md-6">
                    <ul className="mb-0">
                      <li><strong>Justificativa:</strong> Explique por que considera a atividade implementada</li>
                      <li><strong>Evidências:</strong> Descreva links, situações ou documentos que comprovem</li>
                    </ul>
                  </div>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Navegação entre KPAs */}
        {kpas.length > 0 && (
          <div className="card mb-4">
            <div className="card-header">
              <h6 className="mb-0">
                <i className="bi bi-list-task me-2"></i>
                Navegação por KPAs - Nível {avaliacao?.nivel_desejado}
              </h6>
            </div>
            <div className="card-body">
              <div className="row">
                {kpas.map((kpa, index) => {
                  const atividadesKpa = kpa.atividades || [];
                  const atividadesRespondidas = atividadesKpa.filter(ativ => respostas[ativ.id]).length;
                  const percentualKpa = atividadesKpa.length > 0 ? (atividadesRespondidas / atividadesKpa.length) * 100 : 0;
                  
                  return (
                    <div key={kpa.codigo} className="col-md-4 col-lg-2 mb-3">
                      <button
                        className={`btn w-100 h-100 ${kpaAtivo?.codigo === kpa.codigo ? 'btn-primary' : 'btn-outline-primary'}`}
                        onClick={() => setKpaAtivo(kpa)}
                      >
                        <div className="text-center">
                          <strong>{kpa.codigo}</strong><br />
                          <small>{kpa.area}</small><br />
                          <div className="progress mt-2" style={{height: '4px'}}>
                            <div 
                              className="progress-bar bg-success" 
                              style={{width: `${percentualKpa}%`}}
                            ></div>
                          </div>
                          <small className="text-muted">{Math.round(percentualKpa)}%</small>
                        </div>
                      </button>
                    </div>
                  );
                })}
              </div>
            </div>
          </div>
        )}

        {/* KPA Ativo */}
        {kpaAtivo && (
          <div className="card mb-4">
            <div className="card-header bg-primary text-white">
              <h5 className="mb-0">
                <i className="bi bi-target me-2"></i>
                {kpaAtivo.codigo}: {kpaAtivo.area}
              </h5>
            </div>
            <div className="card-body">
              <div className="row mb-4">
                <div className="col-md-6">
                  <h6 className="text-info">
                    <i className="bi bi-info-circle me-1"></i>
                    Descrição do KPA:
                  </h6>
                  <p className="text-muted">{kpaAtivo.descricao}</p>
                </div>
                <div className="col-md-6">
                  <h6 className="text-success">
                    <i className="bi bi-bullseye me-1"></i>
                    Objetivo do KPA:
                  </h6>
                  <p className="text-muted">{kpaAtivo.objetivo}</p>
                </div>
              </div>

              {/* Atividades do KPA */}
              {(kpaAtivo.atividades || []).map((atividade, index) => {
                const resposta = respostas[atividade.id] || {};
                
                return (
                  <div key={atividade.id} className="border rounded p-4 mb-4 bg-light">
                    <div className="row">
                      <div className="col-12">
                        <h6 className="text-primary">
                          <i className="bi bi-check-circle me-2"></i>
                          Atividade {atividade.id}
                        </h6>
                        <p className="fw-bold mb-3">{atividade.descricao}</p>
                      </div>
                    </div>

                    {/* Orientações Gerais - Exibir sempre no topo */}
                    {atividade.orientacoes && (
                      <div className="row mb-4">
                        <div className="col-12">
                          <div className="alert alert-warning border-warning">
                            <h6 className="text-warning mb-2">
                              <i className="bi bi-lightbulb-fill me-2"></i>
                              Orientações Gerais:
                            </h6>
                            <div className="text-dark" style={{whiteSpace: 'pre-line'}}>
                              {atividade.orientacoes}
                            </div>
                          </div>
                        </div>
                      </div>
                    )}

                    {/* Checkboxes de Avaliação */}
                    <div className="row mb-3">
                      <div className="col-md-6">
                        <div className="form-check">
                          <input 
                            className="form-check-input" 
                            type="checkbox" 
                            id={`instituido_${atividade.id}`}
                            checked={resposta.instituido || false}
                            onChange={(e) => {
                              salvarResposta(atividade.id, {
                                ...resposta,
                                instituido: e.target.checked
                              });
                            }}
                          />
                          <label className="form-check-label fw-bold text-success" htmlFor={`instituido_${atividade.id}`}>
                            <i className="bi bi-file-text me-1"></i>
                            Instituído (Possui normativo/política)
                          </label>
						  
						  {/* Orientações sobre instituição - Exibir sempre no topo */}
						  {atividade.evidencias_instituicao && (
							<div className="row mb-4">
								<div className="col-12">
									<div className="border rounded p-3 mb-3 bg-success bg-opacity-10">
										<h6 className="text-success">
											<i className="bi bi-lightbulb-fill me-2"></i>
										</h6>
										<div className="text-dark" style={{whiteSpace: 'pre-line'}}>
											{atividade.evidencias_instituicao}
										</div>
									</div>
								</div>
							</div>
						  )}
                        </div>
                      </div>
                      <div className="col-md-6">
                        <div className="form-check">
                          <input 
                            className="form-check-input" 
                            type="checkbox" 
                            id={`institucionalizado_${atividade.id}`}
                            checked={resposta.institucionalizado || false}
                            onChange={(e) => {
                              salvarResposta(atividade.id, {
                                ...resposta,
                                institucionalizado: e.target.checked
                              });
                            }}
                          />
                          <label className="form-check-label fw-bold text-info" htmlFor={`institucionalizado_${atividade.id}`}>
                            <i className="bi bi-gear me-1"></i>
                            Institucionalizado (Possui práticas)
                          </label>
						  {/* Orientações sobre a institucionalização - Exibir sempre no topo */}
						  {atividade.evidencias_institucionalizacao && (
							<div className="row mb-4">
								<div className="col-12">
									<div className="border rounded p-3 mb-3 bg-info bg-opacity-10">
										<h6 className="text-info">
											<i className="bi bi-lightbulb-fill me-2"></i>
										</h6>
										<div className="text-dark" style={{whiteSpace: 'pre-line'}}>
											{atividade.evidencias_institucionalizacao}
										</div>
									</div>
								</div>
							</div>
						  )}
                        </div>
                      </div>
                    </div>

                    {/* Seção Instituído */}
                    {resposta.instituido && (
                      <div className="border rounded p-3 mb-3 bg-success bg-opacity-10">
                        <h6 className="text-success">
                          <i className="bi bi-file-text me-1"></i>
                          Avaliação - Instituído
                        </h6>
                        
                        <div className="row mb-3">
                          <div className="col-12">
                            <label className="form-label fw-bold">Exemplos de Evidências de Instituição:</label>
                            <div className="bg-white p-3 rounded border">
                              <small className="text-muted" style={{whiteSpace: 'pre-line'}}>
                                {atividade.evidencias_instituicao || 'Não especificado'}
                              </small>
                            </div>
                          </div>
                        </div>

                        <div className="row mb-3">
                          <div className="col-md-6">
                            <label className="form-label fw-bold">Justificativa:</label>
                            <textarea
                              className="form-control"
                              rows="3"
                              placeholder="Explique por que considera esta atividade instituída..."
                              value={resposta.justificativa_instituido || ''}
                              onChange={(e) => {
                                salvarResposta(atividade.id, {
                                  ...resposta,
                                  justificativa_instituido: e.target.value
                                });
                              }}
                            />
                          </div>
                          <div className="col-md-6">
                            <label className="form-label fw-bold">Evidências Documentais:</label>
                            <textarea
                              className="form-control"
                              rows="3"
                              placeholder="Descreva links, documentos, situações que comprovem..."
                              value={resposta.evidencias_instituido || ''}
                              onChange={(e) => {
                                salvarResposta(atividade.id, {
                                  ...resposta,
                                  evidencias_instituido: e.target.value
                                });
                              }}
                            />
                          </div>
                        </div>

                        <div className="row mb-3">
                          <div className="col-12">
                            <label className="form-label fw-bold">Upload de Arquivos:</label>
                            <input
                              type="file"
                              className="form-control"
                              multiple
                              onChange={(e) => {
                                Array.from(e.target.files).forEach(file => {
                                  uploadArquivo(file, 'instituido', atividade.id);
                                });
                              }}
                            />
                            {resposta.arquivos_instituido && resposta.arquivos_instituido.length > 0 && (
                              <div className="mt-2">
                                <small className="text-muted">Arquivos enviados:</small>
                                <ul className="list-unstyled">
                                  {resposta.arquivos_instituido.map((arquivo, idx) => (
                                    <li key={idx}>
                                      <a href={arquivo.url} target="_blank" rel="noopener noreferrer">
                                        <i className="bi bi-file-earmark me-1"></i>
                                        {arquivo.nome}
                                      </a>
                                    </li>
                                  ))}
                                </ul>
                              </div>
                            )}
                          </div>
                        </div>
                      </div>
                    )}

                    {/* Seção Institucionalizado */}
                    {resposta.institucionalizado && (
                      <div className="border rounded p-3 mb-3 bg-info bg-opacity-10">
                        <h6 className="text-info">
                          <i className="bi bi-gear me-1"></i>
                          Avaliação - Institucionalizado
                        </h6>
                        
                        <div className="row mb-3">
                          <div className="col-12">
                            <label className="form-label fw-bold">Exemplos de Evidências de Institucionalização:</label>
                            <div className="bg-white p-3 rounded border">
                              <small className="text-muted" style={{whiteSpace: 'pre-line'}}>
                                {atividade.evidencias_institucionalizacao || 'Não especificado'}
                              </small>
                            </div>
                          </div>
                        </div>

                        <div className="row mb-3">
                          <div className="col-md-6">
                            <label className="form-label fw-bold">Justificativa:</label>
                            <textarea
                              className="form-control"
                              rows="3"
                              placeholder="Explique por que considera esta atividade institucionalizada..."
                              value={resposta.justificativa_institucionalizado || ''}
                              onChange={(e) => {
                                salvarResposta(atividade.id, {
                                  ...resposta,
                                  justificativa_institucionalizado: e.target.value
                                });
                              }}
                            />
                          </div>
                          <div className="col-md-6">
                            <label className="form-label fw-bold">Evidências Práticas:</label>
                            <textarea
                              className="form-control"
                              rows="3"
                              placeholder="Descreva práticas, histórico, aplicações que comprovem..."
                              value={resposta.evidencias_institucionalizado || ''}
                              onChange={(e) => {
                                salvarResposta(atividade.id, {
                                  ...resposta,
                                  evidencias_institucionalizado: e.target.value
                                });
                              }}
                            />
                          </div>
                        </div>

                        <div className="row mb-3">
                          <div className="col-12">
                            <label className="form-label fw-bold">Upload de Arquivos:</label>
                            <input
                              type="file"
                              className="form-control"
                              multiple
                              onChange={(e) => {
                                Array.from(e.target.files).forEach(file => {
                                  uploadArquivo(file, 'institucionalizado', atividade.id);
                                });
                              }}
                            />
                            {resposta.arquivos_institucionalizado && resposta.arquivos_institucionalizado.length > 0 && (
                              <div className="mt-2">
                                <small className="text-muted">Arquivos enviados:</small>
                                <ul className="list-unstyled">
                                  {resposta.arquivos_institucionalizado.map((arquivo, idx) => (
                                    <li key={idx}>
                                      <a href={arquivo.url} target="_blank" rel="noopener noreferrer">
                                        <i className="bi bi-file-earmark me-1"></i>
                                        {arquivo.nome}
                                      </a>
                                    </li>
                                  ))}
                                </ul>
                              </div>
                            )}
                          </div>
                        </div>
                      </div>
                    )}

                    {/* Status da Atividade */}
                    {(resposta.instituido || resposta.institucionalizado) && (
                      <div className="row mt-3">
                        <div className="col-12">
                          <div className="alert alert-success">
                            <i className="bi bi-check-circle-fill me-2"></i>
                            <strong>Status:</strong>
                            {resposta.instituido && <span className="badge bg-success ms-2">Instituído</span>}
                            {resposta.institucionalizado && <span className="badge bg-info ms-2">Institucionalizado</span>}
                          </div>
                        </div>
                      </div>
                    )}
                  </div>
                );
              })}
            </div>
          </div>
        )}

        {/* Botões de Ação */}
        <div className="row mb-4">
          <div className="col">
            <div className="d-flex gap-2">
              <button className="btn btn-success" onClick={calcularProgresso}>
                <i className="bi bi-save me-1"></i>
                Salvar Progresso ({progresso}%)
              </button>
              <button className="btn btn-primary" onClick={finalizarAvaliacao}>
                <i className="bi bi-check-circle me-1"></i>
                Finalizar Avaliação
              </button>
              <button className="btn btn-info" onClick={() => window.print()}>
                <i className="bi bi-printer me-1"></i>
                Imprimir
              </button>
            </div>
          </div>
        </div>

        {/* Resumo Final */}
        <div className="card mb-4">
          <div className="card-header">
            <h6 className="mb-0">
              <i className="bi bi-graph-up me-2"></i>
              Resumo da Avaliação
            </h6>
          </div>
          <div className="card-body">
            <div className="row">
              <div className="col-md-3">
                <div className="text-center">
                  <h4 className="text-primary">{kpas.length}</h4>
                  <small>KPAs Totais</small>
                </div>
              </div>
              <div className="col-md-3">
                <div className="text-center">
                  <h4 className="text-info">{kpas.reduce((total, kpa) => total + (kpa.atividades?.length || 0), 0)}</h4>
                  <small>Atividades Totais</small>
                </div>
              </div>
              <div className="col-md-3">
                <div className="text-center">
                  <h4 className="text-success">{Object.keys(respostas).length}</h4>
                  <small>Atividades Avaliadas</small>
                </div>
              </div>
              <div className="col-md-3">
                <div className="text-center">
                  <h4 className="text-warning">{progresso}%</h4>
                  <small>Progresso</small>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default FormularioAvaliacao;