<template>
  <div class="notebook-workspace">
    <header class="notebook-topbar">
      <div class="notebook-topbar__identity">
        <button class="icon-button" title="返回笔记本列表" @click="goBack">
          <el-icon><ArrowLeft /></el-icon>
        </button>
        <BrandMark />
        <span class="notebook-topbar__divider" />
        <strong>{{ notebook?.title || "学习笔记本" }}</strong>
      </div>
      <div class="notebook-topbar__actions">
        <el-popover placement="bottom-end" trigger="click" width="320">
          <template #reference>
            <el-button plain round>
              <el-icon><User /></el-icon>
              学习画像
            </el-button>
          </template>
          <div class="profile-popover">
            <strong>动态学习画像</strong>
            <p v-if="!profile">在中央对话中介绍你的专业、目标和学习情况，画像智能体会持续完善档案。</p>
            <dl v-else>
              <dt>专业</dt><dd>{{ profile.major }}</dd>
              <dt>目标</dt><dd>{{ profile.learning_goal }}</dd>
              <dt>基础</dt><dd>{{ profile.knowledge_level }}</dd>
              <dt>薄弱点</dt><dd>{{ profile.weak_points?.length ? profile.weak_points.join("、") : "待补充" }}</dd>
              <dt>偏好</dt><dd>{{ profile.learning_style }}</dd>
              <dt>时间</dt><dd>{{ profile.available_time }}</dd>
            </dl>
          </div>
        </el-popover>
        <UserMenu :user="currentUser" @logout="logout" />
      </div>
    </header>

    <main v-loading="loading" class="notebook-columns">
      <aside class="notebook-panel source-panel">
        <div class="notebook-panel__header">
          <h2>来源</h2>
          <el-tag effect="plain" size="small">{{ sources.length }}/5</el-tag>
        </div>
        <input
          ref="sourceInput"
          accept="application/pdf,.pdf"
          hidden
          multiple
          type="file"
          @change="uploadSources"
        />
        <button
          class="source-add-button"
          :disabled="uploadingSource || sources.length >= 5"
          @click="selectSources"
        >
          <el-icon><Plus /></el-icon>
          {{ uploadingSource ? "正在入库" : "添加PDF来源" }}
        </button>
        <div v-if="uploadingSource" class="source-upload-progress">
          <el-progress :percentage="sourceUploadProgress" :stroke-width="8" />
          <span>{{ sourceUploadStatus }}</span>
        </div>
        <div v-if="!sources.length" class="source-placeholder">
          <el-icon :size="22"><Files /></el-icon>
          <strong>添加当前笔记本的PDF来源</strong>
          <p>最多5份，每份不超过10MB。文本型PDF直接抽取，扫描型PDF会进入OCR解析。</p>
        </div>
        <div v-else class="source-list">
          <div
            v-for="item in sources"
            :key="item.id"
            class="source-list-row"
          >
            <div class="source-list-item">
              <el-icon><Document /></el-icon>
              <span>
                <strong>{{ item.original_name }}</strong>
                <em>{{ sourceMeta(item) }}</em>
              </span>
            </div>
            <button
              class="note-delete-button"
              :disabled="deletingSourceId === item.id || uploadingSource"
              title="删除PDF来源"
              @click="removeSource(item)"
            >
              <el-icon><Delete /></el-icon>
            </button>
          </div>
        </div>
        <div class="source-panel__notes">
          <div class="notebook-panel__subheading">
            <strong>笔记</strong>
            <button class="text-button" @click="noteDialogVisible = true">
              <el-icon><Plus /></el-icon>
              添加
            </button>
          </div>
          <p v-if="!notes.length" class="empty-copy">可以手动记录，也可以把对话回复保存为笔记。</p>
          <div
            v-for="item in notes"
            :key="item.id"
            class="note-list-row"
          >
            <button class="note-list-item" @click="openNote(item)">
              <el-icon><EditPen /></el-icon>
              <span>{{ item.title }}</span>
            </button>
            <button
              class="note-delete-button"
              :disabled="deletingNoteId === item.id"
              title="删除笔记"
              @click.stop="removeNote(item)"
            >
              <el-icon><Delete /></el-icon>
            </button>
          </div>
        </div>
      </aside>

      <section class="notebook-panel conversation-panel">
        <div class="notebook-panel__header">
          <div>
            <h2>对话</h2>
            <span>画像智能体与辅导智能体协同工作</span>
          </div>
          <el-tag :type="profile ? 'success' : 'warning'" effect="light" round size="small">
            {{ profile ? "画像已建立" : "画像待建立" }}
          </el-tag>
        </div>

        <div ref="chatBody" class="conversation-body">
          <section v-if="!messages.length" class="conversation-welcome">
            <div class="conversation-welcome__icon"><el-icon><ChatDotRound /></el-icon></div>
            <h2>从当前主题开始聊一聊</h2>
            <p>你可以介绍学习目标和基础，也可以直接提出问题。系统会在对话中更新画像，并据此生成个性化内容。</p>
            <div class="conversation-prompts">
              <button v-for="item in starterPrompts" :key="item" @click="composer = item">{{ item }}</button>
            </div>
          </section>

          <article
            v-for="item in messages"
            :key="item.id"
            :class="['conversation-message', `conversation-message--${item.role}`]"
          >
            <div class="conversation-message__meta">
              <strong>{{ item.role === "assistant" ? "学习辅导智能体" : "我" }}</strong>
            </div>
            <div class="conversation-message__content">
              <MarkdownContent
                v-if="item.role === 'assistant'"
                :content="item.content"
                :render-diagrams="!item.streaming"
              />
              <p v-else>{{ item.content }}</p>
              <div v-if="item.attachments?.length" class="conversation-message__attachments">
                <span v-for="attachment in item.attachments" :key="attachment.id">
                  <el-icon><Picture /></el-icon>
                  {{ attachment.original_name }}
                </span>
              </div>
            </div>
            <div
              v-if="item.role === 'assistant' && !item.streaming"
              class="conversation-message__actions"
            >
              <el-tooltip content="保存到笔记" placement="bottom">
                <button
                  class="conversation-message__action"
                  title="保存到笔记"
                  @click="saveAsNote(item.id)"
                >
                  <el-icon><EditPen /></el-icon>
                </button>
              </el-tooltip>
            </div>
          </article>

          <div v-if="sendingChat" class="conversation-thinking">
            <span />
            <span />
            <span />
            <em>{{ chatStatus || "画像分析与辅导回复生成中" }}</em>
          </div>
        </div>

        <div class="conversation-composer">
          <div v-if="pendingAttachments.length" class="conversation-composer__attachments">
            <span v-for="item in pendingAttachments" :key="item.id">
              <el-icon><Picture /></el-icon>
              <em>{{ item.original_name }}</em>
              <button
                :disabled="sendingChat"
                title="移除图片"
                @click="removeAttachment(item)"
              >
                <el-icon><Close /></el-icon>
              </button>
            </span>
          </div>
          <el-input
            v-model="composer"
            :autosize="{ minRows: 2, maxRows: 5 }"
            placeholder="提问、描述学习需求，或上传图片与文字一起发送"
            type="textarea"
            @keydown.ctrl.enter="sendChat"
          />
          <div>
            <span>支持图片混合提问 · Ctrl + Enter 发送</span>
            <div class="conversation-composer__actions">
              <input
                ref="attachmentInput"
                accept="image/png,image/jpeg,image/webp,image/gif"
                hidden
                multiple
                type="file"
                @change="uploadAttachments"
              />
              <el-button
                :disabled="sendingChat || uploadingAttachment || pendingAttachments.length >= 4"
                :loading="uploadingAttachment"
                circle
                title="上传图片"
                @click="selectAttachments"
              >
                <el-icon><Paperclip /></el-icon>
              </el-button>
              <el-button :loading="sendingChat" circle type="primary" @click="sendChat">
                <el-icon><Promotion /></el-icon>
              </el-button>
            </div>
          </div>
        </div>
      </section>

      <aside class="notebook-panel studio-panel">
        <div class="notebook-panel__header">
          <div>
            <h2>Studio</h2>
            <span>多智能体按需生成</span>
          </div>
          <el-icon><MagicStick /></el-icon>
        </div>
        <div class="studio-grid">
          <button
            v-for="item in studioApps"
            :key="item.type"
            :class="[
              'studio-app',
              `studio-app--${item.tone}`,
              {
                'studio-app--running': generatingArtifactType === item.type,
                'studio-app--waiting': generatingArtifact && generatingArtifactType !== item.type,
              },
            ]"
            :disabled="generatingArtifact"
            @click="openStudioDialog(item)"
          >
            <el-icon><component :is="item.icon" /></el-icon>
            <span>{{ item.label }}</span>
            <span v-if="generatingArtifactType === item.type" class="studio-app__status">
              <el-icon><Loading /></el-icon>
              生成中
            </span>
            <el-icon v-else class="studio-app__arrow"><ArrowRight /></el-icon>
          </button>
        </div>
        <div class="studio-history">
          <div class="notebook-panel__subheading">
            <strong>已生成内容</strong>
            <span>{{ artifacts.length }}</span>
          </div>
          <p v-if="!artifacts.length" class="empty-copy">选择上方应用，生成当前笔记本的个性化学习产物。</p>
          <div
            v-for="item in artifacts"
            :key="item.id"
            class="artifact-list-row"
          >
            <button class="artifact-list-item" @click="openArtifact(item)">
              <el-icon><Document /></el-icon>
              <span>
                <strong>{{ item.title }}</strong>
                <em>{{ artifactLabel(item.artifact_type) }}</em>
              </span>
            </button>
            <button
              class="note-delete-button"
              :disabled="deletingArtifactId === item.id"
              title="删除内容"
              @click.stop="removeArtifact(item)"
            >
              <el-icon><Delete /></el-icon>
            </button>
          </div>
        </div>
        <div v-if="latestTrace.length" class="agent-trace">
          <div class="notebook-panel__subheading">
            <strong>智能体协作轨迹</strong>
            <el-icon><Connection /></el-icon>
          </div>
          <ol>
            <li v-for="item in latestTrace" :key="item">{{ item }}</li>
          </ol>
        </div>
      </aside>
    </main>

    <el-dialog v-model="studioDialog.visible" :title="`生成${studioDialog.app?.label || '内容'}`" width="min(92vw, 620px)">
      <el-form label-position="top">
        <el-form-item label="输出语言">
          <el-select v-model="studioDialog.language">
            <el-option label="中文（简体）" value="中文（简体）" />
            <el-option label="English" value="English" />
          </el-select>
        </el-form-item>
        <el-form-item v-if="supportsDifficulty" label="难度">
          <el-radio-group v-model="studioDialog.difficulty">
            <el-radio-button label="easy">基础</el-radio-button>
            <el-radio-button label="medium">适中</el-radio-button>
            <el-radio-button label="hard">进阶</el-radio-button>
          </el-radio-group>
        </el-form-item>
        <el-form-item v-if="supportsQuantity" label="数量">
          <el-radio-group v-model="studioDialog.quantity">
            <el-radio-button label="fewer">少量</el-radio-button>
            <el-radio-button label="standard">标准</el-radio-button>
            <el-radio-button label="more">更多</el-radio-button>
          </el-radio-group>
        </el-form-item>
        <el-form-item label="补充要求">
          <el-input
            v-model="studioDialog.customPrompt"
            :rows="4"
            placeholder="可选：描述你希望强调的知识点、内容范围或输出形式"
            type="textarea"
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="studioDialog.visible = false">取消</el-button>
        <el-button :loading="generatingArtifact" type="primary" @click="generateArtifact">生成</el-button>
      </template>
    </el-dialog>

    <el-dialog
      v-model="artifactDialogVisible"
      :title="activeArtifact?.title || 'Studio 内容'"
      class="artifact-dialog"
      width="min(92vw, 760px)"
    >
      <section v-if="activeArtifact?.artifact_type === 'quiz'" class="quiz-viewer">
        <div class="quiz-viewer__status">
          <p>第 {{ quizIndex + 1 }} / {{ quizItemCount }} 题</p>
          <span>已答 {{ answeredQuizCount }} / {{ quizItemCount }}</span>
        </div>
        <h3>{{ activeQuizItem?.question }}</h3>
        <button
          v-for="(option, index) in activeQuizItem?.options || []"
          :key="option"
          :class="['quiz-option', quizOptionClass(index)]"
          @click="selectQuizOption(index)"
        >
          {{ option }}
        </button>
        <div v-if="selectedQuizAnswer !== null" class="quiz-explanation">
          <strong>{{ selectedQuizAnswer === activeQuizItem.answer ? "回答正确" : "再想一想" }}</strong>
          <p>{{ activeQuizItem.explanation }}</p>
        </div>
        <div v-if="quizReview" class="quiz-review">
          <strong>测验点评</strong>
          <MarkdownContent :content="quizReview.review" />
        </div>
        <div class="viewer-actions">
          <el-button :disabled="quizIndex === 0" @click="changeQuiz(-1)">上一题</el-button>
          <el-button :disabled="selectedQuizAnswer === null || sendingChat" @click="askActiveQuiz">
            <el-icon><ChatDotRound /></el-icon>
            解释
          </el-button>
          <el-button
            :disabled="!quizCompleted || quizReviewSubmitting || Boolean(quizReview)"
            :loading="quizReviewSubmitting"
            type="primary"
            @click="submitQuizReview"
          >
            {{ quizReview ? "已点评" : "完成并点评" }}
          </el-button>
          <el-button :disabled="quizIndex >= quizItemCount - 1" type="primary" @click="changeQuiz(1)">下一题</el-button>
        </div>
      </section>
      <section v-else-if="activeArtifact?.artifact_type === 'flashcards'" class="flashcard-viewer">
        <p>第 {{ flashcardIndex + 1 }} / {{ activeArtifact.artifact_data.items.length }} 张</p>
        <button class="flashcard" @click="flashcardRevealed = !flashcardRevealed">
          <span>{{ flashcardRevealed ? "答案" : "问题" }}</span>
          <strong>{{ flashcardRevealed ? activeFlashcard?.back : activeFlashcard?.front }}</strong>
          <em>点击翻面</em>
        </button>
        <p v-if="flashcardRevealed" class="flashcard-explanation">{{ activeFlashcard?.explanation }}</p>
        <div class="viewer-actions">
          <el-button :disabled="flashcardIndex === 0" @click="changeFlashcard(-1)">上一张</el-button>
          <el-button :disabled="flashcardIndex >= activeArtifact.artifact_data.items.length - 1" type="primary" @click="changeFlashcard(1)">下一张</el-button>
        </div>
      </section>
      <MarkdownContent v-else :content="activeArtifact?.content || ''" />
    </el-dialog>

    <el-dialog v-model="noteDialogVisible" title="添加笔记" width="min(92vw, 560px)">
      <el-form label-position="top">
        <el-form-item label="标题">
          <el-input v-model="noteForm.title" />
        </el-form-item>
        <el-form-item label="内容">
          <el-input v-model="noteForm.content" :rows="6" type="textarea" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="noteDialogVisible = false">取消</el-button>
        <el-button :loading="savingNote" type="primary" @click="submitNote">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { computed, nextTick, onBeforeUnmount, onMounted, reactive, ref } from "vue";
