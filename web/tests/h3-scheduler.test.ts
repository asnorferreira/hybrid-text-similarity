import test from 'node:test';
import assert from 'node:assert/strict';
import { runH3User } from '../scripts/load-h3';

test('H3: 180 s / 7 s permits 26 starts, with no shortened final cadence', async () => {
  let time=0;
  const starts: number[]=[];
  await runH3User(180000,7000,async (_,started)=>{ starts.push(started); time+=2300; },
    ()=>time,async ms=>{ time+=ms; });
  assert.equal(starts.length,26);
  assert.equal(starts[0],0);
  assert.equal(starts.at(-1),175000);
  assert.ok(starts.slice(1).every((t,i)=>t-starts[i]>=7000));
});

test('H3: an early timer wake cannot start a request early or at the deadline', async () => {
  let time=0;
  const starts: number[]=[];
  await runH3User(14000,7000,async (_,started)=>{ starts.push(started); time+=100; },
    ()=>time,async ms=>{ time+=ms>1?ms-.25:ms; });
  assert.deepEqual(starts,[0,7000]);
});

test('H3: slow requests remain closed loop and may complete after the window', async () => {
  let time=0;
  const starts: number[]=[];
  await runH3User(20000,7000,async (_,started)=>{ starts.push(started); time+=11000; },
    ()=>time,async ms=>{ time+=ms; });
  assert.deepEqual(starts,[0,11000]);
  assert.equal(time,22000);
});
