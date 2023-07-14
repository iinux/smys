import logging
import multiprocessing
import threading
import time
import psutil
import os
import datetime

from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

rs_map = {

}

file_name = 'remote_socket_map.txt'
newest_version = multiprocessing.Value('i', 0)
version = 0


def put_to_map(s):
    if s is None or len(s) != 4:
        logging.error("error input %s", s)
        return
    src_host = s[0].decode()
    src_port = int(s[1])
    dst_host = s[2].decode()
    dst_port = int(s[3])
    k = rs_map.get(src_host)
    if k is None:
        rs_map[src_host] = {}
    rs_map[src_host][src_port] = (dst_host, dst_port)


def get_from_map(host, port):
    if isinstance(host, bytes):
        host = host.decode()
    global version
    if newest_version.value > version:
        load_config()
        version = newest_version.value
    k = rs_map.get(host)
    if k is None:
        return None
    v = k.get(port)

    return v


def load_config():
    try:
        with open(file_name, 'rb') as f:
            lines = f.readlines()

            rs_map.clear()
            for line in lines:
                put_to_map(line.strip().split(b' '))
            logging.debug(rs_map)

    except FileNotFoundError:
        pass


def print_var(v):
    t = threading.currentThread()
    print('Thread %d(%s), var %d' % (t.ident, t.getName(), id(v)))


def log_var(v):
    t = threading.currentThread()
    logging.debug('Thread %d(%s), var %d' % (t.ident, t.getName(), id(v)))


def process_show():
    pid = os.getpid()
    p = psutil.Process(pid)
    print('Process id: %d' % pid)
    print('Process name: %s' % p.name())
    print('Process bin path: %s' % p.exe())
    print('Process path: %s' % p.cwd())
    print('Process status: %s' % p.status())
    print('Process creation time: %s' % datetime.datetime.fromtimestamp(p.create_time()).strftime("%Y-%m-%d %H:%M:%S"))
    print(p.cpu_times())
    print('Memory usage: %s%%' % p.memory_percent())
    print(p.io_counters())
    print(p.connections())
    print('Process number of threads: %s' % p.num_threads())


class MapConfigWatch(FileSystemEventHandler):

    def __init__(self):
        self.observer = None

    def on_modified(self, event):
        if not event.is_directory:
            if event.src_path.endswith('/' + file_name):
                logging.info(f"File {event.src_path} was modified")
                newest_version.value = int(time.time())

    def start(self):
        newest_version.value = int(time.time())
        # 创建一个观察者对象并指定要监视的目录
        self.observer = Observer()
        path = '.'  # 要监视的目录路径
        self.observer.schedule(MapConfigWatch(), path, recursive=True)
        # 启动观察者
        self.observer.start()

    def stop(self):
        self.observer.stop()
        # 等待观察者完成处理并释放资源
        self.observer.join()