import { useRoute, useRouter } from "vue-router";
import {
  ArrowLeft,
  ArrowRight,
  ChatDotRound,
  Close,
  Connection,
  DataAnalysis,
  DataLine,
  Delete,
  Document,
  EditPen,
  Files,
  Grid,
  Guide,
  Loading,
  MagicStick,
  Paperclip,
  Picture,
  Plus,
  Promotion,
  Reading,
  Tickets,
  User,
} from "@element-plus/icons-vue";
import { ElMessage, ElMessageBox } from "element-plus";

import { getCurrentUser } from "../api/auth";
import { getErrorMessage } from "../api/http";
import {
  createNotebookNote,
  deleteNotebookAttachment,
  deleteNotebookNote,
  deleteNotebookSource,
  deleteStudioArtifact,
  generateStudioArtifact,
  getNotebookWorkspace,
  saveMessageAsNote,
  streamNotebookChat,
  submitQuizAttempt,
  uploadNotebookAttachment,
  uploadNotebookSource,
} from "../api/notebook";
import BrandMark from "../components/BrandMark.vue";
import MarkdownContent from "../components/MarkdownContent.vue";
import UserMenu from "../components/UserMenu.vue";
import { clearToken } from "../utils/auth";
import {
  readQuizProgress,
  removeQuizProgress as removeStoredQuizProgress,
  writeQuizProgress,
} from "../utils/quizProgressStorage";

