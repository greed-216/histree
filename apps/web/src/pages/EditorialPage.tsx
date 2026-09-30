import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import type {
  Topic,
  Source,
  FactClaim,
  Person,
  Event,
  PersonRelationship,
  PersonEventRelation,
  EventCausalityRelation,
  ClaimSubject,
} from "@histree/shared-types";
import { apiFetch, getCurrentUserRole } from "../lib/api";
import { PublicationField } from "../components/PublicationField";
import { relationshipSentence } from "../lib/graph";

type Table = "topic" | "source" | "fact_claim";
type Catalog = {
  person: Person[];
  event: Event[];
  person_relationship: PersonRelationship[];
  person_event: PersonEventRelation[];
  event_causality: EventCausalityRelation[];
};
const blankCatalog: Catalog = {
  person: [],
  event: [],
  person_relationship: [],
  person_event: [],
  event_causality: [],
};
const labels: Record<ClaimSubject, string> = {
  person: "人物",
  event: "事件",
  person_relationship: "人物关系",
  person_event: "事件参与",
  event_causality: "事件因果",
};
const sourceTypes = {
  primary: "原始史料",
  reference: "工具书",
  scholarship: "研究论著",
  digital: "数字资源",
  media: "媒体",
};
export function EditorialPage() {
  const [admin, setAdmin] = useState(false);
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [message, setMessage] = useState("");
  const [tab, setTab] = useState<Table>("topic");
  const [query, setQuery] = useState("");
  const [topics, setTopics] = useState<Topic[]>([]);
  const [sources, setSources] = useState<Source[]>([]);
  const [claims, setClaims] = useState<FactClaim[]>([]);
  const [catalog, setCatalog] = useState<Catalog>(blankCatalog);
  const [topic, setTopic] = useState<Partial<Topic> | null>(null);
  const [source, setSource] = useState<Partial<Source> | null>(null);
  const [claim, setClaim] = useState<Partial<FactClaim> | null>(null);
  const load = async () => {
    const [t, s, c, p, e, pr, pe, ec] = await Promise.all([
      apiFetch<Topic[]>("/editorial/topic", { auth: true }),
      apiFetch<Source[]>("/editorial/source", { auth: true }),
      apiFetch<FactClaim[]>("/editorial/fact_claim", { auth: true }),
      apiFetch<Person[]>("/editorial/person", { auth: true }),
      apiFetch<Event[]>("/editorial/event", { auth: true }),
      apiFetch<PersonRelationship[]>("/editorial/person_relationship", {
        auth: true,
      }),
      apiFetch<PersonEventRelation[]>("/editorial/person_event", {
        auth: true,
      }),
      apiFetch<EventCausalityRelation[]>("/editorial/event_causality", {
        auth: true,
      }),
    ]);
    setTopics(t);
    setSources(s);
    setClaims(c);
    setCatalog({
      person: p,
      event: e,
      person_relationship: pr,
      person_event: pe,
      event_causality: ec,
    });
  };
  useEffect(() => {
    let active = true;
    getCurrentUserRole()
      .then(async (role) => {
        if (!active) return;
        setAdmin(role === "admin");
        if (role === "admin") await load();
      })
      .catch((e) => {
        if (active) setError(e.message);
      })
      .finally(() => {
        if (active) setLoading(false);
      });
    return () => {
      active = false;
    };
  }, []);
  const run = async (action: () => Promise<void>) => {
    setBusy(true);
    setError("");
    setMessage("");
    try {
      await action();
    } catch (e) {
      setError(e instanceof Error ? e.message : "操作失败");
    } finally {
      setBusy(false);
    }
  };
  const save = (table: Table, row: Partial<Topic | Source | FactClaim>) =>
    run(async () => {
      await apiFetch(`/editorial/${table}${row.id ? `/${row.id}` : ""}`, {
        auth: true,
        method: row.id ? "PATCH" : "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(row),
      });
      setTopic(null);
      setSource(null);
      setClaim(null);
      await load();
      setMessage("已保存。已发布内容会出现在公开页面，草稿仅在后台显示。");
    });
  const remove = (table: Table, id: string) => {
    if (confirm("确定删除这条记录吗？"))
      void run(async () => {
        await apiFetch(`/editorial/${table}/${id}`, {
          auth: true,
          method: "DELETE",
        });
        await load();
      });
  };
  const personName = (id: string) =>
    catalog.person.find((p) => p.id === id)?.name || "人物已移除";
  const eventName = (id: string) =>
    catalog.event.find((e) => e.id === id)?.title || "事件已移除";
  const subjectOptions = (subject: string): { id: string; label: string }[] => {
    switch (subject) {
      case "person":
        return catalog.person.map((n) => ({ id: n.id, label: n.name }));
      case "event":
        return catalog.event.map((n) => ({ id: n.id, label: n.title }));
      case "person_relationship":
        return catalog.person_relationship.map((r) => ({
          id: r.id,
          label: relationshipSentence(personName(r.person_a), personName(r.person_b), r.relation_type),
        }));
      case "person_event":
        return catalog.person_event.map((r) => ({
          id: r.id,
          label: `${personName(r.person_id)} → ${r.role} → ${eventName(r.event_id)}`,
        }));
      case "event_causality":
        return catalog.event_causality.map((r) => ({
          id: r.id,
          label: `${eventName(r.cause_event_id)} → ${eventName(r.effect_event_id)}`,
        }));
      default:
        return [];
    }
  };
  const field = (
    label: string,
    value: string | undefined,
    onChange: (v: string) => void,
    multiline = false,
  ) => (
    <label className="block text-sm text-slate-600">
      {label}
      {multiline ? (
        <textarea
          className="reading-input mt-1"
          rows={4}
          value={value || ""}
          onChange={(e) => onChange(e.target.value)}
        />
      ) : (
        <input
          className="reading-input mt-1"
          value={value || ""}
          onChange={(e) => onChange(e.target.value)}
        />
      )}
    </label>
  );
  const actions = (onSave: () => void, onCancel: () => void) => (
    <div className="flex gap-3 pt-3">
      <button
        disabled={busy}
        type="submit"
        onClick={onSave}
        className="px-6 py-2 rounded-xl bg-teal-800 text-white"
      >
        {busy ? "保存中…" : "保存"}
      </button>
      <button disabled={busy} onClick={onCancel} className="px-4 py-2">
        取消
      </button>
    </div>
  );
  if (loading) return <p className="py-16">加载管理台…</p>;
  if (!admin)
    return (
      <p role="alert" className="py-16">
        {error || "请先使用管理员账号登录，再进入管理台。"}
      </p>
    );
  const newItem = () => {
    setError("");
    setMessage("");
    if (tab === "topic")
      setTopic({
        status: "draft",
        sections: [{ heading: "", body: "", node_ids: [] }],
      });
    if (tab === "source") setSource({ source_type: "primary" });
    if (tab === "fact_claim")
      setClaim({
        subject_table: "person",
        field_path: "biography",
        status: "draft",
      });
  };
  const rows = (
    tab === "topic" ? topics : tab === "source" ? sources : claims
  ).filter((row) =>
    ("claim_text" in row ? row.claim_text : row.title).includes(query),
  );
  const nodes = [
    ...catalog.person.map((p) => ({
      id: p.id,
      title: p.name,
      status: p.status,
    })),
    ...catalog.event.map((e) => ({
      id: e.id,
      title: e.title,
      status: e.status,
    })),
  ];
  return (
    <div className="space-y-6">
      <Link to="/admin" className="text-teal-700 text-sm">
        ← 人物、事件与关系管理
      </Link>
      <h1 className="font-serif text-3xl">专题与出处管理</h1>
      <p className="text-sm text-slate-500">
        先保存人物和事件，再编排专题。为具体陈述或关系选择来源，并填写卷、篇或页码。
      </p>
      {error && (
        <p role="alert" className="bg-rose-50 text-rose-700 p-4 rounded-xl">
          {error}
        </p>
      )}
      {message && (
        <p role="status" className="bg-teal-50 text-teal-800 p-4 rounded-xl">
          {message}
        </p>
      )}
      <div className="flex flex-wrap gap-2">
        {(
          [
            ["topic", "专题"],
            ["source", "来源库"],
            ["fact_claim", "陈述与引用"],
          ] as const
        ).map(([value, label]) => (
          <button
            disabled={busy}
            key={value}
            onClick={() => {
              setTab(value);
              setTopic(null);
              setSource(null);
              setClaim(null);
              setQuery("");
            }}
            className={`px-5 py-2 rounded-xl ${tab === value ? "bg-teal-800 text-white" : "bg-white border"}`}
          >
            {label}
          </button>
        ))}
      </div>
      {topic && (
        <section className="reading-card space-y-4">
          <h2 className="text-xl font-semibold">
            {topic.id ? "编辑" : "新增"}专题
          </h2>
          {field("标题", topic.title, (title) => setTopic({ ...topic, title }))}
          {field("专题地址（如 liang-jin）", topic.slug, (slug) =>
            setTopic({ ...topic, slug }),
          )}
          {field(
            "导读",
            topic.description,
            (description) => setTopic({ ...topic, description }),
            true,
          )}
          <PublicationField
            value={topic.status}
            onChange={(status) => setTopic({ ...topic, status })}
          />
          {topic.sections?.map((section, index) => {
            const update = (next: typeof section) =>
              setTopic({
                ...topic,
                sections: topic.sections!.map((s, i) =>
                  i === index ? next : s,
                ),
              });
            return (
              <div key={index} className="border rounded-xl p-4 space-y-3">
                <h3 className="font-semibold">章节 {index + 1}</h3>
                {field("章节标题", section.heading, (heading) =>
                  update({ ...section, heading }),
                )}
                {field(
                  "正文",
                  section.body,
                  (body) => update({ ...section, body }),
                  true,
                )}
                <p className="text-sm text-slate-600">
                  关联阅读（按勾选顺序排列）
                </p>
                <div className="max-h-48 overflow-y-auto grid sm:grid-cols-2 gap-2">
                  {nodes.map((node) => (
                    <label
                      key={node.id}
                      className="text-sm flex gap-2 items-center"
                    >
                      <input
                        type="checkbox"
                        checked={section.node_ids.includes(node.id)}
                        onChange={(e) =>
                          update({
                            ...section,
                            node_ids: e.target.checked
                              ? [...section.node_ids, node.id]
                              : section.node_ids.filter((id) => id !== node.id),
                          })
                        }
                      />
                      {node.title} ·{" "}
                      {node.status === "published" ? "已发布" : "草稿"}
                    </label>
                  ))}
                </div>
                <div className="flex gap-4 text-sm">
                  <button
                    disabled={index === 0}
                    onClick={() => {
                      const sections = [...topic.sections!];
                      [sections[index - 1], sections[index]] = [
                        sections[index],
                        sections[index - 1],
                      ];
                      setTopic({ ...topic, sections });
                    }}
                  >
                    ↑ 上移
                  </button>
                  <button
                    onClick={() =>
                      setTopic({
                        ...topic,
                        sections: topic.sections!.filter((_, i) => i !== index),
                      })
                    }
                    className="text-rose-700"
                  >
                    删除章节
                  </button>
                </div>
              </div>
            );
          })}
          <button
            className="text-teal-700"
            onClick={() =>
              setTopic({
                ...topic,
                sections: [
                  ...(topic.sections ?? []),
                  { heading: "", body: "", node_ids: [] },
                ],
              })
            }
          >
            ＋ 添加章节
          </button>
          {actions(
            () => void save("topic", topic),
            () => setTopic(null),
          )}
        </section>
      )}
      {source && (
        <section className="reading-card space-y-4">
          <h2 className="text-xl font-semibold">
            {source.id ? "编辑" : "新增"}来源
          </h2>
          {field("书名／资料标题", source.title, (title) =>
            setSource({ ...source, title }),
          )}
          <label className="block text-sm">
            来源类型
            <select
              className="reading-input mt-1"
              value={source.source_type}
              onChange={(e) =>
                setSource({
                  ...source,
                  source_type: e.target.value as Source["source_type"],
                })
              }
            >
              {Object.entries(sourceTypes).map(([v, l]) => (
                <option key={v} value={v}>
                  {l}
                </option>
              ))}
            </select>
          </label>
          {field("作者", source.author, (author) =>
            setSource({ ...source, author }),
          )}
          {field("版本", source.edition, (edition) =>
            setSource({ ...source, edition }),
          )}
          {field("链接（可选）", source.url, (url) =>
            setSource({ ...source, url }),
          )}
          {field(
            "说明",
            source.note,
            (note) => setSource({ ...source, note }),
            true,
          )}
          {actions(
            () => void save("source", source),
            () => setSource(null),
          )}
        </section>
      )}
      {claim && (
        <section className="reading-card space-y-4">
          <h2 className="text-xl font-semibold">
            {claim.id ? "编辑" : "新增"}陈述与引用
          </h2>
          <label className="block text-sm">
            挂载对象类型
            <select
              className="reading-input mt-1"
              value={claim.subject_table}
              onChange={(e) =>
                setClaim({
                  ...claim,
                  subject_table: e.target.value,
                  subject_id: "",
                  field_path:
                    e.target.value === "person" ? "biography" : "description",
                })
              }
            >
              {Object.entries(labels).map(([value, label]) => (
                <option key={value} value={value}>
                  {label}
                </option>
              ))}
            </select>
          </label>
          <label className="block text-sm">
            具体条目或关系
            <select
              className="reading-input mt-1"
              value={claim.subject_id || ""}
              onChange={(e) =>
                setClaim({ ...claim, subject_id: e.target.value })
              }
            >
              <option value="">请选择</option>
              {subjectOptions(claim.subject_table || "").map((o) => (
                <option key={o.id} value={o.id}>
                  {o.label}
                </option>
              ))}
            </select>
          </label>
          {field(
            "对应字段（如 biography、description）",
            claim.field_path,
            (field_path) => setClaim({ ...claim, field_path }),
          )}
          {field(
            "具体陈述",
            claim.claim_text,
            (claim_text) => setClaim({ ...claim, claim_text }),
            true,
          )}
          <label className="block text-sm">
            来源
            <select
              className="reading-input mt-1"
              aria-label="来源"
              value={claim.source_id || ""}
              onChange={(e) =>
                setClaim({ ...claim, source_id: e.target.value })
              }
            >
              <option value="">请选择来源</option>
              {sources.map((s) => (
                <option value={s.id} key={s.id}>
                  {s.title}
                  {s.edition ? ` · ${s.edition}` : ""}
                </option>
              ))}
            </select>
          </label>
          {field("定位（卷、篇、章节或页码）", claim.citation, (citation) =>
            setClaim({ ...claim, citation }),
          )}
          {field(
            "解释／争议说明",
            claim.note,
            (note) => setClaim({ ...claim, note }),
            true,
          )}
          <PublicationField
            value={claim.status}
            onChange={(status) => setClaim({ ...claim, status })}
          />
          {actions(
            () => void save("fact_claim", claim),
            () => setClaim(null),
          )}
        </section>
      )}
      <div className="flex gap-3">
        <input
          aria-label="筛选管理记录"
          placeholder="按标题或陈述筛选…"
          className="reading-input"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
        />
        <button
          disabled={busy}
          className="shrink-0 px-5 py-2 bg-teal-800 text-white rounded-xl"
          onClick={newItem}
        >
          ＋ 新增
        </button>
      </div>
      <div className="space-y-3">
        {rows.map((row) => (
          <div
            key={row.id}
            className="reading-card flex flex-wrap items-center justify-between gap-4"
          >
            <div className="min-w-0 flex-1">
              <p className="font-medium">
                {"claim_text" in row ? row.claim_text : row.title}
              </p>
              <p className="text-xs text-slate-500 mt-2">
                {"source_type" in row
                  ? sourceTypes[row.source_type]
                  : row.status === "published"
                    ? "已发布"
                    : "草稿"}
                {"subject_table" in row &&
                  ` · ${subjectOptions(row.subject_table).find((o) => o.id === row.subject_id)?.label || "关联对象已移除"}`}
              </p>
              {"slug" in row && row.status === "published" && (
                <Link
                  to={`/topics/${row.slug}`}
                  className="text-sm text-teal-700"
                >
                  查看专题 →
                </Link>
              )}
            </div>
            <div className="flex gap-4 text-sm">
              <button
                disabled={busy}
                onClick={() => {
                  if (tab === "topic") setTopic(row as Topic);
                  if (tab === "source") setSource(row as Source);
                  if (tab === "fact_claim") setClaim(row as FactClaim);
                  window.scrollTo(0, 0);
                }}
              >
                编辑
              </button>
              <button
                disabled={busy}
                className="text-rose-700"
                onClick={() => remove(tab, row.id)}
              >
                删除
              </button>
            </div>
          </div>
        ))}
        {rows.length === 0 && (
          <p className="text-slate-500 py-8 text-center">没有匹配的记录。</p>
        )}
      </div>
    </div>
  );
}
