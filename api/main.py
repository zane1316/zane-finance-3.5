# 财经资讯爬虫后端服务
# 支持：东方财富、新浪财经、同花顺等主流财经网站

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
import requests
from bs4 import BeautifulSoup
import json
from datetime import datetime
import re

app = FastAPI(title="Zane财经资讯API", version="1.0.0")

# 启用CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class NewsItem(BaseModel):
    title: str
    summary: str
    source: str
    url: str
    publishTime: str
    category: str
    hot: bool = False

class NewsResponse(BaseModel):
    success: bool
    data: List[NewsItem]
    updateTime: str

# 东方财富快讯
def crawl_eastmoney_news():
    """爬取东方财富7x24快讯"""
    url = "https://push2.eastmoney.com/api/qt/stock/get?ut=fa5fd1943c7b386f172d6893dbfba10b&fltt=2&invt=2&volt=2&fields=f43,f44,f45,f46,f47,f48,f50,f51,f52,f57,f58,f60,f107,f116,f117,f162&secid=1.000001"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }
    
    try:
        # 东方财富API接口
        news_url = "https://np-anotice-stock.eastmoney.com/api/security/ann?sr=-1&page_size=20&page_index=1&ann_type=A"
        response = requests.get(news_url, headers=headers, timeout=10)
        data = response.json()
        
        news_items = []
        if 'data' in data and 'list' in data['data']:
            for item in data['data']['list'][:10]:
                news_items.append(NewsItem(
                    title=item.get('title', ''),
                    summary=item.get('content', '')[:200] + '...' if len(item.get('content', '')) > 200 else item.get('content', ''),
                    source=item.get('source', '东方财富'),
                    url=item.get('url', ''),
                    publishTime=item.get('time', datetime.now().strftime('%Y-%m-%d %H:%M')),
                    category='公告',
                    hot=False
                ))
        return news_items
    except Exception as e:
        print(f"东方财富爬取失败: {e}")
        return []

# 新浪财经要闻
def crawl_sina_finance():
    """爬取新浪财经要闻"""
    url = "https://feed.mix.sina.com.cn/api/roll/get?pageid=153&lid=2509&k=&num=20&page=1&r=0." + str(int(datetime.now().timestamp()))
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Referer': 'https://finance.sina.com.cn/'
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=10)
        data = response.json()
        
        news_items = []
        if 'result' in data and 'data' in data['result']:
            for item in data['result']['data'][:10]:
                news_items.append(NewsItem(
                    title=item.get('title', ''),
                    summary=item.get('summary', '')[:150] + '...' if item.get('summary') else '',
                    source='新浪财经',
                    url=item.get('url', ''),
                    publishTime=item.get('ctime', datetime.now().strftime('%Y-%m-%d %H:%M')),
                    category='财经要闻',
                    hot=False
                ))
        return news_items
    except Exception as e:
        print(f"新浪财经爬取失败: {e}")
        return []

# 同花顺热点
def crawl_ths_hot():
    """爬取同花顺热点资讯"""
    url = "https://basic.10jqka.com.cn/api/stockph/"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Referer': 'https://www.10jqka.com.cn/'
    }
    
    try:
        # 使用同花顺另一接口
        url = "https://news.10jqka.com.cn/tapp/news/push/stock/"
        response = requests.get(url, headers=headers, timeout=10)
        
        news_items = []
        try:
            data = response.json()
            if 'data' in data:
                for item in data['data'][:8]:
                    news_items.append(NewsItem(
                        title=item.get('title', ''),
                        summary=item.get('digest', '')[:150] + '...' if item.get('digest') else '',
                        source='同花顺',
                        url=item.get('url', ''),
                        publishTime=item.get('datetime', datetime.now().strftime('%Y-%m-%d %H:%M')),
                        category='热点',
                        hot=True
                    ))
        except:
            pass
        return news_items
    except Exception as e:
        print(f"同花顺爬取失败: {e}")
        return []

