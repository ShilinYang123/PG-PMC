import React from 'react';
import ReactECharts from 'echarts-for-react';
import { Card } from 'antd';
import { ProductionProgressData, ChartConfig, STATUS_COLORS } from './types';

interface ProductionProgressChartProps {
  data: ProductionProgressData[];
  config?: ChartConfig;
}

const ProductionProgressChart: React.FC<ProductionProgressChartProps> = ({ 
  data, 
  config = {} 
}) => {
  const {
    title = '生产进度统计',
    height = 400,
    showLegend = true,
    showTooltip = true
  } = config;

  const getOption = () => {
    const xAxisData = data.map(item => item.orderName);
    const progressData = data.map(item => item.progress);
    const statusData = data.map(item => ({
      value: item.progress,
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
              <strong>${item.orderName}</strong><br/>
              订单编号: ${item.orderId}<br/>
              总数量: ${item.totalQuantity}<br/>
              已完成: ${item.completedQuantity}<br/>
              进度: ${item.progress}%<br/>
              状态: ${getStatusText(item.status)}<br/>
              开始日期: ${item.startDate}<br/>
              结束日期: ${item.endDate}
            </div>
          `;
        }
      } : undefined,
      legend: showLegend ? {
        data: ['生产进度'],
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
          name: '生产进度',
          type: 'bar',
          data: statusData,
          label: {
            show: true,
            position: 'top',
            formatter: '{c}%'
          },
          markLine: {
            data: [
              {
                yAxis: 80,
                lineStyle: {
                  color: '#52c41a',
                  type: 'dashed'
                },
                label: {
                  formatter: '目标进度: 80%'
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
      pending: '待开始',
      in_progress: '进行中',
      completed: '已完成',
      delayed: '延期'
    };
    return statusMap[status as keyof typeof statusMap] || status;
  };

  return (
    <Card>
      <ReactECharts
        option={getOption()}
        style={{ height: `${height}px` }}
        notMerge={true}
        lazyUpdate={true}
      />
    </Card>
  );
};

export default ProductionProgressChart;