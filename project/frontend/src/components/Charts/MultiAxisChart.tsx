import React from 'react';
import ReactECharts from 'echarts-for-react';
import { Card, Switch, Space, Tooltip } from 'antd';
import { InfoCircleOutlined } from '@ant-design/icons';
import { CHART_COLORS } from './types';

interface SeriesData {
  name: string;
  data: number[];
  type: 'line' | 'bar';
  yAxisIndex: number;
  color?: string;
  unit?: string;
  smooth?: boolean;
  stack?: string;
}

interface YAxisConfig {
  name: string;
  unit: string;
  position: 'left' | 'right';
  min?: number;
  max?: number;
  color?: string;
}

interface MultiAxisChartProps {
  xAxisData: string[];
  series: SeriesData[];
  yAxes: YAxisConfig[];
  title?: string;
  height?: number;
  showDataZoom?: boolean;
  showBrush?: boolean;
}

const MultiAxisChart: React.FC<MultiAxisChartProps> = ({ 
  xAxisData,
  series,
  yAxes,
  title = '多轴图表分析',
  height = 400,
  showDataZoom = true,
  showBrush = false
}) => {
  const [enableDataZoom, setEnableDataZoom] = React.useState(showDataZoom);
  const [enableBrush, setEnableBrush] = React.useState(showBrush);
  const [visibleSeries, setVisibleSeries] = React.useState<Record<string, boolean>>(
    series.reduce((acc, s) => ({ ...acc, [s.name]: true }), {})
  );

  const getOption = () => {
    const filteredSeries = series.filter(s => visibleSeries[s.name]);
    
    return {
      title: {
        text: title,
        left: 'center',
        textStyle: {
          fontSize: 16,
          fontWeight: 'bold'
        }
      },
      tooltip: {
        trigger: 'axis',
        axisPointer: {
          type: 'cross',
          crossStyle: {
            color: '#999'
          }
        },
        formatter: (params: any) => {
          let content = `<strong>${params[0].axisValue}</strong><br/>`;
          params.forEach((param: any) => {
            const seriesConfig = series.find(s => s.name === param.seriesName);
            const unit = seriesConfig?.unit || '';
            content += `${param.marker} ${param.seriesName}: ${param.value}${unit}<br/>`;
          });
          return content;
        }
      },
      legend: {
        data: filteredSeries.map(s => s.name),
        bottom: enableDataZoom ? 60 : 10,
        selected: visibleSeries
      },
      grid: {
        left: '10%',
        right: '10%',
        bottom: enableDataZoom ? '20%' : '10%',
        top: '15%',
        containLabel: true
      },
      toolbox: {
        feature: {
          dataView: { show: true, readOnly: false },
          magicType: { show: true, type: ['line', 'bar'] },
          restore: { show: true },
          saveAsImage: { show: true }
        },
        right: '2%',
        top: '2%'
      },
      xAxis: {
        type: 'category',
        data: xAxisData,
        axisPointer: {
          type: 'shadow'
        },
        axisLabel: {
          rotate: 45
        }
      },
      yAxis: yAxes.map((yAxis, index) => ({
        type: 'value',
        name: yAxis.name,
        position: yAxis.position,
        min: yAxis.min,
        max: yAxis.max,
        axisLabel: {
          formatter: `{value} ${yAxis.unit}`,
          color: yAxis.color || '#666'
        },
        axisLine: {
          lineStyle: {
            color: yAxis.color || '#666'
          }
        },
        splitLine: {
          show: index === 0,
          lineStyle: {
            color: '#e8e8e8',
            type: 'dashed'
          }
        }
      })),
      dataZoom: enableDataZoom ? [
        {
          type: 'slider',
          show: true,
          xAxisIndex: [0],
          start: 0,
          end: 100,
          bottom: '5%'
        },
        {
          type: 'inside',
          xAxisIndex: [0],
          start: 0,
          end: 100
        }
      ] : undefined,
      brush: enableBrush ? {
        toolbox: ['rect', 'polygon', 'lineX', 'lineY', 'keep', 'clear'],
        xAxisIndex: 0
      } : undefined,
      series: filteredSeries.map((s, index) => ({
        name: s.name,
        type: s.type,
        yAxisIndex: s.yAxisIndex,
        data: s.data,
        smooth: s.smooth,
        stack: s.stack,
        itemStyle: {
          color: s.color || CHART_COLORS.primary
        },
        lineStyle: s.type === 'line' ? {
          width: 2,
          color: s.color || CHART_COLORS.primary
        } : undefined,
        areaStyle: s.type === 'line' && !s.stack ? {
          color: {
            type: 'linear',
            x: 0,
            y: 0,
            x2: 0,
            y2: 1,
            colorStops: [
              {
                offset: 0,
                color: (s.color || CHART_COLORS.primary) + '40'
              },
              {
                offset: 1,
                color: (s.color || CHART_COLORS.primary) + '10'
              }
            ]
          }
        } : undefined,
        markPoint: {
          data: [
            { type: 'max', name: '最大值' },
            { type: 'min', name: '最小值' }
          ]
        },
        markLine: {
          data: [
            { type: 'average', name: '平均值' }
          ]
        }
      }))
    };
  };

  const getSeriesStats = () => {
    return series.map(s => {
      const values = s.data.filter(v => v !== null && v !== undefined);
      if (values.length === 0) return { name: s.name, avg: 0, max: 0, min: 0, unit: s.unit || '' };
      
      const sum = values.reduce((acc, val) => acc + val, 0);
      const avg = sum / values.length;
      const max = Math.max(...values);
      const min = Math.min(...values);
      
      return {
        name: s.name,
        avg: avg.toFixed(2),
        max,
        min,
        unit: s.unit || ''
      };
    });
  };

  const stats = getSeriesStats();

  return (
    <div>
      <Card size="small" style={{ marginBottom: 16 }}>
        <Space wrap>
          <span>图表控制:</span>
          <Space>
            <span>数据缩放:</span>
            <Switch 
              checked={enableDataZoom} 
              onChange={setEnableDataZoom}
              size="small"
            />
          </Space>
          <Space>
            <span>数据刷选:</span>
            <Switch 
              checked={enableBrush} 
              onChange={setEnableBrush}
              size="small"
            />
          </Space>
          <Tooltip title="点击图例可以显示/隐藏对应的数据系列">
            <InfoCircleOutlined style={{ color: '#1890ff' }} />
          </Tooltip>
        </Space>
      </Card>

      <Card>
        <div style={{ marginBottom: 16, padding: '12px', backgroundColor: '#f5f5f5', borderRadius: '6px' }}>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '16px' }}>
            {stats.map((stat, index) => (
              <div key={index} style={{ textAlign: 'center' }}>
                <div style={{ fontSize: '14px', fontWeight: 'bold', marginBottom: '8px' }}>
                  {stat.name}
                </div>
                <div style={{ display: 'flex', justifyContent: 'space-around', fontSize: '12px' }}>
                  <div>
                    <div style={{ color: '#666' }}>平均</div>
                    <div style={{ fontWeight: 'bold' }}>{stat.avg}{stat.unit}</div>
                  </div>
                  <div>
                    <div style={{ color: '#666' }}>最大</div>
                    <div style={{ fontWeight: 'bold', color: '#ff4d4f' }}>{stat.max}{stat.unit}</div>
                  </div>
                  <div>
                    <div style={{ color: '#666' }}>最小</div>
                    <div style={{ fontWeight: 'bold', color: '#52c41a' }}>{stat.min}{stat.unit}</div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
        
        <ReactECharts
          option={getOption()}
          style={{ height: `${height}px` }}
          notMerge={true}
          lazyUpdate={true}
          onEvents={{
            legendselectchanged: (params: any) => {
              setVisibleSeries(params.selected);
            }
          }}
        />
      </Card>
    </div>
  );
};

export default MultiAxisChart;