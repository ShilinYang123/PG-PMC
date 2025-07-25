import React, { useState } from 'react';
import {
  Card,
  Table,
  Button,
  Space,
  Tag,
  Modal,
  Form,
  Input,
  Select,
  Row,
  Col,
  Tabs,
  Progress,
  Timeline,
  Statistic,
  DatePicker,
  Alert,
  Tooltip,
  Badge
} from 'antd';
import {
  PlusOutlined,
  EditOutlined,
  DeleteOutlined,
  EyeOutlined,
  ClockCircleOutlined,
  CheckCircleOutlined,
  ExclamationCircleOutlined,
  BarChartOutlined,
  CalendarOutlined
} from '@ant-design/icons';
import ReactECharts from 'echarts-for-react';
import type { ColumnsType } from 'antd/es/table';
import dayjs from 'dayjs';

const { Option } = Select;
const { TabPane } = Tabs;
const { RangePicker } = DatePicker;

interface ProgressRecord {
  key: string;
  orderNo: string;
  productName: string;
  planStartDate: string;
  planEndDate: string;
  actualStartDate: string;
  actualEndDate?: string;
  currentStage: string;
  progress: number;
  status: string;
  responsible: string;
  workshop: string;
  priority: string;
  remark: string;
}

interface StageRecord {
  key: string;
  stageName: string;
  planStartDate: string;
  planEndDate: string;
  actualStartDate?: string;
  actualEndDate?: string;
  progress: number;
  status: string;
  responsible: string;
  duration: number;
  remark: string;
}

interface QualityRecord {
  key: string;
  orderNo: string;
  stageName: string;
  checkDate: string;
  checkResult: string;
  qualityScore: number;
  defectCount: number;
  inspector: string;
  remark: string;
}

