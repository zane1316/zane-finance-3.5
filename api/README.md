# 爬虫API部署指南

## 部署方式

### 方式1：Vercel Serverless Functions（推荐）
1. 将 `api/` 文件夹上传到 GitHub
2. Vercel 自动识别为 Serverless Functions
3. 免费额度：100GB/月 带宽

### 方式2：PythonAnywhere（免费）
1. 注册 pythonanywhere.com
2. 上传 `main.py`
3. 配置WSGI指向FastAPI应用

### 方式3：Render（免费）
1. 连接GitHub仓库
2. 自动部署Python服务

### 方式4：自有服务器
```bash
pip install fastapi uvicorn requests beautifulsoup4
python main.py
```

## API端点

| 端点 | 方法 | 说明 |
|------|------|------|
| /api/news | GET | 获取财经资讯 |
| /api/news/hot | GET | 获取热点资讯 |
| /api/stock/realtime | GET | 股票实时数据 |
| /health | GET | 健康检查 |

## 参数说明

### /api/news
- `category`: 分类 (announcement/news/hot/all)
- `limit`: 数量限制 (默认20)

### /api/stock/realtime
- `codes`: 股票代码，逗号分隔，如 `sh000001,sz399001`

## 前端调用示例

```javascript
// 获取资讯
fetch('https://your-api.com/api/news?limit=10')
  .then(r => r.json())
  .then(data => console.log(data));

// 获取股票数据
fetch('https://your-api.com/api/stock/realtime?codes=sh000001,sz399001')
  .then(r => r.json())
  .then(data => console.log(data));
```
