import os
import time
import logging
import csv  # 追加: CSV出力用
import argparse
import sys
from urllib.parse import urlparse, parse_qs
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from selenium.webdriver.support.ui import Select

# ログ設定
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s', datefmt='%H:%M:%S')
logger = logging.getLogger(__name__)

# --- 設定 ---
LOGIN_URL = "https://www.kantankaigo.jp/home/users/login"
BASE_URL = "https://www.kantankaigo.jp/home"

# ユーザー情報（環境変数から取得、なければデフォルト値）
USERNAME = os.getenv("KANTAN_USERNAME", "4845850")
PASSWORD = os.getenv("KANTAN_PASSWORD", "fskildzolk")
GROUP_NAME = os.getenv("KANTAN_GROUP_NAME", "ibuki")


class KantanKaigoFastScraper:
    def __init__(self, headless=True):
        options = webdriver.ChromeOptions()
        # 高速化オプション
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--disable-gpu')
        # バックグラウンド実行のためヘッドレスモードを有効化
        if headless:
            options.add_argument('--headless')
        options.add_argument('--disable-blink-features=AutomationControlled')
        options.add_experimental_option("excludeSwitches", ["enable-logging"])

        self.driver = webdriver.Chrome(options=options)
        self.wait = WebDriverWait(self.driver, 10)
        self.progress_callback = None

    def close(self):
        self.driver.quit()

    def login(self):
        """ログイン処理"""
        logger.info("ログイン処理を開始...")
        self.driver.get(LOGIN_URL)
        try:
            self.wait.until(EC.visibility_of_element_located(
                (By.NAME, "data[User][username]"))).send_keys(USERNAME)
            self.driver.find_element(
                By.NAME, "data[User][password]").send_keys(PASSWORD)
            try:
                # 担当者コードがある場合
                self.driver.find_element(
                    By.ID, "UserGroupGroupname2").send_keys(GROUP_NAME)
            except:
                pass
            self.driver.find_element(By.NAME, "login").click()
            self.wait.until(lambda d: "login" not in d.current_url)
            logger.info("ログイン成功")
            return True
        except Exception as e:
            logger.error(f"ログイン失敗: {e}")
            return False

    def get_all_customers(self):
        """利用者一覧ページから、全員の「名前」と「PID」を一括取得する"""
        logger.info("利用者情報のリストアップを開始...")
        try:
            # 利用者一覧ページに移動
            try:
                self.driver.find_element(By.ID, "headMenuCustomer").click()
                self.wait.until(EC.presence_of_element_located(
                    (By.ID, "customerList")))
                time.sleep(1)  # ページ読み込み待機
            except:
                logger.info("メニューから遷移できなかったため、直接URLにアクセスします")
                self.driver.get(f"{BASE_URL}/customers")
                self.wait.until(EC.presence_of_element_located(
                    (By.ID, "customerList")))
                time.sleep(1)  # ページ読み込み待機

        except Exception as e:
            logger.error(f"利用者一覧ページへのアクセスに失敗: {e}")
            return []

        customers = []
        try:
            # PID属性から取得
            elements = self.driver.find_elements(
                By.CSS_SELECTOR, "span.planJisseki")

            logger.info(f"見つかったplanJisseki要素数: {len(elements)}")

            for idx, el in enumerate(elements, 1):
                try:
                    pid = el.get_attribute("pid")
                    if not pid:
                        logger.debug(f"要素 {idx}: PID属性が見つかりません")
                        continue

                    # 名前を取得
                    try:
                        row = el.find_element(By.XPATH, "./ancestor::tr")
                        name_el = row.find_element(By.CSS_SELECTOR, "a.focus")
                        name = name_el.text.strip()
                        if not name:
                            name = f"利用者ID_{pid}"
                    except Exception as e:
                        logger.warning(f"要素 {idx} (PID: {pid}): 名前の取得に失敗: {e}")
                        name = f"利用者ID_{pid}"

                    customers.append({"name": name, "pid": pid})
                    logger.debug(f"利用者追加: {name} (PID: {pid})")
                except Exception as e:
                    logger.warning(f"要素 {idx} の処理でエラー: {e}")
                    continue

            logger.info(f"合計 {len(customers)} 名の利用者IDを取得しました")
            if len(customers) == 0:
                logger.error("利用者が1人も取得できませんでした。ページの構造が変更されている可能性があります。")
            return customers
        except Exception as e:
            logger.error(f"利用者リスト取得エラー: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return []

    def ensure_list_view_and_date(self, target_year, target_month):
        """カレンダーの年月を合わせる処理"""
        max_retries = 2
        for retry in range(max_retries):
            try:
                # serviceDate要素が存在するまで待機（Render環境での読み込み遅延対策）
                service_date_found = False
                for wait_attempt in range(15):  # 最大15秒待機
                    try:
                        # 要素の存在確認
                        element = self.driver.find_element(By.ID, "serviceDate")
                        if element:
                            # 値が設定されているか確認
                            current_date_val = self.driver.execute_script(
                                "var el = document.getElementById('serviceDate'); return el && el.value ? el.value : null;")
                            if current_date_val:
                                service_date_found = True
                                break
                    except:
                        pass
                    time.sleep(1)
                    if wait_attempt % 3 == 0:  # 3秒ごとにログ出力
                        logger.debug(f"  serviceDate要素を待機中... ({wait_attempt + 1}/15)")

                if not service_date_found:
                    logger.error("  serviceDate要素が見つかりません")
                    if retry < max_retries - 1:
                        time.sleep(2)
                        continue
                    else:
                        return False

                # 現在の日付を取得（形式: "2025-11-01"）
            current_date_val = self.driver.execute_script(
                    "var el = document.getElementById('serviceDate'); return el && el.value ? el.value : null;")

                if not current_date_val:
                    logger.error("  serviceDateの値が取得できませんでした")
                    if retry < max_retries - 1:
                        time.sleep(2)
                        continue
                    else:
                        return False

                # 年月部分を抽出（"2025-11-01" -> "2025-11"）
                current_year_month = "-".join(current_date_val.split("-")[:2])
                target_year_month = f"{target_year}-{target_month:02d}"

                # 既に正しい年月が設定されているか確認
                if current_year_month == target_year_month:
                    logger.info(f"  年月は既に正しく設定されています: {current_date_val}")
                    # テーブルが読み込まれるまで待機（短縮）
                    try:
                        self.wait.until(EC.presence_of_element_located(
                            (By.CSS_SELECTOR, ".list_table")))
                    except:
                        pass
                return True

            logger.info(
                    f"  日付変更: {current_date_val} -> {target_year}年{target_month}月 (試行 {retry + 1}/{max_retries})")

                # カレンダーピッカーを開く（既に開いている場合はスキップ）
                try:
                    # 月ピッカーが既に表示されているかチェック
                    monthpicker_visible = self.driver.execute_script(
                        "return $('#ui-monthpicker-div').is(':visible');")

                    if not monthpicker_visible:
                        # JavaScriptで直接クリック（より確実）
                        self.driver.execute_script(
                            "$('.ui-monthpicker-trigger').click();")
                        time.sleep(0.3)
                    else:
                        logger.info("  月ピッカーは既に開いています")
                except Exception as e:
                    logger.warning(f"  カレンダートリガーの処理に失敗: {e}")
                    # フォールバック: 強制的にJavaScriptでクリック
                    try:
                        self.driver.execute_script(
                            "$('#ui-monthpicker-div').hide(); $('.ui-monthpicker-trigger').click();")
                        time.sleep(0.3)
            except:
                pass

                # 年を選択（存在する場合）
                try:
                    year_select = Select(self.wait.until(EC.presence_of_element_located(
                        (By.CSS_SELECTOR, "select.ui-datepicker-year"))))
                    current_year = year_select.first_selected_option.get_attribute(
                        "value")
                    if current_year != str(target_year):
                        year_select.select_by_value(str(target_year))
                        logger.info(f"  年を {target_year} に設定")
                        time.sleep(0.3)  # 年変更後の待機
                except Exception as e:
                    logger.warning(f"  年の選択に失敗（スキップ）: {e}")

                # 月を選択（<a>タグで直接クリック、0ベースなので target_month - 1）
                month_index = target_month - 1
                try:
                    # 方法1: JavaScriptで直接クリック
                    self.driver.execute_script(
                        f"$('#ui-monthpicker-div a[data-month=\"{month_index}\"]').click();")
                    logger.info(
                        f"  月を {target_month} に設定（data-month={month_index}）")

                    # 月ピッカーが閉じられるまで待機
                    time.sleep(0.5)
                    for _ in range(10):  # 最大3秒待機
                        monthpicker_visible = self.driver.execute_script(
                            "return $('#ui-monthpicker-div').is(':visible');")
                        if not monthpicker_visible:
                            break
                        time.sleep(0.3)

                    # 方法2: serviceDateを直接設定してからページをリロード（フォールバック）
                    # まず通常のクリックを試し、失敗した場合に使用
                    time.sleep(1)  # 初期待機

                    # もし更新されていない場合、直接設定を試す
                    check_date = self.driver.execute_script(
                        "var el = document.getElementById('serviceDate'); return el ? el.value : null;")

                    if check_date:
                        check_year_month = "-".join(check_date.split("-")[:2])
                        if check_year_month != target_year_month:
                            logger.info("  直接設定を試行します...")
                            # serviceDateを直接設定
                            self.driver.execute_script(
                                f"var el = document.getElementById('serviceDate'); if (el) {{ el.value = '{target_year}-{target_month:02d}-01'; }}")
                            # changeイベントを発火
                            self.driver.execute_script(
                                "$('#serviceDate').trigger('change');")
                            time.sleep(1)
                    else:
                        logger.warning("  serviceDate要素が見つからないため、直接設定をスキップします")

                except Exception as e:
                    logger.warning(f"  JavaScriptでの月選択に失敗: {e}")
                    # フォールバック: Seleniumでクリック
                    try:
                        month_link = self.wait.until(EC.element_to_be_clickable(
                            (By.CSS_SELECTOR, f"#ui-monthpicker-div a[data-month='{month_index}']")))
                        # スクロールして要素を表示
                        self.driver.execute_script(
                            "arguments[0].scrollIntoView(true);", month_link)
                        time.sleep(0.2)
                        month_link.click()
                        logger.info(f"  Seleniumで月を選択しました")
                        time.sleep(1)
                    except Exception as e2:
                        logger.error(f"  月の選択が完全に失敗: {e2}")
                        raise

                # 年月が正しく設定されるまで待機（最大10秒に延長）
                wait_time = 0
                while wait_time < 10:
                    time.sleep(0.5)  # 待機間隔
                    wait_time += 0.5
                    try:
                        updated_date_val = self.driver.execute_script(
                            "var el = document.getElementById('serviceDate'); return el ? el.value : null;")

                        if not updated_date_val:
                            logger.debug("  serviceDate要素が見つかりません（待機中）")
                            continue

                        updated_year_month = "-".join(
                            updated_date_val.split("-")[:2])
                        if updated_year_month == target_year_month:
                            logger.info(f"  年月の設定が確認されました: {updated_date_val}")
                            # テーブルが読み込まれるまで待機
                            try:
                                self.wait.until(EC.presence_of_element_located(
                                    (By.CSS_SELECTOR, ".list_table")))
            except:
                pass
                            time.sleep(0.5)
            return True
                        else:
                            logger.debug(
                                f"  待機中... 現在: {updated_year_month}, 目標: {target_year_month}")
                    except Exception as e:
                        logger.debug(f"  日付取得エラー: {e}")
                        pass

                # リトライ前に少し待機
                if retry < max_retries - 1:
                    logger.warning(f"  年月の設定確認に失敗。リトライします...")
                    time.sleep(1)

        except Exception as e:
                logger.warning(
                    f"  日付変更処理でエラー (試行 {retry + 1}/{max_retries}): {e}")
                if retry < max_retries - 1:
                    time.sleep(1)
                    continue
                else:
                    logger.error(f"  日付変更処理が最終的に失敗しました: {e}")
                    return False

        logger.error("  年月の設定に失敗しました（最大リトライ回数に達しました）")
            return False

    def scrape_schedule_table(self):
        """一覧形式のテーブルからデータを抽出"""
        schedules = []
        try:
            # テーブルが読み込まれるまで待機（短縮）
            try:
                self.wait.until(EC.presence_of_element_located(
                    (By.CSS_SELECTOR, ".list_table")))
                time.sleep(0.3)  # 待機時間を短縮
            except TimeoutException:
                logger.warning("  テーブル要素が見つかりません。空の結果を返します。")
                return schedules

            # 要素を取得
            dates = self.driver.find_elements(By.CSS_SELECTOR, ".day.edit")
            times = self.driver.find_elements(By.CSS_SELECTOR, ".time.edit")
            services = self.driver.find_elements(
                By.CSS_SELECTOR, ".service.edit")
            staffs = self.driver.find_elements(By.CSS_SELECTOR, ".staff.edit")

            if len(dates) == 0:
                logger.warning("  日付要素が1つも見つかりませんでした")
                return schedules

            logger.info(
                f"  取得した要素数: 日付={len(dates)}, 時間={len(times)}, サービス={len(services)}, スタッフ={len(staffs)}")

            loop_count = len(dates)
            for i in range(loop_count):
                try:
                date_txt = dates[i].text.strip()
                if not date_txt:
                    continue

                    time_txt = times[i].text.strip() if i < len(times) else ""
                    service_txt = services[i].text.strip(
                    ) if i < len(services) else ""
                    staff_txt = staffs[i].text.strip(
                    ) if i < len(staffs) else ""

                schedules.append({
                    "date": date_txt,
                        "time": time_txt,
                        "service": service_txt,
                        "staff": staff_txt
                    })
                except Exception as e:
                    logger.warning(f"  インデックス {i} のデータ抽出でエラー: {e}")
                    continue

            logger.info(f"  合計 {len(schedules)} 件のスケジュールデータを抽出しました")

        except Exception as e:
            logger.error(f"  データ抽出エラー: {e}")
            import traceback
            logger.error(traceback.format_exc())

        return schedules

    def save_to_csv(self, year, month, results, day=None):
        """結果をCSVファイルに保存する"""
        if day:
            filename = f"schedule_{year}_{month:02d}_{day:02d}.csv"
        else:
            filename = f"schedule_{year}_{month:02d}.csv"

        try:
            # encoding='utf-8-sig' にすることでExcelで文字化けせずに開けます
            with open(filename, 'w', newline='', encoding='utf-8-sig') as f:
                writer = csv.writer(f)

                # ヘッダー行
                writer.writerow(["利用者名", "日付", "時間帯", "サービス内容", "スタッフ名"])

                count = 0
                for name, scheds in results.items():
                    for s in scheds:
                        writer.writerow([
                            name,
                            s['date'],
                            s['time'],
                            s['service'],
                            s['staff']
                        ])
                        count += 1

            logger.info("=" * 50)
            logger.info(f"CSVファイル保存完了: {filename}")
            logger.info(f"利用者数: {len(results)}名")
            logger.info(f"書き込み行数: {count}行")
            # 各利用者のデータ件数をログ出力
            data_count = 0
            no_data_count = 0
            for name, scheds in results.items():
                if len(scheds) > 0:
                    logger.info(f"  ✓ {name}: {len(scheds)}件")
                    data_count += 1
                else:
                    logger.warning(f"  ✗ {name}: データなし")
                    no_data_count += 1
            logger.info(f"データあり: {data_count}名, データなし: {no_data_count}名")
            logger.info("=" * 50)

            # ファイル名を標準出力に出力（Node.js側で取得するため）
            print(f"CSV_FILE:{filename}", flush=True)

        except Exception as e:
            logger.error(f"CSV保存中にエラーが発生しました: {e}")
            raise

    def update_progress(self, progress, message):
        """進捗情報を出力（Node.js側で取得するため）"""
        print(f"PROGRESS:{progress}:{message}", flush=True)
        logger.info(f"[進捗 {progress}%] {message}")

    def run(self, target_year, target_month, target_day=None):
        try:
            self.update_progress(10, "ログイン処理を開始しています...")
            if not self.login():
                self.close()
                return False

            self.update_progress(
                20, f"対象年月: {target_year}年{target_month}月" + (f"{target_day}日" if target_day else ""))
            logger.info(f"対象年月: {target_year}年{target_month}月" +
                        (f"{target_day}日" if target_day else ""))

            # 1. 全員のIDを取得
            self.update_progress(30, "利用者情報を取得しています...")
            customers = self.get_all_customers()

            if not customers:
                self.update_progress(0, "利用者情報の取得に失敗しました")
                self.close()
                return False

            all_results = {}
            total = len(customers)
            logger.info(f"合計 {total} 名の利用者を処理します")

            # 2. 全員分ループ
            for idx, cust in enumerate(customers, 1):
                name = cust['name']
                pid = cust['pid']
                target_url = f"{BASE_URL}/jissekis/editCustomer/{pid}"

                progress = 30 + int((idx / total) * 60)
                self.update_progress(
                    progress, f"[{idx}/{total}] {name} の処理中...")
                logger.info(f"[{idx}/{total}] {name} (PID: {pid}) の処理を開始...")

                try:
                    # ページに移動（URLパラメータで年月を指定してみる）
                    # ただし、この方法が動作しない可能性もあるので、通常のURLも試す
                    target_url_with_params = f"{target_url}?year={target_year}&month={target_month}"
                    self.driver.get(target_url_with_params)

                    # ページが完全に読み込まれるまで待機（Render環境対応）
                    # まず、基本的な要素が読み込まれるまで待機
                    try:
                        self.wait.until(EC.presence_of_element_located(
                            (By.CSS_SELECTOR, "body")))
                        # JavaScriptの実行が完了するまで待機
                        for ready_check in range(5):  # 最大5秒待機
                            ready_state = self.driver.execute_script("return document.readyState")
                            if ready_state == "complete":
                                break
                            time.sleep(1)
                        time.sleep(2)  # 追加の待機時間（Render環境では長めに）
                    except:
                        time.sleep(2)  # フォールバック

                    # serviceDate要素が存在するまで待機（タイムアウトを延長）
                    service_date_found = False
                    for wait_attempt in range(10):  # 最大10秒待機
                        try:
                            self.wait.until(EC.presence_of_element_located(
                                (By.ID, "serviceDate")))
                            # 要素が実際に値を持っているか確認
                            current_date_val = self.driver.execute_script(
                                "var el = document.getElementById('serviceDate'); return el && el.value ? el.value : null;")
                            if current_date_val:
                                service_date_found = True
                                break
                        except:
                            pass
                        time.sleep(1)
                        logger.debug(f"  serviceDate要素を待機中... ({wait_attempt + 1}/10)")

                    if not service_date_found:
                        logger.warning(
                            "  serviceDate要素が見つかりません（URLパラメータ確認をスキップ）")
                        current_date_val = None
                    else:
                        logger.info(f"  serviceDate要素を確認: {current_date_val}")

                    target_year_month = f"{target_year}-{target_month:02d}"

                    if current_date_val:
                        current_year_month = "-".join(
                            current_date_val.split("-")[:2])
                        if current_year_month == target_year_month:
                            logger.info(
                                f"  URLパラメータで年月が正しく設定されました: {current_date_val}")
                            # テーブルが読み込まれるまで待機
                            try:
                                self.wait.until(EC.presence_of_element_located(
                                    (By.CSS_SELECTOR, ".list_table")))
                            except:
                                pass
                            time.sleep(0.5)
                            # 年月設定をスキップしてデータ抽出へ
                            date_set_success = True
                        else:
                            # 通常の年月設定処理を実行
                            date_set_success = None
                    else:
                        # 通常の年月設定処理を実行
                        date_set_success = None

                    # 年月を設定（URLパラメータで設定できなかった場合のみ）
                    if date_set_success is None:
                        date_set_success = self.ensure_list_view_and_date(
                            target_year, target_month)

                    if not date_set_success:
                        logger.error(f"  {name}: 年月の設定に失敗しました")
                        all_results[name] = []
                        continue

                    # データを抽出
                    data = self.scrape_schedule_table()

                    if len(data) == 0:
                        logger.warning(f"  {name}: データが0件でした。")
                        # 現在の日付を確認
                        try:
                            current_date = self.driver.execute_script(
                                "return document.getElementById('serviceDate').value")
                            logger.info(f"  現在表示されている日付: {current_date}")
                        except:
                            pass

                    all_results[name] = data
                    logger.info(f"  -> {name}: {len(data)}件のデータを取得しました")

                except Exception as e:
                    logger.error(f"  -> {name} の処理失敗: {e}")
                    import traceback
                    logger.error(traceback.format_exc())
                    # エラーが発生しても空のリストを追加（全員分の記録を保持）
                    all_results[name] = []

            # 3. CSV保存とログ出力
            logger.info(f"全員分の処理が完了しました。取得した利用者数: {len(all_results)}名")
            self.update_progress(95, "CSVファイルを保存しています...")
            self.save_to_csv(target_year, target_month,
                             all_results, target_day)
            self.update_progress(100, "処理が完了しました")
            self.close()
            return True
        except Exception as e:
            logger.error(f"実行エラー: {e}")
            self.update_progress(0, f"エラーが発生しました: {str(e)}")
            self.close()
            return False


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='かんたん介護スケジュール取得')
    parser.add_argument('--year', type=int, required=True, help='対象年')
    parser.add_argument('--month', type=int, required=True, help='対象月')
    parser.add_argument('--day', type=int, help='対象日（オプション）')
    parser.add_argument('--job-id', type=str, help='ジョブID（進捗管理用）')

    args = parser.parse_args()

    scraper = KantanKaigoFastScraper(headless=True)
    success = scraper.run(args.year, args.month, args.day)
    sys.exit(0 if success else 1)
