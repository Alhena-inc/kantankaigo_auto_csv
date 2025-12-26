import { spawn } from 'child_process';
import { updateJob } from './jobManager';
import path from 'path';

export async function runScraper(
  jobId: string,
  year: number,
  month: number,
  day?: number
): Promise<void> {
  return new Promise((resolve, reject) => {
    updateJob(jobId, {
      status: 'running',
      progress: 10,
      message: 'スクレイピング処理を開始しています...',
    });

    // Pythonスクリプトを実行
    const scriptPath = path.join(process.cwd(), 'auto_login.py');
    const pythonProcess = spawn('python3', [
      scriptPath,
      '--year', year.toString(),
      '--month', month.toString(),
      ...(day ? ['--day', day.toString()] : []),
      '--job-id', jobId,
    ]);

    let output = '';
    let errorOutput = '';

    pythonProcess.stdout.on('data', (data) => {
      const text = data.toString();
      output += text;

      // 進捗情報をパース（Pythonスクリプトから送信される）
      const progressMatch = text.match(/PROGRESS:(\d+):(.+)/);
      if (progressMatch) {
        const progress = parseInt(progressMatch[1], 10);
        const message = progressMatch[2].trim();
        updateJob(jobId, {
          progress,
          message,
        });
      }
    });

    pythonProcess.stderr.on('data', (data) => {
      errorOutput += data.toString();
    });

    pythonProcess.on('close', (code) => {
      if (code === 0) {
        // CSVファイル名を取得（出力から抽出）
        const csvMatch = output.match(/CSV_FILE:(.+)/);
        const filename = csvMatch ? csvMatch[1].trim() : `schedule_${year}_${month}.csv`;

        updateJob(jobId, {
          status: 'completed',
          progress: 100,
          message: '処理が完了しました',
          result: {
            filename,
            downloadUrl: `/api/download/${filename}`,
          },
        });
        resolve();
      } else {
        updateJob(jobId, {
          status: 'failed',
          progress: 0,
          message: '処理に失敗しました',
          error: errorOutput || '不明なエラーが発生しました',
        });
        reject(new Error(`Python script exited with code ${code}`));
      }
    });

    pythonProcess.on('error', (error) => {
      updateJob(jobId, {
        status: 'failed',
        progress: 0,
        message: 'スクレイピング処理の開始に失敗しました',
        error: error.message,
      });
      reject(error);
    });
  });
}

