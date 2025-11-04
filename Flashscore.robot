*** Settings ***
Library    Browser
Library    Flashscore_keywords.FlashscoreKeywords

Suite Setup     Open Suite Browser
Suite Teardown  Close Browser

*** Variables ***
${INPUT_PATH}      input.json
${OUTPUT_PATH}     results.json

*** Test Cases ***
Zbierz tabele dla wielu lig
    ${leagues}=    Load Leagues From File    ${INPUT_PATH}
    ${results}=    Collect Standings For Leagues    ${leagues}
    Save Results Json    ${results}    ${OUTPUT_PATH}

*** Keywords ***
Open Suite Browser
    New Browser    chromium    headless=False    slowMo=0ms
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

