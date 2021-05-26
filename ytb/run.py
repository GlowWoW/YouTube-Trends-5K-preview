#Для запуска должен быть установлен список шрифтов и быть продублирован .ttf или  .otf файлами по пути "/ytb/fonts", Roboto-основной шрифт на YouTube, для остальных локальных языков-Arial (или более подходящие, если есть). Пока не разобрался с лицензированием, поэтому не имею права их выкладывать на Github
#Аналогично-эмодзи в версии Microsoft должны быть сохранены по пути "/ytb/emj", были получены из этого списка https://emojipedia.org/microsoft/ в расширении 120x120, оригинальные названия сохранены
#Кроме указанных ниже библиотек, необходимо установить libraqm для поддержки кернинга шрифтов, потому что в Windows по умолчанию кернинг не предусмотрен для использования с помощью PIL. https://www.lfd.uci.edu/~gohlke/pythonlibs/#pillow установить libraqm в: Путь_до_папки_пользователя/vcpkg-master/ports)
#Возможность создания видео-превью включается изменением 2-го аргумента на True в вызове get_video

import ffmpeg
import subprocess
import youtube_dl
from requests_html import HTMLSession
import requests
from bs4 import BeautifulSoup as bs
import json
import urllib.request
import os
from PIL import ImageFont
from PIL import Image
from PIL import ImageDraw
import textwrap
from PIL import ImageFilter
import emoji
from langdetect import detect
from langdetect import detect_langs
import re
from operator import itemgetter
from fontTools.ttLib import TTFont
import sys
import time as time_out
from googleapiclient.discovery import build
from datetime import datetime
import pytz
import io
import unicodedata
import shutil
import random
from datetime import timedelta
import pathlib
from zones import time_zones
from colors import color_like

folder=(str(pathlib.Path(__file__).parent.parent.absolute())).replace("\\","") 
session = HTMLSession()
font_rect = ImageFont.truetype(folder+"/ytb/fonts/Roboto-Medium.ttf", 62)
font_roboto_thin = ImageFont.truetype(folder+"/ytb/fonts/Roboto-Thin.ttf", 150)
font_emoji_descr = ImageFont.truetype(folder+"/ytb/fonts/seguiemj.ttf", 70)
font_emoji_main = ImageFont.truetype(folder+"/ytb/fonts/seguiemj.ttf", 95)
font_Roboto = TTFont(folder+"/ytb/fonts/Roboto-Regular.ttf")
font0=folder+"/ytb/fonts/{0}"
# цвет текста, RGB
color_main = (3,3,3)
color_descr = (96,96,96)
color_soft = (204,204,204)
color_time = (255,255,255)
#Название шрифта, Язык, Отступ главного шрифта, Отступ малого шрифта
locals=(["arial.ttf","All not Roboto","0","0"])
"""
locals=(["malgun.ttf", "Korean","-16","-11"],
["Nirmala.ttf", "Hindi","-14","-9"],
["arial.ttf","Arabic or symbols","0","0"],
["seguiemj.ttf","emoji","0","15"])
"""

#Конвертация в актуальный часовой пояс страны 
def good_timezone_converter(input_dt, current_tz, target_tz): 
    current_tz = pytz.timezone(current_tz) 
    target_tz = pytz.timezone(target_tz) 
    target_dt = current_tz.localize(input_dt).astimezone(target_tz) 
    return target_tz.normalize(target_dt) 

#Проверка на наличие символа в шрифте
def char_in_font(unicode_char, font):
    for cmap in font["cmap"].tables:
        if cmap.isUnicode():
            if ord(unicode_char) in cmap.cmap:
                return True
    return False

#Функция скругления угла для прямоугольника длительности видео
def round_corner(radius, fill):
    corner = Image.new('RGBA', (radius, radius), (0, 0, 0, 0))
    draw = ImageDraw.Draw(corner)
    draw.pieslice((0, 0, radius*2, radius*2), 180, 270, (0,0,0,204))
    return corner

#Функция для создания прямоугольника длительности видео
def round_rectangle(size, radius, fill):
    width, height = size
    rectangle = Image.new('RGBA', size, (0,0,0,204))
    corner = round_corner(radius, (0,0,0,0))
    rectangle.paste(corner, (0, 0))
    rectangle.paste(corner.rotate(90), (0, height - radius))  # Rotate the corner and paste it
    rectangle.paste(corner.rotate(180), (width - radius, height - radius))
    rectangle.paste(corner.rotate(270), (width - radius, 0))
    return rectangle
    


