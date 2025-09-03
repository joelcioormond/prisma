import React from 'react';
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
} from 'chart.js';
import { Bar, Doughnut, Line } from 'react-chartjs-2';

ChartJS.register(
  CategoryScale,
  LinearScale,
  BarElement,
  Title,
  Tooltip,
  Legend,
  ArcElement,
  PointElement,
  LineElement
);

const GraficosRelatorio = ({ dados }) => {
  // Gráfico de barras - Avaliações por órgão
  const dadosBarras = {
    labels: dados.avaliacoes_por_orgao.map(item => 
      item.orgao_sigla || item.orgao_nome.substring(0, 15) + '...'
    ),
    datasets: [
      {
        label: 'Finalizadas',
        data: dados.avaliacoes_por_orgao.map(item => item.finalizadas),
        backgroundColor: 'rgba(40, 167, 69, 0.8)',
        borderColor: 'rgba(40, 167, 69, 1)',
        borderWidth: 1,
      },
      {
        label: 'Em Andamento',
        data: dados.avaliacoes_por_orgao.map(item => item.em_andamento),
        backgroundColor: 'rgba(255, 193, 7, 0.8)',
        borderColor: 'rgba(255, 193, 7, 1)',
        borderWidth: 1,
      }
    ],
  };

  const opcoesBarras = {
    responsive: true,
    plugins: {
      legend: {
        position: 'top',
      },
      title: {
        display: true,
        text: 'Avaliações por Órgão',
        font: {
          size: 16
        }
      },
    },
    scales: {
      y: {
        beginAtZero: true,
        ticks: {
          stepSize: 1
        }
      }
    },
  };

  // Gráfico de rosca - Status das avaliações
  const dadosRosca = {
    labels: ['Finalizadas', 'Em Andamento', 'Rascunho'],
    datasets: [
      {
        data: [
          dados.estatisticas_gerais.avaliacoes_finalizadas,
          dados.estatisticas_gerais.total_avaliacoes - dados.estatisticas_gerais.avaliacoes_finalizadas,
          0 // Rascunho - pode ser implementado depois
        ],
        backgroundColor: [
          'rgba(40, 167, 69, 0.8)',
          'rgba(255, 193, 7, 0.8)',
          'rgba(108, 117, 125, 0.8)',
        ],
        borderColor: [
          'rgba(40, 167, 69, 1)',
          'rgba(255, 193, 7, 1)',
          'rgba(108, 117, 125, 1)',
        ],
        borderWidth: 2,
      },
    ],
  };

  const opcoesRosca = {
    responsive: true,
    plugins: {
      legend: {
        position: 'bottom',
      },
      title: {
        display: true,
        text: 'Status das Avaliações',
        font: {
          size: 16
        }
      },
    },
  };

  // Gráfico de linha - Ranking de maturidade
  const dadosLinha = {
    labels: dados.ranking_maturidade.slice(0, 10).map(item => 
      item.orgao_sigla || item.orgao_nome.substring(0, 10) + '...'
    ),
    datasets: [
      {
        label: 'Maturidade (%)',
        data: dados.ranking_maturidade.slice(0, 10).map(item => item.maturidade_media),
        borderColor: 'rgba(13, 110, 253, 1)',
        backgroundColor: 'rgba(13, 110, 253, 0.1)',
        borderWidth: 3,
        fill: true,
        tension: 0.4,
        pointBackgroundColor: 'rgba(13, 110, 253, 1)',
        pointBorderColor: '#fff',
        pointBorderWidth: 2,
        pointRadius: 6,
      },
    ],
  };

  const opcoesLinha = {
    responsive: true,
    plugins: {
      legend: {
        position: 'top',
      },
      title: {
        display: true,
        text: 'Top 10 - Ranking de Maturidade',
        font: {
          size: 16
        }
      },
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
    },
  };

  return (
    <div className="row">
      {/* Gráfico de Status */}
      <div className="col-md-6 mb-4">
        <div className="card h-100">
          <div className="card-body">
            <Doughnut data={dadosRosca} options={opcoesRosca} />
          </div>
        </div>
      </div>

      {/* Gráfico de Ranking */}
      <div className="col-md-6 mb-4">
        <div className="card h-100">
          <div className="card-body">
            <Line data={dadosLinha} options={opcoesLinha} />
          </div>
        </div>
      </div>

      {/* Gráfico de Barras */}
      <div className="col-12 mb-4">
        <div className="card">
          <div className="card-body">
            <Bar data={dadosBarras} options={opcoesBarras} />
          </div>
        </div>
      </div>
    </div>
  );
};

export default GraficosRelatorio;