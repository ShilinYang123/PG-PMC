import React from 'react';
import ReactECharts from 'echarts-for-react';
import { Card, Row, Col, Statistic } from 'antd';
import { EquipmentStatusData, ChartConfig, STATUS_COLORS } from './types';

interface EquipmentStatusChartProps {
  data: EquipmentStatusData[];
  config?: ChartConfig;
}

const EquipmentStatusChart: React.FC<EquipmentStatusChartProps> = ({ 
  data, 
  config = {} 
}) => {
  const {
    title = '设备状态监控',
    height = 400,
    showLegend = true,
    showTooltip = true
  } = config;

  const getOption = () => {
    const xAxisData = data.map(item => item.equipmentName);
    const utilizationData = data.map(item => ({
      value: item.utilization,
      itemStyle: {
        color: STATUS_COLORS[item.status]
      }
    }));

    return {
      title: {
        text: title,
        left: 'center',
        textStyle: {
          fontSize: 16,
          fontWeight: 'bold'
        }
      },
      tooltip: showTooltip ? {
        trigger: 'axis',
        formatter: (params: any) => {
          const dataIndex = params[0].dataIndex;
          const item = data[dataIndex];
          return `
            <div>
              <strong>${item.equipmentName}</strong><br/>
              设备编号: ${item.equipmentId}<br/>
              状态: ${getStatusText(item.status)}<br/>
              利用率: ${item.utilization}%<br/>
              上次维护: ${item.lastMaintenance}<br/>
              下次维护: ${item.nextMaintenance}
            </div>
          `;
        }
      } : undefined,
      legend: showLegend ? {
        data: ['设备利用率'],
        bottom: 10
      } : undefined,
      grid: {
        left: '3%',
        right: '4%',
        bottom: showLegend ? '15%' : '3%',
        containLabel: true
      },
      xAxis: {
        type: 'category',
        data: xAxisData,
        axisLabel: {
          rotate: 45,
          interval: 0
        }
      },
      yAxis: {
        type: 'value',
        min: 0,
        max: 100,
        axisLabel: {
          formatter: '{value}%'
        }
      },
      series: [
        {
          name: '设备利用率',
          type: 'bar',
          data: utilizationData,
          label: {
            show: true,
            position: 'top',
            formatter: '{c}%'
          },
          markLine: {
            data: [
              {
                yAxis: 85,
                lineStyle: {
                  color: '#52c41a',
                  type: 'dashed'
                },
                label: {
                  formatter: '目标利用率: 85%'
                }
              },
              {
                yAxis: 60,
                lineStyle: {
                  color: '#faad14',
                  type: 'dashed'
                },
                label: {
                  formatter: '警戒线: 60%'
                }
              }
            ]
          }
        }
      ]
    };
  };

  const getStatusText = (status: string) => {
    const statusMap = {
      running: '运行中',
      idle: '空闲',
      maintenance: '维护中',
      error: '故障'
    };
    return statusMap[status as keyof typeof statusMap] || status;
  };

  const getStatusStats = () => {
    const stats = data.reduce((acc, item) => {
      acc[item.status] = (acc[item.status] || 0) + 1;
      return acc;
    }, {} as Record<string, number>);

    return {
      total: data.length,
      running: stats.running || 0,
      idle: stats.idle || 0,
      maintenance: stats.maintenance || 0,
      error: stats.error || 0
    };
  };

  const getAverageUtilization = () => {
    if (data.length === 0) return 0;
    const total = data.reduce((sum, item) => sum + item.utilization, 0);
    return (total / data.length).toFixed(1);
  };

  const stats = getStatusStats();

  return (
    <div>
      <Row gutter={16} style={{ marginBottom: 16 }}>
        <Col span={6}>
          <Card>
            <Statistic 
              title="设备总数" 
              value={stats.total} 
              valueStyle={{ color: '#1890ff' }}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic 
              title="运行中" 
              value={stats.running} 
              valueStyle={{ color: '#52c41a' }}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic 
              title="故障设备" 
              value={stats.error} 
              valueStyle={{ color: '#ff4d4f' }}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic 
              title="平均利用率" 
              value={getAverageUtilization()} 
              suffix="%"
              valueStyle={{ color: '#722ed1' }}
            />
          </Card>
        </Col>
      </Row>
      
      <Card>
        <ReactECharts
          option={getOption()}
          style={{ height: `${height}px` }}
          notMerge={true}
          lazyUpdate={true}
        />
      </Card>
    </div>
  );
};

export default EquipmentStatusChart;