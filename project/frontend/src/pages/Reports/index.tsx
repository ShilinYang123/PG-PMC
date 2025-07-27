import React, { useState, useEffect } from 'react';
import {
  Card,
  Row,
  Col,
  DatePicker,
  Button,
  Tabs,
  Statistic,
  Table,
  Space,
  message,
  Spin,
  Typography
} from 'antd';
import {
  BarChartOutlined,
  LineChartOutlined,
  FileExcelOutlined,
  FilePdfOutlined
} from '@ant-design/icons';
import dayjs, { Dayjs } from 'dayjs';
import type { ColumnsType } from 'antd/es/table';
import { LineChart, BarChart, PieChart } from '../../components/Charts';

const { RangePicker } = DatePicker;
const { TabPane } = Tabs;
const { Title, Text } = Typography;

// 类型定义
interface ReportRequest {
  start_date: string;
  end_date: string;
  format?: string;
}

interface ProductionReportData {
  total_plans: number;
  completed_plans: number;
  in_progress_plans: number;
  overdue_plans: number;
  completion_rate: number;
  avg_progress: number;
  workshop_stats: Array<{
    workshop: string;
    total_plans: number;
    avg_progress: number;
  }>;
  daily_production: Array<{
    date: string;
    count: number;
  }>;
  efficiency_analysis: {
    on_time_completion_rate: number;
    average_delay_days: number;
    resource_utilization: number;
  };
}

interface QualityReportData {
  total_checks: number;
  passed_checks: number;
  failed_checks: number;
  pass_rate: number;
  defect_rate: number;
  quality_trends: Array<{
    date: string;
    total_checks: number;
    pass_rate: number;
  }>;
  defect_analysis: Array<{
    defect_type: string;
    count: number;
    percentage: number;
  }>;
  product_quality: Array<{
    product_name: string;
    total_checks: number;
    passed_checks: number;
    pass_rate: number;
  }>;
}

interface EquipmentReportData {
  total_equipment: number;
  running_equipment: number;
  maintenance_equipment: number;
  fault_equipment: number;
  utilization_rate: number;
  maintenance_stats: Array<{
    maintenance_type: string;
    count: number;
    avg_cost: number;
  }>;
  fault_analysis: Array<{
    equipment_type: string;
    fault_count: number;
    fault_rate: number;
  }>;
  efficiency_trends: Array<{
    date: string;
    utilization_rate: number;
    maintenance_count: number;
  }>;
}

