'use client';

import { FormEvent, useEffect, useState } from 'react';
import { savedSchema, SavedComparison, ViewMode } from '../modules/comparison/domain/envelope';
import { Result } from './result';
import { format } from './format';
import { newRequestId } from './request-id';

type Identity = { user: { id: string; email: string }; csrf: string };
type History = { items: { id: string; created_at: string; view_mode: string; documents: { role: string; filename: string }[]; state: string; index: number | null; policy: string }[]; page: number; has_next: boolean };
async function readResponse(response: Response) {
  let value;
  try { value = await response.json(); }
  catch { throw new Error('Resposta inválida. Se houve envio, a operação pode continuar no servidor.'); }
  if (!response.ok) {
    if (response.status === 401) window.dispatchEvent(new Event('hts-session-expired'));
    throw new Error(value.detail ?? 'Não foi possível concluir a operação.');
  }
  return value;
}
function upload(form: FormData, csrf: string, processing: () => void): Promise<unknown> {
  return new Promise((resolve, reject) => {
    const xhr = new XMLHttpRequest();
    xhr.open('POST', '/api/comparisons');
    xhr.setRequestHeader('x-hts-request', '1'); xhr.setRequestHeader('x-csrf-token', csrf);
    xhr.timeout = 240000;
    xhr.upload.onload = processing;
    xhr.onerror = () => reject(new Error('Conexão perdida. A operação pode continuar no servidor; uma retentativa preservará o identificador.'));
    xhr.ontimeout = () => reject(new Error('Prazo de resposta excedido. Isso não confirma cancelamento no servidor; tente novamente com a mesma entrada.'));
    xhr.onload = () => {
      if (xhr.status === 401) window.dispatchEvent(new Event('hts-session-expired'));
      try { const value = JSON.parse(xhr.responseText); if (xhr.status < 200 || xhr.status >= 300) reject(new Error(value.detail ?? 'Falha na comparação.')); else resolve(value); }
      catch { reject(new Error('Resposta inválida; não foi possível confirmar a conclusão.')); }
    };
    xhr.send(form);
  });
}
export function Workspace({ initialId }: { initialId?: string }) {
  const [identity, setIdentity] = useState<Identity | null>(null), [checking, setChecking] = useState(true);
  const [authMode, setAuthMode] = useState<'login' | 'register'>('login');
  const [busy, setBusy] = useState(''), [error, setError] = useState('');
  const [inputMode, setInputMode] = useState<'files' | 'text'>('files'), [method, setMethod] = useState<ViewMode>('hybrid');
  const [view, setView] = useState<'input' | 'history' | 'result'>(initialId ? 'result' : 'input');
  const [saved, setSaved] = useState<SavedComparison | null>(null), [history, setHistory] = useState<History | null>(null);
  const [requestId, setRequestId] = useState<string | null>(null), [clientMs, setClientMs] = useState<number | null>(null);
  useEffect(() => {
    const expired = () => { setIdentity(null); setSaved(null); setHistory(null); setView('input'); setError('Sessão inválida ou expirada; entre novamente.'); };
    window.addEventListener('hts-session-expired', expired);
    return () => window.removeEventListener('hts-session-expired', expired);
  }, []);
  useEffect(() => {
    let active = true;
    fetch('/api/auth/session', { cache: 'no-store' }).then(async response => {
      if (response.status === 401) return null;
      return readResponse(response);
    }).then(value => { if (active) setIdentity(value); }).catch(() => { if (active) setError('Não foi possível verificar a sessão; confira se os serviços estão disponíveis.'); })
      .finally(() => { if (active) setChecking(false); });
    return () => { active = false; };
  }, []);
  useEffect(() => {
    if (!identity || !initialId) return;
    let active = true;
    fetch('/api/comparisons/' + encodeURIComponent(initialId), { cache: 'no-store' }).then(readResponse).then(value => {
      if (active) { setSaved(savedSchema.parse(value)); setView('result'); }
    }).catch(error => { if (active) setError(error.message); });
    return () => { active = false; };
  }, [identity?.user.id, initialId]);
  async function auth(event: FormEvent<HTMLFormElement>) {
    event.preventDefault(); setBusy('Verificando credenciais…'); setError('');
    const form = new FormData(event.currentTarget), element = event.currentTarget;
    try {
      const value = await fetch('/api/auth/' + authMode, { method: 'POST', headers: { 'content-type': 'application/json', 'x-hts-request': '1' },
        body: JSON.stringify({ email: form.get('email'), password: form.get('password') }) }).then(readResponse);
      element.reset(); setIdentity(value);
    } catch (error) { setError(error instanceof Error ? error.message : 'Falha na autenticação.'); }
    finally { setBusy(''); }
  }
  async function logout() {
    if (!identity) return;
    setError(''); setBusy('Encerrando sessão…');
    try {
      await fetch('/api/auth/logout', { method: 'POST', headers: { 'x-hts-request': '1', 'x-csrf-token': identity.csrf } }).then(readResponse);
      setIdentity(null); setSaved(null); setHistory(null); setView('input'); setRequestId(null);
      window.history.replaceState(null, '', '/');
    } catch (error) { setError(error instanceof Error ? error.message : 'Não foi possível confirmar o logout.'); }
    finally { setBusy(''); }
  }
  async function compare(event: FormEvent<HTMLFormElement>) {
    event.preventDefault(); if (!identity) return;
    const form = new FormData(event.currentTarget);
    let id: string;
    try { id = requestId ?? newRequestId(); }
    catch { setError('Este navegador não disponibiliza o gerador seguro de identificadores.'); return; }
    form.set('contract_version', '1.0'); form.set('mode', method); form.set('request_id', id);
    setRequestId(id); setBusy('Enviando entrada…'); setError('');
    const started = performance.now();
    try {
      const value = savedSchema.parse(await upload(form, identity.csrf, () => setBusy('Processando no servidor…')));
      setClientMs(performance.now() - started); setSaved(value); setView('result'); setRequestId(null);
      window.history.replaceState(null, '', '/results/' + value.id);
    } catch (error) { setError(error instanceof Error ? error.message : 'Falha na comparação.'); }
    finally { setBusy(''); }
  }
  async function loadHistory(page = 1) {
    setBusy('Consultando histórico…'); setError(''); setView('history');
    try { setHistory(await fetch('/api/comparisons?page=' + page, { cache: 'no-store' }).then(readResponse)); }
    catch (error) { setError(error instanceof Error ? error.message : 'Histórico indisponível.'); }
    finally { setBusy(''); }
  }
  return <><header className="app-header no-print"><a href="/" className="brand">HTS <span>Comparação de conteúdo</span></a>
    {identity && <nav aria-label="Navegação principal"><button onClick={() => { setView('input'); setError(''); }} disabled={!!busy}>Nova comparação</button><button onClick={() => loadHistory()} disabled={!!busy}>Histórico</button><span>{identity.user.email}</span><button className="secondary" onClick={logout} disabled={!!busy}>Sair</button></nav>}</header>
    <main className="mx-auto w-full max-w-6xl p-5"><div className="no-print">{checking && <p role="status">Verificando sessão…</p>}{error && <p role="alert" className="error">{error}</p>}{busy && <p role="status" aria-live="polite" className="progress"><span className="spinner" aria-hidden="true" />{busy} O indicador é indeterminado.</p>}</div>
      {!checking && !identity && <section className="auth-card no-print"><p className="eyebrow">Execução local · PT-BR</p><h1>{authMode === 'register' ? 'Criar conta local' : 'Entrar'}</h1><p>Compare dois conteúdos e consulte somente o seu histórico. Similaridade não é uma conclusão de plágio.</p>
        <form onSubmit={auth}><label>E-mail<input name="email" type="email" autoComplete="username" required maxLength={254} /></label><label>Senha<input name="password" type="password" autoComplete={authMode === 'register' ? 'new-password' : 'current-password'} required minLength={12} maxLength={128} /></label>
          <p className="muted">De 12 a 128 caracteres, sem truncamento. Não há recuperação por e-mail nem “lembrar de mim”.</p><button type="submit" disabled={!!busy}>{authMode === 'register' ? 'Cadastrar e entrar' : 'Entrar'}</button></form>
        <button className="link-button" disabled={!!busy} onClick={() => { setAuthMode(authMode === 'login' ? 'register' : 'login'); setError(''); }}>{authMode === 'login' ? 'Criar conta' : 'Já tenho conta'}</button></section>}
      {identity && <div className="private-content">{view === 'input' && <section className="input-card no-print"><p className="eyebrow">Dois conteúdos · unidade sentença</p><h1>Nova comparação</h1><p>Identifique a fonte e o documento analisado. PDF com texto, DOCX ou TXT. Sem OCR ou busca online.</p>
        <div className="toolbar" aria-label="Tipo de entrada"><button aria-pressed={inputMode === 'files'} className="secondary" onClick={() => { setInputMode('files'); setRequestId(null); }} disabled={!!busy}>Dois arquivos</button><button aria-pressed={inputMode === 'text'} className="secondary" onClick={() => { setInputMode('text'); setRequestId(null); }} disabled={!!busy}>Texto colado</button></div>
        <form onSubmit={compare} onChange={() => setRequestId(null)}><fieldset disabled={!!busy}><legend className="sr-only">Entrada dos conteúdos</legend><div className="two-columns">
          {inputMode === 'files' ? <><label>Arquivo fonte<input type="file" name="source" accept=".pdf,.docx,.txt" required /></label><label>Arquivo analisado<input type="file" name="suspect" accept=".pdf,.docx,.txt" required /></label></> : <><label>Texto fonte<textarea name="source_text" required rows={10} /></label><label>Texto analisado<textarea name="suspect_text" required rows={10} /></label></>}
        </div><label>Método / apresentação<select value={method} onChange={event => setMethod(event.target.value as ViewMode)}><option value="hybrid">Híbrido — índice e correspondências</option><option value="lexical">Lexical TF-IDF — comparação separada</option><option value="semantic">Semântico — baseline C_op, com diagnósticos</option><option value="all">Rodar todos — pipeline compartilhado e diagnósticos por par</option></select></label>
          <p>Limites do core: 5 MiB por arquivo, 30.000 caracteres por documento e 120 sentenças. Entradas vazias são recusadas. Vetor lexical nulo legítimo é zero sinalizado; ausência técnica não é nota zero.</p><button type="submit">Comparar conteúdos</button></fieldset></form>
      </section>}
      {view === 'history' && <section className="no-print"><p className="eyebrow">Somente suas comparações</p><h1>Histórico</h1>{history && <>{!history.items.length ? <p>Nenhuma comparação nesta página. Dados legados sem proprietário não são atribuídos a esta conta.</p> : <div className="table-scroll"><table><thead><tr><th>Data</th><th>Documentos</th><th>Método</th><th>Índice / estado</th><th>Resultado</th></tr></thead><tbody>{history.items.map(item => <tr key={item.id}><td>{new Date(item.created_at).toLocaleString('pt-BR')}</td><td>{item.documents.map(doc => <p key={doc.role}>{doc.role === 'source' ? 'Fonte' : 'Analisado'}: {doc.filename}</p>)}</td><td>{item.view_mode} · {item.policy}</td><td>{item.index === null ? 'Indisponível' : format(item.index)} / {item.state}</td><td><a href={'/results/' + item.id}>Abrir resultado</a></td></tr>)}</tbody></table></div>}
        <div className="toolbar"><button className="secondary" disabled={!!busy || history.page <= 1} onClick={() => loadHistory(history.page - 1)}>Página anterior</button><span>Página {history.page}</span><button className="secondary" disabled={!!busy || !history.has_next} onClick={() => loadHistory(history.page + 1)}>Próxima página</button></div></>}</section>}
      {view === 'result' && (saved ? <Result key={saved.id} saved={saved} clientMs={clientMs} /> : <p>Aguardando consulta autorizada do resultado.</p>)}</div>}
    </main><footer className="app-footer no-print">Pesquisa em desenvolvimento. Índices e classes são operacionais; não comprovam autoria, intenção, plágio ou originalidade.</footer></>;
}
