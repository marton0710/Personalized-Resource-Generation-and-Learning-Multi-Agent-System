<template>
  <AuthPanel>
    <div class="auth-card__heading">
      <p>CREATE ACCOUNT</p>
      <h2>开始学习旅程</h2>
      <span>创建账号，生成属于你的学习路径</span>
    </div>

    <el-form ref="formRef" :model="form" :rules="rules" label-position="top">
      <el-form-item label="用户名" prop="username">
        <el-input v-model="form.username" placeholder="设置用户名" size="large">
          <template #prefix>
            <el-icon><User /></el-icon>
          </template>
        </el-input>
      </el-form-item>

      <el-form-item label="邮箱" prop="email">
        <el-input v-model="form.email" placeholder="用于账号识别" size="large">
          <template #prefix>
            <el-icon><Message /></el-icon>
          </template>
        </el-input>
      </el-form-item>

      <el-form-item label="验证码" prop="email_code">
        <el-input v-model="form.email_code" maxlength="6" placeholder="请输入验证码" size="large">
          <template #prefix>
            <el-icon><Key /></el-icon>
          </template>
          <template #append>
            <el-button
              :disabled="registerCodeCountdown > 0"
              :loading="registerCodeSending"
              @click="sendRegisterCode"
            >
              {{ registerCodeButtonText }}
            </el-button>
          </template>
        </el-input>
      </el-form-item>

      <el-form-item label="密码" prop="password">
        <el-input v-model="form.password" placeholder="设置密码" show-password size="large" type="password">
          <template #prefix>
            <el-icon><Lock /></el-icon>
          </template>
        </el-input>
      </el-form-item>

      <el-form-item label="确认密码" prop="confirm_password">
        <el-input
          v-model="form.confirm_password"
          placeholder="再次输入密码"
          show-password
          size="large"
          type="password"
        >
          <template #prefix>
            <el-icon><Lock /></el-icon>
          </template>
        </el-input>
      </el-form-item>

      <el-button :loading="loading" class="auth-submit" size="large" type="primary" @click="submit">
        创建账号
        <el-icon><ArrowRight /></el-icon>
      </el-button>
    </el-form>

    <p class="auth-switch">
      已有账号？
      <router-link to="/login">返回登录</router-link>
    </p>
  </AuthPanel>
</template>

<script setup>
import { computed, onUnmounted, reactive, ref } from "vue";
import { useRouter } from "vue-router";
import { ArrowRight, Key, Lock, Message, User } from "@element-plus/icons-vue";
import { ElMessage } from "element-plus";

import { register, sendEmailCode } from "../api/auth";
import { getErrorMessage } from "../api/http";
import AuthPanel from "../components/AuthPanel.vue";

const router = useRouter();
const formRef = ref(null);
const loading = ref(false);
const registerCodeSending = ref(false);
const registerCodeCountdown = ref(0);
let registerCodeTimer = 0;
const form = reactive({
  username: "",
  email: "",
  email_code: "",
  password: "",
  confirm_password: "",
});
const validatePassword = (rule, value, callback) => {
  if (value !== form.password) {
    callback(new Error("两次输入的密码不一致"));
    return;
  }

  callback();
};
const rules = {
  username: [
    {
      required: true,
      message: "请输入用户名",
      trigger: "blur",
    },
  ],
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
  password: [
    {
      required: true,
      message: "请输入密码",
      trigger: "blur",
    },
  ],
  confirm_password: [
    {
      required: true,
      message: "请再次输入密码",
      trigger: "blur",
    },
    {
      validator: validatePassword,
      trigger: "blur",
    },
  ],
};
const registerCodeButtonText = computed(() => {
  if (registerCodeCountdown.value > 0) {
    return `${registerCodeCountdown.value}s`;
  }

  return "获取验证码";
});

async function submit() {
  const valid = await formRef.value?.validate().catch(() => false);

  if (!valid || loading.value) {
    return;
  }

  loading.value = true;

  try {
    await register(form);
    ElMessage.success("注册成功，请登录");
    await router.push({
      name: "login",
    });
  } catch (error) {
    ElMessage.error(getErrorMessage(error));
  } finally {
    loading.value = false;
  }
}

async function sendRegisterCode() {
  const valid = await formRef.value?.validateField("email").catch(() => false);

  if (valid === false || registerCodeSending.value || registerCodeCountdown.value > 0) {
    return;
  }

  registerCodeSending.value = true;

  try {
    await sendEmailCode({
      email: form.email,
      purpose: "register",
    });
    startRegisterCodeCountdown();
    ElMessage.success("验证码已发送");
  } catch (error) {
    ElMessage.error(getErrorMessage(error));
  } finally {
    registerCodeSending.value = false;
  }
}

function startRegisterCodeCountdown() {
  registerCodeCountdown.value = 60;
  window.clearInterval(registerCodeTimer);
  registerCodeTimer = window.setInterval(() => {
    registerCodeCountdown.value -= 1;
    if (registerCodeCountdown.value <= 0) {
      window.clearInterval(registerCodeTimer);
    }
  }, 1000);
}

onUnmounted(() => {
  window.clearInterval(registerCodeTimer);
});
</script>
