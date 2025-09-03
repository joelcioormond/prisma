import React, { useState, useEffect } from 'react';
import { useAuth } from '../contexts/AuthContext';

const NovaAvaliacaoModal = ({ show, onClose, onSuccess }) => {
  const { user } = useAuth();
  const [formData, setFormData] = useState({
    titulo: '',
    orgao_id: '',
    nivel_desejado: 2
  });
  const [orgaos, setOrgaos] = useState([]);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (show) {
      carregarOrgaos();
    }
  }, [show]);

  const carregarOrgaos = async () => {
    try {
     const apiUrl = `http://${window.location.hostname}:5000/api/orgaos`;
     const response = await fetch(apiUrl );
      if (response.ok) {
        const data = await response.json();
        setOrgaos(data);
      }
    } catch (error) {
      console.error('Erro ao carregar órgãos:', error);
    }
  };

  const criarAvaliacao = async (e) => {
    e.preventDefault();
    setLoading(true);

    try {
      const apiUrl = `http://${window.location.hostname}:5000/api/avaliacoes`;
      const response = await fetch(apiUrl, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-User-Email': user?.email || ''
        },
        body: JSON.stringify(formData )
      });

      const data = await response.json();

      if (data.success) {
        alert('Avaliação criada com sucesso!');
        setFormData({ titulo: '', orgao_id: '', nivel_desejado: 2 });
        onSuccess();
      } else {
        alert('Erro: ' + data.message);
      }
    } catch (error) {
      console.error('Erro ao criar avaliação:', error);
      alert('Erro de conexão');
    } finally {
      setLoading(false);
    }
  };

  if (!show) return null;

  return (
    <div className="modal show d-block" tabIndex="-1" style={{backgroundColor: 'rgba(0,0,0,0.5)'}}>
      <div className="modal-dialog">
        <div className="modal-content">
          <div className="modal-header">
            <h5 className="modal-title">
              <i className="bi bi-plus-circle me-2"></i>
              Nova Avaliação de Gestão de Riscos
            </h5>
            <button type="button" className="btn-close" onClick={onClose}></button>
          </div>
          <form onSubmit={criarAvaliacao}>
            <div className="modal-body">
              <div className="mb-3">
                <label className="form-label">Título da Avaliação *</label>
                <input
                  type="text"
                  className="form-control"
                  value={formData.titulo}
                  onChange={(e) => setFormData({...formData, titulo: e.target.value})}
                  placeholder="Ex: Avaliação de Gestão de Riscos 2025"
                  required
                />
              </div>

              <div className="mb-3">
                <label className="form-label">Órgão *</label>
                <select
                  className="form-select"
                  value={formData.orgao_id}
                  onChange={(e) => setFormData({...formData, orgao_id: e.target.value})}
                  required
                >
                  <option value="">Selecione um órgão</option>
                  {orgaos.map(orgao => (
                    <option key={orgao.id} value={orgao.id}>
                      {orgao.nome} ({orgao.sigla})
                    </option>
                  ))}
                </select>
              </div>

              <div className="mb-3">
                <label className="form-label">Nível Desejado *</label>
                <select
                  className="form-select"
                  value={formData.nivel_desejado}
                  onChange={(e) => setFormData({...formData, nivel_desejado: parseInt(e.target.value)})}
                  required
                >
                  <option value={2}>Nível 2 - Básico</option>
                  <option value={3}>Nível 3 - Intermediário</option>
                  <option value={4}>Nível 4 - Avançado</option>
                  <option value={5}>Nível 5 - Otimizado</option>
                </select>
                <small className="text-muted">
                  Selecione o nível de maturidade que o órgão deseja alcançar
                </small>
              </div>

              <div className="alert alert-info">
                <i className="bi bi-info-circle me-2"></i>
                <strong>Informação:</strong> A avaliação será baseada no modelo ISO 31000 
                com KPAs específicos para o nível selecionado.
              </div>
            </div>
            <div className="modal-footer">
              <button type="button" className="btn btn-secondary" onClick={onClose}>
                Cancelar
              </button>
              <button type="submit" className="btn btn-primary" disabled={loading}>
                {loading ? (
                  <>
                    <span className="spinner-border spinner-border-sm me-1"></span>
                    Criando...
                  </>
                ) : (
                  <>
                    <i className="bi bi-plus me-1"></i>
                    Criar Avaliação
                  </>
                )}
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>
  );
};

export default NovaAvaliacaoModal;