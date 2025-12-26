// ジョブ管理システム（メモリベース、本番環境ではRedis等を使用推奨）
interface Job {
  id: string;
  status: 'pending' | 'running' | 'completed' | 'failed';
  progress: number;
  message: string;
  result?: {
    filename: string;
    downloadUrl: string;
  };
  error?: string;
  createdAt: Date;
  updatedAt: Date;
}

const jobs: Map<string, Job> = new Map();

export function createJob(): string {
  const jobId = `job_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
  jobs.set(jobId, {
    id: jobId,
    status: 'pending',
    progress: 0,
    message: 'ジョブを開始しています...',
    createdAt: new Date(),
    updatedAt: new Date(),
  });
  return jobId;
}

export function getJob(jobId: string): Job | undefined {
  return jobs.get(jobId);
}

export function updateJob(
  jobId: string,
  updates: Partial<Omit<Job, 'id' | 'createdAt'>>
): void {
  const job = jobs.get(jobId);
  if (job) {
    Object.assign(job, updates, { updatedAt: new Date() });
  }
}

export function deleteJob(jobId: string): void {
  jobs.delete(jobId);
}

// 古いジョブをクリーンアップ（24時間以上経過したジョブを削除）
export function cleanupOldJobs(): void {
  const now = new Date();
  const oneDayAgo = new Date(now.getTime() - 24 * 60 * 60 * 1000);

  for (const [jobId, job] of jobs.entries()) {
    if (job.updatedAt < oneDayAgo) {
      jobs.delete(jobId);
    }
  }
}

