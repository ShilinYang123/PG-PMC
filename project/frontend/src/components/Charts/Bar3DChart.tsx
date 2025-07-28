import React, { useRef } from 'react';
import ReactECharts from 'echarts-for-react';
import 'echarts-gl';
import { Card, Space, Tag } from 'antd';
import { CHART_COLORS } from './types';

interface Bar3DDataItem {
  name: string;
  value: number;
  category?: string;
  color?: string;
}

interface Bar3DChartProps {
  data: Bar3DDataItem[];
  title?: string;
  height?: number;
  showTooltip?: boolean;
  colorPalette?: string[];
  viewAngle?: {
    alpha: number;
    beta: number;
  };
  barWidth?: number;
  barDepth?: number;
}

const Bar3DChart: React.FC<Bar3DChartProps> = ({
  data,
  title = '3D柱状图',
  height = 500,
  showTooltip = true,
  colorPalette = [
    CHART_COLORS.primary,
    CHART_COLORS.success,
    CHART_COLORS.warning,
    CHART_COLORS.error,
    CHART_COLORS.info,
    CHART_COLORS.purple,
    CHART_COLORS.orange
  ],
  viewAngle = { alpha: 40, beta: 40 },
  barWidth = 1,
  barDepth = 1
}) => {
  const chartRef = useRef<any>(null);

  // 处理数据，为3D图表格式化
  const processData = () => {
    return data.map((item, index) => {
      const color = item.color || colorPalette[index % colorPalette.length];
      return {
        name: item.name,
        value: [index, 0, item.value],
        itemStyle: {
          color: color
        },
        label: {
          show: true,
          position: 'top',
          formatter: '{c}',
          textStyle: {
            color: '#333',
            fontSize: 12,
            fontWeight: 'bold'
          }
        }
      };
    });
  };

  const getOption = () => {
    const processedData = processData();
    const maxValue = Math.max(...data.map(item => item.value));
    
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
          return `${name}<br/>数值: ${value[2]}`;
        }
      } : undefined,
      visualMap: {
        max: maxValue,
        inRange: {
          color: colorPalette
        },
        show: false
      },
      xAxis3D: {
        type: 'category',
        data: data.map(item => item.name),
        axisLabel: {
          textStyle: {
            color: '#333'
          },
          interval: 0,
          rotate: data.length > 8 ? 45 : 0
        },
        axisLine: {
          lineStyle: {
            color: '#ccc'
          }
        }
      },
      yAxis3D: {
        type: 'category',
        data: [''],
        axisLabel: {
          show: false
        },
        axisLine: {
          show: false
        },
        axisTick: {
          show: false
        }
      },
      zAxis3D: {
        type: 'value',
        min: 0,
        max: maxValue * 1.1,
        axisLabel: {
          textStyle: {
            color: '#333'
          }
        },
        axisLine: {
          lineStyle: {
            color: '#ccc'
          }
        },
        splitLine: {
          lineStyle: {
            color: '#f0f0f0'
          }
        }
      },
      grid3D: {
        boxWidth: data.length * 10,
        boxHeight: 20,
        boxDepth: 20,
        viewControl: {
          alpha: viewAngle.alpha,
          beta: viewAngle.beta,
          distance: 200,
          minDistance: 100,
          maxDistance: 400,
          panSensitivity: 1,
          zoomSensitivity: 1
        },
        light: {
          main: {
            intensity: 1.2,
            shadow: true,
            shadowQuality: 'medium',
            alpha: 30,
            beta: 40
          },
          ambient: {
            intensity: 0.3
          }
        },
        environment: 'auto',
        postEffect: {
          enable: true,
          SSAO: {
            enable: true,
            quality: 'medium',
            radius: 2
          }
        }
      },
      series: [
        {
          type: 'bar3D',
          data: processedData,
          shading: 'lambert',
          barSize: [barWidth, barDepth],
          itemStyle: {
            opacity: 0.8
          },
          emphasis: {
            itemStyle: {
              opacity: 1
            },
            label: {
              show: true,
              textStyle: {
                fontSize: 14,
                fontWeight: 'bold'
              }
            }
          },
          animationDurationUpdate: 1000,
          animationEasingUpdate: 'cubicInOut'
        }
      ]
    };
  };

  // 计算统计信息
  const getStatistics = () => {
    const values = data.map(item => item.value);
    const total = values.reduce((sum, val) => sum + val, 0);
    const max = Math.max(...values);
    const min = Math.min(...values);
    const avg = total / values.length;
    
    return { total, max, min, avg: parseFloat(avg.toFixed(2)) };
  };

  const stats = getStatistics();

  return (
    <Card 
      title={title} 
      style={{ height: height + 120 }}
      extra={
        <Space>
          <Tag color="blue">总计: {stats.total}</Tag>
          <Tag color="green">最大: {stats.max}</Tag>
          <Tag color="orange">最小: {stats.min}</Tag>
          <Tag color="purple">平均: {stats.avg}</Tag>
        </Space>
      }
    >
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

export default Bar3DChart;
export type { Bar3DDataItem, Bar3DChartProps };