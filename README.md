# ocs-desktop-bin

OCS Desktop（OCS 网课助手）的 **Arch Linux 非官方打包项目**。提供 `PKGBUILD` 和配套文件，构建时从上游获取发行包。当前实测版本为 **OCS Desktop 3.10.0**（`ocs-desktop-bin 3.10.0-1`），支持 **Arch Linux x86_64**。最新打包版本见 [`.SRCINFO`](.SRCINFO)。

因 AUR 暂停新账号注册，本项目暂在 GitHub 独立维护。后续如取得原 AUR 包的维护权限，再协调更新。原维护者 syhanjin 的提交和署名保留在 Git 历史及 `PKGBUILD` 中。

- [OCS Desktop 上游仓库](https://github.com/ocsjs/ocs-desktop)
- [OCS Desktop 官方 Releases](https://github.com/ocsjs/ocs-desktop/releases)
- [原 AUR 软件包 ocs-desktop-bin](https://aur.archlinux.org/packages/ocs-desktop-bin)

## 安装

安装构建工具后，以普通用户克隆并构建。安装阶段由 `makepkg` 调用 `pacman`。

```sh
sudo pacman -S --needed base-devel git
git clone https://github.com/steveyang137/ocs-desktop-bin.git
cd ocs-desktop-bin
makepkg --verifysource
makepkg -si
```

从应用菜单打开 **OCS Desktop**，或运行 `ocs-desktop`。首次启动会从包内 ZIP 初始化内置浏览器并重启应用。

## 更新与卸载

在克隆目录更新 Git 工作树并重新构建。若当前版本已安装，`makepkg` 提示已有构建产物时可直接跳过。

```sh
git pull --ff-only
makepkg -si
```

卸载软件包使用 `sudo pacman -R ocs-desktop-bin`。个人设置和浏览器配置位于 `${XDG_CONFIG_HOME:-$HOME/.config}/OCS Desktop/`，由用户自行备份和管理。

## 相比原 AUR 包的改进

- 使用官方 x86_64 AppImage 和上游锁定的 Chrome for Testing，校验每个源文件的 SHA-256。
- 构建时解包 AppImage，安装程序、命令、桌面入口和图标。构建和启动均无需 FUSE。
- Electron 与 Playwright 使用 user namespaces 保留 Chromium 沙箱。Linux 补丁也会迁移旧 AUR 包记录的内置浏览器路径。
- 首次启动在用户目录解压 Chrome，浏览器配置默认位于 `userDataDirs/`。应用更新由重新构建和安装软件包处理。

## 兼容性与已知问题

- 已在 Arch Linux x86_64 的 X11（Xvfb）和原生 Wayland（KWin 虚拟会话）验证 Electron 首次启动、内置 Chrome 初始化、Playwright 启动及本地导航页。两类会话的 Electron 和 Chrome 渲染进程均确认使用命名空间和 seccomp。
- 启动需要非特权 user namespaces。遇到 `No usable sandbox` 时，可用 `unshare -Ur true` 检查当前用户的命名空间支持。
- Chrome for Testing 目前固定为上游指定的 `137.0.7151.55`，用于保持命令行加载扩展的兼容性。这个版本已落后于当前 Chrome 安全更新，且不会自行更新。
- 智慧树登录和实际课程中的软件辅助流程尚未验证。可通过应用创建内置浏览器，在同一浏览器登录并检查脚本和软件辅助状态。

## 上游版本检查

[Check OCS Desktop releases](https://github.com/steveyang137/ocs-desktop-bin/actions/workflows/update-ocs-desktop.yml) 每天在 UTC 02:23（北京时间 10:23）运行，也可在 Actions 页面手动运行。手动运行默认会验证当前版本，便于重查构建状态。

发现新版时，工作流核对官方发行包的 SHA-256 和该标签锁定的 Chrome 版本与校验值，在 Arch 容器中检查包结构、应用补丁、构建并生成 `.SRCINFO`。校验或构建失败会标记为失败，并在运行日志中给出原因。验证通过后仅创建更新 PR，由维护者审阅及补做图形和平台测试。工作流使用 GitHub 的短期令牌，需要在仓库设置中启用 **Allow GitHub Actions to create and approve pull requests**。
