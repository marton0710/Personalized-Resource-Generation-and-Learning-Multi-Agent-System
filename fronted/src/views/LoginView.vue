<template>
  <AuthPanel>
    <div class="auth-card__heading">
      <p>WELCOME BACK</p>
      <h2>欢迎回来</h2>
      <span>登录后继续你的个性化学习旅程</span>
    </div>

    <el-tabs v-model="loginMode" class="auth-tabs" stretch @keyup.enter="submit">
      <el-tab-pane label="密码登录" name="password">
        <el-form ref="passwordFormRef" :model="passwordForm" :rules="passwordRules" label-position="top">
          <el-form-item label="用户名" prop="username">
            <el-input v-model="passwordForm.username" placeholder="请输入用户名" size="large">
              <template #prefix>
                <el-icon><User /></el-icon>
              </template>
            </el-input>
          </el-form-item>

          <el-form-item label="密码" prop="password">
            <el-input
              v-model="passwordForm.password"
              placeholder="请输入密码"
              show-password
              size="large"
              type="password"
            >
              <template #prefix>
                <el-icon><Lock /></el-icon>
              </template>
            </el-input>
          </el-form-item>

          <el-button
            :loading="passwordLoading"
            class="auth-submit"
            size="large"
            type="primary"
            @click="submitPassword"
          >
            登录
            <el-icon><ArrowRight /></el-icon>
          </el-button>
        </el-form>
      </el-tab-pane>

      <el-tab-pane label="邮箱登录" name="email">
        <el-form ref="emailFormRef" :model="emailForm" :rules="emailRules" label-position="top">
          <el-form-item label="邮箱" prop="email">
            <el-input v-model="emailForm.email" placeholder="请输入注册邮箱" size="large">
              <template #prefix>
                <el-icon><Message /></el-icon>
              </template>
            </el-input>
          </el-form-item>

          <el-form-item label="验证码" prop="email_code">
            <el-input v-model="emailForm.email_code" maxlength="6" placeholder="请输入验证码" size="large">
              <template #prefix>
                <el-icon><Key /></el-icon>
              </template>
              <template #append>
                <el-button
                  :disabled="loginCodeCountdown > 0"
                  :loading="loginCodeSending"
                  @click="sendLoginCode"
                >
                  {{ loginCodeButtonText }}
                </el-button>
              </template>
            </el-input>
          </el-form-item>

          <el-button
            :loading="emailLoading"
            class="auth-submit"
            size="large"
            type="primary"
            @click="submitEmailCode"
          >
            登录
            <el-icon><ArrowRight /></el-icon>
          </el-button>
        </el-form>
      </el-tab-pane>
    </el-tabs>

    <p class="auth-switch">
      还没有账号？
      <router-link to="/register">创建新账号</router-link>
    </p>
  </AuthPanel>
</template>

<script setup>
import { computed, onUnmounted, reactive, ref } from "vue";
import { useRouter } from "vue-router";
import { ArrowRight, Key, Lock, Message, User } from "@element-plus/icons-vue";
import { ElMessage } from "element-plus";

import { login, loginByEmailCode, sendEmailCode } from "../api/auth";
import { getErrorMessage } from "../api/http";
import AuthPanel from "../components/AuthPanel.vue";
import { setToken } from "../utils/auth";

const router = useRouter();
const loginMode = ref("password");
const passwordFormRef = ref(null);
const emailFormRef = ref(null);
const passwordLoading = ref(false);
const emailLoading = ref(false);
const loginCodeSending = ref(false);
const loginCodeCountdown = ref(0);
let loginCodeTimer = 0;

const passwordForm = reactive({
  username: "",
  password: "",
});
const emailForm = reactive({
  email: "",
  email_code: "",
});
const passwordRules = {
  username: [
    {
      required: true,
      message: "请输入用户名",
      trigger: "blur",
    },
  ],
  password: [
    {
      required: true,
      message: "请输入密码",
      trigger: "blur",
    },
  ],
};
const emailRules = {
  email: [
    {
      required: true,
      message: "请输入邮箱",
      trigger: "blur",
    },
    {
      type: "email",
      message: "请输入有效邮箱",
      trigger: "blur",
    },
  ],
  email_code: [
    {
      required: true,
      message: "请输入验证码",
      trigger: "blur",
    },
  ],
};
const loginCodeButtonText = computed(() => {
  if (loginCodeCountdown.value > 0) {
    return `${loginCodeCountdown.value}s`;
  }

  return "获取验证码";
});

async function submit() {
  if (loginMode.value === "password") {
    await submitPassword();
    return;
  }

  await submitEmailCode();
}

async function submitPassword() {
  const valid = await passwordFormRef.value?.validate().catch(() => false);

  if (!valid || passwordLoading.value) {
    return;
  }

  passwordLoading.value = true;

  try {
    const result = await login(passwordForm);
    await finishLogin(result.token);
  } catch (error) {
    ElMessage.error(getErrorMessage(error));
  } finally {
    passwordLoading.value = false;
  }
}

async function submitEmailCode() {
  const valid = await emailFormRef.value?.validate().catch(() => false);

  if (!valid || emailLoading.value) {
    return;
  }

  emailLoading.value = true;

  try {
    const result = await loginByEmailCode(emailForm);
    await finishLogin(result.token);
  } catch (error) {
    ElMessage.error(getErrorMessage(error));
  } finally {
    emailLoading.value = false;
  }
}

async function sendLoginCode() {
  const valid = await emailFormRef.value?.validateField("email").catch(() => false);

  if (valid === false || loginCodeSending.value || loginCodeCountdown.value > 0) {
    return;
  }

  loginCodeSending.value = true;

  try {
    await sendEmailCode({
      email: emailForm.email,
      purpose: "login",
    });
    startLoginCodeCountdown();
    ElMessage.success("验证码已发送");
  } catch (error) {
    ElMessage.error(getErrorMessage(error));
  } finally {
    loginCodeSending.value = false;
  }
}

function startLoginCodeCountdown() {
  loginCodeCountdown.value = 60;
  window.clearInterval(loginCodeTimer);
  loginCodeTimer = window.setInterval(() => {
    loginCodeCountdown.value -= 1;
    if (loginCodeCountdown.value <= 0) {
      window.clearInterval(loginCodeTimer);
    }
  }, 1000);
}

async function finishLogin(token) {
  setToken(token);
  ElMessage.success("登录成功");
  await router.push({
    name: "notebooks",
  });
}

onUnmounted(() => {
  window.clearInterval(loginCodeTimer);
});
</script>
