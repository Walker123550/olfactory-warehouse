# WSL 环境说明

## 结论

闻香程序没有丢。它最早创建在 Windows 文件系统：

```text
C:\Users\swk\Documents\New project
```

在 WSL Ubuntu 里，这个路径会以挂载目录形式出现：

```bash
/mnt/c/Users/swk/Documents/New\ project
```

Windows 文件不会自动复制到 WSL 的 Linux home 目录，所以在 `~/projects` 或 `~` 下面找不到原项目是正常现象。

## 当前 WSL 项目位置

已经把 GitHub 仓库克隆到 WSL 原生目录：

```bash
~/projects/olfactory-warehouse
```

推荐以后在 WSL 中使用这个目录开发和运行，因为它是 Linux 文件系统，权限、性能和 Git 行为都更稳定。

## 在 WSL 中运行

```bash
cd ~/projects/olfactory-warehouse
PYTHONPATH=src python3 -m olfactory_warehouse
```

浏览器打开：

```text
http://127.0.0.1:8765
```

## 在 WSL 中测试

```bash
cd ~/projects/olfactory-warehouse
PYTHONPATH=src python3 -m unittest discover -s tests
```

排查时已经验证：5 个单元测试全部通过。

## 数据库位置差异

如果从 Windows 原目录运行，默认数据库是：

```text
C:\Users\swk\Documents\New project\data\olfactory_warehouse.sqlite3
```

如果从 WSL 原生目录运行，默认数据库是：

```bash
~/projects/olfactory-warehouse/data/olfactory_warehouse.sqlite3
```

这两个数据库不是同一个文件。也就是说，在 Windows 版本录入的数据，不会自动出现在 WSL 原生目录的数据库里。

## 使用 Windows 那份数据库

如果希望 WSL 程序继续使用 Windows 那份数据库，可以指定环境变量：

```bash
cd ~/projects/olfactory-warehouse
export OLFACTORY_DB_PATH="/mnt/c/Users/swk/Documents/New project/data/olfactory_warehouse.sqlite3"
PYTHONPATH=src python3 -m olfactory_warehouse
```

## 推荐做法

长期建议固定一种运行位置：

- 如果主要在 WSL 开发：使用 `~/projects/olfactory-warehouse`，数据也留在 WSL。
- 如果主要在 Windows 使用：继续使用 `C:\Users\swk\Documents\New project`。
- 不建议两边频繁切换同一个 SQLite 文件，避免路径混乱和文件锁问题。

## WSL 提示说明

执行 WSL 命令时可能看到类似提示：

```text
A localhost proxy configuration was detected but not mirrored into WSL.
```

这是 WSL NAT 模式下的代理提示，不是闻香程序缺失的原因。当前项目代码、Git、Python 和测试都可以正常使用。
