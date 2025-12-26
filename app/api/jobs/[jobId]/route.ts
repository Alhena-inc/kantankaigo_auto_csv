import { NextRequest, NextResponse } from 'next/server';
import { getJob } from '@/lib/jobManager';

export async function GET(
  request: NextRequest,
  { params }: { params: { jobId: string } }
) {
  try {
    const job = getJob(params.jobId);

    if (!job) {
      return NextResponse.json(
        { error: 'ジョブが見つかりません' },
        { status: 404 }
      );
    }

    return NextResponse.json(job);
  } catch (error) {
    console.error('API error:', error);
    return NextResponse.json(
      { error: 'サーバーエラーが発生しました' },
      { status: 500 }
    );
  }
}

