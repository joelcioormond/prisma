import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider, useAuth } from './contexts/AuthContext';
import LoginSimples from './components/LoginSimples';
import Dashboard from './components/Dashboard';
import FormularioAvaliacao from './components/FormularioAvaliacao';
import GestaoUsuarios from './components/GestaoUsuarios';
import GestaoOrgaos from './components/GestaoOrgaos';
import RelatoriosAdmin from './components/RelatoriosAdmin';
import RelatorioIndividual from './components/RelatorioIndividual';
import AlterarSenha from './components/AlterarSenha';
import HeaderNavigation from './components/HeaderNavigation';



// Componente para proteger rotas
const RotaProtegida = ({ children }) => {
  const { user, loading } = useAuth();
  
  if (loading) {
    return <div className="d-flex justify-content-center mt-5">
      <div className="spinner-border" role="status"></div>
    </div>;
  }
  
  return user ? children : <Navigate to="/login" />;
};

// Layout principal com header
const MainLayout = ({ children }) => {
  return (
    <>
      <HeaderNavigation />
      <main className="container-fluid py-3">
        {children}
      </main>
    </>
  );
};


// Componente para rotas administrativas
const RotaAdmin = ({ children }) => {
  const { user } = useAuth();
  
  if (!user) {
    return <Navigate to="/login" />;
  }
  
  if (!user.permissoes?.gerenciar_usuarios) {
    alert('Você não tem permissão para acessar esta área');
    return <Navigate to="/dashboard" />;
  }
  
  return (
    <MainLayout>
      {children}
    </MainLayout>
  );
};

function App() {
  return (
    <AuthProvider>
      <Router future={{ 
        v7_startTransition: true,
        v7_relativeSplatPath: true 
      }}>
        <div className="App">
          <Routes>
            {/* Rota pública */}
            <Route path="/login" element={<LoginSimples />} />
            
            {/* Rotas protegidas normais */}
            <Route path="/dashboard" element={
              <RotaProtegida>
				<MainLayout>
					<Dashboard />
				</MainLayout>
              </RotaProtegida>
            } />
            
            <Route path="/avaliacao/:id" element={
              <RotaProtegida>
				<MainLayout>
					<FormularioAvaliacao />
				</MainLayout>
              </RotaProtegida>
            } />
            
            {/* Rota Alterar Senha */}
			<Route path="/alterar-senha" element={
				<RotaProtegida>
					<MainLayout>
						<AlterarSenha />
					</MainLayout>
				</RotaProtegida>
			} />
			
			{/* ROTAS ADMINISTRATIVAS */}
            <Route path="/admin/usuarios" element={
              <RotaAdmin>
                <GestaoUsuarios />
              </RotaAdmin>
            } />
			
			<Route path="/admin/orgaos" element={
			  <RotaAdmin>
			    <GestaoOrgaos />
			  </RotaAdmin>
            } />
			
			<Route path="/admin/relatorios" element={
			  <RotaAdmin>
			    <RelatoriosAdmin />
		      </RotaAdmin>
			} />
			
			<Route path="/relatorio-individual" element={
				<RotaProtegida>
					<MainLayout>
						<RelatorioIndividual />
					</MainLayout>
				</RotaProtegida>
			} />
            
            {/* Rota padrão */}
            <Route path="/" element={<Navigate to="/dashboard" />} />
            
            {/* Rota 404 */}
            <Route path="*" element={
              <div className="container mt-5 text-center">
                <h1>404 - Página não encontrada</h1>
                <p>A página que você está procurando não existe.</p>
                <a href="/dashboard" className="btn btn-primary">
                  Voltar ao Dashboard
                </a>
              </div>
            } />
          </Routes>
        </div>
      </Router>
    </AuthProvider>
  );
}

export default App;
