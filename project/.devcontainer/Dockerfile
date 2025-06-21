# 3AI工作室开发环境容器
# 基于Ubuntu 22.04，包含Node.js、Python、开发工具等

FROM mcr.microsoft.com/devcontainers/base:ubuntu-22.04

# 设置环境变量
ENV DEBIAN_FRONTEND=noninteractive
ENV NODE_VERSION=18
ENV PYTHON_VERSION=3.11
ENV WORKSPACE_DIR=/workspace

# 设置工作目录
WORKDIR $WORKSPACE_DIR

# 更新包管理器并安装基础工具
RUN apt-get update && apt-get install -y \
    # 基础工具
    curl \
    wget \
    git \
    vim \
    nano \
    htop \
    tree \
    jq \
    unzip \
    zip \
    # 构建工具
    build-essential \
    pkg-config \
    # 网络工具
    net-tools \
    iputils-ping \
    telnet \
    netcat \
    # SSL/TLS
    ca-certificates \
    gnupg \
    lsb-release \
    # Python 依赖
    python3-dev \
    python3-pip \
    python3-venv \
    # PostgreSQL 客户端
    postgresql-client \
    # Redis 客户端
    redis-tools \
    # 图像处理库
    libpng-dev \
    libjpeg-dev \
    libgif-dev \
    # 其他有用工具
    software-properties-common \
    apt-transport-https \
    && rm -rf /var/lib/apt/lists/*

# 安装 Node.js 和 npm
RUN curl -fsSL https://deb.nodesource.com/setup_${NODE_VERSION}.x | bash - \
    && apt-get install -y nodejs

# 安装全局 npm 包
RUN npm install -g \
    npm@latest \
    yarn \
    pnpm \
    typescript \
    ts-node \
    nodemon \
    pm2 \
    @nestjs/cli \
    create-react-app \
    vite \
    eslint \
    prettier \
    jest \
    webpack-cli

# 安装 Python 工具
RUN python3 -m pip install --upgrade pip setuptools wheel

# 安装常用 Python 包
RUN pip3 install \
    # Web 框架
    fastapi \
    uvicorn[standard] \
    # 数据库
    sqlalchemy \
    alembic \
    psycopg2-binary \
    redis \
    # 开发工具
    black \
    isort \
    flake8 \
    mypy \
    pytest \
    pytest-cov \
    pytest-asyncio \
    # 实用库
    python-dotenv \
    pydantic \
    requests \
    aiohttp \
    celery \
    # 数据处理
    pandas \
    numpy \
    # 日期时间
    python-dateutil \
    # 加密
    cryptography \
    passlib[bcrypt] \
    # JWT
    python-jose[cryptography]

# 安装 Docker CLI
RUN curl -fsSL https://download.docker.com/linux/ubuntu/gpg | gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg \
    && echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | tee /etc/apt/sources.list.d/docker.list > /dev/null \
    && apt-get update \
    && apt-get install -y docker-ce-cli \
    && rm -rf /var/lib/apt/lists/*

# 安装 Docker Compose
RUN curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose \
    && chmod +x /usr/local/bin/docker-compose

# 创建开发用户
ARG USERNAME=vscode
ARG USER_UID=1000
ARG USER_GID=$USER_UID

# 创建用户组和用户
RUN groupadd --gid $USER_GID $USERNAME \
    && useradd --uid $USER_UID --gid $USER_GID -m $USERNAME \
    && echo $USERNAME ALL=\(root\) NOPASSWD:ALL > /etc/sudoers.d/$USERNAME \
    && chmod 0440 /etc/sudoers.d/$USERNAME

# 将用户添加到 docker 组
RUN usermod -aG docker $USERNAME

# 设置 Git 安全目录
RUN git config --global --add safe.directory $WORKSPACE_DIR

# 创建必要的目录并设置权限
RUN mkdir -p $WORKSPACE_DIR/.vscode-server/extensions \
    && mkdir -p $WORKSPACE_DIR/node_modules \
    && mkdir -p $WORKSPACE_DIR/venv \
    && mkdir -p $WORKSPACE_DIR/logs \
    && mkdir -p $WORKSPACE_DIR/uploads \
    && mkdir -p $WORKSPACE_DIR/temp \
    && chown -R $USERNAME:$USERNAME $WORKSPACE_DIR

# 安装 Oh My Zsh (可选)
RUN sh -c "$(curl -fsSL https://raw.github.com/ohmyzsh/ohmyzsh/master/tools/install.sh)" "" --unattended \
    && chsh -s $(which zsh) $USERNAME

# 配置 zsh 主题和插件
RUN sed -i 's/ZSH_THEME="robbyrussell"/ZSH_THEME="agnoster"/' /home/$USERNAME/.zshrc \
    && echo 'plugins=(git node npm docker docker-compose python pip)' >> /home/$USERNAME/.zshrc

# 设置 npm 全局目录权限
RUN mkdir -p /home/$USERNAME/.npm-global \
    && chown -R $USERNAME:$USERNAME /home/$USERNAME/.npm-global \
    && echo 'export PATH=/home/$USERNAME/.npm-global/bin:$PATH' >> /home/$USERNAME/.bashrc \
    && echo 'export PATH=/home/$USERNAME/.npm-global/bin:$PATH' >> /home/$USERNAME/.zshrc

# 切换到开发用户
USER $USERNAME

# 设置 npm 配置
RUN npm config set prefix '/home/$USERNAME/.npm-global'

# 创建 Python 虚拟环境
RUN python3 -m venv $WORKSPACE_DIR/venv

# 设置默认 shell
SHELL ["/bin/zsh", "-c"]

# 健康检查
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD node --version && python3 --version || exit 1

# 暴露常用端口
EXPOSE 3000 8000 5173 8080

# 设置启动命令
CMD ["/bin/zsh"]