import { createRouter, createWebHistory } from "vue-router";

import { getToken } from "../utils/auth";
import ForumListView from "../views/ForumListView.vue";
import ForumPostView from "../views/ForumPostView.vue";
import LoginView from "../views/LoginView.vue";
import NotebookListView from "../views/NotebookListView.vue";
import NotebookWorkspaceView from "../views/NotebookWorkspaceView.vue";
import RegisterView from "../views/RegisterView.vue";

const router = createRouter({
  history: createWebHistory(),
  routes: [
    {
      path: "/",
      redirect: "/notebooks",
    },
    {
      path: "/login",
      name: "login",
      component: LoginView,
      meta: {
        guest: true,
      },
    },
    {
      path: "/register",
      name: "register",
      component: RegisterView,
      meta: {
        guest: true,
      },
    },
    {
      path: "/notebooks",
      name: "notebooks",
      component: NotebookListView,
      meta: {
        requiresAuth: true,
      },
    },
    {
      path: "/notebooks/:notebookId",
      name: "notebook",
      component: NotebookWorkspaceView,
      meta: {
        requiresAuth: true,
      },
    },
    {
      path: "/forum",
      name: "forum",
      component: ForumListView,
      meta: {
        requiresAuth: true,
      },
    },
    {
      path: "/forum/posts/:postId",
      name: "forum-post",
      component: ForumPostView,
      meta: {
        requiresAuth: true,
      },
    },
  ],
});

router.beforeEach((to) => {
  const hasToken = Boolean(getToken());

  if (to.meta.requiresAuth && !hasToken) {
    return {
      name: "login",
    };
  }

  if (to.meta.guest && hasToken) {
    return {
      name: "notebooks",
    };
  }
});

export default router;
