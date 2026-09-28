import type { Finding, Scenario } from "./types";

export const scenarios: Scenario[] = [
  {
    id: "competition",
    name: "大学生竞赛审查",
    description: "从赛事通知提取规则，核对资格、材料完整性与跨文件信息。",
    status: "ready",
    documentTypes: ["比赛通知", "报名表", "项目书", "证明材料"]
  },
  {
    id: "contract",
    name: "合同审查",
    description: "核查主体、金额、期限、附件冲突和关键条款风险。",
    status: "ready",
    documentTypes: ["合同正文", "报价单", "交付清单", "内部规则"]
  },
  {
    id: "research",
    name: "科研材料审查",
    description: "比对论文、配置与实验结果，检查材料是否足以复现。",
    status: "preview",
    documentTypes: ["论文", "配置文件", "结果数据", "README"]
  },
  {
    id: "resume",
    name: "招聘材料审查",
    description: "连接简历主张、项目证据和岗位要求，定位能力缺口。",
    status: "planned",
    documentTypes: ["简历", "作品集", "证书", "岗位说明"]
  },
  {
    id: "reimbursement",
    name: "报销材料审查",
    description: "核对申请单、票据、支付记录与费用规则。",
    status: "planned",
    documentTypes: ["申请单", "发票", "支付记录", "采购清单"]
  }
];

export const competitionFindings: Finding[] = [
  {
    id: "C-001",
    severity: "blocking",
    title: "团队人数不符合参赛要求",
    detail: "比赛通知要求团队由 3 至 5 名学生组成，报名表当前仅识别到 2 名成员。",
    source: "比赛通知.pdf",
    page: 3,
    excerpt: "每支参赛团队须由3至5名全日制在校学生组成。",
    suggestion: "补充至少1名符合学籍要求的团队成员，并同步更新项目书成员页。",
    resolved: false
  },
  {
    id: "C-002",
    severity: "high",
    title: "作品名称跨文件不一致",
    detail: "报名表使用“明鉴”，项目书封面使用“赛智通”。",
    source: "项目申报书.pdf",
    page: 1,
    excerpt: "项目名称：赛智通材料审查平台",
    suggestion: "确认正式作品名称后，统一报名表、项目书和演示材料。",
    resolved: false
  },
  {
    id: "C-003",
    severity: "medium",
    title: "指导教师签字缺失",
    detail: "承诺书已包含指导教师姓名，但签字区域为空。",
    source: "参赛承诺书.pdf",
    page: 2,
    excerpt: "指导教师签字：________________",
    suggestion: "完成签字后重新扫描，并确认页面方向与清晰度。",
    resolved: false
  },
  {
    id: "C-004",
    severity: "info",
    title: "项目摘要缺少量化效果",
    detail: "摘要描述了功能，但未给出审查效率或准确率指标。",
    source: "项目申报书.pdf",
    page: 4,
    excerpt: "系统能够帮助参赛者提高材料审查效率。",
    suggestion: "补充测试集规模、问题召回率和人工耗时对比。",
    resolved: false
  }
];

export const contractFindings: Finding[] = [
  {
    id: "H-001",
    severity: "high",
    title: "乙方主体名称不一致",
    detail: "合同首页与报价单中的乙方名称存在差异。",
    source: "设备采购合同.pdf",
    page: 1,
    excerpt: "乙方：星云数字科技有限公司",
    suggestion: "核实正式签约主体，并同步修改正文、附件及开票信息。",
    resolved: false
  },
  {
    id: "H-002",
    severity: "high",
    title: "预付款超过内部上限",
    detail: "合同约定预付80%，企业规则要求预付款不超过30%。",
    source: "设备采购合同.pdf",
    page: 4,
    excerpt: "合同签订后3个工作日内支付合同总额的80%。",
    suggestion: "调整付款节点，或提交附带理由的例外审批。",
    resolved: false
  },
  {
    id: "H-003",
    severity: "medium",
    title: "验收期限未明确",
    detail: "条款规定完成验收，但没有约定验收期限和逾期处理方式。",
    source: "设备采购合同.pdf",
    page: 6,
    excerpt: "甲方应在设备交付后组织验收。",
    suggestion: "补充明确的验收天数、标准和逾期视为验收的处理方式。",
    resolved: false
  }
];
