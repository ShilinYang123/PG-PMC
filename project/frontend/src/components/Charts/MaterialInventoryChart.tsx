import React from 'react';
import ReactECharts from 'echarts-for-react';
import { Card, Alert, Tag } from 'antd';
import { MaterialInventoryData, ChartConfig, STATUS_COLORS } from './types';

interface MaterialInventoryChartProps {
  data: MaterialInventoryData[];
  config?: ChartConfig;
}

const MaterialInventoryChart: React.FC<MaterialInventoryChartProps> = ({ 
  data, 
  config = {} 
}) => {
  const {
    title = '物料库存状态',
    height = 400,
    showLegend = true,
    showTooltip = true
  } = config;

  const getOption = () => {
    const xAxisData = data.map(item => item.materialName);
    const currentStockData = data.map(item => ({
      value: item.currentStock,
      itemStyle: {
        color: STATUS_COLORS[item.status]
      }
    }));
    const minStockData = data.map(item => item.minStock);
    const maxStockData = data.map(item => item.maxStock);

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
              <strong>${item.materialName}</strong><br/>
              物料编号: ${item.materialId}<br/>
              当前库存: ${item.currentStock} ${item.unit}<br/>
              最小库存: ${item.minStock} ${item.unit}<br/>
              最大库存: ${item.maxStock} ${item.unit}<br/>
              状态: ${getStatusText(item.status)}
            </div>
          `;
        }
      } : undefined,
      legend: showLegend ? {
        data: ['当前库存', '最小库存', '最大库存'],
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
        name: '数量',
        min: 0
      },
      series: [
        {
          name: '当前库存',
          type: 'bar',
          data: currentStockData,
          label: {
            show: true,
            position: 'top',
            formatter: (params: any) => {
              const item = data[params.dataIndex];
              return `${params.value} ${item.unit}`;
            }
          },
          barWidth: '60%'
        },
        {
          name: '最小库存',
          type: 'line',
          data: minStockData,
          lineStyle: {
            color: STATUS_COLORS.error,
            type: 'dashed',
            width: 2
          },
          itemStyle: {
            color: STATUS_COLORS.error
          },
          symbol: 'none'
        },
        {
          name: '最大库存',
          type: 'line',
          data: maxStockData,
          lineStyle: {
            color: STATUS_COLORS.success,
            type: 'dashed',
            width: 2
          },
          itemStyle: {
            color: STATUS_COLORS.success
          },
          symbol: 'none'
        }
      ]
    };
  };

  const getStatusText = (status: string) => {
    const statusMap = {
      normal: '正常',
      low: '库存不足',
      critical: '严重不足',
      overstock: '库存过多'
    };
    return statusMap[status as keyof typeof statusMap] || status;
  };

  const getStatusColor = (status: string) => {
    const colorMap = {
      normal: 'success',
      low: 'warning',
      critical: 'error',
      overstock: 'processing'
    };
    return colorMap[status as keyof typeof colorMap] || 'default';
  };

  const getInventoryStats = () => {
    const stats = data.reduce((acc, item) => {
      acc[item.status] = (acc[item.status] || 0) + 1;
      return acc;
    }, {} as Record<string, number>);

    return {
      total: data.length,
      normal: stats.normal || 0,
      low: stats.low || 0,
      critical: stats.critical || 0,
      overstock: stats.overstock || 0
    };
  };

  const getCriticalMaterials = () => {
    return data.filter(item => item.status === 'critical' || item.status === 'low');
  };

  const stats = getInventoryStats();
  const criticalMaterials = getCriticalMaterials();

  return (
    <div>
      {criticalMaterials.length > 0 && (
        <Alert
          message="库存预警"
          description={
            <div>
              以下物料库存不足，请及时补充：
              <div style={{ marginTop: 8 }}>
                {criticalMaterials.map(item => (
                  <Tag 
                    key={item.materialId} 
                    color={getStatusColor(item.status)}
                    style={{ margin: '2px' }}
                  >
                    {item.materialName} ({item.currentStock} {item.unit})
                  </Tag>
                ))}
              </div>
            </div>
          }
          type="warning"
          showIcon
          style={{ marginBottom: 16 }}
        />
      )}

      <Card 
        title="库存概览"
        extra={
          <div style={{ fontSize: '12px', color: '#666' }}>
            总物料数: {stats.total} | 预警物料: {stats.critical + stats.low}
          </div>
        }
      >
        <div style={{ marginBottom: 16, padding: '12px', backgroundColor: '#f5f5f5', borderRadius: '6px' }}>
          <div style={{ display: 'flex', justifyContent: 'space-around', textAlign: 'center' }}>
            <div>
              <div style={{ fontSize: '12px', color: '#666' }}>正常</div>
              <div style={{ fontSize: '18px', fontWeight: 'bold', color: STATUS_COLORS.normal }}>
                {stats.normal}
              </div>
            </div>
            <div>
              <div style={{ fontSize: '12px', color: '#666' }}>库存不足</div>
              <div style={{ fontSize: '18px', fontWeight: 'bold', color: STATUS_COLORS.low }}>
                {stats.low}
              </div>
            </div>
            <div>
              <div style={{ fontSize: '12px', color: '#666' }}>严重不足</div>
              <div style={{ fontSize: '18px', fontWeight: 'bold', color: STATUS_COLORS.critical }}>
                {stats.critical}
              </div>
            </div>
            <div>
              <div style={{ fontSize: '12px', color: '#666' }}>库存过多</div>
              <div style={{ fontSize: '18px', fontWeight: 'bold', color: STATUS_COLORS.overstock }}>
                {stats.overstock}
              </div>
            </div>
          </div>
        </div>
        
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

export default MaterialInventoryChart;