import React, { useState } from 'react';
import { useAuth } from '../contexts/AuthContext';
import { useNavigate } from 'react-router-dom';

const MenuUsuario = () => {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const [showDropdown, setShowDropdown] = useState(false);

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  const handleAlterarSenha = () => {
    navigate('/alterar-senha');
    setShowDropdown(false);
  };

  const handlePerfil = () => {
    // Navegar para página de perfil se existir
    navigate('/perfil');
    setShowDropdown(false);
  };

  return (
	<div className="dropdown">
		<button
			className="btn btn-outline-light dropdown-toggle"
			type="button"
			data-bs-toggle="dropdown"
			aria-expanded="false"
		>
			<i className="bi bi-person-circle me-2"></i>
			{user?.nome || user?.email}
		</button>

		<ul className="dropdown-menu">
			<li className="dropdown-header">
				<small className="text-muted">{user?.email}</small>
          

				<small className="text-muted">{user?.perfil}</small>
				{user?.orgao_nome && (
					<>
              

						<small className="text-muted">{user.orgao_nome}</small>
					</>
				)}
			</li>
      
			<li><hr className="dropdown-divider" /></li>
      
			{/*<li>
				<a className="dropdown-item" href="#" onClick={handlePerfil}>
					<i className="bi bi-person me-2"></i>
					Meu Perfil
				</a>
			</li> */}
      
			<li>
				<a className="dropdown-item" href="#" onClick={handleAlterarSenha}>
					<i className="bi bi-key me-2"></i>
					Alterar Senha
				</a>
			</li>
      
			<li><hr className="dropdown-divider" /></li>
      
			<li>
				<a className="dropdown-item text-danger" href="#" onClick={handleLogout}>
					<i className="bi bi-box-arrow-right me-2"></i>
					Sair
				</a>
			</li>
		</ul>
    </div>
  );
};

export default MenuUsuario;

