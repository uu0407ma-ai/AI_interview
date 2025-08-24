# FFmpeg 的安装步骤：


# 在 Windows 上安装 FFmpeg

以下是在 Windows 系统上安装 FFmpeg 的简要步骤：

## 步骤

1. **下载 FFmpeg**：
   - 访问 [FFmpeg 官网](https://ffmpeg.org/download.html) 或可信来源，如 [gyan.dev](https://www.gyan.dev/ffmpeg/builds/)。
   - 下载最新的 Windows 稳定版本（如 `ffmpeg-release-full.7z`）。

2. **解压文件**：
   - 使用 7-Zip 或 WinRAR 解压下载的压缩包。
   - 将解压后的文件夹放置到方便的位置，如 `C:\ffmpeg`。

3. **添加 FFmpeg 到系统路径**：
   - 按 `Win + S`，搜索“环境变量”，选择 **编辑系统环境变量** 或 **编辑账户环境变量**。
   - 在弹出的窗口中，点击 **环境变量**。
   - 在 **系统变量**（或用户变量）中，找到 **Path**，点击 **编辑**。
   - 点击 **新建**，添加 FFmpeg 的 `bin` 目录路径（如 `C:\ffmpeg\bin`）。
   - 点击 **确定** 保存所有更改。

4. **检测安装**：
   - 按 `Win + R`，输入 `cmd` 打开命令提示符。
   - 输入 `ffmpeg -version` 并按回车。
   - 如果安装成功，将显示 FFmpeg 的版本信息。

## 提示
- 如果遇到问题，确保下载的 FFmpeg 文件与 Windows 系统兼容（32位或64位）。
- 如需进一步帮助，可联系支持或查阅 FFmpeg 官方文档。



# Mac上安装

brew install ffmpeg