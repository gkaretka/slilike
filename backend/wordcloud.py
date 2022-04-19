import base64
import io
import urllib
from wordcloud import WordCloud


def create_word_cloud_from_data(words_list):
    wordcloud = WordCloud(width=800, height=800,
                          background_color='white',
                          min_font_size=10, collocations=False).fit_words(dict(words_list))

    image = wordcloud.to_image()
    io_bytes = io.BytesIO()
    image.save(io_bytes, format="png")
    io_bytes.seek(0)
    string = base64.b64encode(io_bytes.read())

    image_64 = 'data:image/png;base64,' + urllib.parse.quote(string)
    return image_64