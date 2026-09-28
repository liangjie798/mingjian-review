const features = {
  competition: {
    number: "[00] MATERIAL REVIEW",
    title: "让比赛规则真正可执行",
    body: "上传比赛通知、报名表和项目书。明鉴检查材料完整性、团队人数与关键字段，输出按风险排序的整改清单。",
    image: "./assets/app-workspace.png",
    alt: "明鉴竞赛材料审查工作台"
  },
  contract: {
    number: "[01] CONTRACT REVIEW",
    title: "先看风险，再回到条款",
    body: "检查预付款比例、验收期限、主体信息和附件冲突。每个风险都附带原文片段和可执行建议。",
    image: "./assets/app-workspace.png",
    alt: "明鉴合同材料审查工作台"
  },
  evidence: {
    number: "[02] EVIDENCE TRACE",
    title: "每条结论都有来源",
    body: "问题与文件、页码和原文绑定。人工复核无需重新翻阅整份材料，可以直接检查判断依据。",
    image: "./assets/app-workspace.png",
    alt: "明鉴证据定位与问题详情"
  },
  local: {
    number: "[03] LOCAL FIRST",
    title: "本地运行，材料更安心",
    body: "桌面端在本机启动审查服务。基础解析和确定性规则无需外部账户，也不会把文件上传到远程服务器。",
    image: "./assets/app-home.png",
    alt: "明鉴本地桌面端首页"
  }
};

const nav = document.querySelector("[data-nav]");
const menuButton = document.querySelector("[data-menu]");
const mobileMenu = document.querySelector("[data-mobile-menu]");
const tabs = document.querySelectorAll("[data-feature]");
const visual = document.querySelector(".feature-visual");

window.addEventListener("scroll", () => {
  nav?.classList.toggle("scrolled", window.scrollY > 20);
}, { passive: true });

menuButton?.addEventListener("click", () => {
  const open = menuButton.getAttribute("aria-expanded") === "true";
  menuButton.setAttribute("aria-expanded", String(!open));
  mobileMenu.hidden = open;
});

mobileMenu?.querySelectorAll("a").forEach((link) => {
  link.addEventListener("click", () => {
    mobileMenu.hidden = true;
    menuButton?.setAttribute("aria-expanded", "false");
  });
});

tabs.forEach((tab) => {
  tab.addEventListener("click", () => {
    const feature = features[tab.dataset.feature];
    if (!feature) return;
    tabs.forEach((item) => {
      const active = item === tab;
      item.classList.toggle("active", active);
      item.setAttribute("aria-selected", String(active));
    });
    visual?.classList.add("changing");
    window.setTimeout(() => {
      document.querySelector("[data-feature-number]").textContent = feature.number;
      document.querySelector("[data-feature-title]").textContent = feature.title;
      document.querySelector("[data-feature-body]").textContent = feature.body;
      const image = document.querySelector("[data-feature-image]");
      image.src = feature.image;
      image.alt = feature.alt;
      visual?.classList.remove("changing");
    }, 180);
  });
});

const observer = new IntersectionObserver((entries) => {
  entries.forEach((entry) => {
    if (entry.isIntersecting) {
      entry.target.classList.add("visible");
      observer.unobserve(entry.target);
    }
  });
}, { threshold: 0.12 });

document.querySelectorAll(".reveal").forEach((element) => observer.observe(element));

document.querySelector("[data-copy-hash]")?.addEventListener("click", async (event) => {
  const button = event.currentTarget;
  const hash = document.querySelector("[data-hash]")?.textContent?.trim();
  if (!hash) return;
  try {
    await navigator.clipboard.writeText(hash);
    button.textContent = "已复制 SHA-256";
    window.setTimeout(() => { button.textContent = "复制 SHA-256"; }, 1800);
  } catch {
    button.textContent = "请手动复制下方校验值";
  }
});
