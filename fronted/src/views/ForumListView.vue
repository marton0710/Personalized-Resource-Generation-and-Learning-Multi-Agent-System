<template>
  <div class="forum-page">
    <header class="forum-topbar">
      <div class="forum-topbar__identity">
        <BrandMark />
        <span class="forum-topbar__divider" />
        <strong>学习论坛</strong>
      </div>
      <div class="forum-topbar__actions">
        <el-button plain round @click="openNotebooks">
          <el-icon><Notebook /></el-icon>
          学习笔记本
        </el-button>
        <el-button type="primary" round @click="createDialogVisible = true">
          <el-icon><EditPen /></el-icon>
          发布帖子
        </el-button>
        <UserMenu :user="currentUser" @logout="logout" />
      </div>
    </header>

    <main class="forum-shell">
      <section class="forum-hero">
        <div>
          <p>LEARNING COMMUNITY</p>
          <h1>学习论坛</h1>
          <span>分享学习过程中的思考、经验和问题，与其他学习者一起交流。</span>
        </div>
        <div class="forum-hero__decoration">
          <el-icon><ChatDotRound /></el-icon>
        </div>
      </section>

      <div class="forum-layout">
        <section class="forum-feed">
          <div class="forum-toolbar">
            <el-input
              v-model="keyword"
              clearable
              placeholder="搜索帖子"
              @clear="loadPosts"
              @keyup.enter="loadPosts"
            >
              <template #prefix><el-icon><Search /></el-icon></template>
            </el-input>
            <el-select v-model="category" placeholder="全部分区" @change="loadPosts">
              <el-option label="全部分区" value="" />
              <el-option v-for="item in categories" :key="item" :label="item" :value="item" />
            </el-select>
            <el-checkbox v-model="mineOnly">只看我的</el-checkbox>
          </div>

          <div class="forum-feed__heading">
            <div>
              <p>DISCUSSIONS</p>
              <h2>交流广场</h2>
            </div>
            <span>{{ visiblePosts.length }} 条帖子</span>
          </div>

          <div v-loading="loading" class="forum-post-list">
            <button
              v-for="item in visiblePosts"
              :key="item.id"
              class="forum-post-card"
              @click="openPost(item.id)"
            >
              <div class="forum-post-card__heading">
                <el-tag effect="plain" round size="small">{{ item.category }}</el-tag>
                <span>{{ formatDate(item.created_at) }}</span>
              </div>
              <strong>{{ item.title }}</strong>
              <p>{{ item.content }}</p>
              <div class="forum-post-card__footer">
                <span class="forum-author">{{ item.username.slice(0, 1).toUpperCase() }}</span>
                <em>{{ item.username }}</em>
                <span><el-icon><View /></el-icon>{{ item.view_count }}</span>
                <span><el-icon><ChatLineRound /></el-icon>{{ item.comment_count }}</span>
                <span :class="{ 'forum-post-card__liked': item.liked }">
                  <el-icon><Star /></el-icon>{{ item.like_count }}
                </span>
              </div>
            </button>
            <div v-if="!loading && !visiblePosts.length" class="forum-empty">
              <el-icon :size="28"><ChatDotRound /></el-icon>
              <strong>还没有匹配的帖子</strong>
              <p>发布一条帖子，开启第一次交流。</p>
            </div>
          </div>
        </section>

        <aside class="forum-sidebar">
          <section>
            <p>COMMUNITY GUIDE</p>
            <h3>交流建议</h3>
            <ul>
              <li>明确描述你的问题和当前思路。</li>
              <li>分享对其他学习者有帮助的经验。</li>
              <li>围绕学习主题展开友善交流。</li>
            </ul>
          </section>
          <section>
            <p>TOPICS</p>
            <h3>讨论分区</h3>
            <button v-for="item in categories" :key="item" @click="selectCategory(item)">
              <span>{{ item }}</span>
              <el-icon><ArrowRight /></el-icon>
            </button>
          </section>
        </aside>
      </div>
    </main>

    <el-dialog v-model="createDialogVisible" title="发布帖子" width="min(92vw, 620px)">
      <el-form label-position="top">
        <el-form-item label="标题">
          <el-input v-model="createForm.title" maxlength="256" placeholder="简要说明你想交流的话题" />
        </el-form-item>
        <el-form-item label="分区">
          <el-select v-model="createForm.category">
            <el-option v-for="item in categories" :key="item" :label="item" :value="item" />
          </el-select>
        </el-form-item>
        <el-form-item label="正文">
          <el-input
            v-model="createForm.content"
            :rows="7"
            maxlength="20000"
            placeholder="写下你的问题、想法或学习经验"
            type="textarea"
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="createDialogVisible = false">取消</el-button>
        <el-button :loading="creating" type="primary" @click="submitCreate">发布并查看</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { computed, onMounted, reactive, ref } from "vue";
