import React, { useEffect, useRef } from 'react';
import ReactECharts from 'echarts-for-react';
import 'echarts-gl';
import { Card } from 'antd';
import { CHART_COLORS } from './types';

interface Map3DDataItem {
  name: string;
  value: number[];
  itemStyle?: {
    color?: string;
  };
}

interface Map3DChartProps {
  data: Map3DDataItem[];
  title?: string;
  height?: number;
  mapType?: 'china' | 'world';
  showTooltip?: boolean;
  colorRange?: [string, string];
}

const Map3DChart: React.FC<Map3DChartProps> = ({
  data,
  title = '3D地图可视化',
  height = 600,
  mapType = 'china',
  showTooltip = true,
  colorRange = [CHART_COLORS.info, CHART_COLORS.primary]
}) => {
  const chartRef = useRef<any>(null);

  const getOption = () => {
    return {
      title: {
        text: title,
        left: 'center',
        textStyle: {
          color: '#333',
          fontSize: 16,
          fontWeight: 'bold'
        }
      },
      tooltip: showTooltip ? {
        trigger: 'item',
        formatter: (params: any) => {
          const { name, value } = params;
          return `${name}<br/>数值: ${value[2] || 0}`;
        }
      } : undefined,
      visualMap: {
        min: 0,
        max: Math.max(...data.map(item => item.value[2] || 0)),
        calculable: true,
        inRange: {
          color: colorRange
        },
        textStyle: {
          color: '#333'
        }
      },
      geo3D: {
        map: mapType,
        regionHeight: 3,
        shading: 'lambert',
        light: {
          main: {
            intensity: 1.2,
            shadow: true
          },
          ambient: {
            intensity: 0.3
          }
        },
        viewControl: {
          distance: 70,
          alpha: 30,
          beta: 160,
          panSensitivity: 1,
          zoomSensitivity: 1
        },
        itemStyle: {
          color: '#aaa',
          opacity: 0.8,
          borderWidth: 0.5,
          borderColor: '#333'
        },
        emphasis: {
          itemStyle: {
            color: CHART_COLORS.primary
          }
        }
      },
      series: [
        {
          type: 'map3D',
          map: mapType,
          data: data,
          shading: 'lambert',
          label: {
            show: false,
            textStyle: {
              color: '#fff',
              fontSize: 12,
              backgroundColor: 'rgba(0,0,0,0.5)',
              borderRadius: 3,
              padding: [2, 4]
            }
          },
          emphasis: {
            label: {
              show: true
            }
          }
        }
      ]
    };
  };

  return (
    <Card title={title} style={{ height: height + 60 }}>
      <ReactECharts
        ref={chartRef}
        option={getOption()}
        style={{ height: height, width: '100%' }}
        notMerge={true}
        lazyUpdate={true}
      />
    </Card>
  );
};

export default Map3DChart;
export type { Map3DDataItem, Map3DChartProps };