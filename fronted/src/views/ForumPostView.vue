<template>
  <div class="forum-page">
    <header class="forum-topbar">
      <div class="forum-topbar__identity">
        <button class="icon-button" title="返回论坛" @click="goBack">
          <el-icon><ArrowLeft /></el-icon>
        </button>
        <BrandMark />
        <span class="forum-topbar__divider" />
        <strong>帖子详情</strong>
      </div>
      <div class="forum-topbar__actions">
        <el-button plain round @click="openNotebooks">
          <el-icon><Notebook /></el-icon>
          学习笔记本
        </el-button>
        <UserMenu :user="currentUser" @logout="logout" />
      </div>
    </header>

    <main v-loading="loading" class="forum-detail-shell">
      <section v-if="post" class="forum-detail-main">
        <article class="forum-detail-card">
          <div class="forum-detail-card__meta">
            <el-tag effect="plain" round size="small">{{ post.category }}</el-tag>
            <span>{{ formatDate(post.created_at) }}</span>
          </div>
          <h1>{{ post.title }}</h1>
          <p class="forum-detail-card__content">{{ post.content }}</p>
          <footer class="forum-detail-card__footer">
            <div>
              <span class="forum-author">{{ post.username.slice(0, 1).toUpperCase() }}</span>
              <strong>{{ post.username }}</strong>
              <em>发布者</em>
            </div>
            <div class="forum-detail-card__actions">
              <span><el-icon><View /></el-icon>{{ post.view_count }}</span>
              <span><el-icon><ChatLineRound /></el-icon>{{ post.comment_count }}</span>
              <el-button
                v-if="isAuthor"
                :loading="deleting"
                plain
                round
                type="danger"
                @click="removePost"
              >
                <el-icon><Delete /></el-icon>
                删除帖子
              </el-button>
              <el-button :type="post.liked ? 'primary' : ''" plain round @click="toggleLike">
                <el-icon><Star /></el-icon>
                {{ post.liked ? "已点赞" : "点赞" }} {{ post.like_count }}
              </el-button>
            </div>
          </footer>
        </article>

        <section class="forum-comment-section">
          <div class="forum-comment-section__heading">
            <div>
              <p>COMMENTS</p>
              <h2>评论</h2>
            </div>
            <span>{{ comments.length }} 条评论</span>
          </div>

          <div class="forum-comment-composer">
            <el-input
              v-model="commentContent"
              :rows="3"
              maxlength="4000"
              placeholder="写下你的回复"
              type="textarea"
            />
            <div>
              <span>围绕学习主题展开交流</span>
              <el-button :loading="commenting" type="primary" round @click="submitComment">发表评论</el-button>
            </div>
          </div>

          <div class="forum-comment-list">
            <article v-for="item in comments" :key="item.id" class="forum-comment-card">
              <span class="forum-author">{{ item.username.slice(0, 1).toUpperCase() }}</span>
              <div>
                <strong>{{ item.username }}</strong>
                <em>{{ formatDate(item.created_at) }}</em>
                <p>{{ item.content }}</p>
              </div>
            </article>
            <div v-if="!comments.length" class="forum-empty forum-empty--compact">
              <strong>暂时还没有评论</strong>
              <p>你可以发布第一条回复。</p>
            </div>
          </div>
        </section>
      </section>
    </main>
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from "vue";
import { useRoute, useRouter } from "vue-router";
import { ArrowLeft, ChatLineRound, Delete, Notebook, Star, View } from "@element-plus/icons-vue";
import { ElMessage, ElMessageBox } from "element-plus";

import { getCurrentUser } from "../api/auth";
import { createForumComment, deleteForumPost, getForumPost, toggleForumPostLike } from "../api/forum";
import { getErrorMessage } from "../api/http";
import BrandMark from "../components/BrandMark.vue";
import UserMenu from "../components/UserMenu.vue";
import { clearToken } from "../utils/auth";

const route = useRoute();
const router = useRouter();
const currentUser = ref(null);
const post = ref(null);
const comments = ref([]);
const commentContent = ref("");
const loading = ref(false);
const commenting = ref(false);
const deleting = ref(false);

const postId = computed(() => Number(route.params.postId));
const isAuthor = computed(() => currentUser.value?.username === post.value?.username);

async function loadPage() {
  loading.value = true;
  try {
    const [userResult, postResult] = await Promise.all([
      getCurrentUser(),
      getForumPost(postId.value),
    ]);
    currentUser.value = userResult;
    post.value = postResult.post;
    comments.value = postResult.comments;
  } catch (error) {
    ElMessage.error(getErrorMessage(error));
  } finally {
    loading.value = false;
  }
}

async function submitComment() {
  if (!commentContent.value.trim() || commenting.value) {
    ElMessage.warning("请输入评论内容");
    return;
  }
  commenting.value = true;
  try {
    const result = await createForumComment(postId.value, {
      content: commentContent.value.trim(),
    });
    comments.value.push(result.comment);
    post.value.comment_count += 1;
    commentContent.value = "";
    ElMessage.success("评论已发布");
  } catch (error) {
    ElMessage.error(getErrorMessage(error));
  } finally {
    commenting.value = false;
  }
}

async function toggleLike() {
  try {
    const result = await toggleForumPostLike(postId.value);
    post.value.liked = result.liked;
    post.value.like_count = result.like_count;
  } catch (error) {
    ElMessage.error(getErrorMessage(error));
  }
}

async function removePost() {
  if (!isAuthor.value || deleting.value) {
    return;
  }
  try {
    await ElMessageBox.confirm(
      `确定删除帖子“${post.value.title}”吗？其中的评论和点赞都会一并删除。`,
      "删除帖子",
      {
        type: "warning",
        confirmButtonText: "删除",
        cancelButtonText: "取消",
      },
    );
  } catch {
    return;
  }

  deleting.value = true;
  try {
    await deleteForumPost(postId.value);
    ElMessage.success("帖子已删除");
    await goBack();
  } catch (error) {
    ElMessage.error(getErrorMessage(error));
  } finally {
    deleting.value = false;
  }
}

async function goBack() {
  window.close();
  if (!window.closed) {
    await router.push({
      name: "forum",
    });
  }
}

async function openNotebooks() {
  await router.push({
    name: "notebooks",
  });
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
