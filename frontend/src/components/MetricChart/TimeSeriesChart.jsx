import React from 'react';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
  Filler,
} from 'chart.js';
import { Line } from 'react-chartjs-2';

ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
  Filler
);

export default function TimeSeriesChart({
  title,
  labels = [],
  datasets = [],
  yAxisLabel = '%',
  height = 240,
  suggestedMax = 100,
}) {
  const options = {
    responsive: true,
    maintainAspectRatio: false,
    interaction: {
      mode: 'index',
      intersect: false,
    },
    plugins: {
      legend: {
        display: datasets.length > 1,
        position: 'top',
        labels: {
          color: '#94a3b8',
          font: { family: 'Inter', size: 12 },
          boxWidth: 12,
        },
      },
      tooltip: {
        backgroundColor: '#0d121f',
        titleColor: '#f8fafc',
        bodyColor: '#94a3b8',
        borderColor: 'rgba(255, 255, 255, 0.15)',
        borderWidth: 1,
        padding: 10,
        boxPadding: 4,
        usePointStyle: true,
      },
    },
    scales: {
      x: {
        grid: { color: 'rgba(255, 255, 255, 0.04)' },
        ticks: {
          color: '#64748b',
          font: { family: 'JetBrains Mono', size: 10 },
          maxTicksLimit: 8,
        },
      },
      y: {
        suggestedMin: 0,
        suggestedMax: suggestedMax,
        grid: { color: 'rgba(255, 255, 255, 0.06)' },
        ticks: {
          color: '#94a3b8',
          font: { family: 'JetBrains Mono', size: 11 },
          callback: (value) => `${value}${yAxisLabel}`,
        },
      },
    },
  };

  const data = {
    labels: labels.map((l) => {
      if (!l) return '';
      const d = new Date(l);
      return isNaN(d.getTime()) ? l : d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' });
    }),
    datasets: datasets.map((ds) => ({
      tension: 0.35,
      borderWidth: 2,
      pointRadius: 2,
      pointHoverRadius: 6,
      fill: ds.fill !== undefined ? ds.fill : true,
      ...ds,
    })),
  };

  return (
    <div style={{ height, width: '100%', position: 'relative' }}>
      <Line options={options} data={data} />
    </div>
  );
}
