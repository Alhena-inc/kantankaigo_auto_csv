import { NextRequest, NextResponse } from 'next/server';
import fs from 'fs';
import path from 'path';

export async function GET(
  request: NextRequest,
  { params }: { params: { filename: string } }
) {
  try {
    const filename = params.filename;
    const filePath = path.join(process.cwd(), filename);

    // セキュリティチェック：ファイル名に危険な文字が含まれていないか確認
    // schedule_YYYY_MM.csv または schedule_YYYY_MM_DD.csv のパターンを許可
    if (!/^schedule_\d{4}_\d{1,2}(_\d{1,2})?\.csv$/.test(filename)) {
      return NextResponse.json(
        { error: '無効なファイル名です' },
        { status: 400 }
      );
    }

    if (!fs.existsSync(filePath)) {
      return NextResponse.json(
        { error: 'ファイルが見つかりません' },
        { status: 404 }
      );
    }

    const fileContent = fs.readFileSync(filePath, 'utf-8');

    return new NextResponse(fileContent, {
      headers: {
        'Content-Type': 'text/csv; charset=utf-8',
        'Content-Disposition': `attachment; filename="${filename}"`,
      },
    });
  } catch (error) {
    console.error('Download error:', error);
    return NextResponse.json(
      { error: 'ファイルのダウンロードに失敗しました' },
      { status: 500 }
    );
  }
}
