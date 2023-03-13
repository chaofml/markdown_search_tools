## 说明

基于python flask搭建的，简易的本地`markdown`文档搜索工具。也可以作为简易的代码搜索工具，支持常见的语法高亮。方便快速查找、复制代码。

没有数据库，但是，将文件缓存到db格式文件了。可以直接复制文件，然后，快速的将服务部署到其他位置，而不需要拷贝文章。

对于1000左右的范围的md文档，搜索快速。

### 安装

本代码无需安装，`git clone  仓库地址`,本地运行即可。

```shell
git clone xxxx

# 安装库
pip install markdown peewee flask

cd xxx

# 修改app.py几处 changeme!!!
# 需要先设置一下登录的的密码。 app.py  


# 定义 markdown 目录
<<EOL
paths = glob.glob('/mnt/e/gitee/md/**/*.md',recursive=True)
paths = paths + glob.glob('/mnt/e/gitee/zhuan/**/*.md',recursive=True) # 定义多个
EOL

python app.py

# 登录   登录地址故意搞复杂，而且不提示登录地址，这样麻烦，但更安全。
http://localhost:5023/hidden_login

```

## 技术

### 内容

大概涵盖了一些常用的flask知识点，jinja2知识点。

- flask get、post请求参数。
- path var 获取，使用。
- cookie session获取，顺道完成登录功能。（未使用成熟的flask-login)
- header获取
- 响应，render_templates,jsonfiy,send-from,redirect等等   应该研究一下响应，还可以设置响应的code

jinja2

- base 

即使小项目，也要验证按照成熟的目录来搭建，好处：1、省事，避免项目大的时候再拆分，麻烦。2、借助成熟方案，减少思考、不必要的麻烦。

蓝图，暂未使用。


### 部署

```shell
# 安装
pip install uwsgi -i https://mirrors.aliyun.com/pypi/simple/
# 配置  uwsgi文件  

# 启动
uwsgi --ini uwsgi.ini


```

增加nginx代理，避免直接暴露服务，保护内部接口。静态文件配置，暂时不需要。

```
 server {
        listen       33205;
        listen       [::]:33205;
        #server_name  xxxxx.cn;


        location / {
            proxy_set_header Host $http_host;
            proxy_set_header   X-Real-IP $remote_addr;
            proxy_set_header   X-Forwarded-For $proxy_add_x_forwarded_for;

            proxy_connect_timeout 30;
            proxy_send_timeout 60;
            proxy_read_timeout 60;

            proxy_buffering on;
            proxy_buffer_size 32k;
            proxy_buffers 4 128k;
            proxy_busy_buffers_size 256k;
            proxy_max_temp_file_size 256k;
            proxy_pass http://127.0.0.1:33204;
            proxy_redirect default;
        }
    }
```

### 增加ip记录

增加以下代码，来显示ip记录。从同目录的文件夹下引入，直接写的获取ip的脚本。

```python
from ip_location import get_ip_info

def show_ip():
    ip = request.headers.get('X-Forwarded-For')
    print('%s\t%s'%(ip,ip_addr(ip)))

@functools.lru_cache(100)
def ip_addr(ip):
    print('获取真实的ip：%s'%ip)
    return get_ip_info(ip)

def check_login(func):
    @functools.wraps(func)
    def wrapper(*args, **kw):
        #print('call %s():' % func.__name__)
        show_ip()
        if not session.get('user'):
            return 'error'
        return func(*args, **kw)
    return wrapper

```


## 关于Jinja2的一些小知识点

动态切换导航的active。好像不是特别好的思路。冗余代码较多。

其他想过的思路。
- 1、定义过滤器。（缺点1、定义的过滤器函数，内部无法获取到request.path值，None。缺点2、调用的时候，需要这样调用。{% 'current_path'|filter_is_active %}  
- 2、定义函数，注入到Jinja中。大概调用  {% is_filter(request.path,'/') %}
- 3、定义宏。

```
    <ul class="nav nav-tabs">
      <li role="presentation" {% if request.path == '/' %}class="active"{% endif %}><a href="/">首页</a></li>
      <li role="presentation" {% if request.path == '/category' %}class="active"{% endif %}><a href="/category">分类</a></li>
      <li role="presentation"><a href="/">其他</a></li>
    </ul>
```


定义宏。

```
{% macro nav_li(path,name) -%}
    <li role="presentation" {% if request.path == path %}class="active"{% endif %}><a href="{{ path }}">{{ name }}</a></li>
{%- endmacro -%}

    {{ nav_li('/','首页') }}
    {{ nav_li('/category','分类') }}
```


注册函数


```python
@app.template_global()
def sayhello(word='world') -> str:
    return 'hello %s'%word
```

```jinja2
<h1>{{ sayhello('scc') }}</h1>
```