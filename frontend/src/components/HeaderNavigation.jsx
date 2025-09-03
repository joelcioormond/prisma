import React from 'react';
import { Link, useLocation } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import MenuUsuario from './MenuUsuario';

const HeaderNavigation = () => {
  const { user } = useAuth();
  const location = useLocation();

  const isActive = (path) => {
    return location.pathname === path ? 'nav-link active' : 'nav-link';
  };

  return (
    <nav className="navbar navbar-expand-lg navbar-dark bg-primary">
      <div className="container-fluid">
        <Link className="navbar-brand" to="/dashboard">
          <img 
            src="/logo.png" 
            alt="MT" 
            width="30" 
            height="30" 
            className="d-inline-block align-text-top me-2"
          />
          PRISMA
        </Link>

        <button 
          className="navbar-toggler" 
          type="button" 
          data-bs-toggle="collapse" 
          data-bs-target="#navbarNav"
        >
          <span className="navbar-toggler-icon"></span>
        </button>

        <div className="collapse navbar-collapse" id="navbarNav">
          <ul className="navbar-nav me-auto">
            <li className="nav-item">
              <Link className={isActive('/dashboard')} to="/dashboard">
                <i className="bi bi-speedometer2 me-1"></i>
                Dashboard
              </Link>
            </li>
            
            <li className="nav-item">
              <Link className={isActive('/dashboard')} to="/dashboard">
                <i className="bi bi-clipboard-check me-1"></i>
                Avaliações
              </Link>
            </li>

            {user?.permissoes?.gerenciar_usuarios && (
              <li className="nav-item">
                <Link className={isActive('/admin/usuarios')} to="/admin/usuarios">
                  <i className="bi bi-people me-1"></i>
                  Usuários
                </Link>
              </li>
            )}

            {user?.permissoes?.visualizar_relatorios_gerais && (
              <li className="nav-item">
                <Link className={isActive('/admin/relatorios')} to="/admin/relatorios">
                  <i className="bi bi-graph-up me-1"></i>
                  Relatórios
                </Link>
              </li>
            )}
          </ul>

          <div className="d-flex align-items-center">
            <MenuUsuario />
          </div>
        </div>
      </div>
    </nav>
  );
};

export default HeaderNavigation;

