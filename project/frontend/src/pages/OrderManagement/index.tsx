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
  InputNumber,
  DatePicker,
  Select,
  message,
  Popconfirm,
  Row,
  Col,
  Tooltip,
  Divider,
  Statistic,
  Progress,
  Descriptions,
  Timeline,
  Badge
} from 'antd';
import {
  PlusOutlined,
  EditOutlined,
  DeleteOutlined,
  UploadOutlined,
  DownloadOutlined,
  SearchOutlined,
  EyeOutlined,
  ReloadOutlined,
  ExportOutlined,
  FilterOutlined,
  CheckCircleOutlined,
  ClockCircleOutlined,
  ExclamationCircleOutlined,
  SyncOutlined
} from '@ant-design/icons';
import type { ColumnsType } from 'antd/es/table';
import dayjs from 'dayjs';
import axios from 'axios';
import ImportExportModal from '../../components/ImportExport';
import { Upload, message as antdMessage } from 'antd';
import type { UploadProps } from 'antd';
import * as XLSX from 'xlsx';

const { Option } = Select;
const { RangePicker } = DatePicker;

interface OrderRecord {
  id: number;
  order_number: string;
  customer_name: string;
  customer_code?: string;
  customer_contact?: string;
  customer_phone?: string;
  customer_email?: string;
  customer_address?: string;
  product_name: string;
  product_code: string;
  product_model?: string;
  product_spec?: string;
  quantity: number;
  unit: string;
  unit_price?: number;
  total_amount?: number;
  currency?: string;
  order_date: string;
  delivery_date: string;
  status: string;
  priority: string;
  contact_person?: string;
  contact_phone?: string;
  contact_email?: string;
  delivery_address?: string;
  technical_requirements?: string;
  quality_standards?: string;
  remark?: string;
  created_at?: string;
  updated_at?: string;
  created_by?: string;
  updated_by?: string;
}

interface OrderStats {
  total_orders: number;
  pending_orders: number;
  confirmed_orders: number;
  in_production_orders: number;
  completed_orders: number;
  cancelled_orders: number;
  urgent_orders: number;
  overdue_orders: number;
  monthly_new_orders: number;
  monthly_completed_orders: number;
  total_amount: number;
  monthly_amount: number;
}

interface QueryParams {
  page: number;
  page_size: number;
  keyword?: string;
  status?: string;
  priority?: string;
  customer_name?: string;
  product_name?: string;
  order_date_start?: string;
  order_date_end?: string;
  delivery_date_start?: string;
  delivery_date_end?: string;
  urgent_only?: boolean;
  sort_field?: string;
  sort_order?: 'asc' | 'desc';
}

