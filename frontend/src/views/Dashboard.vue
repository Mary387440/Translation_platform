<template>
  <div class="page">
    <div class="page-header">
      <div>
        <h1 class="page-title">控制台</h1>
        <p class="page-subtitle">总览你的文档、翻译进度与使用情况。</p>
      </div>
      <div class="page-actions">
        <el-button type="primary">上传新文档</el-button>
        <el-button>进入文档库</el-button>
      </div>
    </div>

    <div class="card-grid">
      <el-card>
        <template #header>最近阅读</template>
        <p>这里将展示最近打开的 3～5 篇文档。</p>
      </el-card>
      <el-card>
        <template #header>翻译任务</template>
        <p>这里将展示进行中的全文翻译任务进度。</p>
      </el-card>
      <el-card>
        <template #header>用量概览</template>
        <p>这里可以放近 7 天的调用次数 / 字数统计。</p>
      </el-card>
    </div>
  </div>
</template>

