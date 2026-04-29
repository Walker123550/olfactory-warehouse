# 开发环境约定

本项目后续以 WSL Ubuntu 里的仓库作为主工作区：

```bash
~/projects/olfactory-warehouse
```

Windows 目录 `C:\Users\swk\Documents\New project` 只作为历史副本，不再作为主要修改位置。

## 常用命令

运行应用：

```bash
cd ~/projects/olfactory-warehouse
PYTHONPATH=src python3 -m olfactory_warehouse
```

运行测试：

```bash
cd ~/projects/olfactory-warehouse
PYTHONPATH=src python3 -m unittest discover -s tests
```

同步远程 main：

```bash
cd ~/projects/olfactory-warehouse
git fetch origin main:refs/remotes/origin/main
git status --short --branch
```

## 数据库

WSL 主工作区默认数据库位置：

```bash
~/projects/olfactory-warehouse/data/olfactory_warehouse.sqlite3
```

该文件被 `.gitignore` 排除，不会提交到 GitHub。
