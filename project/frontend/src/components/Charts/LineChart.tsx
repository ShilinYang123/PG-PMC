import React from 'react';
import { Line } from '@ant-design/charts';

export interface LineChartData {
  x: string;
  y: number;
  category?: string;
}

export interface LineChartProps {
  data: LineChartData[];
  height?: number;
  xField?: string;
  yField?: string;
  seriesField?: string;
  smooth?: boolean;
  color?: string | string[];
}

const LineChart: React.FC<LineChartProps> = ({
  data,
  height = 300,
  xField = 'x',
  yField = 'y',
  seriesField,
  smooth = true,
  color = '#1890ff'
}) => {
  const config = {
    data,
    height,
    xField,
    yField,
    seriesField,
    smooth,
    color,
    point: {
      size: 4,
      shape: 'circle',
    },
    tooltip: {
      showMarkers: true,
    },
    interactions: [
      {
        type: 'marker-active',
      },
    ],
  };

  return <Line {...config} />;
};

export default LineChart;