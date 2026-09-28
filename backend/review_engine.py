from __future__ import annotations

import io
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Literal

import fitz
from docx import Document
from openpyxl import load_workbook


Severity = Literal["blocking", "high", "medium", "info"]


@dataclass(slots=True)
class Evidence:
    file: str
    page: int
    excerpt: str


@dataclass(slots=True)
class Finding:
    finding_id: str
    severity: Severity
    title: str
    detail: str
    evidence: list[Evidence]
    suggestion: str
    needs_human_review: bool = False


@dataclass(slots=True)
class ParsedFile:
    path: Path
    name: str
    pages: int
    characters: int
    parser: str


@dataclass(slots=True)
class ReviewResult:
    files: list[ParsedFile]
    findings: list[Finding]


SUPPORTED_SUFFIXES = {".pdf", ".docx", ".xlsx", ".txt", ".md", ".csv", ".json"}


def extract_pdf(data: bytes) -> list[str]:
    document = fitz.open(stream=data, filetype="pdf")
    try:
        return [page.get_text("text") for page in document]
    finally:
        document.close()


def extract_docx(data: bytes) -> list[str]:
    document = Document(io.BytesIO(data))
    lines = [paragraph.text for paragraph in document.paragraphs]
    for table in document.tables:
        for row in table.rows:
            lines.append(" | ".join(cell.text for cell in row.cells))
    return ["\n".join(lines)]


def extract_xlsx(data: bytes) -> list[str]:
    workbook = load_workbook(io.BytesIO(data), read_only=True, data_only=True)
    try:
        pages: list[str] = []
        for sheet in workbook.worksheets:
            rows = [
                " | ".join("" if value is None else str(value) for value in row)
                for row in sheet.iter_rows(values_only=True)
            ]
            pages.append(f"工作表：{sheet.title}\n" + "\n".join(rows))
        return pages
    finally:
        workbook.close()


def extract_text(path: Path) -> tuple[list[str], str]:
    data = path.read_bytes()
    suffix = path.suffix.lower()
    if suffix == ".pdf":
        return extract_pdf(data), "PyMuPDF"
    if suffix == ".docx":
        return extract_docx(data), "python-docx"
    if suffix == ".xlsx":
        return extract_xlsx(data), "openpyxl"
    if suffix in {".txt", ".md", ".csv", ".json"}:
        return [data.decode("utf-8", errors="replace")], "文本解析"
    raise ValueError(f"暂不支持 {suffix or '未知'} 格式")


def first_evidence(documents: list[tuple[str, list[str]]], pattern: str) -> Evidence | None:
    regex = re.compile(pattern, re.IGNORECASE)
    for name, pages in documents:
        for page_number, text in enumerate(pages, start=1):
            match = regex.search(text)
            if match:
                start = max(0, match.start() - 40)
                end = min(len(text), match.end() + 70)
                excerpt = re.sub(r"\s+", " ", text[start:end]).strip()
                return Evidence(file=name, page=page_number, excerpt=excerpt)
    return None


