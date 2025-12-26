# かんたん介護ソフト 自動化用サイト構造ドキュメント

## 1. システム基本情報
- **Base URL**: `https://www.kantankaigo.jp/home`
- **Login URL**: `https://www.kantankaigo.jp/home/users/login`
- **認証情報**: ユーザーID (username), パスワード (password), 担当者コード (group_name)

## 2. 重要なロジック（高速化の鍵）
- **カレンダー操作回避**: UI上のカレンダー操作は遅いため行わない。
- **PIDの取得**: 利用者一覧画面の `span.planJisseki` タグから `pid` 属性を取得する。
- **直接アクセス**: 取得したPIDを使用し、以下のURLパターンでスケジュール一覧（編集）画面へ直接遷移する。
  - URLパターン: `https://www.kantankaigo.jp/home/jissekis/editCustomer/{PID}`
- **CSV出力**: `utf-8-sig` (BOM付き) で保存し、Excelでの文字化けを防ぐ。

---

## 3. ページ別詳細構造

### A. ログインページ
**要素セレクタ**:
- ユーザーID: `input[name="data[User][username]"]`
- パスワード: `input[name="data[User][password]"]`
- 担当者コード: `input[id="UserGroupGroupname2"]` (存在しない場合もある)
- ログインボタン: `input[name="login"]`

---

### B. 利用者一覧ページ
**URL**: `/home/customers` (またはメニュークリックで遷移)
**解析目的**: 全利用者の `名前` と `PID` を取得する。

**HTML構造サンプル**:
```html
<tr class="customerline">
    <td class="no">1</td>
    <td class="check"><input type="checkbox" name="customerId[]" value="263335"></td>
    <td colspan="2"><a href="/home/customers/edit/263335" class="focus">山下博之</a></td>
    <td class="calendar">
        <span class="link planJisseki focus" law="" pid="263335">予定と実績</span>
    </td>
</tr>
データ取得ロジック (Python/Selenium):

Python

elements = driver.find_elements(By.CSS_SELECTOR, "span.planJisseki")
pid = element.get_attribute("pid")
# 名前は親要素を遡って取得、またはPIDベースで仮置きしても良い
C. スケジュール詳細ページ（一覧形式）
URL: https://www.kantankaigo.jp/home/jissekis/editCustomer/{PID} 解析目的: 日付、時間、サービス内容、スタッフ名を抽出する。

HTML構造サンプル: ※以下は「一覧形式」選択時のテーブル構造（推定および解析済み）

HTML

<table class="list_table"> <tr>
        <td class="day edit">12/01(月)</td>
        <td class="time edit">09:00-10:00</td>
        <td class="service edit">身体１介護</td>
        <td class="staff edit">ヘルパーA子</td>
    </tr>
</table>
日付制御:

画面上のhidden inputなどで現在表示中の年月を確認可能。

<input id="serviceDate" value="2025/12/01"> のような要素が存在。

ページロード時に年月が異なる場合、jQuery UIの $('.ui-monthpicker-trigger').click() 等で変更が必要だが、URLパラメータが効く可能性もある（要検証）。
