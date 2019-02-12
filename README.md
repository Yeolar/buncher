bunder
======

基于cmake的打包和部署工具。

配置
----

在 `~` 下配置.bunder.yml：

    arch: amd64

    source:
        host: 'USER@HOST'
        path: 'PACK_ROOT'

在当前工程目录下配置.bunder.yml，以某一版本的raster为例：

    project:
        raster

    build:
        path: './build'

    depend:
        - accelerator-1.2.4
        - flatbuffers-1.9.0

使用方法
--------

编译：

```
  -g [toolchain], --gen [toolchain]     生成编译环境
  -b [job], --build [job]               编译
  -c, --clean                           清理编译临时目录
```

打包：

```
  -p [pkg ...], --pack [pkg ...]        打包到远程主机
  -l, --list                            列出在远程主机的包
```

依赖：

```
  -i [dep ...], --dep-install [dep ...] 安装依赖
  -d [dep ...], --dep-delete [dep ...]  清理依赖
```
