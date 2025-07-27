import React from 'react';
import ReactECharts from 'echarts-for-react';
import { Card } from 'antd';
import { OrderStatusData, ChartConfig } from './types';

interface OrderStatusChartProps {
  data: OrderStatusData[];
  config?: ChartConfig;
}

const OrderStatusChart: React.FC<OrderStatusChartProps> = ({ 
  data, 
  config = {} 
}) => {
  const {
    title = '订单状态分布',
    height = 400,
    showLegend = true,
    showTooltip = true
  } = config;

  const getOption = () => {
    const pieData = data.map(item => ({
      name: getStatusText(item.status),
      value: item.count,
      itemStyle: {
        color: item.color
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
        trigger: 'item',
        formatter: (params: any) => {
          const item = data.find(d => getStatusText(d.status) === params.name);
          return `
            <div>
              <strong>${params.name}</strong><br/>
              数量: ${params.value}<br/>
              占比: ${item?.percentage.toFixed(1)}%
            </div>
          `;
        }
      } : undefined,
      legend: showLegend ? {
        orient: 'vertical',
        left: 'left',
        data: pieData.map(item => item.name)
      } : undefined,
      series: [
        {
          name: '订单状态',
          type: 'pie',
          radius: ['40%', '70%'],
          center: ['60%', '50%'],
          avoidLabelOverlap: false,
          label: {
            show: true,
            position: 'outside',
            formatter: '{b}: {c}\n({d}%)'
          },
          emphasis: {
            label: {
              show: true,
              fontSize: '14',
              fontWeight: 'bold'
            }
          },
          labelLine: {
            show: true
          },
          data: pieData
        }
      ]
    };
  };

  const getStatusText = (status: string) => {
    const statusMap = {
      pending: '待处理',
      confirmed: '已确认',
      in_production: '生产中',
      quality_check: '质检中',
      completed: '已完成',
      shipped: '已发货',
      cancelled: '已取消'
    };
    return statusMap[status as keyof typeof statusMap] || status;
  };

  const getTotalOrders = () => {
    return data.reduce((total, item) => total + item.count, 0);
  };

  return (
    <Card 
      title={`订单总数: ${getTotalOrders()}`}
      extra={
        <div style={{ fontSize: '12px', color: '#666' }}>
          更新时间: {new Date().toLocaleString()}
        </div>
      }
    >
      <ReactECharts
        option={getOption()}
        style={{ height: `${height}px` }}
        notMerge={true}
        lazyUpdate={true}
      />
    </Card>
  );
};

export default OrderStatusChart;