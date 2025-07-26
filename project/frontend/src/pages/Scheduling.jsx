import React, { useState, useEffect } from 'react';
import {
  Card,
  Button,
  Table,
  Modal,
  Form,
  Input,
  Select,
  DatePicker,
  InputNumber,
  message,
  Tabs,
  Row,
  Col,
  Statistic,
  Progress,
  Tag,
  Space,
  Popconfirm,
  Timeline,
  Divider
} from 'antd';
import {
  PlayCircleOutlined,
  ReloadOutlined,
  PlusOutlined,
  SettingOutlined,
  BarChartOutlined,
  ClockCircleOutlined,
  CheckCircleOutlined,
  ExclamationCircleOutlined
} from '@ant-design/icons';
import moment from 'moment';
import * as echarts from 'echarts';
import './Scheduling.css';

const { TabPane } = Tabs;
const { Option } = Select;
const { RangePicker } = DatePicker;

const Scheduling = () => {
  const [loading, setLoading] = useState(false);
  const [orders, setOrders] = useState([]);
  const [equipment, setEquipment] = useState([]);
  const [materials, setMaterials] = useState([]);
  const [ganttData, setGanttData] = useState([]);
  const [summary, setSummary] = useState({});
  const [activeTab, setActiveTab] = useState('1');
  
  // 模态框状态
  const [orderModalVisible, setOrderModalVisible] = useState(false);
  const [equipmentModalVisible, setEquipmentModalVisible] = useState(false);
  const [materialModalVisible, setMaterialModalVisible] = useState(false);
  const [scheduleModalVisible, setScheduleModalVisible] = useState(false);
  
  // 表单实例
  const [orderForm] = Form.useForm();
  const [equipmentForm] = Form.useForm();
  const [materialForm] = Form.useForm();
  const [scheduleForm] = Form.useForm();

  // 初始化数据
  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    setLoading(true);
    try {
      await Promise.all([
        loadOrders(),
        loadEquipment(),
        loadMaterials(),
        loadSummary(),
        loadGanttData()
      ]);
    } catch (error) {
      message.error('加载数据失败');
    } finally {
      setLoading(false);
    }
  };

  const loadOrders = async () => {
    try {
      const response = await fetch('/api/scheduling/orders');
      const result = await response.json();
      if (result.success) {
        setOrders(result.data.orders || []);
      }
    } catch (error) {
      console.error('加载订单失败:', error);
    }
  };

  const loadEquipment = async () => {
    try {
      const response = await fetch('/api/scheduling/equipment');
      const result = await response.json();
      if (result.success) {
        setEquipment(result.data.equipment || []);
      }
    } catch (error) {
      console.error('加载设备失败:', error);
    }
  };

  const loadMaterials = async () => {
    try {
      const response = await fetch('/api/scheduling/materials');
      const result = await response.json();
      if (result.success) {
        setMaterials(result.data.materials || []);
      }
    } catch (error) {
      console.error('加载物料失败:', error);
    }
  };

  const loadSummary = async () => {
    try {
      const response = await fetch('/api/scheduling/summary');
      const result = await response.json();
      if (result.success) {
        setSummary(result.data || {});
      }
    } catch (error) {
      console.error('加载概况失败:', error);
    }
  };

  const loadGanttData = async () => {
    try {
      const response = await fetch('/api/scheduling/gantt');
      const result = await response.json();
      if (result.success) {
        setGanttData(result.data.gantt_data || []);
      }
    } catch (error) {
      console.error('加载甘特图数据失败:', error);
    }
  };

  // 执行排产
  const executeScheduling = async (values) => {
    setLoading(true);
    try {
      const response = await fetch('/api/scheduling/schedule', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          start_date: values.start_date?.toISOString(),
          force_reschedule: values.force_reschedule || false,
          notify_wechat: values.notify_wechat !== false
        }),
      });
      
      const result = await response.json();
      if (result.success) {
        message.success(result.message);
        setScheduleModalVisible(false);
        scheduleForm.resetFields();
        await loadData();
      } else {
        message.error(result.message);
      }
    } catch (error) {
      message.error('排产失败');
    } finally {
      setLoading(false);
    }
  };

  // 创建订单
  const createOrder = async (values) => {
    setLoading(true);
    try {
      const response = await fetch('/api/scheduling/orders', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          ...values,
          due_date: values.due_date.toISOString(),
          material_requirements: values.material_requirements || {}
        }),
      });
      
      const result = await response.json();
      if (result.success) {
        message.success(result.message);
        setOrderModalVisible(false);
        orderForm.resetFields();
        await loadOrders();
      } else {
        message.error(result.message);
      }
    } catch (error) {
      message.error('创建订单失败');
    } finally {
      setLoading(false);
    }
  };

  // 创建设备
  const createEquipment = async (values) => {
    setLoading(true);
    try {
      const response = await fetch('/api/scheduling/equipment', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          ...values,
          maintenance_schedule: values.maintenance_schedule || []
        }),
      });
      
      const result = await response.json();
      if (result.success) {
        message.success(result.message);
        setEquipmentModalVisible(false);
        equipmentForm.resetFields();
        await loadEquipment();
      } else {
        message.error(result.message);
      }
    } catch (error) {
      message.error('创建设备失败');
    } finally {
      setLoading(false);
    }
  };

  // 创建物料
  const createMaterial = async (values) => {
    setLoading(true);
    try {
      const response = await fetch('/api/scheduling/materials', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(values),
      });
      
      const result = await response.json();
      if (result.success) {
        message.success(result.message);
        setMaterialModalVisible(false);
        materialForm.resetFields();
        await loadMaterials();
      } else {
        message.error(result.message);
      }
    } catch (error) {
      message.error('创建物料失败');
    } finally {
      setLoading(false);
    }
  };

  // 重新排产
  const rescheduleOrder = async (orderId) => {
    setLoading(true);
    try {
      const response = await fetch('/api/scheduling/reschedule', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ order_id: orderId }),
      });
      
      const result = await response.json();
      if (result.success) {
        message.success(result.message);
        await loadData();
      } else {
        message.error(result.message);
      }
    } catch (error) {
      message.error('重新排产失败');
    } finally {
      setLoading(false);
    }
  };

  // 订单表格列定义
  const orderColumns = [
    {
      title: '订单号',
      dataIndex: 'order_id',
      key: 'order_id',
      width: 120,
    },
    {
      title: '产品编码',
      dataIndex: 'product_code',
      key: 'product_code',
      width: 120,
    },
    {
      title: '数量',
      dataIndex: 'quantity',
      key: 'quantity',
      width: 80,
    },
    {
      title: '交期',
      dataIndex: 'due_date',
      key: 'due_date',
      width: 120,
      render: (text) => moment(text).format('YYYY-MM-DD'),
    },
    {
      title: '优先级',
      dataIndex: 'priority',
      key: 'priority',
      width: 80,
      render: (priority) => {
        const colors = {
          'LOW': 'default',
          'NORMAL': 'blue',
          'HIGH': 'orange',
          'URGENT': 'red'
        };
        return <Tag color={colors[priority]}>{priority}</Tag>;
      },
    },
    {
      title: '预计工时',
      dataIndex: 'estimated_hours',
      key: 'estimated_hours',
      width: 100,
      render: (hours) => `${hours}h`,
    },
    {
      title: '状态',
      dataIndex: 'status',
      key: 'status',
      width: 100,
      render: (status) => {
        const statusConfig = {
          'pending': { color: 'default', text: '待排产' },
          'scheduled': { color: 'blue', text: '已排产' },
          'in_progress': { color: 'processing', text: '生产中' },
          'completed': { color: 'success', text: '已完成' },
          'cancelled': { color: 'error', text: '已取消' }
        };
        const config = statusConfig[status] || { color: 'default', text: status };
        return <Tag color={config.color}>{config.text}</Tag>;
      },
    },
    {
      title: '排产时间',
      dataIndex: 'scheduled_start',
      key: 'scheduled_start',
      width: 160,
      render: (start, record) => {
        if (start && record.scheduled_end) {
          return (
            <div>
              <div>{moment(start).format('MM-DD HH:mm')}</div>
              <div style={{ fontSize: '12px', color: '#666' }}>
                至 {moment(record.scheduled_end).format('MM-DD HH:mm')}
              </div>
            </div>
          );
        }
        return '-';
      },
    },
    {
      title: '分配设备',
      dataIndex: 'assigned_equipment',
      key: 'assigned_equipment',
      width: 120,
      render: (equipment) => equipment || '-',
    },
    {
      title: '操作',
      key: 'action',
      width: 120,
      render: (_, record) => (
        <Space>
          {record.status === 'scheduled' && (
            <Popconfirm
              title="确定要重新排产吗？"
              onConfirm={() => rescheduleOrder(record.order_id)}
            >
              <Button size="small" type="link">
                重排
              </Button>
            </Popconfirm>
          )}
        </Space>
      ),
    },
  ];

  // 设备表格列定义
  const equipmentColumns = [
    {
      title: '设备ID',
      dataIndex: 'equipment_id',
      key: 'equipment_id',
    },
    {
      title: '设备名称',
      dataIndex: 'name',
      key: 'name',
    },
    {
      title: '每小时产能',
      dataIndex: 'capacity_per_hour',
      key: 'capacity_per_hour',
    },
    {
      title: '每日可用工时',
      dataIndex: 'available_hours_per_day',
      key: 'available_hours_per_day',
      render: (hours) => `${hours}h`,
    },
    {
      title: '当前负荷',
      dataIndex: 'current_load',
      key: 'current_load',
      render: (load) => `${load}h`,
    },
    {
      title: '利用率',
      dataIndex: 'utilization_rate',
      key: 'utilization_rate',
      render: (rate) => (
        <Progress
          percent={rate}
          size="small"
          status={rate > 90 ? 'exception' : rate > 70 ? 'active' : 'normal'}
        />
      ),
    },
  ];

  // 物料表格列定义
  const materialColumns = [
    {
      title: '物料编码',
      dataIndex: 'material_code',
      key: 'material_code',
    },
    {
      title: '物料名称',
      dataIndex: 'name',
      key: 'name',
    },
    {
      title: '当前库存',
      dataIndex: 'current_stock',
      key: 'current_stock',
    },
    {
      title: '安全库存',
      dataIndex: 'safety_stock',
      key: 'safety_stock',
    },
    {
      title: '采购周期',
      dataIndex: 'lead_time_days',
      key: 'lead_time_days',
      render: (days) => `${days}天`,
    },
    {
      title: '供应商',
      dataIndex: 'supplier',
      key: 'supplier',
    },
    {
      title: '库存状态',
      dataIndex: 'stock_status',
      key: 'stock_status',
      render: (status) => (
        <Tag color={status === '充足' ? 'green' : 'red'}>{status}</Tag>
      ),
    },
  ];

  return (
    <div className="scheduling-container">
      <div className="scheduling-header">
        <h2>智能排产管理</h2>
        <Space>
          <Button
            type="primary"
            icon={<PlayCircleOutlined />}
            onClick={() => setScheduleModalVisible(true)}
            loading={loading}
          >
            执行排产
          </Button>
          <Button
            icon={<ReloadOutlined />}
            onClick={loadData}
            loading={loading}
          >
            刷新数据
          </Button>
        </Space>
      </div>

      {/* 概况统计 */}
      <Row gutter={16} style={{ marginBottom: 16 }}>
        <Col span={6}>
          <Card>
            <Statistic
              title="总订单数"
              value={summary.total_orders || 0}
              prefix={<BarChartOutlined />}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic
              title="已排产订单"
              value={summary.scheduled_orders || 0}
              prefix={<ClockCircleOutlined />}
              valueStyle={{ color: '#1890ff' }}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic
              title="生产中订单"
              value={summary.in_progress_orders || 0}
              prefix={<ExclamationCircleOutlined />}
              valueStyle={{ color: '#faad14' }}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic
              title="完成率"
              value={summary.completion_rate || 0}
              suffix="%"
              prefix={<CheckCircleOutlined />}
              valueStyle={{ color: '#52c41a' }}
            />
          </Card>
        </Col>
      </Row>

      {/* 主要内容区域 */}
      <Card>
        <Tabs activeKey={activeTab} onChange={setActiveTab}>
          <TabPane tab="生产订单" key="1">
            <div style={{ marginBottom: 16 }}>
              <Button
                type="primary"
                icon={<PlusOutlined />}
                onClick={() => setOrderModalVisible(true)}
              >
                新增订单
              </Button>
            </div>
            <Table
              columns={orderColumns}
              dataSource={orders}
              rowKey="order_id"
              loading={loading}
              scroll={{ x: 1200 }}
              pagination={{
                showSizeChanger: true,
                showQuickJumper: true,
                showTotal: (total) => `共 ${total} 条记录`,
              }}
            />
          </TabPane>

          <TabPane tab="设备管理" key="2">
            <div style={{ marginBottom: 16 }}>
              <Button
                type="primary"
                icon={<PlusOutlined />}
                onClick={() => setEquipmentModalVisible(true)}
              >
                新增设备
              </Button>
            </div>
            <Table
              columns={equipmentColumns}
              dataSource={equipment}
              rowKey="equipment_id"
              loading={loading}
              pagination={{
                showSizeChanger: true,
                showQuickJumper: true,
                showTotal: (total) => `共 ${total} 条记录`,
              }}
            />
          </TabPane>

          <TabPane tab="物料管理" key="3">
            <div style={{ marginBottom: 16 }}>
              <Button
                type="primary"
                icon={<PlusOutlined />}
                onClick={() => setMaterialModalVisible(true)}
              >
                新增物料
              </Button>
            </div>
            <Table
              columns={materialColumns}
              dataSource={materials}
              rowKey="material_code"
              loading={loading}
              pagination={{
                showSizeChanger: true,
                showQuickJumper: true,
                showTotal: (total) => `共 ${total} 条记录`,
              }}
            />
          </TabPane>

          <TabPane tab="排产甘特图" key="4">
            <div className="gantt-container">
              {ganttData.length > 0 ? (
                <Timeline mode="left">
                  {ganttData.map((item, index) => (
                    <Timeline.Item
                      key={index}
                      label={moment(item.start_time).format('MM-DD HH:mm')}
                      color={item.priority === 'URGENT' ? 'red' : 'blue'}
                    >
                      <div>
                        <strong>{item.order_id}</strong> - {item.product_code}
                      </div>
                      <div style={{ fontSize: '12px', color: '#666' }}>
                        设备: {item.equipment} | 至: {moment(item.end_time).format('MM-DD HH:mm')}
                      </div>
                    </Timeline.Item>
                  ))}
                </Timeline>
              ) : (
                <div style={{ textAlign: 'center', padding: '50px' }}>
                  <p>暂无排产数据</p>
                </div>
              )}
            </div>
          </TabPane>
        </Tabs>
      </Card>

      {/* 执行排产模态框 */}
      <Modal
        title="执行自动排产"
        visible={scheduleModalVisible}
        onCancel={() => setScheduleModalVisible(false)}
        footer={null}
      >
        <Form
          form={scheduleForm}
          layout="vertical"
          onFinish={executeScheduling}
        >
          <Form.Item
            name="start_date"
            label="排产开始时间"
            tooltip="不填写则从当前时间开始"
          >
            <DatePicker
              showTime
              format="YYYY-MM-DD HH:mm"
              placeholder="选择开始时间"
              style={{ width: '100%' }}
            />
          </Form.Item>
          
          <Form.Item
            name="force_reschedule"
            label="强制重新排产"
            tooltip="是否重置已排产的订单"
          >
            <Select placeholder="选择是否强制重排">
              <Option value={false}>否</Option>
              <Option value={true}>是</Option>
            </Select>
          </Form.Item>
          
          <Form.Item
            name="notify_wechat"
            label="微信通知"
            initialValue={true}
          >
            <Select>
              <Option value={true}>发送通知</Option>
              <Option value={false}>不发送通知</Option>
            </Select>
          </Form.Item>
          
          <Form.Item>
            <Space>
              <Button type="primary" htmlType="submit" loading={loading}>
                开始排产
              </Button>
              <Button onClick={() => setScheduleModalVisible(false)}>
                取消
              </Button>
            </Space>
          </Form.Item>
        </Form>
      </Modal>

      {/* 新增订单模态框 */}
      <Modal
        title="新增生产订单"
        visible={orderModalVisible}
        onCancel={() => setOrderModalVisible(false)}
        footer={null}
        width={600}
      >
        <Form
          form={orderForm}
          layout="vertical"
          onFinish={createOrder}
        >
          <Row gutter={16}>
            <Col span={12}>
              <Form.Item
                name="order_id"
                label="订单号"
                rules={[{ required: true, message: '请输入订单号' }]}
              >
                <Input placeholder="输入订单号" />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item
                name="product_code"
                label="产品编码"
                rules={[{ required: true, message: '请输入产品编码' }]}
              >
                <Input placeholder="输入产品编码" />
              </Form.Item>
            </Col>
          </Row>
          
          <Row gutter={16}>
            <Col span={12}>
              <Form.Item
                name="quantity"
                label="生产数量"
                rules={[{ required: true, message: '请输入生产数量' }]}
              >
                <InputNumber
                  min={1}
                  placeholder="输入数量"
                  style={{ width: '100%' }}
                />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item
                name="estimated_hours"
                label="预计工时"
                rules={[{ required: true, message: '请输入预计工时' }]}
              >
                <InputNumber
                  min={0.1}
                  step={0.1}
                  placeholder="输入工时"
                  style={{ width: '100%' }}
                  addonAfter="小时"
                />
              </Form.Item>
            </Col>
          </Row>
          
          <Row gutter={16}>
            <Col span={12}>
              <Form.Item
                name="due_date"
                label="交期"
                rules={[{ required: true, message: '请选择交期' }]}
              >
                <DatePicker
                  showTime
                  format="YYYY-MM-DD HH:mm"
                  placeholder="选择交期"
                  style={{ width: '100%' }}
                />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item
                name="priority"
                label="优先级"
                initialValue="NORMAL"
                rules={[{ required: true, message: '请选择优先级' }]}
              >
                <Select>
                  <Option value="LOW">低</Option>
                  <Option value="NORMAL">普通</Option>
                  <Option value="HIGH">高</Option>
                  <Option value="URGENT">紧急</Option>
                </Select>
              </Form.Item>
            </Col>
          </Row>
          
          <Form.Item>
            <Space>
              <Button type="primary" htmlType="submit" loading={loading}>
                创建订单
              </Button>
              <Button onClick={() => setOrderModalVisible(false)}>
                取消
              </Button>
            </Space>
          </Form.Item>
        </Form>
      </Modal>

      {/* 新增设备模态框 */}
      <Modal
        title="新增设备"
        visible={equipmentModalVisible}
        onCancel={() => setEquipmentModalVisible(false)}
        footer={null}
        width={600}
      >
        <Form
          form={equipmentForm}
          layout="vertical"
          onFinish={createEquipment}
        >
          <Row gutter={16}>
            <Col span={12}>
              <Form.Item
                name="equipment_id"
                label="设备ID"
                rules={[{ required: true, message: '请输入设备ID' }]}
              >
                <Input placeholder="输入设备ID" />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item
                name="name"
                label="设备名称"
                rules={[{ required: true, message: '请输入设备名称' }]}
              >
                <Input placeholder="输入设备名称" />
              </Form.Item>
            </Col>
          </Row>
          
          <Row gutter={16}>
            <Col span={12}>
              <Form.Item
                name="capacity_per_hour"
                label="每小时产能"
                rules={[{ required: true, message: '请输入每小时产能' }]}
              >
                <InputNumber
                  min={0.1}
                  step={0.1}
                  placeholder="输入产能"
                  style={{ width: '100%' }}
                />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item
                name="available_hours_per_day"
                label="每日可用工时"
                rules={[{ required: true, message: '请输入每日可用工时' }]}
              >
                <InputNumber
                  min={1}
                  max={24}
                  placeholder="输入工时"
                  style={{ width: '100%' }}
                  addonAfter="小时"
                />
              </Form.Item>
            </Col>
          </Row>
          
          <Form.Item>
            <Space>
              <Button type="primary" htmlType="submit" loading={loading}>
                创建设备
              </Button>
              <Button onClick={() => setEquipmentModalVisible(false)}>
                取消
              </Button>
            </Space>
          </Form.Item>
        </Form>
      </Modal>

      {/* 新增物料模态框 */}
      <Modal
        title="新增物料"
        visible={materialModalVisible}
        onCancel={() => setMaterialModalVisible(false)}
        footer={null}
        width={600}
      >
        <Form
          form={materialForm}
          layout="vertical"
          onFinish={createMaterial}
        >
          <Row gutter={16}>
            <Col span={12}>
              <Form.Item
                name="material_code"
                label="物料编码"
                rules={[{ required: true, message: '请输入物料编码' }]}
              >
                <Input placeholder="输入物料编码" />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item
                name="name"
                label="物料名称"
                rules={[{ required: true, message: '请输入物料名称' }]}
              >
                <Input placeholder="输入物料名称" />
              </Form.Item>
            </Col>
          </Row>
          
          <Row gutter={16}>
            <Col span={12}>
              <Form.Item
                name="current_stock"
                label="当前库存"
                rules={[{ required: true, message: '请输入当前库存' }]}
              >
                <InputNumber
                  min={0}
                  placeholder="输入库存"
                  style={{ width: '100%' }}
                />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item
                name="safety_stock"
                label="安全库存"
                rules={[{ required: true, message: '请输入安全库存' }]}
              >
                <InputNumber
                  min={0}
                  placeholder="输入安全库存"
                  style={{ width: '100%' }}
                />
              </Form.Item>
            </Col>
          </Row>
          
          <Row gutter={16}>
            <Col span={12}>
              <Form.Item
                name="lead_time_days"
                label="采购周期"
                rules={[{ required: true, message: '请输入采购周期' }]}
              >
                <InputNumber
                  min={1}
                  placeholder="输入天数"
                  style={{ width: '100%' }}
                  addonAfter="天"
                />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item
                name="supplier"
                label="供应商"
                rules={[{ required: true, message: '请输入供应商' }]}
              >
                <Input placeholder="输入供应商" />
              </Form.Item>
            </Col>
          </Row>
          
          <Form.Item>
            <Space>
              <Button type="primary" htmlType="submit" loading={loading}>
                创建物料
              </Button>
              <Button onClick={() => setMaterialModalVisible(false)}>
                取消
              </Button>
            </Space>
          </Form.Item>
        </Form>
      </Modal>
    </div>
  );
};

export default Scheduling;