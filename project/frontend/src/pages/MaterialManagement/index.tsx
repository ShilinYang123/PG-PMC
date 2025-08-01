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
  Select,
  Row,
  Col,
  Tabs,
  Alert,
  Badge,
  Tooltip,
  InputNumber,
  message
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
import { materialApi, bomApi } from '../../services/api';

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

  // 状态数据
  const [materialData, setMaterialData] = useState<Material[]>([]);
  const [bomData, setBomData] = useState<BOMItem[]>([]);
  const [purchaseData, setPurchaseData] = useState<PurchaseOrder[]>([]);
  const [materialStats, setMaterialStats] = useState<any>({});
  const [stockAlerts, setStockAlerts] = useState<any[]>([]);

  // 初始化数据加载
  useEffect(() => {
    loadMaterialData();
    loadBOMData();
    loadMaterialStats();
    loadStockAlerts();
  }, []);

  // 加载物料数据
  const loadMaterialData = async () => {
    try {
      setLoading(true);
      const response = await materialApi.getMaterials();
      if (response.data) {
        setMaterialData(response.data.map((item: any) => ({
          ...item,
          key: item.id || item.material_code
        })));
      }
    } catch (error) {
      console.error('加载物料数据失败:', error);
      message.error('加载物料数据失败');
    } finally {
      setLoading(false);
    }
  };

  // 加载BOM数据
  const loadBOMData = async () => {
    try {
      const response = await bomApi.getBOMs();
      if (response.data) {
        setBomData(response.data.map((item: any) => ({
          ...item,
          key: item.id || item.bom_code
        })));
      }
    } catch (error) {
      console.error('加载BOM数据失败:', error);
      message.error('加载BOM数据失败');
    }
  };

  // 加载物料统计
  const loadMaterialStats = async () => {
    try {
      const response = await materialApi.getMaterialStats();
      if (response.data) {
        setMaterialStats(response.data);
      }
    } catch (error) {
      console.error('加载物料统计失败:', error);
    }
  };

  // 加载库存预警
  const loadStockAlerts = async () => {
    try {
      const response = await materialApi.getStockAlerts();
      if (response.data) {
        setStockAlerts(response.data);
      }
    } catch (error) {
      console.error('加载库存预警失败:', error);
    }
  };

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

  const handleDelete = async (key: string) => {
    try {
      await materialApi.deleteMaterial(key);
      message.success('删除成功');
      loadMaterialData(); // 重新加载数据
    } catch (error) {
      console.error('删除失败:', error);
      message.error('删除失败');
    }
  };

  const handleSubmit = async () => {
    try {
      const values = await form.validateFields();
      setLoading(true);
      
      if (editingRecord) {
        // 更新物料
        await materialApi.updateMaterial(editingRecord.key, values);
        message.success('更新成功');
      } else {
        // 创建物料
        await materialApi.createMaterial(values);
        message.success('创建成功');
      }
      
      setModalVisible(false);
      loadMaterialData(); // 重新加载数据
      loadMaterialStats(); // 重新加载统计数据
    } catch (error) {
      console.error('操作失败:', error);
      message.error('操作失败');
    } finally {
      setLoading(false);
    }
  };

  // BOM提交处理
  const handleBOMSubmit = async () => {
    try {
      const values = await bomForm.validateFields();
      setLoading(true);
      
      await bomApi.createBOM(values);
      message.success('BOM创建成功');
      
      setBomModalVisible(false);
      loadBOMData(); // 重新加载BOM数据
    } catch (error) {
      console.error('BOM创建失败:', error);
      message.error('BOM创建失败');
    } finally {
      setLoading(false);
    }
  };

  // 获取库存预警数量
  const getWarningCount = () => {
    return stockAlerts.filter(alert => alert.alert_type === 'low_stock' || alert.alert_type === 'out_of_stock').length;
  };

  // 获取统计数据
  const getStatsData = () => {
    return {
      totalMaterials: materialStats.total_materials || materialData.length,
      warningCount: getWarningCount(),
      supplierCount: materialStats.supplier_count || 0,
      totalValue: materialStats.total_inventory_value || 0
    };
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
              <div className="stat-number">{getStatsData().totalMaterials}</div>
              <div className="stat-title">物料种类</div>
            </div>
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <div className="stat-card">
              <div className="stat-number" style={{ color: '#ff4d4f' }}>
                <Badge count={getStatsData().warningCount}>
                  {getStatsData().warningCount}
                </Badge>
              </div>
              <div className="stat-title">库存预警</div>
            </div>
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <div className="stat-card">
              <div className="stat-number">{getStatsData().supplierCount}</div>
              <div className="stat-title">供应商数量</div>
            </div>
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <div className="stat-card">
              <div className="stat-number">¥{getStatsData().totalValue.toLocaleString()}</div>
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
        onOk={handleBOMSubmit}
        onCancel={() => setBomModalVisible(false)}
        width={600}
        confirmLoading={loading}
        destroyOnClose
      >
        <Form form={bomForm} layout="vertical">
          <Form.Item label="BOM编码" name="bomCode" rules={[{ required: true, message: '请输入BOM编码' }]}>
            <Input placeholder="请输入BOM编码" />
          </Form.Item>
          <Form.Item label="产品名称" name="productName" rules={[{ required: true, message: '请输入产品名称' }]}>
            <Input placeholder="请输入产品名称" />
          </Form.Item>
          <Form.Item label="版本" name="version" rules={[{ required: true, message: '请输入版本' }]}>
            <Input placeholder="请输入版本" />
          </Form.Item>
          <Form.Item label="物料编码" name="materialCode" rules={[{ required: true, message: '请输入物料编码' }]}>
            <Input placeholder="请输入物料编码" />
          </Form.Item>
          <Form.Item label="物料名称" name="materialName" rules={[{ required: true, message: '请输入物料名称' }]}>
            <Input placeholder="请输入物料名称" />
          </Form.Item>
          <Row gutter={16}>
            <Col span={12}>
              <Form.Item label="用量" name="quantity" rules={[{ required: true, message: '请输入用量' }]}>
                <InputNumber min={0} placeholder="用量" style={{ width: '100%' }} />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item label="单位" name="unit" rules={[{ required: true, message: '请选择单位' }]}>
                <Select placeholder="请选择单位">
                  <Option value="件">件</Option>
                  <Option value="个">个</Option>
                  <Option value="根">根</Option>
                  <Option value="米">米</Option>
                  <Option value="公斤">公斤</Option>
                </Select>
              </Form.Item>
            </Col>
          </Row>
          <Form.Item label="层级" name="level" rules={[{ required: true, message: '请输入层级' }]}>
            <InputNumber min={1} placeholder="层级" style={{ width: '100%' }} />
          </Form.Item>
          <Form.Item label="备注" name="remark">
            <Input.TextArea rows={3} placeholder="请输入备注信息" />
          </Form.Item>
        </Form>
      </Modal>
    </div>
  );
};

export default MaterialManagement;