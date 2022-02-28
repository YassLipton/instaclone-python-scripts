from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options

from datetime import datetime
import urllib.request
import boto3
import time
import pymongo
from bson.objectid import ObjectId
from bson.timestamp import Timestamp

def countdown(t):
    while t:
        mins, secs = divmod(t, 60)
        timer = '{:02d}:{:02d}'.format(mins, secs)
        print(timer, end="\r")
        time.sleep(1)
        t -= 1

def Wait_And_Click(driver, element, index=None):
    wait_init = WebDriverWait(driver, 10)

    if not index:
        wi = wait_init.until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, element)))
    else:
        wi = wait_init.until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, f'{element}:nth-of-type({index})')))

    if not index:
        driver.execute_script(f"""document.querySelector('{element}').click()""", wi)
    else:
        driver.execute_script(f"""document.querySelectorAll('{element}')[{index}].click()""", wi)

class Scraper():

    def __init__(self):
        options = Options()
        #options.headless = True
        self.driver = webdriver.Chrome(options=options)

    def connect(self, username, password):
        driver = self.driver

        driver.get('https://www.instagram.com/')

        Wait_And_Click(self.driver, 'button.bIiDR')

        countdown(1)

        try:
            wait_init0 = WebDriverWait(driver, 10)

            it0 = wait_init0.until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, 'input[type="text"]')))

            usernameInput = driver.find_element_by_css_selector('input[type="text"]')
            passwordInput = driver.find_element_by_css_selector('input[type="password"]')

            usernameInput.send_keys(username)
            passwordInput.send_keys(password)

            countdown(1)

            driver.execute_script("""document.querySelector('button[type="submit"]').click()""", it0)

            countdown(2)
        except:
            print('cannot connect')
            exit()

    def scrapAndSave(self, profile, CONNECTION_URI, AWS_ACCESS_KEY, AWS_SECRET_KEY):
        driver = self.driver

        driver.get(f'https://www.instagram.com/{profile}')

        countdown(3)

        myClient = pymongo.MongoClient(CONNECTION_URI)
        myDB = myClient["insta"]
        User = myDB["users"]
        Post = myDB["posts"]

        def upload_to_aws(local_file, bucket, s3_file):
            s3 = boto3.client('s3', aws_access_key_id=AWS_ACCESS_KEY, aws_secret_access_key=AWS_SECRET_KEY)
            s3.upload_file(local_file, bucket, s3_file, ExtraArgs={'ACL': 'public-read'})

        def ProfileData():
            currentTime = time.mktime(datetime.now().timetuple())

            img = driver.execute_script("""return document.querySelector('img[data-testid="user-avatar"]').src""")

            filename = f"images/{currentTime}_user.jpg"

            urllib.request.urlretrieve(img, filename)

            upload_to_aws(filename, 'instaclone-assets', filename)

            profileData = driver.execute_script(f"""
                const img = document.querySelector('img[data-testid="user-avatar"]').src
                const username = document.querySelector('h2').innerText
                const isVerified = (document.querySelector('span[title="Vérifié"]') !== null)
                const fullName = document.querySelectorAll('.vy6Bb')[3].innerText
                const bio = document.querySelectorAll('.vy6Bb')[4].innerText
                const link = document.querySelectorAll('.vy6Bb')[5].innerText

                const profileData = {{
                  username,
                  password: '721c6ff80a6d3e4ad4ffa52a04c60085',
                  fullName,
                  email: undefined,
                  phone: undefined,
                  bio,
                  link,
                  isPrivate: false,
                  isVerified,
                  profilePicUrl: 'https://instaclone-assets.s3.eu-west-3.amazonaws.com/{filename}',
                  followers: [],
                  following: [],
                }}

                return profileData
            """)
            return profileData

        self.last_inserted_user = User.insert_one(ProfileData())

        def PostsData(userId):
            allPosts = []

            wait_init1 = WebDriverWait(driver, 10)

            it1 = wait_init1.until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, 'div.CzVzU')))

            oneImageIndexes = driver.execute_script("""
                const allBoxes = document.querySelectorAll('div._bz0w')
                let oneImageIndexes = []

                for (let i = 0; i < allBoxes.length; i++) {
                  if (allBoxes[i].querySelector('div.CzVzU') == null) {
                    oneImageIndexes.push(i)
                  }
                }

                return oneImageIndexes
            """, it1)

            print(oneImageIndexes)

            numberOfPostsToScrap = len(oneImageIndexes)

            for i in range(numberOfPostsToScrap):
                driver.execute_script(
                    f"document.querySelectorAll('div._bz0w')[{oneImageIndexes[i]}].querySelector('a').click()")

                wait_init2 = WebDriverWait(driver, 10)

                it2 = wait_init2.until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, 'div.kPFhm')))

                currentTime = time.mktime(datetime.now().timetuple())

                img = driver.execute_script("return document.querySelector('div.kPFhm').querySelector('img').src")

                filename = f"images/{currentTime}_post.jpg"

                urllib.request.urlretrieve(img, filename)

                upload_to_aws(filename, 'instaclone-assets', filename)

                currentPost = driver.execute_script(f"""
                    const img = document.querySelector('div.kPFhm').querySelector('img').src
                    const caption = document.querySelectorAll('span.T0kll')[1].childNodes[0].nodeValue
                    const currentPost = {{
                        images: [{{
                          index: 0,
                          link: 'https://instaclone-assets.s3.eu-west-3.amazonaws.com/{filename}'
                        }}],
                        comments: [],
                        caption,
                        location: '',
                        usersWhoLiked: []
                  }}
                    return currentPost
                """, it2)

                currentPost['user'] = ObjectId(userId)
                currentPost['updatedAt'] = Timestamp(int(datetime.now().timestamp()), 1)
                currentPost['createdAt'] = Timestamp(int(datetime.now().timestamp()), 1)

                allPosts.append(currentPost)

                Post.insert_one(currentPost)

            return allPosts

        PostsData(self.last_inserted_user.inserted_id)

    def close(self):
        self.driver.close()

s = Scraper()
s.connect('<Instagram account username>', '<Instagram account password>')
s.scrapAndSave(
    profile='<profile to scrap>',
    CONNECTION_URI="<MongoDB connection url>",
    AWS_ACCESS_KEY = '<AWS API access key>',
    AWS_SECRET_KEY = '<AWS API secret key>'
)
s.close()