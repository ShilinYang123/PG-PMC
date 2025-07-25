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
  Upload,
  message,
  Popconfirm,
  Row,
  Col
} from 'antd';
import {
  PlusOutlined,
  EditOutlined,
  DeleteOutlined,
  UploadOutlined,
  DownloadOutlined,
  SearchOutlined
} from '@ant-design/icons';
import type { ColumnsType } from 'antd/es/table';
import type { UploadProps } from 'antd';
import dayjs from 'dayjs';

const { Option } = Select;
const { RangePicker } = DatePicker;

interface OrderRecord {
  key: string;
  orderNo: string;
  customer: string;
  product: string;
  specification: string;
  quantity: number;
  unit: string;
  unitPrice: number;
  totalAmount: number;
  orderDate: string;
  deliveryDate: string;
  status: string;
  priority: string;
  remark: string;
}

const OrderManagement: React.FC = () => {
  const [loading, setLoading] = useState(false);
  const [modalVisible, setModalVisible] = useState(false);
  const [editingRecord, setEditingRecord] = useState<OrderRecord | null>(null);
  const [form] = Form.useForm();

  // 模拟订单数据
  const [dataSource, setDataSource] = useState<OrderRecord[]>([
    {
      key: '1',
      orderNo: 'BD400-001',
      customer: '深圳科技有限公司',
      product: '精密零件A',
      specification: '规格A-001',
      quantity: 1000,
      unit: '件',
      unitPrice: 25.5,
      totalAmount: 25500,
      orderDate: '2024-01-15',
      deliveryDate: '2024-02-15',
      status: '生产中',
      priority: '高',
      remark: '客户要求提前交货'
    },
    {
      key: '2',
      orderNo: 'BD400-002',
      customer: '广州制造集团',
      product: '标准件B',
      specification: '规格B-002',
      quantity: 500,
      unit: '套',
      unitPrice: 120.0,
      totalAmount: 60000,
      orderDate: '2024-01-20',
      deliveryDate: '2024-02-20',
      status: '待生产',
      priority: '中',
      remark: '标准交期'
    },
    {
      key: '3',
      orderNo: 'BD400-003',
      customer: '东莞精工厂',
      product: '定制件C',
      specification: '规格C-003',
      quantity: 200,
      unit: '个',
      unitPrice: 85.0,
      totalAmount: 17000,
      orderDate: '2024-01-10',
      deliveryDate: '2024-02-10',
      status: '已完成',
      priority: '低',
      remark: '质量要求严格'
    }
  ]);

  const columns: ColumnsType<OrderRecord> = [
    {
      title: '订单号',
      dataIndex: 'orderNo',
      key: 'orderNo',
      width: 120,
      fixed: 'left'
    },
    {
      title: '客户',
      dataIndex: 'customer',
      key: 'customer',
      width: 150
    },
    {
      title: '产品',
      dataIndex: 'product',
      key: 'product',
      width: 120
    },
    {
      title: '规格',
      dataIndex: 'specification',
      key: 'specification',
      width: 100
    },
    {
      title: '数量',
      dataIndex: 'quantity',
      key: 'quantity',
      width: 80,
      render: (value, record) => `${value} ${record.unit}`
    },
    {
      title: '单价',
      dataIndex: 'unitPrice',
      key: 'unitPrice',
      width: 80,
      render: (value) => `¥${value.toFixed(2)}`
    },
    {
      title: '总金额',
      dataIndex: 'totalAmount',
      key: 'totalAmount',
      width: 100,
      render: (value) => `¥${value.toLocaleString()}`
    },
    {
      title: '下单日期',
      dataIndex: 'orderDate',
      key: 'orderDate',
      width: 100
    },
    {
      title: '交期',
      dataIndex: 'deliveryDate',
      key: 'deliveryDate',
      width: 100
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
        if (status === '生产中') color = 'processing';
        if (status === '已完成') color = 'success';
        if (status === '待生产') color = 'warning';
        if (status === '已取消') color = 'error';
        return <Tag color={color}>{status}</Tag>;
      }
    },
    {
      title: '操作',
      key: 'action',
      width: 150,
      fixed: 'right',
      render: (_, record) => (
        <Space size="small">
          <Button
            type="link"
            icon={<EditOutlined />}
            onClick={() => handleEdit(record)}
          >
            编辑
          </Button>
          <Popconfirm
            title="确定要删除这个订单吗？"
            onConfirm={() => handleDelete(record.key)}
            okText="确定"
            cancelText="取消"
          >
            <Button
              type="link"
              danger
              icon={<DeleteOutlined />}
            >
              删除
            </Button>
          </Popconfirm>
        </Space>
      )
    }
  ];

  const handleAdd = () => {
    setEditingRecord(null);
    form.resetFields();
    setModalVisible(true);
  };

  const handleEdit = (record: OrderRecord) => {
    setEditingRecord(record);
    form.setFieldsValue({
      ...record,
      orderDate: dayjs(record.orderDate),
      deliveryDate: dayjs(record.deliveryDate)
    });
    setModalVisible(true);
  };

  const handleDelete = (key: string) => {
    setDataSource(dataSource.filter(item => item.key !== key));
    message.success('删除成功');
  };

  const handleSubmit = async () => {
    try {
      const values = await form.validateFields();
      const formData = {
        ...values,
        orderDate: values.orderDate.format('YYYY-MM-DD'),
        deliveryDate: values.deliveryDate.format('YYYY-MM-DD'),
        totalAmount: values.quantity * values.unitPrice
      };

      if (editingRecord) {
        // 编辑
        setDataSource(dataSource.map(item => 
          item.key === editingRecord.key 
            ? { ...item, ...formData }
            : item
        ));
        message.success('更新成功');
      } else {
        // 新增
        const newRecord = {
          key: Date.now().toString(),
          ...formData
        };
        setDataSource([...dataSource, newRecord]);
        message.success('添加成功');
      }
      
      setModalVisible(false);
    } catch (error) {
      console.error('表单验证失败:', error);
    }
  };

  const uploadProps: UploadProps = {
    name: 'file',
    action: '/api/orders/import',
    headers: {
      authorization: 'authorization-text',
    },
    onChange(info) {
      if (info.file.status === 'done') {
        message.success(`${info.file.name} 文件上传成功`);
      } else if (info.file.status === 'error') {
        message.error(`${info.file.name} 文件上传失败`);
      }
    },
  };

  return (
    <div>
      <h1 className="page-title">订单管理</h1>
      
      {/* 搜索表单 */}
      <Card className="search-form">
        <Form layout="inline">
          <Row gutter={16} style={{ width: '100%' }}>
            <Col span={6}>
              <Form.Item label="订单号">
                <Input placeholder="请输入订单号" />
              </Form.Item>
            </Col>
            <Col span={6}>
              <Form.Item label="客户">
                <Input placeholder="请输入客户名称" />
              </Form.Item>
            </Col>
            <Col span={6}>
              <Form.Item label="状态">
                <Select placeholder="请选择状态" allowClear>
                  <Option value="待生产">待生产</Option>
                  <Option value="生产中">生产中</Option>
                  <Option value="已完成">已完成</Option>
                  <Option value="已取消">已取消</Option>
                </Select>
              </Form.Item>
            </Col>
            <Col span={6}>
              <Form.Item>
                <Space>
                  <Button type="primary" icon={<SearchOutlined />}>
                    搜索
                  </Button>
                  <Button>重置</Button>
                </Space>
              </Form.Item>
            </Col>
          </Row>
        </Form>
      </Card>

      {/* 操作按钮 */}
      <Card>
        <div className="action-buttons" style={{ marginBottom: 16 }}>
          <Space>
            <Button type="primary" icon={<PlusOutlined />} onClick={handleAdd}>
              新增订单
            </Button>
            <Upload {...uploadProps}>
              <Button icon={<UploadOutlined />}>批量导入</Button>
            </Upload>
            <Button icon={<DownloadOutlined />}>导出Excel</Button>
          </Space>
        </div>

        {/* 订单表格 */}
        <Table
          columns={columns}
          dataSource={dataSource}
          loading={loading}
          scroll={{ x: 1500 }}
          pagination={{
            total: dataSource.length,
            pageSize: 10,
            showSizeChanger: true,
            showQuickJumper: true,
            showTotal: (total) => `共 ${total} 条记录`
          }}
        />
      </Card>

      {/* 新增/编辑订单弹窗 */}
      <Modal
        title={editingRecord ? '编辑订单' : '新增订单'}
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
            status: '待生产',
            priority: '中',
            unit: '件'
          }}
        >
          <Row gutter={16}>
            <Col span={12}>
              <Form.Item
                label="订单号"
                name="orderNo"
                rules={[{ required: true, message: '请输入订单号' }]}
              >
                <Input placeholder="请输入订单号" />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item
                label="客户"
                name="customer"
                rules={[{ required: true, message: '请输入客户名称' }]}
              >
                <Input placeholder="请输入客户名称" />
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
            <Col span={12}>
              <Form.Item
                label="规格"
                name="specification"
                rules={[{ required: true, message: '请输入产品规格' }]}
              >
                <Input placeholder="请输入产品规格" />
              </Form.Item>
            </Col>
          </Row>

          <Row gutter={16}>
            <Col span={8}>
              <Form.Item
                label="数量"
                name="quantity"
                rules={[{ required: true, message: '请输入数量' }]}
              >
                <Input type="number" placeholder="请输入数量" />
              </Form.Item>
            </Col>
            <Col span={8}>
              <Form.Item
                label="单位"
                name="unit"
                rules={[{ required: true, message: '请选择单位' }]}
              >
                <Select placeholder="请选择单位">
                  <Option value="件">件</Option>
                  <Option value="套">套</Option>
                  <Option value="个">个</Option>
                  <Option value="台">台</Option>
                </Select>
              </Form.Item>
            </Col>
            <Col span={8}>
              <Form.Item
                label="单价"
                name="unitPrice"
                rules={[{ required: true, message: '请输入单价' }]}
              >
                <Input type="number" placeholder="请输入单价" />
              </Form.Item>
            </Col>
          </Row>

          <Row gutter={16}>
            <Col span={12}>
              <Form.Item
                label="下单日期"
                name="orderDate"
                rules={[{ required: true, message: '请选择下单日期' }]}
              >
                <DatePicker style={{ width: '100%' }} />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item
                label="交期"
                name="deliveryDate"
                rules={[{ required: true, message: '请选择交期' }]}
              >
                <DatePicker style={{ width: '100%' }} />
              </Form.Item>
            </Col>
          </Row>

          <Row gutter={16}>
            <Col span={12}>
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
            <Col span={12}>
              <Form.Item
                label="状态"
                name="status"
                rules={[{ required: true, message: '请选择状态' }]}
              >
                <Select placeholder="请选择状态">
                  <Option value="待生产">待生产</Option>
                  <Option value="生产中">生产中</Option>
                  <Option value="已完成">已完成</Option>
                  <Option value="已取消">已取消</Option>
                </Select>
              </Form.Item>
            </Col>
          </Row>

          <Form.Item label="备注" name="remark">
            <Input.TextArea rows={3} placeholder="请输入备注信息" />
          </Form.Item>
        </Form>
      </Modal>
    </div>
  );
};

export default OrderManagement;