const route = useRoute();
const router = useRouter();
const chatBody = ref(null);
const attachmentInput = ref(null);
const sourceInput = ref(null);
const currentUser = ref(null);
const notebook = ref(null);
const profile = ref(null);
const messages = ref([]);
const sources = ref([]);
const artifacts = ref([]);
const notes = ref([]);
const latestTrace = ref([]);
const loading = ref(false);
const sendingChat = ref(false);
const uploadingAttachment = ref(false);
const uploadingSource = ref(false);
const sourceUploadProgress = ref(0);
const sourceUploadStatus = ref("");
const chatStatus = ref("");
const generatingArtifact = ref(false);
const generatingArtifactType = ref(null);
const savingNote = ref(false);
const composer = ref("");
const pendingAttachments = ref([]);
const artifactDialogVisible = ref(false);
const noteDialogVisible = ref(false);
const deletingArtifactId = ref(null);
const deletingNoteId = ref(null);
const deletingSourceId = ref(null);
const activeArtifact = ref(null);
const quizIndex = ref(0);
const quizReviewSubmitting = ref(false);
const quizState = reactive({
  answers: {},
  review: null,
});
const flashcardIndex = ref(0);
const flashcardRevealed = ref(false);
const noteForm = reactive({
  title: "新笔记",
  content: "",
});
const studioDialog = reactive({
  visible: false,
  app: null,
  language: "中文（简体）",
  difficulty: "medium",
  quantity: "standard",
  customPrompt: "",
});

