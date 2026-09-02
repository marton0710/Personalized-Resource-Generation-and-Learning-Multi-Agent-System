<template>
  <div ref="contentElement" class="markdown-content" v-html="renderedContent" />
</template>

<script setup>
import { computed, nextTick, onMounted, ref, watch } from "vue";
import MarkdownIt from "markdown-it";

const props = defineProps({
  content: {
    type: String,
    default: "",
  },
  renderDiagrams: {
    type: Boolean,
    default: true,
  },
});

const contentElement = ref(null);
const markdown = new MarkdownIt({
  breaks: true,
  html: false,
  linkify: true,
  typographer: true,
});

let mermaidInstance = null;

/**
 * 移除大模型偶尔附加的整篇Markdown代码围栏。
 * @param {string} content Markdown内容
 * @returns {string} 可直接渲染的Markdown内容
 */
function normalizeMarkdown(content) {
  const openingFence = /^```(?:markdown|md)\s*\n/i;

  if (!openingFence.test(content)) {
    return content;
  }

  let normalized = content.replace(openingFence, "");
  const fences = normalized.match(/^```/gm) || [];

  if (fences.length % 2 === 1) {
    normalized = normalized.replace(/\n```[ \t]*$/, "");
  }

  return normalized;
}

const renderedContent = computed(() => markdown.render(normalizeMarkdown(props.content)));

async function renderMermaid() {
  await nextTick();

  if (!props.renderDiagrams || !contentElement.value) {
    return;
  }

  const blocks = contentElement.value.querySelectorAll("code.language-mermaid");

  if (!blocks.length) {
    return;
  }

  if (!mermaidInstance) {
    const module = await import("mermaid");
    mermaidInstance = module.default;
    mermaidInstance.initialize({
      startOnLoad: false,
      securityLevel: "strict",
      theme: "neutral",
    });
  }

  for (const [index, block] of blocks.entries()) {
    const pre = block.parentElement;
    const graph = block.textContent;
    const container = document.createElement("div");
    container.className = "mermaid-diagram";

    try {
      const { svg } = await mermaidInstance.render(`mermaid-${Date.now()}-${index}`, graph);
      container.innerHTML = svg;
      pre.replaceWith(container);
    } catch {
      container.textContent = graph;
      pre.replaceWith(container);
    }
  }
}

watch(
  () => [props.content, props.renderDiagrams],
  renderMermaid,
);

onMounted(renderMermaid);
</script>
