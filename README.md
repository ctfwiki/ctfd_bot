本仓库仅提供一个监听ctfd平台答题记录的demo

如非重大问题不再更新，不提供问询服务

代码逻辑参考了CTFd-Bot<sup>[2]</sup>，并针对特定平台（https://ctf.show）稍有修改和优化

## 环境配置

### ubunut升级python

```bash
sudo add-apt-repository ppa:jonathonf/python-3.7
sudo apt-get update
sudo apt-get install python3.7
python3 -V

# 更改默认值，python默认为Python2，现在修改为Python3（没试）
sudo update-alternatives --install /usr/bin/python python /usr/bin/python2 100
sudo update-alternatives --install /usr/bin/python python /usr/bin/python3 150
```

### python依赖

```bash
python3 -m pip install -r requirements.txt
```

### redis

```bash
docker run -d --rm --name redis -v /data/redis:/data \
    -p 6379:6379 redis:6.0.8-alpine --requirepass redis密码
```

## 启动

```bash
sudo python3 main.py &
```

如果不加sudo，退出shell后会停止，需要用其他用户挂起进程

## 参考链接

1. [ctfd-api-v1](https://github.com/CTFd/CTFd/blob/master/CTFd/api/__init__.py)
2. [CTFd-Bot](https://github.com/forever404/CTFd-Bot/blob/master/bot.py)
