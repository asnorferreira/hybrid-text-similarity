'use client';

import { useState } from 'react';
import { SavedComparison } from '../modules/comparison/domain/envelope';
import { format, labels, reasons } from './format';

const characterInfo: Record<string, string> = {
  levenshtein: '1 − distância/max(comprimentos); sensível a maiúsculas',
  osa: '1 − distância OSA/max(comprimentos); transposições restritas, não irrestrita',
  jaro: 'Janela max(0,⌊max(m,n)/2⌋−1); transposições/2',
  jaro_winkler: 'Jaro + prefixo comum até 4, fator 0,1; sem corte adicional',
  smith_waterman: 'Máximo local/(2·menor comprimento); match 2, mismatch −1, gap −1',
  ngram: 'Dice de conjuntos de trigramas de caracteres; texto curto usa o texto inteiro',
  vsm_cosine: 'Cosseno de contagens de termos do perfil lexical, sem IDF',
};
const stageNames: Record<string, string> = { resources: 'acesso/preparação de recursos', compare: 'compare total', parse: 'parsing, limpeza e serialização da extração',
  preprocess: 'pré-processamento', lexical: 'léxico e assinaturas', embeddings: 'embeddings e pooling',
  matrices: 'matrizes, fusão e índices', alignment: 'alinhamento', pairs: 'pares, caracteres e classes' };