const notebookId = computed(() => Number(route.params.notebookId));
const supportsDifficulty = computed(() => ["quiz", "flashcards"].includes(studioDialog.app?.type));
const supportsQuantity = computed(() => ["quiz", "flashcards"].includes(studioDialog.app?.type));
const activeQuizItem = computed(() => activeArtifact.value?.artifact_data?.items?.[quizIndex.value]);
const activeFlashcard = computed(() => activeArtifact.value?.artifact_data?.items?.[flashcardIndex.value]);
const quizItemCount = computed(() => activeArtifact.value?.artifact_data?.items?.length || 0);
const selectedQuizAnswer = computed(() => {
  const answer = quizState.answers[quizIndex.value];
  return Number.isInteger(answer) ? answer : null;
});
const answeredQuizCount = computed(() => (
  Object.entries(quizState.answers).filter(([index, answer]) => {
    const item = activeArtifact.value?.artifact_data?.items?.[Number(index)];
    return item && Number.isInteger(answer);
  }).length
));
const quizCompleted = computed(() => quizItemCount.value > 0 && answeredQuizCount.value === quizItemCount.value);
const quizReview = computed(() => quizState.review);

const starterPrompts = [
  "我是初学者，帮我规划这个主题的学习顺序",
  "我想先理解这个主题最核心的概念",
  "我更喜欢通过练习掌握知识，请给我建议",
];

const studioApps = [
  { type: "learning_path", label: "学习路径", icon: DataLine, tone: "blue" },
  { type: "study_guide", label: "学习指南", icon: Guide, tone: "indigo" },
  { type: "mindmap", label: "思维导图", icon: Connection, tone: "purple" },
  { type: "quiz", label: "测验", icon: Tickets, tone: "cyan" },
  { type: "flashcards", label: "闪卡", icon: Grid, tone: "rose" },
  { type: "briefing", label: "拓展报告", icon: Reading, tone: "amber" },
  { type: "data_table", label: "数据表格", icon: DataAnalysis, tone: "green" },
  { type: "code_practice", label: "代码实操", icon: EditPen, tone: "slate" },
];

const CHAT_STREAM_FLUSH_INTERVAL_MS = 28;
const SOURCE_MAX_FILES = 5;
const SOURCE_MAX_BYTES = 10 * 1024 * 1024;
let scrollFrame = null;

function getChatStreamBatchSize(bufferLength) {
  if (bufferLength > 800) {
    return 64;
  }
  if (bufferLength > 320) {
    return 36;
  }
  if (bufferLength > 120) {
    return 20;
  }
  if (bufferLength > 32) {
    return 10;
  }
  return 4;
}

