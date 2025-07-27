import { message } from 'antd';
import { request } from '../utils/request';

// 导入导出相关的类型定义
export interface FileUploadResponse {
  file_id: string;
  filename: string;
  file_size: number;
  upload_time: string;
}

export interface ImportRequest {
  file_id: string;
  data_type: string;
  field_mapping?: Record<string, string>;
  validation_rules?: Record<string, any>;
  import_config?: {
    skip_header?: boolean;
    batch_size?: number;
    ignore_errors?: boolean;
    update_existing?: boolean;
  };
}

export interface ExportRequest {
  data_type: string;
  export_format: 'excel' | 'csv';
  filters?: Record<string, any>;
  fields?: string[];
  export_config?: {
    include_header?: boolean;
    sheet_name?: string;
    date_format?: string;
  };
}

export interface ImportResponse {
  task_id: string;
  status: 'pending' | 'processing' | 'completed' | 'failed';
  message: string;
}

export interface ExportResponse {
  task_id: string;
  status: 'pending' | 'processing' | 'completed' | 'failed';
  message: string;
  download_url?: string;
}

export interface TaskStatus {
  task_id: string;
  status: 'pending' | 'processing' | 'completed' | 'failed';
  progress: number;
  message: string;
  result?: {
    total_records?: number;
    success_count?: number;
    error_count?: number;
    errors?: Array<{
      row: number;
      field: string;
      message: string;
    }>;
    download_url?: string;
  };
  created_at: string;
  updated_at: string;
}

export interface TemplateRequest {
  data_type: string;
  include_sample_data?: boolean;
}

export interface PreviewData {
  headers: string[];
  rows: any[][];
  total_rows: number;
}

class ImportExportService {
  private baseUrl = '/api/import-export';