const OrderManagement: React.FC = () => {
  const [loading, setLoading] = useState(false);
  const [modalVisible, setModalVisible] = useState(false);
  const [detailModalVisible, setDetailModalVisible] = useState(false);
  const [importExportVisible, setImportExportVisible] = useState(false);
  const [importExportType, setImportExportType] = useState<'import' | 'export'>('import');
  const [bd400ImportVisible, setBd400ImportVisible] = useState(false);
  const [importLoading, setImportLoading] = useState(false);
  const [editingRecord, setEditingRecord] = useState<OrderRecord | null>(null);
  const [selectedRecord, setSelectedRecord] = useState<OrderRecord | null>(null);
  const [form] = Form.useForm();
  const [searchForm] = Form.useForm();

  // 数据状态
  const [dataSource, setDataSource] = useState<OrderRecord[]>([]);
  const [orderStats, setOrderStats] = useState<OrderStats | null>(null);
  const [pagination, setPagination] = useState({
    current: 1,
    pageSize: 10,
    total: 0
  });

  // 查询参数
  const [queryParams, setQueryParams] = useState<QueryParams>({
    page: 1,
    page_size: 10
  });

  // API调用函数
  const fetchOrders = async (params: QueryParams = queryParams) => {
    setLoading(true);
    try {
      const response = await axios.get('/api/orders', { params });
      if (response.data.code === 200) {
        setDataSource(response.data.data);
        setPagination({
          current: response.data.page_info.page,
          pageSize: response.data.page_info.page_size,
          total: response.data.page_info.total
        });
      } else {
        message.error(response.data.message || '获取订单列表失败');
      }
    } catch (error) {
      console.error('获取订单列表失败:', error);
      message.error('获取订单列表失败');
    } finally {
      setLoading(false);
    }
  };

  const fetchOrderStats = async () => {
    try {
      const response = await axios.get('/api/orders/stats/overview');
      if (response.data.code === 200) {
        setOrderStats(response.data.data);
      }
    } catch (error) {
      console.error('获取订单统计失败:', error);
    }
  };

  const createOrder = async (values: any) => {
    setLoading(true);
    try {
      const orderData = {
        ...values,
        order_date: values.order_date.format('YYYY-MM-DD HH:mm:ss'),
        delivery_date: values.delivery_date.format('YYYY-MM-DD HH:mm:ss'),
        total_amount: values.unit_price * values.quantity
      };
      
      const response = await axios.post('/api/orders', orderData);
      if (response.data.code === 200) {
        message.success('创建订单成功');
        setModalVisible(false);
        form.resetFields();
        fetchOrders();
        fetchOrderStats();
      } else {
        message.error(response.data.message || '创建订单失败');
      }
    } catch (error) {
      console.error('创建订单失败:', error);
      message.error('创建订单失败');
    } finally {
      setLoading(false);
    }
  };

  const updateOrder = async (id: number, values: any) => {
    setLoading(true);
    try {
      const orderData = {
        ...values,
        order_date: values.order_date.format('YYYY-MM-DD HH:mm:ss'),
        delivery_date: values.delivery_date.format('YYYY-MM-DD HH:mm:ss'),
        total_amount: values.unit_price * values.quantity
      };
      
      const response = await axios.put(`/api/orders/${id}`, orderData);
      if (response.data.code === 200) {
        message.success('更新订单成功');
        setModalVisible(false);
        form.resetFields();
        setEditingRecord(null);
        fetchOrders();
        fetchOrderStats();
      } else {
        message.error(response.data.message || '更新订单失败');
      }
    } catch (error) {
      console.error('更新订单失败:', error);
      message.error('更新订单失败');
    } finally {
      setLoading(false);
    }
  };

  const deleteOrder = async (id: number) => {
    setLoading(true);
    try {
      const response = await axios.delete(`/api/orders/${id}`);
      if (response.data.code === 200) {
        message.success('删除订单成功');
        fetchOrders();
        fetchOrderStats();
      } else {
        message.error(response.data.message || '删除订单失败');
      }
    } catch (error) {
      console.error('删除订单失败:', error);
      message.error('删除订单失败');
    } finally {
      setLoading(false);
    }
  };

  // 初始化数据
  useEffect(() => {
    fetchOrders();
    fetchOrderStats();
  }, []);

  const columns: ColumnsType<OrderRecord> = [
    {
      title: '订单编号',
      dataIndex: 'order_number',
      key: 'order_number',
      width: 120,
      fixed: 'left'
    },
    {
      title: '客户名称',
      dataIndex: 'customer_name',
      key: 'customer_name',
      width: 150
    },
    {
      title: '产品名称',
      dataIndex: 'product_name',
      key: 'product_name',
      width: 120
    },
    {
      title: '产品规格',
      dataIndex: 'product_spec',
      key: 'product_spec',
      width: 120
    },
    {
      title: '数量',
      dataIndex: 'quantity',
      key: 'quantity',
      width: 80,
      render: (value: number, record: OrderRecord) => `${value} ${record.unit || '件'}`
    },
    {
      title: '单价',
      dataIndex: 'unit_price',
      key: 'unit_price',
      width: 100,
      render: (value: number) => `¥${value?.toFixed(2) || '0.00'}`
    },
    {
      title: '总金额',
      dataIndex: 'total_amount',
      key: 'total_amount',
      width: 120,
      render: (value: number) => `¥${value?.toFixed(2) || '0.00'}`
    },
    {
      title: '下单日期',
      dataIndex: 'order_date',
      key: 'order_date',
      width: 120,
      render: (value: string) => value ? dayjs(value).format('YYYY-MM-DD') : '-'
    },
    {
      title: '交货日期',
      dataIndex: 'delivery_date',
      key: 'delivery_date',
      width: 120,
      render: (value: string) => value ? dayjs(value).format('YYYY-MM-DD') : '-'
    },
    {
      title: '优先级',
      dataIndex: 'priority',
      key: 'priority',
      width: 80,
      render: (priority: string) => {
        const priorityConfig = {
          'high': { color: 'red', text: '高' },
          'medium': { color: 'orange', text: '中' },
          'low': { color: 'green', text: '低' }
        };
        const config = priorityConfig[priority as keyof typeof priorityConfig] || { color: 'default', text: priority };
        return <Tag color={config.color}>{config.text}</Tag>;
      }
    },
    {
      title: '状态',
      dataIndex: 'status',
      key: 'status',
      width: 100,
      render: (status: string) => {
        const statusConfig = {
          'pending': { color: 'orange', text: '待生产', icon: <ClockCircleOutlined /> },
          'confirmed': { color: 'blue', text: '已确认', icon: <CheckCircleOutlined /> },
          'in_production': { color: 'processing', text: '生产中', icon: <SyncOutlined spin /> },
          'completed': { color: 'green', text: '已完成', icon: <CheckCircleOutlined /> },
          'cancelled': { color: 'red', text: '已取消', icon: <ExclamationCircleOutlined /> }
        };
        const config = statusConfig[status as keyof typeof statusConfig] || { color: 'default', text: status, icon: null };
        return (
          <Badge 
            status={config.color as any} 
            text={
              <span>
                {config.icon} {config.text}
              </span>
            } 
          />
        );
      }
    },
    {
      title: '操作',
      key: 'action',
      width: 200,
      fixed: 'right',
      render: (_, record: OrderRecord) => (
        <Space size="small">
          <Tooltip title="查看详情">
            <Button
              type="link"
              size="small"
              icon={<EyeOutlined />}
              onClick={() => handleViewDetail(record)}
            >
              详情
            </Button>
          </Tooltip>
          <Tooltip title="编辑订单">
            <Button
              type="link"
              size="small"
              icon={<EditOutlined />}
              onClick={() => handleEdit(record)}
            >
              编辑
            </Button>
          </Tooltip>
          <Popconfirm
            title="确定要删除这个订单吗？"
            description="删除后无法恢复，请谨慎操作。"
            onConfirm={() => deleteOrder(record.id)}
            okText="确定"
            cancelText="取消"
            placement="topRight"
          >
            <Tooltip title="删除订单">
              <Button
                type="link"
                size="small"
                danger
                icon={<DeleteOutlined />}
              >
                删除
              </Button>
            </Tooltip>
          </Popconfirm>
        </Space>
      )
    }
  ];

  // 事件处理函数
  const handleViewDetail = (record: OrderRecord) => {
    setSelectedRecord(record);
    setDetailModalVisible(true);
  };

  const handleEdit = (record: OrderRecord) => {
    setEditingRecord(record);
    form.setFieldsValue({
      ...record,
      order_date: record.order_date ? dayjs(record.order_date) : null,
      delivery_date: record.delivery_date ? dayjs(record.delivery_date) : null
    });
    setModalVisible(true);
  };

  const handleAdd = () => {
    setEditingRecord(null);
    form.resetFields();
    setModalVisible(true);
  };

  const handleSubmit = async (values: any) => {
    if (editingRecord) {
      await updateOrder(editingRecord.id, values);
    } else {
      await createOrder(values);
    }
  };

  const handleSearch = (values: any) => {
    const searchParams = {
      ...queryParams,
      page: 1,
      ...values
    };
    setQueryParams(searchParams);
    fetchOrders(searchParams);
  };

  const handleReset = () => {
    searchForm.resetFields();
    const resetParams = {
      page: 1,
      page_size: 10
    };
    setQueryParams(resetParams);
    fetchOrders(resetParams);
  };

  const handleTableChange = (paginationInfo: any) => {
    const newParams = {
      ...queryParams,
      page: paginationInfo.current,
      page_size: paginationInfo.pageSize
    };
    setQueryParams(newParams);
    fetchOrders(newParams);
  };

  // 导入导出处理函数
  const handleImport = () => {
    setImportExportType('import');
    setImportExportVisible(true);
  };

  const handleExport = () => {
    setImportExportType('export');
    setImportExportVisible(true);
  };

  const handleImportExportSuccess = () => {
    // 导入导出成功后刷新数据
    fetchOrders();
    fetchOrderStats();
    message.success('操作完成');
  };

  // BD400导入处理函数
  const handleBd400Import = async (file: File) => {
    setImportLoading(true);
    const formData = new FormData();
    formData.append('file', file);

    try {
      const response = await axios.post('/api/orders/import/bd400', formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });

      if (response.data.success) {
        const { imported_count, skipped_count, errors, warnings } = response.data.data;
        let messageText = `导入完成！成功导入 ${imported_count} 条订单`;
        if (skipped_count > 0) {
          messageText += `，跳过 ${skipped_count} 条重复订单`;
        }
        message.success(messageText);
        
        if (errors && errors.length > 0) {
          console.warn('导入错误:', errors);
          message.warning(`存在 ${errors.length} 个错误，请检查控制台`);
        }
        
        if (warnings && warnings.length > 0) {
          console.warn('导入警告:', warnings);
          message.warning(`存在 ${warnings.length} 个警告，请检查控制台`);
        }
        
        setBd400ImportVisible(false);
        fetchOrders();
        fetchOrderStats();
      } else {
        message.error(response.data.message || 'BD400导入失败');
      }
    } catch (error) {
      console.error('BD400导入失败:', error);
      message.error('BD400导入失败');
    } finally {
      setImportLoading(false);
    }
  };

  // 下载BD400导入模板
  const downloadBd400Template = async () => {
    try {
      const response = await axios.get('/api/orders/export/template');
      if (response.data.success) {
        const templateData = response.data.data;
        // 创建Excel文件并下载
        const worksheet = XLSX.utils.json_to_sheet([templateData]);
        const workbook = XLSX.utils.book_new();
        XLSX.utils.book_append_sheet(workbook, worksheet, 'BD400订单模板');
        XLSX.writeFile(workbook, 'BD400订单导入模板.xlsx');
        message.success('模板下载成功');
      } else {
        message.error('模板下载失败');
      }
    } catch (error) {
      console.error('模板下载失败:', error);
      message.error('模板下载失败');
    }
  };

  // 上传配置
  const uploadProps: UploadProps = {
    name: 'file',
    accept: '.xlsx,.xls',
    showUploadList: false,
    beforeUpload: (file) => {
      const isExcel = file.type === 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' || 
                     file.type === 'application/vnd.ms-excel';
      if (!isExcel) {
        message.error('只能上传Excel文件！');
        return false;
      }
      const isLt10M = file.size / 1024 / 1024 < 10;
      if (!isLt10M) {
        message.error('文件大小不能超过10MB！');
        return false;
      }
      handleBd400Import(file);
      return false; // 阻止自动上传
    },
  };

  return (
    <div className="order-management">
      {/* 统计卡片 */}
      {orderStats && (
        <Row gutter={16} style={{ marginBottom: 16 }}>
          <Col span={6}>
            <Card>
              <Statistic
                title="总订单数"
                value={orderStats.total_orders}
                valueStyle={{ color: '#1890ff' }}
              />
            </Card>
          </Col>
          <Col span={6}>
            <Card>
              <Statistic
                title="待生产订单"
                value={orderStats.pending_orders}
                prefix={<ClockCircleOutlined />}
                valueStyle={{ color: '#faad14' }}
              />
            </Card>
          </Col>
          <Col span={6}>
            <Card>
              <Statistic
                title="生产中订单"
                value={orderStats.in_production_orders}
                prefix={<SyncOutlined />}
                valueStyle={{ color: '#52c41a' }}
              />
            </Card>
          </Col>
          <Col span={6}>
            <Card>
              <Statistic
                title="已完成订单"
                value={orderStats.completed_orders}
                prefix={<CheckCircleOutlined />}
                valueStyle={{ color: '#52c41a' }}
              />
            </Card>
          </Col>
        </Row>
      )}

      {/* 搜索表单 */}
      <Card style={{ marginBottom: 16 }}>
        <Form
          form={searchForm}
          layout="inline"
          onFinish={handleSearch}
          style={{ marginBottom: 16 }}
        >
          <Form.Item name="order_number" label="订单编号">
            <Input placeholder="请输入订单编号" allowClear />
          </Form.Item>
          <Form.Item name="customer_name" label="客户名称">
            <Input placeholder="请输入客户名称" allowClear />
          </Form.Item>
          <Form.Item name="product_name" label="产品名称">
            <Input placeholder="请输入产品名称" allowClear />
          </Form.Item>
          <Form.Item name="status" label="订单状态">
            <Select placeholder="请选择状态" allowClear style={{ width: 120 }}>
              <Option value="pending">待生产</Option>
              <Option value="confirmed">已确认</Option>
              <Option value="in_production">生产中</Option>
              <Option value="completed">已完成</Option>
              <Option value="cancelled">已取消</Option>
            </Select>
          </Form.Item>
          <Form.Item name="priority" label="优先级">
            <Select placeholder="请选择优先级" allowClear style={{ width: 100 }}>
              <Option value="high">高</Option>
              <Option value="medium">中</Option>
              <Option value="low">低</Option>
            </Select>
          </Form.Item>
          <Form.Item>
            <Space>
              <Button type="primary" htmlType="submit" icon={<SearchOutlined />}>
                搜索
              </Button>
              <Button onClick={handleReset} icon={<ReloadOutlined />}>
                重置
              </Button>
            </Space>
          </Form.Item>
        </Form>
      </Card>

      {/* 订单列表 */}
      <Card title="订单列表" extra={
        <Space>
          <Button type="primary" icon={<PlusOutlined />} onClick={handleAdd}>
            新增订单
          </Button>
          <Button icon={<UploadOutlined />} onClick={handleImport}>
            批量导入
          </Button>
          <Button icon={<UploadOutlined />} onClick={() => setBd400ImportVisible(true)}>
            BD400导入
          </Button>
          <Button icon={<DownloadOutlined />} onClick={handleExport}>
            导出数据
          </Button>
        </Space>
      }>
        <Table
          columns={columns}
          dataSource={dataSource}
          loading={loading}
          scroll={{ x: 1400 }}
          pagination={{
            ...pagination,
            showSizeChanger: true,
            showQuickJumper: true,
            showTotal: (total, range) => `第 ${range[0]}-${range[1]} 条/共 ${total} 条`,
            onChange: handleTableChange,
            onShowSizeChange: handleTableChange
          }}
        />
      </Card>

      {/* 新增/编辑订单弹窗 */}
      <Modal
        title={editingRecord ? '编辑订单' : '新增订单'}
        open={modalVisible}
        onCancel={() => {
          setModalVisible(false);
          form.resetFields();
          setEditingRecord(null);
        }}
        footer={[
          <Button key="cancel" onClick={() => setModalVisible(false)}>
            取消
          </Button>,
          <Button key="submit" type="primary" loading={loading} onClick={() => form.submit()}>
            {editingRecord ? '更新' : '创建'}
          </Button>
        ]}
        width={900}
        destroyOnClose
      >
        <Form
          form={form}
          layout="vertical"
          onFinish={handleSubmit}
          initialValues={{
            priority: 'medium',
            status: 'pending',
            unit: '件'
          }}
        >
          <Row gutter={16}>
            <Col span={12}>
              <Form.Item
                name="order_number"
                label="订单编号"
                rules={[{ required: true, message: '请输入订单编号' }]}
              >
                <Input placeholder="请输入订单编号" />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item
                name="customer_name"
                label="客户名称"
                rules={[{ required: true, message: '请输入客户名称' }]}
              >
                <Input placeholder="请输入客户名称" />
              </Form.Item>
            </Col>
          </Row>

          <Row gutter={16}>
             <Col span={8}>
               <Form.Item
                 name="customer_contact"
                 label="联系人"
               >
                 <Input placeholder="请输入联系人" />
               </Form.Item>
             </Col>
             <Col span={8}>
               <Form.Item
                 name="customer_phone"
                 label="联系电话"
               >
                 <Input placeholder="请输入联系电话" />
               </Form.Item>
             </Col>
             <Col span={8}>
               <Form.Item
                 name="customer_email"
                 label="邮箱"
               >
                 <Input placeholder="请输入邮箱" />
               </Form.Item>
             </Col>
           </Row>

          <Row gutter={16}>
            <Col span={12}>
              <Form.Item
                name="product_name"
                label="产品名称"
                rules={[{ required: true, message: '请输入产品名称' }]}
              >
                <Input placeholder="请输入产品名称" />
              </Form.Item>
            </Col>
            <Col span={12}>
               <Form.Item
                 name="product_code"
                 label="产品编码"
                 rules={[{ required: true, message: '请输入产品编码' }]}
               >
                 <Input placeholder="请输入产品编码" />
               </Form.Item>
             </Col>
          </Row>

          <Row gutter={16}>
            <Col span={12}>
              <Form.Item
                name="product_spec"
                label="产品规格"
              >
                <Input placeholder="请输入产品规格" />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item
                name="technical_requirements"
                label="技术要求"
              >
                <Input placeholder="请输入技术要求" />
              </Form.Item>
            </Col>
          </Row>

          <Row gutter={16}>
            <Col span={8}>
              <Form.Item
                name="quantity"
                label="数量"
                rules={[{ required: true, message: '请输入数量' }]}
              >
                <InputNumber
                  min={1}
                  placeholder="请输入数量"
                  style={{ width: '100%' }}
                />
              </Form.Item>
            </Col>
            <Col span={8}>
              <Form.Item
                name="unit"
                label="单位"
                rules={[{ required: true, message: '请选择单位' }]}
              >
                <Select placeholder="请选择单位">
                  <Option value="件">件</Option>
                  <Option value="套">套</Option>
                  <Option value="个">个</Option>
                  <Option value="台">台</Option>
                  <Option value="批">批</Option>
                  <Option value="米">米</Option>
                  <Option value="公斤">公斤</Option>
                </Select>
              </Form.Item>
            </Col>
            <Col span={8}>
              <Form.Item
                name="unit_price"
                label="单价"
                rules={[{ required: true, message: '请输入单价' }]}
              >
                <InputNumber
                  min={0}
                  precision={2}
                  placeholder="请输入单价"
                  style={{ width: '100%' }}
                  addonBefore="¥"
                />
              </Form.Item>
            </Col>
          </Row>

          <Row gutter={16}>
            <Col span={12}>
              <Form.Item
                name="order_date"
                label="下单日期"
                rules={[{ required: true, message: '请选择下单日期' }]}
              >
                <DatePicker
                  style={{ width: '100%' }}
                  placeholder="请选择下单日期"
                  showTime
                />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item
                name="delivery_date"
                label="交货日期"
                rules={[{ required: true, message: '请选择交货日期' }]}
              >
                <DatePicker
                  style={{ width: '100%' }}
                  placeholder="请选择交货日期"
                  showTime
                />
              </Form.Item>
            </Col>
          </Row>

          <Row gutter={16}>
            <Col span={8}>
              <Form.Item
                name="priority"
                label="优先级"
                rules={[{ required: true, message: '请选择优先级' }]}
              >
                <Select placeholder="请选择优先级">
                  <Option value="high">高</Option>
                  <Option value="medium">中</Option>
                  <Option value="low">低</Option>
                </Select>
              </Form.Item>
            </Col>
            <Col span={8}>
              <Form.Item
                name="status"
                label="订单状态"
                rules={[{ required: true, message: '请选择订单状态' }]}
              >
                <Select placeholder="请选择订单状态">
                  <Option value="pending">待生产</Option>
                  <Option value="confirmed">已确认</Option>
                  <Option value="in_production">生产中</Option>
                  <Option value="completed">已完成</Option>
                  <Option value="cancelled">已取消</Option>
                </Select>
              </Form.Item>
            </Col>
            <Col span={8}>
              <Form.Item
                name="delivery_address"
                label="交货地址"
              >
                <Input placeholder="请输入交货地址" />
              </Form.Item>
            </Col>
          </Row>

          <Form.Item
            name="remark"
            label="备注"
          >
            <Input.TextArea
              rows={3}
              placeholder="请输入备注信息"
            />
          </Form.Item>
        </Form>
      </Modal>

      {/* 订单详情弹窗 */}
      <Modal
        title="订单详情"
        open={detailModalVisible}
        onCancel={() => setDetailModalVisible(false)}
        footer={[
          <Button key="close" onClick={() => setDetailModalVisible(false)}>
            关闭
          </Button>
        ]}
        width={800}
      >
        {selectedRecord && (
          <Descriptions bordered column={2}>
            <Descriptions.Item label="订单编号">{selectedRecord.order_number}</Descriptions.Item>
            <Descriptions.Item label="订单状态">
              <Badge 
                status={selectedRecord.status === 'completed' ? 'success' : 'processing'} 
                text={selectedRecord.status} 
              />
            </Descriptions.Item>
            <Descriptions.Item label="客户名称">{selectedRecord.customer_name}</Descriptions.Item>
            <Descriptions.Item label="联系人">{selectedRecord.customer_contact || '-'}</Descriptions.Item>
             <Descriptions.Item label="联系电话">{selectedRecord.customer_phone || '-'}</Descriptions.Item>
             <Descriptions.Item label="邮箱">{selectedRecord.customer_email || '-'}</Descriptions.Item>
            <Descriptions.Item label="产品名称">{selectedRecord.product_name}</Descriptions.Item>
            <Descriptions.Item label="产品编码">{selectedRecord.product_code}</Descriptions.Item>
            <Descriptions.Item label="产品规格">{selectedRecord.product_spec || '-'}</Descriptions.Item>
            <Descriptions.Item label="技术要求">{selectedRecord.technical_requirements || '-'}</Descriptions.Item>
            <Descriptions.Item label="数量">{selectedRecord.quantity} {selectedRecord.unit}</Descriptions.Item>
            <Descriptions.Item label="单价">¥{selectedRecord.unit_price?.toFixed(2)}</Descriptions.Item>
            <Descriptions.Item label="总金额">¥{selectedRecord.total_amount?.toFixed(2)}</Descriptions.Item>
            <Descriptions.Item label="优先级">
              <Tag color={selectedRecord.priority === 'high' ? 'red' : selectedRecord.priority === 'medium' ? 'orange' : 'green'}>
                {selectedRecord.priority === 'high' ? '高' : selectedRecord.priority === 'medium' ? '中' : '低'}
              </Tag>
            </Descriptions.Item>
            <Descriptions.Item label="下单日期">
              {selectedRecord.order_date ? dayjs(selectedRecord.order_date).format('YYYY-MM-DD HH:mm:ss') : '-'}
            </Descriptions.Item>
            <Descriptions.Item label="交货日期">
              {selectedRecord.delivery_date ? dayjs(selectedRecord.delivery_date).format('YYYY-MM-DD HH:mm:ss') : '-'}
            </Descriptions.Item>
            <Descriptions.Item label="交货地址" span={2}>{selectedRecord.delivery_address || '-'}</Descriptions.Item>
            <Descriptions.Item label="备注" span={2}>{selectedRecord.remark || '-'}</Descriptions.Item>
            <Descriptions.Item label="创建时间">
              {selectedRecord.created_at ? dayjs(selectedRecord.created_at).format('YYYY-MM-DD HH:mm:ss') : '-'}
            </Descriptions.Item>
            <Descriptions.Item label="更新时间">
              {selectedRecord.updated_at ? dayjs(selectedRecord.updated_at).format('YYYY-MM-DD HH:mm:ss') : '-'}
            </Descriptions.Item>
          </Descriptions>
        )}
      </Modal>

      {/* 导入导出弹窗 */}
      <ImportExportModal
        visible={importExportVisible}
        mode={importExportType}
        dataType="orders"
        onCancel={() => setImportExportVisible(false)}
        onSuccess={handleImportExportSuccess}
      />

      {/* BD400导入弹窗 */}
      <Modal
        title="BD400订单导入"
        open={bd400ImportVisible}
        onCancel={() => setBd400ImportVisible(false)}
        footer={[
          <Button key="template" onClick={downloadBd400Template}>
            下载模板
          </Button>,
          <Button key="cancel" onClick={() => setBd400ImportVisible(false)}>
            取消
          </Button>
        ]}
        width={600}
      >
        <div style={{ textAlign: 'center', padding: '40px 20px' }}>
          <Upload.Dragger {...uploadProps} disabled={importLoading}>
            <p className="ant-upload-drag-icon">
              <UploadOutlined style={{ fontSize: '48px', color: '#1890ff' }} />
            </p>
            <p className="ant-upload-text">
              {importLoading ? '正在导入中...' : '点击或拖拽BD400订单表到此区域'}
            </p>
            <p className="ant-upload-hint">
              支持Excel格式文件(.xlsx, .xls)，文件大小不超过10MB
            </p>
          </Upload.Dragger>
          
          {importLoading && (
            <div style={{ marginTop: '20px' }}>
              <Progress percent={50} status="active" />
              <p style={{ marginTop: '10px', color: '#666' }}>正在解析并导入订单数据...</p>
            </div>
          )}
          
          <div style={{ marginTop: '20px', textAlign: 'left' }}>
            <h4>导入说明：</h4>
            <ul style={{ color: '#666', fontSize: '14px' }}>
              <li>请确保Excel文件包含必要的列：订单号、客户名称、产品名称、数量、交货日期</li>
              <li>系统会自动跳过重复的订单号</li>
              <li>导入过程中如有错误，请查看控制台详细信息</li>
              <li>建议先下载模板，按照模板格式整理数据</li>
            </ul>
          </div>
        </div>
      </Modal>
    </div>
  );
};

export default OrderManagement;