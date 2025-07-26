# Git提交前检查系统使用说明

## 概述

为了防止错误内容被提交到Git仓库，我们建立了一套自动化的提交前检查系统。该系统会在每次Git提交前自动运行，验证项目结构和内容的正确性。

## 系统组成

### 1. 核心检查脚本
- **文件位置**: `tools/git_pre_commit_check.py`
- **功能**: 执行项目结构和内容验证
- **检查项目**:
  - project目录结构验证
  - Python源代码完整性检查
  - 禁止前端配置文件混入
  - 文件编码格式验证
  - docs和tools目录结构检查

### 2. Git钩子脚本
- **文件位置**: `.git/hooks/pre-commit`
- **功能**: 在Git提交前自动调用检查脚本
- **触发时机**: 每次执行`git commit`命令时

## 检查规则详解

### Project目录检查

#### 必需目录结构
```
project/src/
├── ai/          # AI模块
├── config/      # 配置模块
├── core/        # 核心模块
├── creo/        # Creo连接模块
├── geometry/    # 几何处理模块
├── ui/          # 用户界面模块
└── utils/       # 工具模块
```

#### 必需文件
- `project/src/main.py` - 主程序入口

#### 禁止文件（前端配置）
- `.eslintrc.js`
- `.prettierrc`
- `webpack_config.js`
- `babel_config.js`
- `jest_config.js`
- `tsconfig.json`
- 其他JavaScript/TypeScript配置文件

### Docs目录检查

#### 推荐目录结构
```
docs/
├── 01-设计/     # 设计文档
├── 02-开发/     # 开发文档
├── 03-管理/     # 管理文档
└── 04-模板/     # 模板文档
```

### Tools目录检查

#### 必需文件
- `check_structure.py` - 项目结构检查工具
- `finish.py` - 完成脚本

#### 禁止目录
- `node_modules/`
- `dist/`
- `build/`

## 使用方法

### 自动检查（推荐）

系统已配置为自动运行，无需手动操作：

```bash
# 正常的Git提交流程
git add .
git commit -m "提交信息"
```

如果检查通过，提交将正常进行。如果检查失败，提交将被阻止，并显示错误信息。

### 手动检查

可以在提交前手动运行检查：

```bash
# 在Git仓库根目录下运行
python tools/git_pre_commit_check.py
```

### 强制提交（紧急情况）

如果确实需要跳过检查（不推荐），可以使用：

```bash
git commit --no-verify -m "紧急提交信息"
```

## 检查结果说明

### 成功示例
```
============================================================
Git提交前检查结果
============================================================

✅ 所有检查通过！
============================================================
```

### 失败示例
```
============================================================
Git提交前检查结果
============================================================

❌ 发现 2 个错误:
  1. 发现禁止的前端配置文件: project/.eslintrc.js
  2. 缺少必需文件: project/src/main.py

⚠️  发现 1 个警告:
  1. 建议添加目录: docs/01-设计

❌ 检查失败，请修复错误后重新提交
============================================================
```

## 常见问题处理

### 1. 检查脚本无法运行

**问题**: `ImportError: cannot import name 'setup_logging'`

**解决**: 确保tools目录下有完整的依赖文件：
- `utils.py`
- `logging_config.py`
- `exceptions.py`

### 2. 前端文件被误检测

**问题**: 正常的配置文件被标记为禁止文件

**解决**: 检查文件是否放在了错误的位置。前端配置文件应该放在project目录之外。

### 3. Python文件包含JavaScript代码

**问题**: `.py`文件中包含了JavaScript语法

**解决**: 清理Python文件中的JavaScript代码，或将JavaScript代码移动到正确的位置。

### 4. 文件编码问题

**问题**: `文件编码不是UTF-8`

**解决**: 将文件重新保存为UTF-8编码格式。

## 系统维护

### 更新检查规则

修改`tools/git_pre_commit_check.py`中的`expected_structure`配置：

```python
self.expected_structure = {
    'project/src': {
        'required_dirs': ['ai', 'config', 'core', 'creo', 'geometry', 'ui', 'utils'],
        'required_files': ['main.py'],
        'forbidden_files': ['.eslintrc.js', '.prettierrc', 'webpack_config.js']
    },
    # 添加新的检查规则...
}
```

### 禁用检查系统

如果需要临时禁用检查系统：

```bash
# 重命名钩子文件
mv .git/hooks/pre-commit .git/hooks/pre-commit.disabled
```

### 重新启用检查系统

```bash
# 恢复钩子文件
mv .git/hooks/pre-commit.disabled .git/hooks/pre-commit
```

## 最佳实践

1. **定期更新检查规则**: 随着项目发展，及时更新检查规则以适应新的需求

2. **团队培训**: 确保所有团队成员了解检查系统的工作原理和使用方法

3. **错误处理**: 遇到检查失败时，仔细阅读错误信息并逐一修复

4. **备份重要更改**: 在进行大规模重构前，确保有完整的备份

5. **渐进式修复**: 对于大量错误，建议分批次修复并提交

## 技术支持

如果遇到技术问题，请：

1. 查看日志文件：`logs/其他日志/application.log`
2. 运行手动检查获取详细错误信息
3. 联系技术负责人：雨俊

---

**版本**: 1.0  
**更新日期**: 2025-07-26  
**维护人**: 雨俊