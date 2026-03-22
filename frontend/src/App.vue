<template>
  <el-container style="height: 100vh">
    <el-aside width="220px">
      <el-menu router default-active="/" :collapse="false">
        <el-menu-item index="/">
          <span>控制台</span>
        </el-menu-item>
        <el-menu-item index="/works">
          <span>书库</span>
        </el-menu-item>
        <el-menu-item index="/docs">
          <span>文档库</span>
        </el-menu-item>
        <el-menu-item index="/ocr">
          <span>场景 OCR</span>
        </el-menu-item>
        <el-menu-item index="/datasets">
          <span>数据集</span>
        </el-menu-item>
        <el-menu-item index="/glossary">
          <span>术语库</span>
        </el-menu-item>
        <el-menu-item index="/favorites">
          <span>收藏</span>
        </el-menu-item>
        <el-menu-item index="/settings">
          <span>设置</span>
        </el-menu-item>
      </el-menu>
    </el-aside>
    <el-container>
      <el-header height="56px">
        <div class="app-title">
          <span>SailoAI 文学出海</span>
          <span class="app-subtitle">多语种智能翻译阅读</span>
        </div>
        <div class="app-header-right">
          <el-select size="small" placeholder="界面语言" style="width: 120px">
            <el-option label="简体中文" value="zh-CN" />
            <el-option label="English" value="en-US" />
          </el-select>
          <el-avatar size="small">U</el-avatar>
        </div>
      </el-header>
      <el-main>
        <router-view />
      </el-main>
    </el-container>
  </el-container>
</template>

