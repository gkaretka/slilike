import base64
import io
import urllib
import PIL.Image as Image

from matplotlib import pyplot as plt
from wordcloud import WordCloud


def create_word_cloud_from_data(words):
    wordcloud = WordCloud(width=800, height=800,
                          background_color='white',
                          min_font_size=10).generate(words)

    image = wordcloud.to_image()
    io_bytes = io.BytesIO()
    image.save(io_bytes, format="png")
    io_bytes.seek(0)
    string = base64.b64encode(io_bytes.read())

    image_64 = 'data:image/png;base64,' + urllib.parse.quote(string)
    return image_64