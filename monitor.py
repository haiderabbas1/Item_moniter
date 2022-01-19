from threading import Thread
from random import choice
import requests
import json
import time, random
from bs4 import BeautifulSoup
import os
from discord_webhook import DiscordWebhook, DiscordEmbed

currpath = os.getcwd()

with open(f'{currpath}/assets/config.json') as f:
    data = json.load(f)

with open(f"{currpath}/assets/proxies.txt", 'r') as file:
    proxyList = [proxy.strip() for proxy in file ]
    
with open(f"{currpath}/assets/skus.txt", 'r') as file:
    skuList = [sku.strip() for sku in file ]
    

timeWait = data["interval"]
discordWebhook = data["webhook"]

threads = []
    
headers = {
    'authority': 'cart.production.store-web.dynamics.com',
    'pragma': 'no-cache',
    'cache-control': 'no-cache',
    'ms-cv': '',
    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/93.0.4577.63 Safari/537.36',
    'content-type': 'application/json',
    'accept': '*/*',
    'sec-gpc': '1',
    'origin': 'https://www.microsoft.com',
    'sec-fetch-site': 'cross-site',
    'sec-fetch-mode': 'cors',
    'sec-fetch-dest': 'empty',
    'referer': 'https://www.microsoft.com/',
    'accept-language': 'en-US,en;q=0.9',
}

def startup():
    for itemInfo in skuList:
        t = Thread(target=check, args=(itemInfo,))
        t.start()


def check(itemInfo):
    
        link, skuID = itemInfo.split("|") # This replicates.
        productID = link.split("/")[-1]
        instock = False

        try:
            initial_value_getter(link)
        except:
            print("Error while getting info. Trying again.")
            check(itemInfo)

        availabilityId =  random.randint(100000000000,900000000000)
        post_data =  {"itemsToCheck":[ {"productId": productID, "availabilityId": availabilityId, "skuId": skuID, "distributorId":"9000000013", "isPreOrder":False}]}

        while True:
            try:
                print(f"Searching For Stock on SKU {productID}")
                time.sleep(timeWait)
                proxySingle = choice(proxyList) 
                proxy = {'https': f'http://{proxySingle}'}
                page = requests.put('https://cart.production.store-web.dynamics.com/cart/v1.0/Cart/checkProductInventory?market=GB&appId=storeCart', headers=headers, json = post_data, proxies = proxy).json()
                
                if page['productInventory'][f"{productID}/{skuID}/{availabilityId}"][0]['inStock'] != False and not instock:  # if its sold and instock = false
                    alert(product_price, product_name, product_image_link, link, productID)
                    print("Stock Found and Webhook Called")

                elif page['productInventory'][f"{productID}/{skuID}/{availabilityId}"][0]['inStock'] == False:
                    instock = False
                    print("Out of Stock")
    
            except KeyboardInterrupt:
                print("Exiting Code in 5 seconds")
                time.sleep(5)
                exit()
    
            except:
                print("Proxy Error | Trying on a new proxy")
                pass
            
    
def initial_value_getter(link):
    global product_name, product_image_link, product_price
    product_page = requests.get(link)
    soup = BeautifulSoup(product_page.text, 'lxml')
    product_name = soup.find('h1', class_ = "mb-sm-3 mb-2 h2").get_text()
    product_image_link = soup.find('img', class_ = 'img-fluid BundleBuilderHeader-module__productImage___2CnwL pb-2').attrs['src']
    product_price = soup.find('h2', class_ = 'pb-1 my-0').get_text()
    return 0


def alert(price, name, image, productLink, sku):
    webhook = DiscordWebhook(url=f"{discordWebhook}")
    embed = DiscordEmbed(
        title="Microsoft", description=f'[**{name}**]({productLink})', color=655104)
    embed.set_timestamp()
    embed.set_thumbnail(url=f'{image}')
    embed.add_embed_field(name="**Notification Type**", value="**Restock**", inline = False)
    embed.add_embed_field(name="**Sku**", value=f"**{sku}**" , inline = False)
    embed.add_embed_field(name="**Price**", value=f"**{price}**" , inline = False)

    webhook.add_embed(embed)
    response = webhook.execute()


startup()