async function loadWorkspace() {
  loading.value = true;
  try {
    const [userResult, workspace] = await Promise.all([
      getCurrentUser(),
      getNotebookWorkspace(notebookId.value),
    ]);
    currentUser.value = userResult;
    notebook.value = workspace.notebook;
    profile.value = workspace.profile;
    sources.value = workspace.sources;
    messages.value = workspace.messages;
    pendingAttachments.value = workspace.pending_attachments;
    artifacts.value = workspace.artifacts;
    notes.value = workspace.notes;
    latestTrace.value = workspace.artifacts[0]?.artifact_data?.agent_trace || [];
    await scrollToBottom();
  } catch (error) {
    ElMessage.error(getErrorMessage(error));
  } finally {
    loading.value = false;
  }
}

async function sendChat() {
  const message = composer.value.trim();
  if ((!message && !pendingAttachments.value.length) || sendingChat.value || uploadingAttachment.value) {
    return;
  }
  sendingChat.value = true;
  chatStatus.value = "正在连接学习智能体";
  composer.value = "";
  const submittedAttachments = [...pendingAttachments.value];
  pendingAttachments.value = [];
  let streamedUserMessage = null;
  let streamedAssistantMessage = null;
  let queuedAssistantContent = "";
  let deltaTimer = null;
  let pendingCompleteEvent = null;
  let networkFinished = false;
  let resolveDisplayDone = null;
  const displayDone = new Promise((resolve) => {
    resolveDisplayDone = resolve;
  });
  const clearDeltaTimer = () => {
    if (deltaTimer !== null) {
      window.clearTimeout(deltaTimer);
      deltaTimer = null;
    }
  };
  const ensureStreamedAssistantMessage = () => {
    if (streamedAssistantMessage) {
      return streamedAssistantMessage;
    }
    streamedAssistantMessage = {
      id: `stream-${Date.now()}`,
      role: "assistant",
      content: "",
      streaming: true,
    };
    messages.value.push(streamedAssistantMessage);
    return streamedAssistantMessage;
  };
  const maybeFinishDisplay = () => {
    if (networkFinished && !queuedAssistantContent && deltaTimer === null && !pendingCompleteEvent) {
      resolveDisplayDone();
    }
  };
  const applyCompleteEvent = (event) => {
    pendingCompleteEvent = null;
    if (streamedAssistantMessage) {
      Object.assign(streamedAssistantMessage, event.message, {
        content: event.message?.content ?? streamedAssistantMessage.content,
        streaming: false,
      });
    } else if (event.message) {
      messages.value.push(event.message);
    }
    profile.value = event.profile;
    latestTrace.value = event.agent_trace;
    scheduleScrollToBottom();
    maybeFinishDisplay();
  };
  const scheduleDeltaFlush = () => {
    if (deltaTimer !== null) {
      return;
    }
    deltaTimer = window.setTimeout(flushDeltaContent, CHAT_STREAM_FLUSH_INTERVAL_MS);
  };
  const flushDeltaContent = () => {
    deltaTimer = null;
    if (queuedAssistantContent) {
      const messageTarget = ensureStreamedAssistantMessage();
      const batchSize = getChatStreamBatchSize(queuedAssistantContent.length);
      messageTarget.content += queuedAssistantContent.slice(0, batchSize);
      queuedAssistantContent = queuedAssistantContent.slice(batchSize);
      scheduleScrollToBottom();
    }
    if (queuedAssistantContent) {
      scheduleDeltaFlush();
      return;
    }
    if (pendingCompleteEvent) {
      applyCompleteEvent(pendingCompleteEvent);
      return;
    }
    maybeFinishDisplay();
  };
  try {
    await streamNotebookChat(notebookId.value, {
      message,
      attachment_ids: submittedAttachments.map((item) => item.id),
    }, (event) => {
      if (event.event === "user_message") {
        streamedUserMessage = event.message;
        messages.value.push(streamedUserMessage);
        scheduleScrollToBottom();
      }
      if (event.event === "status") {
        chatStatus.value = event.message;
      }
      if (event.event === "tool_start") {
        generatingArtifact.value = true;
        generatingArtifactType.value = event.artifact_type;
        chatStatus.value = event.message;
      }
      if (event.event === "tool_end" && generatingArtifactType.value === event.artifact_type) {
        generatingArtifact.value = false;
        generatingArtifactType.value = null;
      }
      if (event.event === "delta") {
        queuedAssistantContent += event.content;
        scheduleDeltaFlush();
      }
      if (event.event === "complete") {
        pendingCompleteEvent = event;
        if (!queuedAssistantContent && deltaTimer === null) {
          applyCompleteEvent(event);
        }
      }
      if (event.event === "artifact") {
        artifacts.value.unshift(event.artifact);
        latestTrace.value = event.agent_trace;
      }
      if (event.event === "error") {
        throw new Error(event.message);
      }
    });
    networkFinished = true;
    if (!queuedAssistantContent && deltaTimer === null && pendingCompleteEvent) {
      applyCompleteEvent(pendingCompleteEvent);
    }
    maybeFinishDisplay();
    await displayDone;
  } catch (error) {
    clearDeltaTimer();
    queuedAssistantContent = "";
    pendingCompleteEvent = null;
    messages.value = messages.value.filter(
      (item) => item !== streamedUserMessage && item !== streamedAssistantMessage,
    );
    composer.value = message;
    pendingAttachments.value = [
      ...submittedAttachments,
      ...pendingAttachments.value,
    ];
    ElMessage.error(getErrorMessage(error));
  } finally {
    sendingChat.value = false;
    chatStatus.value = "";
    generatingArtifact.value = false;
    generatingArtifactType.value = null;
  }
}

