export class AdmissionError extends Error {
  constructor(public reason: 'capacity' | 'timeout' | 'aborted') { super(reason); }
}
type Waiter = { grant: () => void };

/** Process-local FIFO: bounded active work, queue and waiting time. */
export class AdmissionQueue {
  private active = 0;
  private waiting: Waiter[] = [];
  constructor(private slots = 2, private capacity = 8, private waitMs = 30_000,
    private clock: () => number = () => performance.now()) {
    if (![slots, capacity, waitMs].every(Number.isInteger) || slots < 1 || capacity < 0 || waitMs < 1) throw new Error('invalid admission limits');
  }
  async acquire(signal?: AbortSignal): Promise<() => void> {
    if (signal?.aborted) throw new AdmissionError('aborted');
    if (this.active < this.slots) {
      this.active++;
      return this.release();
    }
    if (this.waiting.length >= this.capacity) throw new AdmissionError('capacity');
    return new Promise((resolve, reject) => {
      const expiresAt = this.clock() + this.waitMs;
      const cleanup = () => {
        clearTimeout(timer);
        signal?.removeEventListener('abort', abort);
        this.waiting = this.waiting.filter(item => item !== waiter);
      };
      const abort = () => { cleanup(); reject(new AdmissionError('aborted')); };
      const waiter: Waiter = { grant: () => {
        cleanup();
        // Check the deadline again: an occupied event loop can delay timers.
        if (signal?.aborted || this.clock() >= expiresAt) {
          reject(new AdmissionError(signal?.aborted ? 'aborted' : 'timeout'));
          this.waiting[0]?.grant();
          return;
        }
        this.active++; resolve(this.release());
      } };
      const timer = setTimeout(() => { cleanup(); reject(new AdmissionError('timeout')); }, this.waitMs);
      signal?.addEventListener('abort', abort, { once: true });
      this.waiting.push(waiter);
    });
  }
  private release() {
    let released = false;
    return () => {
      if (released) return;
      released = true;
      this.active--;
      this.waiting[0]?.grant();
    };
  }
}
