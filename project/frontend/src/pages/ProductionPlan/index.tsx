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
  DatePicker,
  Select,
  Row,
  Col,
  Progress,
  Tooltip,
  Divider
} from 'antd';
import {
  PlusOutlined,
  EditOutlined,
  DeleteOutlined,
  CalendarOutlined,
  BarChartOutlined,
  SettingOutlined
} from '@ant-design/icons';
import ReactECharts from 'echarts-for-react';
import type { ColumnsType } from 'antd/es/table';
import dayjs from 'dayjs';

const { Option } = Select;
const { RangePicker } = DatePicker;

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

  // 模拟生产计划数据
  const [dataSource, setDataSource] = useState<ProductionPlan[]>([
    {
      key: '1',
      planNo: 'PP-2024-001',
      orderNo: 'BD400-001',
      product: '精密零件A',
      quantity: 1000,
      unit: '件',
      startDate: '2024-01-20',
      endDate: '2024-02-10',
      status: '进行中',
      progress: 65,
      workshop: '车间A',
      operator: '张师傅',
      priority: '高',
      remark: '优先生产'
    },
    {
      key: '2',
      planNo: 'PP-2024-002',
      orderNo: 'BD400-002',
      product: '标准件B',
      quantity: 500,
      unit: '套',
      startDate: '2024-02-01',
      endDate: '2024-02-15',
      status: '待开始',
      progress: 0,
      workshop: '车间B',
      operator: '李师傅',
      priority: '中',
      remark: '按计划执行'
    },
    {
      key: '3',
      planNo: 'PP-2024-003',
      orderNo: 'BD400-003',
      product: '定制件C',
      quantity: 200,
      unit: '个',
      startDate: '2024-01-15',
      endDate: '2024-02-05',
      status: '已完成',
      progress: 100,
      workshop: '车间C',
      operator: '王师傅',
      priority: '低',
      remark: '提前完成'
    }
  ]);

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

  const handleDelete = (key: string) => {
    setDataSource(dataSource.filter(item => item.key !== key));
  };

  const handleSubmit = async () => {
    try {
      const values = await form.validateFields();
      const formData = {
        ...values,
        startDate: values.startDate.format('YYYY-MM-DD'),
        endDate: values.endDate.format('YYYY-MM-DD')
      };

      if (editingRecord) {
        setDataSource(dataSource.map(item => 
          item.key === editingRecord.key 
            ? { ...item, ...formData }
            : item
        ));
      } else {
        const newRecord = {
          key: Date.now().toString(),
          ...formData
        };
        setDataSource([...dataSource, newRecord]);
      }
      
      setModalVisible(false);
    } catch (error) {
      console.error('表单验证失败:', error);
    }
  };

  return (
    <div>
      <h1 className="page-title">生产计划</h1>
      
      {/* 统计卡片 */}
      <Row gutter={16} style={{ marginBottom: 24 }}>
        <Col span={6}>
          <Card>
            <div className="stat-card">
              <div className="stat-number">12</div>
              <div className="stat-title">进行中计划</div>
            </div>
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <div className="stat-card">
              <div className="stat-number">8</div>
              <div className="stat-title">待开始计划</div>
            </div>
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <div className="stat-card">
              <div className="stat-number">25</div>
              <div className="stat-title">已完成计划</div>
            </div>
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <div className="stat-card">
              <div className="stat-number">92%</div>
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
          <Space>
            <Button type="primary" icon={<PlusOutlined />} onClick={handleAdd}>
              新增计划
            </Button>
            <Button icon={<CalendarOutlined />} onClick={() => setGanttVisible(true)}>
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

        <Table
          columns={columns}
          dataSource={dataSource}
          loading={loading}
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
    </div>
  );
};

export default ProductionPlan;