  /**
   * 上传文件
   */
  async uploadFile(file: File): Promise<FileUploadResponse> {
    const formData = new FormData();
    formData.append('file', file);

    try {
      const response = await request.post(`${this.baseUrl}/upload`, formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });
      return response.data;
    } catch (error: any) {
      message.error(`文件上传失败: ${error.message}`);
      throw error;
    }
  }

  /**
   * 预览文件数据
   */
  async previewFile(fileId: string, rows: number = 10): Promise<PreviewData> {
    try {
      const response = await request.get(`${this.baseUrl}/preview/${fileId}`, {
        params: { rows }
      });
      return response.data;
    } catch (error: any) {
      message.error(`文件预览失败: ${error.message}`);
      throw error;
    }
  }

  /**
   * 导入数据
   */
  async importData(importRequest: ImportRequest): Promise<ImportResponse> {
    try {
      const response = await request.post(
        `${this.baseUrl}/import/${importRequest.data_type}`,
        importRequest
      );
      return response.data;
    } catch (error: any) {
      message.error(`数据导入失败: ${error.message}`);
      throw error;
    }
  }

  /**
   * 导出数据
   */
  async exportData(exportRequest: ExportRequest): Promise<ExportResponse> {
    try {
      const response = await request.post(
        `${this.baseUrl}/export/${exportRequest.data_type}`,
        exportRequest
      );
      return response.data;
    } catch (error: any) {
      message.error(`数据导出失败: ${error.message}`);
      throw error;
    }
  }

  /**
   * 获取任务状态
   */
  async getTaskStatus(taskId: string): Promise<TaskStatus> {
    try {
      const response = await request.get(`${this.baseUrl}/task/${taskId}/status`);
      return response.data;
    } catch (error: any) {
      message.error(`获取任务状态失败: ${error.message}`);
      throw error;
    }
  }

  /**
   * 下载模板文件
   */
  async downloadTemplate(templateRequest: TemplateRequest): Promise<void> {
    try {
      const response = await request.get(
        `${this.baseUrl}/template/${templateRequest.data_type}`,
        {
          params: templateRequest,
          responseType: 'blob'
        }
      );
      
      // 创建下载链接
      const blob = new Blob([response.data]);
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = `${templateRequest.data_type}_template.xlsx`;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      window.URL.revokeObjectURL(url);
      
      message.success('模板下载成功');
    } catch (error: any) {
      message.error(`模板下载失败: ${error.message}`);
      throw error;
    }
  }

  /**
   * 下载文件
   */
  async downloadFile(fileId: string, filename?: string): Promise<void> {
    try {
      const response = await request.get(`${this.baseUrl}/download/${fileId}`, {
        responseType: 'blob'
      });
      
      // 从响应头获取文件名
      const contentDisposition = response.headers['content-disposition'];
      let downloadFilename = filename;
      if (contentDisposition) {
        const filenameMatch = contentDisposition.match(/filename="(.+)"/i);
        if (filenameMatch) {
          downloadFilename = filenameMatch[1];
        }
      }
      
      // 创建下载链接
      const blob = new Blob([response.data]);
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = downloadFilename || 'download';
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      window.URL.revokeObjectURL(url);
      
      message.success('文件下载成功');
    } catch (error: any) {
      message.error(`文件下载失败: ${error.message}`);
      throw error;
    }
  }

  /**
   * 获取数据类型的字段配置
   */
  async getFieldConfig(dataType: string): Promise<Record<string, any>> {
    try {
      const response = await request.get(`${this.baseUrl}/fields/${dataType}`);
      return response.data;
    } catch (error: any) {
      message.error(`获取字段配置失败: ${error.message}`);
      throw error;
    }
  }

  /**
   * 验证导入数据
   */
  async validateImportData(fileId: string, dataType: string, fieldMapping?: Record<string, string>): Promise<{
    valid: boolean;
    errors: Array<{
      row: number;
      field: string;
      message: string;
    }>;
    warnings: Array<{
      row: number;
      field: string;
      message: string;
    }>;
  }> {
    try {
      const response = await request.post(`${this.baseUrl}/validate`, {
        file_id: fileId,
        data_type: dataType,
        field_mapping: fieldMapping
      });
      return response.data;
    } catch (error: any) {
      message.error(`数据验证失败: ${error.message}`);
      throw error;
    }
  }

  /**
   * 取消任务
   */
  async cancelTask(taskId: string): Promise<void> {
    try {
      await request.post(`${this.baseUrl}/task/${taskId}/cancel`);
      message.success('任务已取消');
    } catch (error: any) {
      message.error(`取消任务失败: ${error.message}`);
      throw error;
    }
  }

  /**
   * 获取导入导出历史
   */
  async getHistory(params?: {
    page?: number;
    page_size?: number;
    data_type?: string;
    status?: string;
    start_date?: string;
    end_date?: string;
  }): Promise<{
    items: TaskStatus[];
    total: number;
    page: number;
    page_size: number;
  }> {
    try {
      const response = await request.get(`${this.baseUrl}/history`, {
        params
      });
      return response.data;
    } catch (error: any) {
      message.error(`获取历史记录失败: ${error.message}`);
      throw error;
    }
  }

  /**
   * 批量删除历史记录
   */
  async deleteHistory(taskIds: string[]): Promise<void> {
    try {
      await request.delete(`${this.baseUrl}/history`, {
        data: { task_ids: taskIds }
      });
      message.success('历史记录删除成功');
    } catch (error: any) {
      message.error(`删除历史记录失败: ${error.message}`);
      throw error;
    }
  }

  /**
   * 获取支持的数据类型
   */
  getSupportedDataTypes(): Array<{
    value: string;
    label: string;
    description: string;
  }> {
    return [
      {
        value: 'progress',
        label: '进度数据',
        description: '项目进度跟踪数据'
      },
      {
        value: 'equipment',
        label: '设备数据',
        description: '设备信息和状态数据'
      },
      {
        value: 'material',
        label: '物料数据',
        description: '物料信息和库存数据'
      },
      {
        value: 'production_plan',
        label: '生产计划',
        description: '生产计划和排程数据'
      },
      {
        value: 'order',
        label: '订单数据',
        description: '订单信息和状态数据'
      },
      {
        value: 'user',
        label: '用户数据',
        description: '用户信息和权限数据'
      }
    ];
  }

  /**
   * 获取导出格式选项
   */
  getExportFormats(): Array<{
    value: string;
    label: string;
    description: string;
  }> {
    return [
      {
        value: 'excel',
        label: 'Excel (.xlsx)',
        description: '支持多工作表和格式化'
      },
      {
        value: 'csv',
        label: 'CSV (.csv)',
        description: '纯文本格式，兼容性好'
      }
    ];
  }
}

// 创建单例实例
const importExportService = new ImportExportService();

export default importExportService;