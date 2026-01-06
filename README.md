# 虎牙直播源 API

部署在 Vercel 上的虎牙直播源解析服务。

## 使用方法

```
https://你的域名.vercel.app/huya/房间号
```

例如：
```
https://huya-live-api.vercel.app/huya/660000
```

## M3U 直播源示例

```m3u
#EXTM3U
#EXTINF:-1,虎牙-LPL英雄联盟
https://你的域名.vercel.app/huya/660000
```

## 原理

1. 电视请求 `/huya/660000`
2. 服务器实时获取虎牙直播真实地址
3. 302 重定向到真实播放地址
4. 电视播放
