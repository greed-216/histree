import type { PublicationStatus } from "@histree/shared-types";
export function PublicationField({
  value,
  onChange,
}: {
  value?: PublicationStatus;
  onChange: (v: PublicationStatus) => void;
}) {
  return (
    <label className="block text-sm text-slate-600">
      发布状态
      <select
        className="block w-full p-2 mt-1 border rounded-lg bg-white"
        value={value ?? "draft"}
        onChange={(e) => onChange(e.target.value as PublicationStatus)}
      >
        <option value="draft">草稿 · 仅管理员可见</option>
        <option value="published">已发布 · 公开可见</option>
      </select>
    </label>
  );
}
