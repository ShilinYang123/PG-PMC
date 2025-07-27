import React, { useState, useCallback } from 'react';
import {
  Modal,
  Upload,
  Button,
  Select,
  Form,
  Input,
  Switch,
  Progress,
  Table,
  message,
  Space,
  Divider,
  Card,
  Row,
  Col,
  Tag,
  Tooltip,
  Alert
} from 'antd';
import {
  UploadOutlined,
  DownloadOutlined,
  FileExcelOutlined,
  FileTextOutlined,
  CloudUploadOutlined,
  CheckCircleOutlined,
  ExclamationCircleOutlined,
  InfoCircleOutlined
} from '@ant-design/icons';
import type { UploadFile, UploadProps } from 'antd/es/upload/interface';
import type { ColumnsType } from 'antd/es/table';
import './index.css';

const { Option } = Select;
const { TextArea } = Input;

// 数据类型配置
const DATA_TYPES = {
  progress: { label: '进度数据', icon: <FileExcelOutlined />, color: '#1890ff' },
  equipment: { label: '设备数据', icon: <FileExcelOutlined />, color: '#52c41a' },
  material: { label: '物料数据', icon: <FileExcelOutlined />, color: '#faad14' },
  production_plan: { label: '生产计划', icon: <FileExcelOutlined />, color: '#722ed1' },
  order: { label: '订单数据', icon: <FileExcelOutlined />, color: '#eb2f96' },
  user: { label: '用户数据', icon: <FileExcelOutlined />, color: '#13c2c2' }
};

// 文件格式配置
const FILE_FORMATS = {
  xlsx: { label: 'Excel 2007+', icon: <FileExcelOutlined />, accept: '.xlsx' },
  xls: { label: 'Excel 97-2003', icon: <FileExcelOutlined />, accept: '.xls' },
  csv: { label: 'CSV 文件', icon: <FileTextOutlined />, accept: '.csv' }
};

interface ImportExportProps {
  visible: boolean;
  mode: 'import' | 'export';
  dataType: string;
  onCancel: () => void;
  onSuccess?: (result: any) => void;
}

interface TaskStatus {
  taskId: string;
  status: 'pending' | 'processing' | 'completed' | 'failed';
  progress: number;
  message: string;
  result?: any;
  error?: string;
}

