import React, { useEffect, useRef, useState } from 'react';
import { Card, Button, Space, Select, DatePicker, message, Spin, Tooltip } from 'antd';
import { FullscreenOutlined, ReloadOutlined, SettingOutlined } from '@ant-design/icons';
import * as echarts from 'echarts';
import dayjs from 'dayjs';
import './index.less';

const { Option } = Select;
const { RangePicker } = DatePicker;

interface GanttTask {
  id: number;
  name: string;
  start: string;
  end: string;
  resource: string;
  progress: number;
  priority: string;
  status: string;
  utilization: number;
}

interface GanttResource {
  id: string;
  name: string;
}

interface GanttData {
  tasks: GanttTask[];
  resources: GanttResource[];
  timeline: {
    start: string;
    end: string;
  };
}

interface GanttChartProps {
  data: GanttData;
  loading?: boolean;
  height?: number;
  onTaskClick?: (task: GanttTask) => void;
  onRefresh?: () => void;
}

const GanttChart: React.FC<GanttChartProps> = ({
  data,
  loading = false,
  height = 400,
  onTaskClick,
  onRefresh
}) => {
  const chartRef = useRef<HTMLDivElement>(null);
  const chartInstance = useRef<echarts.ECharts | null>(null);
  const [viewMode, setViewMode] = useState<'day' | 'week' | 'month'>('week');
  const [selectedResource, setSelectedResource] = useState<string>('all');
  const [dateRange, setDateRange] = useState<[dayjs.Dayjs, dayjs.Dayjs] | null>(null);

  // 状态颜色映射
  const statusColors = {
    '草稿': '#d9d9d9',
    '已确认': '#1890ff',
    '进行中': '#52c41a',
    '已完成': '#13c2c2',
    '已取消': '#ff4d4f',
    '暂停': '#fa8c16'
  };

  // 优先级颜色映射
  const priorityColors = {
    '紧急': '#ff4d4f',
    '高': '#fa8c16',
    '中': '#1890ff',
    '低': '#52c41a'
  };

  useEffect(() => {
    if (chartRef.current && data.tasks.length > 0) {
      initChart();
    }
    return () => {
      if (chartInstance.current) {
        chartInstance.current.dispose();
      }
    };
  }, [data, viewMode, selectedResource, dateRange]);

  const initChart = () => {
    if (!chartRef.current) return;

    // 销毁现有图表
    if (chartInstance.current) {
      chartInstance.current.dispose();
    }

    // 创建新图表
    chartInstance.current = echarts.init(chartRef.current);

    // 处理数据
    const processedData = processGanttData();
    
    // 配置图表选项
    const option = {
      title: {
        text: '生产计划甘特图',
        left: 'center',
        textStyle: {
          fontSize: 16,
          fontWeight: 'bold'
        }
      },
      tooltip: {
        trigger: 'item',
        formatter: (params: any) => {
          const task = params.data.task;
          if (!task) return '';
          
          return `
            <div style="padding: 8px;">
              <div style="font-weight: bold; margin-bottom: 4px;">${task.name}</div>
              <div>开始时间: ${dayjs(task.start).format('YYYY-MM-DD HH:mm')}</div>
              <div>结束时间: ${dayjs(task.end).format('YYYY-MM-DD HH:mm')}</div>
              <div>执行车间: ${task.resource}</div>
              <div>完成进度: ${task.progress}%</div>
              <div>优先级: ${task.priority}</div>
              <div>状态: ${task.status}</div>
              <div>资源利用率: ${(task.utilization * 100).toFixed(1)}%</div>
            </div>
          `;
        }
      },
      grid: {
        left: '15%',
        right: '10%',
        top: '15%',
        bottom: '10%'
      },
      xAxis: {
        type: 'time',
        axisLabel: {
          formatter: (value: number) => {
            const date = new Date(value);
            if (viewMode === 'day') {
              return dayjs(date).format('MM-DD');
            } else if (viewMode === 'week') {
              return dayjs(date).format('MM-DD');
            } else {
              return dayjs(date).format('MM-DD');
            }
          }
        },
        splitLine: {
          show: true,
          lineStyle: {
            color: '#e8e8e8',
            type: 'dashed'
          }
        }
      },
      yAxis: {
        type: 'category',
        data: processedData.categories,
        axisLabel: {
          formatter: (value: string) => {
            return value.length > 15 ? value.substring(0, 15) + '...' : value;
          }
        },
        splitLine: {
          show: true,
          lineStyle: {
            color: '#e8e8e8'
          }
        }
      },
      series: [
        {
          type: 'custom',
          renderItem: renderGanttItem,
          encode: {
            x: [1, 2],
            y: 0
          },
          data: processedData.data
        }
      ]
    };

    chartInstance.current.setOption(option);

    // 添加点击事件
    chartInstance.current.on('click', (params: any) => {
      if (params.data && params.data.task && onTaskClick) {
        onTaskClick(params.data.task);
      }
    });

    // 响应式调整
    const resizeChart = () => {
      if (chartInstance.current) {
        chartInstance.current.resize();
      }
    };

    window.addEventListener('resize', resizeChart);
    return () => window.removeEventListener('resize', resizeChart);
  };

  const processGanttData = () => {
    let filteredTasks = data.tasks;

    // 按资源过滤
    if (selectedResource !== 'all') {
      filteredTasks = filteredTasks.filter(task => task.resource === selectedResource);
    }

    // 按日期范围过滤
    if (dateRange) {
      const [startDate, endDate] = dateRange;
      filteredTasks = filteredTasks.filter(task => {
        const taskStart = dayjs(task.start);
        const taskEnd = dayjs(task.end);
        return taskStart.isBefore(endDate) && taskEnd.isAfter(startDate);
      });
    }

    // 按资源分组
    const resourceGroups: { [key: string]: GanttTask[] } = {};
    filteredTasks.forEach(task => {
      if (!resourceGroups[task.resource]) {
        resourceGroups[task.resource] = [];
      }
      resourceGroups[task.resource].push(task);
    });

    // 构建分类和数据
    const categories: string[] = [];
    const chartData: any[] = [];

    Object.keys(resourceGroups).forEach((resource, resourceIndex) => {
      const tasks = resourceGroups[resource];
      
      tasks.forEach((task, taskIndex) => {
        const categoryName = `${resource} - ${task.name}`;
        categories.push(categoryName);
        
        const startTime = new Date(task.start).getTime();
        const endTime = new Date(task.end).getTime();
        
        chartData.push({
          name: task.name,
          value: [categories.length - 1, startTime, endTime],
          task: task,
          itemStyle: {
            color: getTaskColor(task)
          }
        });
      });
    });

    return {
      categories,
      data: chartData
    };
  };

  const getTaskColor = (task: GanttTask): string => {
    // 根据状态和优先级确定颜色
    if (task.status in statusColors) {
      return statusColors[task.status as keyof typeof statusColors];
    }
    return priorityColors[task.priority as keyof typeof priorityColors] || '#1890ff';
  };

  const renderGanttItem = (params: any, api: any) => {
    const categoryIndex = api.value(0);
    const start = api.coord([api.value(1), categoryIndex]);
    const end = api.coord([api.value(2), categoryIndex]);
    const height = api.size([0, 1])[1] * 0.6;
    
    const rectShape = echarts.graphic.clipRectByRect(
      {
        x: start[0],
        y: start[1] - height / 2,
        width: end[0] - start[0],
        height: height
      },
      {
        x: params.coordSys.x,
        y: params.coordSys.y,
        width: params.coordSys.width,
        height: params.coordSys.height
      }
    );

    if (!rectShape) return;

    const task = params.data.task;
    const progress = task ? task.progress / 100 : 0;

    return {
      type: 'group',
      children: [
        // 背景条
        {
          type: 'rect',
          shape: rectShape,
          style: {
            fill: '#f0f0f0',
            stroke: '#d9d9d9',
            lineWidth: 1
          }
        },
        // 进度条
        {
          type: 'rect',
          shape: {
            ...rectShape,
            width: rectShape.width * progress
          },
          style: {
            fill: params.data.itemStyle.color,
            opacity: 0.8
          }
        },
        // 文本标签
        {
          type: 'text',
          style: {
            text: task ? `${task.name} (${task.progress}%)` : '',
            x: rectShape.x + 4,
            y: rectShape.y + rectShape.height / 2,
            textVerticalAlign: 'middle',
            fontSize: 12,
            fill: '#333'
          }
        }
      ]
    };
  };

  const handleViewModeChange = (mode: 'day' | 'week' | 'month') => {
    setViewMode(mode);
  };

  const handleResourceChange = (resource: string) => {
    setSelectedResource(resource);
  };

  const handleDateRangeChange = (dates: any) => {
    setDateRange(dates);
  };

  const handleFullscreen = () => {
    if (chartRef.current) {
      if (chartRef.current.requestFullscreen) {
        chartRef.current.requestFullscreen();
      }
    }
  };

  return (
    <Card
      title="生产计划甘特图"
      extra={
        <Space>
          <Select
            value={viewMode}
            onChange={handleViewModeChange}
            style={{ width: 80 }}
          >
            <Option value="day">日视图</Option>
            <Option value="week">周视图</Option>
            <Option value="month">月视图</Option>
          </Select>
          
          <Select
            value={selectedResource}
            onChange={handleResourceChange}
            style={{ width: 120 }}
            placeholder="选择车间"
          >
            <Option value="all">全部车间</Option>
            {data.resources.map(resource => (
              <Option key={resource.id} value={resource.id}>
                {resource.name}
              </Option>
            ))}
          </Select>
          
          <RangePicker
            value={dateRange}
            onChange={handleDateRangeChange}
            style={{ width: 240 }}
            placeholder={['开始日期', '结束日期']}
          />
          
          <Tooltip title="刷新">
            <Button icon={<ReloadOutlined />} onClick={onRefresh} />
          </Tooltip>
          
          <Tooltip title="全屏">
            <Button icon={<FullscreenOutlined />} onClick={handleFullscreen} />
          </Tooltip>
        </Space>
      }
      className="gantt-chart-card"
    >
      <Spin spinning={loading}>
        <div
          ref={chartRef}
          style={{ width: '100%', height: `${height}px` }}
          className="gantt-chart-container"
        />
      </Spin>
    </Card>
  );
};

export default GanttChart;