# 财联社电报
def crawl_cls_telegram():
    """爬取财联社电报"""
    url = "https://www.cls.cn/api/telegraph"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Referer': 'https://www.cls.cn/'
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=10)
        data = response.json()
        
        news_items = []
        if data.get('code') == 200 and 'data' in data:
            for item in data['data'][:10]:
                news_items.append(NewsItem(
                    title=item.get('title', item.get('content', ''))[:50] + '...',
                    summary=item.get('content', ''),
                    source='财联社',
                    url=f"https://www.cls.cn/detail/{item.get('id', '')}",
                    publishTime=item.get('time', datetime.now().strftime('%Y-%m-%d %H:%M')),
                    category='7x24快讯',
                    hot=item.get('is_important', False)
                ))
        return news_items
    except Exception as e:
        print(f"财联社爬取失败: {e}")
        return []

@app.get("/api/news", response_model=NewsResponse)
async def get_news(category: Optional[str] = None, limit: int = 20):
    """
    获取财经资讯
    - category: 分类筛选 (announcement/news/hot/all)
    - limit: 返回数量
    """
    all_news = []
    
    # 并行爬取多个源
    all_news.extend(crawl_eastmoney_news())
    all_news.extend(crawl_sina_finance())
    all_news.extend(crawl_ths_hot())
    all_news.extend(crawl_cls_telegram())
    
    # 按时间排序
    all_news.sort(key=lambda x: x.publishTime, reverse=True)
    
    # 分类筛选
    if category and category != 'all':
        category_map = {
            'announcement': '公告',
            'news': '财经要闻',
            'hot': '热点'
        }
        target = category_map.get(category)
        if target:
            all_news = [n for n in all_news if n.category == target]
    
    # 限制数量
    all_news = all_news[:limit]
    
    return NewsResponse(
        success=True,
        data=all_news,
        updateTime=datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    )

@app.get("/api/news/hot")
async def get_hot_news(limit: int = 10):
    """获取热点资讯"""
    hot_news = []
    hot_news.extend(crawl_ths_hot())
    hot_news.extend([n for n in crawl_cls_telegram() if n.hot])
    
    # 标记为热点
    for news in hot_news:
        news.hot = True
    
    return NewsResponse(
        success=True,
        data=hot_news[:limit],
        updateTime=datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    )

@app.get("/api/stock/realtime")
async def get_stock_realtime(codes: str):
    """
    获取股票实时数据
    - codes: 股票代码，多个用逗号分隔，如 sh000001,sz399001
    """
    try:
        code_list = codes.split(',')
        url = f"https://hq.sinajs.cn/list={','.join(code_list)}"
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Referer': 'https://finance.sina.com.cn/'
        }
        
        response = requests.get(url, headers=headers, timeout=10)
        text = response.text
        
        results = []
        lines = text.strip().split('\n')
        for line in lines:
            match = re.search(r'var hq_str_(\w+)="([^"]*)"', line)
            if match and match.group(2):
                fields = match.group(2).split(',')
                if len(fields) >= 33:
                    name = fields[0]
                    open_price = float(fields[1]) if fields[1] else 0
                    prev_close = float(fields[2]) if fields[2] else 0
                    current = float(fields[3]) if fields[3] else 0
                    high = float(fields[4]) if fields[4] else 0
                    low = float(fields[5]) if fields[5] else 0
                    volume = float(fields[8]) if fields[8] else 0
                    change = current - prev_close
                    change_percent = (change / prev_close * 100) if prev_close else 0
                    
                    results.append({
                        'code': match.group(1),
                        'name': name,
                        'price': round(current, 2),
                        'open': round(open_price, 2),
                        'high': round(high, 2),
                        'low': round(low, 2),
                        'prevClose': round(prev_close, 2),
                        'change': round(change, 2),
                        'changePercent': round(change_percent, 2),
                        'volume': volume
                    })
        
        return {
            'success': True,
            'data': results,
            'updateTime': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health_check():
    """健康检查"""
    return {"status": "ok", "time": datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
