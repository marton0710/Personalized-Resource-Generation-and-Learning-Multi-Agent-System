<template>
  <div class="notebook-home">
    <header class="notebook-home__header">
      <BrandMark />
      <div class="notebook-home__actions">
        <el-button type="primary" round @click="openForum">
          <el-icon><ChatDotRound /></el-icon>
          学习论坛
        </el-button>
        <UserMenu :user="currentUser" @logout="logout" />
      </div>
    </header>

    <main class="notebook-home__main">
      <section class="notebook-home__hero">
        <div>
          <p>PERSONALIZED LEARNING NOTEBOOKS</p>
          <h1>从一个主题开始，<br /><span>让多智能体协作陪你学下去。</span></h1>
        </div>
        <p class="notebook-home__description">
          每个笔记本围绕一门课程或一个知识主题展开。中央对话会持续更新学习画像，右侧 Studio
          可以按需生成路径、讲解、导图、测验和实操内容。
        </p>
      </section>

      <section class="notebook-section">
        <div class="notebook-section__heading">
          <div>
            <p>YOUR NOTEBOOKS</p>
            <h2>学习笔记本</h2>
          </div>
          <span>{{ notebooks.length }} 个笔记本</span>
        </div>

        <div v-loading="loading" class="notebook-grid">
          <button class="notebook-card notebook-card--create" @click="createDialogVisible = true">
            <span><el-icon><Plus /></el-icon></span>
            <strong>创建新笔记本</strong>
            <em>选择一个课程或知识主题开始学习</em>
          </button>

          <div
            v-for="item in notebooks"
            :key="item.id"
            class="notebook-card-shell"
          >
            <button class="notebook-card" @click="openNotebook(item.id)">
              <span class="notebook-card__icon"><el-icon><Notebook /></el-icon></span>
              <strong>{{ item.title }}</strong>
              <em>{{ item.description || "围绕这个主题开始对话和生成学习资源" }}</em>
              <small>{{ formatDate(item.updated_at) }} 更新</small>
            </button>
            <button
              class="notebook-card__delete"
              :disabled="deletingNotebookId === item.id"
              title="删除笔记本"
              @click.stop="removeNotebook(item)"
            >
              <el-icon><Delete /></el-icon>
            </button>
          </div>
        </div>
      </section>
    </main>

    <el-dialog v-model="createDialogVisible" title="创建学习笔记本" width="min(92vw, 520px)">
      <el-form label-position="top">
        <el-form-item label="笔记本标题">
          <el-input v-model="createForm.title" maxlength="256" placeholder="例如：Python 数据分析基础" />
        </el-form-item>
        <el-form-item label="学习说明">
          <el-input
            v-model="createForm.description"
            :rows="3"
            maxlength="2000"
            placeholder="可选：写下课程范围、当前目标或学习场景"
            type="textarea"
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="createDialogVisible = false">取消</el-button>
        <el-button :loading="creating" type="primary" @click="submitCreate">创建并进入</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { onMounted, reactive, ref } from "vue";
import { useRouter } from "vue-router";
import { ChatDotRound, Delete, Notebook, Plus } from "@element-plus/icons-vue";
import { ElMessage, ElMessageBox } from "element-plus";

import { getCurrentUser } from "../api/auth";
import { getErrorMessage } from "../api/http";
import { createNotebook, deleteNotebook, listNotebooks } from "../api/notebook";
import BrandMark from "../components/BrandMark.vue";
import UserMenu from "../components/UserMenu.vue";
import { clearToken } from "../utils/auth";
import { clearNotebookQuizProgress } from "../utils/quizProgressStorage";

const router = useRouter();
const currentUser = ref(null);
const notebooks = ref([]);
const loading = ref(false);
const creating = ref(false);
const deletingNotebookId = ref(null);
const createDialogVisible = ref(false);
const createForm = reactive({
  title: "",
  description: "",
});

async function loadPage() {
  loading.value = true;
  try {
    const [userResult, notebookResult] = await Promise.all([
      getCurrentUser(),
      listNotebooks(),
    ]);
    currentUser.value = userResult;
    notebooks.value = notebookResult.notebooks;
  } catch (error) {
    ElMessage.error(getErrorMessage(error));
  } finally {
    loading.value = false;
  }
}

async function submitCreate() {
  if (!createForm.title.trim() || creating.value) {
    ElMessage.warning("请输入笔记本标题");
    return;
  }
  creating.value = true;
  try {
    const result = await createNotebook({
      title: createForm.title.trim(),
      description: createForm.description.trim(),
    });
    await openNotebook(result.notebook.id);
  } catch (error) {
    ElMessage.error(getErrorMessage(error));
  } finally {
    creating.value = false;
  }
}

async function openNotebook(id) {
  await router.push({
    name: "notebook",
    params: {
      notebookId: id,
    },
  });
}

async function openForum() {
  await router.push({
    name: "forum",
  });
}

async function removeNotebook(item) {
  if (deletingNotebookId.value) {
    return;
  }
  try {
    await ElMessageBox.confirm(
      `确定删除笔记本“${item.title}”吗？其中的对话、Studio 产物和笔记都会一并删除。`,
      "删除学习笔记本",
      {
        type: "warning",
        confirmButtonText: "删除",
        cancelButtonText: "取消",
      },
    );
  } catch {
    return;
  }

  deletingNotebookId.value = item.id;
  try {
    await deleteNotebook(item.id);
    clearNotebookQuizProgress(item.id);
    notebooks.value = notebooks.value.filter((notebook) => notebook.id !== item.id);
    ElMessage.success("笔记本已删除");
  } catch (error) {
    ElMessage.error(getErrorMessage(error));
  } finally {
    deletingNotebookId.value = null;
  }
}

async function logout() {
  clearToken();
  await router.push({
    name: "login",
  });
}

function formatDate(value) {
  return value ? new Date(value).toLocaleDateString("zh-CN") : "刚刚";
}

onMounted(loadPage);
</script>
