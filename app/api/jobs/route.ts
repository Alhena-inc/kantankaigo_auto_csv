import { NextRequest, NextResponse } from 'next/server';
import { createJob } from '@/lib/jobManager';
import { runScraper as runScraperTask } from '@/lib/scraperRunner';

export async function POST(request: NextRequest) {
  try {
    const body = await request.json();
    const { year, month, day } = body;

    if (!year || !month) {
      return NextResponse.json(
        { error: '年と月は必須です' },
        { status: 400 }
      );
    }

    // ジョブを作成
    const jobId = createJob();

    // バックグラウンドでスクレイピングを実行（awaitしない）
    runScraperTask(jobId, year, month, day).catch((error) => {
      console.error('Scraper error:', error);
    });

    return NextResponse.json({ jobId });
  } catch (error) {
    console.error('API error:', error);
    return NextResponse.json(
      { error: 'サーバーエラーが発生しました' },
      { status: 500 }
    );
  }
}
