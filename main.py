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
        
        # 使用 JavaScript 檢查邊框顏色
        border_color = driver.execute_script("""
            const messageDiv = document.querySelector('.basic-message.basic-success');
            if (messageDiv) {
                // 獲取計算後的樣式
                const style = window.getComputedStyle(messageDiv);
                // 獲取 border-left-color
                return style.getPropertyValue('border-left-color');
            }
            return 'not found';
        """)
        
        # logging.info(f"檢測到訊息邊框顏色: {border_color}")
        
        # 檢查邊框顏色是否為綠色 (#008000)
        if '#008000' in border_color:
            logging.info("檢測到成功指示：邊框顏色為綠色 (#008000)")
            return True
        else:
            logging.warning("檢測到失敗指示：邊框顏色為紅色 (#ff0000)")
            return False
    except Exception as e:
        logging.error(f"檢查投票結果時發生錯誤：{str(e)}")
        return False

# --- vote_for_candidate ---
def vote_for_candidate(driver, candidate_name_text_for_search, candidate_name_for_log):
    # 使用 .format() 方法將候選人名字插入到 XPath 字符串中
    xpath_candidate_to_click = XPATH_CANDIDATE_SELECT_FORMAT_STRING.format(candidate_name_text_for_search)
    
    logging.info(f"準備投票給候選人: {candidate_name_for_log}")
    # logging.info(f"將使用的 XPath: {xpath_candidate_to_click}")
    logging.info(f"正在訪問投票頁面: {TARGET_URL}")
    driver.get(TARGET_URL)
    time.sleep(3)  # 增加等待時間，確保頁面完全加載

    try:
        # 檢查投票按鈕是否為 display: none
        vote_button_display = driver.execute_script(
            """
            const voteButton = document.querySelector('.basic-vote-button');
            if (voteButton) {
                return window.getComputedStyle(voteButton).getPropertyValue('display');
            }
            return "unknown";
            """
        )
        
        if vote_button_display == "none":
            logging.info(f"檢測到投票按鈕為 display: none，已經為 {candidate_name_for_log} 投票！")
            return "already_voted"  # 返回特殊標記表示已投票
        
        logging.info(f"投票按鈕顯示狀態: {vote_button_display}，將繼續投票流程。")
        
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

def main_vote_process():
    driver = None 
    result_status = "unknown"  # 設置一個默認的狀態
    
    try:
        driver = setup_driver()
        # 將實際用於搜索的文本和用於日誌的名字傳遞給函數
        vote_result = vote_for_candidate(driver, CANDIDATE_NAME_TEXT_TO_FIND, CANDIDATE_NAME_LOGGING)
        
        if vote_result == "already_voted":
            # 如果已經投票，直接返回，不進行後續檢查
            logging.info(f"已經為 {CANDIDATE_NAME_LOGGING} 投過票，跳過投票結果檢查。")
            result_status = "already_voted"
        elif vote_result:
            # 只有在實際執行投票操作成功時才檢查投票結果
            if check_vote_success(driver): 
                logging.info(f"成功為 {CANDIDATE_NAME_LOGGING} 投票！")
                result_status = "vote_success"
            else:
                logging.warning(f"為 {CANDIDATE_NAME_LOGGING} 投票後，未能確認成功狀態。請檢查日誌。")
                result_status = "vote_unknown"
        else:
            logging.error(f"為 {CANDIDATE_NAME_LOGGING} 的投票流程未能成功執行選擇或提交步驟。")
            result_status = "vote_failed"
        
    except Exception as e:
        logging.error(f"在主投票過程中發生錯誤: {str(e)}")
        result_status = "error"
    finally:
        if driver:
            logging.info("關閉瀏覽器...")
            driver.quit()
            logging.info("瀏覽器已關閉。")
    
    return result_status  # 返回投票結果狀態

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
            logging.info(f"距離下次投票還有 {remaining_minutes} 分鐘 {remaining_seconds_part} 秒。")
        time.sleep(sleep_duration)


if __name__ == "__main__":
    logging.info(f"投票機器人開始執行，目標候選人: {CANDIDATE_NAME_LOGGING}")
    run_count = 0
    success_count = 0  # 新增變數來追蹤成功投票次數
    
    # 定義不同狀態的等待時間（分鐘）
    wait_times = {
        "vote_success": VOTE_INTERVAL_MINUTES,   # 成功投票後等待5分鐘
        "already_voted": 1,                      # 已投票狀態等待1分鐘
        "vote_unknown": 2,                       # 投票結果未知等待2分鐘
        "vote_failed": 3,                        # 投票失敗等待3分鐘
        "error": 1,                              # 錯誤情況等待1分鐘
        "unknown": VOTE_INTERVAL_MINUTES         # 未知狀態使用默認值
    }
    
    while True:
        run_count += 1
        logging.info(f"--- 開始第 {run_count} 輪投票 ---")
        try:
            # 執行投票流程並獲取結果狀態
            vote_status = main_vote_process()
            
            # 如果投票成功，增加成功計數
            if vote_status == "vote_success":
                success_count += 1
            
            # 記錄投票狀態和累計成功次數
            logging.info(f"--- 第 {run_count} 輪投票流程結束，狀態: {vote_status}，累計成功投票次數: {success_count} ---")
            
            # 根據狀態決定等待時間
            wait_time = wait_times.get(vote_status, VOTE_INTERVAL_MINUTES)
            logging.info(f"將等待 {wait_time} 分鐘後進行下一輪投票")
            
            # 使用適當的等待時間
            wait_until_next_vote_cycle(wait_time)
            
        except KeyboardInterrupt:
            logging.info(f"程式被使用者手動中斷。正在退出... 總共成功投票 {success_count} 次")
            break
        except Exception as e: 
            logging.critical(f"主循環中發生未捕獲的嚴重錯誤: {str(e)}")
            logging.critical(f"由於發生嚴重錯誤，腳本將在 1 分鐘後嘗試重試。")
            time.sleep(60)  # 發生嚴重錯誤時只等待1分鐘