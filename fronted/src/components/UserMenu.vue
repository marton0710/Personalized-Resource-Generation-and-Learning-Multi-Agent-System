<template>
  <el-dropdown trigger="click">
    <button class="avatar-button">{{ userInitial }}</button>
    <template #dropdown>
      <el-dropdown-menu>
        <el-dropdown-item @click="profileVisible = true">
          <el-icon><User /></el-icon>
          个人主页
        </el-dropdown-item>
        <el-dropdown-item divided @click="emit('logout')">
          <el-icon><SwitchButton /></el-icon>
          退出登录
        </el-dropdown-item>
      </el-dropdown-menu>
    </template>
  </el-dropdown>

  <el-dialog
    v-model="profileVisible"
    class="user-profile-dialog"
    title="个人主页"
    width="min(92vw, 460px)"
  >
    <section class="user-profile-card">
      <div class="user-profile-card__avatar">{{ userInitial }}</div>
      <div>
        <strong>{{ nickname }}</strong>
        <span>{{ email }}</span>
      </div>
    </section>

    <el-descriptions :column="1" border>
      <el-descriptions-item label="用户昵称">{{ nickname }}</el-descriptions-item>
      <el-descriptions-item label="邮箱">{{ email }}</el-descriptions-item>
      <el-descriptions-item label="个性签名">
        <div v-if="!editingSignature" class="user-profile-signature">
          <span>{{ signature }}</span>
          <el-button link type="primary" @click="startEditSignature">修改</el-button>
        </div>
        <div v-else class="user-profile-signature-editor">
          <el-input
            v-model="signatureDraft"
            :rows="3"
            maxlength="200"
            placeholder="写一句介绍自己的话"
            show-word-limit
            type="textarea"
          />
          <div>
            <el-button @click="cancelEditSignature">取消</el-button>
            <el-button :loading="savingSignature" type="primary" @click="saveSignature">保存</el-button>
          </div>
        </div>
      </el-descriptions-item>
    </el-descriptions>
  </el-dialog>
</template>

<script setup>
import { computed, ref, watch } from "vue";
import { SwitchButton, User } from "@element-plus/icons-vue";
import { ElMessage } from "element-plus";

import { updateCurrentUserSignature } from "../api/auth";
import { getErrorMessage } from "../api/http";

const props = defineProps({
  user: {
    type: Object,
    default: null,
  },
});
const emit = defineEmits(["logout"]);
const profileVisible = ref(false);
const editingSignature = ref(false);
const savingSignature = ref(false);
const savedSignature = ref(null);
const signatureDraft = ref("");

const nickname = computed(() => props.user?.nickname || props.user?.username || "未登录用户");
const email = computed(() => props.user?.email || "暂未绑定邮箱");
const rawSignature = computed(() => savedSignature.value ?? props.user?.signature ?? "");
const signature = computed(() => rawSignature.value || "这个人还没有填写个性签名");
const userInitial = computed(() => nickname.value.slice(0, 1).toUpperCase() || "U");

watch(
  () => props.user?.signature,
  (value) => {
    savedSignature.value = value || "";
  },
  {
    immediate: true,
  },
);

function startEditSignature() {
  signatureDraft.value = rawSignature.value;
  editingSignature.value = true;
}

function cancelEditSignature() {
  editingSignature.value = false;
  signatureDraft.value = rawSignature.value;
}

async function saveSignature() {
  if (savingSignature.value) {
    return;
  }

  savingSignature.value = true;
  try {
    const result = await updateCurrentUserSignature({
      signature: signatureDraft.value,
    });
    savedSignature.value = result.signature || "";
    editingSignature.value = false;
    ElMessage.success("个性签名已更新");
  } catch (error) {
    ElMessage.error(getErrorMessage(error));
  } finally {
    savingSignature.value = false;
  }
}
</script>