#Основная функция
def get_video_info(url,video_preview,api_key):    
    print("Выберите страну по номеру:\n0. Австралия\n12. Бразилия\n13. Великобритания\n19. Германия\n29. Индия\n39. Канада\n55. Мексика \n72. Россия\n82. США\n98. Швейцария")
    country = int(input())
    
    print("Ведите диапазон трендов, от 1 до 50\nПервое значение:") 
    start=int(input())
    print("Второе значение:") 
    finish =int(input())
     
    headers = {
    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/84.0.4147.125 Safari/537.36'
    ,'cookie': time_zones[country][3]
    }
    headers_mobile = {
    'user-agent': 'Mozilla/5.0 (Linux; Android 9; SM-G950F Build/PPR1.180610.011; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/74.0.3729.157 Mobile Safari/537.36'
    ,'cookie': time_zones[country][3]
    }
    response = session.get(url,headers=headers)    

        
    #Вычленение данных страницы в формате json 
    json_start=response.text.find("{\"responseContext\"")
    json_finish=response.text.find(";</script>",json_start)
    
    js_final=response.text[json_start:json_finish]
    d=json.loads(js_final)              
    videoRenderer00=(d["contents"]["twoColumnBrowseResultsRenderer"]["tabs"][0]["tabRenderer"]["content"]["sectionListRenderer"]["contents"][0]["itemSectionRenderer"]["contents"][0]["shelfRenderer"]["content"]["expandedShelfContentsRenderer"]["items"])
        
    if(len(d["contents"]["twoColumnBrowseResultsRenderer"]["tabs"][0]["tabRenderer"]["content"]["sectionListRenderer"]["contents"])>2):
        no_add_count=len(videoRenderer00)
        videoRenderer11=(d["contents"]["twoColumnBrowseResultsRenderer"]["tabs"][0]["tabRenderer"]["content"]["sectionListRenderer"]["contents"][2]["itemSectionRenderer"]["contents"][0]["shelfRenderer"]["content"]["expandedShelfContentsRenderer"]["items"])    
    else:
        no_add_count=999
    print("Число блоков=",len(d["contents"]["twoColumnBrowseResultsRenderer"]["tabs"][0]["tabRenderer"]["content"]["sectionListRenderer"]["contents"]))
    
    full_links=""
    Tags_text=""
    
    #Первые 10 трендов
    for cnt0 in range(start-1,finish):
        #Получение ID и превью
        if (cnt0>=no_add_count):          
            videoRenderer0=videoRenderer11[cnt0-no_add_count]
            video_id=videoRenderer0["videoRenderer"]["videoId"]
        else:
            videoRenderer0=videoRenderer00[cnt0]
            video_id=videoRenderer0["videoRenderer"]["videoId"]
        
        
        #Загрузка наилучшего превью из имеющихся на сервере
        way="https://i.ytimg.com/vi/{0}/maxresdefault.jpg"
        way=way.format(video_id) 
        time_out.sleep(2)
        print("#",cnt0+1)
        print(way)
        
        response = requests.get(way)
        wayopen=(folder+"/ytb/1Render/{1}/thumbnails/{0}.png").format(video_id,country)
        os.makedirs(os.path.dirname(wayopen), exist_ok=True)
        if response.status_code == 200:           
            i = Image.open(io.BytesIO(response.content))
            i.save(wayopen)
        else:
            way="https://i.ytimg.com/vi/{0}/sddefault.jpg"
            way=way.format(video_id) 
            response = requests.get(way)
            if response.status_code == 200:
                print("640x480")
                i = Image.open(io.BytesIO(response.content))
                area = (0, 60, 640, 420)
                i = i.crop(area)
                i = i.resize((1280,720),resample=Image.BILINEAR).convert("RGB")
                i.save(wayopen)
            else:
                way="https://i.ytimg.com/vi/{0}/hqdefault.jpg"
                way=way.format(video_id) 
                response = requests.get(way)
                if response.status_code == 200:
                    print("480x360")
                    i = Image.open(io.BytesIO(response.content))
                    area = (0, 60, 480, 300)
                    i = i.crop(area)
                    i = i.resize((1280,720),resample=Image.BILINEAR).convert("RGB")
                    i.save(wayopen)
        
        shutil.copyfile((folder+"/ytb/1Render/{1}/thumbnails/{0}.png").format(video_id,country), (folder+"/ytb/1Render/{1}/thumbnails_orig/{0}.png").format(cnt0+1,country))
                        
        
        url_mobile = "https://www.youtube.com/watch?v={0}"        
        url_mobile=url_mobile.format(video_id)
        full_links = full_links+"#"+str(cnt0+1)+" "+url_mobile+"\n"
        response_mobile = session.get(url_mobile,headers=headers)
        
        
        #Вычленение json конкретной страницы видео, сохранение данных видео в контексте требуемого языка
        json_start=response_mobile.text.find("ytInitialData = {\"responseContext\"")
        json_finish=response_mobile.text.find(";</script>",json_start)
        js_final=response_mobile.text[json_start+16:json_finish]
        d=json.loads(js_final)
        cut=d["contents"]["twoColumnWatchNextResults"]["results"]["results"]
        if "videoPrimaryInfoRenderer" in cut["contents"][0]:
            covid_sign=0
        else:
            covid_sign=1
        text_likes_cut=cut["contents"][covid_sign]["videoPrimaryInfoRenderer"]["videoActions"]["menuRenderer"]["topLevelButtons"][0]["toggleButtonRenderer"]["defaultText"]["simpleText"]
        text_dislikes_cut=cut["contents"][covid_sign]["videoPrimaryInfoRenderer"]["videoActions"]["menuRenderer"]["topLevelButtons"][1]["toggleButtonRenderer"]["defaultText"]["simpleText"]
        text_channel_link=cut["contents"][covid_sign+1]["videoSecondaryInfoRenderer"]["owner"]["videoOwnerRenderer"]["title"]["runs"][0]["navigationEndpoint"]["browseEndpoint"]["canonicalBaseUrl"]
        text_likes_cut=text_likes_cut.upper()
        text_dislikes_cut=text_dislikes_cut.upper()
 
        if "subscriberCountText" in cut["contents"][covid_sign+1]["videoSecondaryInfoRenderer"]["owner"]["videoOwnerRenderer"]:
            text_subscribers_cut=cut["contents"][covid_sign+1]["videoSecondaryInfoRenderer"]["owner"]["videoOwnerRenderer"]["subscriberCountText"]["simpleText"] #Округленное число подписчиков
            print("Subscribers=",text_subscribers_cut)
        else: #Если скрыто число подписчиков
            text_subscribers_cut=False            
        print("likes=",text_likes_cut,"dislikes=",text_dislikes_cut)
        
        youtube = build('youtube', 'v3', developerKey=api_key)
        
        #Число лайков дизлайков
        request = youtube.videos().list(
            part='statistics',
            id=video_id
        )
        #https://www.youtube.com/watch?v=pu9TYsgEV8E&persist_app=1&app=m
        response = request.execute()
        if "likeCount" in response['items'][0]['statistics']:
            text_likes=int(response['items'][0]['statistics']['likeCount'])
            text_dislikes=int(response['items'][0]['statistics']['dislikeCount'])        
            like_percent=round(text_likes/(text_likes+text_dislikes)*100) #Процент лайков
            print(text_likes,text_dislikes)
            print("Проценты",like_percent)
        else:
            text_likes=False
            print("Лайки скрыты")

        #Установка времени
        request = youtube.videos().list(
            part='snippet',
            id=video_id
        )
        response = request.execute()
        text_time_published=response['items'][0]['snippet']['publishedAt']
        tags=""
        if "tags" in response['items'][0]['snippet']:
            tags=', '.join(response['items'][0]['snippet']['tags'])
        time_published_region=good_timezone_converter(datetime.strptime(text_time_published,'%Y-%m-%dT%H:%M:%SZ'), current_tz='UTC', target_tz=time_zones[country][1])# target_tz='Etc/GMT-3')
        time_published_format=time_published_region.strftime(time_zones[country][2])
       
        
        if (videoRenderer0["videoRenderer"].get("ownerBadges",False)):
           badge=videoRenderer0["videoRenderer"]["ownerBadges"][0]["metadataBadgeRenderer"]["style"]
        else:
            badge=""
        
        time=videoRenderer0["videoRenderer"]["lengthText"]["simpleText"]
        text_main = videoRenderer0["videoRenderer"]["title"]["runs"][0]["text"]
        print(text_main)
        
        
        if "descriptionSnippet" in videoRenderer0["videoRenderer"]:
            text_descr = videoRenderer0["videoRenderer"]["descriptionSnippet"]["runs"][0]["text"] #Описание под видео
        else:
            text_descr=False
        text_channel=videoRenderer0["videoRenderer"]["longBylineText"]["runs"][0]["text"] #Название канала
        text_views=videoRenderer0["videoRenderer"]["shortViewCountText"]["simpleText"] #Округленное количество просмотров
        text_ago=videoRenderer0["videoRenderer"]["publishedTimeText"]["simpleText"]

        Tags_text=Tags_text+"#"+str(cnt0+1)+"   "+text_main+"\n   "+text_channel+"\n"+tags+"\n"


        #Загрузка отрывка видео и преобразование его в превью-формат (быстрый предпросмотр видео с низким фпс, по умолчанию отключено)
        if (video_preview):
            ydl = youtube_dl.YoutubeDL({'format': '22/136/best'})
            result = ydl.extract_info(('http://www.youtube.com/watch?v={0}').format(video_id),download=False)
            if (len(time)<6):
                time_obj = datetime.strptime(time, '%M:%S')
            else:
                time_obj = datetime.strptime(time, '%H:%M:%S')
            seconds = (time_obj.time().hour * 60 + time_obj.time().minute) * 60 + time_obj.time().second
            start1=int(seconds/random.uniform(9.6,10.4))
            start1=str(timedelta(seconds=start1))+'.800'
            if (seconds>180):
                start2=int(seconds/random.uniform(7.2,7.9))            
            else:
                if (seconds>60):
                    start2=int(seconds/random.uniform(6.2,6.9))
                else:
                    start2=int(seconds/random.uniform(2.1,2.9))
            start2=str(timedelta(seconds=start2))+'.800'
            print("SECONDS=",start1,"  ", start2)
            

            print("height=======",result['height'])
            subprocess.call(["ffmpeg","-loglevel", "16","-ss",start1,"-i",result['url'],"-t","00:00:07","-vf","fps=4/1",(folder+"/ytb/1Render/{1}/screens/{0}_0_%d.png").format(cnt0+1,country)])
            subprocess.call(["ffmpeg","-loglevel", "16","-ss",start2,"-i",result['url'],"-t","00:00:07","-vf","fps=4/1",(folder+"/ytb/1Render/{1}/screens/{0}_1_%d.png").format(cnt0+1,country)])
            for rnm in range(1,29):
                shutil.move((folder+"/ytb/1Render/{2}/screens/{0}_1_{1}.png").format(cnt0+1,rnm,country), (folder+"/ytb/1Render/{2}/screens/{0}_0_{1}.png").format(cnt0+1,rnm+28,country))
            if (result['height']!=720):
                subprocess.call(["ffmpeg", "-loglevel", "16", "-r", "8/1",  "-i", (folder+"/ytb/1Render/{1}/screens/{0}_0_%d.png").format(cnt0+1,country), "-c:v", "libx264", "-vf", "fps=25", "-pix_fmt", "yuv420p", (folder+"/ytb/1Render/{1}/videos/{0}_1.mp4").format(cnt0+1,country)])
                subprocess.call(["ffmpeg", "-i", (folder+"/ytb/1Render/{1}/videos/{0}_1.mp4").format(cnt0+1,country), "-vf", "scale=1280:-1,pad=1280:720:(ow-iw)/2:(oh-ih)/2", (folder+"/ytb/1Render/{1}/videos/{0}.mp4").format(cnt0+1,country)])            

            if (result['width']!=1280):
                subprocess.call(["ffmpeg", "-loglevel", "16", "-r", "8/1",  "-i", (folder+"/ytb/1Render/{1}/screens/{0}_0_%d.png").format(cnt0+1,country), "-c:v", "libx264", "-vf", "fps=25", "-pix_fmt", "yuv420p", (folder+"/ytb/1Render/{1}/videos/{0}_1.mp4").format(cnt0+1,country)])
                subprocess.call(["ffmpeg", "-i", (folder+"/ytb/1Render/{1}/videos/{0}_1.mp4").format(cnt0+1,country), "-vf", "scale=-1:720,pad=1280:720:(ow-iw)/2:(oh-ih)/2", (folder+"/ytb/1Render/{1}/videos/{0}.mp4").format(cnt0+1,country)])            
                
            if (result['width']==1280 and result['height']==720):  
                subprocess.call(["ffmpeg", "-loglevel", "16", "-r", "8/1",  "-i", (folder+"/ytb/1Render/{1}/screens/{0}_0_%d.png").format(cnt0+1,country), "-c:v", "libx264", "-vf", "fps=25", "-pix_fmt", "yuv420p", (folder+"/ytb/1Render/{1}/videos/{0}.mp4").format(cnt0+1,country)])
                    
        #Определение объектов на глвном изображении
        text_position0 = (0, 0)

        Xcord=300 #X координата старта
        Ycord=1077 #Y координата старта
        
        
        # собственно, сам текст
        img= Image.new("RGB", (5120, 2880), (241,241,241)) #(3840, 2160)
        img_main= Image.new("RGBA", (7120, 150), (0,0,0,0)) #(3840, 2160)
        img_channel= Image.new("RGB", (9120, 100), (241,241,241)) #(3840, 2160)
        img_descr= Image.new("RGB", (8120, 100), (241,241,241)) #(3840, 2160)
        img_rect= Image.new("RGB", (500, 94), (0,0,0)) #(3840, 2160)
        img_like= Image.new("RGB", (1280, 300), (241,241,241)) #(3840, 2160)
        img_like_text= Image.new("RGB", (1280, 300), (241,241,241)) #(3840, 2160)

        # определяете объект для рисования
        draw = ImageDraw.Draw(img) #Основное изображение
        draw_main = ImageDraw.Draw(img_main)
        draw_channel = ImageDraw.Draw(img_channel)
        draw_rect = ImageDraw.Draw(img_rect)
        draw_descr = ImageDraw.Draw(img_descr)
        draw_like = ImageDraw.Draw(img_like)
        draw_like_text = ImageDraw.Draw(img_like_text)
        
        #Чтение эмодзи (https://emojipedia.org/microsoft/)
        with open(folder+"/ytb/files/emj_list.html", encoding="utf-8") as file:
            nums = file.read().splitlines()

        #///===============================
        #///===============================
        #///===============================
        #Название видео
        #///===============================
        #///===============================
        #///===============================    
        text_position0 = (0, 10)
        matrix = []

              
        #Замена лишних пробелов и переносов на одинарные пробелы
        text_main=re.sub(r'\s+', ' ', text_main)
        for cnt in range(0,6494,2):
            for m in re.finditer(nums[cnt], text_main):
                if (m.start()) is not None:
                    matrix.append([])
                    #Начало в строке
                    #Конец в строке
                    #Длина символа
                    #Порядковый номер эмодзя
                    #Длина эмодзи в пикселях
                    matrix[len(matrix)-1].append(m.start())
                    matrix[len(matrix)-1].append(m.end())
                    matrix[len(matrix)-1].append(len(nums[cnt]))
                    matrix[len(matrix)-1].append(cnt)
                    matrix[len(matrix)-1].append(draw_main.textsize(nums[cnt], font_emoji_main))

        #Отброс корявых эмодзи
        main=sorted(matrix, key=itemgetter(0)) 
        main0=[] #Список удаляемых элементов-эмодзи из main
        for s in range (0,len(main)):
            if (s<len(main)):
                if (main[s][2]>1):
                    main_start=main[s][0]
                    main_len=main[s][2]
                    for t in range (0,len(main)):
                        if (t<len(main)):
                            if (main[t][0]==main_start and main[t][2]<main_len):
                                main0.append(t)
                            if (main[t][0]>main_start and  main[t][0]<=main_start+main_len-1):
                                main0.append(t)

        #Удаление элементов-эмодзи из main
        set_main0 = set(main0)
        list_main0 = list(set_main0)
        for t in range (len(list_main0)-1,-1,-1):
            del main[list_main0[t]]
            
            
        for s in range (len(main)-1,-1,-1):
            text_main=text_main[:main[s][0]]+" " + text_main[main[s][1]:]

        #Корректная замена эмодзи на пробел со сдвигом
        dwj=0
        for s in range (0,len(main)):
            main[s][0]=main[s][0]-dwj
            dwj=dwj+main[s][2]-1

        double_str=False
        line_len=3000 #Максимальная длина строки в пикселях
        texto_list=list(text_main)
        char_size=0
        font_past=0
        kern_position1=0
        kern1=0
        font_past_string=0
        kernstring=''
        
        #Отрисовка текста, в зависимости от языка и с учетом кернингов шрифта         
        for ln in range (0,len(texto_list)):           
            #Поиск другой локали, если есть
            if not (char_in_font(texto_list[ln],font_Roboto)):
                for lang in range (0,len(locals)):
                    if (char_in_font(texto_list[ln],TTFont(font0.format(locals[lang][0])))):
                        font_string=locals[lang][0]
                        font_up=int(locals[lang][2])
                        font=ImageFont.truetype(font0.format(locals[lang][0]), 94)
            else:
                font_string="Roboto-Regular.ttf"
                font=ImageFont.truetype(folder+"/ytb/fonts/Roboto-Regular.ttf", 94)
                font_up=0
              
              
            #Kern
            char_size=draw_main.textsize(texto_list[ln], font,features="kern")[0]
            if ln!=0:
                if (font_past_string!=font_string):   
                    for kr in range (kern1,ln):
                        kernstring=kernstring+texto_list[kr] 
                    draw_main.text(text_position0, kernstring, color_main, font_past,features="kern")
                    kern_position1=draw_main.textsize(kernstring, font_past,features="kern")
                    text_position0=(text_position0[0],10)
                    text_position0=(text_position0[0]+kern_position1[0],text_position0[1]+font_up)
                    kern1=ln

                
                if (texto_list[ln-1]==' ' and texto_list[ln]!=' '):
                    kernstring=''
                    for kr in range (kern1,ln):
                        kernstring=kernstring+texto_list[kr]
                    draw_main.text(text_position0, kernstring, color_main, font_past,features="kern")
                    kern_position1=draw_main.textsize(kernstring, font_past,features="kern")
                    kern1=ln
                    text_position0=(text_position0[0]+kern_position1[0],text_position0[1])                    
                    if ((text_position0[0]+char_size)<line_len):   
                        probel=text_position0[0]
                          

            if (ln==len(texto_list)-1):
                kernstring=''
                for kr in range (kern1,ln+1):
                    kernstring=kernstring+texto_list[kr] 
                draw_main.text(text_position0, kernstring, color_main, font_past,features="kern")
                kern_position1=draw_descr.textsize(kernstring, font_past,features="kern")
                if ((text_position0[0]+kern_position1[0])<line_len):
                    double_str=False
                else:
                    double_str=True
                        
            
            
            #Если в тексте есть эмодзи, конвертация до необходимого размера и вставка в текст
            for s in range (0,len(main)):
                if main[s][0]==ln:
                    imgemj=Image.open(folder+nums[main[s][3]+1]).convert("RGBA")
                    imgemj106 = imgemj.resize((106,106),resample=Image.BILINEAR).convert("RGBA")
                    
                    if (main[s][4][0]>=122):
                        char_size0=122
                    else:
                        area=(((122-main[s][4][0])/2),0,(106-((122-main[s][4][0])/2)),106)
                        imgemj106=imgemj106.crop(area).convert("RGBA")
                     
                        char_size0=main[s][4][0]
                    for kr in range (kern1,ln):
                        kernstring=kernstring+texto_list[kr]
                    if ln!=0: 
                        draw_main.text(text_position0, kernstring, color_main, font_past,features="kern")
                    kern_position1=draw_main.textsize(kernstring, font,features="kern")
                    text_position0=(text_position0[0]+kern_position1[0],text_position0[1])
                    kern1=ln+1
                    
                    img_main.paste(imgemj106, (text_position0[0]+8,text_position0[1]),mask=imgemj106)
                    char_size=char_size0   
                    text_position0=(text_position0[0]+char_size,text_position0[1])

            kernstring=''
            font_past_string=font_string
            font_past=font    
        
        #Добавление текста названия видео к основному изображению
        #Если двойная строка 
        if (double_str):
            area = (0, 0, probel, 130)
            area2 = (probel, 0, 7120, 130)
            cropped_img = img_main.crop(area)
            cropped_img2 = img_main.crop(area2)
            img.paste (cropped_img,(Xcord+1365,Ycord),mask=cropped_img)
            Ycord=Ycord+126
            img.paste (cropped_img2,(Xcord+1365,Ycord),mask=cropped_img2)
        else:
            img.paste (img_main,(Xcord+1365,Ycord),mask=img_main)
        Ycord=Ycord+123

        #///===============================
        #///===============================
        #///===============================
        #Канал автора видео
        #///===============================
        #///===============================
        #///===============================

        #Оформление значка верефикации ютубера или музыкального автора
        badge_yes=False
        if (badge=="BADGE_STYLE_TYPE_VERIFIED"):
            img_badge=Image.open(folder+"/ytb/files/verif59.png")
            badge_yes=True
        if (badge=="BADGE_STYLE_TYPE_VERIFIED_ARTIST"):
            img_badge=Image.open(folder+"/ytb/files/music34.png")
            badge_yes=True    
        if (badge_yes):
            if (text_subscribers_cut):
                text_channel_full=text_channel+"   "+text_subscribers_cut+" • "+text_views+" • "+time_published_format+" • "+text_ago 
            else:
                text_channel_full=text_channel+"   "+text_views+" • "+time_published_format+" • "+text_ago 
        else:
            if (text_subscribers_cut):
                text_channel_full=text_channel+" • "+text_subscribers_cut+" • "+text_views+" • "+time_published_format+" • "+text_ago 
            else:
                text_channel_full=text_channel+" • "+text_views+" • "+time_published_format+" • "+text_ago 


        text_position0 = (0, 10)
        line_len=3000 #Максимальная длина строки в пикселях
        text_channel_len=len(text_channel)+1
        texto_list=list(text_channel_full)
        char_size=0
        font_past=0
        kern_position1=0
        kern1=0
        font_past_string=0
        kernstring=''
        for ln in range (0,len(texto_list)):
            if not (char_in_font(texto_list[ln],font_Roboto)):
                for lang in range (0,len(locals)):
                    if (char_in_font(texto_list[ln],TTFont(font0.format(locals[lang][0])))):
                        font_string=locals[lang][0]
                        font_up=int(locals[lang][3])
                        font=ImageFont.truetype(font0.format(locals[lang][0]), 68)       
            else:
                font_string="Roboto-Regular.ttf"
                font=ImageFont.truetype(folder+"/ytb/fonts/Roboto-Regular.ttf", 68)
                font_up=0            
            #Кернинг
            
            char_size=draw_channel.textsize(texto_list[ln], font,features="kern")[0]
            if ln!=0:        
                if (ln==text_channel_len):
                        if (badge_yes):
                            for kr in range (kern1,ln):
                                kernstring=kernstring+texto_list[kr]
                                #print(kernstring)
                            draw_channel.text(text_position0, kernstring, color_descr, font_past,features="kern")
                            kern_position1=draw_channel.textsize(kernstring, font,features="kern")
                            text_position0=(text_position0[0]+kern_position1[0],text_position0[1]) 
                            kern1=ln
                            char_size=img_badge.size[0]+21
                            if (badge=="BADGE_STYLE_TYPE_VERIFIED"):
                                img_channel.paste(img_badge, (text_position0[0]+8,text_position0[1]+9),mask=img_badge)
                            if (badge=="BADGE_STYLE_TYPE_VERIFIED_ARTIST"):
                                img_channel.paste(img_badge, (text_position0[0]+8,text_position0[1]+13),mask=img_badge)
                            text_position0=(text_position0[0]+char_size,text_position0[1])             
            
                if (font_past_string!=font_string):   
                    for kr in range (kern1,ln):
                        kernstring=kernstring+texto_list[kr]
                    draw_channel.text(text_position0, kernstring, color_descr, font_past,features="kern")
                    kern_position1=draw_channel.textsize(kernstring, font_past,features="kern")
                    text_position0=(text_position0[0],10)
                    text_position0=(text_position0[0]+kern_position1[0],text_position0[1]+font_up) 
                    kern1=ln
            
            if (ln==text_channel_len+2): #Перенос просмотров и времени после значка, если нужно
                if not (text_subscribers_cut):
                    probel=text_position0[0]
                
            
            if (text_subscribers_cut):
                if (ln==text_channel_len+2+len(text_subscribers_cut)+3): #Перенос просмотров и времени после значка, если нужно                
                    for kr in range (kern1,ln):
                        kernstring=kernstring+texto_list[kr]
                                    #print(kernstring)
                    draw_channel.text(text_position0, kernstring, color_descr, font_past,features="kern")
                    kern_position1=draw_channel.textsize(kernstring, font_past,features="kern")
                    text_position0=(text_position0[0]+kern_position1[0],text_position0[1])
                    kern1=ln
                    probel=text_position0[0]
                    #probel2=text_position0[0]+draw_channel.textsize("• ", font,features="kern")[0]
                
            
            if (ln==len(texto_list)-1): #нужен ли перенос строки
                for kr in range (kern1,ln+1):
                    kernstring=kernstring+texto_list[kr]
                kern_position1=draw_channel.textsize(kernstring, font_past,features="kern")
                draw_channel.text(text_position0, kernstring, color_descr, font_past,features="kern")
                if ((text_position0[0]+kern_position1[0])<line_len):
                    double_str=False
                else:
                    double_str=True
            
            kernstring=''
            font_past_string=font_string
            font_past=font

        #Добавление текста названия канала; числа подписчиков; просмотров этого видео;, времени/дате публикации; времени, прошедему с момента публикации(1 час, 1 день и тд)
        if (double_str):
            area = (0, 0, probel, 100)
            area2 = (probel, 0, 9120, 100)
            cropped_img = img_channel.crop(area)
            cropped_img2 = img_channel.crop(area2)
            img.paste (cropped_img,(Xcord+1365,Ycord))
            Ycord=Ycord+94
            img.paste (cropped_img2,(Xcord+1365,Ycord))
        else:
            img.paste (img_channel,(Xcord+1365,Ycord))
        Ycord=Ycord+146

        #///===============================
        #///===============================
        #///===============================
        #Описание видео
        #///===============================
        #///===============================
        #///===============================
        if (text_descr):
            #Нахождение эмодзи для описания
            text_position0 = (0, 0)
            matrix = []
            #Замена лишних пробелов и переносов на одинарные пробелы
            text_descr=re.sub(r'\s+', ' ', text_descr)
            print(text_descr)
            for cnt in range(0,6494,2):
                for m in re.finditer(nums[cnt], text_descr):
                    if (m.start()) is not None:
                        matrix.append([])
                        #Начало в строке
                        #Конец в строке
                        #Длина символа
                        #Порядковый номер эмодзя
                        #Длина эмодзи в пикселях
                        matrix[len(matrix)-1].append(m.start())
                        matrix[len(matrix)-1].append(m.end())
                        matrix[len(matrix)-1].append(len(nums[cnt]))
                        matrix[len(matrix)-1].append(cnt)
                        matrix[len(matrix)-1].append(draw_descr.textsize(nums[cnt], font_emoji_descr))
     
            #Отброс корявых эмодзи
            main=sorted(matrix, key=itemgetter(0)) 
            main0=[] #Список удаляемых элементов-эмодзи из main
            for s in range (0,len(main)):
                if (s<len(main)):
                    if (main[s][2]>1):
                        main_start=main[s][0]
                        main_len=main[s][2]
                        for t in range (0,len(main)):
                            if (t<len(main)):
                                if (main[t][0]==main_start and main[t][2]<main_len):
                                    main0.append(t)
                                if (main[t][0]>main_start and  main[t][0]<=main_start+main_len-1):
                                    main0.append(t)

            #Удаление элементов-эмодзи из main
            set_main0 = set(main0)
            list_main0 = list(set_main0)
            for t in range (len(list_main0)-1,-1,-1):
                del main[list_main0[t]]
                      
            for s in range (len(main)-1,-1,-1):
                text_descr=text_descr[:main[s][0]]+" " + text_descr[main[s][1]:]

            #Корректная замена эмодзи на пробел со сдвигом
            dwj=0
            for s in range (0,len(main)):
                main[s][0]=main[s][0]-dwj
                dwj=dwj+main[s][2]-1


            line_len=3100 #Максимальная длина строки в пикселях
            texto_list=list(text_descr)
            char_size=0
            font_past=0
            kern_position1=0
            kern1=0
            font_past_string=0
            kernstring=''
            for ln in range (0,len(texto_list)):
                #Поиск другой локали, если есть
                if not (char_in_font(texto_list[ln],font_Roboto)):
                    for lang in range (0,len(locals)):
                        if (char_in_font(texto_list[ln],TTFont(font0.format(locals[lang][0])))):
                            font_string=locals[lang][0]
                            font_up=int(locals[lang][3])
                            font=ImageFont.truetype(font0.format(locals[lang][0]), 68)       
                else:
                    font_string="Roboto-Regular.ttf"
                    font=ImageFont.truetype(folder+"/ytb/fonts/Roboto-Regular.ttf", 68)
                    font_up=0
                    
                #Кернинг
                char_size=draw_descr.textsize(texto_list[ln], font,features="kern")[0]
                
                if ln!=0:    
                    if (font_past_string!=font_string):   
                        for kr in range (kern1,ln):
                            kernstring=kernstring+texto_list[kr]
                        draw_descr.text(text_position0, kernstring, color_descr, font_past,features="kern")
                        kern_position1=draw_descr.textsize(kernstring, font_past,features="kern")
                        text_position0=(text_position0[0],0)
                        text_position0=(text_position0[0]+kern_position1[0],text_position0[1]+font_up)  
                        kern1=ln

                    
                    if (texto_list[ln-1]==' ' and texto_list[ln]!=' '):
                        kernstring=''
                        for kr in range (kern1,ln):
                            kernstring=kernstring+texto_list[kr]
                        draw_descr.text(text_position0, kernstring, color_descr, font_past,features="kern")
                        kern_position1=draw_descr.textsize(kernstring, font_past,features="kern")
                        kern1=ln

                        text_position0=(text_position0[0]+kern_position1[0],text_position0[1])            
                        if ((text_position0[0])<line_len):   
                            probel=text_position0[0]
                                    
                if (ln==len(texto_list)-1): 
                    kernstring=''
                    for kr in range (kern1,ln+1):
                        kernstring=kernstring+texto_list[kr]
                    draw_descr.text(text_position0, kernstring, color_descr, font_past,features="kern")
                    kern_position1=draw_descr.textsize(kernstring, font_past,features="kern")
                    if ((text_position0[0]+kern_position1[0])<line_len):
                        double_str=False
                    else:
                        double_str=True
                
                #Если есть эмодзи
                for s in range (0,len(main)):
                    if main[s][0]==ln:
                        
                        imgemj=Image.open(folder+nums[main[s][3]+1]).convert("RGBA")
                        imgemj78 = imgemj.resize((78,78),resample=Image.BILINEAR).convert("RGBA")
                        
                        if (main[s][4][0]>=96):
                            char_size0=94
                        else:
                            area=(((94-main[s][4][0])/2),0,(78-((94-main[s][4][0])/2)),78)
                            imgemj78=imgemj78.crop(area).convert("RGBA")
                         
                            char_size0=main[s][4][0]
                        for kr in range (kern1,ln):
                            kernstring=kernstring+texto_list[kr]
                        if ln!=0: 
                            draw_descr.text(text_position0, kernstring, color_descr, font_past,features="kern")
                        kern_position1=draw_descr.textsize(kernstring, font,features="kern")
                        text_position0=(text_position0[0]+kern_position1[0],text_position0[1])
                        kern1=ln+1
                        
                        img_descr.paste(imgemj78, (text_position0[0]+8,text_position0[1]),mask=imgemj78)
                        char_size=char_size0   
                        text_position0=(text_position0[0]+char_size,text_position0[1])

                kernstring=''
                font_past_string=font_string
                font_past=font

            #Добавление к основному изображению описание видео
            if (double_str):
                area = (0, 0, probel, 100)
                area2 = (probel, 0, 8120, 100)
                cropped_img = img_descr.crop(area)
                cropped_img2 = img_descr.crop(area2)
                img.paste (cropped_img,(Xcord+1365,Ycord))
                Ycord=Ycord+93
                img.paste (cropped_img2,(Xcord+1365,Ycord))
            else:
                img.paste (img_descr,(Xcord+1365,Ycord))
            
        #Добавление к основному изображению ссылки на канал и видео
        draw.text((Xcord+1365,Ycord+140), "https://www.youtube.com"+text_channel_link, color_descr, ImageFont.truetype(folder+"/ytb/fonts/Roboto-Regular.ttf", 68),features="kern")
        draw.text((Xcord+1365,Ycord+230), "https://www.youtube.com/watch?v="+video_id, color_descr, ImageFont.truetype(folder+"/ytb/fonts/Roboto-Regular.ttf", 68),features="kern")
        
        #=============
        #Лайки под превью
        #=============
        if (text_likes):
            text_position0 = (0, 0)
            font_past=0
            kern_position1=0
            kern1=0
            font_past_string=0
            kernstring=''
            imglike=Image.open(folder+"/ytb/files/like3700.png").convert("RGBA")
            imgkike_T164 = imglike.resize((100,100),resample=Image.BILINEAR).convert("RGBA")
            img_like.paste(imgkike_T164, (44, 64),mask=imgkike_T164) 


            likdis=text_likes_cut+text_dislikes_cut
            for ln in range (0,len(likdis)):
                #Поиск другой локали, если есть            
                if not (char_in_font(likdis[ln],font_Roboto)):
                    for lang in range (0,len(locals)):
                        if (char_in_font(likdis[ln],TTFont(font0.format(locals[lang][0])))):
                            #print(locals[lang][1])
                            font_string=locals[lang][0]
                            font_up=int(locals[lang][3])
                            font=ImageFont.truetype(font0.format(locals[lang][0]), 68)       
                else:
                    font_string="Roboto-Regular.ttf"
                    font=ImageFont.truetype(folder+"/ytb/fonts/Roboto-Regular.ttf", 68)
                    font_up=0
                
                if ln!=0:    
                    if (font_past_string!=font_string and ln!=len(text_likes_cut)):   
                        for kr in range (kern1,ln):
                            kernstring=kernstring+likdis[kr]
                        draw_like_text.text(text_position0, kernstring, color_descr, font_past,features="kern")
                        kern_position1=draw_like_text.textsize(kernstring, font_past,features="kern")
                        text_position0=(text_position0[0],0)
                        text_position0=(text_position0[0]+kern_position1[0],text_position0[1]+font_up)  
                        kern1=ln
                    if (ln==len(text_likes_cut) or ln==len(likdis)-1):                        
                        if (ln==len(likdis)-1):
                            for kr in range (kern1,ln+1):
                                kernstring=kernstring+likdis[kr]                    
                        else:
                            for kr in range (kern1,ln):
                                kernstring=kernstring+likdis[kr]
                        draw_like_text.text(text_position0, kernstring, color_descr, font_past,features="kern")
                        kern_position1=draw_like_text.textsize(kernstring, font_past,features="kern")
                        text_position0=(text_position0[0],0)
                        text_position0=(text_position0[0]+kern_position1[0],text_position0[1]+font_up)  
                        if (ln==len(text_likes_cut)):
                            text_positionT=text_position0
                        else:
                            text_positionF=text_position0
                        kern1=ln
                
                kernstring=''
                font_past_string=font_string
                font_past=font
            
            
            #Вставка текста лайка
            area = (0, 0, text_positionT[0], 100)
            area2 = (text_positionT[0], 0, text_positionF[0], 100)
            cropped_img = img_like_text.crop(area)
            cropped_img2 = img_like_text.crop(area2)
            img_like.paste(cropped_img,(44+100+42,85))

            
            #Рисование полоски процентов
            img_like_draw = ImageDraw.Draw(img_like)
            img_like_draw.rectangle([(0,215),(1280,229)], fill =color_soft) 
                
            if (like_percent>=95):
                percent_color=(0,215,0)
            else:
                if (like_percent<=94 and like_percent>=21):
                    percent_color=(int(color_like[like_percent-21][1]),int(color_like[like_percent-21][2]),0)
                else:
                    percent_color=(235,0,0)
                    
            img_like_draw.rectangle([(0,215),(round(12.8*int(like_percent)),229)], fill =percent_color) 
            
            #Рисование количества процентов(число)
            like_percent=str(like_percent)+"%"
            like_percent_size=draw_like.textsize(like_percent, ImageFont.truetype(folder+"/ytb/fonts/Roboto-Regular.ttf", 60),features="kern")
            draw_like.text((1280-like_percent_size[0],93), like_percent, color_descr, ImageFont.truetype(folder+"/ytb/fonts/Roboto-Regular.ttf", 60),features="kern")
            #Вставка текста дизлайка и символа
            XcordF=1280-44-(text_positionF[0]-text_positionT[0])-like_percent_size[0]
            img_like.paste(cropped_img2,(XcordF,85))
            imgkike_F164=imgkike_T164.transpose(Image.ROTATE_180)
            img_like.paste(imgkike_F164,(XcordF-100-42, 80),mask=imgkike_F164) 
            
            #Вставка лайков в главное изображение
            img.paste(img_like, (Xcord, 1820))
        
       
        #Превью
        wayopen=(folder+"/ytb/1Render/{1}/thumbnails/{0}.png").format(video_id,country)
        img_thumb=Image.open(wayopen)
        img.paste(img_thumb, (Xcord, 1080))


        #Время в прямоугольнике
        #Прямоугольник
        rect_x=draw_rect.textsize(time, font_rect)[0]+(len(time)*2)-2+48
        img_rect = round_rectangle((rect_x, 94), 11, "yellow")
        img_rect2 =img_rect.filter(ImageFilter.GaussianBlur(radius = 0.4))
        img.paste(img_rect, (Xcord+1280-21-rect_x, 1800-21-94), mask=img_rect2)

        #Время
        time_pos0=(Xcord+1235-rect_x+48, 1695)
        for tm in range (0,len(time)):
            draw.text(time_pos0, time[tm], color_time, font_rect)
            time_pos0=(time_pos0[0]+draw_descr.textsize(time[tm], font_rect)[0],time_pos0[1])
            time_pos0=(time_pos0[0]+2,time_pos0[1])

   
        #Номер в трендах
        draw_trend_number = ImageDraw.Draw(img)
        draw_trend_number.text((300,840), '#'+str(cnt0+1), (34,97,207), ImageFont.truetype(folder+"/ytb/fonts/Roboto-Regular.ttf", 150),features="kern")
        

        os.rmdir((folder+"/ytb/1Render/{0}/thumbnails").format(country))
        wayopen1=(folder+"/ytb/1Render/{1}/thumbnails0/{0}.png").format(cnt0+1,country)
        img.save(wayopen1)
        
    shutil.copy((folder+"/ytb/1big_flags/{0}.png").format(country), (folder+"/ytb/1Render/{0}/thumbnails0/flag.png").format(country))    
        
    time_render=good_timezone_converter(datetime.utcnow(), current_tz='UTC', target_tz=time_zones[country][1])
    time_render_format=time_render.strftime(time_zones[country][2]) 
    
    """
    date_render_format=time_render.strftime(time_zones[country][4]) 
    img_date_render= Image.new("RGBA", (1700, 340), (255,0,0,0))
    draw_date_render = ImageDraw.Draw(img_date_render)
    draw_date_render.text((0,0), date_render_format, color_main, ImageFont.truetype(folder+"/ytb/fonts/Roboto-Regular.ttf", 300),features="kern")
    wayopen3=((folder+"/ytb/1Render/{0}/thumbnails0/date.png").format(country))
    img_date_render.save(wayopen3)
    """ 
    
    img_time_render= Image.new("RGBA", (1500, 210), (255,0,0,0)) #(3840, 2160)
    draw_time_render = ImageDraw.Draw(img_time_render)
    draw_time_render.text((0,0), time_render_format, color_main, ImageFont.truetype(folder+"/ytb/fonts/Roboto-Thin.ttf", 110),features="kern")
    draw_time_render.text((0,120), "Update time", color_main, ImageFont.truetype(folder+"/ytb/fonts/Roboto-Thin.ttf", 80),features="kern")     
    wayopen3=((folder+"/ytb/1Render/{0}/thumbnails0/time.png").format(country))
    img_time_render.save(wayopen3)
      
    """
    print(Tags_text)
    print(full_links)
    with open((folder+"/ytb/1Render/{0}/links.txt").format(country), "a", encoding='utf8') as file:
        file.write(full_links)
        file.write(Tags_text)
    """


if __name__ == "__main__":
    import argparse    
    url = f"https://www.youtube.com/feed/trending"
    #Ваш YouTube api ключ вместо ...
    print("Введите ваш YouTube api key:")
    
    api_key = str(input())
    
    get_video(url, False,api_key)
