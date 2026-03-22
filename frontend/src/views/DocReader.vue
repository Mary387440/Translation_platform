<template>
  <div class="page">
    <el-alert
      title="网络文学对照阅读与 AI 翻译请使用「书库」"
      type="info"
      show-icon
      style="margin-bottom: 16px"
    >
      <router-link to="/works">前往书库</router-link>
    </el-alert>
    <div class="page-header">
      <div>
        <h1 class="page-title">文档阅读器</h1>
        <p class="page-subtitle">用于上传的原始文档；书库作品请从侧栏「书库」进入。</p>
      </div>
      <div class="page-actions">
        <el-select size="small" placeholder="目标语种" style="width: 140px">
          <el-option label="中文（简体）" value="zh-CN" />
          <el-option label="英文" value="en" />
        </el-select>
        <el-select size="small" placeholder="翻译引擎" style="width: 150px">
          <el-option label="高质量引擎" value="hq" />
          <el-option label="快速引擎" value="fast" />
        </el-select>
        <el-button size="small" type="primary">整篇翻译</el-button>
      </div>
    </div>

    <div class="two-column">
      <el-card>
        <template #header>原文</template>
        <p style="color: #9ca3af; font-size: 13px">
          这里将按句/段落展示原文内容，可点击逐句翻译。
        </p>
      </el-card>
      <el-card>
        <template #header>译文与辅助</template>
        <p style="color: #9ca3af; font-size: 13px">
          这里将显示对应的译文、多候选结果和术语高亮。
        </p>
      </el-card>
    </div>
  </div>
</template>

