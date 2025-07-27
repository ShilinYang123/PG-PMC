import React from 'react';
import ReactECharts from 'echarts-for-react';
import { Card } from 'antd';
import { QualityTrendData, ChartConfig, CHART_COLORS } from './types';

interface QualityTrendChartProps {
  data: QualityTrendData[];
  config?: ChartConfig;
}

const QualityTrendChart: React.FC<QualityTrendChartProps> = ({ 
  data, 
  config = {} 
}) => {
  const {
    title = '质量趋势分析',
    height = 400,
    showLegend = true,
    showTooltip = true
  } = config;

  const getOption = () => {
    const xAxisData = data.map(item => item.date);
    const passRateData = data.map(item => item.passRate);
    const defectRateData = data.map(item => item.defectRate);
    const reworkRateData = data.map(item => item.reworkRate);

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
              <strong>日期: ${item.date}</strong><br/>
              合格率: ${item.passRate}%<br/>
              不良率: ${item.defectRate}%<br/>
              返工率: ${item.reworkRate}%<br/>
              检验总数: ${item.totalInspected}
            </div>
          `;
        }
      } : undefined,
      legend: showLegend ? {
        data: ['合格率', '不良率', '返工率'],
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
          rotate: 45
        }
      },
      yAxis: [
        {
          type: 'value',
          name: '百分比(%)',
          min: 0,
          max: 100,
          position: 'left',
          axisLabel: {
            formatter: '{value}%'
          }
        }
      ],
      series: [
        {
          name: '合格率',
          type: 'line',
          data: passRateData,
          smooth: true,
          lineStyle: {
            color: CHART_COLORS.success,
            width: 3
          },
          itemStyle: {
            color: CHART_COLORS.success
          },
          areaStyle: {
            color: {
              type: 'linear',
              x: 0,
              y: 0,
              x2: 0,
              y2: 1,
              colorStops: [
                {
                  offset: 0,
                  color: CHART_COLORS.success + '40'
                },
                {
                  offset: 1,
                  color: CHART_COLORS.success + '10'
                }
              ]
            }
          },
          markLine: {
            data: [
              {
                yAxis: 95,
                lineStyle: {
                  color: CHART_COLORS.success,
                  type: 'dashed'
                },
                label: {
                  formatter: '目标合格率: 95%'
                }
              }
            ]
          }
        },
        {
          name: '不良率',
          type: 'line',
          data: defectRateData,
          smooth: true,
          lineStyle: {
            color: CHART_COLORS.error,
            width: 2
          },
          itemStyle: {
            color: CHART_COLORS.error
          },
          markLine: {
            data: [
              {
                yAxis: 3,
                lineStyle: {
                  color: CHART_COLORS.error,
                  type: 'dashed'
                },
                label: {
                  formatter: '不良率警戒线: 3%'
                }
              }
            ]
          }
        },
        {
          name: '返工率',
          type: 'line',
          data: reworkRateData,
          smooth: true,
          lineStyle: {
            color: CHART_COLORS.warning,
            width: 2
          },
          itemStyle: {
            color: CHART_COLORS.warning
          },
          markLine: {
            data: [
              {
                yAxis: 2,
                lineStyle: {
                  color: CHART_COLORS.warning,
                  type: 'dashed'
                },
                label: {
                  formatter: '返工率警戒线: 2%'
                }
              }
            ]
          }
        }
      ]
    };
  };

  const getLatestQuality = () => {
    if (data.length === 0) return null;
    return data[data.length - 1];
  };

  const getAverageQuality = () => {
    if (data.length === 0) return { passRate: 0, defectRate: 0, reworkRate: 0 };
    
    const totals = data.reduce(
      (acc, item) => ({
        passRate: acc.passRate + item.passRate,
        defectRate: acc.defectRate + item.defectRate,
        reworkRate: acc.reworkRate + item.reworkRate
      }),
      { passRate: 0, defectRate: 0, reworkRate: 0 }
    );

    return {
      passRate: (totals.passRate / data.length).toFixed(1),
      defectRate: (totals.defectRate / data.length).toFixed(1),
      reworkRate: (totals.reworkRate / data.length).toFixed(1)
    };
  };

  const latest = getLatestQuality();
  const average = getAverageQuality();

  return (
    <Card 
      title="质量指标概览"
      extra={
        latest && (
          <div style={{ fontSize: '12px', color: '#666' }}>
            最新数据: {latest.date} | 合格率: {latest.passRate}%
          </div>
        )
      }
    >
      <div style={{ marginBottom: 16, padding: '12px', backgroundColor: '#f5f5f5', borderRadius: '6px' }}>
        <div style={{ display: 'flex', justifyContent: 'space-around', textAlign: 'center' }}>
          <div>
            <div style={{ fontSize: '12px', color: '#666' }}>平均合格率</div>
            <div style={{ fontSize: '18px', fontWeight: 'bold', color: CHART_COLORS.success }}>
              {average.passRate}%
            </div>
          </div>
          <div>
            <div style={{ fontSize: '12px', color: '#666' }}>平均不良率</div>
            <div style={{ fontSize: '18px', fontWeight: 'bold', color: CHART_COLORS.error }}>
              {average.defectRate}%
            </div>
          </div>
          <div>
            <div style={{ fontSize: '12px', color: '#666' }}>平均返工率</div>
            <div style={{ fontSize: '18px', fontWeight: 'bold', color: CHART_COLORS.warning }}>
              {average.reworkRate}%
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
  );
};

export default QualityTrendChart;