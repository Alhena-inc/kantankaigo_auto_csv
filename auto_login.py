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
            self.driver.find_element(By.ID, "headMenuCustomer").click()
            self.wait.until(EC.presence_of_element_located(
                (By.ID, "customerList")))
        except:
            self.driver.get(f"{BASE_URL}/customers")

        customers = []
        try:
            # PID属性から取得
            elements = self.driver.find_elements(
                By.CSS_SELECTOR, "span.planJisseki")

            for el in elements:
                try:
                    pid = el.get_attribute("pid")
                    if not pid:
                        continue

                    # 名前を取得
                    try:
                        row = el.find_element(By.XPATH, "./ancestor::tr")
                        name_el = row.find_element(By.CSS_SELECTOR, "a.focus")
                        name = name_el.text.strip()
                    except:
                        name = f"利用者ID_{pid}"

                    customers.append({"name": name, "pid": pid})
                except Exception:
                    continue

            logger.info(f"合計 {len(customers)} 名の利用者IDを取得しました")
            return customers
        except Exception as e:
            logger.error(f"利用者リスト取得エラー: {e}")
            return []

    def ensure_list_view_and_date(self, target_year, target_month):
        """カレンダーの年月を合わせる処理"""
        try:
            current_date_val = self.driver.execute_script(
                "return document.getElementById('serviceDate').value")
            target_str = f"{target_year}/{target_month:02d}"

            if target_str in current_date_val:
                return True

            logger.info(
                f"  日付変更: {current_date_val} -> {target_year}年{target_month}月")
            self.driver.execute_script("$('.ui-monthpicker-trigger').click();")
            time.sleep(0.5)

            try:
                year_select = Select(self.driver.find_element(
                    By.CSS_SELECTOR, "select.ui-datepicker-year"))
                year_select.select_by_value(str(target_year))
            except:
                pass

            try:
                month_select = Select(self.driver.find_element(
                    By.CSS_SELECTOR, "select.ui-datepicker-month"))
                month_select.select_by_value(str(target_month - 1))
            except:
                pass

            try:
                ok_btns = self.driver.find_elements(
                    By.CSS_SELECTOR, ".ui-datepicker-ok, button.ui-priority-primary")
                if ok_btns:
                    ok_btns[0].click()
                    time.sleep(1.5)
            except:
                pass
            return True

        except Exception as e:
            logger.warning(f"  日付変更処理でエラー(無視して続行): {e}")
            return False

    def scrape_schedule_table(self):
        """一覧形式のテーブルからデータを抽出"""
        schedules = []
        try:
            dates = self.driver.find_elements(By.CSS_SELECTOR, ".day.edit")
            times = self.driver.find_elements(By.CSS_SELECTOR, ".time.edit")
            services = self.driver.find_elements(
                By.CSS_SELECTOR, ".service.edit")
            staffs = self.driver.find_elements(By.CSS_SELECTOR, ".staff.edit")

            loop_count = len(dates)
            for i in range(loop_count):
                date_txt = dates[i].text.strip()
                if not date_txt:
                    continue

                schedules.append({
                    "date": date_txt,
                    "time": times[i].text.strip() if i < len(times) else "",
                    "service": services[i].text.strip() if i < len(services) else "",
                    "staff": staffs[i].text.strip() if i < len(staffs) else ""
                })

        except Exception as e:
            logger.warning(f"  データ抽出エラー: {e}")

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
            for name, scheds in results.items():
                logger.info(f"  - {name}: {len(scheds)}件")
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
                logger.info(f"[{idx}/{total}] {name} の処理中...")

                try:
                    self.driver.get(target_url)
                    self.ensure_list_view_and_date(target_year, target_month)
                    data = self.scrape_schedule_table()
                    all_results[name] = data
                    logger.info(f"  -> {name}: {len(data)}件のデータを取得しました")
                except Exception as e:
                    logger.error(f"  -> {name} の処理失敗: {e}")
                    # エラーが発生しても空のリストを追加（全員分の記録を保持）
                    all_results[name] = []
                    import traceback
                    logger.error(traceback.format_exc())

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
