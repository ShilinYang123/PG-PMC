import React, { useState, useEffect } from 'react';
import {
  Card,
  Table,
  Button,
  Space,
  Tag,
  Modal,
  Form,
  Input,
  DatePicker,
  Select,
  Row,
  Col,
  Progress,
  Tooltip,
  Divider,
  message,
  Checkbox,
  Spin,
  Alert,
  List,
  Typography
} from 'antd';
import { productionApi } from '../../services/api';
import {
  PlusOutlined,
  EditOutlined,
  DeleteOutlined,
  CalendarOutlined,
  BarChartOutlined,
  SettingOutlined,
  ThunderboltOutlined,
  ScheduleOutlined,
  ReloadOutlined,
  WarningOutlined
} from '@ant-design/icons';
import ReactECharts from 'echarts-for-react';
import type { ColumnsType } from 'antd/es/table';
import dayjs from 'dayjs';

const { Option } = Select;
const { RangePicker } = DatePicker;
const { Text } = Typography;

interface ProductionPlan {
  key: string;
  planNo: string;
  orderNo: string;
  product: string;
  quantity: number;
  unit: string;
  startDate: string;
  endDate: string;
  status: string;
  progress: number;
  workshop: string;
  operator: string;
  priority: string;
  remark: string;
}

const ProductionPlan: React.FC = () => {
  const [loading, setLoading] = useState(false);
  const [modalVisible, setModalVisible] = useState(false);
  const [ganttVisible, setGanttVisible] = useState(false);
  const [editingRecord, setEditingRecord] = useState<ProductionPlan | null>(null);
  const [form] = Form.useForm();
  
  // 排程相关状态
  const [autoScheduleVisible, setAutoScheduleVisible] = useState(false);
  const [manualScheduleVisible, setManualScheduleVisible] = useState(false);
  const [rescheduleVisible, setRescheduleVisible] = useState(false);
  const [conflictAnalysisVisible, setConflictAnalysisVisible] = useState(false);
  const [schedulingLoading, setSchedulingLoading] = useState(false);
  const [selectedPlans, setSelectedPlans] = useState<string[]>([]);
  const [conflictData, setConflictData] = useState<any[]>([]);
  const [scheduleModalVisible, setScheduleModalVisible] = useState(false);
  const [selectedRowKeys, setSelectedRowKeys] = useState<React.Key[]>([]);
  const [scheduleLoading, setScheduleLoading] = useState(false);
  const [ganttLoading, setGanttLoading] = useState(false);
  const [scheduleForm] = Form.useForm();
  const [ganttData, setGanttData] = useState<any[]>([]);
  const [autoScheduleForm] = Form.useForm();
  const [manualScheduleForm] = Form.useForm();
  const [rescheduleForm] = Form.useForm();

  // 排程策略选项
  const scheduleStrategies = [
    { value: 'priority_first', label: '优先级优先' },
    { value: 'deadline_first', label: '交期优先' },
    { value: 'shortest_first', label: '最短作业优先' },
    { value: 'balanced', label: '平衡策略' }
  ];

  // 生产计划数据
  const [dataSource, setDataSource] = useState<ProductionPlan[]>([]);
  const [planStats, setPlanStats] = useState<any>({});
  const [dashboardData, setDashboardData] = useState<any>({});

  const columns: ColumnsType<ProductionPlan> = [
    {
      title: '计划编号',
      dataIndex: 'planNo',
      key: 'planNo',
      width: 120,
      fixed: 'left'
    },
    {
      title: '订单号',
      dataIndex: 'orderNo',
      key: 'orderNo',
      width: 120
    },
    {
      title: '产品',
      dataIndex: 'product',
      key: 'product',
      width: 120
    },
    {
      title: '数量',
      dataIndex: 'quantity',
      key: 'quantity',
      width: 80,
      render: (value, record) => `${value} ${record.unit}`
    },
    {
      title: '开始日期',
      dataIndex: 'startDate',
      key: 'startDate',
      width: 100
    },
    {
      title: '结束日期',
      dataIndex: 'endDate',
      key: 'endDate',
      width: 100
    },
    {
      title: '车间',
      dataIndex: 'workshop',
      key: 'workshop',
      width: 80
    },
    {
      title: '负责人',
      dataIndex: 'operator',
      key: 'operator',
      width: 80
    },
    {
      title: '优先级',
      dataIndex: 'priority',
      key: 'priority',
      width: 80,
      render: (priority) => {
        let color = 'default';
        if (priority === '高') color = 'red';
        if (priority === '中') color = 'orange';
        if (priority === '低') color = 'green';
        return <Tag color={color}>{priority}</Tag>;
      }
    },
    {
      title: '状态',
      dataIndex: 'status',
      key: 'status',
      width: 100,
      render: (status) => {
        let color = 'default';
        if (status === '进行中') color = 'processing';
        if (status === '已完成') color = 'success';
        if (status === '待开始') color = 'warning';
        if (status === '已暂停') color = 'error';
        return <Tag color={color}>{status}</Tag>;
      }
    },
    {
      title: '进度',
      dataIndex: 'progress',
      key: 'progress',
      width: 120,
      render: (progress) => (
        <Progress percent={progress} size="small" />
      )
    },
    {
      title: '操作',
      key: 'action',
      width: 150,
      fixed: 'right',
      render: (_, record) => (
        <Space size="small">
          <Tooltip title="编辑">
            <Button
              type="link"
              icon={<EditOutlined />}
              onClick={() => handleEdit(record)}
            />
          </Tooltip>
          <Tooltip title="删除">
            <Button
              type="link"
              danger
              icon={<DeleteOutlined />}
              onClick={() => handleDelete(record.key)}
            />
          </Tooltip>
        </Space>
      )
    }
  ];

  // 甘特图配置
  const ganttOption = {
    title: {
      text: '生产计划甘特图',
      left: 'center'
    },
    tooltip: {
      formatter: function(params: any) {
        return `${params.name}<br/>开始: ${params.value[1]}<br/>结束: ${params.value[2]}<br/>进度: ${params.value[3]}%`;
      }
    },
    grid: {
      height: '70%'
    },
    xAxis: {
      type: 'time',
      position: 'top',
      splitLine: {
        lineStyle: {
          color: ['#E9EDFF']
        }
      },
      axisLine: {
        show: false
      },
      axisTick: {
        lineStyle: {
          color: '#929ABA'
        }
      },
      axisLabel: {
        color: '#929ABA',
        inside: false,
        align: 'center'
      }
    },
    yAxis: {
      data: ['PP-2024-001', 'PP-2024-002', 'PP-2024-003']
    },
    series: [
      {
        type: 'custom',
        renderItem: function (params: any, api: any) {
          const categoryIndex = api.value(0);
          const start = api.coord([api.value(1), categoryIndex]);
          const end = api.coord([api.value(2), categoryIndex]);
          const height = api.size([0, 1])[1] * 0.6;
          
          return {
            type: 'rect',
            shape: {
              x: start[0],
              y: start[1] - height / 2,
              width: end[0] - start[0],
              height: height
            },
            style: {
              fill: '#1890ff',
              opacity: 0.8
            }
          };
        },
        data: [
          [0, '2024-01-20', '2024-02-10', 65],
          [1, '2024-02-01', '2024-02-15', 0],
          [2, '2024-01-15', '2024-02-05', 100]
        ]
      }
    ]
  };

  // 产能分析图表配置
  const capacityOption = {
    title: {
      text: '车间产能分析',
      left: 'center'
    },
    tooltip: {
      trigger: 'axis',
      axisPointer: {
        type: 'shadow'
      }
    },
    legend: {
      data: ['计划产能', '实际产能', '利用率'],
      bottom: 0
    },
    xAxis: {
      type: 'category',
      data: ['车间A', '车间B', '车间C', '车间D']
    },
    yAxis: [
      {
        type: 'value',
        name: '产能',
        position: 'left'
      },
      {
        type: 'value',
        name: '利用率(%)',
        position: 'right',
        max: 100
      }
    ],
    series: [
      {
        name: '计划产能',
        type: 'bar',
        data: [1200, 1000, 800, 1500]
      },
      {
        name: '实际产能',
        type: 'bar',
        data: [1100, 950, 750, 1400]
      },
      {
        name: '利用率',
        type: 'line',
        yAxisIndex: 1,
        data: [92, 95, 94, 93]
      }
    ]
  };

  const handleAdd = () => {
    setEditingRecord(null);
    form.resetFields();
    setModalVisible(true);
  };

  const handleEdit = (record: ProductionPlan) => {
    setEditingRecord(record);
    form.setFieldsValue({
      ...record,
      startDate: dayjs(record.startDate),
      endDate: dayjs(record.endDate)
    });
    setModalVisible(true);
  };

  const handleDelete = async (key: string) => {
    try {
      await productionApi.deleteProductionPlan(parseInt(key));
      message.success('删除生产计划成功');
      fetchData();
      fetchStats();
    } catch (error) {
      console.error('删除失败:', error);
      message.error('删除生产计划失败');
    }
  };

  const handleSubmit = async () => {
    try {
      setLoading(true);
      const values = await form.validateFields();
      const formData = {
        plan_number: values.planNo,
        plan_name: values.product,
        order_id: values.orderNo ? parseInt(values.orderNo) : null,
        product_name: values.product,
        product_model: values.product,
        planned_quantity: values.quantity,
        unit: values.unit,
        planned_start_date: values.startDate.format('YYYY-MM-DD'),
        planned_end_date: values.endDate.format('YYYY-MM-DD'),
        workshop: values.workshop,
        responsible_person: values.operator,
        priority: values.priority,
        remark: values.remark
      };

      if (editingRecord) {
        await productionApi.updateProductionPlan(parseInt(editingRecord.key), formData);
        message.success('更新生产计划成功');
      } else {
        await productionApi.createProductionPlan(formData);
        message.success('创建生产计划成功');
      }
      
      setModalVisible(false);
      fetchData();
      fetchStats();
    } catch (error) {
      console.error('保存失败:', error);
      message.error('保存生产计划失败');
    } finally {
      setLoading(false);
    }
  };

  // 排程相关处理函数
  const handleOptimizeSchedule = async () => {
    if (selectedPlans.length === 0) {
      message.warning('请选择要优化的生产计划');
      return;
    }

    try {
      setSchedulingLoading(true);
      // 模拟API调用
      setTimeout(() => {
        message.success('排程优化完成');
        fetchData();
        setSchedulingLoading(false);
      }, 1000);
    } catch (error) {
      console.error('排程优化失败:', error);
      message.error('排程优化失败');
      setSchedulingLoading(false);
    }
  };

  const handleViewGantt = () => {
    if (selectedPlans.length === 0) {
      message.warning('请选择要查看的生产计划');
      return;
    }
    setGanttVisible(true);
  };

  // 手动排程处理函数
  const handleManualSchedule = async () => {
    try {
      const values = await manualScheduleForm.validateFields();
      setSchedulingLoading(true);
      
      // 模拟API调用
      setTimeout(() => {
        message.success('手动排程完成');
        setManualScheduleVisible(false);
        manualScheduleForm.resetFields();
        fetchData();
        setSchedulingLoading(false);
      }, 1000);
    } catch (error) {
      console.error('手动排程失败:', error);
      message.error('手动排程失败');
      setSchedulingLoading(false);
    }
  };

  // 重新排程处理函数
  const handleReschedule = async () => {
    try {
      const values = await rescheduleForm.validateFields();
      setSchedulingLoading(true);
      
      // 模拟API调用
      setTimeout(() => {
        message.success('重新排程完成');
        setRescheduleVisible(false);
        rescheduleForm.resetFields();
        fetchData();
        setSchedulingLoading(false);
      }, 1000);
    } catch (error) {
      console.error('重新排程失败:', error);
      message.error('重新排程失败');
      setSchedulingLoading(false);
    }
  };

  // 自动排程处理函数
  const handleAutoSchedule = async () => {
    try {
      const values = await autoScheduleForm.validateFields();
      setSchedulingLoading(true);
      
      // 模拟API调用
      setTimeout(() => {
        message.success('自动排程完成');
        setAutoScheduleVisible(false);
        autoScheduleForm.resetFields();
        fetchData();
        setSchedulingLoading(false);
      }, 1000);
    } catch (error) {
      console.error('自动排程失败:', error);
      message.error('自动排程失败');
      setSchedulingLoading(false);
    }
  };

  // 获取生产计划数据
  const fetchData = async () => {
    setLoading(true);
    try {
      const response = await productionApi.getProductionPlans();
      if (response.data.code === 200) {
        const plans = response.data.data.map((plan: any) => ({
          key: plan.id.toString(),
          planNo: plan.plan_number,
          orderNo: plan.order_number || '-',
          product: plan.product_name,
          quantity: plan.planned_quantity,
          unit: plan.unit,
          startDate: plan.planned_start_date,
          endDate: plan.planned_end_date,
          status: plan.status,
          progress: plan.progress || 0,
          workshop: plan.workshop,
          operator: plan.responsible_person,
          priority: plan.priority,
          remark: plan.remark || ''
        }));
        setDataSource(plans);
      }
    } catch (error) {
      console.error('获取数据失败:', error);
      message.error('获取生产计划数据失败');
    } finally {
      setLoading(false);
    }
  };

  // 获取统计数据
  const fetchStats = async () => {
    try {
      const response = await productionApi.getProductionStats();
      if (response.data.code === 200) {
        setPlanStats(response.data.data);
      }
    } catch (error) {
      console.error('获取统计数据失败:', error);
    }
  };

  // 获取仪表板数据
  const fetchDashboard = async () => {
    try {
      const response = await productionApi.getDashboard();
      if (response.data.code === 200) {
        setDashboardData(response.data.data);
      }
    } catch (error) {
      console.error('获取仪表板数据失败:', error);
    }
  };

  // 组件初始化
  useEffect(() => {
    fetchData();
    fetchStats();
    fetchDashboard();
  }, []);

  const handleConflictAnalysis = async () => {
    setSchedulingLoading(true);
    
    // 模拟冲突分析数据
    setTimeout(() => {
      const mockConflicts = [
        {
          id: '1',
          type: '资源冲突',
          description: '车间A在2024-02-01至2024-02-05期间资源超负荷',
          severity: 'high',
          affectedPlans: ['PP-2024-001', 'PP-2024-002']
        },
        {
          id: '2',
          type: '时间冲突',
          description: '生产线B的计划时间重叠',
          severity: 'medium',
          affectedPlans: ['PP-2024-003']
        }
      ];
      setConflictData(mockConflicts);
      setSchedulingLoading(false);
      setConflictAnalysisVisible(true);
    }, 1000);
  };

  const rowSelection = {
    selectedRowKeys: selectedPlans,
    onChange: (selectedRowKeys: React.Key[]) => {
      setSelectedPlans(selectedRowKeys as string[]);
    },
  };

  return (
    <div>
      <h1 className="page-title">生产计划</h1>
      
      {/* 统计卡片 */}
      <Row gutter={16} style={{ marginBottom: 24 }}>
        <Col span={6}>
          <Card>
            <div className="stat-card">
              <div className="stat-number">{planStats.in_progress_plans || 0}</div>
              <div className="stat-title">进行中计划</div>
            </div>
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <div className="stat-card">
              <div className="stat-number">{planStats.confirmed_plans || 0}</div>
              <div className="stat-title">待开始计划</div>
            </div>
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <div className="stat-card">
              <div className="stat-number">{planStats.completed_plans || 0}</div>
              <div className="stat-title">已完成计划</div>
            </div>
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <div className="stat-card">
              <div className="stat-number">{planStats.avg_progress ? `${planStats.avg_progress.toFixed(0)}%` : '0%'}</div>
              <div className="stat-title">平均完成率</div>
            </div>
          </Card>
        </Col>
      </Row>

      {/* 图表区域 */}
      <Row gutter={16} style={{ marginBottom: 24 }}>
        <Col span={16}>
          <Card title="生产计划甘特图" className="card-shadow">
            <ReactECharts option={ganttOption} style={{ height: 300 }} />
          </Card>
        </Col>
        <Col span={8}>
          <Card title="车间产能分析" className="card-shadow">
            <ReactECharts option={capacityOption} style={{ height: 300 }} />
          </Card>
        </Col>
      </Row>

      {/* 操作按钮和表格 */}
      <Card>
        <div className="action-buttons" style={{ marginBottom: 16 }}>
          <Space wrap>
            <Button type="primary" icon={<PlusOutlined />} onClick={handleAdd}>
              新增计划
            </Button>
            <Divider type="vertical" />
            <Button 
              type="primary" 
              icon={<ThunderboltOutlined />} 
              onClick={() => setAutoScheduleVisible(true)}
              disabled={selectedPlans.length === 0}
              loading={schedulingLoading}
            >
              自动排程
            </Button>
            <Button 
              icon={<ScheduleOutlined />} 
              onClick={() => setManualScheduleVisible(true)}
              disabled={selectedPlans.length === 0}
            >
              手动排程
            </Button>
            <Button 
              icon={<ReloadOutlined />} 
              onClick={() => setRescheduleVisible(true)}
              disabled={selectedPlans.length === 0}
            >
              重新排程
            </Button>
            <Button 
              icon={<WarningOutlined />} 
              onClick={handleConflictAnalysis}
              loading={schedulingLoading}
            >
              冲突分析
            </Button>
            <Divider type="vertical" />
            <Button 
              icon={<CalendarOutlined />} 
              onClick={handleViewGantt}
              disabled={selectedPlans.length === 0}
            >
              甘特图视图
            </Button>
            <Button icon={<BarChartOutlined />}>
              产能分析
            </Button>
            <Button icon={<SettingOutlined />}>
              排程设置
            </Button>
          </Space>
        </div>
        
        {selectedPlans.length > 0 && (
          <Alert
            message={`已选择 ${selectedPlans.length} 个生产计划`}
            type="info"
            showIcon
            style={{ marginBottom: 16 }}
            action={
              <Button size="small" onClick={() => setSelectedPlans([])}>
                清除选择
              </Button>
            }
          />
        )}

        <Table
          columns={columns}
          dataSource={dataSource}
          loading={loading}
          rowSelection={rowSelection}
          scroll={{ x: 1200 }}
          pagination={{
            total: dataSource.length,
            pageSize: 10,
            showSizeChanger: true,
            showQuickJumper: true,
            showTotal: (total) => `共 ${total} 条记录`
          }}
        />
      </Card>

      {/* 新增/编辑计划弹窗 */}
      <Modal
        title={editingRecord ? '编辑生产计划' : '新增生产计划'}
        open={modalVisible}
        onOk={handleSubmit}
        onCancel={() => setModalVisible(false)}
        width={800}
        destroyOnClose
      >
        <Form
          form={form}
          layout="vertical"
          initialValues={{
            status: '待开始',
            priority: '中',
            progress: 0
          }}
        >
          <Row gutter={16}>
            <Col span={12}>
              <Form.Item
                label="计划编号"
                name="planNo"
                rules={[{ required: true, message: '请输入计划编号' }]}
              >
                <Input placeholder="请输入计划编号" />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item
                label="订单号"
                name="orderNo"
                rules={[{ required: true, message: '请输入订单号' }]}
              >
                <Input placeholder="请输入订单号" />
              </Form.Item>
            </Col>
          </Row>
          
          <Row gutter={16}>
            <Col span={12}>
              <Form.Item
                label="产品"
                name="product"
                rules={[{ required: true, message: '请输入产品名称' }]}
              >
                <Input placeholder="请输入产品名称" />
              </Form.Item>
            </Col>
            <Col span={8}>
              <Form.Item
                label="数量"
                name="quantity"
                rules={[{ required: true, message: '请输入数量' }]}
              >
                <Input type="number" placeholder="请输入数量" />
              </Form.Item>
            </Col>
            <Col span={4}>
              <Form.Item
                label="单位"
                name="unit"
                rules={[{ required: true, message: '请选择单位' }]}
              >
                <Select placeholder="单位">
                  <Option value="件">件</Option>
                  <Option value="套">套</Option>
                  <Option value="个">个</Option>
                </Select>
              </Form.Item>
            </Col>
          </Row>

          <Row gutter={16}>
            <Col span={12}>
              <Form.Item
                label="开始日期"
                name="startDate"
                rules={[{ required: true, message: '请选择开始日期' }]}
              >
                <DatePicker style={{ width: '100%' }} />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item
                label="结束日期"
                name="endDate"
                rules={[{ required: true, message: '请选择结束日期' }]}
              >
                <DatePicker style={{ width: '100%' }} />
              </Form.Item>
            </Col>
          </Row>

          <Row gutter={16}>
            <Col span={8}>
              <Form.Item
                label="车间"
                name="workshop"
                rules={[{ required: true, message: '请选择车间' }]}
              >
                <Select placeholder="请选择车间">
                  <Option value="车间A">车间A</Option>
                  <Option value="车间B">车间B</Option>
                  <Option value="车间C">车间C</Option>
                  <Option value="车间D">车间D</Option>
                </Select>
              </Form.Item>
            </Col>
            <Col span={8}>
              <Form.Item
                label="负责人"
                name="operator"
                rules={[{ required: true, message: '请输入负责人' }]}
              >
                <Input placeholder="请输入负责人" />
              </Form.Item>
            </Col>
            <Col span={8}>
              <Form.Item
                label="优先级"
                name="priority"
                rules={[{ required: true, message: '请选择优先级' }]}
              >
                <Select placeholder="请选择优先级">
                  <Option value="高">高</Option>
                  <Option value="中">中</Option>
                  <Option value="低">低</Option>
                </Select>
              </Form.Item>
            </Col>
          </Row>

          <Row gutter={16}>
            <Col span={12}>
              <Form.Item
                label="状态"
                name="status"
                rules={[{ required: true, message: '请选择状态' }]}
              >
                <Select placeholder="请选择状态">
                  <Option value="待开始">待开始</Option>
                  <Option value="进行中">进行中</Option>
                  <Option value="已完成">已完成</Option>
                  <Option value="已暂停">已暂停</Option>
                </Select>
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item
                label="进度(%)"
                name="progress"
                rules={[{ required: true, message: '请输入进度' }]}
              >
                <Input type="number" min={0} max={100} placeholder="请输入进度" />
              </Form.Item>
            </Col>
          </Row>

          <Form.Item label="备注" name="remark">
            <Input.TextArea rows={3} placeholder="请输入备注信息" />
          </Form.Item>
        </Form>
      </Modal>

      {/* 甘特图弹窗 */}
      <Modal
        title="生产计划甘特图"
        open={ganttVisible}
        onCancel={() => setGanttVisible(false)}
        width={1200}
        footer={null}
      >
        <ReactECharts option={ganttOption} style={{ height: 500 }} />
      </Modal>

      {/* 自动排程弹窗 */}
      <Modal
        title="自动排程"
        open={autoScheduleVisible}
        onOk={handleAutoSchedule}
        onCancel={() => setAutoScheduleVisible(false)}
        confirmLoading={schedulingLoading}
        width={600}
      >
        <Form
          form={autoScheduleForm}
          layout="vertical"
          initialValues={{
            strategy: 'earliest_due_date',
            startDate: dayjs()
          }}
        >
          <Alert
            message={`将对选中的 ${selectedPlans.length} 个生产计划进行自动排程`}
            type="info"
            showIcon
            style={{ marginBottom: 16 }}
          />
          
          <Form.Item
            label="排程策略"
            name="strategy"
            rules={[{ required: true, message: '请选择排程策略' }]}
          >
            <Select placeholder="请选择排程策略">
              <Option value="earliest_due_date">最早交期优先</Option>
              <Option value="shortest_processing_time">最短加工时间优先</Option>
              <Option value="priority_first">优先级优先</Option>
              <Option value="balanced">平衡策略</Option>
            </Select>
          </Form.Item>
          
          <Form.Item
            label="排程开始日期"
            name="startDate"
            rules={[{ required: true, message: '请选择排程开始日期' }]}
          >
            <DatePicker style={{ width: '100%' }} />
          </Form.Item>
          
          <Form.Item label="备注" name="remark">
            <Input.TextArea rows={3} placeholder="请输入排程备注" />
          </Form.Item>
        </Form>
       </Modal>

       {/* 手动排程弹窗 */}
       <Modal
         title="手动排程"
         open={manualScheduleVisible}
         onOk={handleManualSchedule}
         onCancel={() => setManualScheduleVisible(false)}
         confirmLoading={schedulingLoading}
         width={800}
       >
         <Form
           form={manualScheduleForm}
           layout="vertical"
         >
           <Alert
             message="手动排程允许您精确控制生产计划的时间和资源分配"
             type="info"
             showIcon
             style={{ marginBottom: 16 }}
           />
           
           <Row gutter={16}>
             <Col span={12}>
               <Form.Item
                 label="计划开始日期"
                 name="startDate"
                 rules={[{ required: true, message: '请选择开始日期' }]}
               >
                 <DatePicker style={{ width: '100%' }} showTime />
               </Form.Item>
             </Col>
             <Col span={12}>
               <Form.Item
                 label="计划结束日期"
                 name="endDate"
                 rules={[{ required: true, message: '请选择结束日期' }]}
               >
                 <DatePicker style={{ width: '100%' }} showTime />
               </Form.Item>
             </Col>
           </Row>
           
           <Row gutter={16}>
             <Col span={8}>
               <Form.Item
                 label="分配车间"
                 name="workshop"
                 rules={[{ required: true, message: '请选择车间' }]}
               >
                 <Select placeholder="请选择车间">
                   <Option value="车间A">车间A</Option>
                   <Option value="车间B">车间B</Option>
                   <Option value="车间C">车间C</Option>
                   <Option value="车间D">车间D</Option>
                 </Select>
               </Form.Item>
             </Col>
             <Col span={8}>
               <Form.Item
                 label="生产线"
                 name="productionLine"
                 rules={[{ required: true, message: '请选择生产线' }]}
               >
                 <Select placeholder="请选择生产线">
                   <Option value="生产线1">生产线1</Option>
                   <Option value="生产线2">生产线2</Option>
                   <Option value="生产线3">生产线3</Option>
                 </Select>
               </Form.Item>
             </Col>
             <Col span={8}>
               <Form.Item
                 label="负责人"
                 name="operator"
                 rules={[{ required: true, message: '请输入负责人' }]}
               >
                 <Input placeholder="请输入负责人" />
               </Form.Item>
             </Col>
           </Row>
           
           <Form.Item label="排程说明" name="description">
             <Input.TextArea rows={3} placeholder="请输入排程说明" />
           </Form.Item>
         </Form>
       </Modal>

       {/* 重新排程弹窗 */}
       <Modal
         title="重新排程"
         open={rescheduleVisible}
         onOk={handleReschedule}
         onCancel={() => setRescheduleVisible(false)}
         confirmLoading={schedulingLoading}
         width={600}
       >
         <Form
           form={rescheduleForm}
           layout="vertical"
           initialValues={{
             strategy: 'earliest_due_date'
           }}
         >
           <Alert
             message={`将对选中的 ${selectedPlans.length} 个生产计划进行重新排程`}
             type="warning"
             showIcon
             style={{ marginBottom: 16 }}
           />
           
           <Form.Item
             label="重排原因"
             name="reason"
             rules={[{ required: true, message: '请选择重排原因' }]}
           >
             <Select placeholder="请选择重排原因">
               <Option value="priority_change">优先级变更</Option>
               <Option value="resource_conflict">资源冲突</Option>
               <Option value="deadline_change">交期变更</Option>
               <Option value="equipment_maintenance">设备维护</Option>
               <Option value="other">其他原因</Option>
             </Select>
           </Form.Item>
           
           <Form.Item
             label="新的排程策略"
             name="strategy"
             rules={[{ required: true, message: '请选择排程策略' }]}
           >
             <Select placeholder="请选择排程策略">
               <Option value="earliest_due_date">最早交期优先</Option>
               <Option value="shortest_processing_time">最短加工时间优先</Option>
               <Option value="priority_first">优先级优先</Option>
               <Option value="balanced">平衡策略</Option>
             </Select>
           </Form.Item>
           
           <Form.Item
             label="新的截止日期"
             name="newDeadline"
           >
             <DatePicker style={{ width: '100%' }} />
           </Form.Item>
           
           <Form.Item label="重排说明" name="description">
             <Input.TextArea rows={3} placeholder="请输入重排说明" />
           </Form.Item>
         </Form>
       </Modal>

       {/* 冲突分析弹窗 */}
       <Modal
         title="排程冲突分析"
         open={conflictAnalysisVisible}
         onCancel={() => setConflictAnalysisVisible(false)}
         width={800}
         footer={[
           <Button key="close" onClick={() => setConflictAnalysisVisible(false)}>
             关闭
           </Button>
         ]}
       >
         <Spin spinning={schedulingLoading}>
           {conflictData.length > 0 ? (
             <List
               dataSource={conflictData}
               renderItem={(item: any) => (
                 <List.Item>
                   <List.Item.Meta
                     avatar={
                       <Tag color={item.severity === 'high' ? 'red' : item.severity === 'medium' ? 'orange' : 'green'}>
                         {item.severity === 'high' ? '高' : item.severity === 'medium' ? '中' : '低'}
                       </Tag>
                     }
                     title={item.type}
                     description={
                       <div>
                         <Text>{item.description}</Text>
                         <br />
                         <Text type="secondary">影响计划: {item.affectedPlans.join(', ')}</Text>
                       </div>
                     }
                   />
                 </List.Item>
               )}
             />
           ) : (
             <div style={{ textAlign: 'center', padding: '40px 0' }}>
               <Text type="secondary">暂无冲突检测到</Text>
             </div>
           )}
         </Spin>
       </Modal>
     </div>
   );
};

export default ProductionPlan;