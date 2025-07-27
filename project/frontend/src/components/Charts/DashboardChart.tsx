import React from 'react';
import ReactECharts from 'echarts-for-react';
import { Card, Row, Col, Statistic, Progress } from 'antd';
import { CHART_COLORS } from './types';

interface DashboardData {
  title: string;
  value: number;
  max: number;
  unit: string;
  status: 'normal' | 'warning' | 'critical';
  trend?: number; // 趋势百分比
}

interface DashboardChartProps {
  data: DashboardData[];
  title?: string;
  height?: number;
}

const DashboardChart: React.FC<DashboardChartProps> = ({ 
  data, 
  title = '仪表盘监控',
  height = 400 
}) => {
  const getGaugeOption = (item: DashboardData, index: number) => {
    const percentage = (item.value / item.max) * 100;
    
    return {
      series: [
        {
          type: 'gauge',
          center: ['50%', '60%'],
          radius: '70%',
          min: 0,
          max: item.max,
          splitNumber: 5,
          axisLine: {
            lineStyle: {
              width: 6,
              color: [
                [0.3, '#67e0e3'],
                [0.7, '#37a2da'],
                [1, '#fd666d']
              ]
            }
          },
          pointer: {
            itemStyle: {
              color: 'auto'
            }
          },
          axisTick: {
            distance: -30,
            length: 8,
            lineStyle: {
              color: '#fff',
              width: 2
            }
          },
          splitLine: {
            distance: -30,
            length: 30,
            lineStyle: {
              color: '#fff',
              width: 4
            }
          },
          axisLabel: {
            color: 'auto',
            distance: 40,
            fontSize: 12
          },
          detail: {
            valueAnimation: true,
            formatter: `{value} ${item.unit}`,
            color: 'auto',
            fontSize: 16,
            offsetCenter: [0, '70%']
          },
          data: [
            {
              value: item.value,
              name: item.title
            }
          ]
        }
      ]
    };
  };

  const getStatusColor = (status: string) => {
    const colorMap = {
      normal: '#52c41a',
      warning: '#faad14',
      critical: '#ff4d4f'
    };
    return colorMap[status as keyof typeof colorMap] || '#1890ff';
  };

  const getStatusText = (status: string) => {
    const statusMap = {
      normal: '正常',
      warning: '警告',
      critical: '严重'
    };
    return statusMap[status as keyof typeof statusMap] || status;
  };

  const getTrendIcon = (trend?: number) => {
    if (!trend) return null;
    if (trend > 0) return '↗';
    if (trend < 0) return '↘';
    return '→';
  };

  const getTrendColor = (trend?: number) => {
    if (!trend) return '#666';
    if (trend > 0) return '#52c41a';
    if (trend < 0) return '#ff4d4f';
    return '#666';
  };

  return (
    <Card title={title}>
      <Row gutter={[16, 16]}>
        {data.map((item, index) => (
          <Col span={12} key={index}>
            <Card 
              size="small" 
              title={
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <span>{item.title}</span>
                  <span style={{ 
                    fontSize: '12px', 
                    color: getStatusColor(item.status),
                    fontWeight: 'normal'
                  }}>
                    {getStatusText(item.status)}
                  </span>
                </div>
              }
            >
              <div style={{ display: 'flex', alignItems: 'center' }}>
                <div style={{ flex: 1 }}>
                  <ReactECharts
                    option={getGaugeOption(item, index)}
                    style={{ height: '200px', width: '100%' }}
                    notMerge={true}
                    lazyUpdate={true}
                  />
                </div>
                <div style={{ width: '120px', paddingLeft: '16px' }}>
                  <Statistic
                    title="当前值"
                    value={item.value}
                    suffix={item.unit}
                    valueStyle={{ fontSize: '18px' }}
                  />
                  <div style={{ marginTop: '8px' }}>
                    <Progress
                      percent={(item.value / item.max) * 100}
                      size="small"
                      strokeColor={getStatusColor(item.status)}
                      showInfo={false}
                    />
                    <div style={{ 
                      fontSize: '12px', 
                      color: '#666', 
                      marginTop: '4px',
                      display: 'flex',
                      justifyContent: 'space-between'
                    }}>
                      <span>0</span>
                      <span>{item.max}</span>
                    </div>
                  </div>
                  {item.trend !== undefined && (
                    <div style={{ 
                      marginTop: '8px',
                      fontSize: '12px',
                      color: getTrendColor(item.trend)
                    }}>
                      {getTrendIcon(item.trend)} {Math.abs(item.trend)}%
                    </div>
                  )}
                </div>
              </div>
            </Card>
          </Col>
        ))}
      </Row>
    </Card>
  );
};

export default DashboardChart;