from playwright.sync_api import sync_playwright, Playwright
from bs4 import BeautifulSoup
import re
import pandas as pd
import requests
def run(playwright: Playwright):
   chromium = playwright.chromium # or "firefox" or "webkit".
   browser = chromium.launch(headless=True)
   page = browser.new_page()
   page.goto("http://vnha.org.vn/member.asp")
   pagation = page.get_by_role("table").filter(has_text="trong tổng số").filter(has_not_text="TÌM KIẾM HỘI VIÊN").filter(has_not_text="Danh sách hội viên").filter(has_not_text="Hội viên chính thức")
   pattern = r"Trang \d+ trong tổng số \d+ trang \(\d+ tin\)"
   page_num_info = re.findall(pattern,pagation.all_inner_texts()[0])[0]
   page_num_info = re.findall(r"\d+",page_num_info)
   total_page_num = int(page_num_info[1]) # Get the total number of pages
   data = pd.DataFrame(columns=["Id","Tên Hội viên","Đơn vị","Ngày cập nhật","Link profile"])
   for i in range(total_page_num):
      print("Current page: " + str(i+1))
      if i != 0:
         pagation = page.get_by_role("table").filter(has_text="trong tổng số").filter(has_not_text="TÌM KIẾM HỘI VIÊN").filter(has_not_text="Danh sách hội viên").filter(has_not_text="Hội viên chính thức")
         pagation.get_by_text(">>").click()
         # another option is locate the button using CSS: page.locator('.paging').get_by_text(">>").click()
         page.wait_for_timeout(2000)
      html = page.inner_html("body")
      soup = BeautifulSoup(html,'html.parser')
      rows = soup.select('table > tbody > tr')
      for row in rows:
         cols = row.find_all('td')
         fields = [td.text.strip() for td in cols if td.text.strip()]
         if fields: # if the row is not empty
            try:
               fields[0] = int(fields[0])
            except:
               continue
         if len(fields) == 4:  
            fields_data = {
               'Id': fields[0],
               "Tên Hội viên":fields[1],
               "Đơn vị":fields[2],
               "Ngày cập nhật":fields[3],
               "Link profile":row.find("a")['href']
               }
         elif len(fields) == 3:
            fields_data = {
               'Id': fields[0],
               "Tên Hội viên":fields[1],
               "Ngày cập nhật":fields[2],
               "Link profile":row.find("a")['href']
               }
         else:
            continue
         fields_data = pd.DataFrame(fields_data,index=[0])
         data = pd.concat([data,fields_data],ignore_index = True)
   data.to_csv("list_of_members.csv",encoding='utf-16') # Panda doesn't work well in processing Vietnamese text by defauly encoding='utf-16' is important

with sync_playwright() as playwright:
   run(playwright)

def get_profile_detail(link_profiles):
   df = pd.DataFrame()
   for link_profile in link_profiles:
      print("Current profile: " + link_profile)
      data = pd.read_html("http://vnha.org.vn/"+link_profile)[-4]
      dict = {
         "Link profile": str(link_profile),
         "Chức vụ":data[1][2],
         "Địa chỉ":data[1][3],
         "Điện thoại cơ quan":data[1][4],
         "Email":data[1][5],
         "Tình trạng hội viên":data[1][6]
         }
      df = pd.concat([df,pd.DataFrame(dict,index=[0])],ignore_index = True)
   return df

memberships_data = pd.read_csv('list_of_members.csv',encoding='utf-16')
profile_details = get_profile_detail(memberships_data["Link profile"])
final_data = memberships_data.set_index("Link profile").join(profile_details.set_index("Link profile"))
final_data.to_csv("final_data.csv",encoding='utf-16')







