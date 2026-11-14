#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Verify the durable 195-country history archive without third-party packages."""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
errors: list[str] = []


def check(condition: bool, message: str) -> None:
    if not condition:
        errors.append(message)


def load_json(path: str) -> dict:
    file = ROOT / path
    try:
        obj = json.loads(file.read_text(encoding="utf-8"))
        if not isinstance(obj, dict):
            raise ValueError("expected JSON object")
        return obj
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        errors.append(f"Cannot read {path}: {exc}")
        return {}


def check_local_links(file: Path) -> None:
    text = file.read_text(encoding="utf-8")
    # Only check simple Markdown links without parentheses in targets.
    for target in re.findall(r"(?<!\!)\[[^\]\n]+\]\(([^\s\)]+)\)", text):
        if target.startswith(("http://", "https://", "mailto:", "#", "data:")):
            continue
        path = target.split("#", 1)[0]
        if path:
            check((file.parent / path).exists(), f"{file.relative_to(ROOT)}: broken local link {path}")


def main() -> int:
    data = load_json("data/countries.json")
    progress = load_json("progress.json")
    countries = data.get("countries", [])
    check(isinstance(countries, list), "data/countries.json.countries must be an array")
    if not isinstance(countries, list):
        countries = []
    check(len(countries) == 195, f"Expected 195 countries, found {len(countries)}")

    published = []
    previous = -1.0
    names_en: set[str] = set()
    slugs: set[str] = set()
    for i, entry in enumerate(countries, 1):
        if not isinstance(entry, dict):
            errors.append(f"country {i}: expected object")
            continue
        check(entry.get("rank") == i, f"country {i}: rank mismatch")
        check(entry.get("code") == f"{i:03d}", f"country {i}: code mismatch")
        en = entry.get("name_en", "")
        zh = entry.get("name_zh", "")
        slug = entry.get("slug", "")
        check(isinstance(en, str) and bool(en), f"country {i}: missing English name")
        check(isinstance(zh, str) and bool(zh), f"country {i}: missing Chinese name")
        check(en not in names_en, f"country {i}: duplicated English name {en}")
        names_en.add(en)
        check(isinstance(slug, str) and bool(re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", slug)), f"country {i}: invalid slug")
        check(slug not in slugs, f"country {i}: duplicated slug {slug}")
        slugs.add(slug)
        try:
            area = float(entry.get("area_km2"))
            check(area > 0, f"country {i}: area must be positive")
            check(area >= previous, f"country {i}: area order descends unexpectedly")
            previous = area
        except (ValueError, TypeError):
            errors.append(f"country {i}: invalid area")
        status = entry.get("status")
        check(status in ("published", "pending"), f"country {i}: invalid status {status}")
        expected_path = f"countries/{i:03d}-{slug}/README.md"
        if status == "published":
            published.append(entry)
            check(entry.get("path") == expected_path, f"country {i}: published path != expected {expected_path}")
            file = ROOT / expected_path
            check(file.is_file(), f"country {i}: missing published document: {expected_path}")
            if file.is_file():
                first = file.read_text(encoding="utf-8").splitlines()[0]
                check(first.startswith(f"# 第{i:03d}国："), f"country {i}: document title numbering error")
                check(len(file.read_text(encoding="utf-8")) > 3000, f"country {i}: document suspiciously short")
        elif status == "pending":
            check(entry.get("path") is None, f"country {i}: pending must have null path")
    n = len(published)

    # Cross-country knowledge reviews are a publication dependency, not a
    # historical-fact verification engine. Legacy chapters 001-007 are exempt
    # from the new editorial decision requirement but not from being recorded.
    knowledge = load_json("data/knowledge_reviews.json")
    reviews = knowledge.get("reviews", [])
    check(isinstance(reviews, list), "knowledge_reviews.reviews must be an array")
    if not isinstance(reviews, list):
        reviews = []
    check(len(reviews) == n,
          f"Expected {n} knowledge-review records for published countries, got {len(reviews)}")
    for i, review in enumerate(reviews):
        if not isinstance(review, dict):
            errors.append(f"knowledge review {i + 1}: expected object")
            continue
        check(review.get("rank") == i + 1,
              f"knowledge review {i + 1}: rank mismatch")
        if i < len(published):
            check(review.get("country") == published[i].get("name_zh"),
                  f"knowledge review {i + 1}: country name mismatch")
        decision = review.get("decision")
        check(decision in ("legacy_not_individually_reviewed", "added_or_updated", "reviewed_no_change"),
              f"knowledge review {i + 1}: invalid decision {decision!r}")
        if i >= 8:
            check(decision in ("added_or_updated", "reviewed_no_change"),
                  f"knowledge review {i + 1}: rank >=009 requires an actual review")
        if decision == "legacy_not_individually_reviewed":
            check(i <= 6, f"knowledge review {i + 1}: only 001-007 can be legacy")
        reason = review.get("reason")
        check(isinstance(reason, str) and len(reason.strip()) >= 20,
              f"knowledge review {i + 1}: missing substantive reason")
        files = review.get("files")
        check(isinstance(files, list), f"knowledge review {i + 1}: files must be list")
        if not isinstance(files, list):
            files = []
        if decision == "added_or_updated":
            check(bool(files), f"knowledge review {i + 1}: changed shared files must be listed")
        for shared in files:
            check(isinstance(shared, str) and shared.endswith(".md") and Path(shared).name == shared and chr(92) not in shared,
                  f"knowledge review {i + 1}: shared file must be a root Markdown file: {shared}")
            if isinstance(shared, str):
                check((ROOT / shared).is_file(),
                      f"knowledge review {i + 1}: missing shared file: {shared}")

    common = progress.get("source_of_truth", {}).get("common_knowledge", [])
    check(isinstance(common, list), "progress.source_of_truth.common_knowledge must be list")
    if isinstance(common, list):
        check(len(common) == len(set(common)), "duplicate shared knowledge paths")
        for file in common:
            check(isinstance(file, str) and (ROOT / file).is_file(),
                  f"progress lists missing common knowledge file: {file}")
    check(progress.get("source_of_truth", {}).get("knowledge_reviews") == "data/knowledge_reviews.json",
          "progress.source_of_truth.knowledge_reviews missing or wrong")

    check([x.get("rank") for x in published] == list(range(1, n + 1)),
          "published entries must form a contiguous prefix 1..N")
    check(progress.get("total") == 195, "progress.total != 195")
    check(progress.get("completed_count") == n, f"progress completed_count mismatch: {n}")
    check(progress.get("last_completed_rank") == (n if n else None),
          "progress.last_completed_rank mismatch")
    expected_next = (n + 1) if n < 195 else None
    check(progress.get("next_rank") == expected_next, "progress.next_rank mismatch")

    completed = progress.get("completed", [])
    check(isinstance(completed, list), "progress.completed must be list")
    if isinstance(completed, list):
        check(len(completed) == n, "progress.completed length differs from countries published")
        for i, item in enumerate(completed[:n]):
            check(item.get("rank") == i + 1, f"progress.completed[{i}].rank mismatch")
            if i < len(published):
                check(item.get("path") == published[i].get("path"),
                      f"progress.completed[{i}].path mismatch")
    last = progress.get("last_completed")
    if n:
        check(isinstance(last, dict), "progress.last_completed must be object")
        if isinstance(last, dict):
            check(last.get("rank") == n and last.get("path") == published[-1].get("path"),
                  "progress.last_completed does not identify latest published chapter")
    else:
        check(last is None, "No published countries: last_completed must be null")
    nxt = progress.get("next")
    if expected_next:
        check(isinstance(nxt, dict), "progress.next must be object")
        if isinstance(nxt, dict) and len(countries) >= expected_next:
            row = countries[expected_next - 1]
            for key, field in [("rank", "rank"), ("name_zh", "name_zh"), ("name_en", "name_en"), ("slug", "slug")]:
                check(nxt.get(key) == row.get(field), f"progress.next.{key} mismatch")
            check(nxt.get("status") == "pending", "progress.next.status must be pending")
            check(nxt.get("path") is None, "progress.next.path must be null")
    else:
        check(nxt is None, "Fully finished project: next must be null")
    index = ROOT / "COUNTRY_INDEX.md"
    if index.is_file():
        text = index.read_text(encoding="utf-8")
        codes = re.findall(r"^\|\s*(\d{3})\s*\|", text, re.M)
        check(codes == [f"{i:03d}" for i in range(1, 196)],
              f"COUNTRY_INDEX.md must list 001..195 exactly once in order; found {len(codes)}")
        for x in countries:
            code, name, status = x.get("code"), x.get("name_zh"), x.get("status")
            lines = [line for line in text.splitlines() if line.startswith(f"| {code} |")]
            if lines:
                check(str(name) in lines[0], f"index missing name for {code}")
                check(("已完成" if status == "published" else "未开始") in lines[0],
                      f"index status mismatch for {code}")
    else:
        errors.append("COUNTRY_INDEX.md missing")

    for path in ("README.md", "AGENTS.md", "WORKFLOW.md", "QUALITY_STANDARD.md",
                 "00-阅读说明与目录.md", "01-人类共同起点.md",
                 "02-六大早期文明区域.md", "03-基督教与罗马帝国.md",
                 "04-跨国共同历史.md", "05-加勒比海与大西洋奴隶制.md",
                 "data/knowledge_reviews.json"):
        check((ROOT / path).is_file(), f"missing required project file: {path}")

    # Validate local Markdown references for these docs; only links we can parse
    # without needing a full Markdown renderer are checked.
    for path in ("README.md", "00-阅读说明与目录.md", "COUNTRY_INDEX.md", "AGENTS.md",
                 "WORKFLOW.md", "QUALITY_STANDARD.md", "04-跨国共同历史.md",
                 "05-加勒比海与大西洋奴隶制.md",
                 *(x.get("path") for x in published if x.get("path"))):
        f = ROOT / path
        if f.is_file():
            check_local_links(f)

    if errors:
        print(f"FAILED: {len(errors)} problem(s)")
        for err in errors:
            print(" - " + err)
        return 1
    print(f"PASS: 195 countries in ascending surface area; {n} published; "
          f"{len(reviews)} knowledge reviews; next={expected_next}; "
          f"chapters, index, progress, shared files and local links agree.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
