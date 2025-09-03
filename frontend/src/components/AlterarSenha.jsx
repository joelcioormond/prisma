import React, { useState } from 'react';
import { useAuth } from '../contexts/AuthContext';

const AlterarSenha = () => {
  const { user } = useAuth();
  const [formData, setFormData] = useState({
    senha_atual: '',
    senha_nova: '',
    confirmar_senha: ''
  });
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState({ type: '', text: '' });

  const handleChange = (e) => {
    setFormData({
      ...formData,
      [e.target.name]: e.target.value
    });
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setMessage({ type: '', text: '' });

    // Validações no frontend
    if (formData.senha_nova !== formData.confirmar_senha) {
      setMessage({ type: 'error', text: 'Confirmação de senha não confere' });
      setLoading(false);
      return;
    }

    if (formData.senha_nova.length < 6) {
      setMessage({ type: 'error', text: 'Nova senha deve ter pelo menos 6 caracteres' });
      setLoading(false);
      return;
    }

    try {
      const apiUrl = `http://${window.location.hostname}:5000/api/auth/alterar-senha`;
      const response = await fetch(apiUrl, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-User-Email': user?.email || ''
        },
        body: JSON.stringify(formData)
      });

      const data = await response.json();

      if (data.success) {
        setMessage({ type: 'success', text: 'Senha alterada com sucesso!' });
        setFormData({
          senha_atual: '',
          senha_nova: '',
          confirmar_senha: ''
        });
      } else {
        setMessage({ type: 'error', text: data.message || 'Erro ao alterar senha' });
      }
    } catch (error) {
      console.error('Erro ao alterar senha:', error);
      setMessage({ type: 'error', text: 'Erro de conexão com o servidor' });
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="container mt-4">
      <div className="row justify-content-center">
        <div className="col-md-6">
          <div className="card">
            <div className="card-header">
              <h4 className="mb-0">
                <i className="bi bi-key me-2"></i>
                Alterar Senha
              </h4>
            </div>
            <div className="card-body">
              <form onSubmit={handleSubmit}>
                <div className="mb-3">
                  <label htmlFor="senha_atual" className="form-label">
                    Senha Atual *
                  </label>
                  <input
                    type="password"
                    className="form-control"
                    id="senha_atual"
                    name="senha_atual"
                    value={formData.senha_atual}
                    onChange={handleChange}
                    required
                  />
                </div>

                <div className="mb-3">
                  <label htmlFor="senha_nova" className="form-label">
                    Nova Senha *
                  </label>
                  <input
                    type="password"
                    className="form-control"
                    id="senha_nova"
                    name="senha_nova"
                    value={formData.senha_nova}
                    onChange={handleChange}
                    minLength="6"
                    required
                  />
                  <div className="form-text">
                    Mínimo de 6 caracteres
                  </div>
                </div>

                <div className="mb-3">
                  <label htmlFor="confirmar_senha" className="form-label">
                    Confirmar Nova Senha *
                  </label>
                  <input
                    type="password"
                    className="form-control"
                    id="confirmar_senha"
                    name="confirmar_senha"
                    value={formData.confirmar_senha}
                    onChange={handleChange}
                    required
                  />
                </div>

                {message.text && (
                  <div className={`alert ${message.type === 'success' ? 'alert-success' : 'alert-danger'}`}>
                    <i className={`bi ${message.type === 'success' ? 'bi-check-circle' : 'bi-exclamation-triangle'} me-2`}></i>
                    {message.text}
                  </div>
                )}

                <div className="d-grid gap-2">
                  <button
                    type="submit"
                    className="btn btn-primary"
                    disabled={loading}
                  >
                    {loading ? (
                      <>
                        <span className="spinner-border spinner-border-sm me-2"></span>
                        Alterando...
                      </>
                    ) : (
                      <>
                        <i className="bi bi-check-lg me-2"></i>
                        Alterar Senha
                      </>
                    )}
                  </button>
                </div>
              </form>
            </div>
          </div>

          <div className="mt-3">
            <div className="alert alert-info">
              <i className="bi bi-info-circle me-2"></i>
              <strong>Dicas de Segurança:</strong>
              <ul className="mb-0 mt-2">
                <li>Use uma senha forte com pelo menos 6 caracteres</li>
                <li>Combine letras, números e símbolos</li>
                <li>Não compartilhe sua senha com outras pessoas</li>
                <li>Altere sua senha regularmente</li>
              </ul>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default AlterarSenha;