const ImportExportModal: React.FC<ImportExportProps> = ({
  visible,
  mode,
  dataType,
  onCancel,
  onSuccess
}) => {
  const [form] = Form.useForm();
  const [loading, setLoading] = useState(false);
  const [fileList, setFileList] = useState<UploadFile[]>([]);
  const [taskStatus, setTaskStatus] = useState<TaskStatus | null>(null);
  const [previewData, setPreviewData] = useState<any[]>([]);
  const [fieldMapping, setFieldMapping] = useState<Record<string, string>>({});
  const [step, setStep] = useState(1);

  // 重置状态
  const resetState = useCallback(() => {
    setFileList([]);
    setTaskStatus(null);
    setPreviewData([]);
    setFieldMapping({});
    setStep(1);
    form.resetFields();
  }, [form]);

  // 处理模态框关闭
  const handleCancel = useCallback(() => {
    resetState();
    onCancel();
  }, [resetState, onCancel]);

  // 文件上传配置
  const uploadProps: UploadProps = {
    name: 'file',
    multiple: false,
    fileList,
    beforeUpload: (file) => {
      const isValidType = Object.values(FILE_FORMATS).some(
        format => file.name.toLowerCase().endsWith(format.accept)
      );
      
      if (!isValidType) {
        message.error('请上传 Excel 或 CSV 文件！');
        return false;
      }
      
      const isLt10M = file.size! / 1024 / 1024 < 10;
      if (!isLt10M) {
        message.error('文件大小不能超过 10MB！');
        return false;
      }
      
      return false; // 阻止自动上传
    },
    onChange: (info) => {
      setFileList(info.fileList.slice(-1)); // 只保留最后一个文件
    },
    onRemove: () => {
      setFileList([]);
      setPreviewData([]);
      setFieldMapping({});
    }
  };

  // 上传文件
  const uploadFile = async (file: UploadFile) => {
    const formData = new FormData();
    formData.append('file', file.originFileObj as File);
    formData.append('category', 'import');

    try {
      const response = await fetch('/api/import-export/upload', {
        method: 'POST',
        body: formData,
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        }
      });

      if (!response.ok) {
        throw new Error('文件上传失败');
      }

      const result = await response.json();
      return result;
    } catch (error) {
      console.error('文件上传错误:', error);
      throw error;
    }
  };

  // 预览数据
  const previewImportData = async () => {
    if (fileList.length === 0) {
      message.warning('请先选择文件');
      return;
    }

    setLoading(true);
    try {
      // 上传文件
      const uploadResult = await uploadFile(fileList[0]);
      
      // 读取文件内容进行预览
      const previewResponse = await fetch('/api/import-export/preview', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        },
        body: JSON.stringify({
          file_path: uploadResult.file_url,
          data_type: dataType,
          max_rows: 10
        })
      });

      if (!previewResponse.ok) {
        throw new Error('预览数据失败');
      }

      const previewResult = await previewResponse.json();
      setPreviewData(previewResult.data || []);
      setStep(2);
      
      message.success('文件上传成功，请配置字段映射');
    } catch (error) {
      console.error('预览数据错误:', error);
      message.error('预览数据失败');
    } finally {
      setLoading(false);
    }
  };

  // 执行导入
  const executeImport = async () => {
    const values = form.getFieldsValue();
    
    setLoading(true);
    try {
      const response = await fetch(`/api/import-export/import/${dataType}`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        },
        body: JSON.stringify({
          file_path: fileList[0]?.response?.file_url,
          field_mapping: fieldMapping,
          ...values
        })
      });

      if (!response.ok) {
        throw new Error('导入失败');
      }

      const result = await response.json();
      setTaskStatus({
        taskId: result.task_id,
        status: 'processing',
        progress: 0,
        message: '正在处理导入任务...'
      });
      
      setStep(3);
      
      // 轮询任务状态
      pollTaskStatus(result.task_id);
      
    } catch (error) {
      console.error('导入错误:', error);
      message.error('导入失败');
    } finally {
      setLoading(false);
    }
  };

  // 执行导出
  const executeExport = async () => {
    const values = form.getFieldsValue();
    
    setLoading(true);
    try {
      const response = await fetch(`/api/import-export/export/${dataType}`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        },
        body: JSON.stringify(values)
      });

      if (!response.ok) {
        throw new Error('导出失败');
      }

      const result = await response.json();
      setTaskStatus({
        taskId: result.task_id,
        status: 'processing',
        progress: 0,
        message: '正在处理导出任务...'
      });
      
      setStep(2);
      
      // 轮询任务状态
      pollTaskStatus(result.task_id);
      
    } catch (error) {
      console.error('导出错误:', error);
      message.error('导出失败');
    } finally {
      setLoading(false);
    }
  };

  // 轮询任务状态
  const pollTaskStatus = async (taskId: string) => {
    const poll = async () => {
      try {
        const response = await fetch(`/api/import-export/task/${taskId}/status`, {
          headers: {
            'Authorization': `Bearer ${localStorage.getItem('token')}`
          }
        });

        if (!response.ok) {
          throw new Error('获取任务状态失败');
        }

        const status = await response.json();
        setTaskStatus(status);

        if (status.status === 'completed') {
          message.success('任务完成');
          onSuccess?.(status.result);
        } else if (status.status === 'failed') {
          message.error(`任务失败: ${status.error}`);
        } else {
          // 继续轮询
          setTimeout(poll, 2000);
        }
      } catch (error) {
        console.error('轮询任务状态错误:', error);
        message.error('获取任务状态失败');
      }
    };

    poll();
  };

  // 下载模板
  const downloadTemplate = async () => {
    try {
      const response = await fetch(`/api/import-export/template/${dataType}?format=xlsx`, {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        }
      });

      if (!response.ok) {
        throw new Error('下载模板失败');
      }

      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `${dataType}_template.xlsx`;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
      
      message.success('模板下载成功');
    } catch (error) {
      console.error('下载模板错误:', error);
      message.error('下载模板失败');
    }
  };

  // 下载导出文件
  const downloadExportFile = async () => {
    if (!taskStatus?.result?.download_url) {
      message.warning('下载链接不可用');
      return;
    }

    try {
      const response = await fetch(taskStatus.result.download_url, {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        }
      });

      if (!response.ok) {
        throw new Error('下载文件失败');
      }

      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `${dataType}_export_${new Date().getTime()}.xlsx`;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
      
      message.success('文件下载成功');
    } catch (error) {
      console.error('下载文件错误:', error);
      message.error('下载文件失败');
    }
  };

  // 预览数据表格列
  const previewColumns: ColumnsType<any> = previewData.length > 0 
    ? Object.keys(previewData[0]).map(key => ({
        title: key,
        dataIndex: key,
        key,
        ellipsis: true,
        width: 150
      }))
    : [];

  // 渲染导入步骤
  const renderImportSteps = () => {
    if (step === 1) {
      return (
        <div className="import-step-1">
          <Alert
            message="导入说明"
            description={
              <div>
                <p>1. 请先下载导入模板，按照模板格式准备数据</p>
                <p>2. 支持 Excel (.xlsx, .xls) 和 CSV 格式文件</p>
                <p>3. 文件大小不能超过 10MB</p>
                <p>4. 请确保数据格式正确，避免导入失败</p>
              </div>
            }
            type="info"
            showIcon
            style={{ marginBottom: 16 }}
          />
          
          <Space direction="vertical" style={{ width: '100%' }}>
            <Button 
              type="dashed" 
              icon={<DownloadOutlined />}
              onClick={downloadTemplate}
              block
            >
              下载导入模板
            </Button>
            
            <Upload.Dragger {...uploadProps}>
              <p className="ant-upload-drag-icon">
                <CloudUploadOutlined />
              </p>
              <p className="ant-upload-text">点击或拖拽文件到此区域上传</p>
              <p className="ant-upload-hint">
                支持 Excel 和 CSV 格式，文件大小不超过 10MB
              </p>
            </Upload.Dragger>
            
            {fileList.length > 0 && (
              <Button 
                type="primary" 
                icon={<FileExcelOutlined />}
                onClick={previewImportData}
                loading={loading}
                block
              >
                预览数据
              </Button>
            )}
          </Space>
        </div>
      );
    }

    if (step === 2) {
      return (
        <div className="import-step-2">
          <Alert
            message="字段映射配置"
            description="请配置Excel列与系统字段的映射关系，确保数据正确导入"
            type="info"
            showIcon
            style={{ marginBottom: 16 }}
          />
          
          <Form form={form} layout="vertical">
            <Row gutter={16}>
              <Col span={12}>
                <Form.Item label="工作表名称" name="sheet_name">
                  <Input placeholder="默认为第一个工作表" />
                </Form.Item>
              </Col>
              <Col span={12}>
                <Form.Item label="标题行" name="header_row" initialValue={0}>
                  <Select>
                    <Option value={0}>第1行</Option>
                    <Option value={1}>第2行</Option>
                    <Option value={2}>第3行</Option>
                  </Select>
                </Form.Item>
              </Col>
            </Row>
            
            <Form.Item label="跳过错误" name="skip_errors" valuePropName="checked">
              <Switch />
            </Form.Item>
          </Form>
          
          {previewData.length > 0 && (
            <>
              <Divider>数据预览</Divider>
              <Table
                columns={previewColumns}
                dataSource={previewData}
                pagination={false}
                scroll={{ x: true, y: 300 }}
                size="small"
              />
            </>
          )}
          
          <div style={{ marginTop: 16, textAlign: 'right' }}>
            <Space>
              <Button onClick={() => setStep(1)}>上一步</Button>
              <Button 
                type="primary" 
                onClick={executeImport}
                loading={loading}
              >
                开始导入
              </Button>
            </Space>
          </div>
        </div>
      );
    }

    if (step === 3 && taskStatus) {
      return (
        <div className="import-step-3">
          <Card>
            <div style={{ textAlign: 'center' }}>
              <div style={{ marginBottom: 16 }}>
                {taskStatus.status === 'processing' && (
                  <InfoCircleOutlined style={{ fontSize: 48, color: '#1890ff' }} />
                )}
                {taskStatus.status === 'completed' && (
                  <CheckCircleOutlined style={{ fontSize: 48, color: '#52c41a' }} />
                )}
                {taskStatus.status === 'failed' && (
                  <ExclamationCircleOutlined style={{ fontSize: 48, color: '#ff4d4f' }} />
                )}
              </div>
              
              <h3>{taskStatus.message}</h3>
              
              <Progress 
                percent={taskStatus.progress} 
                status={taskStatus.status === 'failed' ? 'exception' : 'active'}
                style={{ marginBottom: 16 }}
              />
              
              {taskStatus.result && (
                <div>
                  <Row gutter={16} style={{ marginBottom: 16 }}>
                    <Col span={8}>
                      <Card size="small">
                        <div style={{ textAlign: 'center' }}>
                          <div style={{ fontSize: 24, fontWeight: 'bold', color: '#52c41a' }}>
                            {taskStatus.result.success_count || 0}
                          </div>
                          <div>成功</div>
                        </div>
                      </Card>
                    </Col>
                    <Col span={8}>
                      <Card size="small">
                        <div style={{ textAlign: 'center' }}>
                          <div style={{ fontSize: 24, fontWeight: 'bold', color: '#ff4d4f' }}>
                            {taskStatus.result.error_count || 0}
                          </div>
                          <div>失败</div>
                        </div>
                      </Card>
                    </Col>
                    <Col span={8}>
                      <Card size="small">
                        <div style={{ textAlign: 'center' }}>
                          <div style={{ fontSize: 24, fontWeight: 'bold' }}>
                            {taskStatus.result.total_count || 0}
                          </div>
                          <div>总计</div>
                        </div>
                      </Card>
                    </Col>
                  </Row>
                </div>
              )}
              
              {taskStatus.error && (
                <Alert
                  message="错误信息"
                  description={taskStatus.error}
                  type="error"
                  showIcon
                  style={{ marginBottom: 16 }}
                />
              )}
            </div>
          </Card>
        </div>
      );
    }

    return null;
  };

  // 渲染导出表单
  const renderExportForm = () => {
    return (
      <div className="export-form">
        <Alert
          message="导出说明"
          description="请配置导出参数，系统将根据您的设置生成相应的数据文件"
          type="info"
          showIcon
          style={{ marginBottom: 16 }}
        />
        
        <Form form={form} layout="vertical">
          <Row gutter={16}>
            <Col span={12}>
              <Form.Item 
                label="导出格式" 
                name="format" 
                initialValue="xlsx"
                rules={[{ required: true, message: '请选择导出格式' }]}
              >
                <Select>
                  {Object.entries(FILE_FORMATS).map(([key, format]) => (
                    <Option key={key} value={key}>
                      {format.icon} {format.label}
                    </Option>
                  ))}
                </Select>
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item label="最大行数" name="limit">
                <Select placeholder="不限制">
                  <Option value={1000}>1,000 行</Option>
                  <Option value={5000}>5,000 行</Option>
                  <Option value={10000}>10,000 行</Option>
                  <Option value={50000}>50,000 行</Option>
                </Select>
              </Form.Item>
            </Col>
          </Row>
          
          <Form.Item label="导出字段" name="fields">
            <Select mode="multiple" placeholder="默认导出所有字段">
              <Option value="id">ID</Option>
              <Option value="name">名称</Option>
              <Option value="status">状态</Option>
              <Option value="created_date">创建时间</Option>
              <Option value="updated_date">更新时间</Option>
            </Select>
          </Form.Item>
          
          <Row gutter={16}>
            <Col span={12}>
              <Form.Item label="排序字段" name="sort_by">
                <Select placeholder="默认排序">
                  <Option value="id">ID</Option>
                  <Option value="created_date">创建时间</Option>
                  <Option value="updated_date">更新时间</Option>
                  <Option value="name">名称</Option>
                </Select>
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item label="排序方向" name="sort_order" initialValue="desc">
                <Select>
                  <Option value="asc">升序</Option>
                  <Option value="desc">降序</Option>
                </Select>
              </Form.Item>
            </Col>
          </Row>
          
          <Form.Item label="过滤条件" name="filters">
            <TextArea 
              rows={3} 
              placeholder='JSON格式，例如: {"status": "active", "created_date": {"gte": "2024-01-01"}}'
            />
          </Form.Item>
          
          <Form.Item label="包含标题" name="include_headers" valuePropName="checked" initialValue={true}>
            <Switch />
          </Form.Item>
        </Form>
        
        <div style={{ textAlign: 'right', marginTop: 16 }}>
          <Button 
            type="primary" 
            icon={<DownloadOutlined />}
            onClick={executeExport}
            loading={loading}
          >
            开始导出
          </Button>
        </div>
      </div>
    );
  };

  // 渲染导出结果
  const renderExportResult = () => {
    if (!taskStatus) return null;

    return (
      <div className="export-result">
        <Card>
          <div style={{ textAlign: 'center' }}>
            <div style={{ marginBottom: 16 }}>
              {taskStatus.status === 'processing' && (
                <InfoCircleOutlined style={{ fontSize: 48, color: '#1890ff' }} />
              )}
              {taskStatus.status === 'completed' && (
                <CheckCircleOutlined style={{ fontSize: 48, color: '#52c41a' }} />
              )}
              {taskStatus.status === 'failed' && (
                <ExclamationCircleOutlined style={{ fontSize: 48, color: '#ff4d4f' }} />
              )}
            </div>
            
            <h3>{taskStatus.message}</h3>
            
            <Progress 
              percent={taskStatus.progress} 
              status={taskStatus.status === 'failed' ? 'exception' : 'active'}
              style={{ marginBottom: 16 }}
            />
            
            {taskStatus.status === 'completed' && (
              <Button 
                type="primary" 
                icon={<DownloadOutlined />}
                onClick={downloadExportFile}
                size="large"
              >
                下载文件
              </Button>
            )}
            
            {taskStatus.error && (
              <Alert
                message="错误信息"
                description={taskStatus.error}
                type="error"
                showIcon
                style={{ marginTop: 16 }}
              />
            )}
          </div>
        </Card>
      </div>
    );
  };

  const dataTypeConfig = DATA_TYPES[dataType as keyof typeof DATA_TYPES];

  return (
    <Modal
      title={
        <Space>
          {dataTypeConfig?.icon}
          <span>
            {mode === 'import' ? '导入' : '导出'}
            {dataTypeConfig?.label}
          </span>
          <Tag color={dataTypeConfig?.color}>{dataType}</Tag>
        </Space>
      }
      open={visible}
      onCancel={handleCancel}
      footer={null}
      width={800}
      className="import-export-modal"
    >
      {mode === 'import' ? (
        taskStatus && step === 3 ? renderExportResult() : renderImportSteps()
      ) : (
        taskStatus ? renderExportResult() : renderExportForm()
      )}
    </Modal>
  );
};

export default ImportExportModal;