const Reports: React.FC = () => {
  const [loading, setLoading] = useState(false);
  const [dateRange, setDateRange] = useState<[Dayjs, Dayjs]>([
    dayjs().subtract(30, 'day'),
    dayjs()
  ]);
  const [activeTab, setActiveTab] = useState('production');
  const [productionData, setProductionData] = useState<ProductionReportData | null>(null);
  const [qualityData, setQualityData] = useState<QualityReportData | null>(null);
  const [equipmentData, setEquipmentData] = useState<EquipmentReportData | null>(null);

  // API调用
  const fetchProductionReport = async (request: ReportRequest) => {
    setLoading(true);
    try {
      const response = await fetch('/api/reports/production', {
        method: 'POST',
        headers: { 
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        },
        body: JSON.stringify(request)
      });
      
      if (!response.ok) {
        throw new Error('网络请求失败');
      }
      
      const result = await response.json();
      if (result.code === 200) {
        setProductionData(result.data);
        message.success('生产报表生成成功');
      } else {
        throw new Error(result.message || '生成报表失败');
      }
    } catch (error) {
      console.error('生产报表生成失败:', error);
      message.error('生成生产报表失败');
      // 降级到模拟数据
      const mockData: ProductionReportData = {
        total_plans: 156,
        completed_plans: 128,
        in_progress_plans: 23,
        overdue_plans: 5,
        completion_rate: 82.1,
        avg_progress: 78.5,
        workshop_stats: [
          { workshop: '车间A', total_plans: 45, avg_progress: 85.2 },
          { workshop: '车间B', total_plans: 38, avg_progress: 72.8 },
          { workshop: '车间C', total_plans: 42, avg_progress: 79.3 },
          { workshop: '车间D', total_plans: 31, avg_progress: 76.1 }
        ],
        daily_production: Array.from({ length: 30 }, (_, i) => ({
          date: dayjs().subtract(29 - i, 'day').format('YYYY-MM-DD'),
          count: Math.floor(Math.random() * 20) + 5
        })),
        efficiency_analysis: {
          on_time_completion_rate: 82.1,
          average_delay_days: 2.3,
          resource_utilization: 78.5
        }
      };
      setProductionData(mockData);
    } finally {
      setLoading(false);
    }
  };

  const fetchQualityReport = async (request: ReportRequest) => {
    setLoading(true);
    try {
      const response = await fetch('/api/reports/quality', {
        method: 'POST',
        headers: { 
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        },
        body: JSON.stringify(request)
      });
      
      if (!response.ok) {
        throw new Error('网络请求失败');
      }
      
      const result = await response.json();
      if (result.code === 200) {
        setQualityData(result.data);
        message.success('质量报表生成成功');
      } else {
        throw new Error(result.message || '生成报表失败');
      }
    } catch (error) {
      console.error('质量报表生成失败:', error);
      message.error('生成质量报表失败');
      // 降级到模拟数据
      const mockData: QualityReportData = {
        total_checks: 1248,
        passed_checks: 1156,
        failed_checks: 92,
        pass_rate: 92.6,
        defect_rate: 7.4,
        quality_trends: Array.from({ length: 30 }, (_, i) => ({
          date: dayjs().subtract(29 - i, 'day').format('YYYY-MM-DD'),
          total_checks: Math.floor(Math.random() * 50) + 20,
          pass_rate: Math.random() * 10 + 85
        })),
        defect_analysis: [
          { defect_type: '尺寸偏差', count: 35, percentage: 38.0 },
          { defect_type: '表面缺陷', count: 28, percentage: 30.4 },
          { defect_type: '材料问题', count: 18, percentage: 19.6 },
          { defect_type: '其他', count: 11, percentage: 12.0 }
        ],
        product_quality: [
          { product_name: '产品A', total_checks: 312, passed_checks: 295, pass_rate: 94.6 },
          { product_name: '产品B', total_checks: 285, passed_checks: 261, pass_rate: 91.6 },
          { product_name: '产品C', total_checks: 298, passed_checks: 276, pass_rate: 92.6 },
          { product_name: '产品D', total_checks: 353, passed_checks: 324, pass_rate: 91.8 }
        ]
      };
      setQualityData(mockData);
    } finally {
      setLoading(false);
    }
  };

  const fetchEquipmentReport = async (request: ReportRequest) => {
    setLoading(true);
    try {
      const response = await fetch('/api/reports/equipment', {
        method: 'POST',
        headers: { 
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        },
        body: JSON.stringify(request)
      });
      
      if (!response.ok) {
        throw new Error('网络请求失败');
      }
      
      const result = await response.json();
      if (result.code === 200) {
        setEquipmentData(result.data);
        message.success('设备报表生成成功');
      } else {
        throw new Error(result.message || '生成报表失败');
      }
    } catch (error) {
      console.error('设备报表生成失败:', error);
      message.error('生成设备报表失败');
      // 降级到模拟数据
      const mockData: EquipmentReportData = {
        total_equipment: 48,
        running_equipment: 42,
        maintenance_equipment: 4,
        fault_equipment: 2,
        utilization_rate: 87.5,
        maintenance_stats: [
          { maintenance_type: '预防性维护', count: 15, avg_cost: 2500 },
          { maintenance_type: '故障维修', count: 8, avg_cost: 4200 },
          { maintenance_type: '定期保养', count: 22, avg_cost: 800 }
        ],
        fault_analysis: [
          { equipment_type: '数控机床', fault_count: 3, fault_rate: 6.25 },
          { equipment_type: '注塑机', fault_count: 2, fault_rate: 4.17 },
          { equipment_type: '包装设备', fault_count: 1, fault_rate: 2.08 }
        ],
        efficiency_trends: Array.from({ length: 30 }, (_, i) => ({
          date: dayjs().subtract(29 - i, 'day').format('YYYY-MM-DD'),
          utilization_rate: Math.random() * 15 + 80,
          maintenance_count: Math.floor(Math.random() * 3)
        }))
      };
      setEquipmentData(mockData);
    } finally {
      setLoading(false);
    }
  };

  const generateReport = () => {
    const request: ReportRequest = {
      start_date: dateRange[0].format('YYYY-MM-DD'),
      end_date: dateRange[1].format('YYYY-MM-DD')
    };

    switch (activeTab) {
      case 'production':
        fetchProductionReport(request);
        break;
      case 'quality':
        fetchQualityReport(request);
        break;
      case 'equipment':
        fetchEquipmentReport(request);
        break;
    }
  };

  const exportReport = async (format: string) => {
    try {
      message.info(`正在导出${format.toUpperCase()}格式报表...`);
      
      const params = new URLSearchParams({
        start_date: dateRange[0].format('YYYY-MM-DD'),
        end_date: dateRange[1].format('YYYY-MM-DD'),
        format: format
      });
      
      const response = await fetch(`/api/reports/export/${activeTab}?${params}`, {
        method: 'GET',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        }
      });
      
      if (!response.ok) {
        throw new Error('导出请求失败');
      }
      
      const result = await response.json();
      if (result.code === 200) {
        message.success(`${format.toUpperCase()}格式报表导出成功`);
        // 这里可以处理下载链接
        if (result.data.download_url) {
          window.open(result.data.download_url, '_blank');
        }
      } else {
        throw new Error(result.message || '导出失败');
      }
    } catch (error) {
      console.error('导出报表失败:', error);
      message.error(`导出${format.toUpperCase()}格式报表失败`);
    }
  };

  useEffect(() => {
    generateReport();
  }, [activeTab, dateRange]);

  // 生产报表内容
  const renderProductionReport = () => {
    if (!productionData) return null;

    const workshopColumns: ColumnsType<any> = [
      { title: '车间', dataIndex: 'workshop', key: 'workshop' },
      { title: '计划数', dataIndex: 'total_plans', key: 'total_plans' },
      { 
        title: '平均进度', 
        dataIndex: 'avg_progress', 
        key: 'avg_progress',
        render: (value: number) => `${value.toFixed(1)}%`
      }
    ];

    const lineData = productionData.daily_production.map(item => ({
      x: item.date,
      y: item.count
    }));

    const barData = productionData.workshop_stats.map(item => ({
      x: item.workshop,
      y: item.total_plans
    }));

    return (
      <div>
        <Row gutter={[16, 16]} style={{ marginBottom: 24 }}>
          <Col span={6}>
            <Card>
              <Statistic
                title="总计划数"
                value={productionData.total_plans}
                prefix={<BarChartOutlined />}
              />
            </Card>
          </Col>
          <Col span={6}>
            <Card>
              <Statistic
                title="已完成"
                value={productionData.completed_plans}
                valueStyle={{ color: '#3f8600' }}
              />
            </Card>
          </Col>
          <Col span={6}>
            <Card>
              <Statistic
                title="进行中"
                value={productionData.in_progress_plans}
                valueStyle={{ color: '#1890ff' }}
              />
            </Card>
          </Col>
          <Col span={6}>
            <Card>
              <Statistic
                title="逾期计划"
                value={productionData.overdue_plans}
                valueStyle={{ color: '#cf1322' }}
              />
            </Card>
          </Col>
        </Row>

        <Row gutter={[16, 16]}>
          <Col span={12}>
            <Card title="日产量趋势">
              <LineChart data={lineData} height={300} />
            </Card>
          </Col>
          <Col span={12}>
            <Card title="车间产量分布">
              <BarChart data={barData} height={300} />
            </Card>
          </Col>
        </Row>

        <Row gutter={[16, 16]} style={{ marginTop: 16 }}>
          <Col span={24}>
            <Card title="车间统计详情">
              <Table
                columns={workshopColumns}
                dataSource={productionData.workshop_stats}
                rowKey="workshop"
                pagination={false}
                size="small"
              />
            </Card>
          </Col>
        </Row>
      </div>
    );
  };

  // 质量报表内容
  const renderQualityReport = () => {
    if (!qualityData) return null;

    const defectColumns: ColumnsType<any> = [
      { title: '缺陷类型', dataIndex: 'defect_type', key: 'defect_type' },
      { title: '数量', dataIndex: 'count', key: 'count' },
      { 
        title: '占比', 
        dataIndex: 'percentage', 
        key: 'percentage',
        render: (value: number) => `${value.toFixed(1)}%`
      }
    ];

    const productColumns: ColumnsType<any> = [
      { title: '产品名称', dataIndex: 'product_name', key: 'product_name' },
      { title: '检查次数', dataIndex: 'total_checks', key: 'total_checks' },
      { title: '通过次数', dataIndex: 'passed_checks', key: 'passed_checks' },
      { 
        title: '合格率', 
        dataIndex: 'pass_rate', 
        key: 'pass_rate',
        render: (value: number) => `${value.toFixed(1)}%`
      }
    ];

    const trendData = qualityData.quality_trends.map(item => ({
      x: item.date,
      y: item.pass_rate
    }));

    const pieData = qualityData.defect_analysis.map(item => ({
       type: item.defect_type,
       value: item.count
     }));

    return (
      <div>
        <Row gutter={[16, 16]} style={{ marginBottom: 24 }}>
          <Col span={6}>
            <Card>
              <Statistic
                title="总检查次数"
                value={qualityData.total_checks}
                prefix={<LineChartOutlined />}
              />
            </Card>
          </Col>
          <Col span={6}>
            <Card>
              <Statistic
                title="通过次数"
                value={qualityData.passed_checks}
                valueStyle={{ color: '#3f8600' }}
              />
            </Card>
          </Col>
          <Col span={6}>
            <Card>
              <Statistic
                title="合格率"
                value={qualityData.pass_rate}
                precision={1}
                suffix="%"
                valueStyle={{ color: '#3f8600' }}
              />
            </Card>
          </Col>
          <Col span={6}>
            <Card>
              <Statistic
                title="缺陷率"
                value={qualityData.defect_rate}
                precision={1}
                suffix="%"
                valueStyle={{ color: '#cf1322' }}
              />
            </Card>
          </Col>
        </Row>

        <Row gutter={[16, 16]}>
          <Col span={12}>
            <Card title="质量趋势">
              <LineChart data={trendData} height={300} />
            </Card>
          </Col>
          <Col span={12}>
            <Card title="缺陷分析">
              <PieChart data={pieData} height={300} />
            </Card>
          </Col>
        </Row>

        <Row gutter={[16, 16]} style={{ marginTop: 16 }}>
          <Col span={12}>
            <Card title="缺陷统计">
              <Table
                columns={defectColumns}
                dataSource={qualityData.defect_analysis}
                rowKey="defect_type"
                pagination={false}
                size="small"
              />
            </Card>
          </Col>
          <Col span={12}>
            <Card title="产品质量">
              <Table
                columns={productColumns}
                dataSource={qualityData.product_quality}
                rowKey="product_name"
                pagination={false}
                size="small"
              />
            </Card>
          </Col>
        </Row>
      </div>
    );
  };

  // 设备报表内容
  const renderEquipmentReport = () => {
    if (!equipmentData) return null;

    const maintenanceColumns: ColumnsType<any> = [
      { title: '维护类型', dataIndex: 'maintenance_type', key: 'maintenance_type' },
      { title: '次数', dataIndex: 'count', key: 'count' },
      { 
        title: '平均成本', 
        dataIndex: 'avg_cost', 
        key: 'avg_cost',
        render: (value: number) => `¥${value.toFixed(0)}`
      }
    ];

    const faultColumns: ColumnsType<any> = [
      { title: '设备类型', dataIndex: 'equipment_type', key: 'equipment_type' },
      { title: '故障次数', dataIndex: 'fault_count', key: 'fault_count' },
      { 
        title: '故障率', 
        dataIndex: 'fault_rate', 
        key: 'fault_rate',
        render: (value: number) => `${value.toFixed(2)}%`
      }
    ];

    const utilizationData = equipmentData.efficiency_trends.map(item => ({
      x: item.date,
      y: item.utilization_rate
    }));

    return (
      <div>
        <Row gutter={[16, 16]} style={{ marginBottom: 24 }}>
          <Col span={6}>
            <Card>
              <Statistic
                title="设备总数"
                value={equipmentData.total_equipment}
                prefix={<BarChartOutlined />}
              />
            </Card>
          </Col>
          <Col span={6}>
            <Card>
              <Statistic
                title="运行中"
                value={equipmentData.running_equipment}
                valueStyle={{ color: '#3f8600' }}
              />
            </Card>
          </Col>
          <Col span={6}>
            <Card>
              <Statistic
                title="维护中"
                value={equipmentData.maintenance_equipment}
                valueStyle={{ color: '#1890ff' }}
              />
            </Card>
          </Col>
          <Col span={6}>
            <Card>
              <Statistic
                title="故障设备"
                value={equipmentData.fault_equipment}
                valueStyle={{ color: '#cf1322' }}
              />
            </Card>
          </Col>
        </Row>

        <Row gutter={[16, 16]}>
          <Col span={24}>
            <Card title="设备利用率趋势">
              <LineChart data={utilizationData} height={300} />
            </Card>
          </Col>
        </Row>

        <Row gutter={[16, 16]} style={{ marginTop: 16 }}>
          <Col span={12}>
            <Card title="维护统计">
              <Table
                columns={maintenanceColumns}
                dataSource={equipmentData.maintenance_stats}
                rowKey="maintenance_type"
                pagination={false}
                size="small"
              />
            </Card>
          </Col>
          <Col span={12}>
            <Card title="故障分析">
              <Table
                columns={faultColumns}
                dataSource={equipmentData.fault_analysis}
                rowKey="equipment_type"
                pagination={false}
                size="small"
              />
            </Card>
          </Col>
        </Row>
      </div>
    );
  };

  return (
    <div style={{ padding: 24 }}>
      <Title level={2}>报表生成</Title>
      
      <Card style={{ marginBottom: 24 }}>
        <Row gutter={16} align="middle">
          <Col>
            <Text strong>时间范围：</Text>
          </Col>
          <Col>
            <RangePicker
              value={dateRange}
              onChange={(dates) => {
                if (dates && dates[0] && dates[1]) {
                  setDateRange([dates[0], dates[1]]);
                }
              }}
              format="YYYY-MM-DD"
            />
          </Col>
          <Col>
            <Button type="primary" onClick={generateReport} loading={loading}>
              生成报表
            </Button>
          </Col>
          <Col>
            <Space>
              <Button 
                icon={<FileExcelOutlined />} 
                onClick={() => exportReport('excel')}
              >
                导出Excel
              </Button>
              <Button 
                icon={<FilePdfOutlined />} 
                onClick={() => exportReport('pdf')}
              >
                导出PDF
              </Button>
            </Space>
          </Col>
        </Row>
      </Card>

      <Spin spinning={loading}>
        <Tabs activeKey={activeTab} onChange={setActiveTab}>
          <TabPane tab="生产报表" key="production">
            {renderProductionReport()}
          </TabPane>
          <TabPane tab="质量报表" key="quality">
            {renderQualityReport()}
          </TabPane>
          <TabPane tab="设备报表" key="equipment">
            {renderEquipmentReport()}
          </TabPane>
        </Tabs>
      </Spin>
    </div>
  );
};

export default Reports;