function selectAttachments() {
  attachmentInput.value?.click();
}

function selectSources() {
  if (uploadingSource.value || sources.value.length >= SOURCE_MAX_FILES) {
    return;
  }
  sourceInput.value?.click();
}

function validateSourceFile(file) {
  if (file.type && file.type !== "application/pdf") {
    return "仅支持PDF文件";
  }
  if (!file.name.toLowerCase().endsWith(".pdf")) {
    return "仅支持PDF文件";
  }
  if (file.size > SOURCE_MAX_BYTES) {
    return "单个PDF不能超过10MB";
  }
  return "";
}

async function uploadSources(event) {
  const selectedFiles = [...event.target.files];
  event.target.value = "";
  if (!selectedFiles.length || uploadingSource.value) {
    return;
  }
  const remaining = SOURCE_MAX_FILES - sources.value.length;
  if (remaining <= 0) {
    ElMessage.warning("每个笔记本最多上传5份PDF来源");
    return;
  }
  if (selectedFiles.length > remaining) {
    ElMessage.warning(`还可以上传 ${remaining} 份PDF，已忽略超出部分`);
  }
  const files = selectedFiles.slice(0, remaining);
  uploadingSource.value = true;
  try {
    for (const [index, file] of files.entries()) {
      const validationMessage = validateSourceFile(file);
      if (validationMessage) {
        ElMessage.error(`${file.name}：${validationMessage}`);
        continue;
      }
      sourceUploadProgress.value = 0;
      sourceUploadStatus.value = `上传 ${index + 1}/${files.length}：${file.name}`;
      try {
        const result = await uploadNotebookSource(notebookId.value, file, (progressEvent) => {
          if (!progressEvent.total) {
            return;
          }
          const uploaded = Math.round((progressEvent.loaded / progressEvent.total) * 80);
          sourceUploadProgress.value = Math.min(uploaded, 80);
          if (sourceUploadProgress.value >= 80) {
            sourceUploadStatus.value = "PDF已上传，正在解析文本、OCR并写入知识库";
          }
        });
        sourceUploadProgress.value = 100;
        sourceUploadStatus.value = "入库完成";
        sources.value.unshift(result.source);
        ElMessage.success(`${file.name} 已入库`);
      } catch (error) {
        ElMessage.error(`${file.name}：${getErrorMessage(error)}`);
      }
    }
  } finally {
    window.setTimeout(() => {
      sourceUploadProgress.value = 0;
      sourceUploadStatus.value = "";
    }, 500);
    uploadingSource.value = false;
  }
}

async function uploadAttachments(event) {
  const files = [...event.target.files].slice(0, 4 - pendingAttachments.value.length);
  event.target.value = "";
  if (!files.length) {
    return;
  }
  uploadingAttachment.value = true;
  try {
    for (const file of files) {
      try {
        const result = await uploadNotebookAttachment(notebookId.value, file);
        pendingAttachments.value.push(result.attachment);
      } catch (error) {
        ElMessage.error(`${file.name}：${getErrorMessage(error)}`);
      }
    }
  } finally {
    uploadingAttachment.value = false;
  }
}

async function removeAttachment(item) {
  if (sendingChat.value) {
    return;
  }
  try {
    await deleteNotebookAttachment(notebookId.value, item.id);
    pendingAttachments.value = pendingAttachments.value.filter(
      (attachment) => attachment.id !== item.id,
    );
  } catch (error) {
    ElMessage.error(getErrorMessage(error));
  }
}

async function removeSource(item) {
  if (deletingSourceId.value || uploadingSource.value) {
    return;
  }
  try {
    await ElMessageBox.confirm(`确定删除PDF来源“${item.original_name}”吗？`, "删除来源", {
      type: "warning",
      confirmButtonText: "删除",
      cancelButtonText: "取消",
    });
  } catch {
    return;
  }

  deletingSourceId.value = item.id;
  try {
    await deleteNotebookSource(notebookId.value, item.id);
    sources.value = sources.value.filter((source) => source.id !== item.id);
    ElMessage.success("PDF来源已删除");
  } catch (error) {
    ElMessage.error(getErrorMessage(error));
  } finally {
    deletingSourceId.value = null;
  }
}

function openStudioDialog(app) {
  studioDialog.app = app;
  studioDialog.customPrompt = "";
  studioDialog.visible = true;
}

async function generateArtifact() {
  if (!studioDialog.app || generatingArtifact.value) {
    return;
  }
  generatingArtifact.value = true;
  generatingArtifactType.value = studioDialog.app.type;
  studioDialog.visible = false;
  try {
    const result = await generateStudioArtifact(notebookId.value, {
      artifact_type: studioDialog.app.type,
      language: studioDialog.language,
      difficulty: studioDialog.difficulty,
      quantity: studioDialog.quantity,
      custom_prompt: studioDialog.customPrompt.trim(),
    });
    artifacts.value.unshift(result.artifact);
    latestTrace.value = result.agent_trace;
    openArtifact(result.artifact);
  } catch (error) {
    ElMessage.error(getErrorMessage(error));
  } finally {
    generatingArtifact.value = false;
    generatingArtifactType.value = null;
  }
}

