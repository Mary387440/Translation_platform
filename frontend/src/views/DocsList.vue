<template>
  <div class="page">
    <div class="page-header">
      <div>
        <h1 class="page-title">文档库</h1>
        <p class="page-subtitle">管理和搜索你上传的小语种文档。</p>
      </div>
      <div class="page-actions">
        <el-button type="primary">上传文档</el-button>
      </div>
    </div>

    <el-card>
      <div style="display: flex; justify-content: space-between; margin-bottom: 16px; gap: 12px; flex-wrap: wrap">
        <el-input placeholder="搜索标题或关键词" style="max-width: 260px" />
        <div style="display: flex; gap: 8px">
          <el-select placeholder="原文语种" style="width: 140px">
            <el-option label="全部" value="" />
            <el-option label="日语" value="ja" />
            <el-option label="韩语" value="ko" />
            <el-option label="西班牙语" value="es" />
          </el-select>
          <el-select placeholder="状态" style="width: 140px">
            <el-option label="全部" value="" />
            <el-option label="已解析" value="ready" />
            <el-option label="翻译中" value="translating" />
          </el-select>
        </div>
      </div>

      <el-table :data="[]" size="small">
        <el-table-column prop="title" label="标题" />
        <el-table-column prop="srcLang" label="原文语种" width="120" />
        <el-table-column prop="createdAt" label="上传时间" width="180" />
        <el-table-column prop="status" label="状态" width="120" />
        <el-table-column label="操作" width="160" />
      </el-table>

      <div style="margin-top: 12px; text-align: center; color: #9ca3af; font-size: 13px">
        暂无数据，后端接入后将展示真实文档列表。
      </div>
    </el-card>
  </div>
</template>

