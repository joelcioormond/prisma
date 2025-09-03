import React, { useState } from 'react';
import { useAuth } from '../contexts/AuthContext';
import { useNavigate } from 'react-router-dom';

const LoginSimples = () => {
  const [email, setEmail] = useState('');
  const [senha, setSenha] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const { login } = useAuth();
  const navigate = useNavigate();

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');

    if (!email.endsWith('mt.gov.br')) {
      setError('Apenas emails mt.gov.br são permitidos');
      setLoading(false);
      return;
    }

    if (!senha) {
      setError('Senha é obrigatória');
      setLoading(false);
      return;
    }

    const result = await login(email, senha);
    
    if (result.success) {
      navigate('/dashboard');
    } else {
      setError(result.error || 'Email ou senha incorretos');
    }
    
    setLoading(false);
  };

  return (
    <div className="container-fluid vh-100 d-flex align-items-center justify-content-center bg-light">
      <div className="row w-100">
        <div className="col-md-6 col-lg-4 mx-auto">
          <div className="card shadow">
            <div className="card-body p-5">
              <div className="text-center mb-4">			  
				<img 
					src="/logo.png" 
					alt="Brasão do Estado de Mato Grosso" 
					style={{width: '80px', height: '80px', objectFit: 'contain'}}
				/>			  
                <h2 className="card-title text-primary">
                  <i className="bi bi-shield-check me-2"></i>
                  PRISMA
                </h2>
                <p className="text-muted">Plataforma de Riscos e Maturidade</p>
              </div>

              <form onSubmit={handleSubmit}>
                <div className="mb-3">
                  <label htmlFor="email" className="form-label">
                    Email Institucional
                  </label>
                  <input
                    type="email"
                    className="form-control"
                    id="email"
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    placeholder="seu.email@[orgao].mt.gov.br"
                    required
                  />
                  <div className="form-text">
                    Apenas emails terminados com mt.gov.br são permitidos
                  </div>
                </div>

                <div className="mb-3">
                  <label htmlFor="senha" className="form-label">
                    Senha
                  </label>
                  <input
                    type="password"
                    className="form-control"
                    id="senha"
                    value={senha}
                    onChange={(e) => setSenha(e.target.value)}
                    placeholder="Digite sua senha"
                    required
                  />
                </div>

                {error && (
                  <div className="alert alert-danger" role="alert">
                    <i className="bi bi-exclamation-triangle me-2"></i>
                    {error}
                  </div>
                )}

                <button
                  type="submit"
                  className="btn btn-primary w-100"
                  disabled={loading}
                >
                  {loading ? (
                    <>
                      <span className="spinner-border spinner-border-sm me-2" role="status"></span>
                      Entrando...
                    </>
                  ) : (
                    <>
                      <i className="bi bi-box-arrow-in-right me-2"></i>
                      Entrar
                    </>
                  )}
                </button>
              </form>

              <div className="text-center mt-3">
                <small className="text-muted">
                  <a href="#" className="text-decoration-none" onClick={() => alert('Entre em contato com o administrador do sistema para recuperar sua senha.')}>
                    Esqueceu sua senha?
                  </a>
                </small>
              </div>

              <div className="text-center mt-4">
                <small className="text-muted">
                  PRISMA<br />
                  Plataforma de Riscos e Maturidade
                </small>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default LoginSimples;