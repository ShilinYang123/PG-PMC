import React from 'react';
import { Pie } from '@ant-design/charts';

export interface PieChartData {
  type: string;
  value: number;
}

export interface PieChartProps {
  data: PieChartData[];
  height?: number;
  angleField?: string;
  colorField?: string;
  radius?: number;
  innerRadius?: number;
  color?: string[];
}

const PieChart: React.FC<PieChartProps> = ({
  data,
  height = 300,
  angleField = 'value',
  colorField = 'type',
  radius = 0.8,
  innerRadius = 0,
  color
}) => {
  const config = {
    data,
    height,
    angleField,
    colorField,
    radius,
    innerRadius,
    color,
    label: {
      type: 'outer' as const,
      content: '{name} {percentage}',
    },
    tooltip: {
      showMarkers: false,
    },
    interactions: [
      {
        type: 'element-active',
      },
    ],
    legend: {
      position: 'bottom' as const,
    },
  };

  return <Pie {...config} />;
};

export default PieChart;