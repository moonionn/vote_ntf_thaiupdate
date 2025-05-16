import logging
import time
from datetime import datetime, timedelta
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException

from webdriver_manager.chrome import ChromeDriverManager

# ---名字配置 ---
NAME_NT = "Namtan Tipnaree"
NAME_FR = "Film Rachanun"
TO_EXE_NAME = NAME_NT # 實際名字 edit here (NAME_NT or NAME_FR)

# --- 配置 ---
TARGET_URL = "https://www.thaiupdate.info/the-best-glamorous-star-final/"
CANDIDATE_NAME_LOGGING = TO_EXE_NAME # 用於日誌記錄
CANDIDATE_NAME_TEXT_TO_FIND = TO_EXE_NAME # 用於 XPath 文本搜索

VOTE_INTERVAL_MINUTES = 5

# XPath 定位器
# 動態構建候選人選擇的 XPath
XPATH_CANDIDATE_SELECT_FORMAT_STRING = "//label[contains(normalize-space(.), '{}')]"
XPATH_VOTE_BUTTON = "//*[@id='post-63076']/div[2]/div[2]/div/div/div/div/form/div[5]/a"


# 設置日誌 (與之前版本相同)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("voting_bot.log"),
        logging.StreamHandler()
    ]
)

def setup_driver():
    # 此函數與上一版本相同，這裡省略以節省空間，實際腳本中應保留
    logging.info("開始設置 Chrome 驅動程式...")
    chrome_options = Options()
    # chrome_options.add_argument('--headless')
    chrome_options.add_argument('--no-sandbox') # ... 其他選項 ...
    chrome_options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/135.0.0.0 Safari/537.36')
    try:
        logging.info("使用 webdriver-manager 自動獲取 ChromeDriver...")
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=chrome_options)
        driver.execute_cdp_cmd('Page.addScriptToEvaluateOnNewDocument', {
            'source': '''Object.defineProperty(navigator, 'webdriver', {get: () => undefined})'''
        })
        logging.info("Chrome 驅動程式設置完成")
        return driver
    except Exception as e:
        logging.error(f"設置 ChromeDriver 時發生嚴重錯誤: {e}")
        raise

def check_vote_success(driver):
    try:
        logging.info("檢查投票結果...")
        time.sleep(2)  # 等待投票後頁面響應
        page_source = driver.page_source.lower()
        success_keyword = 'thank you for your vote'
        if success_keyword in page_source:
            logging.info(f"檢測到成功關鍵字: '{success_keyword}'")
            return True
        logging.warning("未檢測到成功關鍵字。投票結果未知。")
        return False
    except Exception as e:
        logging.error(f"檢查投票結果時發生錯誤：{str(e)}")
        return False

# --- vote_for_candidate ---
def vote_for_candidate(driver, candidate_name_text_for_search, candidate_name_for_log):
    # 使用 .format() 方法將候選人名字插入到 XPath 字符串中
    xpath_candidate_to_click = XPATH_CANDIDATE_SELECT_FORMAT_STRING.format(candidate_name_text_for_search)
    
    logging.info(f"準備投票給候選人: {candidate_name_for_log} (通過 XPath 文本搜索: '{candidate_name_text_for_search}')")
    logging.info(f"將使用的 XPath: {xpath_candidate_to_click}")
    logging.info(f"正在訪問投票頁面: {TARGET_URL}")
    driver.get(TARGET_URL)
    time.sleep(3)  # 增加等待時間，確保頁面完全加載

    try:
        # 1. 使用 JavaScript 選擇並點擊候選人
        logging.info(f"嘗試使用 XPath 選擇候選人 '{candidate_name_text_for_search}'...")
        candidate_element = WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.XPATH, xpath_candidate_to_click))
        )
        
        # 先滾動到候選人元素位置
        driver.execute_script("arguments[0].scrollIntoView(true);", candidate_element)
        time.sleep(1)  # 等待滾動完成
        
        # 使用 JavaScript 點擊
        driver.execute_script("arguments[0].click();", candidate_element)
        logging.info(f"已通過 JavaScript 點擊包含文本 '{candidate_name_text_for_search}' 的候選人選擇元素。")
        
        time.sleep(1)  # 增加點擊後的等待時間

        # 2. 使用 JavaScript 點擊投票按鈕
        logging.info(f"嘗試使用 XPath 點擊投票按鈕: {XPATH_VOTE_BUTTON}")
        vote_button_element = WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.XPATH, XPATH_VOTE_BUTTON))
        )
        
        # 先滾動到投票按鈕位置
        driver.execute_script("arguments[0].scrollIntoView(true);", vote_button_element)
        time.sleep(1)  # 等待滾動完成
        
        # 使用 JavaScript 點擊
        driver.execute_script("arguments[0].click();", vote_button_element)
        logging.info("已通過 JavaScript 點擊投票按鈕。")
        
        return True
        
    except TimeoutException:
        logging.error(f"使用 XPath 定位元素超時 (候選人: {candidate_name_text_for_search})。請檢查 XPath 和候選人名字是否正確。")
        return False
    except Exception as e:
        logging.error(f"執行 XPath 投票操作時發生錯誤 (候選人: {candidate_name_text_for_search}): {str(e)}")
        return False

