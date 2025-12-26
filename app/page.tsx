'use client';

import { useState, useEffect } from 'react';

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
}

export default function Home() {
  const [year, setYear] = useState(new Date().getFullYear());
  const [month, setMonth] = useState(new Date().getMonth() + 1);
  const [day, setDay] = useState<number | undefined>(undefined);
  const [useDay, setUseDay] = useState(false);
  const [jobId, setJobId] = useState<string | null>(null);
  const [job, setJob] = useState<Job | null>(null);
  const [loading, setLoading] = useState(false);

  // ジョブステータスをポーリング
  useEffect(() => {
    if (!jobId) return;

    const interval = setInterval(async () => {
      try {
        const response = await fetch(`/api/jobs/${jobId}`);
        if (response.ok) {
          const jobData = await response.json();
          setJob(jobData);

          // 完了または失敗したらポーリングを停止
          if (jobData.status === 'completed' || jobData.status === 'failed') {
            clearInterval(interval);
            setLoading(false);
          }
        }
      } catch (error) {
        console.error('Failed to fetch job status:', error);
      }
    }, 2000); // 2秒ごとにポーリング

    return () => clearInterval(interval);
  }, [jobId]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setJob(null);

    try {
      const response = await fetch('/api/jobs', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          year,
          month,
          day: useDay ? day : undefined,
        }),
      });

      if (response.ok) {
        const data = await response.json();
        setJobId(data.jobId);
      } else {
        const error = await response.json();
        alert(`エラー: ${error.error}`);
        setLoading(false);
      }
    } catch (error) {
      console.error('Failed to start job:', error);
      alert('ジョブの開始に失敗しました');
      setLoading(false);
    }
  };

  const handleDownload = () => {
    if (job?.result?.downloadUrl) {
      window.open(job.result.downloadUrl, '_blank');
    }
  };

  // 年の選択肢（現在年から±5年）
  const currentYear = new Date().getFullYear();
  const years = Array.from({ length: 11 }, (_, i) => currentYear - 5 + i);

  // 月の選択肢
  const months = Array.from({ length: 12 }, (_, i) => i + 1);

  // 日の選択肢（選択された年月に基づく）
  const getDaysInMonth = (year: number, month: number) => {
    return new Date(year, month, 0).getDate();
  };
  const days = useDay
    ? Array.from({ length: getDaysInMonth(year, month) }, (_, i) => i + 1)
    : [];

  return (
    <div style={{ maxWidth: '800px', margin: '0 auto', padding: '2rem' }}>
      <h1 style={{ marginBottom: '2rem', textAlign: 'center' }}>
        かんたん介護 スケジュール取得
      </h1>

      <form onSubmit={handleSubmit} style={{ marginBottom: '2rem' }}>
        <div style={{ marginBottom: '1rem' }}>
          <label style={{ display: 'block', marginBottom: '0.5rem' }}>
            年:
          </label>
          <select
            value={year}
            onChange={(e) => setYear(parseInt(e.target.value, 10))}
            style={{
              width: '100%',
              padding: '0.5rem',
              fontSize: '1rem',
              border: '1px solid #ccc',
              borderRadius: '4px',
            }}
          >
            {years.map((y) => (
              <option key={y} value={y}>
                {y}年
              </option>
            ))}
          </select>
        </div>

        <div style={{ marginBottom: '1rem' }}>
          <label style={{ display: 'block', marginBottom: '0.5rem' }}>
            月:
          </label>
          <select
            value={month}
            onChange={(e) => setMonth(parseInt(e.target.value, 10))}
            style={{
              width: '100%',
              padding: '0.5rem',
              fontSize: '1rem',
              border: '1px solid #ccc',
              borderRadius: '4px',
            }}
          >
            {months.map((m) => (
              <option key={m} value={m}>
                {m}月
              </option>
            ))}
          </select>
        </div>

        <div style={{ marginBottom: '1rem' }}>
          <label style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            <input
              type="checkbox"
              checked={useDay}
              onChange={(e) => setUseDay(e.target.checked)}
            />
            特定の日を指定する
          </label>
        </div>

        {useDay && (
          <div style={{ marginBottom: '1rem' }}>
            <label style={{ display: 'block', marginBottom: '0.5rem' }}>
              日:
            </label>
            <select
              value={day || ''}
              onChange={(e) =>
                setDay(e.target.value ? parseInt(e.target.value, 10) : undefined)
              }
              style={{
                width: '100%',
                padding: '0.5rem',
                fontSize: '1rem',
                border: '1px solid #ccc',
                borderRadius: '4px',
              }}
            >
              <option value="">選択してください</option>
              {days.map((d) => (
                <option key={d} value={d}>
                  {d}日
                </option>
              ))}
            </select>
          </div>
        )}

        <button
          type="submit"
          disabled={loading || (useDay && !day)}
          style={{
            width: '100%',
            padding: '0.75rem',
            fontSize: '1rem',
            backgroundColor: loading ? '#ccc' : '#0070f3',
            color: 'white',
            border: 'none',
            borderRadius: '4px',
            cursor: loading ? 'not-allowed' : 'pointer',
          }}
        >
          {loading ? '処理中...' : 'スケジュール取得を開始'}
        </button>
      </form>

      {job && (
        <div
          style={{
            padding: '1.5rem',
            border: '1px solid #ccc',
            borderRadius: '8px',
            backgroundColor: '#f9f9f9',
          }}
        >
          <h2 style={{ marginTop: 0 }}>処理状況</h2>
          <div style={{ marginBottom: '1rem' }}>
            <div
              style={{
                width: '100%',
                height: '24px',
                backgroundColor: '#e0e0e0',
                borderRadius: '12px',
                overflow: 'hidden',
              }}
            >
              <div
                style={{
                  width: `${job.progress}%`,
                  height: '100%',
                  backgroundColor:
                    job.status === 'completed'
                      ? '#4caf50'
                      : job.status === 'failed'
                      ? '#f44336'
                      : '#2196f3',
                  transition: 'width 0.3s ease',
                }}
              />
            </div>
            <div style={{ marginTop: '0.5rem', textAlign: 'center' }}>
              {job.progress}%
            </div>
          </div>

          <div style={{ marginBottom: '1rem' }}>
            <strong>ステータス:</strong>{' '}
            {job.status === 'pending'
              ? '待機中'
              : job.status === 'running'
              ? '実行中'
              : job.status === 'completed'
              ? '完了'
              : '失敗'}
          </div>

          <div style={{ marginBottom: '1rem' }}>
            <strong>メッセージ:</strong> {job.message}
          </div>

          {job.error && (
            <div
              style={{
                padding: '1rem',
                backgroundColor: '#ffebee',
                color: '#c62828',
                borderRadius: '4px',
                marginBottom: '1rem',
              }}
            >
              <strong>エラー:</strong> {job.error}
            </div>
          )}

          {job.status === 'completed' && job.result && (
            <div>
              <button
                onClick={handleDownload}
                style={{
                  padding: '0.75rem 1.5rem',
                  fontSize: '1rem',
                  backgroundColor: '#4caf50',
                  color: 'white',
                  border: 'none',
                  borderRadius: '4px',
                  cursor: 'pointer',
                }}
              >
                CSVファイルをダウンロード ({job.result.filename})
              </button>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

