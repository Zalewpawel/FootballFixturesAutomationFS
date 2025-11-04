*** Settings ***
Documentation       This task suite scrapes league tables from Flashscore.
Library             Browser
Library             flashscore_keywords.FlashscoreKeywords
Resource            common.resource

Suite Setup         Open Suite Browser
Suite Teardown      Close Browser

*** Variables ***
${INPUT_PATH}       Config/input.json
${OUTPUT_PATH}      results.json

*** Tasks ***
Collect Football League Standings
    ${leagues}=         Load Leagues From File    ${INPUT_PATH}
    ${results}=         Collect Standings For Leagues    ${leagues}
    Save Results Json   ${results}    ${OUTPUT_PATH}