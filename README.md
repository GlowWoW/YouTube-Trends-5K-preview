# YouTube-Trends-5K-preview
Software for creating an extended 5K preview of Trends on YouTube (with the ability to create an extended video-preview)<p>Софт для создания расширенных 5K превью Трендов YouTube (с возможностью создания расширенного видео-превью)

#Запускается скриптом run.py. Для запуска должен быть установлен список шрифтов и быть продублирован .ttf или  .otf файлами по пути "/ytb/fonts". Roboto-основной шрифт на YouTube, для остальных локальных языков-Arial (или более подходящие, если есть)

#Аналогично-эмодзи в версии Microsoft должны быть сохранены по пути "/ytb/emj", были получены из этого списка https://emojipedia.org/microsoft/ в разрешении 120x120, оригинальные названия сохранены

#Кроме указанных ниже библиотек, необходимо установить libraqm для поддержки кернинга шрифтов, потому что в Windows по умолчанию кернинг не предусмотрен для использования с помощью PIL. https://www.lfd.uci.edu/~gohlke/pythonlibs/#pillow установить libraqm в: Путь_до_папки_пользователя/vcpkg-master/ports)

#Возможность создания видео-превью включается изменением 2-го аргумента на True в вызове get_video

<h4>Пример конечного вывода изображения</h4> 
<img src="https://i.ibb.co/Zhy8RCT/1.png" width="80%" height="70%">
<h6>Еще примеры изображений в: /ytb/1Render/82/thumbnails0<h6>
<h4>GIF пример видеопревью</h4>
<img src="ytb/files/Trends_gif.gif" width="50%" height="50%">
<center><h4>Пример использования связки изображение и видео-превью</h4></center>
<p align="center"><a href="https://www.youtube.com/watch?v=dKuYhT-A9m0"><img src="https://i.ibb.co/KVF1q7R/YT.png" width="70%" height="70%"></p>

