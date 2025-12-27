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

    // Vercel環境ではPython/Seleniumが動作しない可能性が高い
    // エラーメッセージを明確にする
    const isVercel = process.env.VERCEL === '1';

    if (isVercel) {
      // Vercel環境では、Pythonスクリプトの実行を試みるが、失敗する可能性が高い
      updateJob(jobId, {
        status: 'running',
        progress: 20,
        message: 'Vercel環境を検出しました。Pythonスクリプトの実行を試みます...',
      });
    }

    // Pythonスクリプトを実行
    const scriptPath = path.join(process.cwd(), 'auto_login.py');
    const pythonCommand = process.platform === 'win32' ? 'python' : 'python3';

    const pythonProcess = spawn(pythonCommand, [
      scriptPath,
      '--year', year.toString(),
      '--month', month.toString(),
      ...(day ? ['--day', day.toString()] : []),
      '--job-id', jobId,
    ], {
      env: {
        ...process.env,
        KANTAN_USERNAME: process.env.KANTAN_USERNAME || '',
        KANTAN_PASSWORD: process.env.KANTAN_PASSWORD || '',
        KANTAN_GROUP_NAME: process.env.KANTAN_GROUP_NAME || '',
      },
    });

    let output = '';
    let errorOutput = '';

    pythonProcess.stdout.on('data', (data) => {
      const text = data.toString();
      output += text;
      console.log(`[Python stdout] ${text}`);

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
      const text = data.toString();
      errorOutput += text;
      console.error(`[Python stderr] ${text}`);
    });

    // タイムアウトを設定（5分）
    const timeout = setTimeout(() => {
      pythonProcess.kill();
      updateJob(jobId, {
        status: 'failed',
        progress: 0,
        message: '処理がタイムアウトしました（5分）',
        error: 'Vercelのサーバーレス環境では、Selenium/ChromeDriverが動作しない可能性があります。別のホスティングサービス（Railway、Renderなど）の使用を推奨します。',
      });
      reject(new Error('Process timeout'));
    }, 5 * 60 * 1000);

    pythonProcess.on('close', (code) => {
      clearTimeout(timeout);

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
        const errorMessage = errorOutput || '不明なエラーが発生しました';
        const detailedError = isVercel
          ? `${errorMessage}\n\n注意: Vercelのサーバーレス環境では、Selenium/ChromeDriverが動作しない可能性があります。ChromeDriverやChromeバイナリがインストールされていないため、この機能は動作しません。\n\n推奨される解決策:\n1. RailwayやRenderなどの別のホスティングサービスを使用\n2. Puppeteer/Playwrightに変更（Node.jsネイティブ）\n3. 外部スクレイピングサービス（Browserless、ScrapingBeeなど）を使用`
          : errorMessage;

        updateJob(jobId, {
          status: 'failed',
          progress: 0,
          message: '処理に失敗しました',
          error: detailedError,
        });
        reject(new Error(`Python script exited with code ${code}: ${errorMessage}`));
      }
    });

    pythonProcess.on('error', (error) => {
      clearTimeout(timeout);
      const errorMessage = error.message;
      const detailedError = isVercel
        ? `${errorMessage}\n\nVercelのサーバーレス環境では、PythonスクリプトやSeleniumの実行に制限があります。`
        : errorMessage;

      updateJob(jobId, {
        status: 'failed',
        progress: 0,
        message: 'スクレイピング処理の開始に失敗しました',
        error: detailedError,
      });
      reject(error);
    });
  });
}