def competition_review(documents: list[tuple[str, list[str]]]) -> list[Finding]:
    findings: list[Finding] = []
    all_names = " ".join(name for name, _ in documents)
    expected = {"报名表": r"报名|申报", "项目书": r"项目书|计划书|商业计划", "承诺书": r"承诺"}
    for label, pattern in expected.items():
        if not re.search(pattern, all_names, re.IGNORECASE):
            findings.append(Finding(
                finding_id=f"C-MISSING-{len(findings) + 1:02d}",
                severity="blocking" if label != "承诺书" else "high",
                title=f"未识别到{label}",
                detail=f"当前文件名中没有识别到{label}，请确认它是否属于必交材料。",
                evidence=[Evidence(file="材料清单", page=1, excerpt=f"待核对材料：{label}")],
                suggestion=f"上传{label}，或在正式规则中确认该材料并非必交。",
                needs_human_review=True,
            ))

    evidence = first_evidence(documents, r"团队成员\s*[:：]\s*([^\n]+)")
    if evidence:
        value = re.split(r"[:：]", evidence.excerpt, maxsplit=1)[-1]
        members = [item.strip() for item in re.split(r"[、,，;；]", value) if item.strip()]
        if 0 < len(members) < 3:
            findings.append(Finding(
                finding_id="C-TEAM-01", severity="blocking", title="团队人数可能不足",
                detail=f"成员字段中识别到约 {len(members)} 名成员，当前演示规则要求 3 至 5 人。",
                evidence=[evidence], suggestion="根据正式比赛通知确认人数要求，并同步更新报名表和项目书。",
                needs_human_review=True,
            ))
    if not findings:
        findings.append(Finding(
            finding_id="C-INFO-01", severity="info", title="基础检查未发现阻断项",
            detail="已完成文件名、材料类型和可提取文本检查。语义规则仍需人工确认。",
            evidence=[Evidence(file=documents[0][0], page=1, excerpt="材料已成功解析并进入审查流程。")],
            suggestion="继续核对作品名称、成员、指导教师和签章等跨文档字段。", needs_human_review=True,
        ))
    return findings


def contract_review(documents: list[tuple[str, list[str]]]) -> list[Finding]:
    findings: list[Finding] = []
    payment = first_evidence(documents, r"(?:预付|预付款|首付款)[^。；\n]{0,35}?(\d{1,3})\s*%")
    if payment:
        percentage_match = re.search(r"(\d{1,3})\s*%", payment.excerpt)
        percentage = int(percentage_match.group(1)) if percentage_match else 0
        if percentage > 30:
            findings.append(Finding(
                finding_id="H-PAY-01", severity="high", title="预付款超过规则上限",
                detail=f"识别到预付款比例为 {percentage}%，高于当前内部规则的 30%。",
                evidence=[payment], suggestion="调整付款节点，或提交附带理由的例外审批。",
            ))
    acceptance = first_evidence(documents, r"验收")
    acceptance_period = first_evidence(documents, r"验收[^。；\n]{0,30}\d+\s*(?:个)?(?:工作)?日")
    if acceptance and not acceptance_period:
        findings.append(Finding(
            finding_id="H-ACCEPT-01", severity="medium", title="验收期限未明确",
            detail="材料提到验收，但没有识别到明确的天数或工作日限制。", evidence=[acceptance],
            suggestion="补充验收期限、验收标准和逾期处理方式。", needs_human_review=True,
        ))
    if not findings:
        findings.append(Finding(
            finding_id="H-INFO-01", severity="info", title="基础条款检查完成",
            detail="未触发预付款和验收期限规则，仍需人工确认主体、金额和责任条款。",
            evidence=[Evidence(file=documents[0][0], page=1, excerpt="合同材料已成功解析并进入审查流程。")],
            suggestion="结合企业内部制度补充规则后重新运行审查。", needs_human_review=True,
        ))
    return findings


def review_paths(
    scenario: Literal["competition", "contract"],
    paths: list[Path],
    progress: Callable[[int, int, str], None] | None = None,
) -> ReviewResult:
    if not paths:
        raise ValueError("请先添加需要审查的材料")
    parsed_files: list[ParsedFile] = []
    documents: list[tuple[str, list[str]]] = []
    total = len(paths)
    for index, path in enumerate(paths, start=1):
        if progress:
            progress(index - 1, total, f"正在解析 {path.name}")
        pages, parser = extract_text(path)
        documents.append((path.name, pages))
        parsed_files.append(ParsedFile(path, path.name, max(1, len(pages)), sum(len(page) for page in pages), parser))
    if progress:
        progress(total, total, "正在执行审查规则")
    findings = contract_review(documents) if scenario == "contract" else competition_review(documents)
    return ReviewResult(parsed_files, findings)
