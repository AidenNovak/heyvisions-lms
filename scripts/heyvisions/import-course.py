#!/usr/bin/env python3
"""把 HeyVisions 课程「AI 协作基础」导入 LearnHouse。

事实源是 website 仓库的课程合同（不是本仓库的副本）：
  <website>/example/src/course/curriculum.js      阶段 / 单元结构与发布状态
  <website>/example/src/course-content/units/*.md 单元正文（按 unitKey 以 Markdown URL 拉取）

设计要点：
- **幂等**：重复执行不会产生重复的课程、章节或活动。按名字找到既有的就复用。
- **尊重发布合同**：只有 publication=published 的单元会导入；draft 单元不生成活动，
  与课程合同「draft 不生成公开课时页」一致。
- **不复制正文**：正文留在 website 仓库，本脚本只传 URL，避免两处事实源漂移。

用法：
  python3 scripts/heyvisions/import-course.py \
      --website ~/projects/website \
      --api http://localhost:1349/api/v1 \
      --units-base http://127.0.0.1:8022/units
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

import requests

COURSE_NAME = "AI 协作基础"


def load_curriculum(website: Path) -> dict:
    """用 node 读取课程合同，避免在 Python 里重复解析 JS。"""
    curriculum_js = website / "example/src/course/curriculum.js"
    if not curriculum_js.exists():
        sys.exit(f"找不到课程合同：{curriculum_js}")
    script = (
        f"import {{curriculum, courseKey, courseVersion}} from 'file://{curriculum_js}';"
        "console.log(JSON.stringify({curriculum, courseKey, courseVersion}))"
    )
    out = subprocess.run(
        ["node", "--input-type=module", "-e", script],
        capture_output=True, text=True,
    )
    if out.returncode != 0:
        sys.exit(f"读取课程合同失败：{out.stderr.strip()}")
    return json.loads(out.stdout)


def read_admin_password(secrets_path: Path) -> str:
    if not secrets_path.exists():
        sys.exit(f"找不到凭据文件：{secrets_path}")
    for line in secrets_path.read_text().splitlines():
        if line.startswith("LEARNHOUSE_INITIAL_ADMIN_PASSWORD="):
            return line.split("=", 1)[1]
    sys.exit(f"{secrets_path} 缺少 LEARNHOUSE_INITIAL_ADMIN_PASSWORD")


def login(api: str, email: str, password: str, org_slug: str) -> dict:
    r = requests.post(
        f"{api}/auth/login",
        data={"username": email, "password": password, "org_slug": org_slug},
        timeout=30,
    )
    r.raise_for_status()
    return {"Authorization": f"Bearer {r.json()['tokens']['access_token']}"}


def find_course(api: str, headers: dict, org_slug: str, page_size: int = 100) -> dict | None:
    """按名字找既有课程，实现幂等。"""
    r = requests.get(
        f"{api}/courses/org_slug/{org_slug}/page/1/limit/{page_size}",
        headers=headers,
        timeout=30,
    )
    if not r.ok:
        return None
    for course in r.json() or []:
        if course.get("name") == COURSE_NAME:
            return course
    return None


def ensure_course(api: str, headers: dict, org_id: int, org_slug: str, learnings: str) -> dict:
    existing = find_course(api, headers, org_slug)
    if existing:
        print(f"复用既有课程：{existing['name']} (uuid={existing['course_uuid']})")
        return existing
    r = requests.post(
        f"{api}/courses/",
        params={"org_id": org_id},
        headers=headers,
        data={
            "name": COURSE_NAME,
            "description": "六阶段实践课程：从判断任务到沉淀可复用的 AI 协作工作流。当前开放前两个阶段的 6 个公开单元。",
            "about": "AI 协作基础。六个阶段逐步交付：个人 AI 任务地图、可验收的任务说明、"
            "上下文资料包、协作记录、验证与修复记录、可复用工作流。",
            "learnings": learnings,
            "tags": "AI 协作,知识工作,工作流",
            "public": "true",
        },
        timeout=30,
    )
    r.raise_for_status()
    course = r.json()
    print(f"新建课程：{course['name']} (uuid={course['course_uuid']})")
    return course


def find_chapter(api: str, headers: dict, course_id: int, name: str) -> dict | None:
    r = requests.get(
        f"{api}/chapters/course/{course_id}/page/1/limit/100", headers=headers, timeout=30
    )
    if not r.ok:
        return None
    for ch in r.json() or []:
        if ch.get("name") == name:
            return ch
    return None


def ensure_chapter(api: str, headers: dict, course_id: int, org_id: int, stage: dict) -> dict:
    name = f"{stage['number']} {stage['title']}"
    existing = find_chapter(api, headers, course_id, name)
    if existing:
        print(f"  复用章节：{name}")
        return existing
    r = requests.post(
        f"{api}/chapters/",
        headers=headers,
        json={
            "name": name,
            "description": stage["summary"],
            "org_id": org_id,
            "course_id": course_id,
        },
        timeout=30,
    )
    r.raise_for_status()
    ch = r.json()
    print(f"  新建章节：{name}")
    return ch


def existing_activity_names(api: str, headers: dict, chapter_id: int) -> set[str]:
    """某章节下已有的活动名，用于跳过重复导入。"""
    r = requests.get(f"{api}/activities/chapter/{chapter_id}", headers=headers, timeout=30)
    if not r.ok:
        return set()
    return {(a.get("name") or "") for a in (r.json() or [])}


def ensure_activity(
    api: str,
    headers: dict,
    course_id: int,
    chapter_id: int,
    unit: dict,
    units_base: str,
    existing: set[str],
) -> None:
    name = f"{unit['number']} {unit['title']}"
    if name in existing:
        print(f"    复用活动：{name}")
        return
    payload = {
        "name": name,
        "chapter_id": chapter_id,
        "course_id": course_id,
        "activity_type": "TYPE_DYNAMIC",
        "activity_sub_type": "SUBTYPE_DYNAMIC_MARKDOWN",
        "content": {"markdown_url": f"{units_base}/{unit['unitKey']}.md"},
        "published": True,
        "lock_type": "public" if unit.get("accessLevel") == "public" else "authenticated",
    }
    r = requests.post(f"{api}/activities/", headers=headers, json=payload, timeout=30)
    r.raise_for_status()
    print(f"    新建活动：{name}")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--website", default="~/projects/website", help="website 仓库根目录")
    ap.add_argument("--api", default="http://localhost:1349/api/v1", help="LearnHouse API 基址")
    ap.add_argument("--units-base", default="http://127.0.0.1:8022/units", help="Markdown 单元的 URL 前缀")
    ap.add_argument("--secrets", default=None, help="凭据文件（默认取 fork 内 apps/api/.demo-secrets）")
    ap.add_argument("--admin-email", default="admin@school.dev")
    ap.add_argument("--org-slug", default="default")
    args = ap.parse_args()

    website = Path(args.website).expanduser()
    secrets = Path(args.secrets).expanduser() if args.secrets else Path(__file__).resolve().parents[2] / "apps/api/.demo-secrets"

    data = load_curriculum(website)
    stages = [
        s for s in data["curriculum"]
        if any(u.get("publication") == "published" for u in s["units"])
    ]
    print(f"课程合同：{data['courseKey']} v{data['courseVersion']}，含公开单元的阶段 {len(stages)} 个")

    headers = login(args.api, args.admin_email, read_admin_password(secrets), args.org_slug)
    print("登录成功")

    r = requests.get(f"{args.api}/orgs/slug/{args.org_slug}", headers=headers, timeout=30)
    r.raise_for_status()
    org_id = r.json()["id"]

    learnings = "|".join(s["outcome"] for s in data["curriculum"])
    course = ensure_course(args.api, headers, org_id, args.org_slug, learnings)
    course_id, course_uuid = course["id"], course["course_uuid"]

    for stage in stages:
        ch = ensure_chapter(args.api, headers, course_id, org_id, stage)
        existing = existing_activity_names(args.api, headers, ch["id"])
        for unit in stage["units"]:
            if unit.get("publication") != "published":
                print(f"    跳过草稿：{unit['unitKey']}")
                continue
            ensure_activity(
                args.api, headers, course_id, ch["id"], unit, args.units_base, existing
            )

    r = requests.put(f"{args.api}/courses/{course_uuid}", headers=headers, json={"published": True}, timeout=30)
    r.raise_for_status()
    print("课程已发布")

    r = requests.put(f"{args.api}/orgs/{org_id}", headers=headers, json={"name": "HeyVisions"}, timeout=30)
    print("组织改名：", r.status_code, (r.json().get("name") if r.ok else r.text[:120]))

    print(f"\n完成。课程页：/course/{course_uuid}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