# --- main_vote_process 和 wait_until_next_vote_cycle 與上一版本相似 ---
def main_vote_process():
    driver = None 
    try:
        driver = setup_driver()
        # 將實際用於搜索的文本和用於日誌的名字傳遞給函數
        if vote_for_candidate(driver, CANDIDATE_NAME_TEXT_TO_FIND, CANDIDATE_NAME_LOGGING):
            if check_vote_success(driver): # 檢查投票結果
                logging.info(f"成功為 {CANDIDATE_NAME_LOGGING} 投票！")
            else:
                logging.warning(f"為 {CANDIDATE_NAME_LOGGING} 投票後，未能確認成功狀態。請檢查日誌。")
        else:
            logging.error(f"為 {CANDIDATE_NAME_LOGGING} 的投票流程未能成功執行選擇或提交步驟。")
        time.sleep(2)
    except Exception as e:
        logging.error(f"在主投票過程中發生錯誤: {str(e)}")
    finally:
        if driver:
            logging.info("關閉瀏覽器...")
            driver.quit()
            logging.info("瀏覽器已關閉。")

def wait_until_next_vote_cycle(interval_minutes):
    now = datetime.now()
    next_vote_time = now + timedelta(minutes=interval_minutes)
    # ... (其餘等待邏輯)
    logging.info(f"下次投票計劃時間: {next_vote_time.strftime('%Y-%m-%d %H:%M:%S')}")
    while datetime.now() < next_vote_time:
        # ... (休眠和日誌記錄)
        remaining_delta = next_vote_time - datetime.now()
        remaining_seconds_total = int(remaining_delta.total_seconds())
        sleep_duration = min(60, remaining_seconds_total) if remaining_seconds_total > 0 else 1
        if remaining_seconds_total > 0 :
            remaining_minutes = remaining_seconds_total // 60
            remaining_seconds_part = remaining_seconds_total % 60
            logging.info(f"距離下次投票還有 {remaining_minutes} 分鐘 {remaining_seconds_part} 秒。休眠 {sleep_duration} 秒。")
        time.sleep(sleep_duration)


if __name__ == "__main__":
    logging.info(f"投票機器人開始執行，目標候選人: {CANDIDATE_NAME_LOGGING}")
    run_count = 0
    while True:
        run_count += 1
        logging.info(f"--- 開始第 {run_count} 輪投票 ---")
        try:
            main_vote_process()
            logging.info(f"--- 第 {run_count} 輪投票流程結束 ---")
            wait_until_next_vote_cycle(VOTE_INTERVAL_MINUTES)
        except KeyboardInterrupt:
            logging.info("程式被使用者手動中斷。正在退出...")
            break
        except Exception as e: 
            logging.critical(f"主循環中發生未捕獲的嚴重錯誤: {str(e)}")
            logging.critical(f"由於發生嚴重錯誤，腳本將在 {VOTE_INTERVAL_MINUTES} 分鐘後嘗試重試。")
            time.sleep(VOTE_INTERVAL_MINUTES * 60)