<template>
  <div class="auth-shell">
    <section class="auth-shell__intro">
      <BrandMark />

      <div class="auth-shell__content">
        <el-tag effect="plain" round>至道 · 多智能体学习系统</el-tag>
        <h1>让每一次学习，<br /><span>都有清晰的下一步。</span></h1>
        <p>
          在学习笔记本中自然对话，持续更新个人画像，并按需生成真正贴合你的学习路径和多模态资源。
        </p>
      </div>

      <div class="auth-shell__features">
        <div v-for="item in features" :key="item.title" class="intro-feature">
          <el-icon :size="18">
            <component :is="item.icon" />
          </el-icon>
          <div>
            <strong>{{ item.title }}</strong>
            <span>{{ item.description }}</span>
          </div>
        </div>
      </div>
    </section>

    <section class="auth-shell__form">
      <div class="auth-form-card">
        <slot />
      </div>
    </section>
  </div>
</template>

<script setup>
import { ChatDotRound, Collection, TrendCharts } from "@element-plus/icons-vue";

import BrandMark from "./BrandMark.vue";

const features = [
  {
    icon: ChatDotRound,
    title: "对话式画像",
    description: "告别繁琐表单，自然交流中理解你的需求",
  },
  {
    icon: TrendCharts,
    title: "动态学习路径",
    description: "围绕当前目标，规划由浅入深的学习顺序",
  },
  {
    icon: Collection,
    title: "Studio 按需生成",
    description: "路径、讲解、导图、习题、阅读与代码实操",
  },
];
</script>
