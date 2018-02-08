import asyncio
from base64 import b64encode

import aiohttp

class CartoonAPI:
    def __init__(self, url):
        self.url = url
        self.randomUrl = self.url + 'api/random'
        self.captionUrl = self.url + 'api/caption?e={}&t={}'
        self.searchUrl = self.url + 'api/search?q='
        self.imageUrl = self.url + 'meme/{}/{}.jpg?b64lines={}'
        self.gifUrl = self.url + 'gif/{}/{}/{}.gif?b64lines={}'

    # Generates a random cartoon image/gif, with caption embedded into the
    # image/gif, chooses jpg by default
    async def getRandomCartoon(self, gif=False):
        async with aiohttp.ClientSession() as session:
            async with session.get(self.randomUrl, timeout=30) as cartoonPage:

                if cartoonPage.status == 200:
                    cartoonJson = await cartoonPage.json()

                    episode = str(cartoonJson['Episode']['Key'])

                    if gif:
                        timestamp = cartoonJson['Subtitles'][0]['StartTimestamp']

                        if len(cartoonJson['Subtitles']) < 2:
                            endTimestamp = cartoonJson['Subtitles'][0]['EndTimestamp']

                        else:
                            endTimestamp = cartoonJson['Subtitles'][1]['EndTimestamp']

                        return self.gifUrl.format(episode, timestamp, endTimestamp, self.encodeCaption(cartoonJson))

                    else:
                        timestamp = cartoonJson['Frame']['Timestamp']
                        return self.imageUrl.format(episode, timestamp, self.encodeCaption(cartoonJson))

                else:
                    return 'Error 404. {} may be down.'.format(self.url)

    # Generates a cartoon image/gif, with caption embedded into the image/gif,
    # uses first search result returned from messageText
    async def findCartoonQuote(self, searchText, gif=False):
        searchText = searchText.replace(' ', '+')
        search = self.searchUrl + searchText

        async with aiohttp.ClientSession() as session:
            async with session.get(search, timeout=15) as cartoonSearch:
                if cartoonSearch.status == 200:
                    searchResults = await cartoonSearch.json()

                    if len(searchResults) > 0:
                        firstResult = searchResults[0]

                        episode = str(firstResult['Episode'])
                        timestamp = str(firstResult['Timestamp'])

                    else:
                        return 'No search results found.'

                else:
                    return 'Error 404. {} may be down.'.format(self.url)

            async with session.get(self.captionUrl.format(episode, timestamp), timeout=15) as caption:
                if caption.status == 200:
                    cartoonJson = await caption.json()

                    if gif:
                        timestamp = cartoonJson['Subtitles'][0]['StartTimestamp']

                        if len(cartoonJson['Subtitles']) < 2:
                            endTimestamp = cartoonJson['Subtitles'][0]['EndTimestamp']

                        else:
                            endTimestamp = cartoonJson['Subtitles'][1]['EndTimestamp']

                        return self.gifUrl.format(episode, timestamp, endTimestamp, self.encodeCaption(cartoonJson))

                    else:
                        timestamp = cartoonJson['Frame']['Timestamp']
                        return self.imageUrl.format(episode, timestamp, self.encodeCaption(cartoonJson))

                else:
                    return 'Error 404. {} may be down.'.format(self.url)

    # Generate the gif and get the direct url for embedding
    async def generateGif(self, gifUrl):
        async with aiohttp.ClientSession() as session:
            try:
                async with session.get(gifUrl, timeout=30) as generator:
                    if generator.status == 200:
                        return generator.url

            except asyncio.TimeoutError:
                return gifUrl

    # Loop through all words of the subtitles, add them to the caption and then
    # return the caption encoded in base64 for use in the url
    def encodeCaption(self, captionJson):
        charCount = 0
        lineCount = 0
        caption = ''

        for quote in captionJson['Subtitles']:
            for word in quote['Content'].split():
                charCount += len(word) + 1

                if charCount < 24 and lineCount < 4:
                    caption += ' %s' % word

                elif lineCount < 4:
                    charCount = len(word) + 1
                    lineCount += 1
                    if lineCount < 4:
                        caption += '\n' + ' %s' % word


        caption = self.shortenCaption(caption)
        encoded = b64encode(str.encode(caption, 'utf-8'), altchars=b'__')

        return encoded.decode('utf-8')

    # Favours ending the caption at the latest sentence ending (., !, ?)
    def shortenCaption(self, caption):
        for i in range(len(caption) - 1, 0, -1):
            if caption[i] == '.' or caption[i] == '!' or caption[i] == '?':
                return caption[:i+1]

        return caption