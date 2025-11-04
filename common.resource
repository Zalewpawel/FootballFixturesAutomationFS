*** Keywords ***
Open Suite Browser
    New Browser    chromium    headless=True    slowMo=0ms
    New Context    viewport={'width':1280,'height':800}    locale=en-US
    New Page
    Set Browser Timeout    45s
    Go To    https://www.flashscore.com/    wait_until=domcontentloaded
    ${url}=    Get Url
    ${title}=  Get Title
    Log    URL: ${url}
    Log    Title: ${title}
    IF    '${url}'.startswith('https://m.flashscore.com')
        Go To    https://www.flashscore.com/    wait_until=domcontentloaded
        ${url}=    Get Url
        ${title}=  Get Title
        Log    URL (retry): ${url}
        Log    Title (retry): ${title}
    END