function openArtifact(item) {
  activeArtifact.value = item;
  artifactDialogVisible.value = true;
  quizIndex.value = 0;
  if (item.artifact_type === "quiz") {
    loadQuizProgress(item);
  } else {
    resetQuizState();
  }
  flashcardIndex.value = 0;
  flashcardRevealed.value = false;
}

function openNote(item) {
  activeArtifact.value = {
    note_id: item.id,
    title: item.title,
    content: item.content,
    artifact_type: "note",
  };
  artifactDialogVisible.value = true;
}

async function removeNote(item) {
  if (deletingNoteId.value) {
    return;
  }
  try {
    await ElMessageBox.confirm(`确定删除笔记“${item.title}”吗？`, "删除笔记", {
      type: "warning",
      confirmButtonText: "删除",
      cancelButtonText: "取消",
    });
  } catch {
    return;
  }

  deletingNoteId.value = item.id;
  try {
    await deleteNotebookNote(notebookId.value, item.id);
    notes.value = notes.value.filter((note) => note.id !== item.id);
    if (activeArtifact.value?.note_id === item.id) {
      artifactDialogVisible.value = false;
      activeArtifact.value = null;
    }
    ElMessage.success("笔记已删除");
  } catch (error) {
    ElMessage.error(getErrorMessage(error));
  } finally {
    deletingNoteId.value = null;
  }
}

async function removeArtifact(item) {
  if (deletingArtifactId.value) {
    return;
  }
  try {
    await ElMessageBox.confirm(`确定删除已生成内容“${item.title}”吗？`, "删除内容", {
      type: "warning",
      confirmButtonText: "删除",
      cancelButtonText: "取消",
    });
  } catch {
    return;
  }

  deletingArtifactId.value = item.id;
  try {
    const deletingLatest = artifacts.value[0]?.id === item.id;
    await deleteStudioArtifact(notebookId.value, item.id);
    artifacts.value = artifacts.value.filter((artifact) => artifact.id !== item.id);
    if (deletingLatest) {
      latestTrace.value = artifacts.value[0]?.artifact_data?.agent_trace || [];
    }
    if (activeArtifact.value?.id === item.id) {
      artifactDialogVisible.value = false;
      activeArtifact.value = null;
      resetQuizState();
    }
    removeQuizProgress(item);
    ElMessage.success("内容已删除");
  } catch (error) {
    ElMessage.error(getErrorMessage(error));
  } finally {
    deletingArtifactId.value = null;
  }
}

async function saveAsNote(messageId) {
  try {
    const result = await saveMessageAsNote(notebookId.value, messageId);
    notes.value.unshift(result.note);
    ElMessage.success("已保存到笔记");
  } catch (error) {
    ElMessage.error(getErrorMessage(error));
  }
}

async function submitNote() {
  if (!noteForm.title.trim() || !noteForm.content.trim() || savingNote.value) {
    ElMessage.warning("请填写笔记标题和内容");
    return;
  }
  savingNote.value = true;
  try {
    const result = await createNotebookNote(notebookId.value, {
      title: noteForm.title.trim(),
      content: noteForm.content.trim(),
    });
    notes.value.unshift(result.note);
    noteForm.title = "新笔记";
    noteForm.content = "";
    noteDialogVisible.value = false;
  } catch (error) {
    ElMessage.error(getErrorMessage(error));
  } finally {
    savingNote.value = false;
  }
}

function resetQuizState() {
  quizState.answers = {};
  quizState.review = null;
}

function getPersistedQuizReview(item) {
  const latestReview = item?.artifact_data?.latest_quiz_review;
  if (!latestReview?.review) {
    return null;
  }
  return {
    correct_count: latestReview.correct_count,
    total_count: latestReview.total_count,
    score_percent: latestReview.score_percent,
    review: latestReview.review,
  };
}

function normalizeQuizAnswers(rawAnswers, item = activeArtifact.value) {
  const items = item?.artifact_data?.items || [];
  const normalized = {};
  if (!rawAnswers || typeof rawAnswers !== "object") {
    return normalized;
  }

  Object.entries(rawAnswers).forEach(([rawIndex, rawAnswer]) => {
    const index = Number(rawIndex);
    const answer = Number(rawAnswer);
    const options = items[index]?.options || [];
    if (
      Number.isInteger(index)
      && Number.isInteger(answer)
      && index >= 0
      && index < items.length
      && answer >= 0
      && answer < options.length
    ) {
      normalized[index] = answer;
    }
  });
  return normalized;
}

function loadQuizProgress(item) {
  resetQuizState();
  const persistedReview = getPersistedQuizReview(item);
  if (!item?.id) {
    quizState.review = persistedReview;
    return;
  }
  const cached = readQuizProgress(notebookId.value, item.id);
  if (!cached) {
    quizState.review = persistedReview;
    return;
  }
  quizState.answers = normalizeQuizAnswers(cached.answers, item);
  quizState.review = cached.review || persistedReview;
}