const ProgressTracking: React.FC = () => {
  const [loading, setLoading] = useState(false);
  const [modalVisible, setModalVisible] = useState(false);
  const [detailModalVisible, setDetailModalVisible] = useState(false);
  const [editingRecord, setEditingRecord] = useState<ProgressRecord | null>(null);
  const [selectedOrder, setSelectedOrder] = useState<ProgressRecord | null>(null);
  const [form] = Form.useForm();

  // 进度跟踪数据
  const [progressData, setProgressData] = useState<ProgressRecord[]>([
    {
      key: '1',
      orderNo: 'ORD-2024-001',
      productName: '精密零件A',
      planStartDate: '2024-01-15',
      planEndDate: '2024-02-15',
      actualStartDate: '2024-01-15',
      currentStage: '机加工',
      progress: 65,
      status: '进行中',
      responsible: '张师傅',
      workshop: '机加工车间',
      priority: '高',
      remark: '按计划进行'
    },
    {
      key: '2',
      orderNo: 'ORD-2024-002',
      productName: '标准件B',
      planStartDate: '2024-01-20',
      planEndDate: '2024-02-10',
      actualStartDate: '2024-01-22',
      currentStage: '质检',
      progress: 90,
      status: '延期',
      responsible: '李师傅',
      workshop: '装配车间',
      priority: '中',
      remark: '材料延期到货'
    },
    {
      key: '3',
      orderNo: 'ORD-2024-003',
      productName: '定制件C',
      planStartDate: '2024-01-10',
      planEndDate: '2024-01-25',
      actualStartDate: '2024-01-10',
      actualEndDate: '2024-01-24',
      currentStage: '完成',
      progress: 100,
      status: '已完成',
      responsible: '王师傅',
      workshop: '精密车间',
      priority: '高',
      remark: '提前完成'
    }
  ]);

  // 阶段详情数据
  const [stageData, setStageData] = useState<StageRecord[]>([
    {
      key: '1',
      stageName: '下料',
      planStartDate: '2024-01-15',
      planEndDate: '2024-01-17',
      actualStartDate: '2024-01-15',
      actualEndDate: '2024-01-17',
      progress: 100,
      status: '已完成',
      responsible: '张师傅',
      duration: 2,
      remark: '按时完成'
    },
    {
      key: '2',
      stageName: '机加工',
      planStartDate: '2024-01-18',
      planEndDate: '2024-01-28',
      actualStartDate: '2024-01-18',
      progress: 65,
      status: '进行中',
      responsible: '李师傅',
      duration: 10,
      remark: '正在进行'
    },
    {
      key: '3',
      stageName: '质检',
      planStartDate: '2024-01-29',
      planEndDate: '2024-02-02',
      progress: 0,
      status: '未开始',
      responsible: '王检验员',
      duration: 4,
      remark: '等待前序完成'
    }
  ]);

  // 质量检查数据
  const [qualityData, setQualityData] = useState<QualityRecord[]>([
    {
      key: '1',
      orderNo: 'ORD-2024-001',
      stageName: '下料',
      checkDate: '2024-01-17',
      checkResult: '合格',
      qualityScore: 95,
      defectCount: 0,
      inspector: '质检员A',
      remark: '尺寸精度良好'
    },
    {
      key: '2',
      orderNo: 'ORD-2024-002',
      stageName: '机加工',
      checkDate: '2024-01-25',
      checkResult: '不合格',
      qualityScore: 75,
      defectCount: 2,
      inspector: '质检员B',
      remark: '表面粗糙度超标'
    }
  ]);

  // 进度表格列配置
  const progressColumns: ColumnsType<ProgressRecord> = [
    {
      title: '订单编号',
      dataIndex: 'orderNo',
      key: 'orderNo',
      width: 120,
      fixed: 'left'
    },
    {
      title: '产品名称',
      dataIndex: 'productName',
      key: 'productName',
      width: 120
    },
    {
      title: '计划开始',
      dataIndex: 'planStartDate',
      key: 'planStartDate',
      width: 100
    },
    {
      title: '计划完成',
      dataIndex: 'planEndDate',
      key: 'planEndDate',
      width: 100
    },
    {
      title: '当前阶段',
      dataIndex: 'currentStage',
      key: 'currentStage',
      width: 100
    },
    {
      title: '进度',
      dataIndex: 'progress',
      key: 'progress',
      width: 120,
      render: (progress) => (
        <Progress 
          percent={progress} 
          size="small" 
          status={progress === 100 ? 'success' : progress > 80 ? 'active' : 'normal'}
        />
      )
    },
    {
      title: '状态',
      dataIndex: 'status',
      key: 'status',
      width: 80,
      render: (status) => {
        let color = 'processing';
        if (status === '已完成') color = 'success';
        if (status === '延期') color = 'error';
        if (status === '暂停') color = 'warning';
        return <Tag color={color}>{status}</Tag>;
      }
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
      title: '负责人',
      dataIndex: 'responsible',
      key: 'responsible',
      width: 80
    },
    {
      title: '车间',
      dataIndex: 'workshop',
      key: 'workshop',
      width: 100
    },
    {
      title: '操作',
      key: 'action',
      width: 150,
      fixed: 'right',
      render: (_, record) => (
        <Space size="small">
          <Tooltip title="查看详情">
            <Button
              type="link"
              icon={<EyeOutlined />}
              onClick={() => handleViewDetail(record)}
            />
          </Tooltip>
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

  // 阶段表格列配置
  const stageColumns: ColumnsType<StageRecord> = [
    {
      title: '阶段名称',
      dataIndex: 'stageName',
      key: 'stageName',
      width: 100
    },
    {
      title: '计划开始',
      dataIndex: 'planStartDate',
      key: 'planStartDate',
      width: 100
    },
    {
      title: '计划完成',
      dataIndex: 'planEndDate',
      key: 'planEndDate',
      width: 100
    },
    {
      title: '实际开始',
      dataIndex: 'actualStartDate',
      key: 'actualStartDate',
      width: 100,
      render: (date) => date || '-'
    },
    {
      title: '实际完成',
      dataIndex: 'actualEndDate',
      key: 'actualEndDate',
      width: 100,
      render: (date) => date || '-'
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
      title: '状态',
      dataIndex: 'status',
      key: 'status',
      width: 80,
      render: (status) => {
        let color = 'default';
        if (status === '已完成') color = 'success';
        if (status === '进行中') color = 'processing';
        if (status === '延期') color = 'error';
        return <Tag color={color}>{status}</Tag>;
      }
    },
    {
      title: '负责人',
      dataIndex: 'responsible',
      key: 'responsible',
      width: 80
    }
  ];

  // 进度统计图表配置
  const progressStatsOption = {
    title: {
      text: '生产进度统计',
      left: 'center'
    },
    tooltip: {
      trigger: 'item'
    },
    legend: {
      orient: 'vertical',
      left: 'left'
    },
    series: [
      {
        name: '订单状态',
        type: 'pie',
        radius: '50%',
        data: [
          { value: 45, name: '进行中' },
          { value: 30, name: '已完成' },
          { value: 15, name: '延期' },
          { value: 10, name: '暂停' }
        ],
        emphasis: {
          itemStyle: {
            shadowBlur: 10,
            shadowOffsetX: 0,
            shadowColor: 'rgba(0, 0, 0, 0.5)'
          }
        }
      }
    ]
  };

  // 车间产能分析图表配置
  const workshopCapacityOption = {
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
      data: ['计划产能', '实际产能']
    },
    xAxis: {
      type: 'category',
      data: ['机加工车间', '装配车间', '精密车间', '包装车间']
    },
    yAxis: {
      type: 'value',
      name: '产能利用率(%)'
    },
    series: [
      {
        name: '计划产能',
        type: 'bar',
        data: [85, 90, 78, 95],
        itemStyle: {
          color: '#1890ff'
        }
      },
      {
        name: '实际产能',
        type: 'bar',
        data: [78, 85, 82, 88],
        itemStyle: {
          color: '#52c41a'
        }
      }
    ]
  };

  const handleAdd = () => {
    setEditingRecord(null);
    form.resetFields();
    setModalVisible(true);
  };

  const handleEdit = (record: ProgressRecord) => {
    setEditingRecord(record);
    form.setFieldsValue({
      ...record,
      planStartDate: dayjs(record.planStartDate),
      planEndDate: dayjs(record.planEndDate),
      actualStartDate: record.actualStartDate ? dayjs(record.actualStartDate) : null
    });
    setModalVisible(true);
  };

  const handleDelete = (key: string) => {
    setProgressData(progressData.filter(item => item.key !== key));
  };

  const handleViewDetail = (record: ProgressRecord) => {
    setSelectedOrder(record);
    setDetailModalVisible(true);
  };

  const handleSubmit = async () => {
    try {
      const values = await form.validateFields();
      const formattedValues = {
        ...values,
        planStartDate: values.planStartDate.format('YYYY-MM-DD'),
        planEndDate: values.planEndDate.format('YYYY-MM-DD'),
        actualStartDate: values.actualStartDate ? values.actualStartDate.format('YYYY-MM-DD') : null
      };
      
      if (editingRecord) {
        setProgressData(progressData.map(item => 
          item.key === editingRecord.key 
            ? { ...item, ...formattedValues }
            : item
        ));
      } else {
        const newRecord = {
          key: Date.now().toString(),
          ...formattedValues
        };
        setProgressData([...progressData, newRecord]);
      }
      
      setModalVisible(false);
    } catch (error) {
      console.error('表单验证失败:', error);
    }
  };

  // 获取延期订单数量
  const getDelayedCount = () => {
    return progressData.filter(item => item.status === '延期').length;
  };

  // 获取平均进度
  const getAverageProgress = () => {
    const total = progressData.reduce((sum, item) => sum + item.progress, 0);
    return Math.round(total / progressData.length);
  };

  return (
    <div>
      <h1 className="page-title">进度跟踪</h1>
      
      {/* 延期预警 */}
      {getDelayedCount() > 0 && (
        <Alert
          message={`当前有 ${getDelayedCount()} 个订单延期，请及时处理！`}
          type="error"
          showIcon
          closable
          style={{ marginBottom: 16 }}
        />
      )}

      {/* 统计卡片 */}
      <Row gutter={16} style={{ marginBottom: 24 }}>
        <Col span={6}>
          <Card>
            <Statistic
              title="总订单数"
              value={progressData.length}
              prefix={<CalendarOutlined />}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic
              title="平均进度"
              value={getAverageProgress()}
              suffix="%"
              prefix={<BarChartOutlined />}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic
              title="延期订单"
              value={getDelayedCount()}
              valueStyle={{ color: '#cf1322' }}
              prefix={<ExclamationCircleOutlined />}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic
              title="完成订单"
              value={progressData.filter(item => item.status === '已完成').length}
              valueStyle={{ color: '#3f8600' }}
              prefix={<CheckCircleOutlined />}
            />
          </Card>
        </Col>
      </Row>

      {/* 图表区域 */}
      <Row gutter={16} style={{ marginBottom: 24 }}>
        <Col span={12}>
          <Card title="生产进度统计" className="card-shadow">
            <ReactECharts option={progressStatsOption} style={{ height: 300 }} />
          </Card>
        </Col>
        <Col span={12}>
          <Card title="车间产能分析" className="card-shadow">
            <ReactECharts option={workshopCapacityOption} style={{ height: 300 }} />
          </Card>
        </Col>
      </Row>

      {/* 主要内容区域 */}
      <Card>
        <Tabs defaultActiveKey="progress">
          <TabPane tab={<span><ClockCircleOutlined />进度总览</span>} key="progress">
            <div className="action-buttons" style={{ marginBottom: 16 }}>
              <Space>
                <Button type="primary" icon={<PlusOutlined />} onClick={handleAdd}>
                  新增跟踪
                </Button>
                <RangePicker placeholder={['开始日期', '结束日期']} />
                <Select placeholder="选择车间" style={{ width: 120 }}>
                  <Option value="all">全部车间</Option>
                  <Option value="machining">机加工车间</Option>
                  <Option value="assembly">装配车间</Option>
                  <Option value="precision">精密车间</Option>
                </Select>
                <Select placeholder="选择状态" style={{ width: 120 }}>
                  <Option value="all">全部状态</Option>
                  <Option value="progress">进行中</Option>
                  <Option value="completed">已完成</Option>
                  <Option value="delayed">延期</Option>
                </Select>
              </Space>
            </div>

            <Table
              columns={progressColumns}
              dataSource={progressData}
              loading={loading}
              scroll={{ x: 1400 }}
              pagination={{
                total: progressData.length,
                pageSize: 10,
                showSizeChanger: true,
                showQuickJumper: true,
                showTotal: (total) => `共 ${total} 条记录`
              }}
            />
          </TabPane>

          <TabPane tab={<span><CheckCircleOutlined />质量检查</span>} key="quality">
            <div className="action-buttons" style={{ marginBottom: 16 }}>
              <Space>
                <Button type="primary" icon={<PlusOutlined />}>
                  新增检查记录
                </Button>
                <Button>质量报告</Button>
                <Button>不合格处理</Button>
              </Space>
            </div>

            <Table
              dataSource={qualityData}
              loading={loading}
              columns={[
                {
                  title: '订单编号',
                  dataIndex: 'orderNo',
                  key: 'orderNo'
                },
                {
                  title: '检查阶段',
                  dataIndex: 'stageName',
                  key: 'stageName'
                },
                {
                  title: '检查日期',
                  dataIndex: 'checkDate',
                  key: 'checkDate'
                },
                {
                  title: '检查结果',
                  dataIndex: 'checkResult',
                  key: 'checkResult',
                  render: (result) => (
                    <Tag color={result === '合格' ? 'success' : 'error'}>
                      {result}
                    </Tag>
                  )
                },
                {
                  title: '质量评分',
                  dataIndex: 'qualityScore',
                  key: 'qualityScore',
                  render: (score) => (
                    <span style={{ color: score >= 90 ? '#52c41a' : score >= 80 ? '#faad14' : '#ff4d4f' }}>
                      {score}分
                    </span>
                  )
                },
                {
                  title: '缺陷数量',
                  dataIndex: 'defectCount',
                  key: 'defectCount'
                },
                {
                  title: '检验员',
                  dataIndex: 'inspector',
                  key: 'inspector'
                }
              ]}
              pagination={{
                total: qualityData.length,
                pageSize: 10,
                showSizeChanger: true,
                showQuickJumper: true,
                showTotal: (total) => `共 ${total} 条记录`
              }}
            />
          </TabPane>
        </Tabs>
      </Card>

      {/* 新增/编辑进度弹窗 */}
      <Modal
        title={editingRecord ? '编辑进度' : '新增进度跟踪'}
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
            status: '进行中',
            priority: '中',
            progress: 0
          }}
        >
          <Row gutter={16}>
            <Col span={12}>
              <Form.Item
                label="订单编号"
                name="orderNo"
                rules={[{ required: true, message: '请输入订单编号' }]}
              >
                <Input placeholder="请输入订单编号" />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item
                label="产品名称"
                name="productName"
                rules={[{ required: true, message: '请输入产品名称' }]}
              >
                <Input placeholder="请输入产品名称" />
              </Form.Item>
            </Col>
          </Row>
          
          <Row gutter={16}>
            <Col span={12}>
              <Form.Item
                label="计划开始日期"
                name="planStartDate"
                rules={[{ required: true, message: '请选择计划开始日期' }]}
              >
                <DatePicker style={{ width: '100%' }} />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item
                label="计划完成日期"
                name="planEndDate"
                rules={[{ required: true, message: '请选择计划完成日期' }]}
              >
                <DatePicker style={{ width: '100%' }} />
              </Form.Item>
            </Col>
          </Row>

          <Row gutter={16}>
            <Col span={12}>
              <Form.Item
                label="实际开始日期"
                name="actualStartDate"
              >
                <DatePicker style={{ width: '100%' }} />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item
                label="当前阶段"
                name="currentStage"
                rules={[{ required: true, message: '请输入当前阶段' }]}
              >
                <Select placeholder="请选择当前阶段">
                  <Option value="下料">下料</Option>
                  <Option value="机加工">机加工</Option>
                  <Option value="装配">装配</Option>
                  <Option value="质检">质检</Option>
                  <Option value="包装">包装</Option>
                  <Option value="完成">完成</Option>
                </Select>
              </Form.Item>
            </Col>
          </Row>

          <Row gutter={16}>
            <Col span={8}>
              <Form.Item
                label="进度(%)"
                name="progress"
                rules={[{ required: true, message: '请输入进度' }]}
              >
                <Select placeholder="请选择进度">
                  {[0, 10, 20, 30, 40, 50, 60, 70, 80, 90, 100].map(value => (
                    <Option key={value} value={value}>{value}%</Option>
                  ))}
                </Select>
              </Form.Item>
            </Col>
            <Col span={8}>
              <Form.Item
                label="状态"
                name="status"
                rules={[{ required: true, message: '请选择状态' }]}
              >
                <Select placeholder="请选择状态">
                  <Option value="进行中">进行中</Option>
                  <Option value="已完成">已完成</Option>
                  <Option value="延期">延期</Option>
                  <Option value="暂停">暂停</Option>
                </Select>
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
                label="负责人"
                name="responsible"
                rules={[{ required: true, message: '请输入负责人' }]}
              >
                <Input placeholder="请输入负责人" />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item
                label="车间"
                name="workshop"
                rules={[{ required: true, message: '请选择车间' }]}
              >
                <Select placeholder="请选择车间">
                  <Option value="机加工车间">机加工车间</Option>
                  <Option value="装配车间">装配车间</Option>
                  <Option value="精密车间">精密车间</Option>
                  <Option value="包装车间">包装车间</Option>
                </Select>
              </Form.Item>
            </Col>
          </Row>

          <Form.Item label="备注" name="remark">
            <Input.TextArea rows={3} placeholder="请输入备注信息" />
          </Form.Item>
        </Form>
      </Modal>

      {/* 详情弹窗 */}
      <Modal
        title={`订单详情 - ${selectedOrder?.orderNo}`}
        open={detailModalVisible}
        onCancel={() => setDetailModalVisible(false)}
        width={1000}
        footer={null}
      >
        {selectedOrder && (
          <div>
            <Row gutter={16} style={{ marginBottom: 24 }}>
              <Col span={12}>
                <Card title="基本信息" size="small">
                  <p><strong>产品名称：</strong>{selectedOrder.productName}</p>
                  <p><strong>计划周期：</strong>{selectedOrder.planStartDate} ~ {selectedOrder.planEndDate}</p>
                  <p><strong>当前阶段：</strong>{selectedOrder.currentStage}</p>
                  <p><strong>负责人：</strong>{selectedOrder.responsible}</p>
                  <p><strong>车间：</strong>{selectedOrder.workshop}</p>
                </Card>
              </Col>
              <Col span={12}>
                <Card title="进度信息" size="small">
                  <Progress percent={selectedOrder.progress} />
                  <p style={{ marginTop: 16 }}><strong>状态：</strong>
                    <Tag color={selectedOrder.status === '已完成' ? 'success' : selectedOrder.status === '延期' ? 'error' : 'processing'}>
                      {selectedOrder.status}
                    </Tag>
                  </p>
                  <p><strong>优先级：</strong>
                    <Tag color={selectedOrder.priority === '高' ? 'red' : selectedOrder.priority === '中' ? 'orange' : 'green'}>
                      {selectedOrder.priority}
                    </Tag>
                  </p>
                </Card>
              </Col>
            </Row>

            <Card title="阶段详情" size="small">
              <Table
                columns={stageColumns}
                dataSource={stageData}
                pagination={false}
                size="small"
              />
            </Card>

            <Card title="进度时间线" size="small" style={{ marginTop: 16 }}>
              <Timeline>
                <Timeline.Item color="green">
                  <p>下料阶段完成</p>
                  <p>2024-01-17 完成</p>
                </Timeline.Item>
                <Timeline.Item color="blue">
                  <p>机加工阶段进行中</p>
                  <p>2024-01-18 开始，预计2024-01-28完成</p>
                </Timeline.Item>
                <Timeline.Item color="gray">
                  <p>质检阶段待开始</p>
                  <p>计划2024-01-29开始</p>
                </Timeline.Item>
              </Timeline>
            </Card>
          </div>
        )}
      </Modal>
    </div>
  );
};

export default ProgressTracking;