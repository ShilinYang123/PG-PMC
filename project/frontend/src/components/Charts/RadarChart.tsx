import React from 'react';
import ReactECharts from 'echarts-for-react';
import { Card, Table, Tag } from 'antd';
import { CHART_COLORS } from './types';

interface RadarDataItem {
  name: string;
  values: number[];
  color?: string;
}

interface RadarIndicator {
  name: string;
  max: number;
  unit?: string;
}

interface RadarChartProps {
  data: RadarDataItem[];
  indicators: RadarIndicator[];
  title?: string;
  height?: number;
  showTable?: boolean;
}

const RadarChart: React.FC<RadarChartProps> = ({ 
  data, 
  indicators,
  title = '多维度分析',
  height = 400,
  showTable = true
}) => {
  const getOption = () => {
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
        trigger: 'item',
        formatter: (params: any) => {
          const dataIndex = params.dataIndex;
          const seriesIndex = params.seriesIndex;
          const item = data[seriesIndex];
          let content = `<strong>${item.name}</strong><br/>`;
          
          indicators.forEach((indicator, index) => {
            const value = item.values[index];
            const percentage = ((value / indicator.max) * 100).toFixed(1);
            content += `${indicator.name}: ${value}${indicator.unit || ''} (${percentage}%)<br/>`;
          });
          
          return content;
        }
      },
      legend: {
        data: data.map(item => item.name),
        bottom: 10
      },
      radar: {
        indicator: indicators.map(indicator => ({
          name: indicator.name,
          max: indicator.max
        })),
        center: ['50%', '50%'],
        radius: '60%',
        axisName: {
          color: '#666',
          fontSize: 12
        },
        splitLine: {
          lineStyle: {
            color: '#e8e8e8'
          }
        },
        splitArea: {
          show: true,
          areaStyle: {
            color: ['rgba(250,250,250,0.1)', 'rgba(200,200,200,0.1)']
          }
        }
      },
      series: [
        {
          type: 'radar',
          data: data.map((item, index) => ({
            value: item.values,
            name: item.name,
            itemStyle: {
              color: item.color || CHART_COLORS.primary
            },
            areaStyle: {
              color: (item.color || CHART_COLORS.primary) + '20'
            },
            lineStyle: {
              width: 2
            }
          }))
        }
      ]
    };
  };

  const getScoreLevel = (value: number, max: number) => {
    const percentage = (value / max) * 100;
    if (percentage >= 80) return { level: '优秀', color: 'success' };
    if (percentage >= 60) return { level: '良好', color: 'processing' };
    if (percentage >= 40) return { level: '一般', color: 'warning' };
    return { level: '较差', color: 'error' };
  };

  const tableColumns = [
    {
      title: '项目',
      dataIndex: 'name',
      key: 'name',
      width: 120
    },
    ...indicators.map((indicator, index) => ({
      title: indicator.name,
      key: indicator.name,
      width: 100,
      render: (_: any, record: any) => {
        const value = record.values[index];
        const { level, color } = getScoreLevel(value, indicator.max);
        return (
          <div>
            <div>{value}{indicator.unit || ''}</div>
            <Tag color={color}>{level}</Tag>
          </div>
        );
      }
    })),
    {
      title: '综合评分',
      key: 'total',
      width: 100,
      render: (_: any, record: any) => {
        const total = record.values.reduce((sum: number, value: number, index: number) => {
          return sum + (value / indicators[index].max) * 100;
        }, 0);
        const average = total / indicators.length;
        const { level, color } = getScoreLevel(average, 100);
        return (
          <div>
            <div style={{ fontWeight: 'bold' }}>{average.toFixed(1)}</div>
            <Tag color={color}>{level}</Tag>
          </div>
        );
      }
    }
  ];

  const tableData = data.map((item, index) => ({
    key: index,
    name: item.name,
    values: item.values
  }));

  return (
    <div>
      <Card>
        <ReactECharts
          option={getOption()}
          style={{ height: `${height}px` }}
          notMerge={true}
          lazyUpdate={true}
        />
      </Card>
      
      {showTable && (
        <Card title="详细数据" style={{ marginTop: 16 }}>
          <Table
            columns={tableColumns}
            dataSource={tableData}
            pagination={false}
            size="small"
            scroll={{ x: 'max-content' }}
          />
        </Card>
      )}
    </div>
  );
};

export default RadarChart;