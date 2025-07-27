import React from 'react';
import { Column } from '@ant-design/charts';

export interface BarChartData {
  x: string;
  y: number;
  category?: string;
}

export interface BarChartProps {
  data: BarChartData[];
  height?: number;
  xField?: string;
  yField?: string;
  seriesField?: string;
  color?: string | string[];
  columnWidthRatio?: number;
}

const BarChart: React.FC<BarChartProps> = ({
  data,
  height = 300,
  xField = 'x',
  yField = 'y',
  seriesField,
  color = '#1890ff',
  columnWidthRatio = 0.8
}) => {
  const config = {
    data,
    height,
    xField,
    yField,
    seriesField,
    color,
    columnWidthRatio,
    label: {
      position: 'middle' as const,
      style: {
        fill: '#FFFFFF',
        opacity: 0.6,
      },
    },
    tooltip: {
      showMarkers: false,
    },
    interactions: [
      {
        type: 'element-active',
      },
    ],
  };

  return <Column {...config} />;
};

export default BarChart;