import { useRouter } from "vue-router";
import {
  ArrowRight,
  ChatDotRound,
  ChatLineRound,
  EditPen,
  Notebook,
  Search,
  Star,
  View,
} from "@element-plus/icons-vue";
import { ElMessage } from "element-plus";

import { getCurrentUser } from "../api/auth";
import { createForumPost, listForumPosts } from "../api/forum";
import { getErrorMessage } from "../api/http";
import BrandMark from "../components/BrandMark.vue";
import UserMenu from "../components/UserMenu.vue";
import { clearToken } from "../utils/auth";

const router = useRouter();
const categories = ["交流讨论", "学习求助", "经验分享", "资源推荐"];
const currentUser = ref(null);
const posts = ref([]);
const keyword = ref("");
const category = ref("");
const mineOnly = ref(false);
const loading = ref(false);
const creating = ref(false);
const createDialogVisible = ref(false);
const createForm = reactive({
  title: "",
  content: "",
  category: categories[0],
});

const visiblePosts = computed(() => {
  if (!mineOnly.value) {
    return posts.value;
  }
  return posts.value.filter((item) => item.username === currentUser.value?.username);
});

async function loadPage() {
  try {
    currentUser.value = await getCurrentUser();
    await loadPosts();
  } catch (error) {
    ElMessage.error(getErrorMessage(error));
  }
}

async function loadPosts() {
  loading.value = true;
  try {
    const result = await listForumPosts({
      keyword: keyword.value.trim(),
      category: category.value,
    });
    posts.value = result.posts;
  } catch (error) {
    ElMessage.error(getErrorMessage(error));
  } finally {
    loading.value = false;
  }
}

async function submitCreate() {
  if (!createForm.title.trim() || !createForm.content.trim() || creating.value) {
    ElMessage.warning("请填写帖子标题和正文");
    return;
  }
  const detailWindow = window.open("", "_blank");
  if (detailWindow) {
    detailWindow.opener = null;
  }
  creating.value = true;
  try {
    const result = await createForumPost({
      title: createForm.title.trim(),
      content: createForm.content.trim(),
      category: createForm.category,
    });
    createDialogVisible.value = false;
    createForm.title = "";
    createForm.content = "";
    createForm.category = categories[0];
    openPost(result.post.id, detailWindow);
  } catch (error) {
    detailWindow?.close();
    ElMessage.error(getErrorMessage(error));
  } finally {
    creating.value = false;
  }
}

function openPost(id, detailWindow = null) {
  const url = router.resolve({
    name: "forum-post",
    params: {
      postId: id,
    },
  }).href;
  if (detailWindow && !detailWindow.closed) {
    detailWindow.location.href = url;
    return;
  }
  window.open(url, "_blank", "noopener");
}

async function openNotebooks() {
  await router.push({
    name: "notebooks",
  });
}

async function selectCategory(value) {
  category.value = value;
  await loadPosts();
}

async function logout() {
  clearToken();
  await router.push({
    name: "login",
  });
}

function formatDate(value) {
  return value ? new Date(value).toLocaleString("zh-CN") : "刚刚";
}

onMounted(loadPage);
</script>
