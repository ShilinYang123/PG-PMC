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
  Alert,
  Badge,
  Tooltip,
  InputNumber
} from 'antd';
import {
  PlusOutlined,
  EditOutlined,
  DeleteOutlined,
  WarningOutlined,
  ShoppingCartOutlined,
  InboxOutlined,
  FileTextOutlined
} from '@ant-design/icons';
import ReactECharts from 'echarts-for-react';
import type { ColumnsType } from 'antd/es/table';

const { Option } = Select;
const { TabPane } = Tabs;

interface Material {
  key: string;
  materialCode: string;
  materialName: string;
  specification: string;
  unit: string;
  category: string;
  currentStock: number;
  safetyStock: number;
  unitPrice: number;
  supplier: string;
  status: string;
  location: string;
  remark: string;
}

interface BOMItem {
  key: string;
  bomCode: string;
  productName: string;
  version: string;
  materialCode: string;
  materialName: string;
  quantity: number;
  unit: string;
  level: number;
  remark: string;
}

interface PurchaseOrder {
  key: string;
  poNo: string;
  supplier: string;
  materialCode: string;
  materialName: string;
  quantity: number;
  unit: string;
  unitPrice: number;
  totalAmount: number;
  orderDate: string;
  expectedDate: string;
  status: string;
}

