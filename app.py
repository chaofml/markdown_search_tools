import os
from flask import Flask, jsonify, redirect,render_template, request,session, url_for
import glob
import markdown
import pickle
import functools

app = Flask(__name__)
# 以下几处需要 changeme!!!   设置。
app.secret_key = 'changeme!!!'
paths = []
articles = {}
# todo 按时间等等排序


# 因为作用域问题，需要先定义，否则后面的函数，会提示找不到check_login变量
def check_login(func):
    @functools.wraps(func)
    def wrapper(*args, **kw):
        #print('call %s():' % func.__name__)
        if not session.get('user'):
            return 'error'
        return func(*args, **kw)
    return wrapper

@app.route('/')
@check_login
def index():
    cat = request.args.get('category','').strip()
    if cat:
        return render_template("list.html",paths = [x for x in paths if x.startswith(cat)] )
    return render_template("list.html",paths = paths)

@app.route('/category')
def category():
    result = list(set([ os.path.dirname(x) for x in paths])) # 去重 + 排序
    result.sort()
    return render_template("category.html",paths = result)

@app.route('/hidden_login',methods=['GET','POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        if username == 'changeme!!!' and password == 'changeme!!!':
            session['user'] = 'admin'
            return redirect('/')
        else:
            return 'login error'
    return render_template('login.html')

@app.route('/logout')
@check_login
def login_out():
    session.clear()
    #del session['user']
    return 'ok'

@app.route('/search')
@check_login
def search():
    result = []
    words = request.args.get('words','').strip()
    if not words :
        return 'no search words'
    idx = request.args.get('idx','').strip()
    new_idxs = set() 
    art = { paths[x]:articles.get(paths[x],'')  for x in map(lambda x:int(x),idx.split('-')) } if idx else articles
    w = [x.strip() for x in words.split(' ') if x.strip() ]
    for path,article in art.items():
        for line in article:
            if string_search(line,w):
                new_idxs.add("%s"%get_path_id(path))
                result.append({"path":path,"content":line })
    return render_template("search.html",items = result,idx = '-'.join(list(new_idxs)))

@app.route('/md/old')
@check_login
def read_markdown_old():
    filename = request.args.get('file','')
    if not filename or not filename.endswith('.md') or not os.path.exists(filename):
        return 'file not found'
    text = ''
    try:
        with open(filename,'r',encoding='utf-8') as fi:
            text = ''.join(fi.readlines())
    except UnicodeDecodeError:
        with open('upload/%s'%filename,'r',encoding='gbk') as fi:
            text = ''.join(fi.readlines())
    content = markdown.markdown(text,
         extensions=[
          'markdown.extensions.extra',
          'markdown.extensions.codehilite',
          'markdown.extensions.toc',
      ])
    return render_template("md.html",content=content,title = filename)

@app.route('/md')
@check_login
def read_markdown():
    filename = request.args.get('file','')
    lines = articles.get(filename,'')
    if not lines:
        return 'file not found'
    text = ''.join(lines)
    _,ext = os.path.splitext(filename)
    ext = ext[1:] if len(ext) > 1 else '' # 防止有不存在扩展名的文件
    if ext.lower() == 'md' :
        content = markdown.markdown(text, extensions=[
              'markdown.extensions.extra',
              'markdown.extensions.codehilite',
              'markdown.extensions.toc',
              #'markdown.extensions.meta',
          ])
    else:
        content = text
    return render_template("md.html",content=content,title = filename,ext = ext )

@app.get('/remove/db')
@check_login
def del_db():
    os.remove('db')
    return 'ok'

@app.get('/flush/db')
@check_login
def flush_db():
    global articles
    articles = {}
    os.remove('db')
    init()
    return 'flush ok'

def safe_open(filename):
    lines = []
    try:
        with open(filename,'r',encoding='utf-8') as fi:
            lines = fi.readlines()
    except UnicodeDecodeError:
        with open('upload/%s'%filename,'r',encoding='gbk') as fi:
            lines = fi.readlines()
    return lines

def string_search(line:str,words:list):
    for word in words:
        if line.find(word) < 0:
            return False
    return True

@app.template_filter('obsidian_url')
def obsidian_url(href:str):
    paths,_ = os.path.splitext(href)
    find_idx = href.find('zhuan')
    if find_idx >=0 :
        offset = len('zhuan') + 1
        return ['zhuan',paths[find_idx + offset:]]
    find_idx = href.find('md')
    if find_idx >=0 :
        offset = len('md') + 1
        return ['md',paths[find_idx + offset:]]

@app.template_filter('breadcrumb')
def breadcrumb(href:str):
    cur = []
    result  = []
    for i in href.split('/'):
        cur.append(i)
        result.append({'name':i,'value':'/'.join(cur)})
    return result

@app.template_global()
def sayhello(word='world') -> str:
    return 'hello %s'%word

@functools.lru_cache(100)
def get_path_id(path:str) -> int:
    return paths.index(path)    
 
def init(reflush = False ):
    global paths,articles
    if os.path.exists('db') and not reflush: # cache
        print('use cache')
        with open('db','rb') as fi:
            articles = pickle.load(fi)
        paths = list(articles.keys())
    else:    # disk
        print('read all articles form disk')
        # 定义 加载的内容
        paths = glob.glob('E:/gitee/md/**/*.md',recursive=True)

        for path in paths:
            articles[path] = safe_open(path)
        with open('db','wb') as fo:
            pickle.dump(articles,fo)

if __name__ == '__main__':
    init()
    app.debug = True
    app.run(port=5023)