export function Result({ saved, clientMs }: { saved: SavedComparison; clientMs: number | null }) {
  const result = saved.result;
  const [pair, setPair] = useState({ i: 0, j: 0 });
  const [matrixName, setMatrixName] = useState<keyof typeof result.matrices>(result.matrices.fused ? 'fused' : 'lexical');
  const [rowStart, setRowStart] = useState(0), [colStart, setColStart] = useState(0);
  const matrix = result.matrices[matrixName];
  const index = saved.view_mode === 'semantic' ? result.semantic_index : saved.view_mode === 'lexical' ? result.lexical_index : result.index;
  const chosen = result.matches?.find(match => match.source === pair.i && match.suspect === pair.j);
  const model = result.metadata.model;
  const select = (i: number, j: number) => { setPair({ i, j }); setRowStart(Math.floor(i / 6) * 6); setColStart(Math.floor(j / 8) * 8); };
  const methods = [
    { name: 'Lexical TF-IDF', value: result.lexical_index, unit: 'Documento: máximos lexicais por sentença, ponderados por palavras nos dois sentidos', norm: 'TF-IDF suavizado; cosseno [0,1]' },
    { name: 'Semântico', value: result.semantic_index, unit: 'Documento: máximos de C_op por sentença, com a mesma ponderação', norm: 'C bruto [-1,1]; índice usa C_op = max(0,C)' },
    { name: 'Híbrido', value: result.method === 'hybrid' ? result.index : null, unit: 'Documento: máximos de F por sentença, com a mesma ponderação', norm: 'F = 0,6·C_op + 0,4·L; índice [0,100]' },
  ];
  return <article className="report" aria-label="Relatório da comparação">
    <div className="report-title"><div><p className="eyebrow">Comparação persistida · {saved.view_mode}</p><h1>Relações entre os conteúdos</h1></div>
      <button className="no-print secondary" onClick={() => window.print()}>Imprimir relatório</button></div>
    <p className="muted">{new Date(saved.created_at).toLocaleString('pt-BR')} · ID {saved.id}</p>
    <div className="document-names">{saved.documents.map(doc => <p key={doc.role}><strong>{doc.role === 'source' ? 'Fonte' : 'Documento analisado'}:</strong> {doc.filename}</p>)}</div>
    <section className="score-panel" aria-label="Índice de similaridade"><div><h2>Índice de similaridade {saved.view_mode === 'lexical' ? 'lexical' : saved.view_mode === 'semantic' ? 'semântico' : 'híbrido'}</h2>
      <p className="big-score" data-testid="similarity-index">{index ? format(index.value) + ' / 100' : 'Indisponível'}</p></div>
      <div>{index && <><p>Fonte → analisado: <strong>{format(index.source_to_suspect)}</strong></p><p>Analisado → fonte: <strong>{format(index.suspect_to_source)}</strong></p></>}
        <p>Direções em [0,1]; nota simétrica em [0,100]. Não é Pearson, Spearman, probabilidade ou percentual de plágio.</p></div></section>
    {result.state === 'resource_unavailable' && <p className="notice" role="status">Recurso semântico indisponível. Híbrido, alinhamento e classes não foram calculados. A comparação lexical separada continua identificada abaixo; ausência não virou zero.</p>}
    <p className="notice">Rótulos provisórios de Q5-V2. “Exata” indica igualdade do texto após limpeza, sem afirmar arquivos idênticos. “Editada” e “paráfrase” são regras operacionais; “sem correspondência detectada” não comprova originalidade. Igualdade textual não força nota 100.</p>
    <p>Limiares desta execução, ainda sem calibração: editada D ≥ {String(result.metadata.configuration.edited_threshold)}; corte max(L,C_op) ≤ {String(result.metadata.configuration.low_threshold)}; paráfrase C_op &gt; {String(result.metadata.configuration.paraphrase_threshold)} após as regras anteriores. L &gt; {String(result.metadata.configuration.lexical_high)} é apenas diagnóstico.</p>
    <section><h2>Métodos e alcance disponível</h2><div className="table-scroll"><table><thead><tr><th>Método</th><th>Índice</th><th>Unidade e agregação</th><th>Normalização</th></tr></thead>
      <tbody>{methods.map(method => <tr key={method.name}><th>{method.name}</th><td>{method.value ? format(method.value.value) : 'Indisponível neste modo/recurso'}</td><td>{method.unit}</td><td>{method.norm}</td></tr>)}</tbody></table></div>
      <p>“Rodar todos” compartilha uma única execução híbrida: compara os três índices já definidos e mostra caracteres dos melhores pares. Não cria índices documentais para algoritmos de caracteres. Limites: 5 MiB por arquivo; 30.000 caracteres por documento; 120 sentenças; 4.000 caracteres por sentença; 12.000 tokens de conteúdo por sentença.</p>
      <p>E2: assinatura adaptada de termos salientes, diagnóstico sem escore contínuo. Igualdade de hash não prova identidade. Fonte: <code>{String((result.metadata.signature.source as { value?: string })?.value ?? 'indisponível')}</code>; analisado: <code>{String((result.metadata.signature.suspect as { value?: string })?.value ?? 'indisponível')}</code>.</p>
    </section>
    <section><h2>Textos comparados lado a lado</h2><p>Sentenças da representação extraída e limpa, em ordem. A limpeza pode juntar quebras de palavra e remover hífen suave; não é anotação sobre o PDF original. A seleção usa índices de ocorrência, inclusive em textos repetidos.</p>
      {saved.engineering.core.filter(item => item.operation === 'extract').map((item, i) => <p className="muted" key={i}>{item.document_role === 'source' ? 'Fonte' : 'Documento analisado'}: {item.extraction ? `${item.extraction.format}; limpeza final ${item.extraction.cleanup_changed ? 'alterou' : 'não alterou'} o texto extraído; hífen suave ${item.extraction.soft_hyphen_observed ? 'observado' : 'não observado'}; quebra após hífen ${item.extraction.hyphen_linebreak_observed ? 'observada (tratamento heurístico, preservando compostos reconhecidos)' : 'não observada'}.` : 'diagnóstico de limpeza não informado pelo core'}</p>)}
      <div className="two-columns texts">{([['source', 'Fonte'], ['suspect', 'Documento analisado']] as const).map(([side, title]) => <section key={side} aria-label={'Sentenças: ' + title}><h3>{title}</h3>
        {result[side].map(sentence => { const match = side === 'suspect' ? result.matches?.find(item => item.suspect === sentence.index) : undefined;
          const selected = sentence.index === (side === 'source' ? pair.i : pair.j);
          return <div key={sentence.index} className={'sentence ' + (selected ? 'selected ' : '') + (match?.decision.label ?? '')}>
            <span className="sentence-id">{side === 'source' ? 'F' : 'A'}{sentence.index + 1}</span><p>{sentence.raw}</p>
            {match && <span className="badge">{labels[match.decision.label]}</span>}
            {sentence.flags.includes('lexical_zero_vector') && <small>Sem representação lexical: zero sinalizado.</small>}</div>; })}</section>)}</div>
    </section>
    <section><h2>Mapa de calor</h2><p>Linhas = fonte; colunas = documento analisado. M = melhor par usado na classificação; H = atribuição exclusiva do húngaro. São seleções diferentes.</p>
      <div className="toolbar no-print"><label>Matriz <select value={matrixName} onChange={event => setMatrixName(event.target.value as typeof matrixName)}>{Object.entries(result.matrices).map(([name, values]) => <option key={name} value={name} disabled={!values}>{({ lexical: 'L lexical [0,1]', semantic_raw: 'C semântico bruto [-1,1]', semantic_operational: 'C_op operacional [0,1]', fused: 'F fundido [0,1]' })[name]}</option>)}</select></label>
        <button className="secondary" disabled={!rowStart} onClick={() => setRowStart(Math.max(0, rowStart - 6))}>Linhas anteriores</button><button className="secondary" disabled={rowStart + 6 >= result.source.length} onClick={() => setRowStart(rowStart + 6)}>Próximas linhas</button>
        <button className="secondary" disabled={!colStart} onClick={() => setColStart(Math.max(0, colStart - 8))}>Colunas anteriores</button><button className="secondary" disabled={colStart + 8 >= result.suspect.length} onClick={() => setColStart(colStart + 8)}>Próximas colunas</button></div>
      <p>Matriz {matrixName}; janela F{rowStart + 1}–F{Math.min(rowStart + 6, result.source.length)}, A{colStart + 1}–A{Math.min(colStart + 8, result.suspect.length)}. A impressão mostra esta janela; a lista de melhores pares abaixo é completa.</p>
      {!matrix ? <p>Esta matriz está indisponível.</p> : <div className="table-scroll"><table className="heatmap"><thead><tr><th>Fonte / analisado</th>{result.suspect.slice(colStart, colStart + 8).map(sentence => <th key={sentence.index}>A{sentence.index + 1}</th>)}</tr></thead>
        <tbody>{result.source.slice(rowStart, rowStart + 6).map(source => <tr key={source.index}><th>F{source.index + 1}</th>{result.suspect.slice(colStart, colStart + 8).map(suspect => {
          const value = matrix[source.index][suspect.index];
          const best = result.matches?.some(match => match.source === source.index && match.suspect === suspect.index);
          const aligned = result.alignment?.pairs.some(match => match.source === source.index && match.suspect === suspect.index);
          return <td key={suspect.index}><button aria-label={`Selecionar F${source.index + 1}, A${suspect.index + 1}, ${format(value)}`} aria-pressed={source.index === pair.i && suspect.index === pair.j}
            style={{ backgroundColor: value < 0 ? `rgba(180,45,45,${Math.abs(value) * .35})` : `rgba(20,100,155,${value * .4})` }} onClick={() => select(source.index, suspect.index)}>{format(value)} {best && 'M'}{aligned && 'H'}</button></td>;
        })}</tr>)}</tbody></table></div>}
      <p>Azul mais intenso: maior valor positivo; vermelho: valor bruto negativo. O número e os marcadores continuam visíveis sem depender da cor.</p>
      <div className="selected-pair"><h3>Par selecionado: F{pair.i + 1} × A{pair.j + 1}</h3><p>{result.source[pair.i]?.raw}</p><p>{result.suspect[pair.j]?.raw}</p>
        <details><summary>Representações usadas nos cálculos deste par</summary><p>Semântico fonte: {result.source[pair.i]?.semantic}</p><p>Semântico analisado: {result.suspect[pair.j]?.semantic}</p><p>Termos lexicais fonte: {result.source[pair.i]?.lexical.join(', ') || 'sem termos'}</p><p>Termos lexicais analisado: {result.suspect[pair.j]?.lexical.join(', ') || 'sem termos'}</p></details>
        {chosen ? <><p><strong>{labels[chosen.decision.label]}</strong> — {reasons[chosen.decision.reason] ?? chosen.decision.reason}</p><p>L={format(chosen.lexical)}, C bruto={format(chosen.semantic_raw)}, C_op={format(chosen.semantic_operational)}, F={format(chosen.fused)}. L alto é somente diagnóstico.</p>
          <div className="table-scroll"><table><caption>Algoritmos no melhor par selecionado; similaridades [0,1], sem agregação documental</caption><thead><tr><th>Algoritmo</th><th>Valor</th><th>Configuração</th></tr></thead><tbody>{Object.entries(chosen.characters).map(([name, value]) => <tr key={name}><th>{name === 'osa' ? 'OSA restrita' : name}</th><td>{format(value)}</td><td>{characterInfo[name] ?? 'Configuração versionada no core'}</td></tr>)}</tbody></table></div></> : <p>Não há classe/caracteres calculados para este par neste modo: a classificação usa somente o melhor F de cada sentença analisada.</p>}</div>
    </section>
    <section><h2>Melhores pares e classes por sentença</h2>{!result.matches ? <p>Classes indisponíveis neste modo/recurso.</p> : <div className="table-scroll matches"><table><thead><tr><th>Par</th><th>Classe</th><th>Motivo</th><th>L</th><th>C bruto</th><th>C_op</th><th>F</th></tr></thead><tbody>{result.matches.map(match => <tr key={match.suspect}><td><button className="link-button" onClick={() => select(match.source, match.suspect)}>F{match.source + 1} → A{match.suspect + 1}</button></td><td>{labels[match.decision.label]}</td><td>{reasons[match.decision.reason] ?? match.decision.reason}</td><td>{format(match.lexical)}</td><td>{format(match.semantic_raw)}</td><td>{format(match.semantic_operational)}</td><td>{format(match.fused)}</td></tr>)}</tbody></table></div>}
      {result.alignment && <p>Húngaro explicativo: soma não ponderada {format(result.alignment.objective)}; {result.alignment.pairs.map(p => `F${p.source + 1}↔A${p.suspect + 1}`).join(', ') || 'nenhum par positivo'}. Sem par exclusivo: {result.alignment.unmatched_source.length} na fonte e {result.alignment.unmatched_suspect.length} no analisado. Não determina a nota ou as classes.</p>}
    </section>
    <section><h2>Resumo do documento analisado</h2>{result.summary ? <><p>Denominador: {result.summary.denominator} sentenças. Predominância: <strong>{labels[result.summary.predominance] ?? result.summary.predominance}</strong>.</p>
      <ul>{Object.entries(result.summary.counts).map(([label, count]) => <li key={label}>{labels[label]}: {count} ({format(result.summary!.proportions[label] * 100)}%)</li>)}</ul></> : <p>Resumo de classes indisponível.</p>}
      <p>Trecho inserido: indisponível. A fração direcional de reuso do dataset não é conhecida nestes documentos e não foi inferida pela nota.</p></section>
    {result.trained_models ? <section aria-label="Modelos treinados"><h2>Modelos treinados — demonstração exploratória</h2>
      <p>Aplicados aos melhores pares de Q5-V2. Saídas por sentença, separadas do índice de similaridade. H1/H2 não superaram os baselines na avaliação final; Platt piorou Brier e log-loss. A probabilidade de derivação usa ancestralidade sintética e não tem garantia de calibração nestes documentos.</p>
      <p>Data desta comparação: {new Date(saved.created_at).toLocaleString('pt-BR')}.</p>
      {result.trained_models.models.map(item => <p key={item.name}>{item.name}; versão <code>{item.version}</code>; SHA-256 <code>{item.sha256}</code>.</p>)}
      <div className="table-scroll"><table><thead><tr><th>Par</th><th>Classe H1 aprendida</th><th>Escore H2 siamês [0,1]</th><th>Probabilidade de derivação [0,1]</th></tr></thead>
        <tbody>{result.trained_models.pairs.map(item => <tr key={item.suspect}><td>F{item.source+1} → A{item.suspect+1}</td><td>{labels[item.h1_label]}</td><td>{format(item.h2_score)}</td><td>{format(item.derivation_probability)}</td></tr>)}</tbody></table></div>
    </section> : <p>Siamês treinado, fusão aprendida e probabilidade de derivação: desativados nesta execução.</p>}
    <section><h2>Instrumentação de engenharia</h2><p>Tempos monotônicos desta execução; não são resultado experimental ou validação de H3. Preparação/carregamento e comparação compartilham recursos; não há tempo ou memória atribuídos individualmente aos algoritmos.</p>
      <ul><li>Parsing e transporte dos dois arquivos em paralelo: {format(saved.engineering.parsing_http_ms)} ms.</li><li>Chamada HTTP de comparação: {format(saved.engineering.compare_http_ms)} ms, incluindo transporte e acesso a recursos.</li>
        <li>Persistência antes da publicação do registro final: {format(saved.engineering.persistence_before_publish_ms)} ms.</li><li>Caso de uso antes da publicação: {format(saved.engineering.server_before_publish_ms)} ms; exclui autenticação, recepção do formulário, gravação final, releitura e transporte da resposta.</li>
        {clientMs !== null && <li>Envio até validação da resposta no cliente nesta criação: {format(clientMs)} ms; exclui renderização, não é tempo por motor nem será recalculado no histórico.</li>}</ul>
      {saved.engineering.core.map((item, i) => <p key={i}>Core {item.operation}: {Object.entries(item.stages_ms).map(([name, value]) => `${stageNames[name] ?? name}=${format(value)} ms`).join('; ') || 'tempos internos não disponíveis'}.
        {' '}Acesso a recursos: {item.resource_state ?? 'não aplicável/não informado'}. Pico RSS do processo desde o início: {item.process_lifetime_peak_rss_kib === null ? 'não disponível nesta plataforma' : format(item.process_lifetime_peak_rss_kib, 0) + ' KiB'}.</p>)}
      <p>RSS é do processo inteiro e pode incluir requisições anteriores/concomitantes, não é memória por algoritmo. Não se mediu alocação Python ou GPU. As subetapas estão contidas em compare total; não somar ambos nem atribuir o bloco compartilhado a cada algoritmo. Etapas não executadas no modo/recurso escolhido ficam ausentes, sem preencher zero.</p>
    </section>
    <section className="provenance"><h2>Rastreabilidade e limites</h2><p>Política {result.metadata.policy}; configuração <code>{result.metadata.config_sha256}</code>.</p>
      <p>IDF provisório: versão <code>{String(result.metadata.idf.historical_version ?? result.metadata.idf.version ?? 'ver metadados de identidade')}</code>; identidade <code>{String(result.metadata.idf.identity ?? 'indisponível')}</code>. Descritor observado não é atestação retroativa de construção.</p>
      <p>Modelo: {String(model?.model ?? 'indisponível')}; revisão <code>{String(model?.revision ?? 'indisponível')}</code>. Janelas completas por tokens, sem sobreposição; pooling ponderado e normalização final conforme configuração.</p>
      <p>Exibição decimal half-up em duas casas; resultados persistidos mantêm a precisão. Similaridade e correspondências não concluem plágio, autoria ou intenção. Sem OCR ou busca online. Modelos ativos, quando presentes, usam artefatos congelados; nenhuma calibração é ajustada nestes documentos.</p></section>
  </article>;
}