const MaterialManagement: React.FC = () => {
  const [loading, setLoading] = useState(false);
  const [modalVisible, setModalVisible] = useState(false);
  const [bomModalVisible, setBomModalVisible] = useState(false);
  const [editingRecord, setEditingRecord] = useState<Material | null>(null);
  const [form] = Form.useForm();
  const [bomForm] = Form.useForm();

  // 物料数据
  const [materialData, setMaterialData] = useState<Material[]>([
    {
      key: '1',
      materialCode: 'M001',
      materialName: '钢材A',
      specification: 'Q235 10*20*100',
      unit: '根',
      category: '原材料',
      currentStock: 150,
      safetyStock: 50,
      unitPrice: 25.5,
      supplier: '钢材供应商A',
      status: '正常',
      location: 'A区-01',
      remark: '常用材料'
    },
    {
      key: '2',
      materialCode: 'M002',
      materialName: '螺丝B',
      specification: 'M6*20',
      unit: '个',
      category: '标准件',
      currentStock: 20,
      safetyStock: 100,
      unitPrice: 0.5,
      supplier: '标准件供应商B',
      status: '缺货',
      location: 'B区-05',
      remark: '需要补货'
    }
  ]);

  // BOM数据
  const [bomData, setBomData] = useState<BOMItem[]>([
    {
      key: '1',
      bomCode: 'BOM-001',
      productName: '精密零件A',
      version: 'V1.0',
      materialCode: 'M001',
      materialName: '钢材A',
      quantity: 2,
      unit: '根',
      level: 1,
      remark: '主要材料'
    },
    {
      key: '2',
      bomCode: 'BOM-001',
      productName: '精密零件A',
      version: 'V1.0',
      materialCode: 'M002',
      materialName: '螺丝B',
      quantity: 8,
      unit: '个',
      level: 1,
      remark: '紧固件'
    }
  ]);

  // 采购订单数据
  const [purchaseData, setPurchaseData] = useState<PurchaseOrder[]>([
    {
      key: '1',
      poNo: 'PO-2024-001',
      supplier: '钢材供应商A',
      materialCode: 'M001',
      materialName: '钢材A',
      quantity: 100,
      unit: '根',
      unitPrice: 25.5,
      totalAmount: 2550,
      orderDate: '2024-01-20',
      expectedDate: '2024-01-30',
      status: '已下单'
    }
  ]);

  // 物料表格列配置
  const materialColumns: ColumnsType<Material> = [
    {
      title: '物料编码',
      dataIndex: 'materialCode',
      key: 'materialCode',
      width: 100,
      fixed: 'left'
    },
    {
      title: '物料名称',
      dataIndex: 'materialName',
      key: 'materialName',
      width: 120
    },
    {
      title: '规格',
      dataIndex: 'specification',
      key: 'specification',
      width: 120
    },
    {
      title: '类别',
      dataIndex: 'category',
      key: 'category',
      width: 80
    },
    {
      title: '当前库存',
      dataIndex: 'currentStock',
      key: 'currentStock',
      width: 100,
      render: (value, record) => {
        const isLow = value <= record.safetyStock;
        return (
          <span style={{ color: isLow ? '#ff4d4f' : '#52c41a' }}>
            {value} {record.unit}
            {isLow && <WarningOutlined style={{ marginLeft: 4 }} />}
          </span>
        );
      }
    },
    {
      title: '安全库存',
      dataIndex: 'safetyStock',
      key: 'safetyStock',
      width: 100,
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
      title: '供应商',
      dataIndex: 'supplier',
      key: 'supplier',
      width: 120
    },
    {
      title: '状态',
      dataIndex: 'status',
      key: 'status',
      width: 80,
      render: (status) => {
        let color = 'success';
        if (status === '缺货') color = 'error';
        if (status === '预警') color = 'warning';
        return <Tag color={color}>{status}</Tag>;
      }
    },
    {
      title: '库位',
      dataIndex: 'location',
      key: 'location',
      width: 80
    },
    {
      title: '操作',
      key: 'action',
      width: 120,
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

  // BOM表格列配置
  const bomColumns: ColumnsType<BOMItem> = [
    {
      title: 'BOM编码',
      dataIndex: 'bomCode',
      key: 'bomCode',
      width: 120
    },
    {
      title: '产品名称',
      dataIndex: 'productName',
      key: 'productName',
      width: 120
    },
    {
      title: '版本',
      dataIndex: 'version',
      key: 'version',
      width: 80
    },
    {
      title: '物料编码',
      dataIndex: 'materialCode',
      key: 'materialCode',
      width: 100
    },
    {
      title: '物料名称',
      dataIndex: 'materialName',
      key: 'materialName',
      width: 120
    },
    {
      title: '用量',
      dataIndex: 'quantity',
      key: 'quantity',
      width: 80,
      render: (value, record) => `${value} ${record.unit}`
    },
    {
      title: '层级',
      dataIndex: 'level',
      key: 'level',
      width: 60
    },
    {
      title: '备注',
      dataIndex: 'remark',
      key: 'remark',
      width: 120
    }
  ];

  // 库存分析图表配置
  const stockAnalysisOption = {
    title: {
      text: '库存分析',
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
        name: '库存状态',
        type: 'pie',
        radius: '50%',
        data: [
          { value: 65, name: '正常库存' },
          { value: 20, name: '库存预警' },
          { value: 10, name: '缺货' },
          { value: 5, name: '超储' }
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

  // 物料周转率图表配置
  const turnoverOption = {
    title: {
      text: '物料周转率',
      left: 'center'
    },
    tooltip: {
      trigger: 'axis'
    },
    xAxis: {
      type: 'category',
      data: ['钢材A', '螺丝B', '垫片C', '轴承D', '密封圈E']
    },
    yAxis: {
      type: 'value',
      name: '周转率'
    },
    series: [
      {
        name: '周转率',
        type: 'bar',
        data: [12, 8, 15, 6, 10],
        itemStyle: {
          color: '#1890ff'
        }
      }
    ]
  };

  const handleAdd = () => {
    setEditingRecord(null);
    form.resetFields();
    setModalVisible(true);
  };

  const handleEdit = (record: Material) => {
    setEditingRecord(record);
    form.setFieldsValue(record);
    setModalVisible(true);
  };

  const handleDelete = (key: string) => {
    setMaterialData(materialData.filter(item => item.key !== key));
  };

  const handleSubmit = async () => {
    try {
      const values = await form.validateFields();
      
      if (editingRecord) {
        setMaterialData(materialData.map(item => 
          item.key === editingRecord.key 
            ? { ...item, ...values }
            : item
        ));
      } else {
        const newRecord = {
          key: Date.now().toString(),
          ...values
        };
        setMaterialData([...materialData, newRecord]);
      }
      
      setModalVisible(false);
    } catch (error) {
      console.error('表单验证失败:', error);
    }
  };

  // 获取库存预警数量
  const getWarningCount = () => {
    return materialData.filter(item => item.currentStock <= item.safetyStock).length;
  };

  return (
    <div>
      <h1 className="page-title">物料管理</h1>
      
      {/* 预警提示 */}
      {getWarningCount() > 0 && (
        <Alert
          message={`当前有 ${getWarningCount()} 种物料库存不足，请及时补货！`}
          type="warning"
          showIcon
          closable
          style={{ marginBottom: 16 }}
        />
      )}

      {/* 统计卡片 */}
      <Row gutter={16} style={{ marginBottom: 24 }}>
        <Col span={6}>
          <Card>
            <div className="stat-card">
              <div className="stat-number">{materialData.length}</div>
              <div className="stat-title">物料种类</div>
            </div>
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <div className="stat-card">
              <div className="stat-number" style={{ color: '#ff4d4f' }}>
                <Badge count={getWarningCount()}>
                  {getWarningCount()}
                </Badge>
              </div>
              <div className="stat-title">库存预警</div>
            </div>
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <div className="stat-card">
              <div className="stat-number">15</div>
              <div className="stat-title">供应商数量</div>
            </div>
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <div className="stat-card">
              <div className="stat-number">¥125,680</div>
              <div className="stat-title">库存总值</div>
            </div>
          </Card>
        </Col>
      </Row>

      {/* 图表区域 */}
      <Row gutter={16} style={{ marginBottom: 24 }}>
        <Col span={12}>
          <Card title="库存状态分析" className="card-shadow">
            <ReactECharts option={stockAnalysisOption} style={{ height: 300 }} />
          </Card>
        </Col>
        <Col span={12}>
          <Card title="物料周转率" className="card-shadow">
            <ReactECharts option={turnoverOption} style={{ height: 300 }} />
          </Card>
        </Col>
      </Row>

      {/* 主要内容区域 */}
      <Card>
        <Tabs defaultActiveKey="materials">
          <TabPane tab={<span><InboxOutlined />物料清单</span>} key="materials">
            <div className="action-buttons" style={{ marginBottom: 16 }}>
              <Space>
                <Button type="primary" icon={<PlusOutlined />} onClick={handleAdd}>
                  新增物料
                </Button>
                <Button icon={<ShoppingCartOutlined />}>
                  生成采购计划
                </Button>
                <Button icon={<WarningOutlined />}>
                  库存预警
                </Button>
              </Space>
            </div>

            <Table
              columns={materialColumns}
              dataSource={materialData}
              loading={loading}
              scroll={{ x: 1200 }}
              pagination={{
                total: materialData.length,
                pageSize: 10,
                showSizeChanger: true,
                showQuickJumper: true,
                showTotal: (total) => `共 ${total} 条记录`
              }}
            />
          </TabPane>

          <TabPane tab={<span><FileTextOutlined />BOM管理</span>} key="bom">
            <div className="action-buttons" style={{ marginBottom: 16 }}>
              <Space>
                <Button type="primary" icon={<PlusOutlined />} onClick={() => setBomModalVisible(true)}>
                  新增BOM
                </Button>
                <Button>导入BOM</Button>
                <Button>导出BOM</Button>
              </Space>
            </div>

            <Table
              columns={bomColumns}
              dataSource={bomData}
              loading={loading}
              pagination={{
                total: bomData.length,
                pageSize: 10,
                showSizeChanger: true,
                showQuickJumper: true,
                showTotal: (total) => `共 ${total} 条记录`
              }}
            />
          </TabPane>

          <TabPane tab={<span><ShoppingCartOutlined />采购管理</span>} key="purchase">
            <div className="action-buttons" style={{ marginBottom: 16 }}>
              <Space>
                <Button type="primary" icon={<PlusOutlined />}>
                  新增采购单
                </Button>
                <Button>采购计划</Button>
                <Button>供应商管理</Button>
              </Space>
            </div>

            <Table
              dataSource={purchaseData}
              loading={loading}
              pagination={{
                total: purchaseData.length,
                pageSize: 10,
                showSizeChanger: true,
                showQuickJumper: true,
                showTotal: (total) => `共 ${total} 条记录`
              }}
            />
          </TabPane>
        </Tabs>
      </Card>

      {/* 新增/编辑物料弹窗 */}
      <Modal
        title={editingRecord ? '编辑物料' : '新增物料'}
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
            status: '正常',
            category: '原材料'
          }}
        >
          <Row gutter={16}>
            <Col span={12}>
              <Form.Item
                label="物料编码"
                name="materialCode"
                rules={[{ required: true, message: '请输入物料编码' }]}
              >
                <Input placeholder="请输入物料编码" />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item
                label="物料名称"
                name="materialName"
                rules={[{ required: true, message: '请输入物料名称' }]}
              >
                <Input placeholder="请输入物料名称" />
              </Form.Item>
            </Col>
          </Row>
          
          <Row gutter={16}>
            <Col span={12}>
              <Form.Item
                label="规格"
                name="specification"
                rules={[{ required: true, message: '请输入规格' }]}
              >
                <Input placeholder="请输入规格" />
              </Form.Item>
            </Col>
            <Col span={6}>
              <Form.Item
                label="单位"
                name="unit"
                rules={[{ required: true, message: '请选择单位' }]}
              >
                <Select placeholder="请选择单位">
                  <Option value="件">件</Option>
                  <Option value="个">个</Option>
                  <Option value="根">根</Option>
                  <Option value="米">米</Option>
                  <Option value="公斤">公斤</Option>
                </Select>
              </Form.Item>
            </Col>
            <Col span={6}>
              <Form.Item
                label="类别"
                name="category"
                rules={[{ required: true, message: '请选择类别' }]}
              >
                <Select placeholder="请选择类别">
                  <Option value="原材料">原材料</Option>
                  <Option value="半成品">半成品</Option>
                  <Option value="成品">成品</Option>
                  <Option value="标准件">标准件</Option>
                </Select>
              </Form.Item>
            </Col>
          </Row>

          <Row gutter={16}>
            <Col span={8}>
              <Form.Item
                label="当前库存"
                name="currentStock"
                rules={[{ required: true, message: '请输入当前库存' }]}
              >
                <InputNumber min={0} placeholder="当前库存" style={{ width: '100%' }} />
              </Form.Item>
            </Col>
            <Col span={8}>
              <Form.Item
                label="安全库存"
                name="safetyStock"
                rules={[{ required: true, message: '请输入安全库存' }]}
              >
                <InputNumber min={0} placeholder="安全库存" style={{ width: '100%' }} />
              </Form.Item>
            </Col>
            <Col span={8}>
              <Form.Item
                label="单价"
                name="unitPrice"
                rules={[{ required: true, message: '请输入单价' }]}
              >
                <InputNumber min={0} precision={2} placeholder="单价" style={{ width: '100%' }} />
              </Form.Item>
            </Col>
          </Row>

          <Row gutter={16}>
            <Col span={12}>
              <Form.Item
                label="供应商"
                name="supplier"
                rules={[{ required: true, message: '请输入供应商' }]}
              >
                <Input placeholder="请输入供应商" />
              </Form.Item>
            </Col>
            <Col span={6}>
              <Form.Item
                label="库位"
                name="location"
                rules={[{ required: true, message: '请输入库位' }]}
              >
                <Input placeholder="请输入库位" />
              </Form.Item>
            </Col>
            <Col span={6}>
              <Form.Item
                label="状态"
                name="status"
                rules={[{ required: true, message: '请选择状态' }]}
              >
                <Select placeholder="请选择状态">
                  <Option value="正常">正常</Option>
                  <Option value="预警">预警</Option>
                  <Option value="缺货">缺货</Option>
                </Select>
              </Form.Item>
            </Col>
          </Row>

          <Form.Item label="备注" name="remark">
            <Input.TextArea rows={3} placeholder="请输入备注信息" />
          </Form.Item>
        </Form>
      </Modal>

      {/* BOM弹窗 */}
      <Modal
        title="新增BOM"
        open={bomModalVisible}
        onCancel={() => setBomModalVisible(false)}
        width={600}
        footer={null}
      >
        <Form form={bomForm} layout="vertical">
          <Form.Item label="BOM编码" name="bomCode" rules={[{ required: true }]}>
            <Input placeholder="请输入BOM编码" />
          </Form.Item>
          <Form.Item label="产品名称" name="productName" rules={[{ required: true }]}>
            <Input placeholder="请输入产品名称" />
          </Form.Item>
          <Form.Item label="版本" name="version" rules={[{ required: true }]}>
            <Input placeholder="请输入版本" />
          </Form.Item>
        </Form>
      </Modal>
    </div>
  );
};

export default MaterialManagement;