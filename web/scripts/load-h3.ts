import { createHash } from 'node:crypto';
import { readFile, writeFile, appendFile, mkdir } from 'node:fs/promises';
import { dirname } from 'node:path';
import { createTestUser, testBase } from './test-client';

export async function runH3User(deadline: number, cadenceMs: number,
  request: (sequence: number, started: number) => Promise<void>,
  clock: () => number = () => performance.now(),
  sleep: (ms: number) => Promise<void> = ms => new Promise(resolve => setTimeout(resolve, ms))) {
  let sequence=0, nextStart=clock();
  while (true) {
    const now=clock();
    if (now>=deadline || nextStart>=deadline) break;
    if (now<nextStart) { await sleep(nextStart-now); continue; }
    nextStart=now+cadenceMs;
    await request(sequence++,now);
  }
}

export async function runH3() {
  const path = process.env.HTS_H3_PROTOCOL!;
  const bytes = await readFile(path);
  const protocol = JSON.parse(bytes.toString());
  if (protocol.schema !== 'hts-h3-protocol-1' || protocol.duration_ms !== 180000 || protocol.cadence_ms !== 7000) throw new Error('protocolo H3 incompatível');
  const config = process.env.HTS_H3_CONFIGURATION;
  if (!protocol.configurations.includes(config)) throw new Error('configuração H3 obrigatória');
  const output = process.env.HTS_LOAD_OUTPUT!;
  if (!output) throw new Error('saída H3 obrigatória');
  await mkdir(dirname(output), { recursive: true });
  const journal = output + '.partial.jsonl';
  const protocolHash = createHash('sha256').update(bytes).digest('hex');
  await writeFile(journal, JSON.stringify({ event: 'start', config, protocol_sha256: protocolHash, utc: new Date().toISOString(), base: testBase() })+'\n', { flag: 'wx' });
  const clients: Awaited<ReturnType<typeof createTestUser>>[] = [];
  for (let i=0; i<10; i++) clients.push(await createTestUser());
  const quantile = (values: number[], p: number) => {
    if (!values.length) return null;
    const a = [...values].sort((a,b)=>a-b), index=(a.length-1)*p, lo=Math.floor(index), hi=Math.ceil(index);
    return a[lo]+(index-lo)*(a[hi]-a[lo]);
  };
  const phases = [];
  for (const count of protocol.sentence_counts as number[]) {
    const text = Array.from({length:count}, (_,i)=>`A pesquisa número ${i+1} compara documentos e apresenta resultados claros.`).join(' ');
    const call = async (client: typeof clients[number]) => {
      const start = performance.now();
      try {
        const form = new FormData();
        form.set('contract_version','1.0'); form.set('mode','hybrid');
        form.set('source_text',text); form.set('suspect_text',text);
        const response = await client.request('/api/comparisons',{method:'POST',body:form,signal:AbortSignal.timeout(protocol.request_timeout_ms)});
        const body = await response.json();
        const ok = response.status===200 && body.result?.state==='calculated';
        const actualCount = body.result?.source?.length ?? null;
        const active = Boolean(body.result?.trained_models);
        const expected = config==='enabled';
        if (ok && (actualCount!==count || active!==expected)) throw new Error('protocolo/quantidade/configuração observada divergente');
        return {ms:performance.now()-start,status:response.status,ok,actual_sentences:actualCount,active,
          core:body.engineering?.core ?? null, failure:null as string|null};
      } catch(error) {
        return {ms:performance.now()-start,status:null,ok:false,actual_sentences:null,active:null,core:null,
          failure:error instanceof Error ? error.message : 'unknown'};
      }
    };
    const warmup=[];
    for (let user=0; user<clients.length; user++) {
      const row=await call(clients[user]); warmup.push(row);
      await appendFile(journal,JSON.stringify({event:'warmup',count,user,...row})+'\n');
      if (!row.ok) throw new Error('aquecimento H3 falhou; preservar diário e corrigir infraestrutura antes de medir');
    }
    for (const concurrency of protocol.concurrency as number[]) {
      const observations: (Awaited<ReturnType<typeof call>> & {
        user: number; sequence: number; request_started_ms: number; request_completed_ms: number;
      })[]=[];
      const start=performance.now(), startedUtc=new Date().toISOString();
      const deadline=start+protocol.duration_ms;
      await Promise.all(clients.slice(0,concurrency).map((client,user)=>
        runH3User(deadline,protocol.cadence_ms,async (sequence,requestStart)=>{
          const measured=await call(client);
          const observation={...measured,user,sequence,
            request_started_ms:requestStart-start,request_completed_ms:performance.now()-start};
          observations.push(observation);
          await appendFile(journal,JSON.stringify({event:'sample',count,concurrency,...observation})+'\n');
        })));
      // Preserve the full observation window even when every user's next
      // eligible start lies beyond the deadline. Early timer wakes are rechecked.
      while (performance.now()<deadline) await new Promise(resolve=>setTimeout(resolve,deadline-performance.now()));
      const elapsed=performance.now()-start, successful=observations.filter(r=>r.ok).map(r=>r.ms);
      const errors=observations.length-successful.length, p95=quantile(successful,.95);
      const targeted=protocol.goal_concurrency.includes(concurrency);
      const phase={count,concurrency,started_utc:startedUtc,duration_ms:elapsed,window_ms:protocol.duration_ms,
        attempts:observations.length,successes:successful.length,errors,
        rejected_429:observations.filter(r=>r.status===429).length,unavailable_503:observations.filter(r=>r.status===503).length,
        p50_ms:quantile(successful,.5),p95_ms:p95,p99_ms:quantile(successful,.99),
        all_attempt_throughput_per_second:observations.length/(elapsed/1000),successful_throughput_per_second:successful.length/(elapsed/1000),
        failure_rate:errors/observations.length,goal_ms:targeted?protocol.goals_ms[String(count)]:null,
        accepted:targeted?successful.length>0&&p95!<=protocol.goals_ms[String(count)]&&errors===0:null,
        observations};
      phases.push(phase);
      await appendFile(journal,JSON.stringify({event:'phase_complete',...phase})+'\n');
      console.log(JSON.stringify({config,count,concurrency,attempts:phase.attempts,errors,p95_ms:p95,accepted:phase.accepted}));
      // Separate fixed windows to avoid carrying a full per-user quota into the next phase.
      if (concurrency!==10 || count!==120) await new Promise(resolve=>setTimeout(resolve,protocol.quiet_between_scenarios_ms));
    }
  }
  const result={purpose:protocol.purpose,config,protocol_sha256:protocolHash,created_utc:new Date().toISOString(),
    node:process.version,platform:process.platform,phases,accepted:phases.filter(p=>p.accepted!==null).every(p=>p.accepted),
    failures_preserved:true,quantiles:protocol.quantiles};
  await writeFile(output,JSON.stringify(result,null,2),{flag:'wx'});
  console.log(JSON.stringify({output,config,accepted:result.accepted,scenarios:phases.length}));
}