function saveQuizProgress() {
  if (!activeArtifact.value?.id || activeArtifact.value?.artifact_type !== "quiz") {
    return;
  }
  writeQuizProgress(notebookId.value, activeArtifact.value.id, {
    answers: quizState.answers,
    review: quizState.review,
  });
}

function removeQuizProgress(item) {
  removeStoredQuizProgress(notebookId.value, item?.id);
}

function selectQuizOption(index) {
  if (!activeQuizItem.value) {
    return;
  }
  quizState.answers[quizIndex.value] = index;
  quizState.review = null;
  saveQuizProgress();
}

function quizOptionClass(index) {
  if (selectedQuizAnswer.value === null) {
    return "";
  }
  if (index === activeQuizItem.value.answer) {
    return "quiz-option--correct";
  }
  return index === selectedQuizAnswer.value ? "quiz-option--wrong" : "";
}

function changeQuiz(step) {
  if (!quizItemCount.value) {
    return;
  }
  const nextIndex = quizIndex.value + step;
  quizIndex.value = Math.min(Math.max(nextIndex, 0), quizItemCount.value - 1);
}

function buildQuizAskPrompt() {
  const item = activeQuizItem.value;
  const selectedIndex = selectedQuizAnswer.value;
  if (!item || selectedIndex === null) {
    return "";
  }
  const selectedOption = item.options?.[selectedIndex];
  const correctOption = item.options?.[item.answer];
  if (!selectedOption || !correctOption) {
    return "";
  }
  if (selectedIndex === item.answer) {
    return [
      `我在做这份材料的测验时遇到了这个问题：“${item.question}”`,
      "",
      `我选择了正确的答案：“${selectedOption}”`,
      "",
      "请深入讲解一下这个主题。",
    ].join("\n");
  }
  return [
    `我在做这份材料的测验时遇到了这个问题：“${item.question}”`,
    "",
    `我选择的答案是：“${selectedOption}”`,
    "",
    `选错了。正确的答案是“${correctOption}”`,
    "",
    "请解释一下我选择的答案哪里错了。",
  ].join("\n");
}

async function askActiveQuiz() {
  if (sendingChat.value) {
    return;
  }
  const prompt = buildQuizAskPrompt();
  if (!prompt) {
    ElMessage.warning("请先选择一个答案");
    return;
  }
  artifactDialogVisible.value = false;
  composer.value = prompt;
  await nextTick();
  await sendChat();
}

function buildQuizAnswerList() {
  return (activeArtifact.value?.artifact_data?.items || []).map(
    (_, index) => quizState.answers[index],
  );
}

function replaceArtifact(updatedArtifact) {
  artifacts.value = artifacts.value.map((item) => (
    item.id === updatedArtifact.id ? updatedArtifact : item
  ));
  if (activeArtifact.value?.id === updatedArtifact.id) {
    activeArtifact.value = updatedArtifact;
  }
}

async function submitQuizReview() {
  if (!activeArtifact.value?.id || !quizCompleted.value || quizReviewSubmitting.value || quizReview.value) {
    return;
  }
  quizReviewSubmitting.value = true;
  try {
    const result = await submitQuizAttempt(notebookId.value, activeArtifact.value.id, {
      answers: buildQuizAnswerList(),
    });
    profile.value = result.profile;
    quizState.review = {
      correct_count: result.correct_count,
      total_count: result.total_count,
      score_percent: result.score_percent,
      review: result.review,
    };
    if (result.artifact) {
      replaceArtifact(result.artifact);
    }
    saveQuizProgress();
    ElMessage.success("测验点评已生成，画像已更新");
  } catch (error) {
    ElMessage.error(getErrorMessage(error));
  } finally {
    quizReviewSubmitting.value = false;
  }
}

function changeFlashcard(step) {
  flashcardIndex.value += step;
  flashcardRevealed.value = false;
}

function artifactLabel(type) {
  return studioApps.find((item) => item.type === type)?.label || "笔记";
}

function formatFileSize(bytes) {
  if (bytes >= 1024 * 1024) {
    return `${(bytes / 1024 / 1024).toFixed(1)}MB`;
  }
  return `${Math.max(1, Math.round(bytes / 1024))}KB`;
}

function sourceMeta(item) {
  const methodLabel = {
    embedded_text: "文本",
    vision_ocr: "OCR",
    mixed: "文本+OCR",
  }[item.extraction_method] || "解析";
  return `${formatFileSize(item.file_size)} · ${item.page_count}页 · ${item.chunk_count}段 · ${methodLabel}`;
}

async function scrollToBottom() {
  await nextTick();
  if (chatBody.value) {
    chatBody.value.scrollTop = chatBody.value.scrollHeight;
  }
}

function scheduleScrollToBottom() {
  if (scrollFrame !== null) {
    return;
  }
  scrollFrame = window.requestAnimationFrame(async () => {
    scrollFrame = null;
    await scrollToBottom();
  });
}

async function goBack() {
  await router.push({ name: "notebooks" });
}

async function logout() {
  clearToken();
  await router.push({ name: "login" });
}

onMounted(loadWorkspace);

onBeforeUnmount(() => {
  if (scrollFrame !== null) {
    window.cancelAnimationFrame(scrollFrame);
    scrollFrame = null;
  }
});
</script>
