import { useEffect, useState } from 'react';
import { Loader2, Plus, Save, Trash2 } from 'lucide-react';
import { api } from '../lib/api';
import { useAgent } from '../context/AgentContext';
import Button from '../components/Button';
import TextField, { TextArea } from '../components/TextField';

const blank = { title: '', body: '', linked_tools: '', version: '1', active: true };

export default function SkillsScreen() {
  const { agentId } = useAgent();
  const [skills, setSkills] = useState(null);
  const [selected, setSelected] = useState(null);
  const [draft, setDraft] = useState(blank);
  const [saving, setSaving] = useState(false);

  const load = () => api.get('/skills', undefined, agentId).then((r) => setSkills(r.results));

  useEffect(() => { load(); }, [agentId]);

  const edit = (skill) => {
    setSelected(skill);
    setDraft({
      title: skill.title,
      body: skill.body,
      linked_tools: skill.linked_tools.join(', '),
      version: skill.version,
      active: skill.active,
    });
  };

  const save = async () => {
    setSaving(true);
    const payload = {
      title: draft.title,
      body: draft.body,
      linked_tools: draft.linked_tools.split(',').map((item) => item.trim()).filter(Boolean),
      version: draft.version || '1',
      active: draft.active,
    };
    try {
      if (selected?.id) await api.patch(`/skills/${selected.id}`, payload, undefined, agentId);
      else await api.post('/skills', payload, undefined, agentId);
      setSelected(null);
      setDraft(blank);
      await load();
    } finally {
      setSaving(false);
    }
  };

  const remove = async () => {
    if (!selected?.id) return;
    await api.del(`/skills/${selected.id}`, undefined, agentId);
    setSelected(null);
    setDraft(blank);
    await load();
  };

  return <div className="p-5 md:p-8">
    <div className="mb-5 flex items-center justify-between">
      <h1 className="text-lg font-medium text-text">Skills</h1>
      <Button onClick={() => { setSelected(null); setDraft(blank); }}><Plus size={15} /> New Skill</Button>
    </div>
    <div className="grid gap-5 lg:grid-cols-[320px_1fr]">
      <section className="rounded-lg border border-border bg-surface">
        {skills === null ? <div className="flex items-center gap-2 p-4 text-sm text-muted"><Loader2 size={14} className="animate-spin" /> Loading skills...</div> :
          skills.length ? skills.map((skill) => <button key={skill.id} onClick={() => edit(skill)} className={`block w-full border-b border-border px-4 py-3 text-left text-sm hover:bg-white/[0.04] ${selected?.id === skill.id ? 'bg-white/[0.06]' : ''}`}>
            <span className="block font-medium text-text">{skill.title}</span>
            <span className="mt-1 block text-xs text-muted">{skill.linked_tools.join(', ') || 'No linked tools'} - v{skill.version} - {skill.active ? 'active' : 'inactive'}</span>
          </button>) : <p className="p-4 text-sm text-muted">No skills yet.</p>}
      </section>
      <section className="rounded-lg border border-border bg-surface p-4">
        <div className="grid gap-4">
          <TextField label="Title" value={draft.title} onChange={(event) => setDraft({ ...draft, title: event.target.value })} />
          <TextArea label="Body" rows={12} value={draft.body} onChange={(event) => setDraft({ ...draft, body: event.target.value })} />
          <TextField label="Linked tool ids" value={draft.linked_tools} onChange={(event) => setDraft({ ...draft, linked_tools: event.target.value })} placeholder="tool.id, another.tool" />
          <TextField label="Version" value={draft.version} onChange={(event) => setDraft({ ...draft, version: event.target.value })} />
          <label className="flex items-center gap-2 text-sm text-text"><input type="checkbox" checked={draft.active} onChange={(event) => setDraft({ ...draft, active: event.target.checked })} /> Active</label>
          <div className="flex justify-end gap-2">
            {selected?.id && <Button variant="danger" onClick={remove}><Trash2 size={14} /> Delete</Button>}
            <Button onClick={save} disabled={saving || !draft.title.trim() || !draft.body.trim()}>{saving ? <Loader2 size={14} className="animate-spin" /> : <Save size={14} />} Save skill</Button>
          </div>
        </div>
      </section>
    </div>
  </div>;
}
